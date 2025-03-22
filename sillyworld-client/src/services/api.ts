import axios from 'axios';

// API基础URL环境变量设置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8006';
console.log('API Base URL:', API_BASE_URL);

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 较长的超时时间，考虑到AI响应可能较慢
  headers: {
    'Content-Type': 'application/json',
  },
});

// 添加请求拦截器 - 用于调试
api.interceptors.request.use(
  (config) => {
    // 调试信息
    console.log('Sending request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// 添加响应拦截器 - 用于调试
api.interceptors.response.use(
  (response) => {
    // 调试信息
    console.log('Received response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('Response error:', error.response?.status || 'Unknown', error.message);
    return Promise.reject(error);
  }
);

export interface Player {
    id: string;
    name: string;
    prompt?: string;
    balance: number;
    items: Item[];
    is_active: boolean;
    last_action?: string;
    last_action_time?: string;
}

export interface Item {
    id: string;
    name: string;
    description: string;
    effect: string;
    price: number;
    type: string;
    used?: boolean;
}

export interface GameState {
    game_id: string;
    round: number;
    phase: string;
    players: Player[];
    prize_pool: number;
    current_player_id?: string;
    status: 'waiting' | 'active' | 'paused' | 'completed';
    winner_id?: string;
    created_at: string;
    updated_at: string;
}

export interface GameAction {
    player_id: string;
    action_type: string;
    target_player_id?: string;
    target_player?: string;
    amount?: number;
    message?: string;
    item_id?: string;
    item_type?: string;
    description?: string;
    timestamp: string;
    thinking_process?: string;  // AI的思考过程
    public_message?: string;    // AI的公开发言
}

export interface GameResult {
    game_id: string;
    winner_id: string;
    winner_name: string;
    final_balance: number;
    players: Player[];
    rounds: number;
    duration: string;
    prize_pool: number;
}

// 游戏API
export const gameApi = {
    // 创建新游戏
    createGame: async (players: Player[]): Promise<GameState> => {
        const response = await api.post('/api/games', { players });
        return response.data;
    },

    // 获取游戏状态
    getGameState: async (gameId: string): Promise<GameState> => {
        const response = await api.get(`/api/games/${gameId}`);
        return response.data;
    },

    // 开始游戏
    startGame: async (gameId: string): Promise<GameState> => {
        const response = await api.post(`/api/games/${gameId}/start`);
        return response.data;
    },

    // 执行游戏行动
    performAction: async (gameId: string, action: Omit<GameAction, 'timestamp'>): Promise<GameState> => {
        const response = await api.post(`/api/games/${gameId}/action`, action);
        return response.data;
    },

    // 购买物品
    buyItem: async (gameId: string, itemType: string): Promise<GameState> => {
        const response = await api.post(`/api/games/${gameId}/buy-item`, { item_type: itemType });
        return response.data;
    },

    // 使用物品
    useItem: async (gameId: string, itemId: string, targetPlayerId: string): Promise<GameState> => {
        const response = await api.post(`/api/games/${gameId}/use-item`, { 
            item_id: itemId,
            target_player_id: targetPlayerId
        });
        return response.data;
    },

    // 谈判/请求
    negotiate: async (gameId: string, targetPlayerId: string, amount: number, message: string): Promise<GameState> => {
        const response = await api.post(`/api/games/${gameId}/negotiate`, {
            target_player_id: targetPlayerId,
            amount: amount,
            message: message
        });
        return response.data;
    },

    // 回应谈判/请求
    respondNegotiation: async (gameId: string, negotiationId: string, accepted: boolean): Promise<GameState> => {
        const response = await api.post(`/api/games/${gameId}/respond-negotiation`, {
            negotiation_id: negotiationId,
            accepted: accepted
        });
        return response.data;
    },

    // 获取游戏结果
    getGameResult: async (gameId: string): Promise<GameResult> => {
        const response = await api.get(`/api/games/${gameId}/result`);
        return response.data;
    }
};

export default api;

export async function fetchFromAPI(endpoint: string) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}

export async function postToAPI(endpoint: string, data: any) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
} 