from typing import List, Dict, Optional, Tuple, Any, Union
from datetime import datetime
import random
import logging
import re
import asyncio
from models import Player, GameState, PersuasionRequest, ItemType, GameAction, PersuasionData

# 确保AI类的定义与相关导入在文件顶部
class AI:
    """
    AI类，用于处理AI玩家的决策逻辑
    """
    def __init__(self, player):
        """
        初始化AI对象
        Args:
            player: Player对象，表示AI玩家
        """
        self.player = player
    
    async def _decide_persuasion(self, game_state) -> tuple:
        """
        AI决定说服哪位玩家，请求多少代币，以及发送什么消息。
        返回一个元组 (GameAction, thinking_process)
        """
        from models import GameAction
        
        print(f"【DEBUG/AI】{self.player.name} is deciding on persuasion")
        
        # 获取除自己外的活跃玩家
        other_players = [p for p in game_state.players if p.id != self.player.id and p.is_active]
        
        # 如果没有其他活跃玩家，跳过
        if not other_players:
            print(f"【DEBUG/AI】No other active players for {self.player.name} to persuade")
            dummy_action = GameAction(
                player_id=self.player.id,
                action_type="persuade",
                description=f"{self.player.name} found no one to persuade",
                timestamp=datetime.now(),
                persuasion_data=None
            )
            return dummy_action, "No other active players to persuade"
        
        # 选择余额最高的玩家作为目标
        target_player = max(other_players, key=lambda p: p.balance)
        
        # 计算请求金额（目标玩家余额的10-20%）
        request_percentage = random.uniform(0.1, 0.2)
        request_amount = max(1, min(20, int(target_player.balance * request_percentage)))
        
        # 生成说服消息
        messages = [
            f"Give me {request_amount} tokens, I'll remember next round.",
            f"Help me with {request_amount} tokens and I'll help you later.",
            f"Win-win, {request_amount} tokens will help me catch up.",
            f"Cooperation is key, {request_amount} tokens now will pay off.",
            f"Strategic alliance: {request_amount} tokens builds trust."
        ]
        message = random.choice(messages)
        
        # 用英文生成思考过程
        thinking = (
            f"AI player {self.player.name}'s thinking process for persuasion:\n\n"
            f"My current balance: {self.player.balance} tokens\n"
            f"Target player: {target_player.name} (balance: {target_player.balance} tokens)\n"
            f"Request amount: {request_amount} tokens ({request_percentage:.1%} of target's balance)\n"
            f"Persuasion message: \"{message}\"\n\n"
            f"Reasoning: I chose {target_player.name} because they have the highest balance "
            f"({target_player.balance} tokens) among active players. I'm requesting {request_amount} tokens, "
            f"which is a reasonable amount that won't significantly impact their position while "
            f"helping me. The message is designed to suggest mutual benefit and future reciprocity."
        )
        
        print(f"【DEBUG/AI】Generated thinking process for {self.player.name}, length: {len(thinking)}")
        print(f"【DEBUG/AI】First 100 chars: {thinking[:100]}")
        
        # 创建说服行动
        action = GameAction(
            player_id=self.player.id,
            action_type="persuade",
            description=f"{self.player.name} persuaded {target_player.name} for {request_amount} tokens",
            timestamp=datetime.now(),
            persuasion_data={
                'target_player': target_player.id,
                'amount': request_amount,
                'message': message
            },
            thinking_process=thinking  # 直接设置思考过程
        )
        
        print(f"【DEBUG/AI】Created persuasion action: type={action.action_type}, has_thinking={action.thinking_process is not None}")
        
        return action, thinking

    async def evaluate_persuasion(self, game_state, request) -> tuple:
        """
        AI评估说服请求并决定是否接受。
        返回一个元组 (is_accepted, thinking_process)
        """
        import random
        
        print(f"【DEBUG/AI】{self.player.name} is evaluating persuasion request from {request.from_name}")
        
        # 检查玩家是否有足够的余额
        if self.player.balance < request.amount:
            print(f"【DEBUG/AI】{self.player.name} rejected due to insufficient balance")
            thinking = (
                f"AI player {self.player.name}'s thinking process for evaluating persuasion:\n\n"
                f"Request from: {request.from_name}\n"
                f"Requested amount: {request.amount} tokens\n"
                f"My current balance: {self.player.balance} tokens\n"
                f"Message received: \"{request.message}\"\n\n"
                f"Decision: REJECT\n"
                f"Reasoning: I don't have enough tokens to fulfill this request. "
                f"My balance ({self.player.balance}) is less than the requested amount ({request.amount})."
            )
            return False, thinking
        
        # 基于性格和游戏状态的决策逻辑
        # 简单起见，如果请求金额小于余额30%，有40%的概率接受
        threshold = 0.3 * self.player.balance
        if request.amount <= threshold and random.random() < 0.4:
            is_accepted = True
        else:
            is_accepted = False
        
        # 用英文生成思考过程
        thinking = (
            f"AI player {self.player.name}'s thinking process for evaluating persuasion:\n\n"
            f"Request from: {request.from_name}\n"
            f"Requested amount: {request.amount} tokens\n"
            f"My current balance: {self.player.balance} tokens\n"
            f"Message received: \"{request.message}\"\n\n"
            f"Decision: {'ACCEPT' if is_accepted else 'REJECT'}\n"
            f"Reasoning: "
        )
        
        if is_accepted:
            thinking += (
                f"I decided to accept this request because:\n"
                f"- The requested amount ({request.amount}) is reasonable compared to my balance ({self.player.balance}).\n"
                f"- It's only {(request.amount / self.player.balance):.1%} of my total tokens.\n"
                f"- Building goodwill with {request.from_name} may benefit me in future rounds.\n"
                f"- Their message was persuasive and suggests future cooperation."
            )
        else:
            thinking += (
                f"I decided to reject this request because:\n"
                f"- The requested amount ({request.amount}) is too high compared to my balance ({self.player.balance}).\n"
                f"- Giving away {(request.amount / self.player.balance):.1%} of my tokens would weaken my position.\n"
                f"- I need to maintain a strong token reserve for future rounds.\n"
                f"- The benefit of potential future cooperation doesn't outweigh the immediate cost."
            )
        
        print(f"【DEBUG/AI】Generated evaluation thinking for {self.player.name}, decision: {is_accepted}")
        print(f"【DEBUG/AI】Thinking process length: {len(thinking)}")
        
        return is_accepted, thinking

# 以下是原始的AISystem类代码
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AI系统类，负责管理AI玩家的决策
class AISystem:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self._reflection_cache = {}
        self.prompt_manager = None
        logger.info("初始化AI系统")
    
    # 用于在各阶段为AI玩家生成决策
    async def make_decision(self, player: Player, game_state: GameState, phase: str, available_actions: List[str]) -> GameAction:
        """
        Generate a decision for the AI player
        """
        logger.info(f"Generating decision for AI player {player.name} in {phase} phase, available actions: {available_actions}")
        
        # Generate different decisions based on current phase
        if phase == "item_phase" and "use_item" in available_actions:
            # Decision for item usage phase
            decision = self._decide_item_usage(game_state, player)
        elif (phase == "preparation_phase" or phase == "preparation") and "buy_item" in available_actions:
            # Decision for item purchase in preparation phase
            decision = self._decide_item_purchase(game_state, player)
        elif (phase == "persuasion_phase" or phase == "persuasion") and "persuade" in available_actions:
            # Decision for persuasion phase
            try:
                # 创建AI实例
                ai_player = AI(player)
                # 调用AI的决策方法
                action, thinking = await ai_player._decide_persuasion(game_state)
                return action
            except Exception as e:
                print(f"ERROR in persuasion decision: {str(e)}")
                # 如果出错，返回一个默认决策
                return GameAction(
                    player_id=player.id,
                    action_type="none",
                    description=f"{player.name} skips persuasion (error occurred)",
                    timestamp=datetime.now()
                )
        else:
            # Default: no action
            decision = GameAction(
                player_id=player.id,
                action_type="none",
                description=f"{player.name} skips action",
                timestamp=datetime.now()
            )
            
        logger.info(f"AI player {player.name} in {phase} phase generated decision - action type: {decision.action_type}, " 
                   f"has thinking process: {'yes' if decision.thinking_process else 'no'}, "
                   f"thinking length: {len(decision.thinking_process) if decision.thinking_process else 0}")
        
        return decision
    
    def _decide_item_usage(self, game_state: GameState, player: Player) -> GameAction:
        """
        决定是否使用道具以及使用哪个道具
        """
        # 获取玩家拥有的未使用道具
        unused_items = [item for item in player.items if not item.used]
        
        if not unused_items:
            thinking = "没有可用的未使用道具"
            return GameAction(
                player_id=player.id,
                action_type="none",
                thinking_process=thinking,
                description=f"{player.name} 没有可用道具",
                timestamp=datetime.now()
            )
        
        # 分析游戏状态，确定是否需要使用道具
        other_players = [p for p in game_state.players if p.id != player.id and p.is_active]
        if not other_players:
            thinking = "没有其他活跃玩家可以作为道具目标"
            return GameAction(
                player_id=player.id,
                action_type="none",
                thinking_process=thinking,
                description=f"{player.name} 无法使用道具（没有目标）",
                timestamp=datetime.now()
            )
        
        # 随机选择一个道具使用
        item_to_use = random.choice(unused_items)
        target_player = random.choice(other_players)
        
        # 根据玩家资金情况和道具类型决定是否使用
        thinking = f"考虑使用{item_to_use.type.value}道具。我的余额: {player.balance}，目标玩家{target_player.name}余额: {target_player.balance}。"
        
        # 根据道具类型制定策略
        if item_to_use.type == ItemType.AGGRESSIVE:
            thinking += f"\n激进卡策略: 如果我的余额较高({player.balance})，使用此卡可以增加说服成功时的收益，风险是说服失败会有额外损失。"
            # 如果自己资金充足，更倾向于使用激进卡
            use_probability = 0.7 if player.balance > target_player.balance else 0.4
        
        elif item_to_use.type == ItemType.SHIELD:
            thinking += f"\n护盾卡策略: 如果我的余额较低({player.balance})或预期会被多人说服，使用此卡可以减少损失。"
            # 如果自己资金较少，更倾向于使用护盾卡
            use_probability = 0.8 if player.balance < target_player.balance else 0.5
        
        elif item_to_use.type == ItemType.INTEL:
            thinking += f"\n情报卡策略: 了解目标玩家的部分提示信息，有助于判断其行动模式和策略倾向。"
            # 情报卡在任何情况下都有用
            use_probability = 0.75
        
        elif item_to_use.type == ItemType.EQUALIZER:
            thinking += f"\n均富卡策略: 如果目标玩家余额远高于我({target_player.balance} vs {player.balance})，使用此卡可以平衡资金差距。"
            # 如果目标玩家资金远高于自己，更倾向于使用均富卡
            use_probability = 0.9 if target_player.balance > player.balance * 1.5 else 0.3
        
        else:
            use_probability = 0.5
        
        # 根据策略概率决定是否使用道具（提高到80%概率使用道具）
        if random.random() < 0.8:
            # 生成有关使用道具的公开消息
            public_message = self._generate_item_use_message(item_to_use.type, target_player.name)
            
            thinking += f"\n决定使用{item_to_use.type.value}道具，目标是{target_player.name}。"
            return GameAction(
                player_id=player.id,
                action_type="use_item",
                target_player=target_player.id,
                item_type=item_to_use.type,
                thinking_process=thinking,
                public_message=public_message,
                description=f"{player.name} 对 {target_player.name} 使用了 {item_to_use.type.value} 道具",
                timestamp=datetime.now()
            )
        else:
            thinking += f"\n决定本回合暂不使用道具，保留到更适合的时机。"
            return GameAction(
                player_id=player.id,
                action_type="none",
                thinking_process=thinking,
                description=f"{player.name} 选择不使用道具",
                timestamp=datetime.now()
            )
    
    # 用于生成道具使用后的公开消息
    def _generate_item_use_message(self, item_type: ItemType, target_name: str) -> str:
        """生成使用道具后的公开消息"""
        messages = {
            ItemType.AGGRESSIVE: [
                f"Launching offensive on {target_name}!",
                f"You'd better be careful, {target_name}",
                f"I'm going to win this round!"
            ],
            ItemType.SHIELD: [
                "Defense is ready!",
                "No one can take my money",
                "A solid defense is my style"
            ],
            ItemType.INTEL: [
                f"I can see through you, {target_name}",
                f"Got intelligence on {target_name}",
                "Information is power"
            ],
            ItemType.EQUALIZER: [
                f"{target_name}, prepare to share your wealth",
                "Wealth gap should be eliminated",
                "Resources should be distributed more evenly"
            ]
        }
        
        return random.choice(messages.get(item_type, ["Using item..."]))
    
    def _decide_item_purchase(self, game_state: GameState, player: Player) -> GameAction:
        """
        决定是否购买道具以及购买哪个道具
        """
        # 获取玩家已拥有的道具类型
        owned_item_types = set(item.type for item in player.items)
        
        # 获取所有可购买的道具类型（排除已拥有的）
        available_item_types = [
            item_type for item_type in [ItemType.AGGRESSIVE, ItemType.SHIELD, 
                                       ItemType.INTEL, ItemType.EQUALIZER]
            if item_type not in owned_item_types
        ]
        
        if not available_item_types:
            thinking = "Already have all types of items, no need to purchase more."
            logger.info(f"[AI Thinking] Player {player.name} - {thinking}")
            return GameAction(
                player_id=player.id,
                action_type="none",
                thinking_process=thinking,
                description=f"{player.name} didn't purchase any items",
                timestamp=datetime.now()
            )
        
        # 分析当前游戏状态，决定是否购买道具
        thinking = f"Preparation phase: considering item purchase. My balance: {player.balance}, owned item types: {[item.type.value for item in player.items]}"
        
        # 计算购买概率，余额越多购买概率越高
        buy_probability = min(0.7, player.balance / 100)  # 余额100时有70%概率购买
        
        if random.random() < buy_probability:
            # 随机选择一个道具类型购买
            item_type_to_buy = random.choice(available_item_types)
            
            # 道具价格（简单起见，所有道具价格相同）
            price = 10  # 假设所有道具价格为10代币
            
            # 如果余额足够，购买该道具
            if player.balance >= price:
                thinking += f"\nDecided to purchase {item_type_to_buy.value} item, price: {price} tokens."
                
                # 生成购买道具后的公开消息
                public_message = self._generate_item_purchase_message(item_type_to_buy)
                
                logger.info(f"[AI Thinking] Player {player.name} - {thinking}")
                
                decision = GameAction(
                    player_id=player.id,
                    action_type="buy_item",
                    item_type=item_type_to_buy,
                    amount=price,
                    thinking_process=thinking,
                    public_message=public_message,
                    description=f"{player.name} purchased {item_type_to_buy.value} item for {price} tokens",
                    timestamp=datetime.now()
                )
                logger.info(f"[AI Decision] Generated decision - Player:{player.name}, Action:{decision.action_type}, Thinking process length:{len(thinking) if thinking else 0}")
                return decision
            else:
                thinking += f"\nInsufficient balance ({player.balance}), can't afford item with price {price}."
        else:
            thinking += "\nDecided not to purchase items this round, keeping funds for other purposes."
        
        logger.info(f"[AI Thinking] Player {player.name} - {thinking}")
        
        decision = GameAction(
            player_id=player.id,
            action_type="none",
            thinking_process=thinking,
            description=f"{player.name} didn't purchase any items",
            timestamp=datetime.now()
        )
        logger.info(f"[AI Decision] Generated decision - Player:{player.name}, Action:{decision.action_type}, Thinking process length:{len(thinking) if thinking else 0}")
        return decision
    
    # 用于生成购买道具后的公开消息
    def _generate_item_purchase_message(self, item_type: ItemType) -> str:
        """生成购买道具后的公开消息"""
        messages = {
            ItemType.AGGRESSIVE: [
                "Offensive item acquired, ready to act!",
                "This item will give me an advantage",
                "Attack is the best defense"
            ],
            ItemType.SHIELD: [
                "Defense item purchase complete",
                "Safety first",
                "Now I have protection"
            ],
            ItemType.INTEL: [
                "Intelligence gathering tool ready",
                "Know your enemy, know yourself",
                "Information is the foundation of strategy"
            ],
            ItemType.EQUALIZER: [
                "Equalizer item acquired",
                "Ready to adjust wealth distribution",
                "This will be an interesting turning point"
            ]
        }
        
        return random.choice(messages.get(item_type, ["Item purchase successful"]))
    
    async def reflect_on_players(self, player: Player, other_player: Player, game_state: GameState, player_actions: List[Dict[str, Any]]) -> str:
        """简化版的玩家行为分析"""
        return f"分析 {other_player.name} 的行为: 余额 {other_player.balance} 代币"
    
    async def apply_reflection_to_decision(self, player: Player, game_state: GameState, phase: str, available_actions: List[str], reflections: Dict[str, str]) -> GameAction:
        """根据反思结果应用到决策中"""
        return await self.make_decision(player, game_state, phase, available_actions)
    
    def _get_phase_description(self, phase: str) -> str:
        """获取阶段描述"""
        descriptions = {
            "preparation_phase": "准备阶段，可以购买道具",
            "item_phase": "道具阶段，可以使用道具影响游戏",
            "persuasion_phase": "说服阶段，可以尝试说服其他玩家转移资金",
            "settlement_phase": "结算阶段，处理所有转账请求",
            "event_phase": "事件阶段，随机事件可能影响游戏",
            "statistics_phase": "统计阶段，查看游戏状态"
        }
        return descriptions.get(phase, f"未知阶段: {phase}")
    
    def _build_reflection_prompt(self, player: Player, target_player: Player, game_state: GameState, target_actions: List[Dict[str, Any]]) -> str:
        """构建反思提示词"""
        return f"分析玩家 {target_player.name} 的行为模式。"
