import React, { useState, useEffect } from 'react';
import {
  Bug, Zap, FlaskConical, Terminal, CheckCircle, XCircle, Clock,
  PlayCircle, Power, RefreshCw, Settings, AlertCircle, Eye,
} from 'lucide-react';
import axios from 'axios';

interface DebugRequest {
  message: string;
  provider?: string;
  include_routing_decision: boolean;
  include_context: boolean;
  include_timing: boolean;
}

interface DebugResponse {
  request_id: string;
  timestamp: string;
  original_message: string;
  routing_decision?: Record<string, any>;
  selected_provider: string;
  provider_response?: string;
  context_used?: Record<string, any>;
  timing?: Record<string, number>;
  errors: string[];
  warnings: string[];
}

interface ProviderTestResult {
  provider: string;
  success: boolean;
  response?: string;
  error?: string;
  latency_ms: number;
  timestamp: string;
}

interface MockModeStatus {
  mock_mode_enabled: boolean;
  mock_responses_configured: number;
  mock_responses: string[];
}

const DevToolsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'debug' | 'test' | 'mock'>('debug');

  // Debug section state
  const [debugMessage, setDebugMessage] = useState('');
  const [debugProvider, setDebugProvider] = useState('');
  const [includeRouting, setIncludeRouting] = useState(true);
  const [includeContext, setIncludeContext] = useState(true);
  const [includeTiming, setIncludeTiming] = useState(true);
  const [debugResult, setDebugResult] = useState<DebugResponse | null>(null);
  const [debugLoading, setDebugLoading] = useState(false);

  // Provider test state
  const [testProvider, setTestProvider] = useState('gemini');
  const [testMessage, setTestMessage] = useState('Hello! This is a test message. Please respond with "Test successful".');
  const [testResults, setTestResults] = useState<ProviderTestResult[]>([]);
  const [testLoading, setTestLoading] = useState(false);

  // Mock mode state
  const [mockStatus, setMockStatus] = useState<MockModeStatus | null>(null);
  const [mockProvider, setMockProvider] = useState('gemini');
  const [mockPattern, setMockPattern] = useState('.*');
  const [mockResponse, setMockResponse] = useState('This is a mock response for testing.');

  // Fetch mock mode status on mount
  useEffect(() => {
    fetchMockStatus();
  }, []);

  const fetchMockStatus = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/dev/mock-mode/status');
      setMockStatus(res.data);
    } catch (error) {
      console.error('Failed to fetch mock status:', error);
    }
  };

  const handleDebugRequest = async () => {
    setDebugLoading(true);
    try {
      const request: DebugRequest = {
        message: debugMessage,
        provider: debugProvider || undefined,
        include_routing_decision: includeRouting,
        include_context: includeContext,
        include_timing: includeTiming,
      };

      const res = await axios.post<DebugResponse>(
        'http://localhost:8000/api/dev/debug',
        request
      );

      setDebugResult(res.data);
    } catch (error: any) {
      setDebugResult({
        request_id: 'error',
        timestamp: new Date().toISOString(),
        original_message: debugMessage,
        selected_provider: 'error',
        errors: [error.message || 'Request failed'],
        warnings: [],
      });
    } finally {
      setDebugLoading(false);
    }
  };

  const handleTestProvider = async () => {
    setTestLoading(true);
    try {
      const res = await axios.post<ProviderTestResult>(
        'http://localhost:8000/api/dev/test-provider',
        {
          provider: testProvider,
          test_message: testMessage,
          timeout_seconds: 30,
        }
      );

      setTestResults([res.data, ...testResults]);
    } catch (error: any) {
      const errorResult: ProviderTestResult = {
        provider: testProvider,
        success: false,
        error: error.message || 'Test failed',
        latency_ms: 0,
        timestamp: new Date().toISOString(),
      };
      setTestResults([errorResult, ...testResults]);
    } finally {
      setTestLoading(false);
    }
  };

  const handleToggleMockMode = async () => {
    try {
      if (mockStatus?.mock_mode_enabled) {
        await axios.post('http://localhost:8000/api/dev/mock-mode/disable');
      } else {
        await axios.post('http://localhost:8000/api/dev/mock-mode/enable');
      }
      await fetchMockStatus();
    } catch (error) {
      console.error('Failed to toggle mock mode:', error);
    }
  };

  const handleAddMockResponse = async () => {
    try {
      await axios.post('http://localhost:8000/api/dev/mock-responses', {
        provider: mockProvider,
        pattern: mockPattern,
        response: mockResponse,
        delay_ms: 0,
      });
      await fetchMockStatus();
      setMockPattern('.*');
      setMockResponse('This is a mock response for testing.');
    } catch (error) {
      console.error('Failed to add mock response:', error);
    }
  };

  const handleClearMockResponses = async () => {
    try {
      await axios.delete('http://localhost:8000/api/dev/mock-responses');
      await fetchMockStatus();
    } catch (error) {
      console.error('Failed to clear mock responses:', error);
    }
  };

  const renderDebugTab = () => (
    <div className="space-y-6">
      {/* Debug Input */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Bug className="w-5 h-5 text-blue-600" />
          Debug Request
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message
            </label>
            <textarea
              value={debugMessage}
              onChange={(e) => setDebugMessage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder="Enter your message to debug..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Provider (optional)
            </label>
            <select
              value={debugProvider}
              onChange={(e) => setDebugProvider(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Auto (let router decide)</option>
              <option value="gemini">Gemini</option>
              <option value="local">Local LLM</option>
              <option value="claude_code">Claude Code</option>
              <option value="chatgpt">ChatGPT</option>
              <option value="claude">Claude</option>
            </select>
          </div>

          <div className="flex gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeRouting}
                onChange={(e) => setIncludeRouting(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Include routing decision</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeContext}
                onChange={(e) => setIncludeContext(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Include context</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={includeTiming}
                onChange={(e) => setIncludeTiming(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Include timing</span>
            </label>
          </div>

          <button
            onClick={handleDebugRequest}
            disabled={!debugMessage || debugLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {debugLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Debugging...
              </>
            ) : (
              <>
                <PlayCircle className="w-4 h-4" />
                Debug Request
              </>
            )}
          </button>
        </div>
      </div>

      {/* Debug Results */}
      {debugResult && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Eye className="w-5 h-5 text-green-600" />
            Debug Results
          </h3>

          <div className="space-y-4">
            {/* Metadata */}
            <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm text-gray-600">Request ID</p>
                <p className="font-mono text-sm">{debugResult.request_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Timestamp</p>
                <p className="font-mono text-sm">{new Date(debugResult.timestamp).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Selected Provider</p>
                <p className="font-semibold text-sm">{debugResult.selected_provider}</p>
              </div>
              {debugResult.timing && (
                <div>
                  <p className="text-sm text-gray-600">Total Time</p>
                  <p className="font-semibold text-sm">{debugResult.timing.total_ms?.toFixed(2)}ms</p>
                </div>
              )}
            </div>

            {/* Routing Decision */}
            {debugResult.routing_decision && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Routing Decision</h4>
                <pre className="p-4 bg-gray-900 text-green-400 rounded-lg overflow-x-auto text-xs">
                  {JSON.stringify(debugResult.routing_decision, null, 2)}
                </pre>
              </div>
            )}

            {/* Provider Response */}
            {debugResult.provider_response && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Provider Response</h4>
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-gray-800 whitespace-pre-wrap">{debugResult.provider_response}</p>
                </div>
              </div>
            )}

            {/* Context */}
            {debugResult.context_used && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Context Used</h4>
                <pre className="p-4 bg-gray-900 text-blue-400 rounded-lg overflow-x-auto text-xs">
                  {JSON.stringify(debugResult.context_used, null, 2)}
                </pre>
              </div>
            )}

            {/* Errors & Warnings */}
            {debugResult.errors.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-2">
                  <XCircle className="w-4 h-4" />
                  Errors
                </h4>
                <ul className="space-y-1">
                  {debugResult.errors.map((error, idx) => (
                    <li key={idx} className="text-sm text-red-600 p-2 bg-red-50 rounded">
                      {error}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {debugResult.warnings.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-yellow-700 mb-2 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Warnings
                </h4>
                <ul className="space-y-1">
                  {debugResult.warnings.map((warning, idx) => (
                    <li key={idx} className="text-sm text-yellow-600 p-2 bg-yellow-50 rounded">
                      {warning}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );

  const renderTestTab = () => (
    <div className="space-y-6">
      {/* Test Configuration */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-600" />
          Provider Testing
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Provider
            </label>
            <select
              value={testProvider}
              onChange={(e) => setTestProvider(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="gemini">Gemini</option>
              <option value="local">Local LLM</option>
              <option value="claude_code">Claude Code</option>
              <option value="chatgpt">ChatGPT</option>
              <option value="claude">Claude</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Test Message
            </label>
            <textarea
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
            />
          </div>

          <button
            onClick={handleTestProvider}
            disabled={testLoading}
            className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {testLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <PlayCircle className="w-4 h-4" />
                Test Provider
              </>
            )}
          </button>
        </div>
      </div>

      {/* Test Results */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Terminal className="w-5 h-5 text-gray-600" />
          Test Results
        </h3>

        {testResults.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No test results yet. Run a provider test to see results.</p>
        ) : (
          <div className="space-y-3">
            {testResults.map((result, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg border-2 ${
                  result.success
                    ? 'bg-green-50 border-green-200'
                    : 'bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {result.success ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-600" />
                      )}
                      <span className="font-semibold">{result.provider}</span>
                      <span className="text-sm text-gray-500">
                        {new Date(result.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-600 mb-2">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {result.latency_ms.toFixed(2)}ms
                      </span>
                    </div>

                    {result.success && result.response && (
                      <p className="text-sm text-gray-700 mt-2 p-2 bg-white rounded border border-green-200">
                        {result.response}
                      </p>
                    )}

                    {!result.success && result.error && (
                      <p className="text-sm text-red-700 mt-2 p-2 bg-white rounded border border-red-200">
                        Error: {result.error}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderMockTab = () => (
    <div className="space-y-6">
      {/* Mock Mode Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <FlaskConical className="w-5 h-5 text-purple-600" />
          Mock Mode
        </h3>

        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg mb-4">
          <div>
            <p className="font-semibold text-gray-900">
              Mock Mode: {mockStatus?.mock_mode_enabled ? 'Enabled' : 'Disabled'}
            </p>
            <p className="text-sm text-gray-600">
              {mockStatus?.mock_responses_configured || 0} mock responses configured
            </p>
          </div>
          <button
            onClick={handleToggleMockMode}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
              mockStatus?.mock_mode_enabled
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-green-600 hover:bg-green-700 text-white'
            }`}
          >
            <Power className="w-4 h-4" />
            {mockStatus?.mock_mode_enabled ? 'Disable' : 'Enable'}
          </button>
        </div>

        {mockStatus?.mock_mode_enabled && (
          <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <p className="text-sm text-purple-800">
              <strong>Mock mode is active.</strong> All LLM requests will use configured mock responses instead of real API calls.
              This is useful for offline development and testing.
            </p>
          </div>
        )}
      </div>

      {/* Add Mock Response */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-600" />
          Add Mock Response
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Provider
            </label>
            <select
              value={mockProvider}
              onChange={(e) => setMockProvider(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="gemini">Gemini</option>
              <option value="local">Local LLM</option>
              <option value="claude_code">Claude Code</option>
              <option value="chatgpt">ChatGPT</option>
              <option value="claude">Claude</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pattern (Regex)
            </label>
            <input
              type="text"
              value={mockPattern}
              onChange={(e) => setMockPattern(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder=".*"
            />
            <p className="text-xs text-gray-500 mt-1">
              Regex pattern to match incoming messages. Use .* to match all messages.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mock Response
            </label>
            <textarea
              value={mockResponse}
              onChange={(e) => setMockResponse(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleAddMockResponse}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
            >
              <PlayCircle className="w-4 h-4" />
              Add Mock Response
            </button>
            <button
              onClick={handleClearMockResponses}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Clear All
            </button>
          </div>
        </div>
      </div>

      {/* Configured Mock Responses */}
      {mockStatus && mockStatus.mock_responses.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Configured Mock Responses
          </h3>
          <ul className="space-y-2">
            {mockStatus.mock_responses.map((key, idx) => (
              <li key={idx} className="p-3 bg-gray-50 rounded-lg">
                <code className="text-sm text-gray-800">{key}</code>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Terminal className="w-8 h-8 text-blue-600" />
          Developer Tools
        </h1>
        <p className="text-gray-600 mt-1">
          Debug requests, test providers, and configure mock mode for offline development
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('debug')}
            className={`px-4 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'debug'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-600 border-transparent hover:text-gray-900'
            }`}
          >
            <span className="flex items-center gap-2">
              <Bug className="w-4 h-4" />
              Debug
            </span>
          </button>
          <button
            onClick={() => setActiveTab('test')}
            className={`px-4 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'test'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-600 border-transparent hover:text-gray-900'
            }`}
          >
            <span className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Test Providers
            </span>
          </button>
          <button
            onClick={() => setActiveTab('mock')}
            className={`px-4 py-3 font-medium transition-colors border-b-2 ${
              activeTab === 'mock'
                ? 'text-blue-600 border-blue-600'
                : 'text-gray-600 border-transparent hover:text-gray-900'
            }`}
          >
            <span className="flex items-center gap-2">
              <FlaskConical className="w-4 h-4" />
              Mock Mode
            </span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'debug' && renderDebugTab()}
        {activeTab === 'test' && renderTestTab()}
        {activeTab === 'mock' && renderMockTab()}
      </div>
    </div>
  );
};

export default DevToolsPage;
