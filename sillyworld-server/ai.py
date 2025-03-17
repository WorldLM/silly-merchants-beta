from typing import List, Dict, Optional
import json
import httpx
from datetime import datetime
from models import Player, GameState, PersuasionRequest, GameAction, ItemType

class AISystem:
    def __init__(self, openrouter_api_key: str):
        # 使用httpx直接发送请求，避免OpenAI客户端的兼容性问题
        self.api_key = openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "openai/gpt-4o-mini"
        
    async def _make_openrouter_request(self, messages):
        """使用httpx直接调用OpenRouter API"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:  # 设置30秒超时
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 500  # 限制响应长度
                    }
                )
                return response.json()
        except Exception as e:
            print(f"API调用异常: {str(e)}")
            # 返回一个空响应，以便调用代码能继续执行
            return {
                "choices": [
                    {
                        "message": {
                            "content": "API调用超时或失败。思考过程：系统故障。决策：reject。回应：对不起，我现在无法处理这个请求。"
                        }
                    }
                ]
            }

    async def make_decision(
        self,
        player: Player,
        game_state: GameState,
        phase: str,
        available_actions: List[str]
    ) -> GameAction:
        # 构建更丰富的AI提示
        prompt = self._build_prompt(player, game_state, phase, available_actions)
        
        # 添加思考请求
        full_prompt = prompt + "\n\n请先思考当前局面和可能的策略，然后做出决策。格式如下：\n\n思考过程：\n[详细描述你的分析、考虑的因素和策略]\n\n决策：\n动作类型: [你选择的动作]\n目标玩家: [如果需要，选择一个目标玩家]\n金额: [如果需要，指定金额]\n道具类型: [如果需要，指定道具类型]\n\n对所有玩家的公开发言：\n[简短的发言，表达你的意图、威胁、请求或其他策略性对话]"
        
        # 调用OpenRouter API
        messages = [
            {"role": "system", "content": player.prompt},
            {"role": "user", "content": full_prompt}
        ]
        response_data = await self._make_openrouter_request(messages)
        
        # 解析AI响应
        response_content = response_data["choices"][0]["message"]["content"]
        decision_dict, thinking, public_message = self._parse_ai_response_with_thinking(response_content)
        
        # 创建GameAction对象
        action = GameAction(
            player_id=player.id,
            action_type=decision_dict.get("action_type", "wait"),
            target_player=decision_dict.get("target_player"),
            amount=decision_dict.get("amount"),
            item_type=decision_dict.get("item_type"),
            description=f"AI玩家 {player.name} 决定执行: {decision_dict.get('action_type', 'wait')}",
            timestamp=datetime.now(),
            thinking_process=thinking,  # 添加思考过程
            public_message=public_message  # 添加公开发言
        )
        
        # 首先记录AI的思考过程（仅显示，不实际执行）
        thinking_action = GameAction(
            player_id=player.id,
            action_type="ai_thinking",
            description=f"AI玩家 {player.name} 的思考过程",
            timestamp=datetime.now(),
            thinking_process=thinking,
            public_message=None
        )
        
        # 记录AI的公开发言（如果有）
        if public_message:
            speech_action = GameAction(
                player_id=player.id,
                action_type="ai_speech",
                description=f"AI玩家 {player.name} 对所有人说",
                timestamp=datetime.now(),
                thinking_process=None,
                public_message=public_message
            )
        
        return action

    def _build_prompt(
        self,
        player: Player,
        game_state: GameState,
        phase: str,
        available_actions: List[str]
    ) -> str:
        # 构建游戏状态描述
        game_info = f"""
        当前游戏状态：
        - 回合：{game_state.current_round}
        - 阶段：{phase}
        - 你的余额：{player.balance}
        - 奖池金额：{game_state.prize_pool}
        - 可用道具：{[item.type.value for item in player.items if not item.used]}
        - 其他玩家状态：
        {self._format_other_players(player, game_state)}
        
        可用动作：
        {', '.join(available_actions)}
        
        请根据你的策略选择一个动作。
        """
        
        return game_info

    def _format_other_players(self, player: Player, game_state: GameState) -> str:
        other_players = [p for p in game_state.players if p.id != player.id]
        return "\n".join([
            f"- 玩家 {p.name}: 余额 {p.balance}"
            for p in other_players
        ])

    def _parse_ai_response_with_thinking(self, response: str) -> tuple:
        # 解析更复杂的AI响应，包括思考过程和公开发言
        thinking = ""
        decision = {
            "action_type": "wait",
            "target_player": None,
            "amount": None,
            "item_type": None
        }
        public_message = ""
        
        try:
            # 尝试解析思考过程
            if "思考过程：" in response:
                thinking_parts = response.split("思考过程：", 1)
                if len(thinking_parts) > 1:
                    decision_parts = thinking_parts[1].split("决策：", 1)
                    if len(decision_parts) > 1:
                        thinking = decision_parts[0].strip()
            
            # 尝试解析决策部分
            if "决策：" in response:
                decision_section = response.split("决策：", 1)[1].split("对所有玩家的公开发言：", 1)[0]
                lines = [line.strip() for line in decision_section.strip().split("\n") if line.strip()]
                
                for line in lines:
                    if ":" in line or "：" in line:
                        parts = line.replace("：", ":").split(":", 1)
                        key = parts[0].strip().lower()
                        value = parts[1].strip() if len(parts) > 1 else ""
                        
                        if "动作类型" in key:
                            decision["action_type"] = value
                        elif "目标玩家" in key:
                            decision["target_player"] = value if value and value.lower() != "无" and value.lower() != "none" else None
                        elif "金额" in key:
                            try:
                                decision["amount"] = int(value) if value and value.isdigit() else None
                            except:
                                decision["amount"] = None
                        elif "道具类型" in key:
                            try:
                                if value and value.lower() not in ["无", "none", ""]:
                                    decision["item_type"] = ItemType(value.lower())
                            except:
                                decision["item_type"] = None
            
            # 尝试解析公开发言
            if "对所有玩家的公开发言：" in response:
                public_message = response.split("对所有玩家的公开发言：", 1)[1].strip()
        except Exception as e:
            print(f"解析AI响应出错: {e}")
        
        return decision, thinking, public_message

    async def evaluate_persuasion(
        self,
        target_player: Player,
        request: PersuasionRequest,
        game_state: GameState
    ) -> tuple:
        # 构建评估提示
        prompt = f"""
        你是一个AI玩家，需要评估是否接受一个说服请求。
        
        当前状态：
        - 你的余额：{target_player.balance}
        - 请求金额：{request.amount}
        - 请求消息：{request.message}
        - 其他玩家状态：
        {self._format_other_players(target_player, game_state)}
        
        请先思考这个请求的利弊，然后决定是否接受这个请求。
        
        格式如下：
        
        思考过程：
        [详细描述你的分析、考虑的因素和策略]
        
        决策：
        [accept或reject]
        
        回应：
        [给请求者的回应，解释你的决定]
        """
        
        # 调用OpenRouter API
        messages = [
            {"role": "system", "content": target_player.prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response_data = await self._make_openrouter_request(messages)
            
            # 检查响应是否有效
            if not response_data or "choices" not in response_data or not response_data["choices"]:
                print(f"获取到无效的AI响应: {response_data}")
                return False, "系统错误：获取到无效的AI响应", "我需要更多时间考虑，暂时拒绝这个请求。"
            
            # 解析响应
            response_content = response_data["choices"][0]["message"]["content"]
            
            # 解析思考过程、决策和回应
            thinking = ""
            decision = "reject"  # 默认拒绝
            response_message = ""
            
            try:
                if "思考过程：" in response_content:
                    parts = response_content.split("思考过程：", 1)[1]
                    
                    if "决策：" in parts:
                        thinking = parts.split("决策：", 1)[0].strip()
                        decision_part = parts.split("决策：", 1)[1]
                        
                        if "回应：" in decision_part:
                            decision = decision_part.split("回应：", 1)[0].strip().lower()
                            response_message = decision_part.split("回应：", 1)[1].strip()
                        else:
                            decision = decision_part.strip().lower()
                else:
                    # 如果找不到预期的格式，尝试简单解析
                    thinking = "无法识别标准格式，尝试简单解析..."
                    if "accept" in response_content.lower():
                        decision = "accept"
                        response_message = "我接受这个请求。"
                    else:
                        decision = "reject"
                        response_message = "我拒绝这个请求。"
            except Exception as e:
                print(f"解析说服评估响应出错: {e}")
                thinking = f"解析异常: {str(e)}"
                decision = "reject"
                response_message = "解析错误，默认拒绝请求。"
            
            print(f"AI决策结果: {decision}, 回应长度: {len(response_message) if response_message else 0}")
            return "accept" in decision, thinking, response_message
        except Exception as e:
            print(f"评估说服过程中发生异常: {str(e)}")
            return False, f"系统错误: {str(e)}", "系统故障，自动拒绝请求。" 