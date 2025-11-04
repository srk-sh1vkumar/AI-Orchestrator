import React, { useState, useEffect } from 'react';
import {
  Target,
  Award,
  Book,
  TrendingUp,
  Plus,
  Edit,
  Trash2,
  CheckCircle,
  Clock,
  Sparkles,
  BarChart3,
  Code2,
  BookOpen
} from 'lucide-react';
import { clsx } from 'clsx';
import axios from 'axios';
import { ProjectEnhancements } from '../components/ProjectEnhancements';
const API_BASE = 'http://localhost:8000/api/tracker';
const GROWTH_API_BASE = 'http://localhost:8000/api/growth';

// Mapping of goal IDs/titles to integration tags
const goalToIntegrationTag: Record<string, string> = {
  'deepseek-local-setup': 'local_llm_setup',
  'ai-systems-design-mastery': 'ai_systems_design',
  'mlops-observability-expertise': 'mlops_observability',
  'leadership-stakeholder-influence': 'leadership_influence',
  'fintech-solution-architecture': 'fintech_ai_architecture',
  'personal-development-system': 'self_dev_system',
  'ai-orchestrator-enhancements': 'architecture_enhancements',
  'bi-directional-sync-tracker-chatgpt': 'system_integration',
};

interface Goal {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  progress: number;
  target_date?: string;
  created_at: string;
  completed_at?: string;
}

interface Milestone {
  id: string;
  title: string;
  description: string;
  category: string;
  achieved_at: string;
  impact: string;
}

interface Skill {
  name: string;
  category: string;
  proficiency: string;
  acquired_at: string;
}

interface Metrics {
  total_learning_hours: number;
  goals_total: number;
  goals_completed: number;
  goals_in_progress: number;
  skills_count: number;
  recent_learning_hours: number;
  milestones_count: number;
}

export const PersonalTrackerPage: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [activeTab, setActiveTab] = useState<'goals' | 'milestones' | 'skills' | 'learning' | 'enhancements'>('enhancements');
  const [showAddGoal, setShowAddGoal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [expandedGoals, setExpandedGoals] = useState<Set<string>>(new Set());

  // Modal states
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);
  const [selectedMilestone, setSelectedMilestone] = useState<Milestone | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [metricsRes, goalsRes, milestonesRes, skillsRes] = await Promise.all([
        axios.get(`${API_BASE}/metrics`),
        axios.get(`${API_BASE}/goals`),
        axios.get(`${API_BASE}/milestones`),
        axios.get(`${API_BASE}/skills`),
      ]);

      setMetrics(metricsRes.data);
      setGoals(goalsRes.data);
      setMilestones(milestonesRes.data);
      setSkills(skillsRes.data);
    } catch (error) {
      console.error('Failed to fetch tracker data:', error);
    } finally {
      setLoading(false);
    }
  };

  const createGoal = async (goal: Partial<Goal>) => {
    try {
      const newGoal = {
        id: `g${Date.now()}`,
        ...goal,
        status: 'planned',
        progress: 0,
      };
      await axios.post(`${API_BASE}/goals`, newGoal);
      fetchData();
      setShowAddGoal(false);
    } catch (error) {
      console.error('Failed to create goal:', error);
    }
  };

  const updateGoalProgress = async (goalId: string, progress: number) => {
    try {
      const goal = goals.find(g => g.id === goalId);
      if (!goal) return;

      const updated = { ...goal, progress };
      if (progress === 100 && goal.status !== 'completed') {
        updated.status = 'completed';
      }

      await axios.put(`${API_BASE}/goals/${goalId}`, updated);
      fetchData();
    } catch (error) {
      console.error('Failed to update goal:', error);
    }
  };

  const generateAIReflection = async () => {
    try {
      await axios.post(`${API_BASE}/reflections/generate`);
      alert('AI reflection generated! Check your reflections.');
    } catch (error) {
      console.error('Failed to generate reflection:', error);
    }
  };

  const toggleGoalExpansion = (goalId: string) => {
    setExpandedGoals(prev => {
      const newSet = new Set(prev);
      if (newSet.has(goalId)) {
        newSet.delete(goalId);
      } else {
        newSet.add(goalId);
      }
      return newSet;
    });
  };

  const formatDescription = (description: string) => {
    // Simple markdown-like formatting
    return description
      .split('\n')
      .map((line, idx) => {
        // Headers
        if (line.startsWith('###')) {
          return <h3 key={idx} className="text-md font-semibold mt-4 mb-2 text-gray-900">{line.replace('###', '').trim()}</h3>;
        }
        if (line.startsWith('##')) {
          return <h2 key={idx} className="text-lg font-bold mt-4 mb-2 text-gray-900">{line.replace('##', '').trim()}</h2>;
        }
        // Lists
        if (line.trim().startsWith('-') || line.trim().startsWith('*')) {
          return <li key={idx} className="ml-4 text-sm text-gray-700">{line.replace(/^[\-\*]\s*/, '').trim()}</li>;
        }
        // Bold text
        if (line.includes('**')) {
          const parts = line.split('**');
          return (
            <p key={idx} className="text-sm text-gray-700 mb-1">
              {parts.map((part, i) => i % 2 === 1 ? <strong key={i}>{part}</strong> : part)}
            </p>
          );
        }
        // Dividers
        if (line.trim() === '---') {
          return <hr key={idx} className="my-3 border-gray-300" />;
        }
        // Regular text
        if (line.trim()) {
          return <p key={idx} className="text-sm text-gray-700 mb-1">{line}</p>;
        }
        return <br key={idx} />;
      });
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      learning: 'bg-blue-100 text-blue-700 border-blue-200',
      fitness: 'bg-green-100 text-green-700 border-green-200',
      career: 'bg-purple-100 text-purple-700 border-purple-200',
      personal: 'bg-pink-100 text-pink-700 border-pink-200',
      financial: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    };
    return colors[category] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      planned: 'bg-gray-100 text-gray-700',
      in_progress: 'bg-blue-100 text-blue-700',
      completed: 'bg-green-100 text-green-700',
      paused: 'bg-yellow-100 text-yellow-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading tracker data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Target className="w-6 h-6 text-primary-600" />
              Personal Tracker
            </h1>
            <p className="text-sm text-gray-600 mt-1">
              Track your personal development, goals, and growth
            </p>
          </div>
          <button
            onClick={generateAIReflection}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            Generate AI Reflection
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Metrics Dashboard */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {metrics?.total_learning_hours || 0}h
                  </div>
                  <div className="text-sm text-gray-600">Total Learning</div>
                </div>
                <Book className="w-8 h-8 text-blue-500" />
              </div>
              <div className="mt-2 text-xs text-gray-500">
                {metrics?.recent_learning_hours || 0}h this week
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {metrics?.goals_completed || 0}/{metrics?.goals_total || 0}
                  </div>
                  <div className="text-sm text-gray-600">Goals Completed</div>
                </div>
                <Target className="w-8 h-8 text-green-500" />
              </div>
              <div className="mt-2 text-xs text-gray-500">
                {metrics?.goals_in_progress || 0} in progress
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {metrics?.skills_count || 0}
                  </div>
                  <div className="text-sm text-gray-600">Skills Gained</div>
                </div>
                <TrendingUp className="w-8 h-8 text-purple-500" />
              </div>
            </div>

            <div className="bg-white rounded-lg p-4 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {metrics?.milestones_count || 0}
                  </div>
                  <div className="text-sm text-gray-600">Milestones</div>
                </div>
                <Award className="w-8 h-8 text-yellow-500" />
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="flex border-b border-gray-200">
              {(['enhancements', 'goals', 'milestones', 'skills', 'learning'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={clsx(
                    'px-6 py-3 font-medium capitalize transition-colors border-b-2',
                    activeTab === tab
                      ? 'text-primary-600 border-primary-600'
                      : 'text-gray-600 border-transparent hover:text-gray-900'
                  )}
                >
                  {tab === 'enhancements' ? (
                    <span className="flex items-center gap-2">
                      <Code2 className="w-4 h-4" />
                      Project Enhancements
                    </span>
                  ) : (
                    tab
                  )}
                </button>
              ))}
            </div>

            <div className="p-6">
              {/* Project Enhancements Tab */}
              {activeTab === 'enhancements' && (
                <ProjectEnhancements />
              )}

              {/* Goals Tab */}
              {activeTab === 'goals' && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-semibold">Your Goals</h2>
                    <button
                      onClick={() => setShowAddGoal(true)}
                      className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                    >
                      <Plus className="w-4 h-4" />
                      Add Goal
                    </button>
                  </div>

                  {goals.length === 0 ? (
                    <div className="text-center py-12">
                      <Target className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-600">No goals yet. Start by adding your first goal!</p>
                    </div>
                  ) : (
                    goals.map(goal => (
                        <div
                          key={goal.id}
                          className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                          onClick={() => setSelectedGoal(goal)}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h3 className="font-semibold text-gray-900">{goal.title}</h3>
                              </div>
                              <p className="text-sm text-gray-600 mb-2 line-clamp-2">{goal.description.split('\n')[0]}</p>

                              <div className="flex gap-2 mb-2">
                                <span
                                  className={clsx(
                                    'px-2 py-1 rounded text-xs font-medium border',
                                    getCategoryColor(goal.category)
                                  )}
                                >
                                  {goal.category}
                                </span>
                                <span
                                  className={clsx(
                                    'px-2 py-1 rounded text-xs font-medium',
                                    getStatusColor(goal.status)
                                  )}
                                >
                                  {goal.status}
                                </span>
                                {goal.target_date && (
                                  <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700 flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {new Date(goal.target_date).toLocaleDateString()}
                                  </span>
                                )}
                              </div>
                            </div>
                            {goal.status === 'completed' && (
                              <CheckCircle className="w-6 h-6 text-green-500" />
                            )}
                          </div>

                        {/* Progress Bar */}
                        <div className="mb-2">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Progress</span>
                            <span className="font-medium">{goal.progress}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary-600 h-2 rounded-full transition-all"
                              style={{ width: `${goal.progress}%` }}
                            ></div>
                          </div>
                        </div>

                        {/* Weekly Reflection Button */}
                        {goal.status === 'active' && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              alert(`Navigate to Growth tab with pre-filled reflection for: ${goal.title}\n\nIntegration Tag: ${goalToIntegrationTag[goal.id] || 'unknown'}`);
                            }}
                            className="w-full mt-3 flex items-center justify-center gap-2 px-3 py-2 bg-green-50 hover:bg-green-100 text-green-700 rounded-md text-sm font-medium transition-colors border border-green-200"
                          >
                            <BookOpen className="w-4 h-4" />
                            Weekly Reflection
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Goal Detail Modal */}
              {selectedGoal && (
                <div
                  className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto"
                  onClick={() => setSelectedGoal(null)}
                >
                  <div
                    className="bg-white rounded-lg p-6 max-w-3xl w-full my-8"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-6">
                      <div className="flex-1">
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">{selectedGoal.title}</h2>
                        <div className="flex items-center gap-2 mb-3">
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                            {selectedGoal.category}
                          </span>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            selectedGoal.status === 'completed' ? 'bg-green-100 text-green-700' :
                            selectedGoal.status === 'in_progress' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {selectedGoal.status.replace('_', ' ')}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => setSelectedGoal(null)}
                        className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
                      >
                        ×
                      </button>
                    </div>

                    {/* Description */}
                    <div className="mb-6">
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">Description</h3>
                      <div className="text-gray-600 whitespace-pre-wrap">
                        {formatDescription(selectedGoal.description)}
                      </div>
                    </div>

                    {/* Progress Section */}
                    <div className="mb-6">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-semibold text-gray-700">Progress</h3>
                        <span className="text-sm font-medium text-gray-900">{selectedGoal.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                        <div
                          className={`h-3 rounded-full transition-all ${
                            selectedGoal.progress === 100 ? 'bg-green-500' :
                            selectedGoal.progress >= 75 ? 'bg-blue-500' :
                            selectedGoal.progress >= 50 ? 'bg-yellow-500' :
                            'bg-orange-500'
                          }`}
                          style={{ width: `${selectedGoal.progress}%` }}
                        ></div>
                      </div>

                      {/* Progress Controls */}
                      {selectedGoal.status !== 'completed' && (
                        <div className="flex gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              updateGoalProgress(selectedGoal.id, Math.min(100, selectedGoal.progress + 10));
                            }}
                            className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
                          >
                            +10%
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              updateGoalProgress(selectedGoal.id, Math.max(0, selectedGoal.progress - 10));
                            }}
                            className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
                          >
                            -10%
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              updateGoalProgress(selectedGoal.id, 100);
                            }}
                            className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
                          >
                            Mark Complete
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Timeline */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-1">Created</h3>
                        <p className="text-sm text-gray-600">
                          {new Date(selectedGoal.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-gray-700 mb-1">Target Date</h3>
                        <p className="text-sm text-gray-600">
                          {selectedGoal.target_date ? new Date(selectedGoal.target_date).toLocaleDateString() : 'Not set'}
                        </p>
                      </div>
                      {selectedGoal.completed_at && (
                        <div>
                          <h3 className="text-sm font-semibold text-gray-700 mb-1">Completed</h3>
                          <p className="text-sm text-gray-600">
                            {new Date(selectedGoal.completed_at).toLocaleDateString()}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Milestones Tab */}
              {activeTab === 'milestones' && (
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold mb-4">Achievements</h2>
                  {milestones.length === 0 ? (
                    <div className="text-center py-12">
                      <Award className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-600">No milestones yet. Keep working towards your goals!</p>
                    </div>
                  ) : (
                    milestones.map(milestone => (
                      <div
                        key={milestone.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => setSelectedMilestone(milestone)}
                      >
                        <div className="flex items-start gap-3">
                          <Award className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-1" />
                          <div className="flex-1">
                            <h3 className="font-semibold text-gray-900 mb-1">{milestone.title}</h3>
                            <p className="text-sm text-gray-600 mb-2 line-clamp-2">{milestone.description}</p>
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <Clock className="w-4 h-4" />
                              {new Date(milestone.achieved_at).toLocaleDateString()}
                              <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                                {milestone.impact} impact
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Milestone Detail Modal */}
              {selectedMilestone && (
                <div
                  className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto"
                  onClick={() => setSelectedMilestone(null)}
                >
                  <div
                    className="bg-white rounded-lg p-6 max-w-3xl w-full my-8"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-6">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Award className="w-8 h-8 text-yellow-500" />
                          <h2 className="text-2xl font-bold text-gray-900">{selectedMilestone.title}</h2>
                        </div>
                        <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded text-sm font-medium">
                          {selectedMilestone.impact} impact
                        </span>
                      </div>
                      <button
                        onClick={() => setSelectedMilestone(null)}
                        className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
                      >
                        ×
                      </button>
                    </div>

                    {/* Description */}
                    <div className="mb-6">
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">Achievement</h3>
                      <div className="text-gray-600 whitespace-pre-wrap">
                        {formatDescription(selectedMilestone.description)}
                      </div>
                    </div>

                    {/* Achieved Date */}
                    <div className="mb-6">
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">Achieved On</h3>
                      <div className="flex items-center gap-2 text-gray-600">
                        <Clock className="w-5 h-5" />
                        <span>{new Date(selectedMilestone.achieved_at).toLocaleDateString('en-US', {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}</span>
                      </div>
                    </div>

                    {/* Category if available */}
                    {selectedMilestone.category && (
                      <div className="mb-6">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">Category</h3>
                        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                          {selectedMilestone.category}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Skills Tab */}
              {activeTab === 'skills' && (
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold mb-4">Skills Acquired</h2>
                  {skills.length === 0 ? (
                    <div className="text-center py-12">
                      <TrendingUp className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-600">No skills tracked yet.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {skills.map((skill, idx) => (
                        <div
                          key={idx}
                          className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
                          onClick={() => setSelectedSkill(skill)}
                        >
                          <h3 className="font-semibold text-gray-900 mb-2">{skill.name}</h3>
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                              {skill.category}
                            </span>
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                              {skill.proficiency}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Skill Detail Modal */}
              {selectedSkill && (
                <div
                  className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto"
                  onClick={() => setSelectedSkill(null)}
                >
                  <div
                    className="bg-white rounded-lg p-6 max-w-3xl w-full my-8"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-6">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <TrendingUp className="w-8 h-8 text-green-500" />
                          <h2 className="text-2xl font-bold text-gray-900">{selectedSkill.name}</h2>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm font-medium">
                            {selectedSkill.category}
                          </span>
                          <span className="px-3 py-1 bg-green-100 text-green-700 rounded text-sm font-medium">
                            {selectedSkill.proficiency}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => setSelectedSkill(null)}
                        className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
                      >
                        ×
                      </button>
                    </div>

                    {/* Description if available */}
                    {selectedSkill.description && (
                      <div className="mb-6">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">About This Skill</h3>
                        <div className="text-gray-600 whitespace-pre-wrap">
                          {formatDescription(selectedSkill.description)}
                        </div>
                      </div>
                    )}

                    {/* Acquired Date if available */}
                    {selectedSkill.acquired_at && (
                      <div className="mb-6">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">Acquired On</h3>
                        <div className="flex items-center gap-2 text-gray-600">
                          <Clock className="w-5 h-5" />
                          <span>{new Date(selectedSkill.acquired_at).toLocaleDateString('en-US', {
                            weekday: 'long',
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })}</span>
                        </div>
                      </div>
                    )}

                    {/* Projects or Related Goals if available */}
                    {selectedSkill.related_projects && selectedSkill.related_projects.length > 0 && (
                      <div className="mb-6">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">Related Projects</h3>
                        <div className="flex flex-wrap gap-2">
                          {selectedSkill.related_projects.map((project: string, idx: number) => (
                            <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                              {project}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Learning Tab */}
              {activeTab === 'learning' && (
                <div className="text-center py-12">
                  <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Learning Analytics</h3>
                  <p className="text-gray-600">Coming soon: Charts, trends, and detailed analytics</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Add Goal Modal - Simplified */}
      {showAddGoal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Add New Goal</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                createGoal({
                  title: formData.get('title') as string,
                  description: formData.get('description') as string,
                  category: formData.get('category') as string,
                });
              }}
            >
              <div className="space-y-4">
                <input
                  name="title"
                  type="text"
                  placeholder="Goal title"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
                <textarea
                  name="description"
                  placeholder="Description"
                  rows={3}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
                <select
                  name="category"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="learning">Learning</option>
                  <option value="fitness">Fitness</option>
                  <option value="career">Career</option>
                  <option value="personal">Personal</option>
                  <option value="financial">Financial</option>
                </select>
              </div>
              <div className="flex gap-2 mt-6">
                <button
                  type="button"
                  onClick={() => setShowAddGoal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  Add Goal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
