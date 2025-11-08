import { useState, useCallback, useRef } from 'react';
import { chatApi, StreamChunk } from '../utils/api';
import type { ChatRequest, LLMProvider } from '../types';

export interface StreamingMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  provider?: LLMProvider;
  timestamp: string;
  isStreaming?: boolean;
  tokensUsed?: number;
}

export interface UseStreamingChatReturn {
  messages: StreamingMessage[];
  isStreaming: boolean;
  error: string | null;
  sendMessage: (content: string, provider?: LLMProvider, useStreaming?: boolean) => Promise<void>;
  stopStreaming: () => void;
  clearMessages: () => void;
}

/**
 * Custom hook for managing streaming chat interactions.
 *
 * Features:
 * - Incremental message updates as chunks arrive
 * - Automatic error handling
 * - Stream cancellation
 * - Fallback to non-streaming mode
 */
export const useStreamingChat = (enableStreaming: boolean = true): UseStreamingChatReturn => {
  const [messages, setMessages] = useState<StreamingMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortStreamRef = useRef<(() => void) | null>(null);
  const currentMessageIndexRef = useRef<number>(-1);

  const stopStreaming = useCallback(() => {
    if (abortStreamRef.current) {
      abortStreamRef.current();
      abortStreamRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  const sendMessage = useCallback(async (
    content: string,
    provider?: LLMProvider,
    useStreaming: boolean = enableStreaming
  ) => {
    setError(null);
    stopStreaming(); // Cancel any ongoing stream

    // Add user message
    const userMessage: StreamingMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);

    // Prepare request
    const request: ChatRequest = {
      message: provider ? `@${provider}: ${content}` : content,
      enable_tools: true,
      enable_collaboration: true,
    };

    if (useStreaming) {
      // Streaming mode
      setIsStreaming(true);

      // Add placeholder for assistant message
      const assistantIndex = messages.length + 1;
      currentMessageIndexRef.current = assistantIndex;

      const assistantMessage: StreamingMessage = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        isStreaming: true,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Start streaming
      abortStreamRef.current = chatApi.streamMessage(
        request,
        // onChunk
        (chunk: StreamChunk) => {
          setMessages(prev => {
            const updated = [...prev];
            if (updated[assistantIndex]) {
              updated[assistantIndex] = {
                ...updated[assistantIndex],
                content: updated[assistantIndex].content + chunk.content,
                provider: chunk.provider as LLMProvider,
              };
            }
            return updated;
          });
        },
        // onError
        (err: Error) => {
          console.error('Streaming error:', err);
          setError(err.message);
          setIsStreaming(false);
          abortStreamRef.current = null;

          // Mark message as complete (with error)
          setMessages(prev => {
            const updated = [...prev];
            if (updated[assistantIndex]) {
              updated[assistantIndex] = {
                ...updated[assistantIndex],
                isStreaming: false,
              };
            }
            return updated;
          });
        },
        // onComplete
        () => {
          setIsStreaming(false);
          abortStreamRef.current = null;

          // Mark message as complete
          setMessages(prev => {
            const updated = [...prev];
            if (updated[assistantIndex]) {
              updated[assistantIndex] = {
                ...updated[assistantIndex],
                isStreaming: false,
              };
            }
            return updated;
          });
        }
      );
    } else {
      // Non-streaming mode (fallback)
      try {
        const response = await chatApi.sendMessage(request);

        const assistantMessage: StreamingMessage = {
          role: 'assistant',
          content: response.message,
          provider: response.provider,
          timestamp: response.timestamp,
        };

        setMessages(prev => [...prev, assistantMessage]);

      } catch (err: any) {
        console.error('Error sending message:', err);
        setError(err.response?.data?.detail || 'Failed to send message. Please try again.');
      }
    }
  }, [enableStreaming, messages.length, stopStreaming]);

  const clearMessages = useCallback(() => {
    stopStreaming();
    setMessages([]);
    setError(null);
  }, [stopStreaming]);

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    stopStreaming,
    clearMessages,
  };
};
