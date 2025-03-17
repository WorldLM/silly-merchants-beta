import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

console.log('API Base URL:', API_BASE_URL); // 调试日志

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 10000, // 10秒超时
    withCredentials: false, // 简化跨域请求
});

// 请求拦截器
api.interceptors.request.use(
    (config) => {
        console.log(`发送请求: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => {
        console.error('请求错误:', error);
        return Promise.reject(error);
    }
);

// 响应拦截器
api.interceptors.response.use(
    (response) => {
        console.log(`收到响应: ${response.status} ${response.config.url}`);
        return response;
    },
    (error) => {
        if (error.response) {
            // 服务器响应了，但状态码不在2xx范围内
            console.error('响应错误:', error.response.status, error.response.data);
        } else if (error.request) {
            // 请求已发送但没有收到响应
            console.error('未收到响应:', error.request);
        } else {
            // 设置请求时出错
            console.error('请求配置错误:', error.message);
        }
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
    buyItem: async (gameId: string, playerId: string, itemId: string): Promise<Player> => {
        const response = await api.post(`/api/games/${gameId}/players/${playerId}/buy`, { item_id: itemId });
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