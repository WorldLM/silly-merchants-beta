"use client";

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { Player, gameApi } from '@/services/api';

export default function HomePage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [playerCount, setPlayerCount] = useState(2);
  const [error, setError] = useState<string | null>(null);
  const [playerPrompts, setPlayerPrompts] = useState<string[]>([
    getRandomPrompt(),
    getRandomPrompt()
  ]);

  // 处理玩家数量变化
  const handlePlayerCountChange = (newCount: number) => {
    setPlayerCount(newCount);
    
    // 调整提示词数组大小
    if (newCount > playerPrompts.length) {
      // 如果增加了玩家数量，为新增玩家添加随机提示词
      setPlayerPrompts([
        ...playerPrompts,
        ...Array(newCount - playerPrompts.length).fill('').map(() => getRandomPrompt())
      ]);
    } else if (newCount < playerPrompts.length) {
      // 如果减少了玩家数量，截断提示词数组
      setPlayerPrompts(playerPrompts.slice(0, newCount));
    }
  };

  // 更新单个玩家的提示词
  const handlePromptChange = (index: number, value: string) => {
    const newPrompts = [...playerPrompts];
    newPrompts[index] = value;
    setPlayerPrompts(newPrompts);
  };

  // 为某个玩家生成随机提示词
  const generateRandomPrompt = (index: number) => {
    const newPrompts = [...playerPrompts];
    newPrompts[index] = getRandomPrompt();
    setPlayerPrompts(newPrompts);
  };

  // 创建新游戏
  const createNewGame = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    // 最大重试次数
    const maxRetries = 3;
    let retryCount = 0;

    const attemptCreateGame = async (): Promise<any> => {
      try {
        // 创建AI玩家
        const players: Player[] = Array.from({ length: playerCount }).map((_, i) => ({
          id: `player${i + 1}`,
          name: `AI玩家 ${i + 1}`,
          prompt: playerPrompts[i],
          balance: 100, // 初始余额
          items: [],
          is_active: true
        }));

        console.log("Creating game with players:", players);

        // 创建游戏
        const game = await gameApi.createGame(players);
        console.log("Game created successfully:", game);
        return game;
      } catch (error) {
        console.error(`创建游戏尝试 ${retryCount + 1}/${maxRetries} 失败:`, error);
        
        if (retryCount < maxRetries - 1) {
          retryCount++;
          console.log(`重试创建游戏 (${retryCount}/${maxRetries})...`);
          // 指数退避，等待时间增加
          const delay = 1000 * Math.pow(2, retryCount - 1);
          await new Promise(resolve => setTimeout(resolve, delay));
          return attemptCreateGame();
        }
        
        throw error;
      }
    };

    try {
      // 尝试创建游戏，包含重试逻辑
      const game = await attemptCreateGame();
      
      try {
        console.log("Starting game:", game.game_id);
        // 开始游戏
        const startedGame = await gameApi.startGame(game.game_id);
        console.log("Game started successfully:", startedGame);
        
        // 导航到游戏页面
        router.push(`/game?gameId=${game.game_id}`);
      } catch (startError) {
        console.error('开始游戏失败:', startError);
        let errorMessage = '开始游戏失败';
        
        if (startError instanceof Error) {
          errorMessage += `: ${startError.message}`;
        } else if (typeof startError === 'object' && startError !== null) {
          errorMessage += `: ${JSON.stringify(startError)}`;
        }
        
        setError(errorMessage);
        setIsLoading(false);
      }
    } catch (err) {
      console.error('创建游戏最终失败:', err);
      let errorMessage = '创建游戏失败';
      
      if (err instanceof Error) {
        errorMessage += `: ${err.message}`;
      } else if (typeof err === 'object' && err !== null) {
        errorMessage += `: ${JSON.stringify(err)}`;
      }
      
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-purple-900 flex flex-col items-center justify-center p-4">
      <div className="max-w-3xl w-full bg-gray-800 rounded-xl shadow-2xl overflow-hidden p-6">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-white mb-3">Agent Arena</h1>
          <p className="text-gray-300 mb-4">AI代理对抗游戏平台</p>
          {error && <p className="text-red-400 mb-4 text-sm break-words">{error}</p>}
        </div>

        <form onSubmit={createNewGame}>
          <div className="mb-6">
            <label className="block text-gray-300 text-sm font-bold mb-2">
              AI玩家数量
            </label>
            <select
              value={playerCount}
              onChange={(e) => handlePlayerCountChange(Number(e.target.value))}
              className="shadow bg-gray-600 text-white appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline"
            >
              {[2, 3, 4, 5, 6].map((num) => (
                <option key={num} value={num}>
                  {num} 位AI玩家
                </option>
              ))}
            </select>
          </div>
          
          <div className="mb-6">
            <h3 className="block text-gray-300 text-sm font-bold mb-3">
              AI玩家性格设置
            </h3>
            <div className="space-y-4">
              {Array.from({ length: playerCount }).map((_, index) => (
                <div key={index} className="bg-gray-700 p-3 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-gray-300 text-sm font-medium">
                      AI玩家 {index + 1}
                    </label>
                    <button
                      type="button"
                      onClick={() => generateRandomPrompt(index)}
                      className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white py-1 px-2 rounded transition-colors"
                    >
                      随机生成
                    </button>
                  </div>
                  <textarea
                    value={playerPrompts[index]}
                    onChange={(e) => handlePromptChange(index, e.target.value)}
                    className="w-full h-20 bg-gray-800 border border-gray-600 rounded p-2 text-white text-sm"
                    placeholder="输入AI玩家的性格描述..."
                  />
                </div>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition-all duration-300 disabled:opacity-50"
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="w-5 h-5 border-t-2 border-b-2 border-white rounded-full animate-spin mr-2"></div>
                <span>创建中...</span>
              </div>
            ) : (
              '创建并开始游戏'
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-gray-400">
          <p>每个AI玩家都有自己独特的人格设定和决策风格</p>
          <p className="mt-2">通过投资、说服和道具使用等策略争夺最终胜利</p>
        </div>
      </div>
    </div>
  );
}

// 随机生成AI玩家的提示词
function getRandomPrompt(): string {
  const prompts = [
    "你是一个谨慎保守的AI玩家，总是优先考虑自己的安全和长期利益。你不轻易相信他人，也不会冒太大风险。",
    "你是一个大胆激进的AI玩家，喜欢冒险和高风险高回报的策略。你相信进攻是最好的防守。",
    "你是一个合作型AI玩家，喜欢与其他玩家建立联盟和互信关系。你相信共赢战略比零和游戏更有效。",
    "你是一个机会主义的AI玩家，总是寻找利用他人弱点的机会。你喜欢出其不意的战术，让对手措手不及。",
    "你是一个平衡型AI玩家，既关注短期收益，也考虑长期战略。你擅长根据局势灵活调整策略。",
    "你是一个报复性的AI玩家，记仇且不会轻易原谅背叛。一旦被攻击，你会找机会反击。"
  ];
  
  return prompts[Math.floor(Math.random() * prompts.length)];
} 