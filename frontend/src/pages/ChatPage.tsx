import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { chatApi } from '../utils/api';
import type { Message, LLMProvider, ChatResponse } from '../types';
import { AlertCircle } from 'lucide-react';

interface ChatPageProps {
  selectedProvider?: LLMProvider;
}

export const ChatPage: React.FC<ChatPageProps> = ({ selectedProvider: initialProvider }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider | undefined>(initialProvider);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string, provider?: LLMProvider) => {
    setError(null);

    // Add user message
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Prepare request with provider prefix if specified
      let finalMessage = content;
      if (provider) {
        finalMessage = `@${provider}: ${content}`;
      }

      const response = await chatApi.sendMessage({
        message: finalMessage,
        enable_tools: true,
        enable_collaboration: true,
      });

      setLastResponse(response);

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.message,
        provider: response.provider,
        timestamp: response.timestamp,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Add system message for collaboration if applicable
      if (response.collaboration_steps && response.collaboration_steps.length > 1) {
        const collabMessage: Message = {
          role: 'system',
          content: `✨ Multi-LLM Collaboration:\n${response.collaboration_steps
            .map(step => `${step.step}. ${step.provider} (${step.execution_time.toFixed(2)}s)`)
            .join('\n')}`,
          timestamp: response.timestamp,
        };
        setMessages(prev => [...prev, collabMessage]);
      }

    } catch (err: any) {
      console.error('Error sending message:', err);
      setError(err.response?.data?.detail || 'Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
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
              <p className="text-gray-600 mb-8">
                I can help you with code generation, deployment, incident analysis, and more!
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
            <ChatMessage
              key={idx}
              message={message}
              toolResults={
                idx === messages.length - 1 &&
                message.role === 'assistant' &&
                lastResponse
                  ? lastResponse.tool_results
                  : undefined
              }
              executionTime={
                idx === messages.length - 1 &&
                message.role === 'assistant' &&
                lastResponse
                  ? lastResponse.execution_time
                  : undefined
              }
            />
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

      {/* Provider Selection Bar */}
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
            <option value="gemini">Gemini (Free Tier - Prompts)</option>
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
          <div className="flex-1"></div>
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
        isLoading={isLoading}
        selectedProvider={selectedProvider}
      />
    </div>
  );
};
