'use client';

import { FC, useEffect, useState, useRef } from 'react';
import { WebSocketService } from '@/services/websocket';

interface GameLogProps {
  gameId: string;
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

const GameLog: FC<GameLogProps> = ({ gameId }) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logContainerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // 初始化日志
    setLogs([
      {
        id: '1',
        timestamp: new Date(),
        type: 'event',
        message: '游戏日志初始化'
      }
    ]);
    
    // 这里可以连接WebSocket或API获取游戏日志
    // 模拟接收游戏事件
    const interval = setInterval(() => {
      const eventTypes = ['action', 'state', 'event'];
      const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)] as 'action' | 'state' | 'event';
      
      const newLog: LogEntry = {
        id: Date.now().toString(),
        timestamp: new Date(),
        type: eventType,
        message: getRandomMessage(eventType)
      };
      
      setLogs(prev => [...prev, newLog]);
    }, 15000); // 每15秒添加一个模拟事件
    
    return () => clearInterval(interval);
  }, [gameId]);
  
  // 日志添加时自动滚动到底部
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);
  
  return (
    <div className="bg-gray-800 rounded-lg shadow-lg p-4">
      <h2 className="text-xl font-bold text-white mb-4">游戏日志</h2>
      
      <div 
        ref={logContainerRef}
        className="bg-gray-900 rounded-lg p-3 h-64 overflow-y-auto text-sm"
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 text-center py-4">暂无日志</div>
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
      icon = '🔔';
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
          
          {/* 显示AI思考过程 */}
          {thinking_process && (
            <div className="mt-2 p-2 bg-gray-800 rounded-md">
              <p className="text-sm text-yellow-300 font-mono">AI思考过程:</p>
              <p className="text-xs text-gray-300 whitespace-pre-wrap">{thinking_process}</p>
            </div>
          )}
          
          {/* 显示AI公开发言 */}
          {public_message && (
            <div className="mt-2 p-2 bg-gray-800 rounded-md">
              <p className="text-sm text-green-300">公开发言:</p>
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

// 模拟消息生成
function getRandomMessage(type: string): string {
  const actionMessages = [
    '玩家1执行了投资操作',
    '玩家2尝试说服玩家3',
    '玩家3使用了道具',
    '玩家4等待了一回合'
  ];
  
  const stateMessages = [
    '游戏进入新回合',
    '玩家2的余额增加',
    '奖池金额更新',
    '玩家3获得了新道具'
  ];
  
  const eventMessages = [
    '新玩家加入游戏',
    '游戏暂停',
    '系统公告: 特殊事件将在下回合触发',
    '玩家1发送了全局消息'
  ];
  
  switch (type) {
    case 'action':
      return actionMessages[Math.floor(Math.random() * actionMessages.length)];
    case 'state':
      return stateMessages[Math.floor(Math.random() * stateMessages.length)];
    case 'event':
      return eventMessages[Math.floor(Math.random() * eventMessages.length)];
    default:
      return '未知事件';
  }
}

export default GameLog; 