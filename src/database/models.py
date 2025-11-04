"""Pydantic models for MongoDB documents."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, handler=None):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class EnhancementDocument(BaseModel):
    """Enhancement document model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    yaml_id: str
    project_tag: str
    title: str
    category: str
    priority: str  # "High", "Medium", "Low"
    status: str  # "Ideation", "Definition", "Design", etc.

    long_description: Optional[str] = None
    technical_breakdown: Optional[Dict[str, Any]] = None
    success_metrics: Optional[Dict[str, Any]] = None
    impact: Optional[str] = None

    dependencies: List[str] = Field(default_factory=list)
    related_agent: Optional[str] = None
    blocks: List[str] = Field(default_factory=list)
    blocked_by: List[str] = Field(default_factory=list)

    log_history: List[Dict[str, Any]] = Field(default_factory=list)
    code_references: Optional[Dict[str, Any]] = None

    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    completion_percentage: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class ConversationMetrics(BaseModel):
    """Conversation metrics sub-document."""

    message_count: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    execution_time_ms: int = 0


class ConversationDocument(BaseModel):
    """Conversation document model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: Optional[str] = None
    title: Optional[str] = None
    provider_used: str
    routing_decision: Dict[str, Any]

    metrics: ConversationMetrics = Field(default_factory=ConversationMetrics)
    status: str = "active"  # "active", "archived", "deleted"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class MessageDocument(BaseModel):
    """Message document model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    conversation_id: PyObjectId
    role: str  # "user", "assistant", "system"
    content: str

    provider: Optional[str] = None
    model: Optional[str] = None

    token_count: Optional[int] = None
    cost_usd: Optional[float] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class ToolExecutionDocument(BaseModel):
    """Tool execution document model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    conversation_id: PyObjectId
    message_id: Optional[PyObjectId] = None

    tool_type: str
    operation: str
    success: bool

    result: Optional[Any] = None
    error: Optional[str] = None

    execution_time_ms: int

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class ContextEventDocument(BaseModel):
    """Context event document model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    conversation_id: PyObjectId

    event_type: str  # "check", "truncation", "overflow", "warning"
    provider: str

    token_count: int
    limit: int
    utilization_percent: float

    truncation_strategy: Optional[str] = None
    messages_removed: Optional[int] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class ProviderMetricDocument(BaseModel):
    """Provider metric document model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    provider: str
    metric_type: str  # "request", "success", "failure", "latency", "tokens", "cost"

    value: float
    unit: Optional[str] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class CostRecordDocument(BaseModel):
    """Detailed cost tracking document for each request/conversation."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    conversation_id: Optional[PyObjectId] = None
    message_id: Optional[PyObjectId] = None

    # User and project context
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None

    # Provider and model information
    provider: str
    model: str

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Cost breakdown (in USD)
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0

    # Additional metadata
    category: Optional[str] = None  # TaskCategory
    request_type: Optional[str] = None  # "chat", "tool_execution", "collaboration"
    success: bool = True

    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class BudgetDocument(BaseModel):
    """Budget limits and tracking document."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    # Budget identification
    budget_name: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None

    # Budget scope (can be provider-specific or global)
    provider: Optional[str] = None  # None means all providers

    # Budget limits (in USD)
    daily_limit: Optional[float] = None
    weekly_limit: Optional[float] = None
    monthly_limit: Optional[float] = None

    # Current usage (in USD)
    daily_spent: float = 0.0
    weekly_spent: float = 0.0
    monthly_spent: float = 0.0

    # Alert thresholds (percentage of limit)
    warning_threshold: float = 0.8  # 80% by default
    critical_threshold: float = 0.95  # 95% by default

    # Alert status
    warning_triggered: bool = False
    critical_triggered: bool = False
    budget_exceeded: bool = False

    # Alert channels
    alert_email: Optional[str] = None
    alert_webhook: Optional[str] = None

    # Status
    is_active: bool = True

    # Timestamps
    period_start: datetime = Field(default_factory=datetime.utcnow)
    last_reset: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class BudgetAlertDocument(BaseModel):
    """Budget alert history document."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    budget_id: PyObjectId

    # Alert details
    alert_type: str  # "warning", "critical", "exceeded"
    threshold_type: str  # "daily", "weekly", "monthly"

    # Budget state at time of alert
    limit_usd: float
    spent_usd: float
    utilization_percent: float

    # Provider context
    provider: Optional[str] = None

    # Alert delivery
    notification_sent: bool = False
    notification_channel: Optional[str] = None  # "email", "webhook", "log"
    notification_error: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
