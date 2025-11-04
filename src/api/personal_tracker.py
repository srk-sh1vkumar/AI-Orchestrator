"""Personal Tracker API endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import json
import os

router = APIRouter(prefix="/api/tracker", tags=["personal-tracker"])

# Simple file-based storage (will upgrade to DB later)
DATA_FILE = "personal_tracker_data.json"


class Goal(BaseModel):
    """Personal development goal."""
    id: str
    title: str
    description: str
    category: str  # learning, fitness, career, personal, financial
    status: str = "planned"  # planned, in_progress, completed, paused
    progress: int = Field(default=0, ge=0, le=100)
    target_date: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None


class Milestone(BaseModel):
    """Achievement milestone."""
    id: str
    title: str
    description: str
    category: str
    achieved_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    impact: str = "medium"  # low, medium, high


class Skill(BaseModel):
    """Skill acquired."""
    name: str
    category: str  # technical, soft_skills, domain_knowledge, tools
    proficiency: str = "beginner"  # beginner, intermediate, advanced, expert
    acquired_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class LearningSession(BaseModel):
    """Learning time tracking."""
    id: str
    date: str
    hours: float
    activity: str
    category: str
    notes: Optional[str] = None
    skills_practiced: List[str] = Field(default_factory=list)


class Reflection(BaseModel):
    """Personal reflection entry."""
    id: str
    content: str
    type: str = "manual"  # manual, ai_generated
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: List[str] = Field(default_factory=list)
    mood: Optional[str] = None


class TrackerData(BaseModel):
    """Complete tracker data structure."""
    goals: List[Goal] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    learning_sessions: List[LearningSession] = Field(default_factory=list)
    reflections: List[Reflection] = Field(default_factory=list)
    metrics: dict = Field(default_factory=lambda: {
        "total_learning_hours": 0.0,
        "current_streak_days": 0,
        "longest_streak_days": 0,
        "skills_count": 0,
        "goals_completed": 0
    })


def load_data() -> TrackerData:
    """Load tracker data from file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return TrackerData(**data)
    return TrackerData()


def save_data(data: TrackerData) -> None:
    """Save tracker data to file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data.dict(), f, indent=2)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "personal-tracker"}


# Goals Endpoints
@router.get("/goals", response_model=List[Goal])
async def get_goals():
    """Get all goals."""
    data = load_data()
    return data.goals


@router.post("/goals", response_model=Goal)
async def create_goal(goal: Goal):
    """Create a new goal."""
    data = load_data()

    # Check for duplicate ID
    if any(g.id == goal.id for g in data.goals):
        raise HTTPException(status_code=400, detail="Goal ID already exists")

    data.goals.append(goal)
    save_data(data)
    return goal


@router.put("/goals/{goal_id}", response_model=Goal)
async def update_goal(goal_id: str, goal: Goal):
    """Update an existing goal."""
    data = load_data()

    for i, g in enumerate(data.goals):
        if g.id == goal_id:
            # Update completed_at if status changed to completed
            if goal.status == "completed" and g.status != "completed":
                goal.completed_at = datetime.utcnow().isoformat()
                data.metrics["goals_completed"] += 1

            data.goals[i] = goal
            save_data(data)
            return goal

    raise HTTPException(status_code=404, detail="Goal not found")


@router.delete("/goals/{goal_id}")
async def delete_goal(goal_id: str):
    """Delete a goal."""
    data = load_data()
    data.goals = [g for g in data.goals if g.id != goal_id]
    save_data(data)
    return {"message": "Goal deleted"}


# Milestones Endpoints
@router.get("/milestones", response_model=List[Milestone])
async def get_milestones():
    """Get all milestones."""
    data = load_data()
    return data.milestones


@router.post("/milestones", response_model=Milestone)
async def create_milestone(milestone: Milestone):
    """Create a new milestone."""
    data = load_data()
    data.milestones.append(milestone)
    save_data(data)
    return milestone


# Skills Endpoints
@router.get("/skills", response_model=List[Skill])
async def get_skills():
    """Get all skills."""
    data = load_data()
    return data.skills


@router.post("/skills", response_model=Skill)
async def add_skill(skill: Skill):
    """Add a new skill."""
    data = load_data()

    # Check if skill already exists
    existing = next((s for s in data.skills if s.name == skill.name), None)
    if existing:
        # Update proficiency if higher
        if skill.proficiency != existing.proficiency:
            for i, s in enumerate(data.skills):
                if s.name == skill.name:
                    data.skills[i] = skill
                    break
    else:
        data.skills.append(skill)
        data.metrics["skills_count"] = len(data.skills)

    save_data(data)
    return skill


# Learning Sessions Endpoints
@router.get("/learning-sessions", response_model=List[LearningSession])
async def get_learning_sessions():
    """Get all learning sessions."""
    data = load_data()
    return data.learning_sessions


@router.post("/learning-sessions", response_model=LearningSession)
async def log_learning_session(session: LearningSession):
    """Log a new learning session."""
    data = load_data()
    data.learning_sessions.append(session)

    # Update total learning hours
    data.metrics["total_learning_hours"] = round(
        data.metrics["total_learning_hours"] + session.hours, 2
    )

    save_data(data)
    return session


# Reflections Endpoints
@router.get("/reflections", response_model=List[Reflection])
async def get_reflections():
    """Get all reflections."""
    data = load_data()
    return data.reflections


@router.post("/reflections", response_model=Reflection)
async def create_reflection(reflection: Reflection):
    """Create a new reflection."""
    data = load_data()
    data.reflections.append(reflection)
    save_data(data)
    return reflection


@router.post("/reflections/generate")
async def generate_ai_reflection():
    """Generate AI-powered reflection based on current progress."""
    from src.self_dev_agent import SelfDevelopmentAgent

    data = load_data()
    agent = SelfDevelopmentAgent()

    # Build context for reflection
    context = {
        "goals": [g.dict() for g in data.goals],
        "learning_hours": data.metrics["total_learning_hours"],
        "skills_gained": [s.name for s in data.skills]
    }

    # Generate reflection
    content = agent.generate_reflection(context)

    # Create reflection entry
    reflection = Reflection(
        id=f"r{len(data.reflections) + 1}",
        content=content,
        type="ai_generated",
        tags=["ai_generated", "progress", "learning"]
    )

    data.reflections.append(reflection)
    save_data(data)

    return reflection


# Metrics Endpoint
@router.get("/metrics")
async def get_metrics():
    """Get current metrics and statistics."""
    data = load_data()

    # Calculate additional stats
    goals_in_progress = sum(1 for g in data.goals if g.status == "in_progress")
    goals_completed = sum(1 for g in data.goals if g.status == "completed")
    goals_planned = sum(1 for g in data.goals if g.status == "planned")

    avg_progress = 0
    if data.goals:
        avg_progress = sum(g.progress for g in data.goals) / len(data.goals)

    # Category breakdown
    categories = {}
    for goal in data.goals:
        categories[goal.category] = categories.get(goal.category, 0) + 1

    # Recent activity (last 7 days)
    recent_sessions = [
        s for s in data.learning_sessions
        if (datetime.utcnow() - datetime.fromisoformat(s.date)).days <= 7
    ]
    recent_hours = sum(s.hours for s in recent_sessions)

    return {
        **data.metrics,
        "goals_total": len(data.goals),
        "goals_in_progress": goals_in_progress,
        "goals_completed": goals_completed,
        "goals_planned": goals_planned,
        "average_progress": round(avg_progress, 1),
        "categories": categories,
        "recent_learning_hours": round(recent_hours, 1),
        "milestones_count": len(data.milestones),
        "reflections_count": len(data.reflections)
    }


# Dashboard Summary
@router.get("/dashboard")
async def get_dashboard():
    """Get complete dashboard data."""
    data = load_data()
    metrics = await get_metrics()

    # Get recent items
    recent_goals = sorted(
        data.goals,
        key=lambda g: g.created_at,
        reverse=True
    )[:5]

    recent_milestones = sorted(
        data.milestones,
        key=lambda m: m.achieved_at,
        reverse=True
    )[:5]

    recent_reflections = sorted(
        data.reflections,
        key=lambda r: r.generated_at,
        reverse=True
    )[:3]

    return {
        "metrics": metrics,
        "recent_goals": recent_goals,
        "recent_milestones": recent_milestones,
        "recent_reflections": recent_reflections,
        "top_skills": data.skills[:10]
    }
