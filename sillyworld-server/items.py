from typing import List, Dict, Optional
from datetime import datetime
from models import Item, ItemType, Player, GameState, GameAction
import random


class ItemSystem:
    ITEM_PRICES = {
        ItemType.AGGRESSIVE: 15,
        ItemType.SHIELD: 10,
        ItemType.INTEL: 8,
        ItemType.EQUALIZER: 12
    }

    @staticmethod
    def get_random_item() -> ItemType:
        """随机生成一个道具类型"""
        return random.choice(list(ItemType))

    @staticmethod
    def create_item(item_type: ItemType) -> Item:
        """创建一个新的道具实例"""
        return Item(type=item_type, price=ItemSystem.ITEM_PRICES[item_type], used=False)

    @staticmethod
    def can_use_item(player: Player, item_type: ItemType) -> bool:
        # 检查玩家是否有足够的余额购买道具
        return player.balance >= ItemSystem.ITEM_PRICES[item_type]

    @staticmethod
    def use_item(
            game_state: GameState,
            player: Player,
            item_type: ItemType,
            target_player: Optional[str] = None
    ) -> GameAction:
        if not ItemSystem.can_use_item(player, item_type):
            raise ValueError("Player does not have enough balance to use this item")

        # 扣除道具费用
        player.balance -= ItemSystem.ITEM_PRICES[item_type]

        # 创建道具使用记录
        action = GameAction(
            player_id=player.id,
            action_type="use_item",
            target_player=target_player,
            item_type=item_type,
            timestamp=datetime.now()
        )

        # 根据道具类型处理效果
        if item_type == ItemType.AGGRESSIVE:
            # 激进卡效果在说服阶段处理
            pass
        elif item_type == ItemType.SHIELD:
            # 护盾卡效果在说服阶段处理
            pass
        elif item_type == ItemType.INTEL:
            # 情报卡效果在说服阶段处理
            pass
        elif item_type == ItemType.EQUALIZER:
            # 均富卡效果在下一轮开始时处理
            pass

        return action

    @staticmethod
    def handle_item_conflicts(
            game_state: GameState,
            actions: List[GameAction]
    ) -> List[GameAction]:
        # 处理道具冲突
        # 按照时间戳排序，先使用的道具生效
        sorted_actions = sorted(actions, key=lambda x: x.timestamp)
        valid_actions = []
        used_items = set()

        for action in sorted_actions:
            if action.item_type not in used_items:
                valid_actions.append(action)
                used_items.add(action.item_type)

        return valid_actions

    @staticmethod
    def apply_aggressive_effect(target_balance: int, prize_pool: int) -> tuple:
        """应用激进卡效果"""
        amount = 10
        if target_balance >= amount:
            target_balance -= amount
            prize_pool += amount
        return target_balance, prize_pool

    @staticmethod
    def apply_equalizer_effect(balance1: int, balance2: int) -> tuple:
        """应用均富卡效果"""
        total = balance1 + balance2
        each = total // 2
        return each, each
