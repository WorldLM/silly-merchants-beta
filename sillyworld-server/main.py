import asyncio
import json
from datetime import datetime

from models import Player, GameState, GameResult, GamePhase, GameAction
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

# 加载环境变量
load_dotenv()

app = FastAPI(title="Agent Arena API")

# 配置CORS
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
        "*",  # 允许所有来源，简化开发环境中的问题
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加一个日志中间件
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"收到请求: {request.method} {request.url}")
    try:
        response = await call_next(request)
        print(f"响应状态码: {response.status_code}")
        return response
    except Exception as e:
        print(f"处理请求时出错: {e}")
        raise

# 初始化系统组件
ai_system = AISystem(openrouter_api_key=os.getenv("OPENROUTER_API_KEY"))
game_system = Game(ai_system)
connection_manager = ConnectionManager()

# API路由
@app.get("/")
async def root():
    return {"message": "Welcome to Agent Arena API!"}

# 添加显式的OPTIONS路由处理器
@app.options("/api/{path:path}")
async def options_handler(path: str):
    print(f"处理OPTIONS请求: /api/{path}")
    return {}  # 返回空响应

class CreateGameRequest(BaseModel):
    players: List[Player]

@app.post("/api/games", response_model=GameState)
async def create_game(request: CreateGameRequest):
    print(f"【调试】接收到创建游戏请求，玩家数量={len(request.players)}")
    try:
        players = [
            Player(id=p.id, name=p.name, prompt=p.prompt, balance=100)  # 每位玩家初始代币为100
            for p in request.players
        ]
        game_state = game_system.create_game(players)
        # 确保奖池金额固定为每位玩家的10代币入场费总和
        game_state.prize_pool = len(players) * 10
        print(f"【调试】游戏创建成功: 游戏ID={game_state.game_id}")
        return game_state
    except Exception as e:
        print(f"【错误】创建游戏失败: {str(e)}")
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
    print(f"【调试】接收到启动游戏请求: 游戏ID={game_id}")
    game_state = game_system.games.get(game_id)
    if not game_state:
        print(f"【错误】找不到游戏: 游戏ID={game_id}")
        raise HTTPException(status_code=404, detail="Game not found")
    
    # 设置游戏为准备阶段，记录开始时间
    print(f"【调试】游戏 {game_id} 进入准备阶段，AI有10秒时间考虑购买道具")
    game_system.game_preparation[game_id] = True
    game_state.status = "preparation"
    preparation_start_time = datetime.now()
    
    # 广播游戏准备阶段开始的消息
    preparation_action = GameAction(
        player_id="system",
        action_type="preparation_start",
        description=f"游戏准备阶段开始，AI有10秒时间考虑购买道具策略",
        timestamp=preparation_start_time
    )
    await connection_manager.broadcast_game_action(game_id, preparation_action)
    
    # 异步执行AI道具购买决策
    try:
        # 创建一个决策任务
        task = asyncio.create_task(ai_preparation_phase(game_id, 10))  # 10秒准备时间
        print(f"【调试】AI准备阶段任务已创建: 游戏ID={game_id}, 任务ID={id(task)}")
    except Exception as e:
        print(f"【错误】创建AI准备阶段任务失败: 游戏ID={game_id}, 错误={e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start preparation phase: {str(e)}")
    
    # 返回与前端期望格式一致的游戏状态
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
    
    print(f"【调试】游戏准备阶段开始响应: 游戏ID={game_id}")
    return response_data

async def ai_preparation_phase(game_id: str, preparation_time: int = 10):
    """AI准备阶段处理，允许AI购买道具，持续指定的时间（默认10秒）"""
    try:
        print(f"【调试】开始AI准备阶段: 游戏ID={game_id}")
        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"【错误】找不到游戏: 游戏ID={game_id}")
            return
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 广播AI思考开始的消息
        for player in game_state.players:
            ai_thinking = GameAction(
                player_id=player.id,
                action_type="ai_thinking",
                description=f"AI玩家 {player.name} 正在思考购买哪些道具...",
                timestamp=datetime.now()
            )
            await connection_manager.broadcast_game_action(game_id, ai_thinking)
        
        # 等待准备时间结束
        await asyncio.sleep(preparation_time)
        
        # 为每个AI玩家购买道具
        for player in game_state.players:
            player_items = game_system.player_item_types.get(game_id, {}).get(player.id, set())
            print(f"【调试】AI决策购买道具: 玩家ID={player.id}, 已有道具类型数={len(player_items)}, 类型={player_items}")
            
            # 模拟AI决策，随机决定购买1-3个道具
            import random
            target_item_count = random.randint(1, 3)
            
            # 广播AI决策结果
            decision_log = GameAction(
                player_id=player.id,
                action_type="ai_decision",
                description=f"AI玩家 {player.name} 决定购买 {target_item_count} 个不同类型的道具",
                timestamp=datetime.now()
            )
            await connection_manager.broadcast_game_action(game_id, decision_log)
            
            # 购买道具直到达到目标数量或资金不足
            while len(player_items) < target_item_count and player.balance >= 10:
                # 尝试购买一个新类型的道具
                item_type = ItemSystem.get_random_item()
                
                # 确保不重复购买同一类型的道具
                attempts = 0
                while item_type.value in player_items and attempts < 10:
                    item_type = ItemSystem.get_random_item()
                    attempts += 1
                
                if item_type.value not in player_items or attempts >= 10:
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
                        description=f"AI玩家 {player.name} 花费 {cost} 代币购买了道具: {item_type.value}，当前余额: {player.balance}",
                        timestamp=datetime.now()
                    )
                    
                    # 广播动作
                    await connection_manager.broadcast_game_action(game_id, action)
                    
                    print(f"【调试】AI玩家购买道具: 玩家ID={player.id}, 道具={item_type.value}")
                    
                    # 更新玩家道具记录
                    player_items = game_system.player_item_types.get(game_id, {}).get(player.id, set())
        
        # 准备阶段结束，开始游戏
        game_state.is_active = True
        game_state.status = "active"
        
        # 结束准备阶段，玩家不能再购买道具
        game_system.game_preparation[game_id] = False
        
        # 广播准备阶段结束消息
        end_prep_action = GameAction(
            player_id="system",
            action_type="preparation_end",
            description=f"准备阶段结束，游戏正式开始！共有 {len(game_state.players)} 位玩家参与",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, end_prep_action)
        
        print(f"【调试】游戏准备阶段结束，开始游戏: 游戏ID={game_id}")
        
        # 启动游戏回合处理
        task = asyncio.create_task(process_game_rounds(game_id))
        print(f"【调试】游戏回合处理任务已创建: 游戏ID={game_id}, 任务ID={id(task)}")
        
    except Exception as e:
        print(f"【错误】AI准备阶段处理出错: 游戏ID={game_id}, 错误={e}")
        import traceback
        traceback.print_exc()

async def process_game_rounds(game_id: str):
    """在后台处理游戏回合"""
    try:
        print(f"【调试】开始处理游戏回合: 游戏ID={game_id}")
        game_state = game_system.games.get(game_id)
        if not game_state:
            print(f"【错误】找不到游戏: 游戏ID={game_id}")
            return
            
        print(f"【调试】游戏状态检查: ID={game_id}, is_active={game_state.is_active}, status={game_state.status}")
        if not game_state.is_active:
            print(f"【错误】游戏不处于活动状态: 游戏ID={game_id}")
            return

        # 处理一轮游戏
        print(f"【调试】处理游戏回合: 游戏ID={game_id}, 回合={game_state.current_round}, 当前阶段={game_state.phase}")
        print(f"【调试】玩家状态: {[(p.name, p.balance, p.is_active) for p in game_state.players]}")
        
        # 记录玩家在回合开始时的状态，用于跟踪变化
        previous_player_states = {player.id: player.dict() for player in game_state.players}
        
        # 记录玩家状态（可观察）
        status_action = GameAction(
            player_id="system",
            action_type="round_start",
            description=f"回合 {game_state.current_round + 1} 开始，当前阶段: {game_state.phase}，奖池: {game_state.prize_pool} 代币",
            timestamp=datetime.now()
        )
        print(f"【调试】广播回合开始: {status_action.description}")
        await connection_manager.broadcast_game_action(game_id, status_action)
        
        # 输出玩家初始状态
        for player in game_state.players:
            if player.is_active:
                # 更详细的道具状态日志
                items_info = "，".join([f"{item.type.value}" + ("(已使用)" if item.used else "") for item in player.items]) if player.items else "无"
                player_status = GameAction(
                    player_id=player.id,
                    action_type="player_status",
                    description=f"玩家 {player.name} 当前状态：资金 {player.balance} 代币，道具: {items_info}",
                    timestamp=datetime.now()
                )
                print(f"【调试】广播玩家状态: {player_status.description}")
                await connection_manager.broadcast_game_action(game_id, player_status)
                
                # 记录AI玩家的决策过程（如果是AI玩家）
                if "AI" in player.name:
                    ai_decision_log = GameAction(
                        player_id=player.id,
                        action_type="ai_decision",
                        description=f"AI玩家 {player.name} 思考中: 当前回合={game_state.current_round+1}, 阶段={game_state.phase}, 资金={player.balance}",
                        timestamp=datetime.now()
                    )
                    print(f"【调试】AI决策日志: {ai_decision_log.description}")
                    await connection_manager.broadcast_game_action(game_id, ai_decision_log)
        
        # 等待2秒，让玩家有时间查看初始状态
        await asyncio.sleep(2)
        
        # AI思考阶段 - 让玩家感受到AI在"思考"
        for player in game_state.players:
            if player.is_active and "AI" in player.name:
                thinking_action = GameAction(
                    player_id=player.id,
                    action_type="ai_thinking",
                    description=f"AI玩家 {player.name} 正在分析局势，规划本轮策略...",
                    timestamp=datetime.now()
                )
                await connection_manager.broadcast_game_action(game_id, thinking_action)
        
        # 等待2秒，模拟AI思考时间
        await asyncio.sleep(2)
        
        # 道具阶段
        print(f"【调试】即将进入道具阶段: 游戏ID={game_id}")
        item_phase_action = GameAction(
            player_id="system",
            action_type="phase_change",
            description=f"回合 {game_state.current_round+1} 道具阶段开始",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, item_phase_action)
        
        # 处理道具阶段
        item_actions = await game_system.process_item_phase(game_id)
        for action in item_actions:
            await connection_manager.broadcast_game_action(game_id, action)
            print(f"【调试】广播道具阶段动作: {action.action_type} - {action.description}")
        
        # 等待1秒，让玩家有时间查看道具阶段结果
        await asyncio.sleep(1)
        
        # 说服阶段
        print(f"【调试】即将进入说服阶段: 游戏ID={game_id}")
        persuasion_phase_action = GameAction(
            player_id="system",
            action_type="phase_change",
            description=f"回合 {game_state.current_round+1} 说服阶段开始",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, persuasion_phase_action)
        
        # 处理说服阶段
        persuasion_actions = await game_system.process_persuasion_phase(game_id)
        for action in persuasion_actions:
            await connection_manager.broadcast_game_action(game_id, action)
            print(f"【调试】广播说服阶段动作: {action.action_type} - {action.description}")
        
        # 等待1秒，让玩家有时间查看说服阶段结果
        await asyncio.sleep(1)
        
        # 结算阶段
        print(f"【调试】即将进入结算阶段: 游戏ID={game_id}")
        settlement_phase_action = GameAction(
            player_id="system",
            action_type="phase_change",
            description=f"回合 {game_state.current_round+1} 结算阶段开始",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, settlement_phase_action)
        
        # 处理结算阶段
        settlement_actions = await game_system.process_settlement_phase(game_id)
        for action in settlement_actions:
            await connection_manager.broadcast_game_action(game_id, action)
            print(f"【调试】广播结算阶段动作: {action.action_type} - {action.description}")
        
        # 等待1秒，让玩家有时间查看结算阶段结果
        await asyncio.sleep(1)
        
        # 统计阶段
        print(f"【调试】即将进入统计阶段: 游戏ID={game_id}")
        statistics_phase_action = GameAction(
            player_id="system",
            action_type="phase_change",
            description=f"回合 {game_state.current_round+1} 统计阶段开始",
            timestamp=datetime.now()
        )
        await connection_manager.broadcast_game_action(game_id, statistics_phase_action)
        
        # 处理统计阶段
        statistics_actions = await game_system.process_statistics_phase(game_id)
        for action in statistics_actions:
            await connection_manager.broadcast_game_action(game_id, action)
            print(f"【调试】广播统计阶段动作: {action.action_type} - {action.description}")
        
        # 回合结束，更新游戏状态
        game_state.current_round += 1
        game_state.last_update = datetime.now()
        
        # 回合结束状态记录
        end_status_action = GameAction(
            player_id="system",
            action_type="round_end",
            description=f"回合 {game_state.current_round} 结束，下一回合为回合 {game_state.current_round+1}，奖池现在为 {game_state.prize_pool} 代币",
            timestamp=datetime.now()
        )
        print(f"【调试】广播回合结束: {end_status_action.description}")
        await connection_manager.broadcast_game_action(game_id, end_status_action)
        
        # 检查游戏是否结束
        is_game_end = game_system.check_game_end(game_id)
        if is_game_end:
            print(f"【调试】游戏结束条件满足，执行结束流程: 游戏ID={game_id}")
            end_actions = await game_system.end_game(game_id)
            for action in end_actions:
                await connection_manager.broadcast_game_action(game_id, action)
            game_state.is_active = False
            
            # 游戏结束，广播游戏结束消息
            if game_state.winner:
                # 发送详细的结束消息
                winner_name = next((p.name for p in game_state.players if p.id == game_state.winner), '未知')
                end_message = GameAction(
                    player_id="system",
                    action_type="game_completed",
                    description=f"游戏结束! 胜利者: {winner_name}，最终奖金: {game_state.prize_pool} 代币",
                    timestamp=datetime.now()
                )
                print(f"【调试】广播游戏结束: {end_message.description}")
                await connection_manager.broadcast_game_action(game_id, end_message)
                await connection_manager.broadcast_game_end(game_id, game_state.winner)
        else:
            # 广播游戏状态更新
            print(f"【调试】广播游戏状态: 游戏ID={game_id}, 回合={game_state.current_round}, 阶段={game_state.phase}")
            broadcast_success = await connection_manager.broadcast_game_state(game_id, game_state)
            
            if not broadcast_success:
                print(f"【警告】没有活跃的WebSocket连接，但游戏回合处理将继续: 游戏ID={game_id}")
            
            # 继续下一轮的处理
            if game_state.is_active:
                # 安排下一轮处理
                delay = 3  # 延迟3秒
                print(f"【调试】计划下一轮处理: 游戏ID={game_id}, 延迟={delay}秒")
                await asyncio.sleep(delay)
                print(f"【调试】启动下一轮处理任务: 游戏ID={game_id}")
                
                try:
                    # 使用独立的任务处理以确保不会中断
                    next_round_task = asyncio.create_task(process_game_rounds(game_id))
                    print(f"【调试】下一轮处理任务已创建: 游戏ID={game_id}, 任务ID={id(next_round_task)}")
                except Exception as e:
                    print(f"【错误】创建下一轮处理任务失败: 游戏ID={game_id}, 错误={e}")
                    import traceback
                    traceback.print_exc()
                    # 尝试重新调度
                    print(f"【调试】尝试重新调度下一轮处理: 游戏ID={game_id}")
                    asyncio.get_event_loop().call_later(5, lambda: asyncio.create_task(process_game_rounds(game_id)))
            else:
                print(f"【调试】游戏已结束: 游戏ID={game_id}")
                
    except Exception as e:
        print(f"【错误】处理游戏回合时出错: 游戏ID={game_id}, 错误={e}")
        # 记录堆栈跟踪以便调试
        import traceback
        traceback.print_exc()

# WebSocket路由
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

class BuyItemRequest(BaseModel):
    player_id: str

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
        description=f"玩家 {player.name} 花费 {cost} 代币购买了道具: {item_type.value}，当前余额: {player.balance}",
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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True) 