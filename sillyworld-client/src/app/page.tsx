'use client';

import { useState, FormEvent, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Player, gameApi } from '@/services/api';
import WalletConnect from '@/components/WalletConnect';
import { getGameContract } from '@/services/gameContract';
import WalletScriptHandler from '@/components/WalletScriptHandler';
import Navbar from '@/components/Navbar';

// Random prompt generator
function getRandomPrompt(): string {
  const prompts = [
    "You are a cautious and conservative AI player who always prioritizes your own safety and long-term interests. You don't easily trust others and avoid taking big risks.",
    "You are a bold and aggressive AI player who enjoys taking risks and pursuing high-risk, high-reward strategies. You believe offense is the best defense.",
    "You are a cooperative AI player who likes to build alliances and relationships of mutual trust with other players. You believe win-win strategies are more effective than zero-sum games.",
    "You are an opportunistic AI player who is always looking for chances to exploit others' weaknesses. You prefer unexpected tactics that catch opponents off guard.",
    "You are a balanced AI player who focuses on both short-term gains and long-term strategy. You excel at adapting your approach based on the current situation.",
    "You are a vengeful AI player who holds grudges and doesn't easily forgive betrayal. Once attacked, you will look for opportunities to retaliate."
  ];
  
  return prompts[Math.floor(Math.random() * prompts.length)];
}

export default function HomePage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [playerCount, setPlayerCount] = useState(2);
  const [error, setError] = useState<string | null>(null);
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletPublicKey, setWalletPublicKey] = useState<string | null>(null);
  const [playerPrompt, setPlayerPrompt] = useState("");
  const [aiPrompts, setAiPrompts] = useState<string[]>([""]);
  const [entryFee, setEntryFee] = useState(0.01); // Default entry fee in ETH
  const [showConnectPrompt, setShowConnectPrompt] = useState(false);
  const [isClient, setIsClient] = useState(false);

  // 使用useEffect在客户端挂载后才生成随机提示，避免服务器/客户端不一致
  useEffect(() => {
    setIsClient(true);
    setPlayerPrompt(getRandomPrompt());
    setAiPrompts([getRandomPrompt()]);
  }, []);

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
      setError('Please connect your wallet first');
      return;
    }
    
    setIsLoading(true);
    setError(null);

    try {
      // Initialize game contract
      const gameContract = getGameContract((window as any).ethereum);
      
      // Initialize game on-chain
      const gameId = await gameContract.initializeGame(entryFee);
      
      // Join the game
      await gameContract.joinGame(gameId);
      
      // Create player list (first player is the user, rest are AI)
      const players: Player[] = [
        {
          id: walletPublicKey!, // User's wallet as player ID
          name: `Player (${walletPublicKey!.slice(0, 6)}...)`,
          prompt: playerPrompt,
          balance: 100,
          items: [],
          is_active: true
        },
        ...aiPrompts.map((prompt, i) => ({
          id: `ai_player_${i + 1}`,
          name: `AI Player ${i + 1}`,
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
      console.error('Failed to create game:', err);
      setError(`Failed to create game: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  // 在客户端渲染前返回占位内容，避免水合错误
  if (!isClient) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-purple-900 flex flex-col">
        <div className="flex-grow flex items-center justify-center p-4 pt-20">
          <div className="max-w-3xl w-full bg-gray-800 rounded-xl shadow-2xl overflow-hidden p-6">
            <div className="text-center mb-6">
              <h1 className="text-3xl font-bold text-white mb-3">Agent Arena</h1>
              <p className="text-gray-300 mb-4">AI Agent Competition Game Platform</p>
            </div>
            <div className="text-center text-gray-300">
              <p>Loading...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-purple-900 flex flex-col">
      <WalletScriptHandler />
      <Navbar onWalletConnect={handleWalletConnect} />
      
      <div className="flex-grow flex items-center justify-center p-4 pt-20">
        <div className="max-w-3xl w-full bg-gray-800 rounded-xl shadow-2xl overflow-hidden p-6">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-white mb-3">Agent Arena</h1>
            <p className="text-gray-300 mb-4">AI Agent Competition Game Platform</p>
            {error && <p className="text-red-400 mb-4 text-sm break-words">{error}</p>}
          </div>

          {showConnectPrompt && !walletConnected ? (
            <div className="bg-indigo-900 border border-indigo-700 rounded-lg p-6 mb-6">
              <h3 className="text-xl font-bold text-white mb-3">Wallet Connection Required</h3>
              <p className="text-gray-300 mb-4">Please connect your MetaMask wallet to create a game</p>
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
                  <span>Wallet Connected: {walletPublicKey?.slice(0, 6)}...{walletPublicKey?.slice(-4)}</span>
                </div>
              </div>
            )}
            
            <div className="mb-6">
              <label className="block text-gray-300 text-sm font-bold mb-2">
                Game Entry Fee
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
                <span className="ml-2 text-gray-300">ETH</span>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Entry fee goes into the prize pool, the winner will receive 90% of the pool
              </p>
            </div>
            
            <div className="mb-6">
              <label className="block text-gray-300 text-sm font-bold mb-2">
                Number of Players
              </label>
              <select
                value={playerCount}
                onChange={(e) => handlePlayerCountChange(Number(e.target.value))}
                className="shadow bg-gray-600 text-white appearance-none border rounded w-full py-2 px-3 leading-tight focus:outline-none focus:shadow-outline"
              >
                <option value={2}>2 Players (1 Player vs. 1 AI Player)</option>
                <option value={3}>3 Players (1 Player vs. 2 AI Players)</option>
                <option value={4}>4 Players (1 Player vs. 3 AI Players)</option>
                <option value={5}>5 Players (1 Player vs. 4 AI Players)</option>
                <option value={6}>6 Players (1 Player vs. 5 AI Players)</option>
              </select>
            </div>
            
            <div className="mb-6">
              <h3 className="block text-gray-300 text-sm font-bold mb-3">
                Your Strategy Settings
              </h3>
              <div className="bg-gray-700 p-3 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                  <label className="text-gray-300 text-sm font-medium">
                    Your Character
                  </label>
                  <button
                    type="button"
                    onClick={() => setPlayerPrompt(getRandomPrompt())}
                    className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white py-1 px-2 rounded transition-colors"
                  >
                    Generate Random
                  </button>
                </div>
                <textarea
                  value={playerPrompt}
                  onChange={(e) => setPlayerPrompt(e.target.value)}
                  className="w-full h-20 bg-gray-800 border border-gray-600 rounded p-2 text-white text-sm"
                  placeholder="Enter your strategy description..."
                />
              </div>
            </div>
            
            <div className="mb-6">
              <h3 className="block text-gray-300 text-sm font-bold mb-3">
                AI Player Settings
              </h3>
              <div className="space-y-4">
                {aiPrompts.map((prompt, index) => (
                  <div key={index} className="bg-gray-700 p-3 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-gray-300 text-sm font-medium">
                        AI Player {index + 1}
                      </label>
                      <button
                        type="button"
                        onClick={() => generateRandomAiPrompt(index)}
                        className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white py-1 px-2 rounded transition-colors"
                      >
                        Generate Random
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
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating Game...
                </span>
              ) : "Create New Game"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
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