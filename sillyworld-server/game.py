from typing import List, Dict, Optional
from datetime import datetime
import uuid
from models import (
    GameState, Player, GamePhase, GameAction,
    PersuasionRequest, GameResult, ItemType
)
from items import ItemSystem
from ai import AISystem

class Game:
    def __init__(self, ai_system: AISystem):
        self.ai_system = ai_system
        self.games: Dict[str, GameState] = {}
        self.player_item_types: Dict[str, Dict[str, set]] = {}  # 用于跟踪每位玩家在每局游戏中已购买的道具类型
        self.round_item_usage: Dict[str, Dict[str, bool]] = {}  # 用于跟踪每个回合中玩家是否已使用道具
        self.game_preparation: Dict[str, bool] = {}  # 用于跟踪游戏是否处于准备阶段
        
        # 用于跟踪特殊道具的使用情况
        self.aggressive_users: Dict[str, set] = {}  # 激进卡使用者
        self.shield_users: Dict[str, set] = {}  # 护盾卡使用者
        self.equalizer_users: Dict[str, set] = {}  # 均富卡使用者
        self.equalizer_targets: Dict[str, Dict[str, str]] = {}  # 均富卡目标

    def create_game(self, players: List[Player]) -> GameState:
        if len(players) < 2:
            raise ValueError("Game requires at least 2 players")

        # 创建新游戏
        game_id = str(uuid.uuid4())
        
        # 计算初始奖池资金（仅包含门票费）
        initial_prize_pool = len(players) * 10  # 每人10代币门票费
        
        # 扣除门票费用
        for player in players:
            player.balance -= 10

        game_state = GameState(
            game_id=game_id,
            phase=GamePhase.ITEM_PHASE,
            players=players,
            start_time=datetime.now(),
            last_update=datetime.now(),
            prize_pool=initial_prize_pool,
            total_resources=initial_prize_pool + sum(player.balance for player in players)  # 总资源 = 奖池 + 所有玩家资金
        )
        
        # 初始化该游戏的道具跟踪器
        self.player_item_types[game_id] = {player.id: set() for player in players}
        self.round_item_usage[game_id] = {player.id: False for player in players}
        # 设置游戏为准备阶段
        self.game_preparation[game_id] = True

        self.games[game_id] = game_state
        return game_state

    # 添加公共方法，检查游戏是否结束
    def check_game_end(self, game_id: str) -> bool:
        game_state = self.games.get(game_id)
        if not game_state:
            return False
        active_players = [p for p in game_state.players if p.is_active]
        return len(active_players) <= 1

    # 添加公共方法，处理游戏结束
    async def end_game(self, game_id: str) -> List[GameAction]:
        game_state = self.games.get(game_id)
        if not game_state:
            return []
        return await self._end_game(game_state)

    # 添加公共方法，处理道具阶段
    async def process_item_phase(self, game_id: str) -> List[GameAction]:
        game_state = self.games.get(game_id)
        if not game_state:
            return []
        
        # 重置每个回合的道具使用跟踪 - 确保在每个回合开始时重置
        if game_id in self.round_item_usage:
            self.round_item_usage[game_id] = {player.id: False for player in game_state.players}
            print(f"【调试/Game】已重置所有玩家的道具使用跟踪，本回合都可以使用道具")
        else:
            # 如果不存在，创建它
            self.round_item_usage[game_id] = {player.id: False for player in game_state.players}
            print(f"【调试/Game】初始化道具使用跟踪字典")
            
        return await self._process_item_phase(game_state)

    # 添加公共方法，处理说服阶段
    async def process_persuasion_phase(self, game_id: str) -> List[GameAction]:
        game_state = self.games.get(game_id)
        if not game_state:
            return []
        return await self._process_persuasion_phase(game_state)

    # 添加公共方法，处理结算阶段
    async def process_settlement_phase(self, game_id: str) -> List[GameAction]:
        game_state = self.games.get(game_id)
        if not game_state:
            return []
        return await self._process_settlement_phase(game_state)

    # 添加公共方法，处理统计阶段
    async def process_statistics_phase(self, game_id: str) -> List[GameAction]:
        game_state = self.games.get(game_id)
        if not game_state:
            return []
        return await self._process_statistics_phase(game_state)

    async def process_round(self, game_id: str) -> List[GameAction]:
        """处理一轮游戏"""
        print(f"【调试/Game】开始处理回合: 游戏ID={game_id}")
        game_state = self.games.get(game_id)
        if not game_state or not game_state.is_active:
            print(f"【错误/Game】游戏不存在或未激活: 游戏ID={game_id}, 状态={game_state.status if game_state else 'None'}")
            raise ValueError("Game not found or not active")

        actions = []  # 用于记录本回合的所有动作
        print(f"【调试/Game】游戏当前状态: 回合={game_state.current_round}, 阶段={game_state.phase}, 玩家数={len(game_state.players)}")

        # 重置每个回合的道具使用跟踪 - 确保在每个回合开始时重置
        if game_id in self.round_item_usage:
            self.round_item_usage[game_id] = {player.id: False for player in game_state.players}
            print(f"【调试/Game】已重置所有玩家的道具使用跟踪，本回合都可以使用道具")
        else:
            # 如果不存在，创建它
            self.round_item_usage[game_id] = {player.id: False for player in game_state.players}
            print(f"【调试/Game】初始化道具使用跟踪字典")
            
        # 处理均富卡效果（在回合开始时执行）
        if game_id in self.equalizer_users and self.equalizer_users[game_id] and game_id in self.equalizer_targets:
            equalizer_actions = []
            for player_id in list(self.equalizer_users[game_id]):
                # 检查玩家是否仍然活跃
                player = next((p for p in game_state.players if p.id == player_id and p.is_active), None)
                if not player:
                    continue
                    
                # 获取目标玩家
                target_id = self.equalizer_targets[game_id].get(player_id)
                target_player = next((p for p in game_state.players if p.id == target_id and p.is_active), None)
                
                if target_player:
                    # 记录初始余额
                    player_balance = player.balance
                    target_balance = target_player.balance
                    
                    # 计算平均值
                    total = player_balance + target_balance
                    each = total // 2
                    
                    # 更新余额
                    player.balance = each
                    target_player.balance = each
                    
                    # 记录动作
                    action = GameAction(
                        player_id=player.id,
                        action_type="equalizer_effect",
                        target_player=target_player.id,
                        description=f"均富卡生效：玩家 {player.name} 和 {target_player.name} 平分资金 (从 {player_balance}/{target_balance} 变为 {each}/{each})",
                        timestamp=datetime.now()
                    )
                    equalizer_actions.append(action)
                    print(f"【调试/Game】均富卡生效: 玩家 {player.name} 和 {target_player.name} 平分资金")
                
                # 从集合中移除已处理的玩家
                self.equalizer_users[game_id].remove(player_id)
                if player_id in self.equalizer_targets[game_id]:
                    del self.equalizer_targets[game_id][player_id]
            
            # 添加均富卡动作到总动作列表
            actions.extend(equalizer_actions)

        # 1. 道具使用阶段
        print(f"【调试/Game】开始道具阶段: 游戏ID={game_id}")
        item_actions = await self._process_item_phase(game_state)
        actions.extend(item_actions)
        print(f"【调试/Game】道具阶段完成: 动作数={len(item_actions)}, 新阶段={game_state.phase}")

        # 2. 说服阶段
        print(f"【调试/Game】开始说服阶段: 游戏ID={game_id}")
        persuasion_actions = await self._process_persuasion_phase(game_state)
        actions.extend(persuasion_actions)
        print(f"【调试/Game】说服阶段完成: 动作数={len(persuasion_actions)}, 新阶段={game_state.phase}")

        # 3. 结算阶段
        print(f"【调试/Game】开始结算阶段: 游戏ID={game_id}")
        settlement_actions = await self._process_settlement_phase(game_state)
        actions.extend(settlement_actions)
        print(f"【调试/Game】结算阶段完成: 动作数={len(settlement_actions)}, 新阶段={game_state.phase}")

        # 4. 统计阶段
        print(f"【调试/Game】开始统计阶段: 游戏ID={game_id}")
        statistics_actions = await self._process_statistics_phase(game_state)
        actions.extend(statistics_actions)
        print(f"【调试/Game】统计阶段完成: 动作数={len(statistics_actions)}, 新阶段={game_state.phase}")

        # 更新游戏状态
        game_state.current_round += 1
        game_state.last_update = datetime.now()
        print(f"【调试/Game】回合结束，更新游戏状态: 回合={game_state.current_round}, 阶段={game_state.phase}")

        # 检查游戏是否结束
        is_game_end = self._check_game_end(game_state)
        print(f"【调试/Game】检查游戏是否结束: 结果={is_game_end}")
        if is_game_end:
            print(f"【调试/Game】游戏结束条件满足，执行结束流程: 游戏ID={game_id}")
            end_actions = await self._end_game(game_state)
            actions.extend(end_actions)
            print(f"【调试/Game】游戏结束流程完成: 动作数={len(end_actions)}")

        print(f"【调试/Game】回合处理完成: 游戏ID={game_id}, 总动作数={len(actions)}")
        return actions

    async def _process_item_phase(self, game_state: GameState) -> List[GameAction]:
        print(f"【调试/Game】进入道具阶段处理函数，当前阶段={game_state.phase}")
        # 设置当前阶段
        game_state.phase = GamePhase.ITEM_PHASE
        actions = []

        # 获取游戏是否在准备阶段
        is_preparation = self.game_preparation.get(game_state.game_id, False)
        
        # 在每个回合开始时打印道具和状态
        for player in game_state.players:
            if player.is_active:
                items_info = "，".join([f"{item.type.value}" + ("(已使用)" if item.used else "") for item in player.items]) if player.items else "无"
                print(f"【调试/Game】玩家 {player.name} 道具状态: {items_info}")
                # 确保round_item_usage正确初始化
                if game_state.game_id in self.round_item_usage and player.id in self.round_item_usage[game_state.game_id]:
                    print(f"【调试/Game】玩家 {player.name} 在本回合是否已使用道具: {self.round_item_usage[game_state.game_id][player.id]}")
        
        # 收集所有玩家的道具使用动作
        for player in game_state.players:
            if not player.is_active:
                continue
                
            # 只有在准备阶段才允许购买道具
            if is_preparation and player.balance >= 10:
                # 检查玩家是否已达到3个不同类型道具的限制
                player_items = self.player_item_types.get(game_state.game_id, {}).get(player.id, set())
                if len(player_items) < 3:  # 如果还没有达到3种不同类型的上限
                    # 获取AI的思考过程和决策
                    available_actions = ["buy_item"]
                    decision = await self.ai_system.make_decision(
                        player=player,
                        game_state=game_state,
                        phase="preparation",
                        available_actions=available_actions
                    )
                    
                    # 记录AI的思考过程(只对玩家可见)
                    if decision.thinking_process:
                        thinking_action = GameAction(
                            player_id=player.id,
                            action_type="ai_thinking",
                            description=f"AI玩家 {player.name} 的道具选择思考过程",
                            timestamp=datetime.now(),
                            thinking_process=decision.thinking_process,
                            public_message=None
                        )
                        actions.append(thinking_action)
                        print(f"【调试/Game】记录AI道具选择思考过程: {player.name}")
                        
                    # 随机选择道具类型(玩家不应该知道选择了什么具体道具)
                    item_type = ItemSystem.get_random_item()
                    
                    # 确保不重复购买同一类型的道具
                    attempts = 0
                    while item_type.value in player_items and attempts < 10:  # 防止无限循环
                        item_type = ItemSystem.get_random_item()
                        attempts += 1
                    
                    if item_type.value not in player_items or attempts >= 10:  # 如果找到了新类型或尝试次数过多
                        cost = ItemSystem.ITEM_PRICES[item_type]  # 使用道具类型对应的价格
                        
                        # 检查玩家余额是否足够
                        if player.balance < cost:
                            print(f"【调试/Game】玩家 {player.name} 余额不足，无法购买道具 {item_type.value}，价格: {cost}，当前余额: {player.balance}")
                            continue

                        # 从玩家余额中扣除成本
                        player.balance -= cost
                        # 购买道具的资金正确流入奖池
                        game_state.prize_pool += cost
                        
                        # 添加道具到玩家库存
                        item = ItemSystem.create_item(item_type)
                        player.items.append(item)
                        
                        # 记录玩家已购买的道具类型
                        if game_state.game_id in self.player_item_types and player.id in self.player_item_types[game_state.game_id]:
                            self.player_item_types[game_state.game_id][player.id].add(item_type.value)
                        
                        # 记录动作但不指明具体道具类型(对其他AI保密)
                        action = GameAction(
                            player_id=player.id,
                            action_type="buy_item",
                            amount=cost,
                            item_type=item_type,  # 这个信息只对玩家可见，不会广播给其他AI
                            description=f"玩家 {player.name} 花费 {cost} 代币购买了一个道具，当前余额: {player.balance}",
                            timestamp=datetime.now()
                        )
                        actions.append(action)
                        
                        # 玩家的公开发言(如果有)
                        if decision.public_message:
                            speech_action = GameAction(
                                player_id=player.id,
                                action_type="ai_speech",
                                description=f"AI玩家 {player.name} 购买道具后说",
                                timestamp=datetime.now(),
                                thinking_process=None,
                                public_message=decision.public_message
                            )
                            actions.append(speech_action)
                            print(f"【调试/Game】记录AI购买道具后发言: {player.name}说: {decision.public_message}")
                        
                        print(f"【调试/Game】玩家 {player.name} 花费 {cost} 代币购买了道具: {item_type.value}")
            
            # 游戏开始后，玩家可以使用道具，但每轮只能使用一个
            if not is_preparation and player.items and len(player.items) > 0:
                # 检查该玩家是否已在本回合使用过道具
                has_used_item_this_round = self.round_item_usage.get(game_state.game_id, {}).get(player.id, True)
                print(f"【调试/Game】检查玩家 {player.name} 是否已在本回合使用过道具: {has_used_item_this_round}")
                
                # 只有当玩家在本回合还没有使用过道具时才考虑使用
                if not has_used_item_this_round:
                    # 筛选出未使用的道具
                    unused_items = [item for item in player.items if not item.used]
                    print(f"【调试/Game】玩家 {player.name} 有 {len(unused_items)} 个未使用的道具")
                    
                    if unused_items:
                        # 获取AI对使用道具的思考与决策
                        available_actions = ["use_item"]
                        decision = await self.ai_system.make_decision(
                            player=player,
                            game_state=game_state,
                            phase="item_usage",
                            available_actions=available_actions
                        )
                        
                        # 记录AI的思考过程(只对玩家可见)
                        if decision.thinking_process:
                            thinking_action = GameAction(
                                player_id=player.id,
                                action_type="ai_thinking",
                                description=f"AI玩家 {player.name} 的道具使用思考过程",
                                timestamp=datetime.now(),
                                thinking_process=decision.thinking_process,
                                public_message=None
                            )
                            actions.append(thinking_action)
                            print(f"【调试/Game】记录AI道具使用思考过程: {player.name}")
                        
                        # 简单随机，70%几率使用一个道具，提高互动频率
                        import random
                        if random.random() > 0.3 or (decision.action_type == "use_item"):
                            item_to_use = random.choice(unused_items)
                            print(f"【调试/Game】AI选择使用道具: {item_to_use.type.value}")
                            
                            # 标记道具为已使用
                            item_to_use.used = True
                            
                            # 标记该玩家在本回合已使用道具，确保每轮只使用一个道具
                            if game_state.game_id in self.round_item_usage:
                                self.round_item_usage[game_state.game_id][player.id] = True
                                print(f"【调试/Game】标记玩家 {player.name} 在本回合已使用道具")
                            
                            # 随机选择一个目标玩家
                            other_players = [p for p in game_state.players if p.id != player.id and p.is_active]
                            if other_players:
                                # 使用决策中的目标玩家，或随机选择
                                target_id = decision.target_player if decision.target_player else random.choice(other_players).id
                                target_player = next((p for p in other_players if p.id == target_id), random.choice(other_players))
                                
                                effect_description = ""
                                
                                # 根据道具类型应用效果
                                if item_to_use.type == ItemType.AGGRESSIVE:
                                    # 激进卡：标记玩家使用了激进卡，说服失败时将受到额外惩罚（在说服阶段处理）
                                    # 为玩家添加标记，稍后在说服阶段使用
                                    if game_state.game_id not in self.aggressive_users:
                                        self.aggressive_users[game_state.game_id] = set()
                                    self.aggressive_users[game_state.game_id].add(player.id)
                                    effect_description = f"激活攻击策略，若本轮说服失败将额外损失 {item_to_use.price} 代币作为惩罚，若成功则无额外奖励"
                                
                                elif item_to_use.type == ItemType.SHIELD:
                                    # 护盾卡：标记玩家使用了护盾，在被说服时支付金额减半（在说服阶段处理）
                                    # 为玩家添加标记，稍后在说服阶段使用
                                    if game_state.game_id not in self.shield_users:
                                        self.shield_users[game_state.game_id] = set()
                                    self.shield_users[game_state.game_id].add(player.id)
                                    effect_description = f"激活防护盾，若本轮被其他玩家成功说服，需要支付的代币减半(50%)"
                                    
                                elif item_to_use.type == ItemType.INTEL:
                                    # 情报卡：查看目标玩家的Prompt信息片段
                                    # 随机获取Prompt的一部分信息（取前1/3部分）
                                    prompt_part = target_player.prompt[:len(target_player.prompt)//3] + "..."
                                    effect_description = f"获取了 {target_player.name} 的隐藏信息片段: '{prompt_part}'，用于猜测对方的策略倾向"
                                    
                                elif item_to_use.type == ItemType.EQUALIZER:
                                    # 均富卡：将在下一轮开始时与当前资金最多的玩家平分资金
                                    # 为玩家添加标记，稍后在下一轮开始时处理
                                    if game_state.game_id not in self.equalizer_users:
                                        self.equalizer_users[game_state.game_id] = set()
                                    self.equalizer_users[game_state.game_id].add(player.id)
                                    
                                    # 找到当前资金最多的玩家(排除自己)
                                    richest_player = max(
                                        [p for p in game_state.players if p.id != player.id and p.is_active], 
                                        key=lambda p: p.balance
                                    )
                                    
                                    # 记录目标玩家，以便在下一轮开始时使用
                                    if game_state.game_id not in self.equalizer_targets:
                                        self.equalizer_targets[game_state.game_id] = {}
                                    self.equalizer_targets[game_state.game_id][player.id] = richest_player.id
                                    
                                    effect_description = f"选择了 {richest_player.name} 作为均富目标，将在下一轮开始时与其平分两人的资金总额"
                                
                                # 记录动作
                                action = GameAction(
                                    player_id=player.id,
                                    action_type="use_item",
                                    item_type=item_to_use.type,
                                    target_player=target_player.id,
                                    description=f"玩家 {player.name} 对 {target_player.name} 使用了道具: {item_to_use.type.value}，{effect_description}",
                                    timestamp=datetime.now()
                                )
                                actions.append(action)
                                
                                # 玩家的公开发言(如果有)
                                if decision.public_message:
                                    speech_action = GameAction(
                                        player_id=player.id,
                                        action_type="ai_speech",
                                        description=f"AI玩家 {player.name} 使用道具后说",
                                        timestamp=datetime.now(),
                                        thinking_process=None,
                                        public_message=decision.public_message
                                    )
                                    actions.append(speech_action)
                                    print(f"【调试/Game】记录AI使用道具后发言: {player.name}说: {decision.public_message}")
                                
                                print(f"【调试/Game】玩家 {player.name} 对 {target_player.name} 使用了道具: {item_to_use.type.value}，效果: {effect_description}")
                    else:
                        print(f"【调试/Game】玩家 {player.name} 没有可用未使用的道具")
                else:
                    print(f"【调试/Game】玩家 {player.name} 在本回合已经使用过道具，跳过")
        
        # 确保阶段更新：在处理完道具阶段后，强制进入说服阶段
        game_state.phase = GamePhase.PERSUASION_PHASE
        print(f"【调试/Game】道具阶段处理完成，设置下一阶段={game_state.phase}")
        
        return actions

    async def _process_persuasion_phase(self, game_state: GameState) -> List[GameAction]:
        print(f"【调试/Game】进入说服阶段处理函数，当前阶段={game_state.phase}")
        game_state.phase = GamePhase.PERSUASION_PHASE
        actions = []
        
        # 活跃玩家
        active_players = [p for p in game_state.players if p.is_active]
        
        # 如果只有一名玩家活跃，跳过说服阶段
        if len(active_players) <= 1:
            print(f"【调试/Game】有效玩家数量不足，跳过说服阶段")
            game_state.phase = GamePhase.SETTLEMENT_PHASE
            return actions
            
        # 每个活跃玩家轮流获得发起说服的机会
        for player in active_players:
            # 假设所有玩家都是AI玩家
            # 随机决定是否发起说服 (70%概率)
            import random
            if random.random() > 0.3:
                # 随机选择目标玩家
                other_players = [p for p in active_players if p.id != player.id]
                if not other_players:
                    continue
                    
                target_player = random.choice(other_players)
                
                # 确定说服金额 (随机5-20代币之间)
                amount = random.randint(5, min(20, target_player.balance))
                
                # 构建AI提示，让AI生成说服请求
                available_actions = ["persuade"]
                decision = await self.ai_system.make_decision(
                    player=player,
                    game_state=game_state,
                    phase="persuasion",
                    available_actions=available_actions
                )
                
                if decision.action_type == "persuade":
                    # 添加AI思考过程的记录，但这不会广播给所有玩家
                    if decision.thinking_process:
                        thinking_action = GameAction(
                            player_id=player.id,
                            action_type="ai_thinking",
                            description=f"AI玩家 {player.name} 的思考过程",
                            timestamp=datetime.now(),
                            thinking_process=decision.thinking_process,
                            public_message=None
                        )
                        actions.append(thinking_action)
                        print(f"【调试/Game】记录AI思考过程: {player.name}")
                    
                    # 如果AI有公开发言，记录并广播它
                    public_speech = None
                    if decision.public_message:
                        speech_action = GameAction(
                            player_id=player.id,
                            action_type="ai_speech",
                            description=f"AI玩家 {player.name} 对所有人说",
                            timestamp=datetime.now(),
                            thinking_process=None,
                            public_message=decision.public_message
                        )
                        actions.append(speech_action)
                        public_speech = decision.public_message
                        print(f"【调试/Game】记录AI公开发言: {player.name}说: {decision.public_message}")
                    
                    # 生成说服消息，使用AI提供的公开发言或默认消息
                    persuasion_message = public_speech if public_speech else f"我提议你转给我 {amount} 代币。这对我们双方都有利!"
                    
                    # 创建说服请求
                    request = PersuasionRequest(
                        from_player=player.id,
                        to_player=target_player.id,
                        amount=amount,
                        message=persuasion_message,
                        timestamp=datetime.now()
                    )
                    
                    # 让目标AI评估是否接受
                    is_accepted, thinking, response_message = await self.ai_system.evaluate_persuasion(
                        target_player=target_player,
                        request=request,
                        game_state=game_state
                    )
                    
                    # 设置接受状态
                    request.accepted = is_accepted
                    
                    # 添加到游戏状态中
                    game_state.persuasion_requests.append(request)
                    
                    # 记录目标AI的思考过程
                    if thinking:
                        target_thinking_action = GameAction(
                            player_id=target_player.id,
                            action_type="ai_thinking",
                            description=f"AI玩家 {target_player.name} 的思考过程",
                            timestamp=datetime.now(),
                            thinking_process=thinking,
                            public_message=None
                        )
                        actions.append(target_thinking_action)
                        print(f"【调试/Game】记录目标AI思考过程: {target_player.name}")
                    
                    # 记录目标AI的回应发言
                    if response_message:
                        target_speech_action = GameAction(
                            player_id=target_player.id,
                            action_type="ai_speech",
                            description=f"AI玩家 {target_player.name} 回应说",
                            timestamp=datetime.now(),
                            thinking_process=None,
                            public_message=response_message
                        )
                        actions.append(target_speech_action)
                        print(f"【调试/Game】记录目标AI回应: {target_player.name}说: {response_message}")
                    
                    # 记录说服动作
                    action_description = (
                        f"玩家 {player.name} 尝试说服 {target_player.name} 转账 {amount} 代币"
                        f"并说：'{persuasion_message}'. "
                        f"{target_player.name} {'接受' if is_accepted else '拒绝'}了请求。"
                    )
                    
                    action = GameAction(
                        player_id=player.id,
                        action_type="persuade",
                        target_player=target_player.id,
                        amount=amount,
                        description=action_description,
                        timestamp=datetime.now()
                    )
                    actions.append(action)
                    
                    print(f"【调试/Game】说服动作: {action_description}")
                    
        # 确保阶段更新：在处理完说服阶段后，强制进入结算阶段
        game_state.phase = GamePhase.SETTLEMENT_PHASE
        print(f"【调试/Game】说服阶段处理完成，设置下一阶段={game_state.phase}")
        
        return actions

    async def _process_settlement_phase(self, game_state: GameState) -> List[GameAction]:
        print(f"【调试/Game】进入结算阶段处理函数，当前阶段={game_state.phase}")
        game_state.phase = GamePhase.SETTLEMENT_PHASE
        actions = []

        # 处理所有已接受的说服请求
        for player in game_state.players:
            if not player.is_active:
                continue

            # 处理玩家收到的请求
            received_requests = [
                r for r in game_state.persuasion_requests
                if r.to_player == player.id and r.accepted and not r.processed
            ]

            for request in received_requests:
                # 获取说服发起者
                from_player = next((p for p in game_state.players if p.id == request.from_player), None)
                if not from_player or not from_player.is_active:
                    continue
                
                # 计算支付金额
                payment_amount = request.amount
                original_amount = payment_amount
                
                # 检查玩家是否使用了护盾卡（支付金额减半）
                if game_state.game_id in self.shield_users and player.id in self.shield_users[game_state.game_id]:
                    payment_amount = max(1, payment_amount // 2)  # 至少支付1代币
                    print(f"【调试/Game】护盾卡生效: 玩家 {player.name} 支付金额从 {original_amount} 减半至 {payment_amount}")
                
                # 检查玩家是否有足够的余额
                if player.balance >= payment_amount:
                    player.balance -= payment_amount
                    from_player.balance += payment_amount
                    request.processed = True
                    
                    # 记录交易动作
                    action = GameAction(
                        player_id=player.id,
                        action_type="transfer",
                        target_player=from_player.id,
                        amount=payment_amount,
                        description=f"玩家 {player.name} 向 {from_player.name} 支付 {payment_amount} 代币" + 
                                   (f" (原始金额 {original_amount} 因护盾卡减半)" if payment_amount != original_amount else ""),
                        timestamp=datetime.now()
                    )
                    actions.append(action)
                
        # 处理激进卡效果（对说服失败的玩家施加惩罚）
        if game_state.game_id in self.aggressive_users:
            for player_id in list(self.aggressive_users[game_state.game_id]):
                player = next((p for p in game_state.players if p.id == player_id and p.is_active), None)
                if not player:
                    # 玩家不存在或不活跃，从集合中移除
                    if player_id in self.aggressive_users[game_state.game_id]:
                        self.aggressive_users[game_state.game_id].remove(player_id)
                    continue
                
                # 检查该玩家是否有发起并成功的说服
                has_successful_persuasion = any(
                    r.from_player == player.id and r.accepted and r.processed
                    for r in game_state.persuasion_requests
                )
                
                # 如果没有成功的说服，则受到惩罚
                if not has_successful_persuasion:
                    # 查找玩家使用的激进卡
                    aggressive_item = next((item for item in player.items if item.used and item.type == ItemType.AGGRESSIVE), None)
                    penalty_amount = aggressive_item.price if aggressive_item else 15  # 默认惩罚15代币
                    
                    if player.balance >= penalty_amount:
                        old_balance = player.balance
                        player.balance -= penalty_amount
                        # 资金流入奖池
                        game_state.prize_pool += penalty_amount
                        
                        # 记录惩罚动作
                        action = GameAction(
                            player_id=player.id,
                            action_type="aggressive_penalty",
                            amount=penalty_amount,
                            description=f"激进卡反噬：玩家 {player.name} 说服失败，损失 {penalty_amount} 代币 (从 {old_balance} 减至 {player.balance})，资金流入奖池",
                            timestamp=datetime.now()
                        )
                        actions.append(action)
                        print(f"【调试/Game】激进卡反噬: 玩家 {player.name} 损失 {penalty_amount} 代币")
                
                # 从集合中移除已处理的玩家
                if player_id in self.aggressive_users[game_state.game_id]:
                    self.aggressive_users[game_state.game_id].remove(player_id)
        
        # 清除护盾用户集合（护盾效果只持续一轮）
        if game_state.game_id in self.shield_users:
            self.shield_users[game_state.game_id].clear()
        
        # 确保阶段更新：在处理完结算阶段后，强制进入统计阶段
        game_state.phase = GamePhase.STATISTICS_PHASE
        print(f"【调试/Game】结算阶段处理完成，设置下一阶段={game_state.phase}")

        return actions

    async def _process_statistics_phase(self, game_state: GameState) -> List[GameAction]:
        game_state.phase = GamePhase.STATISTICS_PHASE
        actions = []

        # 检查玩家是否破产
        for player in game_state.players:
            if player.balance <= 0 and player.is_active:
                player.is_active = False
                
                # 如果玩家还有资金（虽然这种情况不太可能发生，因为前面已经检查了余额<=0）
                # 但为了健壮性，我们仍然处理这种情况
                if player.balance > 0:
                    # 玩家剩余的资金流入奖池
                    game_state.prize_pool += player.balance
                    player.balance = 0
                    
                # 记录玩家破产事件
                action = GameAction(
                    player_id=player.id,
                    action_type="player_bankrupt",
                    description=f"玩家 {player.name} 已破产，退出游戏",
                    timestamp=datetime.now()
                )
                actions.append(action)
                print(f"【调试/Game】玩家 {player.name} 破产退出游戏")
        
        # 删除每5回合重置道具的逻辑
        # 在统计阶段结束时，将游戏阶段重置为道具阶段，准备下一回合
        # 这是修复游戏卡在统计阶段的关键
        game_state.phase = GamePhase.ITEM_PHASE
        
        return actions

    def _check_game_end(self, game_state: GameState) -> bool:
        active_players = [p for p in game_state.players if p.is_active]
        return len(active_players) <= 1

    async def _end_game(self, game_state: GameState) -> List[GameAction]:
        game_state.is_active = False
        active_players = [p for p in game_state.players if p.is_active]
        actions = []

        if len(active_players) == 1:
            winner = active_players[0]
            # 记录获胜前的资金状态
            original_balance = winner.balance
            prize_pool = game_state.prize_pool
            
            # 计算最终奖励（扣除10%税费）
            total_reward = winner.balance + game_state.prize_pool
            final_reward = int(total_reward * 0.9)
            
            # 更新获胜者余额和奖池
            winner.balance = final_reward
            game_state.prize_pool = 0
            game_state.winner = winner.id
            game_state.status = "completed"
            
            # 记录游戏结束动作
            action = GameAction(
                player_id=winner.id,
                action_type="game_end",
                amount=final_reward,
                description=f"游戏结束！玩家 {winner.name} 获胜，获得资金 {original_balance} + 奖池 {prize_pool} = {total_reward}，最终奖励（扣税后）: {final_reward}",
                timestamp=datetime.now()
            )
            actions.append(action)
            print(f"【调试/Game】游戏结束，玩家 {winner.name} 获胜，最终奖励: {final_reward}")
            
            # 创建游戏结果
            game_result = GameResult(
                game_id=game_state.game_id,
                winner_id=winner.id,
                final_balance=final_reward,
                prize_pool=prize_pool,  # 记录奖池原始金额
                total_rounds=game_state.current_round,
                end_time=datetime.now(),
                winner_prompt=winner.prompt
            )
            
            # TODO: 将游戏结果上链
        elif len(active_players) == 0:
            # 所有玩家都破产的情况
            game_state.status = "completed"
            action = GameAction(
                player_id="system",
                action_type="game_end",
                description=f"游戏结束！所有玩家都已破产，没有获胜者",
                timestamp=datetime.now()
            )
            actions.append(action)
            print(f"【调试/Game】游戏结束，所有玩家都已破产")
            
        return actions 