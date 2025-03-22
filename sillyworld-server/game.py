from typing import List, Dict, Optional
from datetime import datetime
import uuid
from models import (
    GameState, Player, GamePhase, GameAction,
    PersuasionRequest, GameResult, ItemType
)
from items import ItemSystem
from ai import AISystem, AI
from game_record import GameRecord
import traceback
import random


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

        # Game recording system
        self.game_records: Dict[str, GameRecord] = {}

    # 修改：验证游戏资金平衡 - 改为仅监测不修复
    def _verify_game_resources(self, game_state: GameState, source: str = "未知位置") -> bool:
        """验证游戏中的总资金是否平衡
        
        Args:
            game_state: 当前游戏状态
            source: 调用此验证的代码位置/原因
            
        Returns:
            bool: 资金是否平衡
        """
        total_player_balance = sum(player.balance for player in game_state.players if player.is_active)
        total_resources = total_player_balance + game_state.prize_pool
        expected_resources = game_state.total_resources
        
        if total_resources != expected_resources:
            print(f"【警告/Game】资金不平衡！来源: {source}")
            print(f"【警告/Game】当前总额: {total_resources}, 预期总额: {expected_resources}, 差额: {expected_resources - total_resources}")
            print(f"【警告/Game】玩家总额: {total_player_balance}, 奖池: {game_state.prize_pool}")
            
            # 记录每个玩家的余额，帮助调试
            for player in game_state.players:
                if player.is_active:
                    print(f"【警告/Game】玩家 {player.name} 余额: {player.balance}")
            
            # 不再自动修复
            # game_state.prize_pool += (expected_resources - total_resources)
            return False
        return True

    def create_game(self, players: List[Player]) -> GameState:
        """
        Initialize a new game with the given players
        """
        game_id = str(uuid.uuid4())
        
        # Initialize game state
        game_state = GameState(
            game_id=game_id,
            phase=GamePhase.ITEM_PHASE,
            players=players,
            start_time=datetime.now(),
            last_update=datetime.now(),
            current_round=0,
            prize_pool=0,  # Will be set based on entry fees
            total_resources=sum(player.balance for player in players)
        )

        # Calculate prize pool from entry fees (10 tokens per player)
        entry_fee = 10
        for player in game_state.players:
            player.balance -= entry_fee
            game_state.prize_pool += entry_fee
            
        # 验证资金平衡
        self._verify_game_resources(game_state, "游戏创建后")

        # Store the game
        self.games[game_id] = game_state

        # Initialize game record
        self.game_records[game_id] = GameRecord()
        self.game_records[game_id].start_game([p.id for p in players], game_state.start_time)
        print(f"Started recording game {game_id} with {len(players)} players at {game_state.start_time}")

        return game_state

    def get_game(self, game_id: str) -> GameState:
        """
        Get game state by ID
        """
        if game_id not in self.games:
            raise ValueError(f"Game not found: {game_id}")
        return self.games[game_id]

    async def start_game(self, game_id: str) -> GameState:
        """
        Start the game and transition to the first phase
        """
        game_state = self.get_game(game_id)
        if game_state.status != "waiting":
            raise ValueError(f"Game cannot be started: current status is {game_state.status}")

        game_state.status = "active"
        game_state.last_update = datetime.now()

        # Record game start
        self.game_records[game_id].start_round(1)

        return game_state

    async def process_item_phase(self, game_id: str) -> List[GameAction]:
        """
        Process the item phase where players can use their items
        """
        game_state = self.get_game(game_id)
        return await self._process_item_phase(game_state)

    async def process_persuasion_phase(self, game_id: str) -> List[GameAction]:
        """
        Process the persuasion phase where players can attempt to persuade others
        """
        game_state = self.get_game(game_id)
        return await self._process_persuasion_phase(game_state)

    async def process_settlement_phase(self, game_id: str) -> List[GameAction]:
        """
        Process the settlement phase to determine the outcome of all actions
        """
        game_state = self.get_game(game_id)
        return await self._process_settlement_phase(game_state)

    async def process_statistics_phase(self, game_id: str) -> List[GameAction]:
        """
        Process the statistics phase to show the current state of the game
        """
        game_state = self.get_game(game_id)
        return await self._process_statistics_phase(game_state)

    def _reset_item_usage_tracking(self, game_id: str):
        """Reset item usage tracking for a new round"""
        self.round_item_usage[game_id] = {
            player.id: False for player in self.games[game_id].players
        }
        print(f"[DEBUG/Game] Reset item usage tracking for all players, all can use items this round")

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

    async def process_round(self, game_id: str) -> None:
        """Process a single round of the game
        
        Args:
            game_id: Game ID to process
        """
        if game_id not in self.games:
            print(f"[ERROR] Game {game_id} not found")
            return

        game_state = self.games[game_id]

        # Skip round processing if the game is over
        if game_state.is_game_over:
            print(f"[INFO] Game {game_id} is already over")
            return

        # Start recording a new round in the game record
        if game_id in self.game_records:
            self.game_records[game_id].start_round(
                round_number=game_state.current_round,
                player_states=[p.to_dict() for p in game_state.players],
                prize_pool=game_state.prize_pool
            )

        print(f"[INFO] Starting round {game_state.current_round} for game {game_id}")

        # Get all active players for this round
        active_players = [p for p in game_state.players if p.is_active]

        if len(active_players) < 2:
            # Not enough active players, end the game
            print(f"[INFO] Not enough active players ({len(active_players)}) to continue game {game_id}")
            await self._end_game(game_state)
            return

        # Reset item usage tracking for this round
        self._reset_item_usage_tracking(game_id)

        # Process each game phase in sequence
        try:
            # 1. Item purchase phase
            print(f"[INFO] Processing item purchase phase for game {game_id}")
            item_purchase_actions = await self._process_item_phase(game_state)
            self._record_actions(game_id, item_purchase_actions)

            # 2. Item usage phase
            print(f"[INFO] Processing item usage phase for game {game_id}")
            item_usage_actions = await self._process_item_usage_phase(game_state)
            self._record_actions(game_id, item_usage_actions)

            # 3. Persuasion phase
            print(f"[INFO] Processing persuasion phase for game {game_id}")
            persuasion_actions = await self._process_persuasion_phase(game_state)
            self._record_actions(game_id, persuasion_actions)

            # 4. Voting phase
            print(f"[INFO] Processing voting phase for game {game_id}")
            voting_actions = await self._process_voting_phase(game_state)
            self._record_actions(game_id, voting_actions)

            # 5. Results phase
            print(f"[INFO] Processing results phase for game {game_id}")
            await self._process_results_phase(game_state)

            # End the round in the game record
            if game_id in self.game_records:
                self.game_records[game_id].end_round(
                    round_number=game_state.current_round,
                    player_states=[p.to_dict() for p in game_state.players]
                )

            # Check if game should end
            if game_state.current_round >= game_state.max_rounds or len(
                    [p for p in game_state.players if p.is_active]) < 2:
                print(f"[INFO] Game {game_id} has reached end conditions")
                await self._end_game(game_state)

                # Move to next round
                game_state.current_round += 1
                print(f"[INFO] Moving to round {game_state.current_round} for game {game_id}")

        except Exception as e:
            print(f"[ERROR] Error processing round for game {game_id}: {str(e)}")
            traceback.print_exc()
            # Try to continue to the next round if there's an error
            game_state.current_round += 1

    async def _generate_reflections(self, game_state: GameState) -> List[GameAction]:
        """Generate AI reflections about other players
        
        Args:
            game_state: Current game state
            
        Returns:
            List[GameAction]: Reflection actions (not shown to players)
        """
        actions = []

        # Get recent actions from game record
        game_id = game_state.game_id
        if game_id not in self.game_records:
            return actions

        # Find the game record and get recent actions
        game_record = self.game_records[game_id]

        # Extract recent actions from the previous round
        recent_actions = []
        if len(game_record.rounds) > 0:
            previous_round = game_record.rounds[-1]
            for phase in previous_round.phases:
                for action in phase.actions:
                    # Convert to dict for easier processing
                    recent_actions.append(action.to_dict())

        # Only proceed if we have actions to analyze
        if not recent_actions:
            return actions

        # Generate reflections for each AI player
        for player in game_state.players:
            if not player.is_active:
                print(f"【DEBUG/Game】Skipping inactive or non-existent player {player.id}")
                continue
                    
            # Skip players without prompts (human players)
            if not hasattr(player, 'prompt') or not player.prompt:
                continue

            try:
                # Generate reflections about other players
                reflections = await self.ai_system.reflect_on_players(
                    player=player,
                    game_state=game_state,
                    recent_actions=recent_actions
                )

                # Store reflections on the player object for later use
                if not hasattr(player, 'reflections'):
                    player.reflections = {}

                # Update with new reflections
                player.reflections.update(reflections)

                # Create an action to record this reflection process
                reflection_summary = "\n".join([f"{p_id}: {r[:50]}..." for p_id, r in reflections.items()])
                action = GameAction(
                player_id=player.id,
                    action_type="reflection",
                    description=f"AI player {player.name} reflected on other players",
                    thinking_process=reflection_summary,
                    timestamp=datetime.now()
                )
                actions.append(action)

            except Exception as e:
                print(f"Error generating reflections for player {player.name}: {str(e)}")

        return actions

    # Private method to handle AI decisions
    async def _process_ai_decision_with_reflection(
            self, game_state: GameState, player: Player, phase: GamePhase, available_actions: List[str]
    ) -> GameAction:
        """Process AI decision with reflection based on recent game history"""
        try:
            # 尝试获取历史动作进行反思
            if game_state.game_id in self.game_records:
                game_record = self.game_records[game_state.game_id]
                
                # 获取所有游戏动作
                try:
                    # 尝试使用game_record的get_all_actions方法
                    all_actions = game_record.get_all_actions() 
                except (AttributeError, Exception) as e:
                    # 如果方法不存在，直接使用游戏状态中的actions
                    print(f"[DEBUG] Error getting actions from game record: {e}, using game_state.actions instead")
                    all_actions = [action.dict() for action in game_state.actions]
                
                # 如果有足够的动作历史
                if len(all_actions) > 0:
                    # 过滤玩家自己的动作，最多取最近5条
                    player_actions = [
                        action for action in all_actions
                        if action.get("player_id") == player.id
                    ][-5:] if len(all_actions) >= 5 else []
                    
                    # 过滤其他玩家的动作，每个玩家最多取最近3条
                    other_players_actions = {}
                    for p in game_state.players:
                        if p.id != player.id:
                            p_actions = [action for action in all_actions if action.get("player_id") == p.id]
                            other_players_actions[p.id] = p_actions[-3:] if len(p_actions) >= 3 else p_actions
                    
                    # 如果有足够的历史，生成反思
                    if len(player_actions) > 0 or any(len(actions) > 0 for actions in other_players_actions.values()):
                        print(f"[DEBUG] Generating decision for AI player {player.name} with reflection")
                        
                        # 使用基本的决策逻辑，不进行复杂的反思
                        decision = await self.ai_system.make_decision(
                            player, game_state, str(phase), available_actions
                        )
                        
                        print(f"[DEBUG] AI decision generated: {player.name}, action={decision.action_type}, has_thinking={decision.thinking_process is not None}")
                        if decision.thinking_process:
                            print(f"[DEBUG] First 50 chars of thinking: {decision.thinking_process[:50]}...")
                        return decision
        except Exception as e:
            print(f"[ERROR] Error generating reflection decision for {player.name}: {e}")
            import traceback
            traceback.print_exc()
        
        # 如果反思逻辑出错或没有足够的历史，使用基本决策
        print(f"[DEBUG] Generating basic decision for AI player {player.name}")
        decision = await self.ai_system.make_decision(player, game_state, str(phase), available_actions)
        print(f"[DEBUG] Basic AI decision generated: {player.name}, action={decision.action_type}, has_thinking={decision.thinking_process is not None}")
        if decision.thinking_process:
            print(f"[DEBUG] First 50 chars of thinking: {decision.thinking_process[:50]}...")
        # 在每个回合开始时打印道具和状态
    async def _process_item_phase(self, game_state: GameState) -> List[GameAction]:
        print(f"【调试/Game】进入道具阶段处理函数，当前阶段={game_state.phase}")
        # 设置当前阶段
        game_state.phase = GamePhase.ITEM_PHASE
        actions = []

        # 获取游戏是否在准备阶段
        is_preparation = self.game_preparation.get(game_state.game_id, False)
        
        # 每轮开始时重置道具使用跟踪状态
        if game_state.game_id not in self.round_item_usage:
            self.round_item_usage[game_state.game_id] = {}
        for player in game_state.players:
            if player.is_active:
                self.round_item_usage[game_state.game_id][player.id] = False
                print(f"【调试/Game】重置玩家 {player.name} 的道具使用状态，允许在本回合使用道具")
        
        # 在每个回合开始时打印道具和状态        for player in game_state.players:
            if player.is_active:
                items_info = "，".join([f"{item.type.value}" + ("(已使用)" if item.used else "") for item in
                                       player.items]) if player.items else "无"
                print(f"【调试/Game】玩家 {player.name} 道具状态: {items_info}")
                # 确保round_item_usage正确初始化
                if game_state.game_id in self.round_item_usage and player.id in self.round_item_usage[
                    game_state.game_id]:
                    print(
                        f"【调试/Game】玩家 {player.name} 在本回合是否已使用道具: {self.round_item_usage[game_state.game_id][player.id]}")
        
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
                    decision = await self._process_ai_decision_with_reflection(
                        game_state=game_state,
                        player=player,
                        phase="preparation",
                        available_actions=available_actions
                    )
                    
                    # 记录AI的思考过程(只对玩家可见)
                    if decision.thinking_process:
                        thinking_action = GameAction(
                            player_id=player.id,
                            action_type="ai_thinking",
                            thinking_process=decision.thinking_process,
                            description=f"AI player {player.name}'s thinking process",
                            timestamp=datetime.now()
                        )
                        actions.append(thinking_action)
                        # 确保思考过程被添加到game_state.actions列表中
                        game_state.actions.append(thinking_action)
                        print(f"【调试/Game】记录AI思考过程: {player.name}")
                        
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
                                print(
                                    f"【调试/Game】玩家 {player.name} 余额不足，无法购买道具 {item_type.value}，价格: {cost}，当前余额: {player.balance}")
                                continue

                            # 从玩家余额中扣除成本
                            player.balance -= cost
                            # 购买道具的资金正确流入奖池
                            game_state.prize_pool += cost
                            
                            # 添加道具到玩家库存
                            item = ItemSystem.create_item(item_type)
                            player.items.append(item)
                            
                            # 记录玩家已购买的道具类型
                            if game_state.game_id in self.player_item_types and player.id in self.player_item_types[
                                game_state.game_id]:
                                self.player_item_types[game_state.game_id][player.id].add(item_type.value)
                            
                            # 记录动作但不指明具体道具类型(对其他AI保密)
                            action = GameAction(
                                player_id=player.id,
                                action_type="buy_item",
                                amount=cost,
                                item_type=item_type,  # 这个信息只对玩家可见，不会广播给其他AI
                                thinking_process=decision.thinking_process,  # 添加思考过程
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
                        decision = await self._process_ai_decision_with_reflection(
                            game_state=game_state,
                            player=player,
                            phase="item_usage",
                            available_actions=available_actions
                        )
                        
                        # 记录AI的思考过程(只对玩家可见)
                        if decision.thinking_process:
                            thinking_action = GameAction(
                                player_id=player.id,
                                action_type="ai_thinking",
                                thinking_process=decision.thinking_process,
                                description=f"AI player {player.name}'s thinking process",
                                timestamp=datetime.now()
                            )
                            actions.append(thinking_action)
                            # 确保思考过程被添加到game_state.actions列表中
                            game_state.actions.append(thinking_action)
                            print(f"【调试/Game】记录AI思考过程: {player.name}")
                            target_player = next((p for p in other_players if p.id == target_id),
                                               random.choice(other_players))
                            
                            effect_description = ""
                            
                            # 根据道具类型应用效果
                            if item_to_use.type == ItemType.AGGRESSIVE:
                                # 激进卡：标记玩家使用了激进卡，说服失败时将受到额外惩罚（在说服阶段处理）
                                # 为玩家添加标记，稍后在说服阶段使用
                                if game_state.game_id not in self.aggressive_users:
                                    self.aggressive_users[game_state.game_id] = set()
                                    self.aggressive_users[game_state.game_id].add(player.id)
                            
                                # 即时效果：从目标玩家处获取5%余额
                                shield_active = target_player.id in self.shield_users.get(game_state.game_id, set())
                                if not shield_active:
                                    penalty_amount = max(1, int(target_player.balance * 0.05))
                                    actual_penalty = min(penalty_amount, target_player.balance)  # 确保不会扣除超过玩家拥有的金额
                                    target_player.balance -= actual_penalty
                                    player.balance += actual_penalty  # 资金直接从目标玩家转移到使用者
                                    effect_description = f"激活攻击策略，立即从 {target_player.name} 获取 {actual_penalty} 代币作为税收。若本轮说服失败将从自己的余额中额外损失代币作为惩罚"
                                else:
                                    effect_description = f"激活攻击策略，但 {target_player.name} 的护盾阻止了即时效果。若本轮说服失败将额外损失 {item_to_use.price} 代币作为惩罚"
                            
                            elif item_to_use.type == ItemType.SHIELD:
                                # 护盾卡：标记玩家使用了护盾，在被说服时支付金额减半（在说服阶段处理）
                                # 为玩家添加标记，稍后在说服阶段使用
                                if game_state.game_id not in self.shield_users:
                                    self.shield_users[game_state.game_id] = set()
                                    self.shield_users[game_state.game_id].add(player.id)
                                effect_description = f"激活防护盾，若本轮被其他玩家成功说服，需要支付的代币减半(50%)"
                            
                            elif item_to_use.type == ItemType.INTEL:
                                # 随机获取Prompt的一部分信息（取前1/3部分）
                                prompt_part = target_player.prompt[:len(target_player.prompt) // 3] + "..."
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
                                print(
                                    f"【调试/Game】记录AI使用道具后发言: {player.name}说: {decision.public_message}")
                            
                            print(
                                f"【调试/Game】玩家 {player.name} 对 {target_player.name} 使用了道具: {item_to_use.type.value}，效果: {effect_description}")
                    else:
                        print(f"【调试/Game】玩家 {player.name} 没有可用未使用的道具")
                else:
                    print(f"【调试/Game】玩家 {player.name} 在本回合已经使用过道具，跳过")
        
        # 确保阶段更新：在处理完道具阶段后，强制进入说服阶段
        game_state.phase = GamePhase.PERSUASION_PHASE
        print(f"【调试/Game】道具阶段处理完成，设置下一阶段={game_state.phase}")
        
        return actions

    async def _process_persuasion_phase(self, game_state: GameState) -> List[GameAction]:
        """
        Process the persuasion phase in the game.
        """
        print(f"【DEBUG/Game】Starting persuasion phase for game {game_state.game_id} (phase: {game_state.phase})")
        print(f"【DEBUG/Game】Players activation order: {self._get_players_by_activation_order(game_state)}")

        persuasion_actions = []
        
        for player_id in self._get_players_by_activation_order(game_state):
            player = next((p for p in game_state.players if p.id == player_id and p.is_active), None)
            if not player:
                print(f"【DEBUG/Game】Skipping inactive or non-existent player {player_id}")
                continue
            print(f"【DEBUG/Game】Processing actions for player {player.name} (AI: {player.is_ai})")
            
            if player.is_ai:
                print(f"【DEBUG/Game】Generating AI decision for {player.name}")
                
                # Create AI player
                ai_player = self._create_ai_player(player)
                
                # Generate AI persuasion
                action, thinking_process = await ai_player._decide_persuasion(game_state)
                
                # 确保我们正确设置了思考过程
                if thinking_process:
                    print(f"【DEBUG/Game】AI thinking process generated, length: {len(thinking_process)}")
                    action.thinking_process = thinking_process
                    action.action_type = "persuade"  # 确保action类型正确
                else:
                    print(f"【ERROR/Game】No thinking process generated for {player.name}!")
                
                # 调试输出完整的action内容
                print(f"【DEBUG/Game】Action details: type={action.action_type}, has_thinking={action.thinking_process is not None}")
                
                # 如果有persuasion数据，记录相关信息
                if hasattr(action, 'persuasion_data') and action.persuasion_data:
                    target_id = action.persuasion_data.get('target_player')
                    amount = action.persuasion_data.get('amount')
                    message = action.persuasion_data.get('message')
                    print(f"【DEBUG/Game】Persuasion data: target={target_id}, amount={amount}, message={message}")
                
                persuasion_actions.append(action)
                game_state.actions.append(action)
                
                # Find the target player
                target_id = action.persuasion_data.get('target_player')
                target = next((p for p in game_state.players if p.id == target_id and p.is_active), None)
                
                if not target:
                    print(f"【ERROR/Game】Target player {target_id} not found or not active")
                    continue
                
                if target.is_ai:
                    print(f"【DEBUG/Game】Target is AI {target.name}, evaluating persuasion from {player.name}")
                    
                    # Create AI target
                    ai_target = self._create_ai_player(target)
                    
                    # Create persuasion request
                    persuasion_request = PersuasionRequest(
                        from_id=player.id,
                        from_name=player.name,
                        to_id=target.id,
                        to_name=target.name,
                        amount=action.persuasion_data.get('amount'),
                        message=action.persuasion_data.get('message')
                    )
                    
                    # Evaluate with AI
                    ai_response, thinking_process = await ai_target.evaluate_persuasion(game_state, persuasion_request)
                    print(f"【DEBUG/Game】AI response: {ai_response}, thinking process length: {len(thinking_process) if thinking_process else 0}")
                    
                    # Create AI response action with current time
                    current_time = datetime.now()
                    thinking_action = GameAction(
                        player_id=target.id,
                        action_type="thinking",
                        description=f"AI player {target.name}'s thinking process",
                        timestamp=current_time,
                        thinking_process=thinking_process
                    )
                    
                    print(f"【DEBUG/Game】Creating thinking_action: player={target.name}, type={thinking_action.action_type}")
                    print(f"【DEBUG/Game】Thinking process exists: {thinking_action.thinking_process is not None}")
                    
                    # 添加到persuasion_actions和game_state.actions
                    persuasion_actions.append(thinking_action)
                    game_state.actions.append(thinking_action)
                    
                    # Handle AI response
                    if ai_response:
                        amount = action.persuasion_data.get('amount')
                        print(f"【DEBUG/Game】AI accepted persuasion, transferring {amount} tokens")
                        
                        # 记录转账前的资金状态
                        print(f"【资金追踪】转账前 - 发起者:{player.name}({player.balance}) 接收者:{target.name}({target.balance}) 奖池:{game_state.prize_pool}")
                        
                        # Transfer tokens
                        old_target_balance = target.balance
                        old_player_balance = player.balance
                        
                        target.balance -= amount
                        player.balance += amount
                        
                        # 记录转账后的资金状态
                        print(f"【资金追踪】转账后 - 发起者:{player.name}({player.balance})(+{player.balance-old_player_balance}) 接收者:{target.name}({target.balance})(-{old_target_balance-target.balance}) 奖池:{game_state.prize_pool}")
                        
                        # 记录总资金变化
                        old_total = old_target_balance + old_player_balance + game_state.prize_pool
                        new_total = target.balance + player.balance + game_state.prize_pool
                        print(f"【资金追踪】总资金: {old_total} -> {new_total}, 差额: {new_total - old_total}")
                        
                        # 验证资金平衡
                        self._verify_game_resources(game_state, f"Persuasion acceptance: {player.name} <- {target.name} ({amount} tokens)")
                    else:
                        print(f"【DEBUG/Game】AI rejected persuasion")
                else:
                    print(f"【DEBUG/Game】Target is human {target.name}, adding to pending requests")
                    # If target is human, add to pending requests
                    game_state.pending_requests.append({
                        'from_id': player.id,
                        'from_name': player.name,
                        'to_id': target.id,
                        'to_name': target.name,
                        'amount': action.persuasion_data.get('amount'),
                        'message': action.persuasion_data.get('message')
                    })
            else:
                # Human players will send their persuasion requests via API
                print(f"【DEBUG/Game】Human player {player.name}, no AI action needed")
                
        print(f"【DEBUG/Game】Persuasion phase completed, returning {len(persuasion_actions)} actions")
        return persuasion_actions

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
                    print(
                        f"【调试/Game】护盾卡生效: 玩家 {player.name} 支付金额从 {original_amount} 减半至 {payment_amount}")
                
                # 检查玩家是否有足够的余额
                if player.balance >= payment_amount:
                    # 记录转账前的资金状态
                    print(f"【资金追踪/结算】转账前 - 发起者:{from_player.name}({from_player.balance}) 接收者:{player.name}({player.balance}) 奖池:{game_state.prize_pool}")
                    
                    # 记录转账前总资金
                    old_total = sum(p.balance for p in game_state.players if p.is_active) + game_state.prize_pool
                    
                    # 保存转账前余额以计算差额
                    old_player_balance = player.balance
                    old_from_player_balance = from_player.balance
                    
                    player.balance -= payment_amount
                    from_player.balance += payment_amount
                    request.processed = True
                    
                    # 记录转账后的资金状态
                    print(f"【资金追踪/结算】转账后 - 发起者:{from_player.name}({from_player.balance})(+{from_player.balance-old_from_player_balance}) 接收者:{player.name}({player.balance})(-{old_player_balance-player.balance}) 奖池:{game_state.prize_pool}")
                    
                    # 记录总资金变化
                    new_total = sum(p.balance for p in game_state.players if p.is_active) + game_state.prize_pool
                    print(f"【资金追踪/结算】总资金: {old_total} -> {new_total}, 差额: {new_total - old_total}")
                    
                    # 验证资金平衡
                    self._verify_game_resources(game_state, f"Settlement phase: {player.name} -> {from_player.name} ({payment_amount} tokens)")
                    
                    # 记录交易动作
                    action = GameAction(
                        player_id=player.id,
                        action_type="transfer",
                        target_player=from_player.id,
                        amount=payment_amount,
                        description=f"玩家 {player.name} 向 {from_player.name} 支付 {payment_amount} 代币" + 
                                    (
                                        f" (原始金额 {original_amount} 因护盾卡减半)" if payment_amount != original_amount else ""),
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
                    aggressive_item = next(
                        (item for item in player.items if item.used and item.type == ItemType.AGGRESSIVE), None)
                    penalty_amount = aggressive_item.price if aggressive_item else 15  # 默认惩罚15代币
                    
                    if player.balance >= penalty_amount:
                        # 记录惩罚前的资金状态
                        print(f"【资金追踪/惩罚】惩罚前 - 玩家:{player.name}({player.balance}) 奖池:{game_state.prize_pool}")
                        
                        old_balance = player.balance
                        old_prize_pool = game_state.prize_pool
                        
                        player.balance -= penalty_amount
                        # 资金流入奖池
                        game_state.prize_pool += penalty_amount
                        
                        # 记录惩罚后的资金状态
                        print(f"【资金追踪/惩罚】惩罚后 - 玩家:{player.name}({player.balance})(-{old_balance-player.balance}) 奖池:{game_state.prize_pool}(+{game_state.prize_pool-old_prize_pool})")
                        
                        # 记录总资金变化
                        old_total = old_balance + old_prize_pool
                        new_total = player.balance + game_state.prize_pool
                        print(f"【资金追踪/惩罚】总资金: {old_total} -> {new_total}, 差额: {new_total - old_total}")
                        
                        # 验证资金平衡
                        self._verify_game_resources(game_state, f"Aggressive penalty: {player.name} to prize pool ({penalty_amount} tokens)")
                        
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
        """End the game and determine the winner
        
        Args:
            game_state: The current game state
            
        Returns:
            List[GameAction]: Actions related to game end
        """
        # Find the player with the highest balance
        active_players = [p for p in game_state.players if p.is_active]
        if not active_players:
            # Emergency fallback - this shouldn't happen
            winner = game_state.players[0]
        else:
            winner = max(active_players, key=lambda p: p.balance)

        # Create game end action
        end_action = GameAction(
                player_id=winner.id,
                action_type="game_end",
            description=f"Game ended. Winner: {winner.name} with {winner.balance} coins",
                timestamp=datetime.now()
            )

        # Update game state
        game_state.winner = winner.id
        game_state.status = "completed"
        game_state.is_active = False
        game_state.last_update = datetime.now()

        # Record game result in GameRecord
        game_id = game_state.game_id
        if game_id in self.game_records:
            self.game_records[game_id].end_game(
                winner_id=winner.id,
                winner_name=winner.name,
                final_states=[{
                    "id": player.id,
                    "name": player.name,
                    "balance": player.balance,
                    "items": player.items,
                    "is_active": player.is_active
                } for player in game_state.players],
                prize_pool=game_state.prize_pool
            )

            # Create GameResult for storage/analysis
            game_result = GameResult(
                game_id=game_state.game_id,
                winner_id=winner.id,
                final_balance=winner.balance,
                prize_pool=game_state.prize_pool,
                total_rounds=game_state.current_round,
                end_time=datetime.now(),
                winner_prompt=winner.prompt
            )
            
        print(f"Game {game_state.game_id} ended. Winner: {winner.name} with {winner.balance} coins")

        return [end_action]

    def _record_action(self, game_id: str, action: GameAction) -> None:
        """Record a player action in the game record
        
        Args:
            game_id: ID of the game
            action: The action to record
        """
        if game_id not in self.game_records:
            return

        game_record = self.game_records[game_id]
        game_state = self.games[game_id]

        # Find target player name if target_player is set
        target_name = None
        if action.target_player:
            target_player = next((p for p in game_state.players if p.id == action.target_player), None)
            target_name = target_player.name if target_player else None

        # Find player name
        player = next((p for p in game_state.players if p.id == action.player_id), None)
        player_name = player.name if player else "Unknown"

        # Record the action
        game_record.record_action(
            player_id=action.player_id,
            player_name=player_name,
            action_type=action.action_type,
            target_id=action.target_player,
            target_name=target_name,
            amount=action.amount,
            item_type=action.item_type.value if action.item_type else None,
            description=action.description,
            thinking_process=action.thinking_process,
            public_message=action.public_message,
            result=None  # Will be updated later for actions that have results
        )

    def _create_ai_player(self, player):
        """
        Create an AI player instance for decision making
        """
        from ai import AI
        
        print(f"【DEBUG/Game】Creating AI instance for player {player.name}")
        
        # Create AI instance
        ai_player = AI(player)
        
        return ai_player

    def _get_players_by_activation_order(self, game_state: GameState) -> List[str]:
        """
        获取玩家激活顺序（玩家ID列表）
        按照余额从高到低排序
        """
        # 只选择活跃的玩家
        active_players = [p for p in game_state.players if p.is_active]
        
        # 按余额排序（从高到低）
        sorted_players = sorted(active_players, key=lambda p: p.balance, reverse=True)
        
        # 返回排序后的玩家ID列表
        return [p.id for p in sorted_players]

    def _record_actions(self, game_id: str, actions: List[GameAction]) -> None:
        """Record multiple player actions in the game record
        
        Args:
            game_id: ID of the game
            actions: List of actions to record
        """
        if not actions:
            return
            
        for action in actions:
            self._record_action(game_id, action)
