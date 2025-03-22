'use client';

import { FC, useState } from 'react';
import { GameState } from '@/services/api';
import { WebSocketService } from '@/services/websocket';

interface GameControlsProps {
  gameId: string | null;
  gameState: GameState;
  onAction: (actionType: string, actionData?: any) => void;
  isUserActive: boolean;
  userPlayerRole: string | null;
}

const GameControls: FC<GameControlsProps> = ({ 
  gameId, 
  gameState, 
  onAction,
  isUserActive,
  userPlayerRole 
}) => {
  const [targetPlayer, setTargetPlayer] = useState<string>('');
  const [amount, setAmount] = useState<number>(0);
  const [message, setMessage] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<string>('');

  const isGameActive = gameState.status === 'active' && !gameState.winner_id;
  const otherPlayers = gameState.players.filter(p => p.id !== userPlayerRole);

  // Send game action
  const sendAction = (actionType: string) => {
    const actionData = {
      actionType: actionType,
      targetPlayerId: targetPlayer || undefined,
      amount: amount || undefined,
      message: message || undefined,
      itemType: selectedItem || undefined
    };

    // Call the onAction callback function
    onAction(actionType, actionData);

    // Reset form
    setTargetPlayer('');
    setAmount(0);
    setMessage('');
    setSelectedItem('');
  };

  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-4">
      <h2 className="text-xl font-bold text-white mb-4">Game Controls</h2>

      {!isGameActive && gameState.winner_id && (
        <div className="bg-green-700 text-white p-4 rounded-lg mb-4 text-center">
          <p className="text-lg font-bold">Game Over!</p>
          <p>Winner: {gameState.winner_id}</p>
        </div>
      )}

      {!isGameActive && !gameState.winner_id && (
        <div className="bg-yellow-700 text-white p-4 rounded-lg mb-4 text-center">
          <p>Game not started or paused</p>
        </div>
      )}

      <div className="space-y-4">
        {/* Basic actions */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => sendAction('invest')}
            disabled={!isGameActive}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            Invest
          </button>

          <button
            onClick={() => sendAction('wait')}
            disabled={!isGameActive}
            className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-800 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            Wait
          </button>
        </div>

        {/* Target player selection */}
        <div>
          <label className="block text-gray-300 text-sm font-bold mb-2">
            Target Player
          </label>
          <select
            value={targetPlayer}
            onChange={(e) => setTargetPlayer(e.target.value)}
            disabled={!isGameActive}
            className="shadow bg-gray-700 text-white appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline"
          >
            <option value="">Select player...</option>
            {otherPlayers.map((player) => (
              <option key={player.id} value={player.id}>
                {player.name}
              </option>
            ))}
          </select>
        </div>

        {/* Amount input */}
        <div>
          <label className="block text-gray-300 text-sm font-bold mb-2">
            Amount
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

        {/* Message input */}
        <div>
          <label className="block text-gray-300 text-sm font-bold mb-2">
            Message
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            disabled={!isGameActive}
            className="shadow bg-gray-700 text-white appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline"
            rows={2}
          />
        </div>

        {/* Advanced actions */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => sendAction('persuade')}
            disabled={!isGameActive || !targetPlayer}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            Persuade
          </button>

          <button
            onClick={() => sendAction('use_item')}
            disabled={!isGameActive || !selectedItem}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-2 px-4 rounded transition-colors"
          >
            Use Item
          </button>
        </div>
      </div>
    </div>
  );
};

export default GameControls; 