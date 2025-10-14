import axios from 'axios';
import type {
  ChatRequest,
  ChatResponse,
  HealthStatus,
  ProvidersResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/api/chat', request);
    return response.data;
  },

  getHealth: async (): Promise<HealthStatus> => {
    const response = await api.get<HealthStatus>('/api/health');
    return response.data;
  },

  getProviders: async (): Promise<ProvidersResponse> => {
    const response = await api.get<ProvidersResponse>('/api/providers');
    return response.data;
  },
};

export default api;
