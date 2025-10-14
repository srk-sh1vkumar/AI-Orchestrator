import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, Clock, Zap } from 'lucide-react';
import type { Message, ToolResult } from '../types';
import { clsx } from 'clsx';

interface ChatMessageProps {
  message: Message;
  toolResults?: ToolResult[];
  executionTime?: number;
}

const providerColors: Record<string, string> = {
  claude_code: 'bg-blue-100 text-blue-800',
  chatgpt: 'bg-green-100 text-green-800',
  gemini: 'bg-purple-100 text-purple-800',
  claude: 'bg-indigo-100 text-indigo-800',
  local: 'bg-orange-100 text-orange-800',
};

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  toolResults,
  executionTime
}) => {
  const isUser = message.role === 'user';

  return (
    <div className={clsx(
      'flex gap-3 p-4',
      isUser ? 'bg-gray-50' : 'bg-white'
    )}>
      <div className="flex-shrink-0">
        {isUser ? (
          <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
        )}
      </div>

      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-gray-900">
            {isUser ? 'You' : 'AI Orchestrator'}
          </span>
          {message.provider && (
            <span className={clsx(
              'px-2 py-0.5 rounded-full text-xs font-medium',
              providerColors[message.provider] || 'bg-gray-100 text-gray-800'
            )}>
              {message.provider.replace('_', ' ')}
            </span>
          )}
          <span className="text-xs text-gray-500">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>

        <div className="prose prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {toolResults && toolResults.length > 0 && (
          <div className="mt-3 space-y-2">
            <div className="text-sm font-medium text-gray-700 flex items-center gap-1">
              <Zap className="w-4 h-4" />
              Tools Executed ({toolResults.length})
            </div>
            <div className="space-y-1">
              {toolResults.map((tool, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 text-sm p-2 rounded bg-gray-50"
                >
                  <span className={clsx(
                    'w-2 h-2 rounded-full',
                    tool.success ? 'bg-green-500' : 'bg-red-500'
                  )} />
                  <span className="font-medium">{tool.tool_type}</span>
                  <span className="text-gray-600">→</span>
                  <span className="text-gray-600">{tool.operation}</span>
                  <span className="text-gray-400 text-xs ml-auto">
                    {tool.execution_time.toFixed(2)}s
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {executionTime !== undefined && (
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            <span>{executionTime.toFixed(2)}s</span>
          </div>
        )}
      </div>
    </div>
  );
};
