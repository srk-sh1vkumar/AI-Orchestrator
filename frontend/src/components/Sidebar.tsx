import React, { useEffect, useState } from 'react';
import {
  Bot,
  Activity,
  Settings,
  CheckCircle,
  XCircle,
  Circle,
  RefreshCw
} from 'lucide-react';
import { clsx } from 'clsx';
import { chatApi } from '../utils/api';
import type { HealthStatus, LLMProvider } from '../types';

interface SidebarProps {
  selectedProvider?: LLMProvider;
  onProviderSelect: (provider?: LLMProvider) => void;
}

const providerInfo: Record<string, { name: string; icon: string }> = {
  claude_code: { name: 'Claude Code', icon: '🤖' },
  chatgpt: { name: 'ChatGPT', icon: '💬' },
  gemini: { name: 'Gemini', icon: '✨' },
  claude: { name: 'Claude', icon: '🧠' },
  local: { name: 'Local LLM', icon: '🏠' },
};

export const Sidebar: React.FC<SidebarProps> = ({
  selectedProvider,
  onProviderSelect
}) => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const data = await chatApi.getHealth();
      setHealth(data);
    } catch (error) {
      console.error('Failed to fetch health:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: boolean) => {
    if (status) return <CheckCircle className="w-4 h-4 text-green-500" />;
    return <XCircle className="w-4 h-4 text-red-500" />;
  };

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Bot className="w-6 h-6 text-primary-400" />
          <h1 className="text-lg font-bold">AI Orchestrator</h1>
        </div>
      </div>

      {/* Status */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            <span className="text-sm font-medium">System Status</span>
          </div>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="p-1 hover:bg-gray-800 rounded transition-colors"
          >
            <RefreshCw className={clsx('w-4 h-4', loading && 'animate-spin')} />
          </button>
        </div>

        {health && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span>Overall</span>
              <span className={clsx(
                'px-2 py-0.5 rounded-full font-medium',
                health.status === 'healthy' && 'bg-green-900 text-green-300',
                health.status === 'degraded' && 'bg-yellow-900 text-yellow-300',
                health.status === 'unhealthy' && 'bg-red-900 text-red-300'
              )}>
                {health.status}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Providers */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="mb-3 flex items-center gap-2">
          <Settings className="w-4 h-4" />
          <span className="text-sm font-medium">LLM Providers</span>
        </div>

        <div className="space-y-2">
          <button
            onClick={() => onProviderSelect(undefined)}
            className={clsx(
              'w-full text-left px-3 py-2 rounded-lg transition-colors text-sm',
              !selectedProvider
                ? 'bg-primary-600 text-white'
                : 'hover:bg-gray-800'
            )}
          >
            <div className="flex items-center gap-2">
              <Circle className="w-4 h-4" />
              <span className="font-medium">Auto-route</span>
            </div>
            <div className="text-xs text-gray-400 mt-1 ml-6">
              Let AI choose best provider
            </div>
          </button>

          {Object.entries(providerInfo).map(([key, info]) => {
            const isAvailable = health?.providers[key] ?? false;
            const isSelected = selectedProvider === key;

            return (
              <button
                key={key}
                onClick={() => onProviderSelect(key as LLMProvider)}
                disabled={!isAvailable}
                className={clsx(
                  'w-full text-left px-3 py-2 rounded-lg transition-colors text-sm',
                  isSelected && 'bg-primary-600 text-white',
                  !isSelected && isAvailable && 'hover:bg-gray-800',
                  !isAvailable && 'opacity-50 cursor-not-allowed'
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span>{info.icon}</span>
                    <span className="font-medium">{info.name}</span>
                  </div>
                  {getStatusIcon(isAvailable)}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800 text-xs text-gray-400">
        <div>v1.0.0</div>
        <div className="mt-1">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-400 hover:text-primary-300"
          >
            API Docs
          </a>
        </div>
      </div>
    </div>
  );
};
