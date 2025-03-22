import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from .models import GameState, GameAction, GameResult


class GameLogger:
    def __init__(self, log_dir: str = "logs"):
        """Initialize game logger with configurable log directory
        
        Args:
            log_dir: Directory path for storing log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Configure main logger
        self.logger = logging.getLogger("game_logger")
        self.logger.setLevel(logging.INFO)

        # Create file handlers for different log types
        self.setup_handlers()

        # Track active games for structured logging
        self.active_games = {}

    def setup_handlers(self):
        """Set up various log handlers for different purposes"""
        # Main log file
        self.file_handler = logging.FileHandler(
            self.log_dir / f"game_{datetime.now().strftime('%Y%m%d')}.log"
        )
        self.file_handler.setLevel(logging.INFO)

        # AI responses log file
        self.ai_handler = logging.FileHandler(
            self.log_dir / f"ai_responses_{datetime.now().strftime('%Y%m%d')}.log"
        )
        self.ai_handler.setLevel(logging.DEBUG)

        # Error log file
        self.error_handler = logging.FileHandler(
            self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        )
        self.error_handler.setLevel(logging.ERROR)

        # Configure formatters
        standard_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
        )
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s\n'
        )

        self.file_handler.setFormatter(standard_formatter)
        self.ai_handler.setFormatter(detailed_formatter)
        self.error_handler.setFormatter(detailed_formatter)

        # Add handlers to logger
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.ai_handler)
        self.logger.addHandler(self.error_handler)

    def log_game_start(self, game_state: GameState):
        """Log the start of a new game
        
        Args:
            game_state: Initial game state
        """
        self.logger.info(f"Game started: {game_state.game_id}")
        self.logger.info(f"Players: {[p.name for p in game_state.players]}")
        self.logger.info(f"Initial prize pool: {game_state.prize_pool}")
        self.logger.info(f"Start time: {game_state.start_time}")

        # Track active game
        self.active_games[game_state.game_id] = {
            "start_time": game_state.start_time,
            "players": [p.name for p in game_state.players],
            "current_round": game_state.current_round
        }

        self._save_game_state(game_state)

    def log_game_action(self, game_id: str, action: GameAction):
        """Log a game action
        
        Args:
            game_id: Game identifier
            action: The action being performed
        """
        # Standard action logging
        self.logger.info(f"Game {game_id} - Action: {action.action_type} by Player: {action.player_id}")

        # Log additional details if present
        details = []
        if action.target_player:
            details.append(f"Target: {action.target_player}")
        if action.amount:
            details.append(f"Amount: {action.amount}")
        if action.item_type:
            details.append(f"Item: {action.item_type}")
        if details:
            self.logger.info(f"Details: {', '.join(details)}")

        # Log AI thinking process separately if present
        if action.thinking_process:
            self.log_ai_thinking(game_id, action.player_id, action.action_type, action.thinking_process)

        # Log public message if present
        if action.public_message:
            self.logger.info(f"Public message from {action.player_id}: {action.public_message}")

    def log_ai_thinking(self, game_id: str, player_id: str, action_type: str, thinking: str):
        """Log AI thinking process
        
        Args:
            game_id: Game identifier
            player_id: AI player identifier
            action_type: Type of action being considered
            thinking: AI's reasoning process
        """
        thinking_logger = logging.getLogger(f"ai_thinking.{game_id}")
        thinking_logger.setLevel(logging.DEBUG)

        # Ensure logger has our handlers
        if not thinking_logger.handlers:
            thinking_logger.addHandler(self.ai_handler)

        # Log structured thinking
        thinking_logger.debug(f"AI THINKING - Game: {game_id}, Player: {player_id}, Action: {action_type}")
        thinking_logger.debug(f"--- REASONING START ---\n{thinking}\n--- REASONING END ---")

    def log_game_state(self, game_state: GameState):
        """Log current game state
        
        Args:
            game_state: Current game state to log
        """
        self.logger.info(f"Game {game_state.game_id} - Round {game_state.current_round} - Phase: {game_state.phase}")
        self.logger.info(f"Prize Pool: {game_state.prize_pool}")

        # Log player states
        player_states = []
        for player in game_state.players:
            item_count = len([i for i in player.items if not i.used])
            player_states.append(f"{player.name}: {player.balance} coins, {item_count} items")

        self.logger.info(f"Player states: {' | '.join(player_states)}")

        # Update active game tracking
        if game_state.game_id in self.active_games:
            self.active_games[game_state.game_id]["current_round"] = game_state.current_round
            self.active_games[game_state.game_id]["last_update"] = datetime.now()

        self._save_game_state(game_state)

    def log_game_end(self, game_result: GameResult):
        """Log game end result
        
        Args:
            game_result: Final game result
        """
        self.logger.info(f"Game {game_result.game_id} ended")
        self.logger.info(f"Winner: {game_result.winner_id}")
        self.logger.info(f"Final balance: {game_result.final_balance}")
        self.logger.info(f"Prize pool: {game_result.prize_pool}")
        self.logger.info(f"Total rounds: {game_result.total_rounds}")
        self.logger.info(
            f"Duration: {(game_result.end_time - self.active_games.get(game_result.game_id, {}).get('start_time', game_result.end_time)).total_seconds()} seconds")

        # Remove from active games
        if game_result.game_id in self.active_games:
            del self.active_games[game_result.game_id]

        self._save_game_result(game_result)

    def log_error(self, error: Exception, context: Optional[str] = None, game_id: Optional[str] = None):
        """Log errors with context
        
        Args:
            error: Exception that occurred
            context: Additional context information
            game_id: Related game ID if applicable
        """
        error_msg = f"ERROR: {str(error)}"
        if context:
            error_msg = f"{error_msg} - Context: {context}"
        if game_id:
            error_msg = f"Game {game_id} - {error_msg}"

        self.logger.error(error_msg, exc_info=True)

    def _save_game_state(self, game_state: GameState):
        """Save full game state to JSON file
        
        Args:
            game_state: Game state to save
        """
        game_dir = self.log_dir / "game_states"
        game_dir.mkdir(exist_ok=True)

        filename = game_dir / f"{game_state.game_id}_{game_state.current_round}.json"

        with open(filename, "w") as f:
            f.write(game_state.json(indent=2))

    def _save_game_result(self, game_result: GameResult):
        """Save game result to JSON file
        
        Args:
            game_result: Game result to save
        """
        results_dir = self.log_dir / "game_results"
        results_dir.mkdir(exist_ok=True)

        filename = results_dir / f"{game_result.game_id}_result.json"

        with open(filename, "w") as f:
            f.write(game_result.json(indent=2))
