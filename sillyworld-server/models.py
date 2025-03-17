from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

class GamePhase(Enum):
    ITEM_PHASE = "item_phase"
    PERSUASION_PHASE = "persuasion_phase"
    SETTLEMENT_PHASE = "settlement_phase"
    STATISTICS_PHASE = "statistics_phase"

class ItemType(Enum):
    AGGRESSIVE = "aggressive"  # 激进卡
    SHIELD = "shield"         # 护盾卡
    INTEL = "intel"          # 情报卡
    EQUALIZER = "equalizer"  # 均富卡

class Item(BaseModel):
    type: ItemType
    price: int
    used: bool = False

class Player(BaseModel):
    id: str
    name: str
    prompt: str
    balance: int = 100  # 初始资金
    items: List[Item] = []
    is_active: bool = True
    last_action_time: Optional[datetime] = None

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
    status: str = "waiting"  # 'waiting', 'active', 'paused', 'completed'
    persuasion_requests: List["PersuasionRequest"] = []

class PersuasionRequest(BaseModel):
    from_player: str
    to_player: str
    amount: int
    message: str
    accepted: bool = False
    processed: bool = False

class GameAction(BaseModel):
    player_id: str
    action_type: str  # buy_item, use_item, 等
    target_player: Optional[str] = None
    amount: Optional[int] = None
    message: Optional[str] = None
    item_id: Optional[str] = None
    item_type: Optional[ItemType] = None
    description: Optional[str] = None  # 动作的详细描述
    timestamp: datetime = Field(default_factory=datetime.now)
    thinking_process: Optional[str] = None  # AI的思考过程
    public_message: Optional[str] = None  # AI的公开发言

class GameResult(BaseModel):
    game_id: str
    winner_id: str
    final_balance: int
    prize_pool: int
    total_rounds: int
    end_time: datetime
    winner_prompt: str 