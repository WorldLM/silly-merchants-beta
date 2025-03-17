'use client';

import { GameState, GameAction } from './api';

export type WebSocketEventType = 'game_state' | 'game_action' | 'game_end' | 'error';

interface WebSocketEvent {
  type: WebSocketEventType;
  data: any;
}

interface WebSocketOptions {
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onGameState?: (gameState: GameState) => void;
  onGameAction?: (action: GameAction) => void;
  onGameEnd?: (result: any) => void;
}

export class WebSocketService {
  private socket: WebSocket | null = null;
  private gameId: string | null = null;
  public options: WebSocketOptions = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isConnecting = false;

  constructor(options: WebSocketOptions = {}) {
    this.options = options;
  }

  // 连接WebSocket
  connect(gameId: string): Promise<void> {
    // 如果已经连接到相同的游戏，直接返回成功
    if (this.isConnected() && this.gameId === gameId) {
      console.log('已连接到相同游戏，不需要重新连接');
      return Promise.resolve();
    }
    
    // 如果正在连接，取消之前的连接
    if (this.isConnecting) {
      console.log('取消正在进行的连接尝试');
      this.disconnect();
    }
    
    // 如果已连接到其他游戏，先断开连接
    if (this.socket && this.gameId !== gameId) {
      console.log('断开与之前游戏的连接');
      this.disconnect();
    }

    // 避免频繁重连
    if (this.reconnectAttempts > 0) {
      const backoffTime = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts - 1), 10000);
      console.log(`应用重连退避策略，等待 ${backoffTime}ms 后重试`);
    }

    this.isConnecting = true;
    this.gameId = gameId;
    // 为用户生成一个默认的玩家ID
    const playerId = "observer";
    // 使用正确的WebSocket URL格式
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8006'}/ws/${gameId}/${playerId}`;
    
    console.log('尝试连接WebSocket:', wsUrl);
    console.log('游戏ID:', gameId);
    console.log('环境变量NEXT_PUBLIC_WS_URL:', process.env.NEXT_PUBLIC_WS_URL);

    return new Promise((resolve, reject) => {
      try {
        // 创建WebSocket对象前检查
        if (typeof WebSocket === 'undefined') {
          const error = new Error('您的浏览器不支持WebSocket');
          console.error(error);
          this.isConnecting = false;
          reject(error);
          return;
        }

        // 添加快速重连逻辑
        const attemptConnection = (attempt = 0) => {
          if (attempt >= 5) { // 增加重试次数
            console.error(`WebSocket连接失败，已尝试 ${attempt} 次`);
            this.isConnecting = false;
            reject(new Error('WebSocket连接失败，已尝试多次'));
            return;
          }
          
          console.log(`尝试WebSocket连接(第${attempt + 1}次)`);
          
          // 确保关闭之前的连接
          if (this.socket) {
            try {
              this.socket.close();
              this.socket = null;
            } catch (e) {
              console.warn('关闭之前的WebSocket连接时出错:', e);
            }
          }
          
          this.socket = new WebSocket(wsUrl);
          console.log('WebSocket对象已创建，等待连接...');

          // 设置更长的超时
          const timeoutId = setTimeout(() => {
            if (this.socket && this.socket.readyState !== WebSocket.OPEN) {
              console.error(`WebSocket连接超时(第${attempt + 1}次)`);
              if (this.socket) {
                const oldSocket = this.socket;
                this.socket = null;
                try {
                  oldSocket.close();
                } catch (error) {
                  console.error('关闭超时WebSocket时出错:', error);
                }
              }
              // 延迟后重试
              const retryDelay = 1000 * Math.pow(1.5, attempt);
              console.log(`将在 ${retryDelay}ms 后重试连接`);
              setTimeout(() => attemptConnection(attempt + 1), retryDelay);
            }
          }, 8000); // 增加超时时间到8秒

          this.socket.onopen = (event) => {
            console.log('WebSocket连接已打开', event);
            clearTimeout(timeoutId);
            this.reconnectAttempts = 0;
            this.isConnecting = false;
            if (this.options.onOpen) this.options.onOpen(event);
            resolve();
          };

          this.socket.onclose = (event) => {
            console.log('WebSocket连接已关闭', event);
            clearTimeout(timeoutId);
            this.isConnecting = false;
            if (this.options.onClose) this.options.onClose(event);
            
            // 如果连接曾经成功打开过，才尝试重新连接
            if (event.wasClean === false && this.gameId) {
              // 尝试重新连接
              if (this.reconnectAttempts < this.maxReconnectAttempts) {
                const retryDelay = 1000 * Math.pow(1.5, this.reconnectAttempts);
                this.reconnectTimeout = setTimeout(() => {
                  this.reconnectAttempts++;
                  console.log(`尝试重新连接(${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                  this.connect(this.gameId!).catch(e => {
                    console.error('重新连接失败:', e);
                  });
                }, retryDelay); // 更智能的退避
              } else {
                console.warn(`已达到最大重连次数(${this.maxReconnectAttempts})，停止重连`);
              }
            }
          };

          this.socket.onerror = (event) => {
            console.error('WebSocket发生错误:', event);
            // 只在界面上显示简化版的错误消息
            if (this.options.onError) {
              this.options.onError({
                ...event,
                toString: () => "WebSocket连接错误，请检查网络"
              } as Event);
            }
            // 错误处理由onclose负责
          };

          this.socket.onmessage = (event) => {
            try {
              console.log('收到WebSocket消息:', event.data);
              const message: WebSocketEvent = JSON.parse(event.data);
              this.handleMessage(message);
            } catch (error) {
              console.error('处理WebSocket消息时出错:', error);
            }
          };
        };

        // 开始第一次尝试
        attemptConnection();
      } catch (error) {
        this.isConnecting = false;
        console.error('创建WebSocket连接时出错:', error);
        reject(error);
      }
    });
  }

  // 断开WebSocket连接
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    this.gameId = null;
    this.reconnectAttempts = 0;
  }

  // 发送消息
  sendMessage(type: string, data: any): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket未连接，无法发送消息');
      return false;
    }

    try {
      const message = JSON.stringify({ type, data });
      console.log('发送WebSocket消息:', message);
      this.socket.send(message);
      return true;
    } catch (error) {
      console.error('发送WebSocket消息时出错:', error);
      return false;
    }
  }

  // 处理接收到的消息
  private handleMessage(event: WebSocketEvent): void {
    switch (event.type) {
      case 'game_state':
        if (this.options.onGameState) {
          this.options.onGameState(event.data as GameState);
        }
        break;
      case 'game_action':
        if (this.options.onGameAction) {
          this.options.onGameAction(event.data as GameAction);
        }
        break;
      case 'game_end':
        if (this.options.onGameEnd) {
          this.options.onGameEnd(event.data);
        }
        break;
      case 'error':
        console.error('WebSocket错误:', event.data);
        break;
      default:
        console.warn('未知的WebSocket消息类型:', event.type);
    }
  }

  // 发送游戏行动
  sendAction(action: Omit<GameAction, 'timestamp'>): boolean {
    return this.sendMessage('game_action', action);
  }

  // 是否已连接
  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

// 创建WebSocket单例
let wsInstance: WebSocketService | null = null;

export function getWebSocketService(options?: WebSocketOptions, forceNew: boolean = false): WebSocketService {
  // 如果需要强制创建新实例，或者实例不存在
  if (forceNew || !wsInstance) {
    // 如果存在旧实例，先断开连接
    if (wsInstance) {
      console.log('正在创建新的WebSocket服务实例，断开旧连接');
      wsInstance.disconnect();
    }
    wsInstance = new WebSocketService(options);
  } else if (options) {
    // 更新选项
    console.log('更新WebSocket服务选项');
    wsInstance.options = { ...wsInstance.options, ...options };
  }

  return wsInstance;
}

// 添加一个重置WebSocket实例的方法
export function resetWebSocketService(): void {
  if (wsInstance) {
    console.log('重置WebSocket服务实例');
    wsInstance.disconnect();
    wsInstance = null;
  }
} 