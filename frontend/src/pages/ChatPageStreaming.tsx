import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { useStreamingChat } from '../hooks/useStreamingChat';
import type { LLMProvider } from '../types';
import { AlertCircle, Zap, ZapOff } from 'lucide-react';

interface ChatPageProps {
  selectedProvider?: LLMProvider;
}

export const ChatPageStreaming: React.FC<ChatPageProps> = ({ selectedProvider: initialProvider }) => {
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider | undefined>(initialProvider);
  const [enableStreaming, setEnableStreaming] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    isStreaming,
    error,
    sendMessage,
    stopStreaming,
    clearMessages
  } = useStreamingChat(enableStreaming);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string, provider?: LLMProvider) => {
    await sendMessage(content, provider || selectedProvider, enableStreaming);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Welcome to AI Orchestrator
              </h2>
              <p className="text-gray-600 mb-2">
                I can help you with code generation, deployment, incident analysis, and more!
              </p>
              <p className="text-sm text-gray-500 mb-8">
                {enableStreaming ? (
                  <span className="inline-flex items-center gap-1 text-green-600">
                    <Zap className="w-4 h-4" />
                    Streaming enabled - responses appear in real-time
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-gray-600">
                    <ZapOff className="w-4 h-4" />
                    Streaming disabled - responses appear when complete
                  </span>
                )}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                <div className="p-4 border rounded-lg hover:border-primary-500 cursor-pointer transition-colors"
                     onClick={() => handleSendMessage('Build a REST API for user authentication')}>
                  <div className="font-medium text-gray-900 mb-1">Build API</div>
                  <div className="text-sm text-gray-600">Create a REST API with authentication</div>
                </div>
                <div className="p-4 border rounded-lg hover:border-primary-500 cursor-pointer transition-colors"
                     onClick={() => handleSendMessage('Create a monitoring dashboard')}>
                  <div className="font-medium text-gray-900 mb-1">Create Dashboard</div>
                  <div className="text-sm text-gray-600">Build a monitoring dashboard UI</div>
                </div>
                <div className="p-4 border rounded-lg hover:border-primary-500 cursor-pointer transition-colors"
                     onClick={() => handleSendMessage('Analyze production incident with high CPU')}>
                  <div className="font-medium text-gray-900 mb-1">Analyze Incident</div>
                  <div className="text-sm text-gray-600">Investigate production issues</div>
                </div>
                <div className="p-4 border rounded-lg hover:border-primary-500 cursor-pointer transition-colors"
                     onClick={() => handleSendMessage('Deploy application to Kubernetes')}>
                  <div className="font-medium text-gray-900 mb-1">Deploy App</div>
                  <div className="text-sm text-gray-600">Deploy to Kubernetes cluster</div>
                </div>
              </div>
            </div>
          )}

          {messages.map((message, idx) => (
            <div key={idx}>
              <ChatMessage
                message={message}
                toolResults={undefined}
                executionTime={undefined}
              />
              {message.isStreaming && (
                <div className="flex items-center gap-2 text-xs text-gray-500 mt-1 ml-12">
                  <div className="flex space-x-1">
                    <div className="w-1.5 h-1.5 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-1.5 h-1.5 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-1.5 h-1.5 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span>Streaming response...</span>
                  <button
                    onClick={stopStreaming}
                    className="text-red-600 hover:text-red-700 underline"
                  >
                    Stop
                  </button>
                </div>
              )}
              {message.tokensUsed && (
                <div className="text-xs text-gray-500 mt-1 ml-12">
                  Tokens used: {message.tokensUsed}
                </div>
              )}
            </div>
          ))}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-medium text-red-900">Error</div>
                <div className="text-sm text-red-700">{error}</div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Provider and Streaming Controls */}
      <div className="border-t bg-gray-50 p-3">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <label className="text-sm font-medium text-gray-700">Provider:</label>
          <select
            value={selectedProvider || ''}
            onChange={(e) => setSelectedProvider(e.target.value as LLMProvider || undefined)}
            className="text-sm border rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">Auto-route (Smart Selection)</option>
            <option value="claude_code">Claude Code (Code Generation)</option>
            <option value="claude">Claude (Analysis & Reasoning)</option>
            <option value="chatgpt">ChatGPT (UI & Workflows)</option>
            <option value="gemini">Gemini (Prompts)</option>
            <option value="local">Local (Ollama - Privacy)</option>
          </select>
          {selectedProvider && (
            <button
              onClick={() => setSelectedProvider(undefined)}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Clear
            </button>
          )}

          {/* Streaming Toggle */}
          <div className="flex-1"></div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enableStreaming}
              onChange={(e) => setEnableStreaming(e.target.checked)}
              disabled={isStreaming}
              className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700 flex items-center gap-1">
              {enableStreaming ? (
                <>
                  <Zap className="w-4 h-4 text-green-600" />
                  Streaming
                </>
              ) : (
                <>
                  <ZapOff className="w-4 h-4 text-gray-400" />
                  Non-streaming
                </>
              )}
            </span>
          </label>

          <span className="text-xs text-gray-500">
            {selectedProvider
              ? `Using: ${selectedProvider.replace('_', ' ')}`
              : 'Intelligent routing enabled'}
          </span>
        </div>
      </div>

      {/* Input area */}
      <ChatInput
        onSendMessage={handleSendMessage}
        isLoading={isStreaming}
        selectedProvider={selectedProvider}
      />
    </div>
  );
};
