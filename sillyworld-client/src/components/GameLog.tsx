'use client';

import { FC, useEffect, useState, useRef } from 'react';
import { WebSocketService } from '@/services/websocket';
import { GameState } from '@/services/api';

interface GameLogProps {
  gameState: GameState;
}

interface LogEntry {
  id: string;
  timestamp: Date;
  type: 'action' | 'state' | 'event' | 'error' | 'ai_thinking' | 'ai_speech';
  message: string;
  details?: any;
  player_id?: string;
  thinking_process?: string;
  public_message?: string;
}

const GameLog: FC<GameLogProps> = ({ gameState }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logContainerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // Initialize logs
    setLogs([
      {
        id: '1',
        timestamp: new Date(),
        type: 'event',
        message: 'Game log initialized'
      }
    ]);
    
    // 连接WebSocket获取游戏日志
    const websocketService = WebSocketService.getInstance();
    
    if (gameState && gameState.game_id) {
      // 连接到游戏WebSocket
      websocketService.connect(gameState.game_id).then(() => {
        console.log(`Connected to game ${gameState.game_id} WebSocket for logs`);
        
        // 添加消息处理器
        websocketService.options.onGameAction = (action) => {
          // 创建新的日志条目
          const newLog: LogEntry = {
            id: Date.now().toString(),
            timestamp: new Date(),
            type: action.action_type === 'ai_thinking' ? 'ai_thinking' : 'action',
            message: action.description || `${action.action_type} action occurred`,
            player_id: action.player_id,
            thinking_process: action.thinking_process,
            public_message: action.public_message
          };
          
          setLogs(prev => [...prev, newLog]);
        };
      }).catch(err => {
        console.error('Failed to connect to WebSocket for logs:', err);
        
        // 添加连接错误日志
        const errorLog: LogEntry = {
          id: Date.now().toString(),
          timestamp: new Date(),
          type: 'error',
          message: `WebSocket连接失败: ${err.message}`
        };
        setLogs(prev => [...prev, errorLog]);
      });
    }
    
    return () => {
      // 清理WebSocket
      if (websocketService) {
        websocketService.options.onGameAction = undefined;
      }
    };
  }, [gameState]);
  
  // Auto-scroll to bottom when logs are added
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);
  
  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-4">
      <h2 className="text-xl font-bold text-white mb-4">Game Log</h2>
      
      <div 
        ref={logContainerRef}
        className="bg-gray-900 rounded-lg p-3 h-64 overflow-y-auto text-sm"
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 text-center py-4">No logs yet</div>
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <LogItem key={log.id} log={log} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const LogItem: FC<{ log: LogEntry }> = ({ log }) => {
  const { type, message, timestamp, thinking_process, public_message, player_id } = log;
  
  let bgColor = 'bg-gray-800';
  let borderColor = 'border-gray-700';
  let iconColor = 'text-gray-400';
  let icon = '🔸';
  
  switch (type) {
    case 'action':
      bgColor = 'bg-blue-900 bg-opacity-30';
      borderColor = 'border-blue-800';
      iconColor = 'text-blue-400';
      icon = '🎮';
      break;
    case 'state':
      bgColor = 'bg-purple-900 bg-opacity-30';
      borderColor = 'border-purple-800';
      iconColor = 'text-purple-400';
      icon = '📊';
      break;
    case 'event':
      bgColor = 'bg-green-900 bg-opacity-30';
      borderColor = 'border-green-800';
      iconColor = 'text-green-400';
      icon = '��';
      break;
    case 'error':
      bgColor = 'bg-red-900 bg-opacity-30';
      borderColor = 'border-red-800';
      iconColor = 'text-red-400';
      icon = '⚠️';
      break;
    case 'ai_thinking':
      bgColor = 'bg-yellow-900 bg-opacity-30';
      borderColor = 'border-yellow-800';
      iconColor = 'text-yellow-400';
      icon = '🧠';
      break;
    case 'ai_speech':
      bgColor = 'bg-green-900 bg-opacity-50';
      borderColor = 'border-green-800';
      iconColor = 'text-green-400';
      icon = '💬';
      break;
  }
  
  return (
    <div className={`${bgColor} border-l-2 ${borderColor} rounded px-3 py-2`}>
      <div className="flex items-start">
        <span className="mr-2 text-lg leading-none">{icon}</span>
        <div className="flex-1">
          <p className="text-white">{message}</p>
          
          {/* Display AI thinking process */}
          {thinking_process && (
            <div className="mt-2 p-2 bg-gray-800 rounded-md">
              <p className="text-sm text-yellow-300 font-mono">AI Thinking Process:</p>
              <p className="text-xs text-gray-300 whitespace-pre-wrap">{thinking_process}</p>
            </div>
          )}
          
          {/* Display AI public message */}
          {public_message && (
            <div className="mt-2 p-2 bg-gray-800 rounded-md">
              <p className="text-sm text-green-300">Public Message:</p>
              <p className="text-sm text-white italic">"{public_message}"</p>
            </div>
          )}
          
          <p className="text-xs text-gray-400 mt-1">
            {timestamp.toLocaleTimeString()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default GameLog; 