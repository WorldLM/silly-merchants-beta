from typing import Dict, Set, List, Optional, Any
import json
from fastapi import WebSocket
from models import GameState, Player, GameAction, GamePhase
from datetime import datetime
from enum import Enum
import asyncio
from llm_client import get_llm_client, get_prompt_manager, create_example_templates
from game_record import GameRecord


# 自定义JSON编码器，处理datetime对象
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)


class EnhancedJSONEncoder(json.JSONEncoder):
    """扩展JSON编码器，处理自定义类型"""

    def default(self, obj):
        if isinstance(obj, Enum):
            # 将枚举类型转换为它的值
            return obj.value
        elif isinstance(obj, datetime):
            # 将datetime对象转换为ISO格式字符串
            return obj.isoformat()
        # 让默认编码器处理其他类型
        return super(EnhancedJSONEncoder, self).default(obj)


def serialize_for_json(obj):
    """将对象序列化为JSON安全的形式"""
    if isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        # 处理Pydantic模型
        return serialize_for_json(obj.dict())
    else:
        return obj


class ConnectionManager:
    def __init__(self):
        # 存储所有活跃连接
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # 存储玩家ID到WebSocket的映射
        self.player_connections: Dict[str, WebSocket] = {}
        # 游戏活动日志
        self.game_logs: Dict[str, List[Dict[str, Any]]] = {}

    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        try:
            print(f"尝试接受WebSocket连接: 游戏ID={game_id}, 玩家ID={player_id}")
            await websocket.accept()
            print(f"WebSocket连接已接受")
            if game_id not in self.active_connections:
                self.active_connections[game_id] = {}
            self.active_connections[game_id][player_id] = websocket

            # 特殊处理observer连接，不添加到player_connections
            if player_id != "observer":
                self.player_connections[player_id] = websocket
                print(f"WebSocket玩家连接已注册: 游戏ID={game_id}, 玩家ID={player_id}")
            else:
                print(f"WebSocket观察者连接已注册: 游戏ID={game_id}")

            print(f"WebSocket连接已注册到管理器: 游戏ID={game_id}, 玩家ID={player_id}")

            # 发送历史日志
            if game_id in self.game_logs:
                for log in self.game_logs[game_id]:
                    try:
                        await websocket.send_json(log)
                    except Exception as e:
                        print(f"【错误/WebSocket】发送历史日志时出错: {e}")
        except Exception as e:
            print(f"WebSocket连接管理器错误: {e}")
            import traceback
            traceback.print_exc()
            raise

    def disconnect(self, game_id: str, player_id: str):
        if game_id in self.active_connections:
            if player_id in self.player_connections:
                del self.active_connections[game_id][player_id]
                if not self.active_connections[game_id]:
                    del self.active_connections[game_id]

    async def broadcast_game_state(self, game_id: str, game_state: GameState):
        """广播游戏状态到所有连接的客户端"""
        if game_id in self.active_connections:
            try:
                # 使用自定义方法序列化GameState
                state_dict = serialize_for_json(game_state.__dict__)

                message = {
                    "type": "game_state",
                    "data": state_dict
                }

                print(
                    f"【调试/WebSocket】准备广播游戏状态: 游戏ID={game_id}, 连接数={len(self.active_connections[game_id])}, 回合={game_state.current_round}, 阶段={game_state.phase}")

                if len(self.active_connections[game_id]) == 0:
                    print(f"【警告/WebSocket】没有活跃的WebSocket连接，游戏状态更新可能不会实时显示: 游戏ID={game_id}")

                # 创建一个失败连接列表，用于跟踪需要移除的连接
                failed_connections = []
                success_count = 0

                for connection in self.active_connections[game_id].values():
                    try:
                        await connection.send_json(message)
                        success_count += 1
                        print(f"【调试/WebSocket】已发送游戏状态到WebSocket连接 #{success_count}")
                    except Exception as e:
                        print(f"【错误/WebSocket】发送游戏状态时出错: {e}")
                        failed_connections.append(connection)

                # 移除失败的连接
                for failed in failed_connections:
                    self.active_connections[game_id].discard(failed)
                    print(f"【调试/WebSocket】移除失败的WebSocket连接")

                if failed_connections:
                    print(
                        f"【警告/WebSocket】移除了 {len(failed_connections)} 个失败的连接，剩余 {len(self.active_connections[game_id])} 个连接")

                return success_count > 0  # 返回是否至少有一个连接成功
            except Exception as e:
                print(f"【错误/WebSocket】广播游戏状态时出错: {e}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print(f"【警告/WebSocket】没有找到游戏的WebSocket连接: 游戏ID={game_id}")
            return False

    async def send_personal_message(self, player_id: str, message: dict):
        if player_id in self.player_connections:
            await self.player_connections[player_id].send_json(message)

    async def broadcast_game_action(self, game_id: str, action: GameAction):
        if game_id in self.active_connections:
            # 使用自定义方法序列化Pydantic模型
            action_dict = serialize_for_json(action.__dict__)

            message = {
                "type": "game_action",
                "data": action_dict
            }

            # 记录到游戏日志
            if game_id not in self.game_logs:
                self.game_logs[game_id] = []
            self.game_logs[game_id].append(message)

            # 广播到所有连接
            disconnected_players = []
            for player_id, connection in self.active_connections[game_id].items():
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"【错误/WebSocket】发送游戏动作时出错: {e}")
                    disconnected_players.append(player_id)

            # 清理断开的连接
            for player_id in disconnected_players:
                self.disconnect(game_id, player_id)

            return len(self.active_connections.get(game_id, {})) > 0
        return False

    async def broadcast_game_end(self, game_id: str, winner_id: str):
        """广播游戏结束消息"""
        message = {
            "type": "game_end",
            "data": {
                "winner_id": winner_id,
                "timestamp": datetime.now().isoformat()
            }
        }

        # 广播到所有连接
        if game_id in self.active_connections:
            disconnected_players = []
            for player_id, connection in self.active_connections[game_id].items():
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"【错误/WebSocket】发送游戏结束消息时出错: {e}")
                    disconnected_players.append(player_id)

            # 清理断开的连接
            for player_id in disconnected_players:
                self.disconnect(game_id, player_id)

            return len(self.active_connections.get(game_id, {})) > 0
        return False


class AIPlayer:
    def __init__(self, player_id, name, personality, strategy_prompt=""):
        self.player_id = player_id
        self.name = name
        self.personality = personality
        self.strategy_prompt = strategy_prompt  # 玩家自定义策略 

    async def make_decision(self, game_state):
        # 组合系统提示词和玩家策略
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self.strategy_prompt},
            {"role": "user", "content": f"当前游戏状态: {game_state}"}
        ]
        # 调用LLM获取决策
        response = await llm_client.chat_completion(messages)
        # ... 


async def test_llm_and_prompts():
    # 创建示例提示词
    create_example_templates()

    # 获取提示词管理器
    prompt_manager = get_prompt_manager()

    # 测试提示词格式化
    system_prompt = prompt_manager.get_template("system_prompt")
    formatted_prompt = prompt_manager.format_prompt(
        "system_prompt",
        player_name="测试玩家",
        personality="谨慎且富有策略",
        game_rules="这是一个多人说服游戏，目标是获得最多的代币。"
    )

    print("=== 格式化后的提示词 ===")
    print(formatted_prompt)
    print("\n")

    # 测试LLM接口
    client = get_llm_client()

    print("=== 向LLM发送测试请求 ===")
    messages = [
        {"role": "system", "content": formatted_prompt},
        {"role": "user", "content": "游戏开始了，请介绍一下你自己和你的策略。"}
    ]

    try:
        response = await client.chat_completion(messages, temperature=0.7)
        text = client.extract_text_response(response)
        print(f"AI回复:\n{text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")
    finally:
        await client.close()


def test_game_record():
    # 创建GameRecord实例
    record = GameRecord()

    # 创建测试游戏数据
    test_game = {
        "game_id": "test_game_001",
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "players": [
            {"id": "p1", "name": "玩家1", "personality": "谨慎的"},
            {"id": "p2", "name": "玩家2", "personality": "冒险的"}
        ],
        "rounds": [
            {
                "round_number": 1,
                "phases": [
                    {
                        "phase_name": "道具阶段",
                        "actions": [
                            {
                                "action_type": "item_use",
                                "player_id": "p1",
                                "player_name": "玩家1",
                                "item_type": "情报卡",
                                "target": "玩家2"
                            }
                        ]
                    }
                ],
                "end_state": {
                    "current_round": 1,
                    "phase": "结算阶段",
                    "prize_pool": 20,
                    "players": [
                        {"id": "p1", "name": "玩家1", "balance": 95, "items": ["护盾卡"]},
                        {"id": "p2", "name": "玩家2", "balance": 105, "items": []}
                    ]
                }
            }
        ],
        "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_rounds": 1,
        "winner": "玩家2",
        "winner_id": "p2"
    }

    # 保存游戏记录
    filepath = record.save_game_record(test_game)
    print(f"游戏记录已保存到: {filepath}")

    # 列出所有记录
    all_records = record.list_game_records()
    print(f"所有游戏记录: {all_records}")

    # 读取最新的记录
    if all_records:
        latest_record = record.load_game_record(all_records[-1])
        print(f"读取记录成功，游戏ID: {latest_record.get('game_id')}")

        # 导出可读记录
        readable_path = record.export_readable_record(all_records[-1])
        print(f"可读记录已导出到: {readable_path}")

        # 获取游戏摘要
        summary = record.get_game_summary(all_records[-1])
        print("游戏摘要:")
        print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(test_llm_and_prompts())
    test_game_record()
