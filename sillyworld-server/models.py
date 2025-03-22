from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class GamePhase(Enum):
    ITEM_PHASE = "item_phase"
    PREPARATION_PHASE = "preparation_phase"
    EVENT_PHASE = "event_phase"
    NEGOTIATION_PHASE = "negotiation_phase"
    PERSUASION_PHASE = "persuasion_phase"
    SETTLEMENT_PHASE = "settlement_phase"
    STATISTICS_PHASE = "statistics_phase"


class ItemType(Enum):
    AGGRESSIVE = "aggressive"  # 激进卡
    SHIELD = "shield"  # 护盾卡
    INTEL = "intel"  # 情报卡
    EQUALIZER = "equalizer"  # 均富卡


class Item(BaseModel):
    type: ItemType
    price: int
    used: bool = False


class Player(BaseModel):
    id: str
    name: str
    prompt: Optional[str] = ""
    balance: int = 100  # 初始资金
    items: List[Item] = []
    is_active: bool = True
    is_ai: bool = True  # 添加is_ai属性，默认为True
    last_action_time: Optional[datetime] = None
    prepared: bool = False  # 添加prepared属性，用于标记玩家是否完成准备
    
    def to_dict(self):
        """将Player对象转换为字典，确保与GameRecord兼容"""
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "balance": self.balance,
            "items": [item.dict() for item in self.items],
            "is_active": self.is_active,
            "is_ai": self.is_ai,
            "last_action_time": self.last_action_time.isoformat() if self.last_action_time else None,
            "prepared": self.prepared,
            "active": self.is_active  # 添加active字段，兼容GameRecord
        }


class GameState(BaseModel):
    game_id: str
    phase: GamePhase
    players: List[Player]
    current_round: int = 0
    prize_pool: int = 0
    total_resources: int = 0  # 游戏总资源（所有玩家资金 + 奖池），应保持不变
    start_time: datetime
    last_update: datetime
    winner: Optional[str] = None
    is_active: bool = True
    is_ai: bool = True  # 添加is_ai属性，默认为True
    status: str = "waiting"  # 'waiting', 'active', 'paused', 'completed'
    persuasion_requests: List["PersuasionRequest"] = []
    actions: List["GameAction"] = []  # 添加actions字段用于记录游戏行动
    pending_requests: List[Dict] = []  # 添加pending_requests字段
    is_game_over: bool = False  # 添加is_game_over属性，标记游戏是否结束
    max_rounds: int = 10  # 添加最大回合数

    @property
    def id(self) -> str:
        """作为game_id的别名，保证兼容性"""
        return self.game_id


class PersuasionRequest(BaseModel):
    from_id: str
    from_name: str
    to_id: Optional[str] = None
    to_name: Optional[str] = None
    amount: int
    message: str
    accepted: bool = False
    processed: bool = False
    timestamp: Optional[datetime] = None


class PersuasionData(BaseModel):
    target_player: str
    amount: int
    message: str
    
    def get(self, key, default=None):
        """获取属性值，类似字典的get方法"""
        if hasattr(self, key):
            return getattr(self, key)
        return default


class PersuasionResponse(BaseModel):
    to_player: str
    is_accepted: bool
    message: str


class GameAction(BaseModel):
    player_id: str
    action_type: str  # buy_item, use_item, persuade, accept_persuasion, reject_persuasion, thinking
    target_player: Optional[str] = None
    amount: Optional[int] = None
    message: Optional[str] = None
    item_id: Optional[str] = None
    item_type: Optional[ItemType] = None
    description: Optional[str] = None  # 动作的详细描述
    timestamp: datetime = Field(default_factory=datetime.now)
    thinking_process: Optional[str] = None  # AI的思考过程
    public_message: Optional[str] = None  # AI的公开发言
    persuasion_data: Optional[PersuasionData] = None  # 说服请求数据
    persuasion_response: Optional[PersuasionResponse] = None  # 说服响应数据
    
    def to_dict(self):
        """将GameAction对象转换为字典"""
        result = {
            "player_id": self.player_id,
            "action_type": self.action_type,
            "timestamp": self.timestamp,
            "description": self.description
        }
        
        if self.target_player:
            result["target_player"] = self.target_player
        if self.amount:
            result["amount"] = self.amount
        if self.message:
            result["message"] = self.message
        if self.item_id:
            result["item_id"] = self.item_id
        if self.item_type:
            result["item_type"] = self.item_type.value if self.item_type else None
        if self.thinking_process:
            result["thinking_process"] = self.thinking_process
        if self.public_message:
            result["public_message"] = self.public_message
        if self.persuasion_data:
            result["persuasion_data"] = self.persuasion_data.dict()
        if self.persuasion_response:
            result["persuasion_response"] = self.persuasion_response.dict()
            
        return result


class GameResult(BaseModel):
    game_id: str
    winner_id: str
    final_balance: int
    prize_pool: int
    total_rounds: int
    end_time: datetime
    winner_prompt: str
