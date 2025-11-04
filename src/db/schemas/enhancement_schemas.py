"""
Pydantic schemas for enhancement tracking database models.

These schemas define the structure and validation rules for projects,
enhancements, dependencies, and progress tracking.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Annotated
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2."""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(cls.validate),
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId")
            return ObjectId(v)
        raise ValueError("Invalid ObjectId type")


class Project(BaseModel):
    """Project model."""

    id: Optional[PyObjectId] = Field(None, alias="_id")
    project_name: str = Field(..., min_length=1, max_length=200)
    project_tag: str = Field(..., min_length=2, max_length=50, pattern="^[a-z][a-z0-9_]*$")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    owner: str = Field(..., min_length=1)
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB document."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        return data

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "Project":
        """Create from MongoDB document."""
        if not data:
            return None
        return cls(**data)


class Enhancement(BaseModel):
    """Enhancement model."""

    id: Optional[PyObjectId] = Field(None, alias="_id")
    project_id: PyObjectId
    enhancement_number: str = Field(..., pattern=r"^\d{3}$")
    db_reference: Optional[str] = None
    title: str = Field(..., min_length=5, max_length=200)
    category: str = Field(..., min_length=1)
    priority: str = Field(..., pattern="^(Critical|High|Medium|Low)$")
    status: str = Field(..., pattern="^(Planned|Ideation|In Progress|Complete|Completed|Blocked|Cancelled)$")
    phase: int = Field(..., ge=1, le=5)
    impact: Optional[str] = None
    related_agent: Optional[str] = None
    estimated_hours: float = Field(..., ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    completion_percentage: int = Field(0, ge=0, le=100)
    completion_date: Optional[datetime] = None
    completion_report: Optional[str] = None
    technical_summary: Optional[str] = None
    success_criteria: List[str] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)
    completion_notes: List[str] = Field(default_factory=list)
    implementation_notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )

    @field_validator('status')
    @classmethod
    def normalize_status(cls, v):
        """Normalize status values (handle both 'Complete' and 'Completed')."""
        if v == "Completed":
            return "Complete"
        return v

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB document."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        return data

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "Enhancement":
        """Create from MongoDB document."""
        if not data:
            return None
        return cls(**data)


class Dependency(BaseModel):
    """Dependency model."""

    id: Optional[PyObjectId] = Field(None, alias="_id")
    enhancement_id: PyObjectId
    depends_on_id: Optional[PyObjectId] = None
    yaml_id: Optional[str] = None
    dependency_type: str = Field(..., pattern="^(required|optional|blocking)$")
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB document."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        return data

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "Dependency":
        """Create from MongoDB document."""
        if not data:
            return None
        return cls(**data)


class CompletionReport(BaseModel):
    """Completion report model."""

    id: Optional[PyObjectId] = Field(None, alias="_id")
    enhancement_id: PyObjectId
    report_path: str = Field(..., min_length=1)
    report_content: Optional[str] = None
    completion_date: datetime
    metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB document."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        return data

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "CompletionReport":
        """Create from MongoDB document."""
        if not data:
            return None
        return cls(**data)


class VelocityMetrics(BaseModel):
    """Velocity metrics sub-model."""

    enhancements_per_week: float = 0.0
    hours_per_week: float = 0.0
    avg_completion_time_days: float = 0.0


class ProgressSnapshot(BaseModel):
    """Progress snapshot model."""

    id: Optional[PyObjectId] = Field(None, alias="_id")
    project_id: PyObjectId
    snapshot_date: datetime
    total_enhancements: int = Field(..., ge=0)
    completed: int = Field(..., ge=0)
    in_progress: int = Field(..., ge=0)
    planned: int = Field(..., ge=0)
    blocked: int = Field(0, ge=0)
    completion_percentage: float = Field(..., ge=0, le=100)
    estimated_total_hours: float = Field(0, ge=0)
    actual_total_hours: float = Field(0, ge=0)
    velocity: Optional[VelocityMetrics] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda v: v.isoformat()}
    )

    def to_mongo(self) -> Dict[str, Any]:
        """Convert to MongoDB document."""
        data = self.model_dump(by_alias=True, exclude_none=True)
        if "_id" in data and data["_id"] is None:
            del data["_id"]
        if self.velocity:
            data["velocity"] = self.velocity.model_dump()
        return data

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]) -> "ProgressSnapshot":
        """Create from MongoDB document."""
        if not data:
            return None
        if "velocity" in data and data["velocity"]:
            data["velocity"] = VelocityMetrics(**data["velocity"])
        return cls(**data)


# Response models for API
class ProjectResponse(BaseModel):
    """Project response with summary statistics."""

    project_id: str
    project_name: str
    project_tag: str
    version: str
    owner: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    total_enhancements: int = 0
    completed: int = 0
    in_progress: int = 0
    planned: int = 0
    completion_percentage: float = 0.0
    created_at: datetime
    updated_at: datetime


class EnhancementResponse(BaseModel):
    """Enhancement response with dependency info."""

    enhancement_id: str
    enhancement_number: str
    title: str
    category: str
    priority: str
    status: str
    phase: int
    completion_percentage: int
    estimated_hours: float
    actual_hours: Optional[float] = None
    completion_date: Optional[datetime] = None
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)


class ProgressResponse(BaseModel):
    """Progress response."""

    project_tag: str
    total_enhancements: int
    completed: int
    in_progress: int
    planned: int
    blocked: int
    completion_percentage: float
    estimated_total_hours: float
    actual_total_hours: float
    remaining_hours: float
    velocity: Optional[VelocityMetrics] = None
