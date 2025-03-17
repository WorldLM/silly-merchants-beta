from fastapi import HTTPException, status

class GameError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class GameNotFoundError(GameError):
    def __init__(self, game_id: str):
        super().__init__(f"Game {game_id} not found")

class PlayerNotFoundError(GameError):
    def __init__(self, player_id: str):
        super().__init__(f"Player {player_id} not found")

class InsufficientBalanceError(GameError):
    def __init__(self, player_id: str, required: int, current: int):
        super().__init__(
            f"Player {player_id} has insufficient balance. "
            f"Required: {required}, Current: {current}"
        )

class InvalidActionError(GameError):
    def __init__(self, action: str, reason: str):
        super().__init__(f"Invalid action '{action}': {reason}")

class GameStateError(GameError):
    def __init__(self, game_id: str, current_state: str, required_state: str):
        super().__init__(
            f"Game {game_id} is in invalid state. "
            f"Current: {current_state}, Required: {required_state}"
        )

class AIError(GameError):
    def __init__(self, player_id: str, error: str):
        super().__init__(f"AI error for player {player_id}: {error}")

class WebSocketError(GameError):
    def __init__(self, connection_id: str, error: str):
        super().__init__(f"WebSocket error for connection {connection_id}: {error}")

class ItemError(GameError):
    def __init__(self, item_type: str, error: str):
        super().__init__(f"Item error for {item_type}: {error}")

class ValidationError(GameError):
    def __init__(self, field: str, error: str):
        super().__init__(f"Validation error for {field}: {error}") 