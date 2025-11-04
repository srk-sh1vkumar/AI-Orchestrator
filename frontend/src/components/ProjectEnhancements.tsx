import React, { useState, useEffect } from 'react';
import {
  Code2,
  CheckCircle,
  Clock,
  AlertCircle,
  FileText,
  TrendingUp,
  Calendar,
  Zap,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { clsx } from 'clsx';
import axios from 'axios';

interface Enhancement {
  id: string;
  title: string;
  category: string;
  priority: string;
  status: string;
  estimated_hours: number;
  actual_hours?: number;
  completion_percentage: number;
  completion_date?: string;
  technical_breakdown?: {
    components?: string[];
    new_files?: number;
    modified_files?: number;
    new_files_count?: number;
    modified_files_count?: number;
    phases?: {
      [key: string]: {
        name: string;
        estimated_hours?: number;
        hours?: number;
        tasks?: string[];
        deliverables?: string[];
        success_criteria?: string[];
      };
    };
  };
  success_criteria?: string[];
  dependencies?: Array<string | { yaml_id?: string; note?: string }>;
}

interface Progress {
  completion_rate: string;
  complete?: number;
  in_progress?: number;
  design?: number;
  planned?: number;
  actual_total_hours?: number;
  estimated_total_hours?: number;
}

interface EnhancementsData {
  enhancements: Enhancement[];
  progress: Progress;
  metadata: {
    project_name?: string;
    version?: string;
    last_updated?: string;
  };
}

type ProjectId = 'ai-orchestrator' | 'ecommerce' | 'sre-analytics';

interface Project {
  id: ProjectId;
  name: string;
  description: string;
  status: string;
}

const PROJECTS: Project[] = [
  {
    id: 'ai-orchestrator',
    name: 'AI Orchestrator',
    description: 'Intelligent LLM orchestration with multi-provider routing',
    status: '35% Complete',
  },
  {
    id: 'ecommerce',
    name: 'E-Commerce Platform',
    description: 'Spring Boot microservices with enterprise monitoring',
    status: 'Production Ready',
  },
  {
    id: 'sre-analytics',
    name: 'SRE Analytics',
    description: 'Multi-source analytics with AI-powered insights',
    status: '38% Complete',
  },
];

export const ProjectEnhancements: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<ProjectId>('ai-orchestrator');
  const [data, setData] = useState<EnhancementsData | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedEnhancement, setSelectedEnhancement] = useState<Enhancement | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEnhancements();
  }, [selectedProject]);

  const fetchEnhancements = async () => {
    setLoading(true);
    try {
      if (selectedProject === 'ai-orchestrator') {
        const response = await axios.get('http://localhost:8000/api/enhancements');
        console.log('Fetched AI Orchestrator data, enhancement count:', response.data.enhancements?.length);
        if (response.data.enhancements?.length > 0) {
          const sample = response.data.enhancements[response.data.enhancements.length - 1];
          console.log('Sample enhancement (last):', sample.id, 'has phases:', !!(sample.technical_breakdown?.phases || sample.phases));
        }
        setData(response.data);
      } else if (selectedProject === 'ecommerce') {
        const response = await axios.get('http://localhost:8000/api/ecommerce/enhancements');
        console.log('Fetched E-commerce data, enhancement count:', response.data.enhancements?.length);
        setData(response.data);
      } else if (selectedProject === 'sre-analytics') {
        const response = await axios.get('http://localhost:8000/api/sre-analytics/enhancements');
        console.log('Fetched SRE Analytics data, enhancement count:', response.data.enhancements?.length);
        if (response.data.enhancements?.length > 0) {
          const sample = response.data.enhancements[response.data.enhancements.length - 1];
          console.log('Sample enhancement (last):', sample.id, 'has phases:', !!(sample.technical_breakdown?.phases || sample.phases));
        }
        setData(response.data);
      } else {
        setData(null);
      }
    } catch (error) {
      console.error('Failed to fetch enhancements:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      Complete: 'bg-green-100 text-green-700 border-green-300',
      Completed: 'bg-green-100 text-green-700 border-green-300',
      'In Progress': 'bg-blue-100 text-blue-700 border-blue-300',
      Design: 'bg-yellow-100 text-yellow-700 border-yellow-300',
      Planned: 'bg-gray-100 text-gray-700 border-gray-300',
    };
    return colors[status] || 'bg-gray-100 text-gray-700 border-gray-300';
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      High: 'text-red-600',
      Medium: 'text-yellow-600',
      Low: 'text-gray-600',
    };
    return colors[priority] || 'text-gray-600';
  };

  const getStatusIcon = (status: string) => {
    if (status === 'Complete' || status === 'Completed') {
      return <CheckCircle className="w-5 h-5 text-green-600" />;
    } else if (status === 'In Progress') {
      return <Clock className="w-5 h-5 text-blue-600 animate-pulse" />;
    } else if (status === 'Design') {
      return <FileText className="w-5 h-5 text-yellow-600" />;
    } else {
      return <AlertCircle className="w-5 h-5 text-gray-600" />;
    }
  };

  const filteredEnhancements = data?.enhancements.filter(enh =>
    selectedStatus === 'all' || enh.status === selectedStatus
  ) || [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading enhancements...</p>
        </div>
      </div>
    );
  }

  const currentProject = PROJECTS.find(p => p.id === selectedProject);

  return (
    <div className="space-y-6">
      {/* Project Tabs */}
      <div className="bg-white rounded-lg border border-gray-200 p-1">
        <div className="grid grid-cols-3 gap-1">
          {PROJECTS.map(project => (
            <button
              key={project.id}
              onClick={() => setSelectedProject(project.id)}
              className={clsx(
                'px-4 py-3 rounded-lg font-medium transition-all text-left',
                selectedProject === project.id
                  ? 'bg-primary-600 text-white shadow-md'
                  : 'text-gray-700 hover:bg-gray-100'
              )}
            >
              <div className="font-semibold">{project.name}</div>
              <div className={clsx(
                'text-xs mt-1',
                selectedProject === project.id ? 'text-primary-100' : 'text-gray-500'
              )}>
                {project.description}
              </div>
              <div className={clsx(
                'text-xs mt-1 font-medium',
                selectedProject === project.id ? 'text-white' : 'text-gray-600'
              )}>
                {project.status}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Project Header */}
      {currentProject && (
        <div className="bg-gradient-to-r from-primary-50 to-primary-100 rounded-lg p-4 border border-primary-200">
          <h2 className="text-2xl font-bold text-primary-900">{currentProject.name}</h2>
          <p className="text-primary-700 mt-1">{currentProject.description}</p>
          <div className="flex items-center gap-2 mt-2">
            <span className="px-3 py-1 bg-white text-primary-700 rounded-full text-sm font-medium">
              {currentProject.status}
            </span>
          </div>
        </div>
      )}

      {/* Content based on selected project */}
      {data ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-green-900">
                {data?.progress?.complete || 0}
              </div>
              <div className="text-sm text-green-700">Completed</div>
            </div>
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <div className="mt-2 text-xs text-green-700">
            {data?.progress?.completion_rate || '0%'} complete
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-blue-900">
                {data?.progress?.in_progress || 0}
              </div>
              <div className="text-sm text-blue-700">In Progress</div>
            </div>
            <Clock className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg p-4 border border-yellow-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-yellow-900">
                {data?.progress?.design || 0}
              </div>
              <div className="text-sm text-yellow-700">Design Phase</div>
            </div>
            <FileText className="w-8 h-8 text-yellow-600" />
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-purple-900">
                {data?.progress?.actual_total_hours || 0}h
              </div>
              <div className="text-sm text-purple-700">Total Hours</div>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="bg-white rounded-lg border border-gray-200 p-1 flex gap-1">
        {['all', 'Complete', 'In Progress', 'Design', 'Planned'].map(status => (
          <button
            key={status}
            onClick={() => setSelectedStatus(status)}
            className={clsx(
              'px-4 py-2 rounded font-medium transition-colors',
              selectedStatus === status
                ? 'bg-primary-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            )}
          >
            {status === 'all' ? 'All' : status}
          </button>
        ))}
      </div>

      {/* Enhancements List */}
      <div className="grid grid-cols-1 gap-4">
        {filteredEnhancements.map(enh => (
          <div
            key={enh.id}
            className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => {
              console.log('=== CARD CLICKED ===');
              console.log('Enhancement:', enh);
              console.log('Has phases:', !!(enh.technical_breakdown?.phases || (enh as any).phases));
              setSelectedEnhancement(enh);
            }}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start gap-3 flex-1">
                {getStatusIcon(enh.status)}
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-mono text-gray-500">#{enh.id}</span>
                    <h3 className="font-semibold text-gray-900">{enh.title}</h3>
                  </div>
                  <div className="flex gap-2 mb-2">
                    <span
                      className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium border',
                        getStatusColor(enh.status)
                      )}
                    >
                      {enh.status}
                    </span>
                    <span className={clsx('px-2 py-0.5 rounded text-xs font-medium', getPriorityColor(enh.priority))}>
                      {enh.priority} Priority
                    </span>
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-medium">
                      {enh.category}
                    </span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">{enh.completion_percentage}%</div>
                <div className="text-xs text-gray-500">Complete</div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-3">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={clsx(
                    'h-2 rounded-full transition-all',
                    enh.completion_percentage === 100 ? 'bg-green-600' : 'bg-primary-600'
                  )}
                  style={{ width: `${enh.completion_percentage}%` }}
                ></div>
              </div>
            </div>

            {/* Time & Date */}
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                <span>
                  {enh.actual_hours || 0} / {enh.estimated_hours}h
                </span>
              </div>
              {enh.completion_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>Completed: {enh.completion_date}</span>
                </div>
              )}
              {enh.technical_breakdown && (
                <div className="flex items-center gap-1">
                  <Code2 className="w-4 h-4" />
                  <span>
                    {enh.technical_breakdown.new_files || 0} new, {enh.technical_breakdown.modified_files || 0} modified
                  </span>
                </div>
              )}
            </div>

            {/* Success Criteria Preview (if completed) */}
            {enh.status === 'Complete' && enh.success_criteria && enh.success_criteria.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="text-xs text-gray-500 mb-1">Success Criteria:</div>
                <div className="text-sm text-gray-700">
                  {enh.success_criteria[0]}
                  {enh.success_criteria.length > 1 && (
                    <span className="text-gray-500 ml-1">+{enh.success_criteria.length - 1} more</span>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredEnhancements.length === 0 && (
        <div className="text-center py-12">
          <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-600">No enhancements found for this status</p>
        </div>
      )}

      {/* Detail Modal */}
      {selectedEnhancement && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto"
          onClick={() => setSelectedEnhancement(null)}
        >
          <div
            className="bg-white rounded-lg p-6 max-w-4xl w-full my-8"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-mono text-gray-500">#{selectedEnhancement?.id || 'N/A'}</span>
                    <h2 className="text-2xl font-bold text-gray-900">{selectedEnhancement?.title || 'Untitled'}</h2>
                </div>
                <div className="flex gap-2 mb-2">
                  <span className={clsx('px-2 py-1 rounded text-xs font-medium border', getStatusColor(selectedEnhancement.status))}>
                    {selectedEnhancement.status}
                  </span>
                  <span className={clsx('px-2 py-1 rounded text-xs font-medium', getPriorityColor(selectedEnhancement.priority))}>
                    {selectedEnhancement.priority} Priority
                  </span>
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                    {selectedEnhancement.category}
                  </span>
                </div>
                {(selectedEnhancement as any).impact && (
                  <p className="text-sm text-gray-600 italic">{(selectedEnhancement as any).impact}</p>
                )}
              </div>
              <button
                onClick={() => setSelectedEnhancement(null)}
                className="text-gray-400 hover:text-gray-600 ml-4"
              >
                ✕
              </button>
            </div>

            {/* Scrollable Content */}
            <div className="max-h-[70vh] overflow-y-auto space-y-6 pr-2">
              {/* Progress */}
              <div>
                <div className="text-sm font-medium text-gray-700 mb-1">Progress</div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-primary-600 h-3 rounded-full"
                    style={{ width: `${selectedEnhancement.completion_percentage}%` }}
                  ></div>
                </div>
                <div className="text-sm text-gray-600 mt-1">{selectedEnhancement.completion_percentage}% Complete</div>
              </div>

              {/* Hours */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-1">Estimated Hours</div>
                  <div className="text-lg font-semibold text-gray-900">{selectedEnhancement.estimated_hours}h</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-1">Actual Hours</div>
                  <div className="text-lg font-semibold text-gray-900">{selectedEnhancement.actual_hours || 0}h</div>
                </div>
              </div>

              {/* Technical Summary */}
              {(selectedEnhancement as any).technical_summary && (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">Technical Summary</div>
                  <div className="bg-gray-50 rounded p-4 text-sm text-gray-700 whitespace-pre-wrap">
                    {(selectedEnhancement as any).technical_summary}
                  </div>
                </div>
              )}

              {/* Implementation Phases */}
              {(() => {
                const phases = selectedEnhancement.technical_breakdown?.phases || (selectedEnhancement as any).phases;
                console.log('=== PHASE DEBUG ===');
                console.log('Selected Enhancement ID:', selectedEnhancement.id);
                console.log('Has technical_breakdown:', !!selectedEnhancement.technical_breakdown);
                console.log('Has phases:', !!phases);
                if (phases) {
                  console.log('Phase keys:', Object.keys(phases));
                  console.log('First phase:', Object.values(phases)[0]);
                } else {
                  console.log('NO PHASES FOUND! Enhancement:', selectedEnhancement);
                }
                return phases;
              })() ? (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-3 bg-green-100 p-2 rounded">
                    ✅ Implementation Phases ({Object.keys(selectedEnhancement.technical_breakdown?.phases || (selectedEnhancement as any).phases).length} phases found)
                  </div>
                  <div className="space-y-4">
                    {Object.entries(
                      selectedEnhancement.technical_breakdown?.phases || (selectedEnhancement as any).phases
                    ).map(([phaseKey, phase]: [string, any]) => (
                      <div key={phaseKey} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-semibold text-gray-900">{phase.name}</h4>
                          {(phase.estimated_hours || phase.hours) && (
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                              {phase.estimated_hours || phase.hours}h
                            </span>
                          )}
                        </div>

                        {phase.tasks && phase.tasks.length > 0 && (
                          <div className="mb-3">
                            <div className="text-xs font-medium text-gray-600 mb-1">Tasks:</div>
                            <ul className="space-y-1">
                              {phase.tasks.map((task: string, idx: number) => (
                                <li key={idx} className="text-xs text-gray-700 flex items-start gap-2">
                                  <span className="text-primary-600 mt-0.5">•</span>
                                  <span>{task}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {phase.deliverables && phase.deliverables.length > 0 && (
                          <div className="mb-3">
                            <div className="text-xs font-medium text-gray-600 mb-1">Deliverables:</div>
                            <div className="flex flex-wrap gap-1">
                              {phase.deliverables.map((deliverable: string, idx: number) => (
                                <span key={idx} className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded">
                                  {deliverable}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {phase.success_criteria && phase.success_criteria.length > 0 && (
                          <div>
                            <div className="text-xs font-medium text-gray-600 mb-1">Success Criteria:</div>
                            <ul className="space-y-1">
                              {phase.success_criteria.map((criterion: string, idx: number) => (
                                <li key={idx} className="text-xs text-gray-700 flex items-start gap-2">
                                  <span className="text-green-600 mt-0.5">✓</span>
                                  <span>{criterion}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="bg-red-50 border border-red-200 rounded p-4">
                  <p className="text-sm text-red-700">⚠️ No implementation phases available for this enhancement</p>
                </div>
              )}

              {/* Success Criteria (top-level) */}
              {selectedEnhancement.success_criteria && selectedEnhancement.success_criteria.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">Overall Success Criteria</div>
                  <ul className="space-y-1 bg-green-50 rounded p-3">
                    {selectedEnhancement.success_criteria.map((criterion, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                        <span className="text-green-600 mt-0.5">✓</span>
                        <span>{criterion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Dependencies */}
              {selectedEnhancement.dependencies && selectedEnhancement.dependencies.length > 0 && (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">Dependencies</div>
                  <div className="space-y-2">
                    {selectedEnhancement.dependencies.map((dep: any, idx) => (
                      <div key={idx} className="flex items-start gap-2 bg-yellow-50 border border-yellow-200 rounded p-2">
                        <span className="text-xs font-mono text-yellow-700">
                          #{typeof dep === 'object' ? (dep.yaml_id || 'N/A') : dep}
                        </span>
                        {typeof dep === 'object' && dep.note && (
                          <span className="text-xs text-gray-600">— {dep.note}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Technical Breakdown - Files */}
              {selectedEnhancement.technical_breakdown && (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">Technical Breakdown</div>
                  <div className="bg-gray-50 rounded p-3 space-y-2 text-sm">
                    {selectedEnhancement.technical_breakdown.new_files_count !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">New Files:</span>
                        <span className="font-semibold text-gray-900">{selectedEnhancement.technical_breakdown.new_files_count}</span>
                      </div>
                    )}
                    {selectedEnhancement.technical_breakdown.modified_files_count !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Modified Files:</span>
                        <span className="font-semibold text-gray-900">{selectedEnhancement.technical_breakdown.modified_files_count}</span>
                      </div>
                    )}
                    {selectedEnhancement.technical_breakdown.new_files !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">New Files:</span>
                        <span className="font-semibold text-gray-900">{selectedEnhancement.technical_breakdown.new_files}</span>
                      </div>
                    )}
                    {selectedEnhancement.technical_breakdown.modified_files !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Modified Files:</span>
                        <span className="font-semibold text-gray-900">{selectedEnhancement.technical_breakdown.modified_files}</span>
                      </div>
                    )}
                    {selectedEnhancement.technical_breakdown.components && (
                      <div>
                        <span className="text-gray-600">Components: </span>
                        <span className="text-gray-900">
                          {Array.isArray(selectedEnhancement.technical_breakdown.components)
                            ? selectedEnhancement.technical_breakdown.components.join(', ')
                            : typeof selectedEnhancement.technical_breakdown.components === 'object'
                            ? JSON.stringify(selectedEnhancement.technical_breakdown.components)
                            : String(selectedEnhancement.technical_breakdown.components)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Completion Date */}
              {selectedEnhancement.completion_date && (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-1">Completion Date</div>
                  <div className="text-gray-900">{selectedEnhancement.completion_date}</div>
                </div>
              )}
            </div>

            {/* Close Button */}
            <div className="mt-6 pt-4 border-t border-gray-200">
              <button
                onClick={() => setSelectedEnhancement(null)}
                className="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
        </>
      ) : null}

      {/* No Data Placeholder */}
      {!data && !loading && (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <Code2 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            No Enhancement Data Available
          </h3>
          <p className="text-gray-600 max-w-md mx-auto">
            Unable to load enhancement tracking data for this project.
          </p>
        </div>
      )}
    </div>
  );
};
