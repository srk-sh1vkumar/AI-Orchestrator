export type LLMProvider = 'claude_code' | 'chatgpt' | 'gemini' | 'claude' | 'local';

export type TaskCategory =
  | 'code_generation'
  | 'code_implementation'
  | 'debugging'
  | 'deployment'
  | 'ui_generation'
  | 'workflow_automation'
  | 'prompt_optimization'
  | 'incident_analysis'
  | 'log_analysis'
  | 'documentation'
  | 'technical_analysis'
  | 'general';

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  provider?: LLMProvider;
  timestamp: string;
}

export interface ToolResult {
  tool_type: string;
  operation: string;
  success: boolean;
  result?: any;
  error?: string;
  execution_time: number;
  timestamp: string;
}

export interface FallbackEvent {
  from_provider: LLMProvider;
  to_provider: LLMProvider;
  reason: string;
  category: TaskCategory;
  timestamp: string;
}

export interface QualityCheck {
  passed: boolean;
  score: number;
  issues: string[];
  metadata?: Record<string, any>;
}

export interface RoutingDecision {
  provider: LLMProvider;
  category: TaskCategory;
  confidence: number;
  reasoning: string;
  fallback_providers: LLMProvider[];
  requires_collaboration: boolean;
  collaboration_plan?: LLMProvider[];
}

export interface CollaborationStep {
  step: number;
  provider: string;
  response: string;
  tool_calls: number;
  tool_results: number;
  execution_time: number;
}

export interface ChatResponse {
  message: string;
  provider: LLMProvider;
  routing_decision: RoutingDecision;
  tool_results: ToolResult[];
  fallback_events: FallbackEvent[];
  quality_check?: QualityCheck;
  collaboration_steps?: CollaborationStep[];
  execution_time: number;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  context?: Record<string, any>;
  explicit_provider?: LLMProvider;
  session_id?: string;
  enable_tools?: boolean;
  enable_collaboration?: boolean;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  providers: Record<string, boolean>;
  tools: Record<string, boolean>;
  timestamp: string;
}

export interface ProviderInfo {
  configured: boolean;
  role: string;
  model?: string;
}

export interface ProvidersResponse {
  providers: Record<string, ProviderInfo>;
}
