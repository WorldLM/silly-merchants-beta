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
  
  // Instance cache
  private static instance: WebSocketService | null = null;

  constructor(options: WebSocketOptions = {}) {
    this.options = options;
  }
  
  // Static method to get WebSocketService instance
  public static getInstance(): WebSocketService {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  // Connect to WebSocket
  connect(gameId: string): Promise<void> {
    // If already connected to the same game, return success directly
    if (this.isConnected() && this.gameId === gameId) {
      console.log('Already connected to the same game, no need to reconnect');
      return Promise.resolve();
    }
    
    // If connecting, cancel the previous connection
    if (this.isConnecting) {
      console.log('Canceling ongoing connection attempt');
      this.disconnect();
    }
    
    // If connected to another game, disconnect first
    if (this.socket && this.gameId !== gameId) {
      console.log('Disconnecting from previous game');
      this.disconnect();
    }

    // Avoid frequent reconnections
    if (this.reconnectAttempts > 0) {
      const backoffTime = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts - 1), 10000);
      console.log(`Applying reconnection backoff, waiting ${backoffTime}ms before retry`);
    }

    this.isConnecting = true;
    this.gameId = gameId;
    // Generate a default player ID for the user
    const playerId = "observer";
    // Use the correct WebSocket URL format
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8008'}/ws/${gameId}/${playerId}`;
    
    console.log('Attempting to connect WebSocket:', wsUrl);
    console.log('Game ID:', gameId);
    console.log('Environment variable NEXT_PUBLIC_WS_URL:', process.env.NEXT_PUBLIC_WS_URL);

    return new Promise((resolve, reject) => {
      try {
        // Check before creating WebSocket object
        if (typeof WebSocket === 'undefined') {
          const error = new Error('Your browser does not support WebSocket');
          console.error(error);
          this.isConnecting = false;
          reject(error);
          return;
        }

        // Add quick reconnect logic
        const attemptConnection = (attempt = 0) => {
          if (attempt >= 5) { // Increase retry count
            console.error(`WebSocket connection failed after ${attempt} attempts`);
            this.isConnecting = false;
            reject(new Error('WebSocket connection failed after multiple attempts'));
            return;
          }
          
          console.log(`Attempting WebSocket connection (attempt ${attempt + 1})`);
          
          // Ensure closing previous connection
          if (this.socket) {
            try {
              this.socket.close();
              this.socket = null;
            } catch (e) {
              console.warn('Error closing previous WebSocket connection:', e);
            }
          }
          
          this.socket = new WebSocket(wsUrl);
          console.log('WebSocket object created, waiting for connection...');

          // Set longer timeout
          const timeoutId = setTimeout(() => {
            if (this.socket && this.socket.readyState !== WebSocket.OPEN) {
              console.error(`WebSocket connection timeout (attempt ${attempt + 1})`);
              if (this.socket) {
                const oldSocket = this.socket;
                this.socket = null;
                try {
                  oldSocket.close();
                } catch (error) {
                  console.error('Error closing timed out WebSocket:', error);
                }
              }
              // Retry after delay
              const retryDelay = 1000 * Math.pow(1.5, attempt);
              console.log(`Will retry connection in ${retryDelay}ms`);
              setTimeout(() => attemptConnection(attempt + 1), retryDelay);
            }
          }, 8000); // Increase timeout to 8 seconds

          this.socket.onopen = (event) => {
            console.log('WebSocket connection opened', event);
            clearTimeout(timeoutId);
            this.reconnectAttempts = 0;
            this.isConnecting = false;
            if (this.options.onOpen) this.options.onOpen(event);
            resolve();
          };

          this.socket.onclose = (event) => {
            console.log('WebSocket connection closed', event);
            clearTimeout(timeoutId);
            this.isConnecting = false;
            if (this.options.onClose) this.options.onClose(event);
            
            // If connection was once successfully opened, try to reconnect
            if (event.wasClean === false && this.gameId) {
              // Try to reconnect
              if (this.reconnectAttempts < this.maxReconnectAttempts) {
                const retryDelay = 1000 * Math.pow(1.5, this.reconnectAttempts);
                this.reconnectTimeout = setTimeout(() => {
                  this.reconnectAttempts++;
                  console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                  this.connect(this.gameId!).catch(e => {
                    console.error('Reconnection failed:', e);
                  });
                }, retryDelay);
              } else {
                console.log(`Maximum reconnection attempts (${this.maxReconnectAttempts}) reached, stopping reconnection`);
              }
            }
          };

          this.socket.onerror = (event) => {
            console.error('WebSocket error:', event);
            // Simplified error handling
            if (this.options.onError) this.options.onError(event);
          };

          this.socket.onmessage = (event) => {
            try {
              const eventData = JSON.parse(event.data) as WebSocketEvent;
              this.handleMessage(eventData);
            } catch (error) {
              console.error('Error parsing WebSocket message:', error, event.data);
            }
          };
        };

        // Start first attempt
        attemptConnection();
      } catch (error) {
        this.isConnecting = false;
        console.error('Error creating WebSocket connection:', error);
        reject(error);
      }
    });
  }

  // Disconnect WebSocket connection
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

  // Send message
  sendMessage(type: string, data: any): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected, cannot send message');
      return false;
    }

    try {
      const message = JSON.stringify({ type, data });
      console.log('Sending WebSocket message:', message);
      this.socket.send(message);
      return true;
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      return false;
    }
  }

  // Handle received messages
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
        console.error('WebSocket error:', event.data);
        break;
      default:
        console.warn('Unknown WebSocket message type:', event.type);
    }
  }

  // Send game action
  sendAction(action: Omit<GameAction, 'timestamp'>): boolean {
    return this.sendMessage('game_action', action);
  }

  // Whether connected
  isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
}

// Create WebSocket singleton
let wsInstance: WebSocketService | null = null;

export function getWebSocketService(options?: WebSocketOptions, forceNew: boolean = false): WebSocketService {
  // If need to force create new instance, or instance does not exist
  if (forceNew || !wsInstance) {
    // If old instance exists, disconnect first
    if (wsInstance) {
      console.log('Creating new WebSocket service instance, disconnecting old connection');
      wsInstance.disconnect();
    }
    wsInstance = new WebSocketService(options);
  } else if (options) {
    // Update options
    console.log('Updating WebSocket service options');
    wsInstance.options = { ...wsInstance.options, ...options };
  }

  return wsInstance;
}

// Add a method to reset WebSocket instance
export function resetWebSocketService(): void {
  if (wsInstance) {
    console.log('Resetting WebSocket service instance');
    wsInstance.disconnect();
    wsInstance = null;
  }
} 