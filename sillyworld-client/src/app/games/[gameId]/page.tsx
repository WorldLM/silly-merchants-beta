'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import GameBoard from '@/components/GameBoard';
import AIThinkingLog from '@/components/AIThinkingLog';
import { GameState, gameApi } from '@/services/api';
import { WebSocketService } from '@/services/websocket';
import { Suspense } from 'react';

export default function GamePage() {
  const params = useParams();
  const gameId = params?.gameId as string;
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [wsService, setWsService] = useState<WebSocketService | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch game data
  const fetchGameData = async () => {
    setIsLoading(true);
    try {
      const data = await gameApi.getGameState(gameId);
      setGameState(data);
      setError(null);
      console.log('Refreshing game state...');
    } catch (err) {
      setError('Failed to load game data');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Setup WebSocket and game data fetching
  useEffect(() => {
    if (!gameId) return;

    // Fetch initial game data
    fetchGameData();

    // Setup WebSocket connection
    const ws = WebSocketService.getInstance();
    ws.connect(gameId);
    setWsService(ws);

    // Refresh game state periodically
    const refreshInterval = setInterval(() => {
      fetchGameData();
    }, 5000);

    return () => {
      clearInterval(refreshInterval);
      console.log('Game page unmounting, disconnecting WebSocket');
      ws.disconnect();
    };
  }, [gameId]);

  if (isLoading) return <div className="text-center p-8">Loading game data...</div>;
  if (error) return <div className="text-center p-8 text-red-500">{error}</div>;
  if (!gameState) return <div className="text-center p-8">No game data available</div>;

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-xl font-bold mb-4 text-center">
        Silly World Game
        <div className="text-sm font-normal text-gray-400 mt-1">Game ID: {gameId}</div>
      </h1>
      
      <div className="flex flex-col md:flex-row h-[calc(100vh-120px)] gap-4">
        <div className="md:w-1/2 h-auto">
          <Suspense fallback={<div>Loading game board...</div>}>
            <GameBoard gameState={gameState} />
          </Suspense>
        </div>
        
        <div className="md:w-1/2 h-auto">
          <Suspense fallback={<div>Loading AI thinking...</div>}>
            <AIThinkingLog gameId={gameId} />
          </Suspense>
        </div>
      </div>
    </div>
  );
} 