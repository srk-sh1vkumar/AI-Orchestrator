"""
Enhancement tracking API endpoints.

Provides REST API for CRUD operations on project enhancements,
with dual-mode support for both YAML and database backends.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import structlog

from src.db.repositories.mongo_enhancement_repository import MongoEnhancementRepository
from src.db.schemas.enhancement_schemas import (
    Project,
    Enhancement,
    Dependency,
    ProjectResponse,
    EnhancementResponse,
    ProgressResponse,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/enhancements", tags=["enhancements"])

# MongoDB configuration
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "ai_orchestrator"

# Global repository instance (initialized on first use)
_repo: Optional[MongoEnhancementRepository] = None


def get_repository() -> MongoEnhancementRepository:
    """Get or create repository instance."""
    global _repo
    if _repo is None:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        _repo = MongoEnhancementRepository(db)
        logger.info("enhancement_repository_initialized", database=DATABASE_NAME)
    return _repo


# ============================================================================
# Project Endpoints
# ============================================================================


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """Get all projects with summary statistics.

    Returns:
        List of projects with enhancement counts and completion percentages
    """
    try:
        repo = get_repository()
        projects = await repo.get_all_projects()
        logger.info("projects_listed", count=len(projects))
        return projects
    except Exception as e:
        logger.error("list_projects_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_tag}", response_model=ProjectResponse)
async def get_project(project_tag: str):
    """Get project details by tag.

    Args:
        project_tag: Project identifier (e.g., "ai_orchestrator")

    Returns:
        Project details with statistics
    """
    try:
        repo = get_repository()
        project = await repo.get_project(project_tag)

        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{project_tag}' not found"
            )

        # Get statistics
        stats = await repo._get_project_stats(project.id)

        return ProjectResponse(
            project_id=str(project.id),
            project_name=project.project_name,
            project_tag=project.project_tag,
            version=project.version,
            owner=project.owner,
            description=project.description,
            technologies=project.technologies,
            total_enhancements=stats["total"],
            completed=stats["completed"],
            in_progress=stats["in_progress"],
            planned=stats["planned"],
            completion_percentage=stats["completion_percentage"],
            created_at=project.created_at,
            updated_at=project.updated_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_project_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects", response_model=dict)
async def create_project(project: Project):
    """Create a new project.

    Args:
        project: Project data

    Returns:
        Created project ID
    """
    try:
        repo = get_repository()
        project_id = await repo.create_project(project)
        logger.info("project_created", project_tag=project.project_tag, project_id=project_id)
        return {"project_id": project_id, "project_tag": project.project_tag}
    except Exception as e:
        logger.error("create_project_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projects/{project_tag}", response_model=dict)
async def update_project(project_tag: str, updates: dict):
    """Update project metadata.

    Args:
        project_tag: Project identifier
        updates: Fields to update

    Returns:
        Success status
    """
    try:
        repo = get_repository()
        success = await repo.update_project(project_tag, updates)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{project_tag}' not found"
            )

        logger.info("project_updated", project_tag=project_tag)
        return {"success": True, "project_tag": project_tag}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_project_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_tag}", response_model=dict)
async def delete_project(project_tag: str):
    """Delete a project and all its enhancements.

    Args:
        project_tag: Project identifier

    Returns:
        Success status
    """
    try:
        repo = get_repository()
        success = await repo.delete_project(project_tag)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{project_tag}' not found"
            )

        logger.info("project_deleted", project_tag=project_tag)
        return {"success": True, "project_tag": project_tag}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_project_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Enhancement Endpoints
# ============================================================================


@router.get("/projects/{project_tag}/enhancements")
async def list_enhancements(
    project_tag: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    phase: Optional[int] = Query(None, description="Filter by phase"),
):
    """Get all enhancements for a project.

    Args:
        project_tag: Project identifier
        status: Optional status filter
        priority: Optional priority filter
        phase: Optional phase filter

    Returns:
        List of enhancements with dependencies
    """
    try:
        repo = get_repository()
        enhancements = await repo.get_enhancements(project_tag)

        # Apply filters
        if status:
            enhancements = [e for e in enhancements if e.status == status]
        if priority:
            enhancements = [e for e in enhancements if e.priority == priority]
        if phase is not None:
            enhancements = [e for e in enhancements if e.phase == phase]

        # Convert to dict for response
        results = []
        for enh in enhancements:
            results.append({
                "enhancement_id": str(enh.id),
                "enhancement_number": enh.enhancement_number,
                "title": enh.title,
                "category": enh.category,
                "priority": enh.priority,
                "status": enh.status,
                "phase": enh.phase,
                "completion_percentage": enh.completion_percentage,
                "estimated_hours": enh.estimated_hours,
                "actual_hours": enh.actual_hours,
                "completion_date": enh.completion_date,
                "dependencies": []  # Will be populated if needed
            })

        logger.info(
            "enhancements_listed",
            project_tag=project_tag,
            count=len(results),
            filters={"status": status, "priority": priority, "phase": phase}
        )
        return results
    except Exception as e:
        logger.error("list_enhancements_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_tag}/enhancements/{enhancement_number}")
async def get_enhancement(project_tag: str, enhancement_number: str):
    """Get specific enhancement details.

    Args:
        project_tag: Project identifier
        enhancement_number: Enhancement number (e.g., "001")

    Returns:
        Enhancement details with dependencies
    """
    try:
        repo = get_repository()
        enh_response = await repo.get_enhancement(project_tag, enhancement_number)

        if not enh_response:
            raise HTTPException(
                status_code=404,
                detail=f"Enhancement {enhancement_number} not found in project {project_tag}"
            )

        # EnhancementResponse already has the right structure
        return {
            "enhancement_id": enh_response.enhancement_id,
            "enhancement_number": enh_response.enhancement_number,
            "title": enh_response.title,
            "category": enh_response.category,
            "priority": enh_response.priority,
            "status": enh_response.status,
            "phase": enh_response.phase,
            "completion_percentage": enh_response.completion_percentage,
            "estimated_hours": enh_response.estimated_hours,
            "actual_hours": enh_response.actual_hours,
            "completion_date": enh_response.completion_date,
            "dependencies": enh_response.dependencies
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_enhancement_failed",
            project_tag=project_tag,
            enhancement_number=enhancement_number,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_tag}/enhancements", response_model=dict)
async def create_enhancement(project_tag: str, enhancement: Enhancement):
    """Create a new enhancement.

    Args:
        project_tag: Project identifier
        enhancement: Enhancement data

    Returns:
        Created enhancement ID
    """
    try:
        repo = get_repository()
        enhancement_id = await repo.create_enhancement(project_tag, enhancement)
        logger.info(
            "enhancement_created",
            project_tag=project_tag,
            enhancement_number=enhancement.enhancement_number,
            enhancement_id=enhancement_id
        )
        return {
            "enhancement_id": enhancement_id,
            "enhancement_number": enhancement.enhancement_number,
            "project_tag": project_tag
        }
    except Exception as e:
        logger.error("create_enhancement_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projects/{project_tag}/enhancements/{enhancement_number}", response_model=dict)
async def update_enhancement(project_tag: str, enhancement_number: str, updates: dict):
    """Update an enhancement.

    Args:
        project_tag: Project identifier
        enhancement_number: Enhancement number
        updates: Fields to update

    Returns:
        Success status
    """
    try:
        repo = get_repository()
        success = await repo.update_enhancement(project_tag, enhancement_number, updates)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Enhancement {enhancement_number} not found in project {project_tag}"
            )

        logger.info(
            "enhancement_updated",
            project_tag=project_tag,
            enhancement_number=enhancement_number
        )
        return {
            "success": True,
            "project_tag": project_tag,
            "enhancement_number": enhancement_number
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "update_enhancement_failed",
            project_tag=project_tag,
            enhancement_number=enhancement_number,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_tag}/enhancements/{enhancement_number}", response_model=dict)
async def delete_enhancement(project_tag: str, enhancement_number: str):
    """Delete an enhancement (soft delete - marks as cancelled).

    Args:
        project_tag: Project identifier
        enhancement_number: Enhancement number

    Returns:
        Success status
    """
    try:
        repo = get_repository()
        success = await repo.delete_enhancement(project_tag, enhancement_number)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Enhancement {enhancement_number} not found in project {project_tag}"
            )

        logger.info(
            "enhancement_deleted",
            project_tag=project_tag,
            enhancement_number=enhancement_number
        )
        return {
            "success": True,
            "project_tag": project_tag,
            "enhancement_number": enhancement_number
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "delete_enhancement_failed",
            project_tag=project_tag,
            enhancement_number=enhancement_number,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Progress & Analytics Endpoints
# ============================================================================


@router.get("/projects/{project_tag}/progress", response_model=ProgressResponse)
async def get_progress(project_tag: str):
    """Get current progress statistics for a project.

    Args:
        project_tag: Project identifier

    Returns:
        Progress statistics with velocity metrics
    """
    try:
        repo = get_repository()
        progress = await repo.get_progress(project_tag)
        logger.info("progress_retrieved", project_tag=project_tag)
        return progress
    except Exception as e:
        logger.error("get_progress_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_tag}/progress/snapshot", response_model=dict)
async def create_progress_snapshot(project_tag: str):
    """Create a progress snapshot for historical tracking.

    Args:
        project_tag: Project identifier

    Returns:
        Created snapshot ID
    """
    try:
        repo = get_repository()
        snapshot_id = await repo.create_progress_snapshot(project_tag)
        logger.info("progress_snapshot_created", project_tag=project_tag, snapshot_id=snapshot_id)
        return {"snapshot_id": snapshot_id, "project_tag": project_tag}
    except Exception as e:
        logger.error("create_progress_snapshot_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_tag}/progress/history")
async def get_progress_history(
    project_tag: str,
    days: int = Query(30, description="Number of days of history")
):
    """Get progress history for a project.

    Args:
        project_tag: Project identifier
        days: Number of days of history to retrieve

    Returns:
        List of progress snapshots
    """
    try:
        repo = get_repository()
        snapshots = await repo.get_progress_history(project_tag, days=days)
        logger.info("progress_history_retrieved", project_tag=project_tag, count=len(snapshots))

        return {
            "project_tag": project_tag,
            "days": days,
            "snapshots": [
                {
                    "snapshot_date": snap.snapshot_date.isoformat(),
                    "total_enhancements": snap.total_enhancements,
                    "completed": snap.completed,
                    "in_progress": snap.in_progress,
                    "planned": snap.planned,
                    "blocked": snap.blocked,
                    "completion_percentage": snap.completion_percentage,
                    "estimated_total_hours": snap.estimated_total_hours,
                    "actual_total_hours": snap.actual_total_hours,
                    "velocity": snap.velocity.model_dump() if snap.velocity else None,
                }
                for snap in snapshots
            ]
        }
    except Exception as e:
        logger.error("get_progress_history_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Search & Filter Endpoints
# ============================================================================


@router.get("/projects/{project_tag}/search")
async def search_enhancements(
    project_tag: str,
    query: str = Query(..., description="Search query"),
):
    """Search enhancements by title, description, or tags.

    Args:
        project_tag: Project identifier
        query: Search query string

    Returns:
        Matching enhancements
    """
    try:
        repo = get_repository()
        results = await repo.search_enhancements(project_tag, query)
        logger.info("enhancements_searched", project_tag=project_tag, query=query, count=len(results))
        return {
            "project_tag": project_tag,
            "query": query,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error("search_enhancements_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_tag}/blocked")
async def get_blocked_enhancements(project_tag: str):
    """Get all blocked enhancements for a project.

    Args:
        project_tag: Project identifier

    Returns:
        List of blocked enhancements
    """
    try:
        repo = get_repository()
        blocked = await repo.get_blocked_enhancements(project_tag)
        logger.info("blocked_enhancements_retrieved", project_tag=project_tag, count=len(blocked))
        return {
            "project_tag": project_tag,
            "blocked_enhancements": blocked,
            "total": len(blocked)
        }
    except Exception as e:
        logger.error("get_blocked_enhancements_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Dependency Endpoints
# ============================================================================


@router.get("/projects/{project_tag}/enhancements/{enhancement_number}/dependencies")
async def get_dependencies(project_tag: str, enhancement_number: str):
    """Get dependencies for an enhancement.

    Args:
        project_tag: Project identifier
        enhancement_number: Enhancement number

    Returns:
        List of dependencies
    """
    try:
        repo = get_repository()

        # Get enhancement ID first
        enhancement = await repo.get_enhancement(project_tag, enhancement_number)
        if not enhancement:
            raise HTTPException(
                status_code=404,
                detail=f"Enhancement {enhancement_number} not found"
            )

        dependencies = await repo.get_dependencies(enhancement.enhancement_id)
        logger.info(
            "dependencies_retrieved",
            project_tag=project_tag,
            enhancement_number=enhancement_number,
            count=len(dependencies)
        )

        return {
            "project_tag": project_tag,
            "enhancement_number": enhancement_number,
            "dependencies": [
                {
                    "depends_on_id": str(dep.depends_on_id) if dep.depends_on_id else None,
                    "yaml_id": dep.yaml_id,
                    "dependency_type": dep.dependency_type,
                    "note": dep.note,
                }
                for dep in dependencies
            ],
            "total": len(dependencies)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "get_dependencies_failed",
            project_tag=project_tag,
            enhancement_number=enhancement_number,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_tag}/enhancements/{enhancement_number}/dependencies", response_model=dict)
async def add_dependency(project_tag: str, enhancement_number: str, dependency: Dependency):
    """Add a dependency to an enhancement.

    Args:
        project_tag: Project identifier
        enhancement_number: Enhancement number
        dependency: Dependency data

    Returns:
        Created dependency ID
    """
    try:
        repo = get_repository()
        dependency_id = await repo.add_dependency(dependency)
        logger.info(
            "dependency_added",
            project_tag=project_tag,
            enhancement_number=enhancement_number,
            dependency_id=dependency_id
        )
        return {
            "dependency_id": dependency_id,
            "project_tag": project_tag,
            "enhancement_number": enhancement_number
        }
    except Exception as e:
        logger.error("add_dependency_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_tag}/dependency-graph")
async def get_dependency_graph(project_tag: str):
    """Get complete dependency graph for a project.

    Args:
        project_tag: Project identifier

    Returns:
        Dependency graph with nodes and edges
    """
    try:
        repo = get_repository()
        graph = await repo.get_dependency_graph(project_tag)
        logger.info("dependency_graph_retrieved", project_tag=project_tag)
        return {
            "project_tag": project_tag,
            "graph": graph
        }
    except Exception as e:
        logger.error("get_dependency_graph_failed", project_tag=project_tag, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
