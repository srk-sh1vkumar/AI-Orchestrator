"""Data models for the AI Orchestrator."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    CLAUDE_CODE = "claude_code"
    CHATGPT = "chatgpt"
    GEMINI = "gemini"
    CLAUDE = "claude"
    LOCAL = "local"
    MISTRAL = "mistral"  # Mistral 7B for general incident analysis
    LLAMA2 = "llama2"    # Llama2 7B for log analysis
    CODELLAMA = "codellama"  # CodeLlama 7B for code-related incident analysis


class TaskCategory(str, Enum):
    """Task categories for routing."""
    CODE_GENERATION = "code_generation"
    CODE_IMPLEMENTATION = "code_implementation"
    DEBUGGING = "debugging"
    DEPLOYMENT = "deployment"
    UI_GENERATION = "ui_generation"
    WORKFLOW_AUTOMATION = "workflow_automation"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    INCIDENT_ANALYSIS = "incident_analysis"
    LOG_ANALYSIS = "log_analysis"
    DOCUMENTATION = "documentation"
    TECHNICAL_ANALYSIS = "technical_analysis"
    GENERAL = "general"


class ToolType(str, Enum):
    """Available tool types."""
    GITHUB = "github"
    JENKINS = "jenkins"
    GITHUB_ACTIONS = "github_actions"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    GRAFANA = "grafana"
    PROMETHEUS = "prometheus"
    ELASTICSEARCH = "elasticsearch"
    SPLUNK = "splunk"
    CLOUDWATCH = "cloudwatch"
    FILE_SYSTEM = "file_system"
    TERMINAL = "terminal"
    CLAUDE_CODE_CLI = "claude_code_cli"


class ToolCall(BaseModel):
    """Represents a tool call to be executed."""
    tool_type: ToolType
    operation: str
    parameters: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class ToolResult(BaseModel):
    """Result from a tool execution."""
    tool_type: ToolType
    operation: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    """Chat message."""
    role: str  # "user", "assistant", "system"
    content: str
    provider: Optional[LLMProvider] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Request for chat completion."""
    message: str
    context: Optional[Dict[str, Any]] = None
    explicit_provider: Optional[LLMProvider] = None
    session_id: Optional[str] = None
    enable_tools: bool = False  # Temporarily disabled until tool definitions are fixed
    enable_collaboration: bool = True


class RoutingDecision(BaseModel):
    """Decision made by the routing engine."""
    provider: LLMProvider
    category: TaskCategory
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    fallback_providers: List[LLMProvider] = Field(default_factory=list)
    requires_collaboration: bool = False
    collaboration_plan: Optional[List[LLMProvider]] = None


class LLMResponse(BaseModel):
    """Response from an LLM provider."""
    provider: LLMProvider
    content: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tokens_used: Optional[int] = None
    execution_time: float
    metadata: Optional[Dict[str, Any]] = None


class StreamChunk(BaseModel):
    """Individual chunk from streaming response."""
    provider: LLMProvider
    content: str  # Delta content (incremental text)
    is_final: bool = False
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FallbackEvent(BaseModel):
    """Event logged when a fallback occurs."""
    from_provider: LLMProvider
    to_provider: LLMProvider
    reason: str
    category: TaskCategory
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QualityCheck(BaseModel):
    """Quality check result for an LLM response."""
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response from the orchestrator."""
    message: str
    provider: LLMProvider
    routing_decision: RoutingDecision
    tool_results: List[ToolResult] = Field(default_factory=list)
    fallback_events: List[FallbackEvent] = Field(default_factory=list)
    quality_check: Optional[QualityCheck] = None
    collaboration_steps: Optional[List[Dict[str, Any]]] = None
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionContext(BaseModel):
    """Session context for maintaining conversation state."""
    session_id: str
    messages: List[Message] = Field(default_factory=list)
    current_task: Optional[str] = None
    active_tools: List[ToolType] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class HealthStatus(BaseModel):
    """Health status of the orchestrator and providers."""
    status: str  # "healthy", "degraded", "unhealthy"
    providers: Dict[str, Dict[str, Any]]
    tools: Dict[str, bool]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
