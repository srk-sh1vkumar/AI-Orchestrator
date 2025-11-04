import React, { useEffect, useState } from 'react';
import { Activity, Server, Database, Clock, TrendingUp, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';

interface ProviderMetrics {
  provider: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens: number;
  avg_response_time_ms: number;
  cache_hit_rate: number;
  rate_limit_stats: {
    rate_per_minute?: number;
    available_tokens?: number;
    burst_capacity?: number;
    daily_limit?: number;
    daily_used?: number;
    daily_remaining?: number;
    date?: string;
  };
}

interface CacheMetrics {
  enabled: boolean;
  total_queries: number;
  cache_hits: number;
  cache_misses: number;
  hit_rate: number;
  avg_similarity_threshold: number;
  total_entries: number;
}

interface SystemMetrics {
  uptime_seconds: number;
  total_requests: number;
  providers_healthy: number;
  providers_total: number;
  cache_enabled: boolean;
  rate_limiting_enabled: boolean;
}

interface MonitoringData {
  timestamp: string;
  system: SystemMetrics;
  providers: ProviderMetrics[];
  cache: CacheMetrics;
  rate_limits: Record<string, any>;
}

const MonitoringDashboardPage: React.FC = () => {
  const [monitoringData, setMonitoringData] = useState<MonitoringData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchMonitoringData = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/monitoring/metrics');
      setMonitoringData(response.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchMonitoringData();
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  if (loading && !monitoringData) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <Activity className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading monitoring data...</p>
        </div>
      </div>
    );
  }

  if (error && !monitoringData) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <p className="text-red-600 font-semibold">Error loading monitoring data</p>
          <p className="text-gray-600 mt-2">{error}</p>
          <button
            onClick={fetchMonitoringData}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!monitoringData) return null;

  const { system, providers, cache } = monitoringData;
  const healthPercentage = (system.providers_healthy / system.providers_total) * 100;

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Monitoring Dashboard</h1>
          <p className="text-gray-600 mt-1">Real-time system metrics and performance</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded text-primary-600 focus:ring-primary-500"
            />
            Auto-refresh (5s)
          </label>
          <button
            onClick={fetchMonitoringData}
            className="px-3 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 text-sm"
          >
            Refresh Now
          </button>
        </div>
      </div>

      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">System Health</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {healthPercentage.toFixed(0)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {system.providers_healthy}/{system.providers_total} providers
              </p>
            </div>
            <div className={`p-3 rounded-full ${healthPercentage === 100 ? 'bg-green-100' : healthPercentage >= 50 ? 'bg-yellow-100' : 'bg-red-100'}`}>
              {healthPercentage === 100 ? (
                <CheckCircle className="w-6 h-6 text-green-600" />
              ) : (
                <AlertCircle className="w-6 h-6 text-yellow-600" />
              )}
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Requests</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatNumber(system.total_requests)}
              </p>
              <p className="text-xs text-gray-500 mt-1">Since startup</p>
            </div>
            <div className="p-3 rounded-full bg-blue-100">
              <TrendingUp className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Cache Hit Rate</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {(cache.hit_rate * 100).toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {cache.cache_hits}/{cache.total_queries} hits
              </p>
            </div>
            <div className="p-3 rounded-full bg-purple-100">
              <Database className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">System Uptime</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {formatUptime(system.uptime_seconds).split(' ')[0]}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {formatUptime(system.uptime_seconds)}
              </p>
            </div>
            <div className="p-3 rounded-full bg-green-100">
              <Clock className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Provider Metrics */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Server className="w-5 h-5" />
            Provider Metrics
          </h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {providers.map((provider) => {
              const successRate = provider.total_requests > 0
                ? (provider.successful_requests / provider.total_requests) * 100
                : 0;

              return (
                <div key={provider.provider} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold capitalize">{provider.provider}</h3>
                      {provider.total_requests > 0 ? (
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                          Idle
                        </span>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">Success Rate</p>
                      <p className={`text-lg font-bold ${successRate >= 95 ? 'text-green-600' : successRate >= 80 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {successRate.toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-gray-600">Total Requests</p>
                      <p className="text-sm font-semibold">{formatNumber(provider.total_requests)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Successful</p>
                      <p className="text-sm font-semibold text-green-600">
                        {formatNumber(provider.successful_requests)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Failed</p>
                      <p className="text-sm font-semibold text-red-600">
                        {formatNumber(provider.failed_requests)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Avg Response Time</p>
                      <p className="text-sm font-semibold">
                        {provider.avg_response_time_ms.toFixed(0)}ms
                      </p>
                    </div>
                  </div>

                  {provider.rate_limit_stats.rate_per_minute !== undefined && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-gray-600">Rate Limit (per minute)</p>
                        <p className="text-xs font-semibold">
                          {provider.rate_limit_stats.available_tokens?.toFixed(0) || 0} / {provider.rate_limit_stats.rate_per_minute} tokens
                        </p>
                      </div>
                      <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all"
                          style={{
                            width: `${((provider.rate_limit_stats.available_tokens || 0) / (provider.rate_limit_stats.rate_per_minute || 1)) * 100}%`
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {provider.rate_limit_stats.daily_limit !== undefined && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-gray-600">Daily Quota {provider.rate_limit_stats.date && `(${provider.rate_limit_stats.date})`}</p>
                        <p className="text-xs font-semibold">
                          {provider.rate_limit_stats.daily_used || 0} / {provider.rate_limit_stats.daily_limit} requests
                        </p>
                      </div>
                      <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            ((provider.rate_limit_stats.daily_used || 0) / (provider.rate_limit_stats.daily_limit || 1)) > 0.8
                              ? 'bg-red-600'
                              : ((provider.rate_limit_stats.daily_used || 0) / (provider.rate_limit_stats.daily_limit || 1)) > 0.5
                              ? 'bg-yellow-600'
                              : 'bg-green-600'
                          }`}
                          style={{
                            width: `${((provider.rate_limit_stats.daily_used || 0) / (provider.rate_limit_stats.daily_limit || 1)) * 100}%`
                          }}
                        />
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {provider.rate_limit_stats.daily_remaining || 0} requests remaining today
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Cache Statistics */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Database className="w-5 h-5" />
            Semantic Cache Statistics
          </h2>
        </div>
        <div className="p-6">
          {cache.enabled ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Cache Hits</p>
                <p className="text-3xl font-bold text-green-600">{formatNumber(cache.cache_hits)}</p>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Cache Misses</p>
                <p className="text-3xl font-bold text-yellow-600">{formatNumber(cache.cache_misses)}</p>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Total Queries</p>
                <p className="text-3xl font-bold text-blue-600">{formatNumber(cache.total_queries)}</p>
              </div>
              <div className="col-span-1 md:col-span-3 mt-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-600">Cache Efficiency</p>
                  <p className="text-sm font-semibold">{(cache.hit_rate * 100).toFixed(2)}%</p>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all"
                    style={{ width: `${cache.hit_rate * 100}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Similarity Threshold: {cache.avg_similarity_threshold.toFixed(2)}
                </p>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <XCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">Semantic cache is not enabled</p>
            </div>
          )}
        </div>
      </div>
      </div>
    </div>
  );
};

export default MonitoringDashboardPage;
