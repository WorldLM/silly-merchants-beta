import asyncio
import json
from datetime import datetime
import random
import uuid
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Player, GameState, GameResult, GamePhase, GameAction, ItemType
from game import Game
from ai import AISystem
from items import ItemSystem
from websocket import ConnectionManager

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
from typing import List, Optional
from llm_client import LLMClient


# 定义请求模型
class ItemPurchaseRequest(BaseModel):
    item_type: str


class PlayerRequest(BaseModel):
    id: str
    name: str
    prompt: Optional[str] = ""
    is_ai: bool = True


class CreateGameRequest(BaseModel):
    players: List[PlayerRequest]


class BuyItemRequest(BaseModel):
    player_id: str


# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Arena API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://localhost:3006",
        "http://localhost:3007",
        "http://localhost:3008",
        "http://localhost:3009",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003",
        "http://localhost:8004",
        "http://localhost:8005",
        "http://localhost:8006",
        "http://localhost:8007",
        "http://localhost:8008",
        "http://localhost:8009",
        "*",  # Allow all origins to simplify development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add a logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"Request received: {request.method} {request.url}")
    try:
        response = await call_next(request)
        print(f"Response status code: {response.status_code}")
        return response
    except Exception as e:
        print(f"Error processing request: {e}")
        raise


# Initialize system components
llm_client = LLMClient(api_key=os.getenv("OPENROUTER_API_KEY"), default_model=os.getenv("DEFAULT_MODEL", "deepseek/deepseek-r1"))
ai_system = AISystem(llm_client=llm_client)
game_system = Game(ai_system)
connection_manager = ConnectionManager()


# API routes
@app.get("/")
async def root():
    return {"message": "Welcome to Agent Arena API!"}


# Add explicit OPTIONS route handler
@app.options("/api/{path:path}")
async def options_handler(path: str):
    print(f"Handling OPTIONS request: /api/{path}")
    return {}  # Return empty response


@app.post("/api/games", response_model=GameState)
async def create_game(request: CreateGameRequest):
    print(f"[DEBUG] Game creation request received, player count={len(request.players)}")
    try:
        print(f"[DEBUG] Request data: {request.dict()}")
        players = [
            Player(
                id=p.id, 
                name=p.name, 
                prompt=p.prompt if p.prompt else "", 
                balance=100,
                is_ai=p.is_ai
            )  # Each player starts with 100 tokens
            for p in request.players
        ]
        print(f"[DEBUG] Players created: {[p.dict() for p in players]}")
        
        game_state = game_system.create_game(players)
        print(f"[DEBUG] Game state created: {game_state.dict(exclude={'players'})}")
        
        print(f"[DEBUG] Game created successfully: game_id={game_state.game_id}")
        return game_state
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Failed to create game: {str(e)}")
        print(f"[ERROR] Traceback: {error_traceback}")
        raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}")


@app.get("/api/games/{game_id}")
async def get_game(game_id: str):
    game_state = game_system.games.get(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")

    # 转换为前端期望的格式
    response_data = {
        "game_id": game_state.game_id,
        "round": game_state.current_round,  # 转换字段名
        "phase": game_state.phase.value if isinstance(game_state.phase, GamePhase) else game_state.phase,
        "players": [player.dict() for player in game_state.players],
        "prize_pool": game_state.prize_pool,
        "current_player_id": None,  # 前端期望的字段，暂时设为None
        "status": game_state.status,
        "winner_id": game_state.winner,  # 转换字段名
        "created_at": game_state.start_time.isoformat(),  # 转换字段名和格式
        "updated_at": game_state.last_update.isoformat(),  # 转换字段名和格式
        "is_preparation": game_system.game_preparation.get(game_id, False)  # 添加准备阶段标志
    }

    return response_data


@app.post("/api/games/{game_id}/start")
async def start_game(game_id: str):
    print(f"[DEBUG] Received game start request: game_id={game_id}")
    game_state = game_system.games.get(game_id)
    if not game_state:
        print(f"[ERROR] Game not found: game_id={game_id}")
        raise HTTPException(status_code=404, detail="Game not found")

    # Set game to preparation phase, record start time
    print(f"[DEBUG] Game {game_id} entering preparation phase, AI has 10 seconds to consider item purchases")
    game_system.game_preparation[game_id] = True
    game_state.status = "preparation"
    game_state.phase = GamePhase.PREPARATION_PHASE  # Explicitly set the game phase
    preparation_start_time = datetime.now()

    # Broadcast game preparation phase start message
    preparation_action = GameAction(
        player_id="system",
        action_type="phase_change",
        description=f"Game preparation phase started, AI has 10 seconds to consider item purchase strategy",
        timestamp=preparation_start_time
    )
    await connection_manager.broadcast_game_action(game_id, preparation_action)

    # Asynchronously execute AI item purchase decisions
    try:
        # Create a decision task
        task = asyncio.create_task(ai_preparation_phase(game_id))  # Use the updated function signature
        print(f"[DEBUG] AI preparation phase task created: game_id={game_id}, task_id={id(task)}")
    except Exception as e:
        print(f"[ERROR] Failed to create AI preparation phase task: game_id={game_id}, error={e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start preparation phase: {str(e)}")

    # Return game state in format expected by frontend
    response_data = {
        "game_id": game_state.game_id,
        "round": game_state.current_round,
        "phase": game_state.phase.value if isinstance(game_state.phase, GamePhase) else game_state.phase,
        "players": [player.dict() for player in game_state.players],
        "prize_pool": game_state.prize_pool,
        "current_player_id": None,
        "status": game_state.status,
        "winner_id": game_state.winner,
        "created_at": game_state.start_time.isoformat(),
        "updated_at": game_state.last_update.isoformat(),
        "is_preparation": True
    }

    print(f"[DEBUG] Game preparation phase start response: game_id={game_id}")
    return response_data


@app.post("/api/games/{game_id}/ai_preparation_phase")
async def ai_preparation_phase(game_id: str):
    """
    Execute AI preparation phase for a game.
    Each player (AI or human) can purchase a maximum of 3 different types of items.
    """
    print(f"[DEBUG] Processing AI preparation phase for game_id={game_id}")

    try:
        # Get the game from state
        game = game_system.games.get(game_id)
        if not game:
            print(f"[ERROR] Game not found: game_id={game_id}")
            raise HTTPException(status_code=404, detail="Game not found")

        # Get game state
        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"[ERROR] Game state not found: game_id={game_id}")
            raise HTTPException(status_code=404, detail="Game state not found")

        # Check if game is in preparation phase
        if game_state.phase != GamePhase.PREPARATION_PHASE:
            print(f"[ERROR] Game is not in preparation phase: current_phase={game_state.phase}")
            raise HTTPException(status_code=400, detail="Game is not in preparation phase")

        # Add logic for AI preparation phase
        ai_actions = []
        for player in game_state.players:
            if player.is_ai and "AI" in player.name:
                print(f"[DEBUG] Processing AI preparation for player={player.name}, balance={player.balance}")

                # Count the number of different item types this player has already purchased
                purchased_item_types = set(item.type for item in player.items)

                # Limit purchases to 3 different types of items per player
                if len(purchased_item_types) >= 3:
                    print(
                        f"[DEBUG] Player {player.name} already has 3 different types of items, skipping further purchases")
                    continue

                # Get available items (considering budget and max 3 different item types limit)
                available_items = []
                for item_type in ItemType:
                    # Skip if player already has this type of item
                    if item_type in purchased_item_types:
                        continue

                    # Get item price from ItemSystem
                    item_price = ItemSystem.ITEM_PRICES.get(item_type)
                    if not item_price:
                        continue  # Skip if price not defined

                    # Check if player can afford the item
                    if player.balance >= item_price:
                        item_info = {
                            "type": item_type,
                            "price": item_price,
                            "name": str(item_type),
                            "description": f"{item_type} item"
                        }
                        available_items.append(item_info)

                # Shuffle items to randomize purchases
                random.shuffle(available_items)

                # AI will purchase items until it reaches 3 different types or runs out of money
                remaining_item_types_to_buy = 3 - len(purchased_item_types)
                items_to_purchase = available_items[:remaining_item_types_to_buy]

                for item_data in items_to_purchase:
                    item_type = item_data["type"]
                    price = item_data["price"]

                    # Check if player can still afford the item
                    # Check if player can still afford the item
                    if player.balance >= price:
                        # Create the item
                        new_item = ItemSystem.create_item(item_type)

                        # Add item to player's inventory
                        player.items.append(new_item)

                        # Deduct balance
                        player.balance -= price
                        # 将扣除的代币添加到奖池中
                        game_state.prize_pool += price

                        # Record action
                        action = GameAction(
                            player_id=player.id,
                            action_type="purchase",
                            amount=price,
                            description=f"AI player {player.name} purchased {item_data['name']} for {price} tokens",
                            timestamp=datetime.now()
                        )
                        game_state.actions.append(action)
                        ai_actions.append(action)

                        print(
                            f"[DEBUG] AI player {player.name} purchased {item_type} for {price} tokens, remaining balance={player.balance}")

                        # Add to purchased item types
                        purchased_item_types.add(item_type)
        # If all players have completed preparation, move to next phase
        all_prepared = True
        for player in game_state.players:
            if not player.is_ai and not player.prepared:
                all_prepared = False
                break

        if all_prepared:
            game_state.phase = GamePhase.NEGOTIATION_PHASE
            print(f"[DEBUG] All players prepared, advancing to {game_state.phase}")

            # Set game to active state
            game_state.status = "active"
            game_state.is_active = True

            # Start game rounds processing
            print(f"[DEBUG] Starting game rounds processing")
            task = asyncio.create_task(process_game_rounds(game_id))
            print(f"[DEBUG] Game rounds processing task created, task_id={id(task)}")

            # Broadcast game start message
            start_action = GameAction(
                player_id="system",
                action_type="phase_change",
                description=f"Game is now active, entering round 1",
                timestamp=datetime.now()
            )
            await connection_manager.broadcast_game_action(game_id, start_action)

        # Return AI actions
        return {"actions": [action.dict() for action in ai_actions]}

    except Exception as e:
        print(f"[ERROR] Exception in AI preparation phase: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/games/{game_id}/player/{player_id}/purchase_item")
async def purchase_item(
        game_id: str,
        player_id: str,
        item_request: ItemPurchaseRequest
):
    """
    Purchase an item for a player.
    Each player can purchase a maximum of 3 different types of items.
    """
    print(
        f"[DEBUG] Processing item purchase: game_id={game_id}, player_id={player_id}, item_type={item_request.item_type}")

    try:
        # Get the game state
        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"[ERROR] Game state not found: game_id={game_id}")
            raise HTTPException(status_code=404, detail="Game state not found")

        # Check if game is in preparation phase
        if game_state.phase != GamePhase.PREPARATION_PHASE:
            print(f"[ERROR] Game is not in preparation phase: current_phase={game_state.phase}")
            raise HTTPException(status_code=400, detail="Game is not in preparation phase")

        # Get the player
        player = next((p for p in game_state.players if p.id == player_id), None)
        if not player:
            print(f"[ERROR] Player not found: player_id={player_id}")
            raise HTTPException(status_code=404, detail="Player not found")

        # Check if the item type is valid
        if item_request.item_type not in game_system.ITEMS:
            print(f"[ERROR] Invalid item type: {item_request.item_type}")
            raise HTTPException(status_code=400, detail=f"Invalid item type: {item_request.item_type}")

        # Check if player already has 3 different types of items
        purchased_item_types = set(item.type for item in player.items)
        if len(purchased_item_types) >= 3:
            print(f"[ERROR] Player {player.name} already has 3 different types of items")
            raise HTTPException(status_code=400, detail="Maximum of 3 different item types allowed per player")

        # Check if player already has this type of item
        if item_request.item_type in purchased_item_types:
            print(f"[ERROR] Player {player.name} already has item of type {item_request.item_type}")
            raise HTTPException(status_code=400, detail=f"Player already has an item of type {item_request.item_type}")

        # Get item details
        item_details = game_system.ITEMS[item_request.item_type]
        price = item_details["price"]

        # Check if player has enough balance
        if player.balance < price:
            print(f"[ERROR] Insufficient balance: player_balance={player.balance}, item_price={price}")
            raise HTTPException(status_code=400, detail=f"Insufficient balance: need {price}, have {player.balance}")

        # Create the item
        new_item = ItemSystem.create_item(item_request.item_type)

        # Add item to player's inventory
        player.items.append(new_item)

        # Deduct balance
        player.balance -= price
        # 将扣除的代币添加到奖池中
        game_state.prize_pool += price

        # Record action
        action = GameAction(
            player_id=player.id,
            action_type="purchase",
            amount=price,
            description=f"Player {player.name} purchased {item_details['name']} for {price} tokens",
            timestamp=datetime.now()
        )
        game_state.actions.append(action)

        print(
            f"[DEBUG] Player {player.name} purchased {item_request.item_type} for {price} tokens, remaining balance={player.balance}")

        # Return success
        return {
            "success": True,
            "player": player.dict(),
            "item": new_item.dict(),
            "remaining_balance": player.balance
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Exception in purchase_item: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


async def process_game_rounds(game_id: str):
    """Process game rounds in a continuous loop until game ends"""
    try:
        print(f"[DEBUG] Starting game round processing: game_id={game_id}")

        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"[ERROR] Game not found: game_id={game_id}")
            return

        round_count = 0
        game_active = True

        while game_active and round_count < 30:  # Maximum 30 rounds for safety
            # Wait between rounds
            await asyncio.sleep(5)

            if game_id not in game_system.games:
                print(f"[DEBUG] Game no longer exists, stopping round processing: game_id={game_id}")
                return

            # Get updated game state
            game_state = game_system.games.get(game_id)
            if not game_state or not game_state.is_active:
                print(f"[DEBUG] Game is no longer active, stopping round processing: game_id={game_id}")
                return

            # Count active players
            active_players = [p for p in game_state.players if p.is_active]
            if len(active_players) <= 1:
                print(f"[DEBUG] Not enough active players ({len(active_players)}), ending game: game_id={game_id}")
                await end_game(game_id, "Not enough active players")
                return

            # Track previous balances to detect changes
            previous_balances = {player.id: player.balance for player in game_state.players}

            # Process round
            round_count += 1

            # Start with event phase
            # await process_event_phase(game_id, round_count)  # 注释掉事件阶段处理

            # Wait for event phase to complete
            # await asyncio.sleep(3)  # 注释掉等待事件阶段

            # Process negotiation phase
            await process_negotiation_phase(game_id, round_count)

            # Wait for negotiation phase to complete
            await asyncio.sleep(10)

            # Process actions phase
            await process_actions_phase(game_id, round_count)

            # Wait for actions to complete
            await asyncio.sleep(5)

            # Process stats and check for game end
            game_active = await process_stats_phase(game_id, round_count)

            # Check if any player has zero balance and no items, they are eliminated
            if game_active:
                for player in game_state.players:
                    if player.is_active and player.balance <= 0 and not player.items:
                        player.is_active = False
                print(f"[DEBUG] Player eliminated due to zero balance and no items: player_id={player.id}")

                        # Broadcast elimination message
                # Broadcast elimination message
                elimination = GameAction(
                    player_id=player.id,
                    action_type="elimination",
                    description=f"Player {player.name} has been eliminated due to lack of resources",
                    timestamp=datetime.now()
                )

            # Compare balances to highlight changes
            for player in game_state.players:
                prev_balance = previous_balances.get(player.id, 0)
                if player.balance != prev_balance:
                    balance_change = player.balance - prev_balance
                    sign = "+" if balance_change > 0 else ""

                    balance_action = GameAction(
                        player_id=player.id,
                        action_type="balance_update",
                        amount=balance_change,
                        description=f"Player {player.name}'s balance changed from {prev_balance} to {player.balance} ({sign}{balance_change})",
                        timestamp=datetime.now()
                    )
                    await connection_manager.broadcast_game_action(game_id, balance_action)

            print(f"[DEBUG] Completed round {round_count} for game_id={game_id}")

        # If we've reached maximum rounds, end the game
        if round_count >= 30 and game_active:
            print(f"[DEBUG] Maximum rounds reached, ending game: game_id={game_id}")
            await end_game(game_id, "Maximum rounds reached")

    except Exception as e:
        print(f"[ERROR] Error in game round processing: game_id={game_id}, error={e}")
        import traceback
        traceback.print_exc()

        # Try to end the game gracefully
        try:
            await end_game(game_id, f"Error: {str(e)}")
        except Exception as end_error:
            print(f"[ERROR] Failed to end game after error: game_id={game_id}, error={end_error}")


# 注释掉整个事件处理函数
'''
async def process_event_phase(game_id: str, round_num: int):
    """Process the event phase of a game round"""
    try:
        print(f"[DEBUG] Processing event phase: game_id={game_id}, round={round_num}")

        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"[ERROR] Game not found: game_id={game_id}")
            return

        # Set phase
        game_state.phase = GamePhase.EVENT_PHASE
        phase_start = GameAction(
            player_id="system",
            action_type="phase_change",
            description=f"Round {round_num}: Event Phase Started",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, phase_start)

        # Get event details
        event_types = ["dividend", "tax", "market_shift", "opportunity", "crisis"]

        # Ensure we have active players before choosing the event
        active_players = [p for p in game_state.players if p.is_active]
        if not active_players:
            print(f"[DEBUG] No active players, skipping event phase: game_id={game_id}")
            return

        # Choose a random event type
        event_type = random.choice(event_types)

        if event_type == "dividend":
            # Everyone with positive balance gets a small dividend
            for player in active_players:
                if player.balance > 0:
                    # Calculate dividend (5-10% of current balance)
                    rate = random.uniform(0.05, 0.1)
                    amount = max(1, int(player.balance * rate))
                    player.balance += amount

                    # Record action
                    action = GameAction(
                        player_id=player.id,
                        action_type="dividend",
                        amount=amount,
                        description=f"Player {player.name} received a dividend of {amount} tokens",
                        timestamp=datetime.now()
                    )
                    await connection_manager.broadcast_game_action(game_id, action)

        elif event_type == "tax":
            # Everyone pays a small tax
            for player in active_players:
                if player.balance > 0:
                    # Calculate tax (3-8% of current balance)
                    rate = random.uniform(0.03, 0.08)
                    amount = max(1, int(player.balance * rate))
                    tax_amount = min(amount, player.balance)  # Don't tax more than player has
                    player.balance -= tax_amount
                    game_state.prize_pool += tax_amount

                    # Record action
                    action = GameAction(
                        player_id=player.id,
                        action_type="tax",
                        amount=tax_amount,
                        description=f"Player {player.name} paid a tax of {tax_amount} tokens",
                        timestamp=datetime.now()
                    )
                    await connection_manager.broadcast_game_action(game_id, action)

        elif event_type == "market_shift":
            # Random market shift affects players differently
            shift_description = random.choice([
                "Technology stocks surge",
                "Commodity prices drop",
                "Currency fluctuations impact markets",
                "Interest rates change unexpectedly"
            ])

            # Broadcast event
            event_action = GameAction(
                player_id="system",
                action_type="market_shift",
                description=f"Market Event: {shift_description}",
                timestamp=datetime.now()
            )
            await connection_manager.broadcast_game_action(game_id, event_action)

            # Apply effects to players (some win, some lose)
            for player in active_players:
                if player.balance > 0:
                    # Determine if player wins or loses (-10% to +15% change)
                    rate = random.uniform(-0.1, 0.15)
                    amount = max(1, int(abs(player.balance * rate)))

                    if rate >= 0:
                        # Player gains
                        player.balance += amount
                        action_type = "market_gain"
                        description = f"Player {player.name} gained {amount} tokens from favorable market conditions"
                    else:
                        # Player loses (but not more than they have)
                        loss_amount = min(amount, player.balance)
                        player.balance -= loss_amount
                        amount = loss_amount
                        action_type = "market_loss"
                        description = f"Player {player.name} lost {amount} tokens from unfavorable market conditions"

                    # Record action
                    action = GameAction(
                        player_id=player.id,
                        action_type=action_type,
                        amount=amount,
                        description=description,
                        timestamp=datetime.now()
                    )
                    await connection_manager.broadcast_game_action(game_id, action)

        elif event_type == "opportunity":
            # A random player gets a windfall opportunity
            if active_players:  # Make sure we have players to choose from
                lucky_player = random.choice(active_players)

                # Calculate amount (20-30% of current balance, minimum 5)
                amount = max(5, int(lucky_player.balance * random.uniform(0.2, 0.3)))
                lucky_player.balance += amount

                # Record action
                action = GameAction(
                    player_id=lucky_player.id,
                    action_type="opportunity",
                    amount=amount,
                    description=f"Opportunity: Player {lucky_player.name} discovered a special opportunity and gained {amount} tokens",
                    timestamp=datetime.now()
                )
                await connection_manager.broadcast_game_action(game_id, action)

        elif event_type == "crisis":
            # A crisis affects all players, but impacts differ based on balance
            crisis_description = random.choice([
                "Economic recession hits markets",
                "Banking crisis creates uncertainty",
                "Supply chain disruptions affect businesses",
                "Regulatory changes impact financial institutions"
            ])

            # Broadcast event
            event_action = GameAction(
                player_id="system",
                action_type="crisis",
                description=f"Crisis Event: {crisis_description}",
                timestamp=datetime.now()
            )
            await connection_manager.broadcast_game_action(game_id, event_action)

            # Apply effects - richer players lose more, percentage-wise
            for player in active_players:
                if player.balance > 0:
                    # Base rate scaled by balance quartile (richer players lose more %)
                    all_balances = sorted([p.balance for p in active_players if p.balance > 0])
                    if not all_balances:  # Safety check
                        continue

                    # Calculate quartile position (roughly)
                    quartile = min(3,
                                   sum(1 for b in all_balances if b <= player.balance) // (len(all_balances) // 4 + 1))

                    # Higher quartile = higher loss rate
                    rate = 0.05 + (quartile * 0.02)  # 5% to 11% loss

                    # Calculate loss
                    amount = max(1, int(player.balance * rate))
                    loss_amount = min(amount, player.balance)  # Don't take more than they have
                    player.balance -= loss_amount

                    # Record action
                    action = GameAction(
                        player_id=player.id,
                        action_type="crisis_impact",
                        amount=loss_amount,
                        description=f"Player {player.name} lost {loss_amount} tokens due to the crisis",
                        timestamp=datetime.now()
                    )
                    await connection_manager.broadcast_game_action(game_id, action)

        # End phase
        game_state.phase = GamePhase.NEGOTIATION_PHASE
        phase_end = GameAction(
            player_id="system",
            action_type="phase_change",
            description=f"Round {round_num}: Event Phase Completed, Entering Negotiation Phase",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, phase_end)

    except Exception as e:
        print(f"[ERROR] Error in event phase: game_id={game_id}, error={e}")
        import traceback
        traceback.print_exc()
'''


async def process_negotiation_phase(game_id: str, round_num: int):
    """Process the negotiation phase of a game round"""
    try:
        print(f"[DEBUG] Processing negotiation phase: game_id={game_id}, round={round_num}")

        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"[ERROR] Game not found: game_id={game_id}")
            return

        # Set phase
        game_state.phase = GamePhase.NEGOTIATION_PHASE
        phase_start = GameAction(
            player_id="system",
            action_type="phase_change",
            description=f"Round {round_num}: Negotiation Phase Started",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, phase_start)

        # Process negotiation (mostly placeholder for future human interaction)
        # In this version, we'll just advance to persuasion phase

        # Set next phase
        game_state.phase = GamePhase.PERSUASION_PHASE
        phase_end = GameAction(
            player_id="system",
            action_type="phase_change",
            description=f"Round {round_num}: Negotiation Phase Completed, Entering Persuasion Phase",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, phase_end)

        # Process persuasion phase immediately
        persuasion_actions = await game_system.process_persuasion_phase(game_id)
        for action in persuasion_actions:
            await connection_manager.broadcast_game_action(game_id, action)

    except Exception as e:
        print(f"[ERROR] Error in negotiation phase: game_id={game_id}, error={e}")
        import traceback
        traceback.print_exc()


async def process_actions_phase(game_id: str, round_num: int):
    """Process the actions phase of a game round (settlement)"""
    try:
        print(f"[DEBUG] Processing actions phase (settlement): game_id={game_id}, round={round_num}")

        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"[ERROR] Game not found: game_id={game_id}")
            return

        # Process settlement phase
        settlement_actions = await game_system.process_settlement_phase(game_id)
        for action in settlement_actions:
            await connection_manager.broadcast_game_action(game_id, action)

    except Exception as e:
        print(f"[ERROR] Error in actions phase: game_id={game_id}, error={e}")
        import traceback
        traceback.print_exc()


async def process_stats_phase(game_id: str, round_num: int) -> bool:
    """Process the statistics phase of a game round and check if game should continue"""
    try:
        print(f"[DEBUG] Processing statistics phase: game_id={game_id}, round={round_num}")

        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"[ERROR] Game not found: game_id={game_id}")
            return False

        # Set phase
        game_state.phase = GamePhase.STATISTICS_PHASE
        phase_start = GameAction(
            player_id="system",
            action_type="phase_change",
            description=f"Round {round_num}: Statistics Phase Started",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, phase_start)

        # Process statistics phase
        statistics_actions = await game_system.process_statistics_phase(game_id)
        for action in statistics_actions:
            await connection_manager.broadcast_game_action(game_id, action)

        # Check if game should end
        should_end = game_system.check_game_end(game_id)
        if should_end:
            print(f"[DEBUG] Game end condition met: game_id={game_id}")
            await end_game(game_id, "Game end condition met")
            return False

        # Update round number in game state
        game_state.current_round += 1

        # Broadcast round end message
        round_end = GameAction(
            player_id="system",
            action_type="round_end",
            description=f"Round {round_num} completed. Starting round {round_num + 1} shortly.",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, round_end)

        return True  # Game should continue

    except Exception as e:
        print(f"[ERROR] Error in statistics phase: game_id={game_id}, error={e}")
        import traceback
        traceback.print_exc()
        return False  # Stop game on error


async def end_game(game_id: str, reason: str):
    """End a game with the given reason"""
    try:
        print(f"[DEBUG] Ending game: game_id={game_id}, reason={reason}")

        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"[ERROR] Game not found: game_id={game_id}")
            return

            # Set game as inactive
            game_state.is_active = False
        game_state.status = "completed"

        # Determine winner (player with highest balance)
        active_players = [p for p in game_state.players if p.is_active]
        if active_players:
            winner = max(active_players, key=lambda p: p.balance)
            game_state.winner = winner.id

            # Create game result record
            result = GameResult(
                game_id=game_id,
                winner_id=winner.id,
                final_balance=winner.balance,
                prize_pool=game_state.prize_pool,
                total_rounds=game_state.current_round,
                end_time=datetime.now(),
                winner_prompt=winner.prompt
            )

            # Broadcast game end message
            end_message = GameAction(
                player_id="system",
                action_type="game_end",
                description=f"Game ended: {reason}. Winner: {winner.name} with {winner.balance} tokens!",
                timestamp=datetime.now()
            )
            await connection_manager.broadcast_game_action(game_id, end_message)
        else:
            # No active players
            game_state.winner = None

            # Broadcast game end message
            end_message = GameAction(
                player_id="system",
                action_type="game_end",
                description=f"Game ended: {reason}. No winner declared.",
                timestamp=datetime.now()
            )
            await connection_manager.broadcast_game_action(game_id, end_message)

        print(f"[DEBUG] Game ended successfully: game_id={game_id}")

    except Exception as e:
        print(f"[ERROR] Error ending game: game_id={game_id}, error={e}")
        import traceback
        traceback.print_exc()


# WebSocket routes
@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    print(f"WebSocket连接请求: 游戏ID={game_id}, 玩家ID={player_id}")
    try:
        # 检查game_id是否存在
        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"WebSocket连接错误: 游戏ID={game_id}不存在")
            await websocket.close(code=1008, reason="游戏不存在")
            return

        await connection_manager.connect(websocket, game_id, player_id)
        print(f"WebSocket连接成功: 游戏ID={game_id}, 玩家ID={player_id}")

        try:
            while True:
                data = await websocket.receive_text()
                print(f"收到WebSocket消息: {data}")
                # 处理接收到的消息
                message = json.loads(data)
                if message["type"] == "game_action":
                    # 处理游戏动作
                    print(f"处理游戏动作: {message}")
        except Exception as e:
            print(f"WebSocket消息处理错误: {e}")
    except Exception as e:
        print(f"WebSocket连接错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"WebSocket连接关闭: 游戏ID={game_id}, 玩家ID={player_id}")
        connection_manager.disconnect(game_id, player_id)

# 添加专门为observer角色设计的WebSocket连接
@app.websocket("/ws/{game_id}/observer")
async def websocket_observer_endpoint(websocket: WebSocket, game_id: str):
    player_id = "observer"
    print(f"Observer WebSocket连接请求: 游戏ID={game_id}")
    try:
        # 检查game_id是否存在
        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"Observer WebSocket连接错误: 游戏ID={game_id}不存在")
            await websocket.close(code=1008, reason="游戏不存在")
            return

        await connection_manager.connect(websocket, game_id, player_id)
        print(f"Observer WebSocket连接成功: 游戏ID={game_id}")

        try:
            # 如果游戏状态存在，立即发送当前游戏状态
            if game_state:
                await connection_manager.broadcast_game_state(game_id, game_state)
                
            # 保持连接开放
            while True:
                # 只接收信息，observer不处理任何动作
                data = await websocket.receive_text()
                print(f"收到Observer WebSocket消息: {data}")
        except Exception as e:
            print(f"Observer WebSocket消息处理错误: {e}")
    except Exception as e:
        print(f"Observer WebSocket连接错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"Observer WebSocket连接关闭: 游戏ID={game_id}")
        connection_manager.disconnect(game_id, player_id)


@app.post("/api/games/{game_id}/buy_item")
async def buy_item(game_id: str, request: BuyItemRequest):
    print(f"【调试】接收到购买道具请求: 游戏ID={game_id}, 玩家ID={request.player_id}")

    # 检查游戏是否存在
    game_state = game_system.games.get(game_id)
    if not game_state:
        print(f"【错误】找不到游戏: 游戏ID={game_id}")
        raise HTTPException(status_code=404, detail="Game not found")

    # 检查是否处于准备阶段
    if not game_system.game_preparation.get(game_id, False):
        print(f"【错误】游戏不在准备阶段，无法购买道具: 游戏ID={game_id}")
        raise HTTPException(status_code=400, detail="Game is not in preparation phase")

    # 查找玩家
    player = next((p for p in game_state.players if p.id == request.player_id), None)
    if not player:
        print(f"【错误】找不到玩家: 游戏ID={game_id}, 玩家ID={request.player_id}")
        raise HTTPException(status_code=404, detail="Player not found")

    # 检查玩家是否已经有3种不同类型的道具
    player_items = game_system.player_item_types.get(game_id, {}).get(player.id, set())
    if len(player_items) >= 3:
        print(f"【错误】玩家已有3种不同类型的道具: 游戏ID={game_id}, 玩家ID={request.player_id}")
        raise HTTPException(status_code=400, detail="Player already has 3 different item types")

    # 检查玩家是否有足够的余额
    if player.balance < 10:
        print(f"【错误】玩家余额不足: 游戏ID={game_id}, 玩家ID={request.player_id}, 余额={player.balance}")
        raise HTTPException(status_code=400, detail="Player does not have enough balance")

    # 生成一个新的道具类型
    item_type = ItemSystem.get_random_item()

    # 确保不重复购买同一类型的道具
    attempts = 0
    while item_type.value in player_items and attempts < 10:
        item_type = ItemSystem.get_random_item()
        attempts += 1

    if item_type.value in player_items and attempts >= 10:
        print(f"【错误】无法找到新的道具类型: 游戏ID={game_id}, 玩家ID={request.player_id}")
        raise HTTPException(status_code=500, detail="Failed to find new item type")

    # 购买道具
    cost = 10
    player.balance -= cost
    game_state.prize_pool += cost

    # 添加道具到玩家库存
    item = ItemSystem.create_item(item_type)
    player.items.append(item)

    # 记录玩家已购买的道具类型
    if game_id in game_system.player_item_types and player.id in game_system.player_item_types[game_id]:
        game_system.player_item_types[game_id][player.id].add(item_type.value)

    # 记录动作
    action = GameAction(
        player_id=player.id,
        action_type="buy_item",
        amount=cost,
        item_type=item_type,
        description=f"Player {player.name} spent {cost} tokens to buy item: {item_type.value}, current balance: {player.balance}",
        timestamp=datetime.now()
    )

    # 广播动作
    await connection_manager.broadcast_game_action(game_id, action)

    print(f"【调试】玩家成功购买道具: 游戏ID={game_id}, 玩家ID={request.player_id}, 道具={item_type.value}")

    return {
        "success": True,
        "item_type": item_type.value,
        "player_balance": player.balance,
        "player_items": [{"type": item.type.value, "used": item.used} for item in player.items],
        "prize_pool": game_state.prize_pool
    }


@app.get("/api/games/{game_id}/thinking")
async def get_game_thinking(game_id: str):
    """
    Get AI thinking processes in the game
    """
    print(f"【DEBUG】Getting AI thinking process: game_id={game_id}")
    
    # Check if game exists
    game_state = game_system.games.get(game_id)
    if not game_state:
        print(f"【DEBUG】Game not found: {game_id}")
        raise HTTPException(status_code=404, detail="Game not found")
    
    print(f"【DEBUG】Game state has {len(game_state.actions)} actions")
    
    # Debugging: list all action types
    action_types = [action.action_type for action in game_state.actions]
    print(f"【DEBUG】Action types in game_state: {action_types}")
    
    # Filter actions with thinking process
    thinking_actions = []
    acceptable_types = ["thinking", "ai_thinking", "persuade", "use_item", "buy_item"]
    
    for action in game_state.actions:
        has_thinking = action.thinking_process is not None and len(action.thinking_process) > 0
        print(f"【DEBUG】Checking action: type={action.action_type}, player={action.player_id}, has_thinking={has_thinking}")
        
        if has_thinking and (action.action_type in acceptable_types):
            thinking_data = {
                "player_id": action.player_id,
                "action_type": action.action_type,
                "player_name": next((p.name for p in game_state.players if p.id == action.player_id), "Unknown player"),
                "timestamp": action.timestamp,
                "thinking_process": action.thinking_process,
                "description": action.description
            }
            thinking_actions.append(thinking_data)
            print(f"【DEBUG】Added thinking action for player {thinking_data['player_name']}, type={action.action_type}")
    
    print(f"【DEBUG】Found {len(thinking_actions)} thinking actions")
    return {"thinking_actions": thinking_actions}


@app.get("/api/games/{game_id}/debug_actions")
async def get_game_debug_actions(game_id: str):
    """
    Debug: Get all actions in the game
    """
    print(f"【DEBUG】Getting all game actions: game_id={game_id}")
    
    # Check if game exists
    game_state = game_system.games.get(game_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Return all action information
    all_actions = [{"type": action.action_type, 
                     "player_id": action.player_id, 
                     "description": action.description,
                     "has_thinking": action.thinking_process is not None,
                     "timestamp": action.timestamp} 
                    for action in game_state.actions]
    
    # Filter all AI thinking actions
    thinking_actions = [{"type": action.action_type, 
                         "player_id": action.player_id, 
                         "description": action.description,
                         "thinking_process": action.thinking_process,
                         "timestamp": action.timestamp} 
                        for action in game_state.actions 
                        if action.action_type == "thinking" or action.action_type == "ai_thinking" or action.thinking_process is not None]
    
    return {"actions": all_actions, "thinking_actions": thinking_actions}


@app.post("/api/admin/reset")
async def reset_server():
    """
    Admin endpoint to reset the server state completely
    This clears all games and resets the game system
    """
    try:
        print(f"【ADMIN】开始重置服务器状态")
        
        # 获取当前游戏数量
        game_count = len(game_system.games)
        print(f"【ADMIN】当前有 {game_count} 个游戏")
        
        # 清空所有游戏数据
        game_system.games = {}
        
        # 重置其他状态
        game_system.player_item_types = {}
        game_system.round_item_usage = {}
        game_system.game_preparation = {}
        game_system.aggressive_users = {}
        game_system.shield_users = {}
        game_system.equalizer_users = {}
        game_system.equalizer_targets = {}
        
        print(f"【ADMIN】服务器状态重置完成。清除了 {game_count} 个游戏")
        return {"status": "success", "message": f"服务器重置完成。清除了 {game_count} 个游戏"}
    except Exception as e:
        import traceback
        error_msg = f"重置服务器时发生错误: {str(e)}"
        print(f"【ERROR/ADMIN】{error_msg}")
        traceback.print_exc()
        return {"status": "error", "message": error_msg}


@app.get("/api/health")
async def health_check():
    """
    Simple health check endpoint to verify the server is running
    """
    return {"status": "ok", "server_time": datetime.now().isoformat()}


@app.post("/api/games/{game_id}/process_round")
async def process_game_round(game_id: str):
    """
    处理游戏的一个完整回合，包括所有阶段（物品、说服等）
    """
    print(f"【DEBUG】Processing complete round for game {game_id}")
    
    try:
        # 获取游戏状态
        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"【ERROR】Game not found: game_id={game_id}")
            raise HTTPException(status_code=404, detail="Game not found")
        
        # 处理回合
        await game_system.process_round(game_id)
        
        # 获取最新游戏状态
        updated_game_state = game_system.games.get(game_id)
        
        # 返回前端预期的格式
        response_data = {
            "game_id": updated_game_state.game_id,
            "round": updated_game_state.current_round,
            "phase": updated_game_state.phase.value if isinstance(updated_game_state.phase, GamePhase) else updated_game_state.phase,
            "players": [player.dict() for player in updated_game_state.players],
            "prize_pool": updated_game_state.prize_pool,
            "current_player_id": None,
            "status": updated_game_state.status,
            "winner_id": updated_game_state.winner,
            "created_at": updated_game_state.start_time.isoformat(),
            "updated_at": updated_game_state.last_update.isoformat(),
            "is_preparation": updated_game_state.phase == GamePhase.PREPARATION_PHASE
        }
        
        return response_data
    
    except Exception as e:
        print(f"【ERROR】Failed to process round: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process round: {str(e)}")


@app.post("/api/games/{game_id}/simulate")
async def simulate_game(game_id: str):
    """
    模拟游戏流程，直接到说服阶段
    """
    print(f"【DEBUG】Simulating game process to reach persuasion phase: game_id={game_id}")
    
    try:
        # 获取游戏状态
        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"【ERROR】Game not found: game_id={game_id}")
            raise HTTPException(status_code=404, detail="Game not found")
        
        # 完成准备阶段
        if game_state.phase == GamePhase.PREPARATION_PHASE:
            print(f"【DEBUG】Game in preparation phase, completing AI item purchases...")
            
            # 为每个AI玩家购买物品
            for player in game_state.players:
                if not player.is_ai:
                    continue
                    
                # 简单起见，每个AI玩家购买三种道具
                items_to_buy = [ItemType.SHIELD, ItemType.INTEL, ItemType.AGGRESSIVE]
                prices = {"shield": 10, "intel": 8, "aggressive": 15}
                
                for item_type in items_to_buy:
                    type_name = item_type.value
                    price = prices.get(type_name, 10)
                    
                    # 检查余额是否足够
                    if player.balance < price:
                        continue
                        
                    # 购买道具
                    player.balance -= price
                        # 将扣除的代币添加到奖池中
                    game_state.prize_pool += price
                    player.items.append(ItemSystem.create_item(item_type))
                    
                    # 记录购买行为
                    purchase_action = GameAction(
                        player_id=player.id,
                        action_type="buy_item",
                        description=f"{player.name} purchased {type_name} for {price} tokens",
                        timestamp=datetime.now(),
                        item_type=item_type
                    )
                    game_state.actions.append(purchase_action)
            
            # 修改游戏阶段到说服阶段
            game_state.phase = GamePhase.PERSUASION_PHASE
            game_state.status = "active"
            
            print(f"【DEBUG】Finished preparation phase, moved to persuasion phase")
        
        # 如果已经在说服阶段，直接处理
        if game_state.phase == GamePhase.PERSUASION_PHASE:
            print(f"【DEBUG】Processing persuasion phase for game {game_id}")
            
            # 处理说服阶段
            persuasion_actions = await game_system._process_persuasion_phase(game_state)
            print(f"【DEBUG】Processed persuasion phase, generated {len(persuasion_actions)} actions")
            
            # 检查是否有思考过程记录
            thinking_actions = [a for a in persuasion_actions if a.thinking_process is not None and a.thinking_process != ""]
            print(f"【DEBUG】Found {len(thinking_actions)} thinking actions")
            
            for i, action in enumerate(thinking_actions):
                print(f"【DEBUG】Thinking action {i+1}: player={action.player_id}, type={action.action_type}")
                print(f"【DEBUG】  - Thinking process length: {len(action.thinking_process) if action.thinking_process else 0}")
        
        # 获取最新游戏状态
        updated_game_state = game_system.games.get(game_id)
        
        # 返回前端预期的格式
        response_data = {
            "game_id": updated_game_state.game_id,
            "round": updated_game_state.current_round,
            "phase": updated_game_state.phase.value if isinstance(updated_game_state.phase, GamePhase) else updated_game_state.phase,
            "players": [player.dict() for player in updated_game_state.players],
            "prize_pool": updated_game_state.prize_pool,
            "current_player_id": None,
            "status": updated_game_state.status,
            "winner_id": updated_game_state.winner,
            "created_at": updated_game_state.start_time.isoformat(),
            "updated_at": updated_game_state.last_update.isoformat(),
            "is_preparation": updated_game_state.phase == GamePhase.PREPARATION_PHASE
        }
        
        return response_data
    
    except Exception as e:
        print(f"【ERROR】Failed to simulate game: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to simulate game: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8009, reload=True)
