'use client';

import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import { GameState, GameAction as ApiGameAction, gameApi } from '@/services/api';
import { resetWebSocketService, getWebSocketService } from '@/services/websocket';
import { WebSocketService } from '@/services/websocket';
import { getGameContract } from '@/services/gameContract';
import Navbar from '@/components/Navbar';
import WalletScriptHandler from '@/components/WalletScriptHandler';
import GameControls from '@/components/GameControls';
import GameBoard from '@/components/GameBoard';
import AIThinkingLog from '@/components/AIThinkingLog';
import { Toaster, toast } from 'react-hot-toast';

// 辅助函数 - 将游戏阶段翻译为中文
const translatePhase = (phase: string): string => {
  const phaseMap: Record<string, string> = {
    'item_phase': 'Item Phase',
    'bid_phase': 'Bidding Phase',
    'result_phase': 'Results Phase',
    'end_phase': 'End Phase'
  };
  return phaseMap[phase] || phase;
};

// 辅助函数 - 将动作类型翻译为中文
const translateAction = (actionType: string): string => {
  const actionMap: Record<string, string> = {
    'select_item': 'selected an item',
    'buy_item': 'bought an item',
    'place_bid': 'placed a bid',
    'passed': 'passed the turn',
    'use_item': 'used an item',
    'balance_change': 'balance changed',
    'item_acquired': 'acquired an item',
    'item_used': 'used an item'
  };
  return actionMap[actionType] || actionType;
};

// 辅助函数 - 将道具类型翻译为中文
const translateItemType = (itemType: string): string => {
  if (!itemType) return 'Unknown Item';
  
  const itemMap: Record<string, string> = {
    'aggressive': 'Attack Card',
    'shield': 'Defense Card',
    'intel': 'Intelligence Card',
    'equalizer': 'Equalizer Card'
  };
  return itemMap[itemType] || itemType;
};

// 辅助函数 - 根据玩家ID获取玩家名称
const getPlayerName = (playerId: string | null): string => {
  if (!playerId) return 'Unknown';
  return playerId;
};

// Rename the interface to avoid conflict
interface GameActionWithOptionals {
  action_type: string;
  player_id: string;
  amount?: number;
  item_type?: string;
  target_player?: string;
  description?: string;
}

// Update the formatGameAction function to use the new interface
const formatGameAction = (action: ApiGameAction, gameState: GameState): string => {
  if (action.description) {
    return action.description;
  }

  const player = gameState.players.find(p => p.id === action.player_id);
  const playerName = player?.name || action.player_id;

  switch (action.action_type) {
    case 'buy_item':
      return `${playerName} spent ${action.amount || 0} tokens to buy ${translateItemType(action.item_type || '')}`;
    
    case 'balance_change':
      // Add null check for amount
      const amount = action.amount || 0;
      return `${playerName} ${amount > 0 ? 'gained' : 'lost'} ${Math.abs(amount)} tokens`;
    
    case 'use_item':
      const targetPlayer = gameState.players.find(p => p.id === action.target_player);
      const targetName = targetPlayer?.name || action.target_player;
      return `${playerName} used ${translateItemType(action.item_type || '')} on ${targetName}`;
    
    case 'item_acquired':
      return `${playerName} acquired an item: ${translateItemType(action.item_type || '')}`;
    
    case 'item_used':
      return `${playerName} used an item: ${translateItemType(action.item_type || '')}`;
    
    default:
      return `${playerName} ${translateAction(action.action_type)}`;
  }
};

// Main component that uses useSearchParams
function GamePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const gameId = searchParams?.get('gameId') || null;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [gameLog, setGameLog] = useState<string[]>([]);
  const [walletPublicKey, setWalletPublicKey] = useState<string | null>(null);
  const [userPlayerRole, setUserPlayerRole] = useState<string | null>(null);
  const [isUserActiveTurn, setIsUserActiveTurn] = useState(false);

  // 获取游戏数据
  const fetchGameData = useCallback(async () => {
    if (!gameId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const state = await gameApi.getGameState(gameId);
      setGameState(state);
      
      // 确定用户的角色
      if (walletPublicKey) {
        const userPlayer = state.players.find(p => p.id === walletPublicKey);
        if (userPlayer) {
          setUserPlayerRole(userPlayer.id);
        }
      }
      
      setLoading(false);
    } catch (err: any) {
      console.error('Failed to fetch game data:', err);
      setError(err.message || 'Failed to load game data');
      setLoading(false);
    }
  }, [gameId, walletPublicKey]);

  // 处理游戏动作的函数
  const handleAction = useCallback(async (actionType: string, actionData?: any) => {
    if (!gameId || !gameState) return;
    
    try {
      console.log(`执行动作: ${actionType}`, actionData);
      
      // 根据不同的动作类型调用不同的API
      switch (actionType) {
        case 'buy_item':
          if (actionData?.itemType) {
            await gameApi.buyItem(gameId, actionData.itemType);
          }
          break;
          
        case 'use_item':
          if (actionData?.itemId && actionData?.targetPlayerId) {
            await gameApi.useItem(gameId, actionData.itemId, actionData.targetPlayerId);
          }
          break;
          
        case 'negotiate':
          if (actionData?.targetPlayerId && actionData?.amount) {
            await gameApi.negotiate(gameId, actionData.targetPlayerId, actionData.amount, actionData.message || '');
          }
          break;
          
        case 'respond_negotiation':
          if (actionData?.negotiationId && actionData?.accepted !== undefined) {
            await gameApi.respondNegotiation(gameId, actionData.negotiationId, actionData.accepted);
          }
          break;
          
        default:
          console.warn(`未实现的动作类型: ${actionType}`);
      }
      
      // 刷新游戏状态
      const updatedState = await gameApi.getGameState(gameId);
      setGameState(updatedState);
      
    } catch (err) {
      console.error(`执行动作失败: ${actionType}`, err);
      // 可以在这里添加错误处理，比如显示错误消息
    }
  }, [gameId, gameState]);

  // 初始化游戏状态和WebSocket连接
  useEffect(() => {
    if (!gameId) {
      setError('Game ID does not exist');
      setLoading(false);
      return;
    }

    // 重置WebSocket服务，确保清除之前的连接状态
    if (typeof resetWebSocketService === 'function') {
      resetWebSocketService();
    } else {
      console.warn('resetWebSocketService is not available');
      // 尝试通过getInstance获取实例并断开
      try {
        const wsInstance = WebSocketService.getInstance();
        if (wsInstance) {
          wsInstance.disconnect();
        }
      } catch (e) {
        console.error('Failed to reset WebSocket service:', e);
      }
    }
    
    let isComponentMounted = true; // 用于防止组件卸载后更新状态

    // 设置一个定时器，定期获取游戏状态以防WebSocket连接失败
    const intervalId = setInterval(async () => {
      try {
        if (gameId && isComponentMounted) {
          console.log('Refreshing game state...');
          const state = await gameApi.getGameState(gameId as string);
          if (isComponentMounted) {
            setGameState(state);
            // 只在WebSocket未连接时才添加日志
            if (!wsConnected) {
              addToLog(`Game state refreshed via API: Round ${state.round}, Phase ${state.phase}`);
            }
          }
        }
      } catch (err) {
        console.error('Failed to refresh game state:', err);
      }
    }, 5000); // 每5秒刷新一次

    async function initGame() {
      try {
        // 获取游戏状态
        const state = await gameApi.getGameState(gameId as string);
        if (isComponentMounted) {
          setGameState(state);
          setLoading(false); // 加载完成，可以显示界面了
        }
        
        // 连接WebSocket - 即使失败也不影响基本功能
        if (isComponentMounted) {
          try {
            const wsService = getWebSocketService({
              onOpen: () => {
                if (isComponentMounted) {
                  setWsConnected(true);
                  addToLog('Connected to game server');
                }
              },
              onClose: () => {
                if (isComponentMounted) {
                  setWsConnected(false);
                  addToLog('Connection to game server lost, will poll for game state updates');
                }
              },
              onError: () => {
                // 简化错误处理，不再设置全局错误
                if (isComponentMounted) {
                  setWsConnected(false);
                  console.warn('WebSocket connection error, real-time updates unavailable');
                }
              },
              onGameState: (newState) => {
                console.log('Received new game state', newState);
                if (isComponentMounted) {
                  setGameState(newState);
                  
                  // 记录游戏事件
                  if (gameState) {
                    if (newState.round > gameState.round) {
                      addToLog(`Round ${newState.round} started`);
                    }
                    if (newState.phase !== gameState.phase) {
                      addToLog(`Phase changed: ${translatePhase(newState.phase)}`);
                    }
                  }
                }
              },
              onGameAction: (action) => {
                console.log('Received game action', action);
                // 使用格式化函数生成详细信息
                if (isComponentMounted && gameState) {
                  const formattedAction = formatGameAction(action, gameState);
                  addToLog(formattedAction);
                }
              },
              onGameEnd: (result) => {
                console.log('Game ended', result);
                if (isComponentMounted) {
                  addToLog(`Game over! Winner: ${getPlayerName(result.winner_id)}`);
                  
                  // Call the handleGameEnd function
                  handleGameEnd(result.winner_id);
                }
              }
            });
            
            // 连接到游戏
            try {
              await wsService.connect(gameId as string);
            } catch (err) {
              console.warn('Unable to connect to WebSocket:', err);
              if (isComponentMounted) {
                addToLog('Unable to connect to real-time server, will use polling for game state updates');
                // 不设置全局错误
              }
            }
          } catch (err) {
            // 即使WebSocket错误也不会影响界面显示
            console.warn('WebSocket setup error, real-time updates unavailable');
            // 不设置全局错误
          }
        }
      } catch (err) {
        console.error('Failed to initialize game:', err);
        if (isComponentMounted) {
          // Check if the error might be related to the OpenRouter API
          if (err instanceof Error && err.message.includes('choices')) {
            setError('Game AI system temporarily unavailable. Please try again later. This might be an API key issue.');
          } else {
            setError('Failed to load game. Please try again.');
          }
          setLoading(false);
        }
      }
    }

    initGame();

    // 清理函数
    return () => {
      console.log('Game page unmounting, disconnecting WebSocket');
      isComponentMounted = false; // 标记组件已卸载
      
      // 直接使用WebSocketService实例断开连接
      const wsService = WebSocketService.getInstance();
      if (wsService) {
        wsService.disconnect();
      }
      
      clearInterval(intervalId); // 清理定时器
    };
  }, [gameId]);

  // 添加日志
  const addToLog = (message: string) => {
    setGameLog(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`]);
  };

  // 返回主页
  const handleReturnHome = () => {
    router.push('/');
  };

  const handleGameEnd = async (winnerId: string) => {
    try {
      // Get game IDs from localStorage
      const currentGameId = searchParams?.get('gameId');
      const contractGameId = localStorage.getItem('contract_game_id');
      
      if (!currentGameId || !contractGameId) {
        console.error('Game ID or contract game ID not found');
        return;
      }
      
      // Check if the winner is the user (player 1)
      const isUserWinner = gameState?.players[0]?.id === winnerId;
      
      // Get winner's public key
      const winnerPublicKey = isUserWinner 
        ? walletPublicKey 
        : '25jUhpQfPWWJ9e4BaP6eNyH3y1YrhF9CDY5DHPhTBiFW'; // Default to a system wallet for AI winners
      
      if (!winnerPublicKey) {
        console.error('Winner public key not found');
        return;
      }
      
      // End the game on-chain
      const gameContract = getGameContract((window as any).sonicWallet);
      const tx = await gameContract.endGame(contractGameId, winnerPublicKey);
      
      console.log('Game ended on-chain:', tx);
      
      // Show success message
      addToLog(`Game over! Rewards have been sent to ${isUserWinner ? 'your' : 'the AI player\'s'} wallet`);
    } catch (err) {
      console.error('Error ending game on-chain:', err);
      addToLog(`Error processing game end: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // Add a handler for wallet connection
  const handleWalletConnect = (publicKey: string) => {
    setWalletPublicKey(publicKey);
  };

  // Return the JSX
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <LoadingSpinner size="large" text="Loading game..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <ErrorMessage message={error} />
        <button 
          onClick={handleReturnHome}
          className="mt-4 btn-primary"
        >
          Return to Home
        </button>
      </div>
    );
  }

  if (!gameState) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <ErrorMessage message="Unable to load game state" />
        <button 
          onClick={handleReturnHome}
          className="mt-4 btn-primary"
        >
          Return to Home
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen w-full p-4 bg-gray-900 text-white">
      <header className="mb-6 text-center">
        <h1 className="text-3xl font-bold">Silly World Game</h1>
        <div className="text-sm text-gray-400">
          Game ID: {gameId}
        </div>
      </header>

      {error ? (
        <ErrorMessage 
          title="Error Loading Game" 
          message={error} 
          onRetry={fetchGameData} 
        />
      ) : loading ? (
        <div className="flex-1 flex items-center justify-center">
          <LoadingSpinner size="large" text="Loading game..." />
        </div>
      ) : (
        <div className="flex-1 flex flex-col gap-4">
          <div className="w-full">
            <GameBoard 
              gameState={gameState!} 
            />
          </div>
          
          <div className="w-full">
            <AIThinkingLog gameId={gameId || ""} />
          </div>
        </div>
      )}

      <Toaster position="top-center" />
    </div>
  );
}

// Wrapper component with Suspense
export default function GamePage() {
  return (
    <Suspense fallback={<LoadingSpinner size="large" text="Loading game..." />}>
      <GamePageContent />
    </Suspense>
  );
} 