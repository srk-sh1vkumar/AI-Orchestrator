import React, { useEffect, useState } from 'react';
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  PieChart,
  Zap,
  Calendar,
} from 'lucide-react';
import axios from 'axios';

interface CostBreakdown {
  provider: string;
  cost: number;
  tokens: number;
  requests: number;
  percentage: number;
}

interface CostSummary {
  total_cost: number;
  total_tokens: number;
  request_count: number;
  breakdown: CostBreakdown[];
  period_start?: string;
  period_end?: string;
}

// Backend API response structure
interface BudgetApiResponse {
  budget_id: string;
  budget_name: string;
  user_id?: string;
  project_id?: string;
  provider?: string;
  limits: {
    daily?: number;
    weekly?: number;
    monthly?: number;
  };
  spent: {
    daily: number;
    weekly: number;
    monthly: number;
  };
  utilization: {
    daily: number;
    weekly: number;
    monthly: number;
  };
  alert_status: {
    warning_triggered: boolean;
    critical_triggered: boolean;
    budget_exceeded: boolean;
  };
}

// Normalized budget for display
interface Budget {
  id: string;
  budget_name: string;
  user_id?: string;
  project_id?: string;
  provider?: string;
  daily_limit?: number;
  weekly_limit?: number;
  monthly_limit?: number;
  current_spend: number;
  usage_percentage: number;
  warning_threshold: number;
  critical_threshold: number;
  status: 'healthy' | 'warning' | 'critical' | 'exceeded';
  alert_email?: string;
}

interface Alert {
  id: string;
  budget_id: string;
  budget_name: string;
  alert_type: 'warning' | 'critical' | 'exceeded';
  current_spend: number;
  limit: number;
  timestamp: string;
  acknowledged: boolean;
}

// Backend API response for projections
interface ProjectionApiResponse {
  based_on_days: number;
  daily_average: number;
  projections: {
    weekly: number;
    monthly: number;
    yearly: number;
  };
  warning?: string;
}

interface CostProjection {
  provider: string;
  current_daily_avg: number;
  projected_weekly: number;
  projected_monthly: number;
  trend: 'increasing' | 'stable' | 'decreasing';
  confidence: number;
}

const CostDashboardPage: React.FC = () => {
  const [costSummary, setCostSummary] = useState<CostSummary | null>(null);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [projections, setProjections] = useState<CostProjection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [timeRange, setTimeRange] = useState<'today' | 'week' | 'month'>('today');

  const fetchCostData = async () => {
    try {
      setLoading(true);

      // Calculate date range
      const now = new Date();
      const startDate = new Date();
      if (timeRange === 'today') {
        startDate.setHours(0, 0, 0, 0);
      } else if (timeRange === 'week') {
        startDate.setDate(now.getDate() - 7);
      } else if (timeRange === 'month') {
        startDate.setMonth(now.getMonth() - 1);
      }

      // Fetch all cost data in parallel
      const [summaryRes, budgetsRes, alertsRes, projectionsRes] = await Promise.all([
        axios.get(`http://localhost:8000/api/costs/summary?start_date=${startDate.toISOString()}&end_date=${now.toISOString()}`),
        axios.get('http://localhost:8000/api/costs/budgets'),
        axios.get('http://localhost:8000/api/costs/alerts'),
        axios.get('http://localhost:8000/api/costs/projections'),
      ]);

      setCostSummary(summaryRes.data);

      // Transform budget API response to match frontend interface
      const normalizedBudgets: Budget[] = (budgetsRes.data.budgets || []).map((b: BudgetApiResponse) => {
        const dailySpend = b.spent?.daily || 0;
        const weeklySpend = b.spent?.weekly || 0;
        const monthlySpend = b.spent?.monthly || 0;
        const dailyLimit = b.limits?.daily || 0;
        const weeklyLimit = b.limits?.weekly || 0;
        const monthlyLimit = b.limits?.monthly || 0;

        // Use the most relevant spend/limit based on what's configured
        const currentSpend = dailyLimit > 0 ? dailySpend : weeklyLimit > 0 ? weeklySpend : monthlySpend;
        const limit = dailyLimit > 0 ? dailyLimit : weeklyLimit > 0 ? weeklyLimit : monthlyLimit;
        const usagePercentage = limit > 0 ? (currentSpend / limit) * 100 : 0;

        let status: 'healthy' | 'warning' | 'critical' | 'exceeded' = 'healthy';
        if (b.alert_status?.budget_exceeded) {
          status = 'exceeded';
        } else if (b.alert_status?.critical_triggered) {
          status = 'critical';
        } else if (b.alert_status?.warning_triggered) {
          status = 'warning';
        }

        return {
          id: b.budget_id,
          budget_name: b.budget_name,
          user_id: b.user_id,
          project_id: b.project_id,
          provider: b.provider,
          daily_limit: b.limits?.daily,
          weekly_limit: b.limits?.weekly,
          monthly_limit: b.limits?.monthly,
          current_spend: currentSpend,
          usage_percentage: usagePercentage,
          warning_threshold: 70,  // Default thresholds
          critical_threshold: 90,
          status,
        };
      });

      setBudgets(normalizedBudgets);
      setAlerts(alertsRes.data.alerts || []);

      // Transform projection API response
      const projectionData: ProjectionApiResponse = projectionsRes.data;
      const normalizedProjections: CostProjection[] = costSummary?.breakdown.map(item => ({
        provider: item.provider,
        current_daily_avg: projectionData.daily_average,
        projected_weekly: projectionData.projections.weekly,
        projected_monthly: projectionData.projections.monthly,
        trend: 'stable' as const,  // We don't have trend data yet
        confidence: projectionData.based_on_days >= 7 ? 85 : 50,
      })) || [];

      setProjections(normalizedProjections);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch cost data');
      console.error('Cost data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCostData();
  }, [timeRange]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchCostData();
    }, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, timeRange]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    if (num >= 1_000_000) {
      return (num / 1_000_000).toFixed(1) + 'M';
    } else if (num >= 1_000) {
      return (num / 1_000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-orange-600 bg-orange-100';
      case 'exceeded': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing': return <TrendingUp className="w-4 h-4 text-red-500" />;
      case 'decreasing': return <TrendingDown className="w-4 h-4 text-green-500" />;
      default: return <div className="w-4 h-4 text-gray-500">—</div>;
    }
  };

  if (loading && !costSummary) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <DollarSign className="w-12 h-12 animate-pulse text-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading cost data...</p>
        </div>
      </div>
    );
  }

  if (error && !costSummary) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 mb-2">Error loading cost data</p>
          <p className="text-gray-600 text-sm">{error}</p>
          <button
            onClick={fetchCostData}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const totalCost = costSummary?.total_cost || 0;
  const totalTokens = costSummary?.total_tokens || 0;
  const totalRequests = costSummary?.request_count || 0;
  const breakdown = costSummary?.breakdown || [];

  return (
    <div className="h-full overflow-auto bg-gray-50">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
              <DollarSign className="w-8 h-8 text-primary-600" />
              Cost Dashboard
            </h1>
            <p className="text-gray-600 mt-1">Real-time LLM cost tracking and budget management</p>
          </div>
          <div className="flex items-center gap-4">
            {/* Time Range Selector */}
            <div className="flex bg-white rounded-lg border border-gray-200 p-1">
              {(['today', 'week', 'month'] as const).map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    timeRange === range
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {range === 'today' ? 'Today' : range === 'week' ? '7 Days' : '30 Days'}
                </button>
              ))}
            </div>

            {/* Auto Refresh Toggle */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg border transition-colors flex items-center gap-2 ${
                autoRefresh
                  ? 'bg-green-50 border-green-200 text-green-700'
                  : 'bg-white border-gray-200 text-gray-600'
              }`}
            >
              <Clock className="w-4 h-4" />
              <span className="text-sm font-medium">
                {autoRefresh ? 'Auto Refresh: On' : 'Auto Refresh: Off'}
              </span>
            </button>
          </div>
        </div>

        {/* Active Alerts */}
        {alerts.filter(a => !a.acknowledged).length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-red-900 mb-2">Budget Alerts</h3>
                <div className="space-y-2">
                  {alerts.filter(a => !a.acknowledged).map((alert) => (
                    <div key={alert.id} className="text-sm text-red-800">
                      <span className="font-medium">{alert.budget_name}</span>: {alert.alert_type} threshold reached
                      ({formatCurrency(alert.current_spend)} / {formatCurrency(alert.limit)})
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Total Cost */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Total Cost</span>
              <DollarSign className="w-5 h-5 text-primary-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{formatCurrency(totalCost)}</div>
            <div className="mt-2 text-sm text-gray-600">
              {totalRequests.toLocaleString()} requests
            </div>
          </div>

          {/* Total Tokens */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Total Tokens</span>
              <Zap className="w-5 h-5 text-yellow-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{formatNumber(totalTokens)}</div>
            <div className="mt-2 text-sm text-gray-600">
              {totalRequests > 0 ? Math.round(totalTokens / totalRequests).toLocaleString() : 0} avg/request
            </div>
          </div>

          {/* Active Budgets */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-600">Budget Status</span>
              <BarChart3 className="w-5 h-5 text-blue-600" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{budgets.length}</div>
            <div className="mt-2 text-sm text-gray-600">
              {budgets.filter(b => b.status === 'healthy').length} healthy,
              {budgets.filter(b => b.status !== 'healthy').length} alerts
            </div>
          </div>
        </div>

        {/* Cost Breakdown by Provider */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <PieChart className="w-5 h-5 text-primary-600" />
            Cost Breakdown by Provider
          </h2>
          {breakdown.length > 0 ? (
            <div className="space-y-3">
              {breakdown.map((item) => (
                <div key={item.provider} className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 capitalize">{item.provider}</span>
                      <span className="text-sm font-semibold text-gray-900">{formatCurrency(item.cost)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${item.percentage}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span className="text-xs text-gray-500">
                        {formatNumber(item.tokens)} tokens • {item.requests} requests
                      </span>
                      <span className="text-xs text-gray-600">{item.percentage.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <PieChart className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">No LLM requests yet</p>
              <p className="text-gray-400 text-xs mt-1">Cost breakdown will appear when you start using the AI Orchestrator</p>
            </div>
          )}
        </div>

        {/* Budget Status Cards */}
        {budgets.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-primary-600" />
              Budget Monitoring
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {budgets.map((budget) => (
                <div
                  key={budget.id}
                  className={`border-2 rounded-lg p-4 ${
                    budget.status === 'exceeded' ? 'border-red-300 bg-red-50' :
                    budget.status === 'critical' ? 'border-orange-300 bg-orange-50' :
                    budget.status === 'warning' ? 'border-yellow-300 bg-yellow-50' :
                    'border-green-300 bg-green-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-900">{budget.budget_name}</h3>
                      {budget.provider && (
                        <span className="text-xs text-gray-600 capitalize">{budget.provider}</span>
                      )}
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(budget.status)}`}>
                      {budget.status}
                    </span>
                  </div>
                  <div className="mb-2">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-700">Spend: {formatCurrency(budget.current_spend)}</span>
                      <span className="text-gray-700">
                        Limit: {formatCurrency(budget.daily_limit || budget.weekly_limit || budget.monthly_limit || 0)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-300 rounded-full h-2.5">
                      <div
                        className={`h-2.5 rounded-full transition-all duration-500 ${
                          budget.usage_percentage >= budget.critical_threshold ? 'bg-red-600' :
                          budget.usage_percentage >= budget.warning_threshold ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(budget.usage_percentage, 100)}%` }}
                      />
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      {budget.usage_percentage.toFixed(1)}% used
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cost Projections */}
        {projections.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-primary-600" />
              Cost Projections
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Daily Avg</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Projected Week</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Projected Month</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trend</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {projections.map((proj) => (
                    <tr key={proj.provider}>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900 capitalize">{proj.provider}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(proj.current_daily_avg)}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(proj.projected_weekly)}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(proj.projected_monthly)}</td>
                      <td className="px-4 py-3">{getTrendIcon(proj.trend)}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full"
                              style={{ width: `${proj.confidence}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-600">{proj.confidence}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-sm text-gray-500">
          Last updated: {new Date().toLocaleString()}
          {autoRefresh && <span className="ml-2">• Updates every 30 seconds</span>}
        </div>
      </div>
    </div>
  );
};

export default CostDashboardPage;
