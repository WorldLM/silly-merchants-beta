import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
import uuid


@dataclass
class PlayerAction:
    """Records a player action during the game"""
    player_id: str
    player_name: str
    action_type: str
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    amount: Optional[int] = None
    item_type: Optional[str] = None
    description: Optional[str] = None
    thinking_process: Optional[str] = None
    public_message: Optional[str] = None
    result: Optional[bool] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime to string
        data["timestamp"] = data["timestamp"].isoformat()
        return data


@dataclass
class PlayerState:
    """Records a player's state at a specific point in the game"""
    player_id: str
    player_name: str
    balance: int
    items: List[Dict[str, Any]]
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class RoundPhase:
    """Records activities in a specific game phase"""
    phase_name: str
    actions: List[PlayerAction] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetimes to strings
        data["start_time"] = data["start_time"].isoformat()
        if data["end_time"]:
            data["end_time"] = data["end_time"].isoformat()
        # Convert actions to dictionaries
        data["actions"] = [a.to_dict() for a in self.actions]
        return data


@dataclass
class GameRound:
    """Records a complete round of the game"""
    round_number: int
    phases: List[RoundPhase] = field(default_factory=list)
    start_state: Dict[str, Any] = field(default_factory=dict)
    end_state: Dict[str, Any] = field(default_factory=dict)
    notable_events: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert phases to dictionaries
        data["phases"] = [p.to_dict() for p in self.phases]
        return data

    def add_notable_event(self, event: str) -> None:
        """Add a notable event to the round"""
        self.notable_events.append(event)


class GameRecord:
    """Game record manager that saves and retrieves detailed game data"""
    
    def __init__(self, record_dir="game_records"):
        """Initialize the game record manager
        
        Args:
            record_dir: Directory where game records will be saved
        """
        self.record_dir = Path(record_dir)
        self.record_dir.mkdir(exist_ok=True)
        self.readable_dir = Path("readable_records")
        self.readable_dir.mkdir(exist_ok=True)

        # Current game data
        self.game_id = None
        self.start_time = None
        self.players = []
        self.rounds = []
        self.current_round = None
        self.current_phase = None

    def start_game(self, player_ids: List[str], start_time: datetime = None) -> None:
        """Start recording a new game

        Args:
            player_ids: List of player IDs
            start_time: Optional start time (default: now)
        """
        self.start_time = start_time if start_time else datetime.now()
        
        # 创建玩家记录
        players = []
        for p_id in player_ids:
            players.append({
                "id": p_id,
                "name": f"Player {p_id[:8]}...",  # 使用ID前8个字符作为临时名称
                "balance": 100,  # 默认初始余额
                "items": []
            })
            
        self.players = players
        self.rounds = []

        # Record initial player states
        initial_states = {
            "players": [PlayerState(
                player_id=p["id"],
                player_name=p["name"],
                balance=p["balance"],
                items=p["items"] if "items" in p else []
            ).to_dict() for p in players],
            "prize_pool": 0,
            "timestamp": datetime.now().isoformat()
        }

        # Log the start of the game
        print(f"Started recording game {self.game_id} with {len(players)} players at {self.start_time}")

        # Create initial game data
        self.game_data = {
            "game_id": self.game_id,
            "start_time": self.start_time.isoformat(),
            "players": players,
            "initial_state": initial_states,
            "rounds": [],
            "winner": None,
            "end_time": None
        }

    def start_round(self, round_number: int, player_states: List[Dict[str, Any]], prize_pool: int) -> None:
        """Start recording a new round
        
        Args:
            round_number: The round number
            player_states: List of current player states
            prize_pool: Current prize pool amount
        """
        # Create start state snapshot
        start_state = {
            "players": [PlayerState(
                player_id=p["id"],
                player_name=p["name"],
                balance=p["balance"],
                items=p["items"] if "items" in p else [],
                active=p.get("is_active", True)
            ).to_dict() for p in player_states],
            "prize_pool": prize_pool,
            "timestamp": datetime.now().isoformat()
        }

        # Create a new round record
        self.current_round = GameRound(
            round_number=round_number,
            start_state=start_state
        )
        self.rounds.append(self.current_round)

        print(f"Started round {round_number} with prize pool {prize_pool}")

    def start_phase(self, phase_name: str) -> None:
        """Start recording a new phase within the current round
        
        Args:
            phase_name: Name of the phase (e.g., "item_phase", "persuasion_phase")
        """
        if not self.current_round:
            raise ValueError("Cannot start phase before starting a round")

        self.current_phase = RoundPhase(phase_name=phase_name)
        self.current_round.phases.append(self.current_phase)
        print(f"Started phase {phase_name} in round {self.current_round.round_number}")

    def end_phase(self) -> None:
        """End the current phase"""
        if not self.current_phase:
            return

        self.current_phase.end_time = datetime.now()
        print(f"Ended phase {self.current_phase.phase_name}")
        self.current_phase = None

    def end_round(self, player_states: List[Dict[str, Any]], prize_pool: int) -> None:
        """End the current round
        
        Args:
            player_states: List of current player states
            prize_pool: Current prize pool amount
        """
        if not self.current_round:
            return

        # Ensure all phases are ended
        self.end_phase()

        # Create end state snapshot
        end_state = {
            "players": [PlayerState(
                player_id=p["id"],
                player_name=p["name"],
                balance=p["balance"],
                items=p["items"] if "items" in p else [],
                active=p.get("is_active", True)
            ).to_dict() for p in player_states],
            "prize_pool": prize_pool,
            "timestamp": datetime.now().isoformat()
        }

        self.current_round.end_state = end_state
        print(f"Ended round {self.current_round.round_number}")

        # Update game data with rounds
        self.game_data["rounds"] = [r.to_dict() for r in self.rounds]

        # Autosave after each round
        self._autosave()

        self.current_round = None

    def record_action(self,
                      player_id: str,
                      player_name: str,
                      action_type: str,
                      target_id: Optional[str] = None,
                      target_name: Optional[str] = None,
                      amount: Optional[int] = None,
                      item_type: Optional[str] = None,
                      description: Optional[str] = None,
                      thinking_process: Optional[str] = None,
                      public_message: Optional[str] = None,
                      result: Optional[bool] = None) -> None:
        """Record a player action
        
        Args:
            player_id: ID of the player performing the action
            player_name: Name of the player performing the action
            action_type: Type of action (e.g., "buy_item", "persuade", "use_item")
            target_id: ID of the target player, if applicable
            target_name: Name of the target player, if applicable
            amount: Amount of coins involved, if applicable
            item_type: Type of item involved, if applicable
            description: Human-readable description of the action
            thinking_process: AI's reasoning process, if applicable
            public_message: Public message from the player, if applicable
            result: Whether the action succeeded, if applicable
        """
        if not self.current_phase:
            raise ValueError("Cannot record action before starting a phase")

        action = PlayerAction(
            player_id=player_id,
            player_name=player_name,
            action_type=action_type,
            target_id=target_id,
            target_name=target_name,
            amount=amount,
            item_type=item_type,
            description=description,
            thinking_process=thinking_process,
            public_message=public_message,
            result=result
        )

        self.current_phase.actions.append(action)
        print(f"Recorded {action_type} by {player_name}")

        # If it's a significant action, add it to notable events
        if action_type in ["persuade", "use_item"] and result is not None:
            result_str = "succeeded" if result else "failed"
            event = f"{player_name}'s {action_type} on {target_name or 'the game'} {result_str}"
            self.current_round.add_notable_event(event)

    def end_game(self, winner_id: str, winner_name: str, final_states: List[Dict[str, Any]], prize_pool: int) -> str:
        """End the game and save the full record
        
        Args:
            winner_id: ID of the winning player
            winner_name: Name of the winning player
            final_states: Final states of all players
            prize_pool: Final prize pool
        
        Returns:
            str: Path to the saved game record file
        """
        # Make sure everything is properly ended
        if self.current_phase:
            self.end_phase()
        if self.current_round:
            self.end_round(final_states, prize_pool)

        end_time = datetime.now()

        # Final game data
        self.game_data["end_time"] = end_time.isoformat()
        self.game_data["winner"] = {
            "id": winner_id,
            "name": winner_name
        }
        self.game_data["final_states"] = [PlayerState(
            player_id=p["id"],
            player_name=p["name"],
            balance=p["balance"],
            items=p["items"] if "items" in p else [],
            active=p.get("is_active", True)
        ).to_dict() for p in final_states]
        self.game_data["prize_pool"] = prize_pool
        self.game_data["total_rounds"] = len(self.rounds)
        self.game_data["duration_seconds"] = (end_time - self.start_time).total_seconds()

        # Save the record
        filepath = self.save_game_record()

        # Also generate a human-readable version
        readable_path = self.export_readable_record()

        print(f"Game {self.game_id} ended and recorded to {filepath}")
        print(f"Readable record saved to {readable_path}")

        return filepath

    def _autosave(self) -> None:
        """Autosave the current game data"""
        if not self.game_id:
            return

        # Create a copy of the game data to avoid modification issues
        game_data_copy = dict(self.game_data)

        # Add timestamp for autosave
        game_data_copy["autosave_time"] = datetime.now().isoformat()

        # Save to autosave file
        filepath = self.record_dir / f"{self.game_id}_autosave.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(game_data_copy, f, ensure_ascii=False, indent=2)

    def save_game_record(self) -> str:
        """Save the full game record
            
        Returns:
            str: Path to the saved file
        """
        if not self.game_id:
            raise ValueError("Cannot save record: no game in progress")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.game_id}_{timestamp}.json"
        filepath = self.record_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.game_data, f, ensure_ascii=False, indent=2)
            
        return str(filepath)
    
    def load_game_record(self, filename: str) -> Dict[str, Any]:
        """Load a game record from file
        
        Args:
            filename: Name of the record file
            
        Returns:
            Dict: Game data dictionary
        """
        filepath = self.record_dir / filename
        
        with open(filepath, "r", encoding="utf-8") as f:
            game_data = json.load(f)
            
        return game_data
    
    def list_game_records(self) -> List[str]:
        """List all game records
        
        Returns:
            List[str]: List of record filenames
        """
        return [f.name for f in self.record_dir.glob("*.json") if not f.name.endswith("_autosave.json")]
    
    def get_game_summary(self, filename: str) -> Dict[str, Any]:
        """Get a summary of a saved game
        
        Args:
            filename: Name of the record file
            
        Returns:
            Dict: Game summary
        """
        game_data = self.load_game_record(filename)
        
        summary = {
            "game_id": game_data.get("game_id", "Unknown"),
            "start_time": game_data.get("start_time", "Unknown"),
            "end_time": game_data.get("end_time", "Unknown"),
            "total_rounds": game_data.get("total_rounds", 0),
            "winner": game_data.get("winner", {}).get("name", "Unknown"),
            "player_count": len(game_data.get("players", [])),
            "players": [p.get("name", "Unknown Player") for p in game_data.get("players", [])],
            "duration_seconds": game_data.get("duration_seconds")
        }
        
        return summary
    
    def export_readable_record(self) -> str:
        """Export a human-readable version of the current game record
            
        Returns:
            str: Path to the exported file
        """
        if not self.game_id:
            raise ValueError("Cannot export record: no game in progress")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{self.game_id}_{timestamp}.txt"
        output_path = self.readable_dir / output_filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"Game ID: {self.game_id}\n")
            f.write(f"Start Time: {self.game_data.get('start_time', 'Unknown')}\n")
            f.write(f"End Time: {self.game_data.get('end_time', 'Unknown')}\n")
            f.write(f"Total Rounds: {len(self.rounds)}\n")
            f.write(f"Winner: {self.game_data.get('winner', {}).get('name', 'Unknown')}\n\n")

            f.write("Player Information:\n")
            for player in self.game_data.get("final_states", []):
                f.write(
                    f"  - {player.get('player_name', 'Unknown Player')}: Final Balance {player.get('balance', 0)} coins\n")

            f.write("\nGame Round Records:\n")
            for round_idx, round_data in enumerate(self.rounds, 1):
                f.write(f"\n==== Round {round_idx} ====\n")

                # Notable events for this round
                if round_data.notable_events:
                    f.write("\nNotable events:\n")
                    for event in round_data.notable_events:
                        f.write(f"  * {event}\n")

                # Phase records
                for phase in round_data.phases:
                    phase_name = phase.phase_name
                    f.write(f"\n-- {phase_name} --\n")
                    
                    # Record various actions
                    for action in phase.actions:
                        action_type = action.action_type
                        player_name = action.player_name

                        if action_type == "use_item":
                            item_type = action.item_type
                            target = action.target_name or "No target"
                            result = "successfully" if action.result else "unsuccessfully" if action.result is not None else ""
                            f.write(f"{player_name} {result} used {item_type} on {target}\n")

                        elif action_type == "persuade":
                            target = action.target_name or "No target"
                            amount = action.amount or 0
                            success = action.result
                            f.write(f"{player_name} attempted to persuade {target} to transfer {amount} coins: ")
                            f.write("Succeeded\n" if success else "Failed\n")

                        elif action_type == "buy_item":
                            item_type = action.item_type
                            amount = action.amount or 0
                            f.write(f"{player_name} bought {item_type} for {amount} coins\n")

                        elif action_type == "ai_speech":
                            if action.public_message:
                                f.write(f"{player_name} said: \"{action.public_message}\"\n")

                # Round end state
                f.write("\nEnd of Round State:\n")
                for player_state in round_data.end_state.get("players", []):
                    player_name = player_state.get("player_name", "Unknown Player")
                    balance = player_state.get("balance", 0)
                    items = [i.get("type", "Unknown Item") for i in player_state.get("items", []) if
                             not i.get("used", False)]
                    f.write(f"  - {player_name}: {balance} coins, Items: {', '.join(items) if items else 'None'}\n")
                
                f.write(f"Prize Pool: {round_data.end_state.get('prize_pool', 0)} coins\n")
            
        return str(output_path) 

    def get_all_actions(self) -> List[Dict[str, Any]]:
        """Get all actions recorded in this game
        
        Returns:
            List of actions from all rounds and phases
        """
        all_actions = []
        for round_obj in self.rounds:
            for phase in round_obj.phases:
                for action in phase.actions:
                    all_actions.append(action.to_dict())
        return all_actions
