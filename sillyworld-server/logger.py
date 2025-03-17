import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from .models import GameState, GameAction, GameResult

class GameLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志格式
        self.logger = logging.getLogger("game_logger")
        self.logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        self.file_handler = logging.FileHandler(
            self.log_dir / f"game_{datetime.now().strftime('%Y%m%d')}.log"
        )
        self.file_handler.setLevel(logging.INFO)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

    def log_game_start(self, game_state: GameState):
        self.logger.info(f"Game started: {game_state.game_id}")
        self.logger.info(f"Players: {[p.name for p in game_state.players]}")
        self._save_game_state(game_state)

    def log_game_action(self, game_id: str, action: GameAction):
        self.logger.info(f"Game {game_id} - Action: {action.action_type}")
        self.logger.info(f"Player: {action.player_id}")
        if action.target_player:
            self.logger.info(f"Target: {action.target_player}")
        if action.amount:
            self.logger.info(f"Amount: {action.amount}")
        if action.item_type:
            self.logger.info(f"Item: {action.item_type}")

    def log_game_state(self, game_state: GameState):
        self.logger.info(f"Game {game_state.game_id} - Round {game_state.current_round}")
        self.logger.info(f"Phase: {game_state.phase}")
        self.logger.info(f"Prize Pool: {game_state.prize_pool}")
        for player in game_state.players:
            self.logger.info(f"Player {player.name}: Balance {player.balance}")
        self._save_game_state(game_state)

    def log_game_end(self, game_result: GameResult):
        self.logger.info(f"Game ended: {game_result.game_id}")
        self.logger.info(f"Winner: {game_result.winner_id}")
        self.logger.info(f"Final Balance: {game_result.final_balance}")
        self.logger.info(f"Total Rounds: {game_result.total_rounds}")
        self._save_game_result(game_result)

    def log_error(self, error: Exception, context: Optional[str] = None):
        self.logger.error(f"Error: {str(error)}")
        if context:
            self.logger.error(f"Context: {context}")

    def _save_game_state(self, game_state: GameState):
        state_file = self.log_dir / f"game_{game_state.game_id}_state.json"
        with open(state_file, "w") as f:
            json.dump(game_state.dict(), f, indent=2, default=str)

    def _save_game_result(self, game_result: GameResult):
        result_file = self.log_dir / f"game_{game_result.game_id}_result.json"
        with open(result_file, "w") as f:
            json.dump(game_result.dict(), f, indent=2, default=str) 