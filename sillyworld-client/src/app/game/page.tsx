'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { GameState, GameAction, gameApi } from '@/services/api';
import { WebSocketService, getWebSocketService, resetWebSocketService } from '@/services/websocket';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorMessage from '@/components/ErrorMessage';
import { getGameContract } from '@/services/gameContract';
import Navbar from '@/components/Navbar';
import WalletScriptHandler from '@/components/WalletScriptHandler';

// 辅助函数 - 将游戏阶段翻译为中文
const translatePhase = (phase: string): string => {
  const phaseMap: Record<string, string> = {
    'item_phase': '道具阶段',
    'bid_phase': '竞价阶段',
    'result_phase': '结果阶段',
    'end_phase': '结束阶段'
  };
  return phaseMap[phase] || phase;
};

// 辅助函数 - 将动作类型翻译为中文
const translateAction = (actionType: string): string => {
  const actionMap: Record<string, string> = {
    'select_item': '选择了道具',
    'buy_item': '购买了道具',
    'place_bid': '出价',
    'passed': '跳过了回合',
    'use_item': '使用了道具',
    'balance_change': '资金变动',
    'item_acquired': '获得了道具',
    'item_used': '使用了道具'
  };
  return actionMap[actionType] || actionType;
};

// 辅助函数 - 将道具类型翻译为中文
const translateItemType = (itemType: string): string => {
  const itemMap: Record<string, string> = {
    'aggressive': '攻击牌',
    'shield': '防御牌',
    'intel': '情报牌',
    'equalizer': '均富牌'
  };
  return itemMap[itemType] || itemType;
};

// 辅助函数 - 根据玩家ID获取玩家名称
const getPlayerName = (playerId: string | null): string => {
  if (!playerId) return '未知';
  return playerId;
};

// 辅助函数 - 格式化游戏动作
const formatGameAction = (action: GameAction, gameState: GameState): string => {
  // 如果有描述字段，直接使用
  if (action.description) {
    return action.description;
  }

  const player = gameState.players.find(p => p.id === action.player_id);
  const playerName = player?.name || action.player_id;

  switch (action.action_type) {
    case 'buy_item':
      return `${playerName} 花费 ${action.amount} 代币购买了 ${translateItemType(action.item_type)}`;
    
    case 'use_item':
      const targetPlayer = gameState.players.find(p => p.id === action.target_player);
      const targetName = targetPlayer?.name || action.target_player;
      return `${playerName} 对 ${targetName} 使用了 ${translateItemType(action.item_type)}`;
    
    case 'balance_change':
      return `${playerName} ${action.amount > 0 ? '获得' : '损失'} ${Math.abs(action.amount)} 代币`;
    
    case 'item_acquired':
      return `${playerName} 获得了道具: ${translateItemType(action.item_type)}`;
    
    case 'item_used':
      return `${playerName} 使用了道具: ${translateItemType(action.item_type)}`;
    
    default:
      return `${playerName} ${translateAction(action.action_type)}`;
  }
};

export default function GamePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const gameId = searchParams.get('gameId');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [gameLog, setGameLog] = useState<string[]>([]);
  const [walletPublicKey, setWalletPublicKey] = useState<string | null>(null);

  // 初始化游戏状态和WebSocket连接
  useEffect(() => {
    if (!gameId) {
      setError('游戏ID不存在');
      setLoading(false);
      return;
    }

    // 重置WebSocket服务，确保清除之前的连接状态
    resetWebSocketService();
    
    let isComponentMounted = true; // 用于防止组件卸载后更新状态

    // 设置一个定时器，定期获取游戏状态以防WebSocket连接失败
    const intervalId = setInterval(async () => {
      try {
        if (gameId && isComponentMounted) {
          console.log('定期刷新游戏状态...');
          const state = await gameApi.getGameState(gameId);
          if (isComponentMounted) {
            setGameState(state);
            // 只在WebSocket未连接时才添加日志
            if (!wsConnected) {
              addToLog(`游戏状态已通过API刷新: 回合 ${state.round}, 阶段 ${state.phase}`);
            }
          }
        }
      } catch (err) {
        console.error('刷新游戏状态失败:', err);
      }
    }, 5000); // 每5秒刷新一次

    async function initGame() {
      try {
        // 获取游戏状态
        const state = await gameApi.getGameState(gameId);
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
                  addToLog('已连接到游戏服务器');
                }
              },
              onClose: () => {
                if (isComponentMounted) {
                  setWsConnected(false);
                  addToLog('与游戏服务器的连接已断开，将通过轮询获取游戏状态');
                }
              },
              onError: () => {
                // 简化错误处理，不再设置全局错误
                if (isComponentMounted) {
                  setWsConnected(false);
                  console.warn('WebSocket连接出错，将不会收到实时更新');
                }
              },
              onGameState: (newState) => {
                console.log('收到新的游戏状态', newState);
                if (isComponentMounted) {
                  setGameState(newState);
                  
                  // 记录游戏事件
                  if (gameState) {
                    if (newState.round > gameState.round) {
                      addToLog(`回合 ${newState.round} 开始`);
                    }
                    if (newState.phase !== gameState.phase) {
                      addToLog(`阶段变更: ${translatePhase(newState.phase)}`);
                    }
                  }
                }
              },
              onGameAction: (action) => {
                console.log('收到游戏动作', action);
                // 使用格式化函数生成详细信息
                if (isComponentMounted && gameState) {
                  const formattedAction = formatGameAction(action, gameState);
                  addToLog(formattedAction);
                }
              },
              onGameEnd: (result) => {
                console.log('游戏结束', result);
                if (isComponentMounted) {
                  addToLog(`游戏结束! 胜利者: ${getPlayerName(result.winner_id)}`);
                  
                  // Call the handleGameEnd function
                  handleGameEnd(result.winner_id);
                }
              }
            });
            
            // 连接到游戏
            try {
              await wsService.connect(gameId);
            } catch (err) {
              console.warn('无法连接到WebSocket:', err);
              if (isComponentMounted) {
                addToLog('无法连接到实时服务器，将使用轮询获取游戏状态');
                // 不设置全局错误
              }
            }
          } catch (err) {
            // 即使WebSocket错误也不会影响界面显示
            console.warn('WebSocket设置出错，将不会收到实时更新');
            // 不设置全局错误
          }
        }
      } catch (err) {
        console.error('初始化游戏失败:', err);
        if (isComponentMounted) {
          // Check if the error might be related to the OpenRouter API
          if (err instanceof Error && err.message.includes('choices')) {
            setError('游戏AI系统暂时不可用，请稍后再试。可能是API密钥问题。');
          } else {
            setError('加载游戏失败，请重试。');
          }
          setLoading(false);
        }
      }
    }

    initGame();

    // 清理函数
    return () => {
      console.log('游戏页面卸载，断开WebSocket连接');
      isComponentMounted = false; // 标记组件已卸载
      resetWebSocketService();
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
      const gameId = searchParams.get('gameId');
      const contractGameId = localStorage.getItem('contract_game_id');
      
      if (!gameId || !contractGameId) {
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
      addToLog(`游戏结束！奖励已发放到${isUserWinner ? '你的' : 'AI玩家的'}钱包`);
    } catch (err) {
      console.error('Error ending game on-chain:', err);
      addToLog(`游戏结束处理出错: ${err instanceof Error ? err.message : '未知错误'}`);
    }
  };

  // Add a handler for wallet connection
  const handleWalletConnect = (publicKey: string) => {
    setWalletPublicKey(publicKey);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <LoadingSpinner size="large" text="加载游戏中..." />
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
          返回主页
        </button>
      </div>
    );
  }

  if (!gameState) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <ErrorMessage message="无法加载游戏状态" />
        <button 
          onClick={handleReturnHome}
          className="mt-4 btn-primary"
        >
          返回主页
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-purple-900 text-white">
      <WalletScriptHandler />
      <Navbar onWalletConnect={handleWalletConnect} />
      
      <div className="max-w-7xl mx-auto pt-20 px-4">
        <header className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold">Agent Arena</h1>
            <p className="text-gray-300">游戏ID: {gameState.game_id} {!wsConnected && <span className="text-red-500">(离线)</span>}</p>
          </div>
          <button 
            onClick={handleReturnHome}
            className="btn-ghost"
          >
            返回主页
          </button>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 游戏面板 */}
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">游戏状态</h2>
                <div className="flex items-center">
                  <span className="px-3 py-1 rounded-full bg-indigo-600 text-sm font-medium">
                    回合 {gameState.round}
                  </span>
                  <span className="ml-2 px-3 py-1 rounded-full bg-purple-600 text-sm font-medium">
                    {gameState.status === 'active' ? '进行中' : 
                     gameState.status === 'waiting' ? '等待中' : 
                     gameState.status === 'paused' ? '暂停' : '已结束'}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-700 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-2">奖池</h3>
                  <p className="text-3xl font-bold text-yellow-400">{gameState.prize_pool} 代币</p>
                </div>
                
                <div className="bg-gray-700 p-4 rounded-lg">
                  <h3 className="text-lg font-semibold mb-2">游戏阶段</h3>
                  <p className="text-3xl font-bold text-indigo-400">{gameState.phase}</p>
                </div>
              </div>

              {gameState.status === 'completed' && gameState.winner_id && (
                <div className="bg-gradient-to-r from-yellow-600 to-yellow-400 p-4 rounded-lg mb-4">
                  <h3 className="text-lg font-semibold mb-2">游戏结束!</h3>
                  <p className="text-xl font-bold">
                    获胜者: {gameState.players.find(p => p.id === gameState.winner_id)?.name || '未知玩家'}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {gameState.players.map(player => (
                  <div key={player.id} className={`bg-gray-700 rounded-lg p-4 border-2 ${player.is_active ? 'border-green-500' : 'border-gray-600'}`}>
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-bold">{player.name}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs ${player.is_active ? 'bg-green-600' : 'bg-gray-600'}`}>
                        {player.is_active ? '活跃' : '出局'}
                      </span>
                    </div>
                    <p className="text-lg font-semibold text-yellow-400 mb-2">{player.balance} 代币</p>
                    
                    {player.items.length > 0 && (
                      <div className="mb-2">
                        <p className="text-sm font-medium mb-1">道具:</p>
                        <div className="flex flex-wrap gap-1">
                          {player.items.map((item, idx) => (
                            <span key={idx} className={`px-2 py-1 rounded text-xs ${item.used ? 'bg-gray-600' : 'bg-purple-700'}`}>
                              {translateItemType(item.type)} {item.used && '(已使用)'}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {player.last_action && (
                      <p className="text-xs text-gray-400 mt-2">
                        上次行动: {player.last_action}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 游戏日志 */}
          <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
            <h2 className="text-xl font-bold mb-4">游戏日志</h2>
            <div className="h-[500px] overflow-y-auto bg-gray-900 rounded-lg p-2">
              {gameLog.length === 0 ? (
                <p className="text-gray-500 p-2">暂无游戏记录...</p>
              ) : (
                <div className="space-y-1">
                  {gameLog.map((log, index) => (
                    <div key={index} className="p-2 bg-gray-800 rounded text-sm">
                      {log}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 