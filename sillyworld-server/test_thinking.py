import asyncio
from datetime import datetime
from ai import AI
from models import Player, GameState, GamePhase, ItemType, PersuasionRequest, GameAction, Item

async def test_ai_thinking():
    print("测试AI思考过程记录")
    
    # 创建两个测试玩家
    player1 = Player(
        id="player1",
        name="Rational AI",
        balance=80,
        is_ai=True,
        is_active=True,
        items=[
            Item(type=ItemType.SHIELD, price=10, used=False),
            Item(type=ItemType.AGGRESSIVE, price=15, used=False)
        ]
    )
    
    player2 = Player(
        id="player2",
        name="Aggressive AI",
        balance=90,
        is_ai=True,
        is_active=True,
        items=[
            Item(type=ItemType.INTEL, price=8, used=False),
            Item(type=ItemType.AGGRESSIVE, price=15, used=False)
        ]
    )
    
    # 创建游戏状态
    game_state = GameState(
        game_id="test-game-123",
        phase=GamePhase.PERSUASION_PHASE,
        players=[player1, player2],
        start_time=datetime.now(),
        last_update=datetime.now(),
        prize_pool=20,
        actions=[]
    )
    
    # 创建AI对象
    ai1 = AI(player1)
    ai2 = AI(player2)
    
    # 测试说服决策
    print("\n=== 测试说服决策 ===")
    persuade_action, thinking = await ai1._decide_persuasion(game_state)
    
    print(f"AI决策类型: {persuade_action.action_type}")
    print(f"决策描述: {persuade_action.description}")
    print(f"思考过程长度: {len(thinking) if thinking else 0}")
    print(f"思考过程摘要: {thinking[:100]}..." if thinking else "无思考过程")
    print(f"persuade_action是否包含thinking_process: {persuade_action.thinking_process is not None}")
    
    # 测试说服评估
    print("\n=== 测试说服评估 ===")
    request = PersuasionRequest(
        from_id="player1",
        from_name="Rational AI",
        to_id="player2",
        to_name="Aggressive AI",
        amount=15,
        message="Give me 15 tokens, I'll remember next round."
    )
    
    is_accepted, eval_thinking = await ai2.evaluate_persuasion(game_state, request)
    
    print(f"评估结果: {'接受' if is_accepted else '拒绝'}")
    print(f"思考过程长度: {len(eval_thinking) if eval_thinking else 0}")
    print(f"思考过程摘要: {eval_thinking[:100]}..." if eval_thinking else "无思考过程")
    
    # 创建思考记录
    thinking_action = GameAction(
        player_id="player2",
        action_type="thinking",
        description=f"AI player Aggressive AI's thinking process",
        timestamp=datetime.now(),
        thinking_process=eval_thinking
    )
    
    print(f"\n思考记录行动类型: {thinking_action.action_type}")
    print(f"思考记录行动是否包含thinking_process: {thinking_action.thinking_process is not None}")
    print(f"思考记录行动thinking_process长度: {len(thinking_action.thinking_process) if thinking_action.thinking_process else 0}")
    
    # 添加到游戏状态
    game_state.actions.append(persuade_action)
    game_state.actions.append(thinking_action)
    
    # 验证游戏状态中的记录
    print("\n=== 游戏状态中的记录 ===")
    print(f"游戏状态actions数量: {len(game_state.actions)}")
    
    for i, action in enumerate(game_state.actions):
        print(f"\n行动 {i+1}:")
        print(f"  类型: {action.action_type}")
        print(f"  玩家: {action.player_id}")
        print(f"  描述: {action.description}")
        print(f"  是否有思考过程: {action.thinking_process is not None}")
        print(f"  思考过程长度: {len(action.thinking_process) if action.thinking_process else 0}")
        
    print("\n测试完成")

if __name__ == "__main__":
    asyncio.run(test_ai_thinking()) 