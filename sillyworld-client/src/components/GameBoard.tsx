'use client';

import { FC } from 'react';
import { GameState, Player } from '@/services/api';
import Image from 'next/image';

interface GameBoardProps {
  gameState: GameState;
}

const GameBoard: FC<GameBoardProps> = ({ gameState }) => {
  const { players, round, prize_pool, phase } = gameState;

  return (
    <div className="bg-gradient-to-br from-purple-800 to-indigo-900 rounded-lg shadow-xl p-6 mb-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white">Agent Arena</h2>
        <div className="bg-purple-700 text-white px-4 py-2 rounded-full">
          回合 {round}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
        {/* 奖池显示 */}
        <div className="bg-purple-700 bg-opacity-50 rounded-lg p-4 flex items-center">
          <div className="bg-yellow-500 rounded-full p-3 mr-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8 text-yellow-900"
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
            <h3 className="text-lg text-gray-300">奖池总额</h3>
            <p className="text-3xl font-bold text-yellow-400">{prize_pool}</p>
          </div>
        </div>

        {/* 当前阶段 */}
        <div className="bg-purple-700 bg-opacity-50 rounded-lg p-4 flex items-center">
          <div className="bg-blue-500 rounded-full p-3 mr-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8 text-blue-900"
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
            <h3 className="text-lg text-gray-300">当前阶段</h3>
            <p className="text-2xl font-bold text-white">{phase}</p>
          </div>
        </div>
      </div>

      {/* 游戏区域 */}
      <div className="bg-purple-900 bg-opacity-50 rounded-lg p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {players.map((player) => (
            <PlayerCard key={player.id} player={player} />
          ))}
        </div>
      </div>
    </div>
  );
};

// 玩家卡片组件
const PlayerCard: FC<{ player: Player }> = ({ player }) => {
  return (
    <div className={`bg-gradient-to-br ${player.is_active ? 'from-green-700 to-green-900' : 'from-gray-700 to-gray-900'} rounded-lg shadow-lg p-4 transition-all duration-300`}>
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-xl font-bold text-white truncate">{player.name}</h3>
        <div className="bg-purple-600 text-white text-sm px-2 py-1 rounded">
          AI
        </div>
      </div>
      
      <div className="mb-4">
        <div className="flex items-center mb-2">
          <div className="bg-yellow-400 rounded-full p-1.5 mr-2">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4 text-yellow-800"
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
      
      <div className="border-t border-purple-700 pt-3">
        <h4 className="text-gray-300 text-sm mb-2">持有道具</h4>
        <div className="flex flex-wrap gap-2">
          {player.items.length > 0 ? (
            player.items.map((item, index) => (
              <div 
                key={index} 
                className={`${item.used ? 'bg-gray-600' : 'bg-blue-600'} text-white text-xs px-2 py-1 rounded-full relative group`}
                title={getItemDescription(item.type)}
              >
                {getItemName(item.type)} ({item.price}代币)
                <div className="absolute left-0 top-full mt-2 z-10 w-64 bg-gray-800 text-white p-2 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                  <p className="font-bold">{getItemName(item.type)} ({item.price}代币)</p>
                  <p className="text-xs mt-1">{getItemDescription(item.type)}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-gray-400 text-xs">无道具</div>
          )}
        </div>
      </div>
    </div>
  );
};

// 添加辅助函数，获取道具名称和描述
const getItemName = (type: string): string => {
  switch (type) {
    case 'aggressive':
      return '激进卡';
    case 'shield':
      return '护盾卡';
    case 'intel':
      return '情报卡';
    case 'equalizer':
      return '均富卡';
    default:
      return type;
  }
};

const getItemDescription = (type: string): string => {
  switch (type) {
    case 'aggressive':
      return '激活攻击策略，若本轮说服失败将额外损失代币作为惩罚，若成功则无额外奖励';
    case 'shield':
      return '激活防护盾，若本轮被其他玩家成功说服，需要支付的代币减半(50%)';
    case 'intel':
      return '查看目标玩家的Prompt信息片段，用于猜测对方的策略倾向';
    case 'equalizer':
      return '选择当前资金最多的玩家作为均富目标，将在下一轮开始时与其平分两人的资金总额';
    default:
      return '未知道具效果';
  }
};

export default GameBoard; 