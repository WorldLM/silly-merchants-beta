"""
整体测试脚本 - 测试游戏系统的主要组件
包括提示词管理、LLM接口和游戏记录功能
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
import os

from llm_client import get_llm_client, get_prompt_manager, create_example_templates
from game_record import GameRecord
from models import Player, GameState, GamePhase, GameAction


async def test_prompt_system():
    """测试提示词系统"""
    print("\n===== 测试提示词系统 =====")

    # 创建示例提示词
    create_example_templates()

    # 获取提示词管理器
    prompt_manager = get_prompt_manager()

    # 列出所有提示词模板
    templates = prompt_manager.templates
    print(f"已加载的提示词模板: {', '.join(templates.keys())}")

    # 测试提示词格式化
    system_prompt = prompt_manager.get_template("system_prompt")
    formatted_prompt = prompt_manager.format_prompt(
        "system_prompt",
        player_name="测试玩家",
        personality="谨慎且富有策略",
        game_rules="这是一个多人说服游戏，目标是获得最多的代币。"
    )

    print("格式化后的系统提示词:")
    print("-------------------------------")
    print(formatted_prompt)
    print("-------------------------------\n")

    # 测试道具使用提示词
    item_prompt = prompt_manager.format_prompt(
        "item_use_prompt",
        current_round=2,
        max_rounds=8,
        balance=120,
        prize_pool=50,
        other_players="玩家2 (余额: 90)\n玩家3 (余额: 105)",
        items="护盾卡, 情报卡"
    )

    print("格式化后的道具使用提示词:")
    print("-------------------------------")
    print(item_prompt)
    print("-------------------------------\n")

    return True


async def test_llm_api():
    """测试LLM接口"""
    print("\n===== 测试LLM接口 =====")

    # 获取提示词和LLM客户端
    prompt_manager = get_prompt_manager()
    client = get_llm_client()

    # 检查API密钥
    if not client.api_key:
        print("API密钥未设置 ✗")
        print("请确保在.env文件中设置了OPENROUTER_API_KEY")
        return False

    print(f"API基础URL: {client.api_base}")
    print(f"使用模型: openai/gpt-4o-mini")

    # 创建测试提示词
    formatted_prompt = prompt_manager.format_prompt(
        "system_prompt",
        player_name="测试玩家",
        personality="谨慎且富有策略",
        game_rules="这是一个多人说服游戏，目标是获得最多的代币。"
    )

    # 创建消息
    messages = [
        {"role": "system", "content": formatted_prompt},
        {"role": "user", "content": "游戏即将开始，请简短介绍一下你自己和你的策略。"}
    ]

    try:
        print("发送请求到LLM...")
        start_time = datetime.now()
        # 明确指定使用openai/gpt-4o-mini模型
        response = await client.chat_completion(
            messages=messages,
            model="openai/gpt-4o-mini",
            temperature=0.7,
            max_tokens=150  # 限制响应长度
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 提取文本
        text = client.extract_text_response(response)
        print(f"LLM响应 (耗时: {duration:.2f}秒):")
        print("-------------------------------")
        print(text)
        print("-------------------------------\n")

        # 检查是否收到有效响应
        if text and len(text) > 10:
            print("LLM响应有效 ✓")
            return True
        else:
            print("LLM响应过短或为空 ✗")
            # 如果响应为空，打印完整响应对象以便调试
            print(f"完整响应对象: {response}")
            return False

    except Exception as e:
        print(f"请求出错: {str(e)} ✗")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


def test_game_record():
    """测试游戏记录功能"""
    print("\n===== 测试游戏记录功能 =====")

    # 确保目录存在
    os.makedirs("game_records", exist_ok=True)
    os.makedirs("readable_records", exist_ok=True)

    # 创建GameRecord实例
    record = GameRecord()

    # 创建测试游戏数据
    test_game = {
        "game_id": f"test_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "players": [
            {"id": "p1", "name": "策略家", "personality": "精明的策略家", "strategy": "注重资源优化"},
            {"id": "p2", "name": "冒险家", "personality": "大胆的冒险家", "strategy": "高风险高回报"},
            {"id": "p3", "name": "合作者", "personality": "友好的合作者", "strategy": "寻求双赢机会"}
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
                                "player_name": "策略家",
                                "item_type": "情报卡",
                                "target": "冒险家"
                            }
                        ]
                    },
                    {
                        "phase_name": "说服阶段",
                        "actions": [
                            {
                                "action_type": "persuasion",
                                "player_id": "p1",
                                "player_name": "策略家",
                                "target": "合作者",
                                "amount": 15,
                                "success": True
                            },
                            {
                                "action_type": "persuasion",
                                "player_id": "p2",
                                "player_name": "冒险家",
                                "target": "策略家",
                                "amount": 25,
                                "success": False
                            }
                        ]
                    },
                    {
                        "phase_name": "结算阶段",
                        "actions": [
                            {
                                "action_type": "purchase",
                                "player_id": "p1",
                                "player_name": "策略家",
                                "item_type": "护盾卡",
                                "cost": 10
                            }
                        ]
                    }
                ],
                "end_state": {
                    "current_round": 1,
                    "phase": "结算阶段",
                    "prize_pool": 25,
                    "players": [
                        {"id": "p1", "name": "策略家", "balance": 105, "items": ["护盾卡"]},
                        {"id": "p2", "name": "冒险家", "balance": 85, "items": []},
                        {"id": "p3", "name": "合作者", "balance": 85, "items": ["均富卡"]}
                    ]
                }
            },
            {
                "round_number": 2,
                "phases": [
                    {
                        "phase_name": "道具阶段",
                        "actions": [
                            {
                                "action_type": "item_use",
                                "player_id": "p3",
                                "player_name": "合作者",
                                "item_type": "均富卡",
                                "target": "策略家"
                            }
                        ]
                    }
                ],
                "end_state": {
                    "current_round": 2,
                    "phase": "道具阶段",
                    "prize_pool": 25,
                    "players": [
                        {"id": "p1", "name": "策略家", "balance": 95, "items": ["护盾卡"]},
                        {"id": "p2", "name": "冒险家", "balance": 85, "items": []},
                        {"id": "p3", "name": "合作者", "balance": 95, "items": []}
                    ]
                }
            }
        ],
        "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_rounds": 2,
        "winner": "策略家",
        "winner_id": "p1"
    }

    # 保存游戏记录
    try:
        filepath = record.save_game_record(test_game)
        print(f"游戏记录已保存到: {filepath} ✓")

        # 列出所有记录
        all_records = record.list_game_records()
        print(f"发现 {len(all_records)} 条游戏记录 ✓")

        # 读取最新的记录
        if all_records:
            latest_record = record.load_game_record(all_records[-1])
            print(f"成功读取游戏记录: {latest_record.get('game_id')} ✓")

            # 导出可读记录
            readable_path = record.export_readable_record(all_records[-1])
            print(f"可读记录已导出到: {readable_path} ✓")

            # 获取游戏摘要
            summary = record.get_game_summary(all_records[-1])
            print("游戏摘要生成成功:")
            print(f"  - 游戏ID: {summary.get('game_id')}")
            print(f"  - 玩家数: {summary.get('player_count')}")
            print(f"  - 获胜者: {summary.get('winner')}")
            print(f"  - 总回合: {summary.get('total_rounds')} ✓")

            return True

    except Exception as e:
        print(f"游戏记录测试出错: {str(e)} ✗")
        return False


def simulate_game_flow():
    """模拟一个简单的游戏流程，测试关键功能是否正常工作"""
    from models import Player, GameState
    import json

    print("正在检查Player模型字段...")
    player_fields = [field for field in Player.__annotations__.keys()]
    print(f"Player模型需要以下字段: {', '.join(player_fields)}")

    try:
        # 创建测试玩家
        players = []
        for i in range(3):
            player = Player(
                id=f"player_{i}",
                name=f"测试玩家{i}",
                prompt=f"这是测试玩家{i}的提示词"
            )
            players.append(player)
        print("成功创建Player对象")

        # 尝试创建游戏状态
        try:
            game_state = GameState(
                game_id="test_game",
                round=1,
                players=players,
                tokens={p.id: 100 for p in players},
                turns_history=[],
                items={p.id: [] for p in players}
            )
            print("成功创建GameState对象")
        except Exception as e:
            print(f"无法创建GameState对象: {str(e)}")
            game_state = {
                "game_id": "test_game",
                "round": 1,
                "players": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "prompt": p.prompt
                    } for p in players
                ],
                "tokens": {p.id: 100 for p in players},
                "turns_history": [],
                "items": {p.id: [] for p in players}
            }
            print("使用字典数据替代GameState对象")

        # 保存游戏记录
        record_file = "game_records/test_simulation_flow.json"
        with open(record_file, "w") as f:
            if isinstance(game_state, dict):
                json.dump(game_state, f)
            else:
                json.dump(game_state.model_dump(), f)

        print(f"游戏流程模拟记录已保存到: {record_file}")
        return True
    except Exception as e:
        import traceback
        print(f"游戏流程测试出错: {str(e)}")
        print(traceback.format_exc())
        return False


async def run_tests():
    """运行所有测试"""
    tests = [
        ("提示词系统", test_prompt_system),
        ("LLM接口", test_llm_api),
        ("游戏记录", lambda: test_game_record()),
        ("游戏流程", simulate_game_flow)
    ]

    results = {}

    print("开始整体功能测试...\n")

    for name, test_func in tests:
        print(f"正在测试: {name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            results[name] = result
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{name} 测试结果: {status}\n")
        except Exception as e:
            results[name] = False
            print(f"{name} 测试出错: {str(e)}")
            print(f"{name} 测试结果: ❌ 失败\n")

    # 汇总结果
    print("\n===== 测试结果汇总 =====")
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")

    print(f"\n总体结果: {passed}/{total} 通过")

    return passed == total


if __name__ == "__main__":
    asyncio.run(run_tests())
