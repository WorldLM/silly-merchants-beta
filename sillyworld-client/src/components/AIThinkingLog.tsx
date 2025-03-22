'use client';

import { FC, useEffect, useState, useRef } from 'react';
import { WebSocketService } from '@/services/websocket';

interface AIThinkingLogProps {
  gameId: string;
}

interface AIThinkingEntry {
  id: string;
  timestamp: Date;
  player_id: string;
  player_name: string;
  thinking_process: string;
  action_type?: string;
}

const AIThinkingLog: FC<AIThinkingLogProps> = ({ gameId }) => {
  const [thinkingLogs, setThinkingLogs] = useState<AIThinkingEntry[]>([]);
  const [expandedLog, setExpandedLog] = useState<string | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const websocketService = WebSocketService.getInstance();
    
    // Subscribe to AI thinking process messages
    const handleGameMessage = (data: any) => {
      if (data.type === 'ai_thinking' && data.thinking_process) {
        const newEntry: AIThinkingEntry = {
          id: `thinking_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date(),
          player_id: data.player_id,
          player_name: data.player_name || `AI Player ${data.player_id.substring(0, 8)}...`,
          thinking_process: data.thinking_process,
          action_type: data.action_type
        };
        
        setThinkingLogs(prev => [...prev, newEntry]);
      }
    };

    // Register WebSocket event listeners
    if (gameId) {
      // Connect to the game with WebSocket service
      websocketService.connect(gameId).then(() => {
        console.log(`Connected to game ${gameId} WebSocket`);
        
        // Add message handler
        websocketService.options.onGameAction = (action) => {
          if (action.thinking_process) {
            handleGameMessage({
              type: 'ai_thinking',
              player_id: action.player_id,
              player_name: `AI Player ${action.player_id.substring(0, 8)}...`,
              thinking_process: action.thinking_process,
              action_type: action.action_type
            });
          }
        };
      }).catch(err => {
        console.error('Failed to connect to WebSocket:', err);
      });
    }

    return () => {
      // Clean up subscriptions
      if (websocketService) {
        websocketService.options.onGameAction = undefined;
        websocketService.disconnect();
      }
    };
  }, [gameId]);

  // Scroll to bottom when new logs are added
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [thinkingLogs]);

  const toggleExpand = (logId: string) => {
    if (expandedLog === logId) {
      setExpandedLog(null);
    } else {
      setExpandedLog(logId);
    }
  };

  // Function to colorize different parts of thinking process
  const colorizeThinking = (text: string) => {
    // Split text into sections
    const sections = text.split(/^(Step \d+:|Analysis:|Decision:|Conclusion:|I'll|Let me|My goal|I should|I will|I need)/gm);
    
    return sections.map((section, index) => {
      if (index === 0 && !section.match(/^(Step \d+:|Analysis:|Decision:|Conclusion:|I'll|Let me|My goal|I should|I will|I need)/)) {
        return <span key={index} className="text-gray-200">{section}</span>;
      }
      
      if (section.match(/^Step \d+:/)) {
        return <span key={index} className="text-blue-400 font-semibold block">{section}</span>;
      } else if (section.match(/^Analysis:/)) {
        return <span key={index} className="text-yellow-300 font-semibold block">{section}</span>;
      } else if (section.match(/^Decision:|^Conclusion:/)) {
        return <span key={index} className="text-green-400 font-semibold block">{section}</span>;
      } else if (section.match(/^(I'll|Let me|My goal|I should|I will|I need)/)) {
        return <span key={index} className="text-purple-300 font-semibold block">{section}</span>;
      } else {
        return <span key={index} className="text-gray-200">{section}</span>;
      }
    });
  };

  return (
    <div className="bg-gray-800 text-white p-4 rounded-lg shadow-md w-full">
      <h2 className="text-xl font-bold mb-3 border-b border-gray-700 pb-2 flex items-center">
        <span className="mr-2">🧠</span>
        <span>AI Thinking Process</span>
      </h2>
      <div 
        ref={logContainerRef} 
        className="overflow-y-auto custom-scrollbar max-h-[calc(100vh-240px)]"
        style={{
          scrollbarWidth: 'thin',
          scrollbarColor: '#4b5563 #1f2937'
        }}
      >
        {thinkingLogs.length === 0 ? (
          <div className="text-gray-400 text-center py-4">No AI thinking records yet</div>
        ) : (
          <div className="space-y-3">
            {thinkingLogs.map((log) => (
              <div 
                key={log.id} 
                className="bg-gray-700 p-3 rounded hover:bg-gray-600 transition-colors border-l-4 border-indigo-500"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="font-medium text-blue-300 flex items-center">
                    <span className="mr-2">👤</span>
                    {log.player_name}
                    {log.action_type && (
                      <span className="ml-2 text-xs bg-blue-600 px-2 py-0.5 rounded-full">
                        {log.action_type}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-gray-400">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </div>
                </div>
                
                <div 
                  className={`thinking-content mt-2 text-sm bg-gray-800 p-3 rounded ${expandedLog === log.id ? '' : 'max-h-32 overflow-hidden'}`}
                  style={{ position: 'relative' }}
                >
                  <div className="whitespace-pre-line leading-relaxed">
                    {colorizeThinking(log.thinking_process)}
                  </div>
                  
                  {expandedLog !== log.id && (
                    <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-gray-800 to-transparent"></div>
                  )}
                </div>
                
                <button 
                  className="text-xs mt-2 bg-gray-600 hover:bg-gray-500 text-white px-3 py-1 rounded-full transition-colors"
                  onClick={() => toggleExpand(log.id)}
                >
                  {expandedLog === log.id ? 'Collapse ↑' : 'Expand ↓'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #1f2937;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #4b5563;
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
};

export default AIThinkingLog; 