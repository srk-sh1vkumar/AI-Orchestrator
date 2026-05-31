"""API router for cross-project analysis.

Enhancement 015: Duplication detection and refactoring suggestions.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import structlog

from src.analysis.pattern_matcher import PatternMatcher, DuplicationReport
from src.analysis.code_analyzer import CodeAnalyzer

logger = structlog.get_logger()
router = APIRouter(prefix="/analysis", tags=["analysis"])

# Store analysis results
_analysis_cache: Dict[str, DuplicationReport] = {}
_analysis_status: Dict[str, str] = {}


class AnalysisRequest(BaseModel):
    """Request to analyze projects."""
    projects: Dict[str, str]  # project_name -> project_path
    similarity_threshold: float = 0.8


class AnalysisResponse(BaseModel):
    """Analysis response."""
    analysis_id: str
    status: str
    message: str


class ProjectAnalysisRequest(BaseModel):
    """Request to analyze a single project."""
    project_path: str
    project_name: str


@router.post("/start", response_model=AnalysisResponse)
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
) -> AnalysisResponse:
    """Start cross-project analysis.

    This runs in the background and results can be retrieved via /results/{analysis_id}.
    """
    # Generate analysis ID
    analysis_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Validate paths
    projects = {}
    for name, path_str in request.projects.items():
        path = Path(path_str)
        if not path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Project path does not exist: {path_str}"
            )
        projects[name] = path

    # Mark as running
    _analysis_status[analysis_id] = "running"

    # Run in background
    background_tasks.add_task(
        _run_analysis,
        analysis_id,
        projects,
        request.similarity_threshold,
    )

    return AnalysisResponse(
        analysis_id=analysis_id,
        status="started",
        message=f"Analysis started for {len(projects)} projects",
    )


async def _run_analysis(
    analysis_id: str,
    projects: Dict[str, Path],
    threshold: float,
) -> None:
    """Run analysis in background."""
    try:
        matcher = PatternMatcher()
        report = matcher.analyze_projects(projects, threshold)

        _analysis_cache[analysis_id] = report
        _analysis_status[analysis_id] = "complete"

        logger.info(
            "analysis_complete",
            analysis_id=analysis_id,
            signatures=report.total_signatures,
            duplicates=report.exact_duplicates,
        )

    except Exception as e:
        logger.error("analysis_failed", analysis_id=analysis_id, error=str(e))
        _analysis_status[analysis_id] = f"failed: {str(e)}"


@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str) -> Dict[str, str]:
    """Get status of an analysis."""
    if analysis_id not in _analysis_status:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return {
        "analysis_id": analysis_id,
        "status": _analysis_status[analysis_id],
    }


@router.get("/results/{analysis_id}")
async def get_analysis_results(analysis_id: str) -> Dict[str, Any]:
    """Get results of a completed analysis."""
    if analysis_id not in _analysis_status:
        raise HTTPException(status_code=404, detail="Analysis not found")

    status = _analysis_status[analysis_id]
    if status == "running":
        raise HTTPException(status_code=202, detail="Analysis still running")

    if status.startswith("failed"):
        raise HTTPException(status_code=500, detail=status)

    if analysis_id not in _analysis_cache:
        raise HTTPException(status_code=404, detail="Results not found")

    return _analysis_cache[analysis_id].to_dict()


@router.get("/suggestions/{analysis_id}")
async def get_suggestions(analysis_id: str) -> List[Dict[str, Any]]:
    """Get refactoring suggestions from analysis."""
    if analysis_id not in _analysis_cache:
        raise HTTPException(status_code=404, detail="Analysis not found")

    report = _analysis_cache[analysis_id]
    return [s.to_dict() for s in report.suggestions]


@router.post("/analyze-single")
async def analyze_single_project(request: ProjectAnalysisRequest) -> Dict[str, Any]:
    """Analyze a single project (synchronous)."""
    path = Path(request.project_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail="Project path does not exist")

    analyzer = CodeAnalyzer()
    signatures = analyzer.analyze_project(path, request.project_name)

    # Group by type
    by_type = {"function": 0, "method": 0, "class": 0}
    for sig in signatures:
        if sig.signature_type in by_type:
            by_type[sig.signature_type] += 1

    return {
        "project": request.project_name,
        "total_signatures": len(signatures),
        "breakdown": by_type,
        "files_analyzed": len(set(s.file_path for s in signatures)),
        "avg_complexity": sum(s.complexity for s in signatures) / len(signatures) if signatures else 0,
    }


@router.get("/projects")
async def get_default_projects() -> Dict[str, str]:
    """Get default project paths for analysis."""
    base_path = Path("/Users/shiva/Projects")

    projects = {
        "ai-orchestrator": str(base_path / "ai-orchestrator"),
        "ecommerce-microservices": str(base_path / "ecommerce-microservices"),
        "sre-analytics": str(base_path / "sre-analytics"),
    }

    # Filter to existing projects
    return {k: v for k, v in projects.items() if Path(v).exists()}


@router.post("/quick-scan")
async def quick_scan() -> Dict[str, Any]:
    """Quick scan of default projects."""
    base_path = Path("/Users/shiva/Projects")

    projects = {
        "ai-orchestrator": base_path / "ai-orchestrator",
        "sre-analytics": base_path / "sre-analytics",
    }

    # Filter to existing
    projects = {k: v for k, v in projects.items() if v.exists()}

    if not projects:
        raise HTTPException(status_code=404, detail="No projects found")

    matcher = PatternMatcher()
    report = matcher.analyze_projects(projects, similarity_threshold=0.85)

    return {
        "summary": {
            "projects": list(projects.keys()),
            "total_signatures": report.total_signatures,
            "exact_duplicates": report.exact_duplicates,
            "similar_code": report.similar_code,
            "suggestions_count": len(report.suggestions),
            "analysis_time": f"{report.analysis_time_seconds:.2f}s",
        },
        "top_suggestions": [s.to_dict() for s in report.suggestions[:5]],
    }
