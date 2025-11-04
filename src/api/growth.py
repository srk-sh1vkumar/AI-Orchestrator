"""Growth tracking API endpoints for self-development integration."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os
from pathlib import Path
from src.core.session_tracker import get_session_tracker

router = APIRouter(prefix="/api/growth", tags=["growth"])

# Data directory for growth artifacts
GROWTH_DATA_DIR = Path("growth_data")
GROWTH_DATA_DIR.mkdir(exist_ok=True)


# Pydantic Models
class Reflection(BaseModel):
    """Weekly reflection entry."""
    id: Optional[str] = None
    integration_tag: str = Field(..., description="Tag linking to a goal (e.g., ai_systems_design)")
    week_of: str = Field(..., description="Week start date (YYYY-MM-DD)")
    learning_hours: float
    topics: List[str]
    goal_title: str
    progress_delta: int = Field(..., description="Progress change this week (%)")
    accomplishments: List[str]
    blockers: List[str] = Field(default_factory=list)
    insights: str
    next_week_focus: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectArtifact(BaseModel):
    """Project artifact or deliverable."""
    id: Optional[str] = None
    integration_tag: str
    title: str
    description: str
    artifact_type: str = Field(..., description="Type: code, documentation, design, etc.")
    url: Optional[str] = None
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PerformanceMetric(BaseModel):
    """Performance metric entry."""
    id: Optional[str] = None
    integration_tag: str
    metric_name: str
    metric_value: float
    unit: str
    context: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LeadershipArtifact(BaseModel):
    """Leadership development artifact."""
    id: Optional[str] = None
    title: str
    artifact_type: str = Field(..., description="presentation, memo, framework, feedback")
    description: str
    key_learnings: List[str]
    impact: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ArchitectureDecision(BaseModel):
    """Architecture decision record."""
    id: Optional[str] = None
    title: str
    status: str = Field(..., description="proposed, accepted, deprecated, superseded")
    context: str
    decision: str
    consequences: str
    alternatives: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Helper functions
def load_json_data(filename: str) -> List[Dict]:
    """Load JSON data from growth directory."""
    file_path = GROWTH_DATA_DIR / f"{filename}.json"
    if not file_path.exists():
        return []
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json_data(filename: str, data: List[Dict]):
    """Save JSON data to growth directory."""
    file_path = GROWTH_DATA_DIR / f"{filename}.json"
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def generate_id(prefix: str) -> str:
    """Generate unique ID."""
    import time
    return f"{prefix}_{int(time.time() * 1000)}"


# Reflection Endpoints
@router.post("/reflections", response_model=Reflection)
async def create_reflection(reflection: Reflection):
    """Create a new weekly reflection entry."""
    reflections = load_json_data("reflections")

    reflection.id = generate_id("refl")
    reflections.append(reflection.dict())
    save_json_data("reflections", reflections)

    return reflection


@router.get("/reflections", response_model=List[Reflection])
async def get_reflections(
    integration_tag: Optional[str] = None,
    limit: int = 50
):
    """Get reflection entries, optionally filtered by integration tag."""
    reflections = load_json_data("reflections")

    if integration_tag:
        reflections = [r for r in reflections if r.get("integration_tag") == integration_tag]

    # Sort by created_at descending
    reflections = sorted(reflections, key=lambda x: x.get("created_at", ""), reverse=True)

    return reflections[:limit]


@router.get("/reflections/{reflection_id}", response_model=Reflection)
async def get_reflection(reflection_id: str):
    """Get a specific reflection by ID."""
    reflections = load_json_data("reflections")
    reflection = next((r for r in reflections if r.get("id") == reflection_id), None)

    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")

    return reflection


# Project Artifacts Endpoints
@router.post("/projects", response_model=ProjectArtifact)
async def create_project_artifact(artifact: ProjectArtifact):
    """Create a new project artifact."""
    artifacts = load_json_data("projects")

    artifact.id = generate_id("proj")
    artifacts.append(artifact.dict())
    save_json_data("projects", artifacts)

    return artifact


@router.get("/projects", response_model=List[ProjectArtifact])
async def get_project_artifacts(
    integration_tag: Optional[str] = None,
    artifact_type: Optional[str] = None
):
    """Get project artifacts, optionally filtered."""
    artifacts = load_json_data("projects")

    if integration_tag:
        artifacts = [a for a in artifacts if a.get("integration_tag") == integration_tag]

    if artifact_type:
        artifacts = [a for a in artifacts if a.get("artifact_type") == artifact_type]

    return artifacts


# Performance Metrics Endpoints
@router.post("/metrics", response_model=PerformanceMetric)
async def create_metric(metric: PerformanceMetric):
    """Record a performance metric."""
    metrics = load_json_data("metrics")

    metric.id = generate_id("metric")
    metrics.append(metric.dict())
    save_json_data("metrics", metrics)

    return metric


@router.get("/metrics", response_model=List[PerformanceMetric])
async def get_metrics(
    integration_tag: Optional[str] = None,
    metric_name: Optional[str] = None
):
    """Get performance metrics, optionally filtered."""
    metrics = load_json_data("metrics")

    if integration_tag:
        metrics = [m for m in metrics if m.get("integration_tag") == integration_tag]

    if metric_name:
        metrics = [m for m in metrics if m.get("metric_name") == metric_name]

    # Sort by timestamp descending
    metrics = sorted(metrics, key=lambda x: x.get("timestamp", ""), reverse=True)

    return metrics


# Leadership Endpoints
@router.post("/leadership", response_model=LeadershipArtifact)
async def create_leadership_artifact(artifact: LeadershipArtifact):
    """Create a new leadership artifact."""
    artifacts = load_json_data("leadership")

    artifact.id = generate_id("lead")
    artifacts.append(artifact.dict())
    save_json_data("leadership", artifacts)

    return artifact


@router.get("/leadership", response_model=List[LeadershipArtifact])
async def get_leadership_artifacts(artifact_type: Optional[str] = None):
    """Get leadership artifacts."""
    artifacts = load_json_data("leadership")

    if artifact_type:
        artifacts = [a for a in artifacts if a.get("artifact_type") == artifact_type]

    return artifacts


# Architecture Decisions Endpoints
@router.post("/architecture", response_model=ArchitectureDecision)
async def create_architecture_decision(decision: ArchitectureDecision):
    """Create a new architecture decision record (ADR)."""
    decisions = load_json_data("architecture")

    decision.id = generate_id("adr")
    decisions.append(decision.dict())
    save_json_data("architecture", decisions)

    return decision


@router.get("/architecture", response_model=List[ArchitectureDecision])
async def get_architecture_decisions(status: Optional[str] = None):
    """Get architecture decision records."""
    decisions = load_json_data("architecture")

    if status:
        decisions = [d for d in decisions if d.get("status") == status]

    # Sort by created_at descending
    decisions = sorted(decisions, key=lambda x: x.get("created_at", ""), reverse=True)

    return decisions


# Portfolio Endpoints (combines multiple artifact types)
@router.get("/portfolio")
async def get_portfolio():
    """Get comprehensive portfolio view."""
    return {
        "projects": load_json_data("projects"),
        "leadership": load_json_data("leadership"),
        "architecture": load_json_data("architecture"),
        "reflections_count": len(load_json_data("reflections")),
        "metrics_count": len(load_json_data("metrics")),
    }


# Summary/Dashboard Endpoints
@router.get("/summary")
async def get_growth_summary():
    """Get summary statistics across all growth data."""
    reflections = load_json_data("reflections")
    projects = load_json_data("projects")
    metrics = load_json_data("metrics")
    leadership = load_json_data("leadership")
    architecture = load_json_data("architecture")

    # Calculate total learning hours
    total_hours = sum(r.get("learning_hours", 0) for r in reflections)

    # Count by integration tag
    tag_counts = {}
    for r in reflections:
        tag = r.get("integration_tag", "unknown")
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {
        "total_reflections": len(reflections),
        "total_learning_hours": round(total_hours, 1),
        "total_projects": len(projects),
        "total_metrics": len(metrics),
        "total_leadership_artifacts": len(leadership),
        "total_architecture_decisions": len(architecture),
        "reflections_by_tag": tag_counts,
        "latest_reflection": reflections[-1] if reflections else None,
    }


@router.get("/reports/weekly")
async def get_weekly_report(week_of: str):
    """Get comprehensive weekly report."""
    reflections = load_json_data("reflections")
    metrics = load_json_data("metrics")

    # Filter by week
    week_reflections = [r for r in reflections if r.get("week_of") == week_of]

    # Get metrics for that week
    week_metrics = []
    for m in metrics:
        timestamp = m.get("timestamp", "")
        if timestamp.startswith(week_of):
            week_metrics.append(m)

    total_hours = sum(r.get("learning_hours", 0) for r in week_reflections)

    return {
        "week_of": week_of,
        "reflections": week_reflections,
        "total_learning_hours": round(total_hours, 1),
        "metrics": week_metrics,
        "goals_worked_on": list(set(r.get("goal_title") for r in week_reflections)),
    }


# ============================================================================
# Session Tracking Endpoints (Automatic Growth Reflection)
# ============================================================================


@router.post("/sessions/track-activity")
async def track_session_activity(
    activity_type: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """Track an activity in the current session.

    Args:
        activity_type: Type of activity (code, documentation, debugging, etc.)
        description: Description of the activity
        metadata: Additional metadata

    Returns:
        Success status
    """
    tracker = get_session_tracker()
    tracker.track_activity(activity_type, description, metadata)

    return {
        "success": True,
        "activity_type": activity_type,
        "description": description
    }


@router.post("/sessions/track-file")
async def track_file_modification(file_path: str, operation: str):
    """Track file modification.

    Args:
        file_path: Path to the file
        operation: Operation type (create, edit, delete)

    Returns:
        Success status
    """
    tracker = get_session_tracker()
    tracker.track_file_modification(file_path, operation)

    return {
        "success": True,
        "file_path": file_path,
        "operation": operation
    }


@router.post("/sessions/track-enhancement")
async def track_enhancement_work(
    enhancement_id: str,
    title: str,
    work_description: str
):
    """Track work on an enhancement.

    Args:
        enhancement_id: Enhancement ID (e.g., "012")
        title: Enhancement title
        work_description: Description of work done

    Returns:
        Success status
    """
    tracker = get_session_tracker()
    tracker.track_enhancement_work(enhancement_id, title, work_description)

    return {
        "success": True,
        "enhancement_id": enhancement_id,
        "title": title
    }


@router.post("/sessions/add-topic")
async def add_session_topic(topic: str):
    """Add a topic covered in this session.

    Args:
        topic: Topic or technology learned

    Returns:
        Success status
    """
    tracker = get_session_tracker()
    tracker.add_topic(topic)

    return {"success": True, "topic": topic}


@router.post("/sessions/add-accomplishment")
async def add_session_accomplishment(accomplishment: str):
    """Add an accomplishment for this session.

    Args:
        accomplishment: What was accomplished

    Returns:
        Success status
    """
    tracker = get_session_tracker()
    tracker.add_accomplishment(accomplishment)

    return {"success": True, "accomplishment": accomplishment}


@router.post("/sessions/add-blocker")
async def add_session_blocker(blocker: str):
    """Add a blocker encountered in this session.

    Args:
        blocker: Description of the blocker

    Returns:
        Success status
    """
    tracker = get_session_tracker()
    tracker.add_blocker(blocker)

    return {"success": True, "blocker": blocker}


@router.post("/sessions/add-technology")
async def add_session_technology(technology: str):
    """Add a technology used in this session.

    Args:
        technology: Technology or tool used

    Returns:
        Success status
    """
    tracker = get_session_tracker()
    tracker.add_technology(technology)

    return {"success": True, "technology": technology}


@router.get("/sessions/current")
async def get_current_session():
    """Get summary of current session without ending it.

    Returns:
        Current session summary
    """
    tracker = get_session_tracker()
    summary = tracker.get_current_session_summary()

    return summary


@router.post("/sessions/end")
async def end_session(
    create_reflection: bool = True,
    integration_tag: str = "architecture_enhancements",
    goal_title: str = "AI Orchestrator Architecture Enhancements"
):
    """End the current session and optionally create a growth reflection.

    Args:
        create_reflection: Whether to create a growth reflection
        integration_tag: Tag linking to a goal
        goal_title: Title of the goal

    Returns:
        Session summary and reflection (if created)
    """
    tracker = get_session_tracker()

    # End session
    summary = tracker.end_session()

    response = {
        "session_ended": True,
        "summary": summary
    }

    # Create growth reflection if requested
    if create_reflection and summary.get("duration_hours", 0) >= 0.5:
        reflection_data = tracker.generate_growth_reflection(
            integration_tag=integration_tag,
            goal_title=goal_title
        )

        # Save reflection
        reflection = Reflection(**reflection_data)
        reflections = load_json_data("reflections")
        reflection.id = generate_id("refl")
        reflections.append(reflection.dict())
        save_json_data("reflections", reflections)

        response["reflection_created"] = True
        response["reflection"] = reflection.dict()
    else:
        response["reflection_created"] = False
        response["reason"] = "Session too short (< 30 min)" if summary.get("duration_hours", 0) < 0.5 else "Not requested"

    return response


@router.post("/sessions/auto-capture")
async def auto_capture_session(
    enhancement_id: str,
    enhancement_title: str,
    accomplishments: List[str],
    topics: List[str],
    technologies: List[str],
    blockers: Optional[List[str]] = None,
    duration_hours: float = 2.0,
    integration_tag: str = "architecture_enhancements",
    goal_title: str = "AI Orchestrator Architecture Enhancements"
):
    """Automatically capture session work and create growth reflection.

    This is a convenience endpoint that captures all session data at once
    and creates a growth reflection.

    Args:
        enhancement_id: Enhancement ID worked on
        enhancement_title: Enhancement title
        accomplishments: List of accomplishments
        topics: List of topics covered
        technologies: List of technologies used
        blockers: List of blockers (optional)
        duration_hours: Session duration in hours
        integration_tag: Tag linking to a goal
        goal_title: Title of the goal

    Returns:
        Created growth reflection
    """
    tracker = get_session_tracker()

    # Track enhancement
    tracker.track_enhancement_work(
        enhancement_id,
        enhancement_title,
        "Session work captured"
    )

    # Add accomplishments
    for acc in accomplishments:
        tracker.add_accomplishment(acc)

    # Add topics
    for topic in topics:
        tracker.add_topic(topic)

    # Add technologies
    for tech in technologies:
        tracker.add_technology(tech)

    # Add blockers
    if blockers:
        for blocker in blockers:
            tracker.add_blocker(blocker)

    # Override learning hours
    tracker.current_session["learning_hours"] = duration_hours

    # Generate reflection
    reflection_data = tracker.generate_growth_reflection(
        integration_tag=integration_tag,
        goal_title=goal_title
    )

    # Save reflection
    reflection = Reflection(**reflection_data)
    reflections = load_json_data("reflections")
    reflection.id = generate_id("refl")
    reflections.append(reflection.dict())
    save_json_data("reflections", reflections)

    # End session
    tracker.end_session()

    return {
        "success": True,
        "reflection": reflection.dict()
    }
