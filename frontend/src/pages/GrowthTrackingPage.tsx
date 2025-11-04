import React, { useState, useEffect } from 'react';
import { BookOpen, TrendingUp, Award, FileCode, Plus, Calendar, BarChart } from 'lucide-react';
import axios from 'axios';

interface Reflection {
  id: string;
  integration_tag: string;
  week_of: string;
  learning_hours: number;
  topics: string[];
  goal_title: string;
  progress_delta: number;
  accomplishments: string[];
  blockers: string[];
  insights: string;
  next_week_focus: string[];
  created_at: string;
}

interface ProjectArtifact {
  id: string;
  integration_tag: string;
  title: string;
  description: string;
  artifact_type: string;
  url?: string;
  file_path?: string;
  metadata: Record<string, any>;
  created_at: string;
}

interface PerformanceMetric {
  id: string;
  integration_tag: string;
  metric_name: string;
  metric_value: number;
  unit: string;
  context?: string;
  timestamp: string;
}

interface GrowthSummary {
  total_reflections: number;
  total_learning_hours: number;
  total_projects: number;
  total_metrics: number;
  total_leadership_artifacts: number;
  total_architecture_decisions: number;
  reflections_by_tag: Record<string, number>;
  latest_reflection: Reflection | null;
}

type ViewMode = 'summary' | 'reflections' | 'projects' | 'metrics';

const API_BASE = 'http://localhost:8000';

export const GrowthTrackingPage: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('summary');
  const [summary, setSummary] = useState<GrowthSummary | null>(null);
  const [reflections, setReflections] = useState<Reflection[]>([]);
  const [projects, setProjects] = useState<ProjectArtifact[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  const [showReflectionForm, setShowReflectionForm] = useState(false);
  const [loading, setLoading] = useState(false);

  // Integration tags from goals
  const integrationTags = [
    { value: 'ai_systems_design', label: 'AI Systems Design & Orchestration' },
    { value: 'mlops_observability', label: 'MLOps & Observability' },
    { value: 'leadership_influence', label: 'Leadership & Influence' },
    { value: 'fintech_ai_architecture', label: 'FinTech AI Architecture' },
    { value: 'self_dev_system', label: 'Personal Development System' },
    { value: 'local_llm_setup', label: 'Local LLM Setup (DeepSeek)' },
    { value: 'architecture_enhancements', label: 'Architecture Enhancements' },
    { value: 'system_integration', label: 'Bi-Directional Sync (System Integration)' },
  ];

  useEffect(() => {
    fetchSummary();
    fetchReflections(); // Always fetch reflections for the chart
  }, []);

  useEffect(() => {
    if (viewMode === 'reflections') {
      fetchReflections();
    } else if (viewMode === 'projects') {
      fetchProjects();
    } else if (viewMode === 'metrics') {
      fetchMetrics();
    }
  }, [viewMode]);

  const fetchSummary = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/api/growth/summary`);
      setSummary(response.data);
    } catch (error) {
      console.error('Failed to fetch summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchReflections = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/api/growth/reflections`);
      setReflections(response.data);
    } catch (error) {
      console.error('Failed to fetch reflections:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/api/growth/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/api/growth/metrics`);
      setMetrics(response.data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const createReflection = async (data: Partial<Reflection>) => {
    try {
      await axios.post(`${API_BASE}/api/growth/reflections`, data);
      setShowReflectionForm(false);
      fetchReflections();
      fetchSummary();
    } catch (error) {
      console.error('Failed to create reflection:', error);
    }
  };

  const renderSummaryView = () => {
    if (!summary) {
      return <div className="text-center py-8 text-gray-500">Loading summary...</div>;
    }

    return (
      <div className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Learning Hours</p>
                <p className="text-3xl font-bold text-primary-600">{summary.total_learning_hours}</p>
              </div>
              <BookOpen className="w-12 h-12 text-primary-200" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Reflections</p>
                <p className="text-3xl font-bold text-green-600">{summary.total_reflections}</p>
              </div>
              <Calendar className="w-12 h-12 text-green-200" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Projects</p>
                <p className="text-3xl font-bold text-blue-600">{summary.total_projects}</p>
              </div>
              <FileCode className="w-12 h-12 text-blue-200" />
            </div>
          </div>
        </div>

        {/* Learning Hours Visualization */}
        {reflections.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Learning Hours Over Time</h3>
            <div className="space-y-2">
              {reflections.slice(0, 5).reverse().map((reflection, idx) => {
                const maxHours = Math.max(...reflections.map(r => r.learning_hours));
                return (
                  <div key={reflection.id} className="flex items-center gap-3">
                    <div className="text-xs text-gray-600 w-20">{reflection.week_of}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-100 rounded-full h-6 relative overflow-hidden">
                          <div
                            className="bg-gradient-to-r from-primary-500 to-primary-600 h-6 rounded-full flex items-center justify-end px-2 transition-all"
                            style={{ width: `${(reflection.learning_hours / maxHours) * 100}%` }}
                          >
                            <span className="text-xs font-medium text-white">{reflection.learning_hours}h</span>
                          </div>
                        </div>
                        <span className="text-xs font-medium text-green-600">+{reflection.progress_delta}%</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{reflection.goal_title}</div>
                    </div>
                  </div>
                );
              })}
            </div>
            {reflections.length > 5 && (
              <p className="text-xs text-gray-500 mt-3 text-center">
                Showing latest 5 weeks of {reflections.length} total reflections
              </p>
            )}
          </div>
        )}

        {/* Reflections by Tag */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Learning Activity by Goal</h3>
          <div className="space-y-3">
            {Object.entries(summary.reflections_by_tag).map(([tag, count]) => {
              const tagLabel = integrationTags.find(t => t.value === tag)?.label || tag;
              return (
                <div key={tag} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{tagLabel}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full"
                        style={{ width: `${(count / summary.total_reflections) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900 w-8 text-right">{count}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Latest Reflection */}
        {summary.latest_reflection && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Latest Reflection</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">{summary.latest_reflection.goal_title}</span>
                <span className="text-sm text-gray-500">Week of {summary.latest_reflection.week_of}</span>
              </div>
              <p className="text-sm text-gray-600">{summary.latest_reflection.insights}</p>
              <div className="flex items-center gap-4 text-sm">
                <span className="text-gray-600">{summary.latest_reflection.learning_hours} hours</span>
                <span className="text-green-600 font-medium">+{summary.latest_reflection.progress_delta}% progress</span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderReflectionsView = () => {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-900">Weekly Reflections</h2>
          <button
            onClick={() => setShowReflectionForm(true)}
            className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Reflection
          </button>
        </div>

        {showReflectionForm && (
          <ReflectionForm
            integrationTags={integrationTags}
            onSubmit={createReflection}
            onCancel={() => setShowReflectionForm(false)}
          />
        )}

        <div className="space-y-4">
          {reflections.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No reflections yet. Create your first one!</p>
            </div>
          ) : (
            reflections.map(reflection => (
              <div key={reflection.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{reflection.goal_title}</h3>
                    <p className="text-sm text-gray-600">Week of {reflection.week_of}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-primary-600">{reflection.learning_hours}h</p>
                    <p className="text-sm text-green-600">+{reflection.progress_delta}%</p>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Topics</h4>
                    <div className="flex flex-wrap gap-2">
                      {reflection.topics.map((topic, idx) => (
                        <span key={idx} className="bg-primary-100 text-primary-700 text-xs px-2 py-1 rounded">
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Accomplishments</h4>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                      {reflection.accomplishments.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>

                  {reflection.blockers.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Blockers</h4>
                      <ul className="list-disc list-inside text-sm text-red-600 space-y-1">
                        {reflection.blockers.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Insights</h4>
                    <p className="text-sm text-gray-600">{reflection.insights}</p>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Next Week's Focus</h4>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                      {reflection.next_week_focus.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  const renderProjectsView = () => {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Project Artifacts</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {projects.length === 0 ? (
            <div className="col-span-2 bg-white rounded-lg shadow p-12 text-center">
              <FileCode className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No project artifacts yet.</p>
            </div>
          ) : (
            projects.map(project => (
              <div key={project.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">{project.title}</h3>
                  <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded">
                    {project.artifact_type}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-4">{project.description}</p>
                {project.url && (
                  <a
                    href={project.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    View Artifact →
                  </a>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  const renderMetricsView = () => {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Performance Metrics</h2>

        <div className="space-y-4">
          {metrics.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <BarChart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No metrics recorded yet.</p>
            </div>
          ) : (
            metrics.map(metric => (
              <div key={metric.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{metric.metric_name}</h3>
                    <p className="text-sm text-gray-600">{metric.context}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-primary-600">{metric.metric_value}</p>
                    <p className="text-sm text-gray-600">{metric.unit}</p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Growth Tracking</h1>
          <p className="text-gray-600">Track your learning journey, reflections, and progress</p>
        </div>

        {/* View Toggle */}
        <div className="flex gap-2 mb-6 border-b border-gray-200">
          <button
            onClick={() => setViewMode('summary')}
            className={`px-4 py-2 font-medium transition-colors border-b-2 ${
              viewMode === 'summary'
                ? 'text-primary-600 border-primary-600'
                : 'text-gray-600 border-transparent hover:text-gray-900'
            }`}
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Summary
            </div>
          </button>
          <button
            onClick={() => setViewMode('reflections')}
            className={`px-4 py-2 font-medium transition-colors border-b-2 ${
              viewMode === 'reflections'
                ? 'text-primary-600 border-primary-600'
                : 'text-gray-600 border-transparent hover:text-gray-900'
            }`}
          >
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              Reflections
            </div>
          </button>
          <button
            onClick={() => setViewMode('projects')}
            className={`px-4 py-2 font-medium transition-colors border-b-2 ${
              viewMode === 'projects'
                ? 'text-primary-600 border-primary-600'
                : 'text-gray-600 border-transparent hover:text-gray-900'
            }`}
          >
            <div className="flex items-center gap-2">
              <FileCode className="w-4 h-4" />
              Projects
            </div>
          </button>
          <button
            onClick={() => setViewMode('metrics')}
            className={`px-4 py-2 font-medium transition-colors border-b-2 ${
              viewMode === 'metrics'
                ? 'text-primary-600 border-primary-600'
                : 'text-gray-600 border-transparent hover:text-gray-900'
            }`}
          >
            <div className="flex items-center gap-2">
              <BarChart className="w-4 h-4" />
              Metrics
            </div>
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>
        ) : (
          <>
            {viewMode === 'summary' && renderSummaryView()}
            {viewMode === 'reflections' && renderReflectionsView()}
            {viewMode === 'projects' && renderProjectsView()}
            {viewMode === 'metrics' && renderMetricsView()}
          </>
        )}
      </div>
    </div>
  );
};

// Reflection Form Component
interface ReflectionFormProps {
  integrationTags: Array<{ value: string; label: string }>;
  onSubmit: (data: Partial<Reflection>) => void;
  onCancel: () => void;
}

const ReflectionForm: React.FC<ReflectionFormProps> = ({ integrationTags, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    integration_tag: '',
    week_of: '',
    learning_hours: 0,
    topics: '',
    goal_title: '',
    progress_delta: 0,
    accomplishments: '',
    blockers: '',
    insights: '',
    next_week_focus: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      integration_tag: formData.integration_tag,
      week_of: formData.week_of,
      learning_hours: formData.learning_hours,
      topics: formData.topics.split(',').map(t => t.trim()),
      goal_title: formData.goal_title,
      progress_delta: formData.progress_delta,
      accomplishments: formData.accomplishments.split('\n').filter(a => a.trim()),
      blockers: formData.blockers.split('\n').filter(b => b.trim()),
      insights: formData.insights,
      next_week_focus: formData.next_week_focus.split('\n').filter(f => f.trim()),
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-semibold mb-4">New Weekly Reflection</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Integration Tag</label>
            <select
              required
              value={formData.integration_tag}
              onChange={(e) => setFormData({ ...formData, integration_tag: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="">Select goal...</option>
              {integrationTags.map(tag => (
                <option key={tag.value} value={tag.value}>{tag.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Week Of</label>
            <input
              required
              type="date"
              value={formData.week_of}
              onChange={(e) => setFormData({ ...formData, week_of: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Learning Hours</label>
            <input
              required
              type="number"
              step="0.5"
              min="0"
              value={formData.learning_hours}
              onChange={(e) => setFormData({ ...formData, learning_hours: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Progress Delta (%)</label>
            <input
              required
              type="number"
              min="0"
              max="100"
              value={formData.progress_delta}
              onChange={(e) => setFormData({ ...formData, progress_delta: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Goal Title</label>
          <input
            required
            type="text"
            value={formData.goal_title}
            onChange={(e) => setFormData({ ...formData, goal_title: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Topics (comma-separated)</label>
          <input
            required
            type="text"
            value={formData.topics}
            onChange={(e) => setFormData({ ...formData, topics: e.target.value })}
            placeholder="e.g., Redis caching, Circuit breakers, Docker optimization"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Accomplishments (one per line)</label>
          <textarea
            required
            rows={3}
            value={formData.accomplishments}
            onChange={(e) => setFormData({ ...formData, accomplishments: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Blockers (one per line, optional)</label>
          <textarea
            rows={2}
            value={formData.blockers}
            onChange={(e) => setFormData({ ...formData, blockers: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Insights</label>
          <textarea
            required
            rows={3}
            value={formData.insights}
            onChange={(e) => setFormData({ ...formData, insights: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Next Week's Focus (one per line)</label>
          <textarea
            required
            rows={3}
            value={formData.next_week_focus}
            onChange={(e) => setFormData({ ...formData, next_week_focus: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Create Reflection
          </button>
        </div>
      </form>
    </div>
  );
};
