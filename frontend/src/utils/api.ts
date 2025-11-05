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

export interface StreamChunk {
  provider: string;
  content: string;
  is_final: boolean;
  tokens_used?: number;
  metadata?: Record<string, any>;
  error?: string;
}

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/api/chat', request);
    return response.data;
  },

  /**
   * Stream a chat message using Server-Sent Events (SSE).
   *
   * @param request - Chat request
   * @param onChunk - Callback for each chunk received
   * @param onError - Callback for errors
   * @param onComplete - Callback when stream completes
   * @returns Function to abort the stream
   */
  streamMessage: (
    request: ChatRequest,
    onChunk: (chunk: StreamChunk) => void,
    onError: (error: Error) => void,
    onComplete: () => void
  ): (() => void) => {
    const controller = new AbortController();

    fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error('Response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        const processChunk = () => {
          reader.read().then(({ done, value }) => {
            if (done) {
              onComplete();
              return;
            }

            // Decode chunk and add to buffer
            buffer += decoder.decode(value, { stream: true });

            // Process complete SSE messages
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const chunkData: StreamChunk = JSON.parse(line.slice(6));

                  if (chunkData.error) {
                    onError(new Error(chunkData.error));
                    return;
                  }

                  onChunk(chunkData);

                  if (chunkData.is_final) {
                    onComplete();
                    return;
                  }
                } catch (err) {
                  console.error('Failed to parse SSE chunk:', err);
                  onError(err as Error);
                  return;
                }
              }
            }

            // Continue reading
            processChunk();
          }).catch(err => {
            if (err.name !== 'AbortError') {
              onError(err);
            }
          });
        };

        processChunk();
      })
      .catch(err => {
        if (err.name !== 'AbortError') {
          onError(err);
        }
      });

    // Return abort function
    return () => controller.abort();
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
