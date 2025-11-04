import React, { useState } from 'react';
import { Code, FileCode, Zap, CheckCircle, AlertCircle, RefreshCw, Play } from 'lucide-react';
import { clsx } from 'clsx';
import { chatApi } from '../utils/api';

interface ImprovementSuggestion {
  id: string;
  category: 'performance' | 'security' | 'code-quality' | 'architecture';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  filePath?: string;
  status: 'pending' | 'in-progress' | 'completed';
}

export const SelfDevelopmentPage: React.FC = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [suggestions, setSuggestions] = useState<ImprovementSuggestion[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [analysisResult, setAnalysisResult] = useState<string>('');

  const categories = [
    { id: 'all', name: 'All', icon: '📋' },
    { id: 'performance', name: 'Performance', icon: '⚡' },
    { id: 'security', name: 'Security', icon: '🔒' },
    { id: 'code-quality', name: 'Code Quality', icon: '✨' },
    { id: 'architecture', name: 'Architecture', icon: '🏗️' },
  ];

  const runSelfAnalysis = async () => {
    setAnalyzing(true);
    setAnalysisResult('');

    try {
      // Ask orchestrator to analyze itself
      const response = await chatApi.sendMessage({
        message: `@codellama: Analyze the AI Orchestrator codebase for improvements.
        Focus on:
        1. Code quality and best practices
        2. Performance optimizations
        3. Security vulnerabilities
        4. Architecture improvements
        5. Test coverage

        Provide specific, actionable recommendations with file paths.`,
        enable_tools: true,
        enable_collaboration: false,
      });

      setAnalysisResult(response.message);

      // Parse response into suggestions (mock for now)
      const mockSuggestions: ImprovementSuggestion[] = [
        {
          id: '1',
          category: 'performance',
          title: 'Implement response caching',
          description: 'Add Redis caching for frequently used LLM responses to reduce latency',
          priority: 'high',
          filePath: 'src/core/orchestrator.py',
          status: 'pending',
        },
        {
          id: '2',
          category: 'security',
          title: 'Add rate limiting',
          description: 'Implement per-user rate limiting to prevent API abuse',
          priority: 'high',
          filePath: 'src/api/main.py',
          status: 'pending',
        },
        {
          id: '3',
          category: 'code-quality',
          title: 'Increase test coverage',
          description: 'Add unit tests for routing logic (current coverage: 65%)',
          priority: 'medium',
          filePath: 'tests/test_router.py',
          status: 'pending',
        },
        {
          id: '4',
          category: 'architecture',
          title: 'Implement circuit breaker',
          description: 'Add circuit breaker pattern for external LLM API calls',
          priority: 'medium',
          filePath: 'src/providers/base.py',
          status: 'pending',
        },
      ];

      setSuggestions(mockSuggestions);
    } catch (error) {
      console.error('Self-analysis failed:', error);
      setAnalysisResult('Failed to analyze codebase. Please try again.');
    } finally {
      setAnalyzing(false);
    }
  };

  const implementSuggestion = async (suggestion: ImprovementSuggestion) => {
    // Update status to in-progress
    setSuggestions(prev =>
      prev.map(s => s.id === suggestion.id ? { ...s, status: 'in-progress' } : s)
    );

    try {
      // Ask orchestrator to implement the improvement
      const response = await chatApi.sendMessage({
        message: `@claude_code: Implement this improvement: ${suggestion.title}

        Description: ${suggestion.description}
        File: ${suggestion.filePath || 'appropriate file'}

        Please provide the complete implementation.`,
        enable_tools: true,
        enable_collaboration: false,
      });

      // Update status to completed
      setSuggestions(prev =>
        prev.map(s => s.id === suggestion.id ? { ...s, status: 'completed' } : s)
      );

      alert('Improvement implemented! Check the response for details.');
    } catch (error) {
      console.error('Implementation failed:', error);
      // Revert status
      setSuggestions(prev =>
        prev.map(s => s.id === suggestion.id ? { ...s, status: 'pending' } : s)
      );
    }
  };

  const filteredSuggestions = selectedCategory === 'all'
    ? suggestions
    : suggestions.filter(s => s.category === selectedCategory);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-blue-600 bg-blue-50 border-blue-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'in-progress': return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      default: return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Code className="w-6 h-6 text-primary-600" />
              Self Development
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              AI-powered analysis and automatic code improvements
            </p>
          </div>
          <button
            onClick={runSelfAnalysis}
            disabled={analyzing}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
              analyzing
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-primary-600 text-white hover:bg-primary-700'
            )}
          >
            {analyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                Run Self-Analysis
              </>
            )}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-gray-900">{suggestions.length}</div>
              <div className="text-sm text-gray-600">Total Suggestions</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-red-600">
                {suggestions.filter(s => s.priority === 'high').length}
              </div>
              <div className="text-sm text-gray-600">High Priority</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-green-600">
                {suggestions.filter(s => s.status === 'completed').length}
              </div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="text-2xl font-bold text-blue-600">
                {suggestions.filter(s => s.status === 'in-progress').length}
              </div>
              <div className="text-sm text-gray-600">In Progress</div>
            </div>
          </div>

          {/* Category Filter */}
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex flex-wrap gap-2">
              {categories.map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={clsx(
                    'px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2',
                    selectedCategory === cat.id
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  )}
                >
                  <span>{cat.icon}</span>
                  <span>{cat.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Analysis Result */}
          {analysisResult && (
            <div className="bg-white rounded-lg p-6 border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <FileCode className="w-5 h-5" />
                Analysis Result
              </h2>
              <div className="prose prose-sm max-w-none">
                <pre className="whitespace-pre-wrap text-sm text-gray-700 bg-gray-50 p-4 rounded">
                  {analysisResult}
                </pre>
              </div>
            </div>
          )}

          {/* Suggestions List */}
          {suggestions.length === 0 ? (
            <div className="bg-white rounded-lg p-12 border border-gray-200 text-center">
              <Code className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No suggestions yet
              </h3>
              <p className="text-gray-600 mb-6">
                Run a self-analysis to discover improvements for the codebase
              </p>
              <button
                onClick={runSelfAnalysis}
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
              >
                <Zap className="w-4 h-4" />
                Start Analysis
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredSuggestions.map(suggestion => (
                <div
                  key={suggestion.id}
                  className="bg-white rounded-lg p-6 border border-gray-200 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {getStatusIcon(suggestion.status)}
                        <h3 className="text-lg font-semibold text-gray-900">
                          {suggestion.title}
                        </h3>
                        <span className={clsx(
                          'px-2 py-1 rounded text-xs font-medium border',
                          getPriorityColor(suggestion.priority)
                        )}>
                          {suggestion.priority}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-2">{suggestion.description}</p>
                      {suggestion.filePath && (
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                          <FileCode className="w-4 h-4" />
                          <code className="bg-gray-100 px-2 py-1 rounded">
                            {suggestion.filePath}
                          </code>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => implementSuggestion(suggestion)}
                      disabled={suggestion.status !== 'pending'}
                      className={clsx(
                        'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors',
                        suggestion.status === 'pending'
                          ? 'bg-primary-600 text-white hover:bg-primary-700'
                          : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                      )}
                    >
                      <Play className="w-4 h-4" />
                      {suggestion.status === 'completed' ? 'Implemented' : 'Implement'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
