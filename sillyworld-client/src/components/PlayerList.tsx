'use client';

import { FC } from 'react';
import { Player } from '@/services/api';

interface PlayerListProps {
  players: Player[];
}

const PlayerList: FC<PlayerListProps> = ({ players }) => {
  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-4 mb-6">
      <h2 className="text-xl font-bold text-white mb-4">玩家列表</h2>
      
      <div className="space-y-3">
        {players.map((player) => (
          <PlayerListItem key={player.id} player={player} />
        ))}
      </div>
    </div>
  );
};

const PlayerListItem: FC<{ player: Player }> = ({ player }) => {
  return (
    <div 
      className={`${
        player.is_active 
          ? 'bg-gradient-to-r from-purple-700 to-indigo-800' 
          : 'bg-gray-700'
      } rounded-lg p-3 transition-all duration-300`}
    >
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-semibold text-white">{player.name}</h3>
        <div className={`
          px-2 py-1 text-xs font-semibold rounded-full 
          ${player.is_active 
            ? 'bg-green-500 text-green-900' 
            : 'bg-gray-500 text-gray-900'}
        `}>
          {player.is_active ? '活跃' : '等待中'}
        </div>
      </div>

      <div className="flex justify-between text-sm mb-2">
        <div className="text-gray-300">余额:</div>
        <div className="text-yellow-300 font-bold">{player.balance}</div>
      </div>

      <div className="mb-2">
        <div className="text-gray-300 text-sm mb-1">道具:</div>
        <div className="flex flex-wrap gap-1">
          {player.items.length > 0 ? (
            player.items.map((item, index) => (
              <div 
                key={index} 
                className={`${
                  item.used 
                    ? 'bg-gray-600 text-gray-300' 
                    : 'bg-blue-600 text-white'
                } text-xs px-2 py-0.5 rounded-full`}
              >
                {item.type}
              </div>
            ))
          ) : (
            <span className="text-gray-500 text-xs">无道具</span>
          )}
        </div>
      </div>

      {player.last_action_time && (
        <div className="flex justify-between text-xs">
          <div className="text-gray-400">上次行动:</div>
          <div className="text-gray-300">
            {new Date(player.last_action_time).toLocaleTimeString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerList; 