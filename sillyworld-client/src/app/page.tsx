'use client';

import { useState, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Player, gameApi } from '@/services/api';
import WalletConnect from '@/components/WalletConnect';
import { getGameContract } from '@/services/gameContract';
import WalletScriptHandler from '@/components/WalletScriptHandler';
import Navbar from '@/components/Navbar';

export default function HomePage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [playerCount, setPlayerCount] = useState(2);
  const [error, setError] = useState<string | null>(null);
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletPublicKey, setWalletPublicKey] = useState<string | null>(null);
  const [playerPrompt, setPlayerPrompt] = useState(getRandomPrompt());
  const [aiPrompts, setAiPrompts] = useState<string[]>([getRandomPrompt()]);
  const [entryFee, setEntryFee] = useState(0.01); // Default entry fee in SOL
  const [showConnectPrompt, setShowConnectPrompt] = useState(false);

  // Handle wallet connection
  const handleWalletConnect = (publicKey: string) => {
    setWalletPublicKey(publicKey);
    setWalletConnected(true);
    setShowConnectPrompt(false);
  };

  // Handle player count change
  const handlePlayerCountChange = (newCount: number) => {
    setPlayerCount(newCount);
    
    // Adjust AI prompts array size (player count - 1 for AI players)
    const aiCount = newCount - 1;
    if (aiCount > aiPrompts.length) {
      // Add more AI prompts
      setAiPrompts([
        ...aiPrompts,
        ...Array(aiCount - aiPrompts.length).fill('').map(() => getRandomPrompt())
      ]);
    } else if (aiCount < aiPrompts.length) {
      // Remove excess AI prompts
      setAiPrompts(aiPrompts.slice(0, aiCount));
    }
  };

  // Generate random prompt for an AI player
  const generateRandomAiPrompt = (index: number) => {
    const newPrompts = [...aiPrompts];
    newPrompts[index] = getRandomPrompt();
    setAiPrompts(newPrompts);
  };

  // Create new game
  const createNewGame = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!walletConnected) {
      setShowConnectPrompt(true);
      setError('请先连接钱包');
      return;
    }
    
    setIsLoading(true);
    setError(null);

    try {
      // Initialize game contract
      const gameContract = getGameContract((window as any).sonicWallet);
      
      // Initialize game on-chain
      const gameId = await gameContract.initializeGame(entryFee);
      
      // Join the game
      await gameContract.joinGame(gameId);
      
      // Create player list (first player is the user, rest are AI)
      const players: Player[] = [
        {
          id: walletPublicKey!, // User's wallet as player ID
          name: `玩家 (${walletPublicKey!.slice(0, 6)}...)`,
          prompt: playerPrompt,
          balance: 100,
          items: [],
          is_active: true
        },
        ...aiPrompts.map((prompt, i) => ({
          id: `ai_player_${i + 1}`,
          name: `AI玩家 ${i + 1}`,
          prompt: prompt,
          balance: 100,
          items: [],
          is_active: true
        }))
      ];

      console.log("Creating game with players:", players);

      // Create game in backend
      const game = await gameApi.createGame(players);
      console.log("Game created:", game);
      
      // Start the game
      const result = await gameApi.startGame(game.game_id);
      console.log("Game started:", result);
      
      // Store game ID and contract game ID for later reference
      localStorage.setItem('current_game_id', game.game_id);
      localStorage.setItem('contract_game_id', gameId);
      
      // Navigate to game page
      router.push(`/game?gameId=${game.game_id}`);
    } catch (err) {
      console.error('创建游戏失败:', err);
      setError(`创建游戏失败: ${err instanceof Error ? err.message : '未知错误'}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-purple-900 flex flex-col">
      <WalletScriptHandler />
      <Navbar onWalletConnect={handleWalletConnect} />
      
      <div className="flex-grow flex items-center justify-center p-4 pt-20">
        <div className="max-w-3xl w-full bg-gray-800 rounded-xl shadow-2xl overflow-hidden p-6">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-white mb-3">Agent Arena</h1>
            <p className="text-gray-300 mb-4">AI代理对抗游戏平台</p>
            {error && <p className="text-red-400 mb-4 text-sm break-words">{error}</p>}
          </div>

          {showConnectPrompt && !walletConnected ? (
            <div className="bg-indigo-900 border border-indigo-700 rounded-lg p-6 mb-6">
              <h3 className="text-xl font-bold text-white mb-3">需要连接钱包</h3>
              <p className="text-gray-300 mb-4">请先连接您的Sonic钱包以创建游戏</p>
              <WalletConnect onConnect={handleWalletConnect} />
            </div>
          ) : null}

          <form onSubmit={createNewGame}>
            {walletConnected && (
              <div className="mb-4">
                <div className="bg-green-700 bg-opacity-30 text-green-300 p-3 rounded-lg mb-6 flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <span>钱包已连接: {walletPublicKey?.slice(0, 6)}...{walletPublicKey?.slice(-4)}</span>
                </div>
              </div>
            )}
            
            <div className="mb-6">
              <label className="block text-gray-300 text-sm font-bold mb-2">
                游戏入场费
              </label>
              <div className="flex items-center">
                <input
                  type="number"
                  value={entryFee}
                  onChange={(e) => setEntryFee(parseFloat(e.target.value))}
                  min="0.001"
                  step="0.001"
                  className="shadow bg-gray-600 text-white appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline"
                />
                <span className="ml-2 text-gray-300">SOL</span>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                入场费将进入奖池，获胜者将获得90%的奖池金额
              </p>
            </div>
            
            <div className="mb-6">
              <label className="block text-gray-300 text-sm font-bold mb-2">
                玩家数量
              </label>
              <select
                value={playerCount}
                onChange={(e) => handlePlayerCountChange(Number(e.target.value))}
                className="shadow bg-gray-600 text-white appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline"
              >
                <option value={2}>2位玩家（1个玩家 vs. 1个AI玩家）</option>
                <option value={3}>3位玩家（1个玩家 vs. 2个AI玩家）</option>
                <option value={4}>4位玩家（1个玩家 vs. 3个AI玩家）</option>
                <option value={5}>5位玩家（1个玩家 vs. 4个AI玩家）</option>
                <option value={6}>6位玩家（1个玩家 vs. 5个AI玩家）</option>
              </select>
            </div>
            
            <div className="mb-6">
              <h3 className="block text-gray-300 text-sm font-bold mb-3">
                你的策略设置
              </h3>
              <div className="bg-gray-700 p-3 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <label className="text-gray-300 text-sm font-medium">
                    你的角色
                  </label>
                  <button
                    type="button"
                    onClick={() => setPlayerPrompt(getRandomPrompt())}
                    className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white py-1 px-2 rounded transition-colors"
                  >
                    随机生成
                  </button>
                </div>
                <textarea
                  value={playerPrompt}
                  onChange={(e) => setPlayerPrompt(e.target.value)}
                  className="w-full h-20 bg-gray-800 border border-gray-600 rounded p-2 text-white text-sm"
                  placeholder="输入你的策略描述..."
                />
              </div>
            </div>
            
            <div className="mb-6">
              <h3 className="block text-gray-300 text-sm font-bold mb-3">
                AI玩家设置
              </h3>
              <div className="space-y-4">
                {aiPrompts.map((prompt, index) => (
                  <div key={index} className="bg-gray-700 p-3 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-gray-300 text-sm font-medium">
                        AI玩家 {index + 1}
                      </label>
                      <button
                        type="button"
                        onClick={() => generateRandomAiPrompt(index)}
                        className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white py-1 px-2 rounded transition-colors"
                      >
                        随机生成
                      </button>
                    </div>
                    <div className="w-full h-20 bg-gray-800 border border-gray-600 rounded p-2 text-white text-sm overflow-auto">
                      {prompt}
                    </div>
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
    </div>
  );
}

// Random prompt generator
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

// Remove the second default export
// export default function Home() {
//   return (
//     <main className="flex min-h-screen flex-col items-center justify-between p-24">
//       <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
//         <h1 className="text-4xl font-bold mb-6">Welcome to SillyWorld</h1>
//         <p className="mb-4">A fun and silly place to explore!</p>
//         <div className="mt-6 flex space-x-4">
//           <Link href="/about" className="text-blue-500 hover:text-blue-700">
//             About
//           </Link>
//           <Link href="/home" className="text-blue-500 hover:text-blue-700">
//             Home Page
//           </Link>
//         </div>
//       </div>
//     </main>
//   )
// } 