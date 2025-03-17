'use client';

import { FC, useState } from 'react';
import { GameState } from '@/services/api';
import { WebSocketService } from '@/services/websocket';

interface GameControlsProps {
  gameState: GameState;
  wsService: WebSocketService;
}

const GameControls: FC<GameControlsProps> = ({ gameState, wsService }) => {
  const [targetPlayer, setTargetPlayer] = useState<string>('');
  const [amount, setAmount] = useState<number>(0);
  const [message, setMessage] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<string>('');

  const isGameActive = gameState.is_active && !gameState.winner;
  const otherPlayers = gameState.players.filter(p => p.id !== 'player1'); // 假设当前玩家ID为player1

  // 发送游戏动作
  const sendAction = (actionType: string) => {
    const actionData = {
      action_type: actionType,
      target_player: targetPlayer || undefined,
      amount: amount || undefined,
      message: message || undefined,
      item_type: selectedItem || undefined
    };

    wsService.sendMessage('game_action', actionData);

    // 重置表单
    setTargetPlayer('');
    setAmount(0);
    setMessage('');
    setSelectedItem('');
  };

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-4">
      <h2 className="text-xl font-bold text-white mb-4">游戏控制</h2>

      {!isGameActive && gameState.winner && (
        <div className="bg-green-700 text-white p-4 rounded-lg mb-4 text-center">
          <p className="text-lg font-bold">游戏已结束!</p>
          <p>获胜者: {gameState.winner}</p>
        </div>
      )}

      {!isGameActive && !gameState.winner && (
        <div className="bg-yellow-700 text-white p-4 rounded-lg mb-4 text-center">
          <p>游戏尚未开始或已暂停</p>
        </div>
      )}

      <div className="space-y-4">
        {/* 基本行动 */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => sendAction('invest')}
            disabled={!isGameActive}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            投资
          </button>

          <button
            onClick={() => sendAction('wait')}
            disabled={!isGameActive}
            className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-800 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            等待
          </button>
        </div>

        {/* 目标玩家选择 */}
        <div>
          <label className="block text-gray-300 text-sm font-bold mb-2">
            目标玩家
          </label>
          <select
            value={targetPlayer}
            onChange={(e) => setTargetPlayer(e.target.value)}
            disabled={!isGameActive}
            className="shadow bg-gray-700 text-white appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline"
          >
            <option value="">选择玩家...</option>
            {otherPlayers.map((player) => (
              <option key={player.id} value={player.id}>
                {player.name}
              </option>
            ))}
          </select>
        </div>

        {/* 金额输入 */}
        <div>
          <label className="block text-gray-300 text-sm font-bold mb-2">
            金额
          </label>
          <input
            type="number"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            min={0}
            disabled={!isGameActive}
            className="shadow bg-gray-700 text-white appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline"
          />
        </div>

        {/* 消息输入 */}
        <div>
          <label className="block text-gray-300 text-sm font-bold mb-2">
            消息
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={!isGameActive}
            className="shadow bg-gray-700 text-white appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline"
            rows={2}
          />
        </div>

        {/* 高级行动 */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => sendAction('persuade')}
            disabled={!isGameActive || !targetPlayer}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            说服
          </button>

          <button
            onClick={() => sendAction('use_item')}
            disabled={!isGameActive || !selectedItem}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            使用道具
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameControls; 