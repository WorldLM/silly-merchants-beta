'use client';

import { FC } from 'react';
import { GameState, Player } from '@/services/api';

interface GameBoardProps {
  gameState: GameState;
}

const GameBoard: FC<GameBoardProps> = ({ gameState }) => {
  const { players, round, prize_pool, phase } = gameState;

  return (
    <div className="bg-gradient-to-br from-purple-800 to-indigo-900 rounded-lg shadow-md p-4 mb-4">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-xl font-bold text-white">Agent Arena</h2>
        <div className="bg-purple-700 text-white px-3 py-1 rounded-full text-sm">
          Round {round}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-3">
        {/* Prize Pool Display */}
        <div className="bg-purple-700 bg-opacity-50 rounded-lg p-3 flex items-center">
          <div className="bg-yellow-500 rounded-full p-2 mr-3">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6 text-yellow-900"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-sm text-gray-300">Prize Pool</h3>
            <p className="text-2xl font-bold text-yellow-400">{prize_pool}</p>
          </div>
        </div>

        {/* Current Phase */}
        <div className="bg-purple-700 bg-opacity-50 rounded-lg p-3 flex items-center">
          <div className="bg-blue-500 rounded-full p-2 mr-3">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6 text-blue-900"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-sm text-gray-300">Current Phase</h3>
            <p className="text-lg font-bold text-white">{phase}</p>
          </div>
        </div>
      </div>

      {/* Game Area */}
      <div className="bg-purple-900 bg-opacity-50 rounded-lg p-3">
        <div className="grid grid-cols-2 gap-3">
          {players.map((player) => (
            <PlayerCard key={player.id} player={player} />
          ))}
        </div>
      </div>
    </div>
  );
};

// Player Card Component
const PlayerCard: FC<{ player: Player }> = ({ player }) => {
  return (
    <div className={`bg-gradient-to-br ${player.is_active ? 'from-green-700 to-green-900' : 'from-gray-700 to-gray-900'} rounded-lg shadow p-3 transition-all duration-300`}>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-base font-bold text-white truncate">{player.name}</h3>
        <div className="bg-purple-600 text-white text-xs px-2 py-0.5 rounded">
          AI
        </div>
      </div>
      
      <div className="mb-2">
        <div className="flex items-center">
          <div className="bg-yellow-400 rounded-full p-1 mr-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-3 w-3 text-yellow-800"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="text-yellow-300 font-bold">{player.balance}</div>
        </div>
      </div>
      
      <div className="border-t border-purple-700 pt-2">
        <h4 className="text-gray-300 text-xs mb-1">Items</h4>
        <div className="flex flex-wrap gap-1">
          {player.items.length > 0 ? (
            player.items.map((item, index) => (
              <div 
                key={index} 
                className={`${item.used ? 'bg-gray-600 text-gray-300' : 'bg-blue-600'} text-white text-xs px-1.5 py-0.5 rounded-full relative group`}
                title={getItemDescription(item.type)}
              >
                {getItemName(item.type)}
                <div className="absolute left-0 top-full mt-2 z-10 w-48 bg-gray-800 text-white p-2 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none text-xs">
                  <p className="font-bold">{getItemName(item.type)} ({item.price} tokens)</p>
                  <p className="text-xs mt-1">{getItemDescription(item.type)}</p>
                  {item.used && <p className="text-xs mt-1 text-gray-400">已使用</p>}
                </div>
              </div>
            ))
          ) : (
            <div className="text-gray-400 text-xs">No items</div>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper functions for item names and descriptions
const getItemName = (type: string): string => {
  switch (type) {
    case 'aggressive':
      return 'Aggressive';
    case 'shield':
      return 'Shield';
    case 'intel':
      return 'Intel';
    case 'equalizer':
      return 'Equalizer';
    default:
      return type;
  }
};

const getItemDescription = (type: string): string => {
  switch (type) {
    case 'aggressive':
      return 'Activates attack strategy. If persuasion fails this round, extra tokens will be lost as penalty. No extra reward if successful.';
    case 'shield':
      return 'Activates shield. If successfully persuaded by other players this round, the tokens you need to pay are reduced by half (50%).';
    case 'intel':
      return 'View a portion of the target player\'s Prompt information to guess their strategy tendencies.';
    case 'equalizer':
      return 'Select the player with the most funds as an equalization target. At the beginning of the next round, the total funds of both players will be divided equally.';
    default:
      return 'Unknown item effect';
  }
};

export default GameBoard; 