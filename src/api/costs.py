"""Cost tracking and budget management API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

from src.database.mongodb import get_mongodb_manager
from src.core.budget_manager import BudgetManager
from src.database.repositories import (
    CostRecordRepository,
    BudgetRepository,
    BudgetAlertRepository,
)
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/costs", tags=["costs"])


# Pydantic models for API requests/responses
class BudgetCreateRequest(BaseModel):
    """Request to create a budget."""
    budget_name: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    provider: Optional[str] = None
    daily_limit: Optional[float] = None
    weekly_limit: Optional[float] = None
    monthly_limit: Optional[float] = None
    warning_threshold: float = 0.8
    critical_threshold: float = 0.95
    alert_email: Optional[str] = None
    alert_webhook: Optional[str] = None


class CostSummaryResponse(BaseModel):
    """Cost summary response."""
    total_cost: float
    total_tokens: int
    request_count: int
    breakdown: List[Dict[str, Any]]
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class BudgetStatusResponse(BaseModel):
    """Budget status response."""
    budgets: List[Dict[str, Any]]
    total_budgets: int


@router.get("/summary")
async def get_cost_summary(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
) -> CostSummaryResponse:
    """Get cost summary for a specified period.

    Args:
        user_id: Optional user ID filter
        project_id: Optional project ID filter
        provider: Optional provider filter
        days: Number of days to look back (default: 30)

    Returns:
        Cost summary with breakdown by provider/model
    """
    try:
        db_manager = await get_mongodb_manager()
        cost_repo = CostRecordRepository(db_manager)

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get total cost
        total_cost = await cost_repo.get_total_cost(
            user_id=user_id,
            project_id=project_id,
            provider=provider,
            start_date=start_date,
            end_date=end_date,
        )

        # Get cost breakdown
        breakdown = await cost_repo.get_cost_breakdown(
            user_id=user_id,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Calculate totals
        total_tokens = sum(b["total_tokens"] for b in breakdown)
        request_count = sum(b["request_count"] for b in breakdown)

        return CostSummaryResponse(
            total_cost=round(total_cost, 4),
            total_tokens=total_tokens,
            request_count=request_count,
            breakdown=breakdown,
            period_start=start_date,
            period_end=end_date,
        )

    except Exception as e:
        logger.error("cost_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cost summary: {str(e)}")


@router.post("/budgets")
async def create_budget(budget: BudgetCreateRequest) -> Dict[str, Any]:
    """Create a new budget with limits and alerts.

    Args:
        budget: Budget creation request

    Returns:
        Created budget information
    """
    try:
        db_manager = await get_mongodb_manager()
        budget_repo = BudgetRepository(db_manager)

        # Create budget
        created_budget = await budget_repo.create_budget(
            budget_name=budget.budget_name,
            user_id=budget.user_id,
            project_id=budget.project_id,
            provider=budget.provider,
            daily_limit=budget.daily_limit,
            weekly_limit=budget.weekly_limit,
            monthly_limit=budget.monthly_limit,
            warning_threshold=budget.warning_threshold,
            critical_threshold=budget.critical_threshold,
            alert_email=budget.alert_email,
            alert_webhook=budget.alert_webhook,
        )

        return {
            "budget_id": str(created_budget.id),
            "budget_name": created_budget.budget_name,
            "status": "active",
            "message": "Budget created successfully",
        }

    except Exception as e:
        logger.error("budget_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create budget: {str(e)}")


@router.get("/budgets")
async def get_budgets(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
) -> BudgetStatusResponse:
    """Get all active budgets with current utilization.

    Args:
        user_id: Optional user ID filter
        project_id: Optional project ID filter

    Returns:
        Budget status with utilization metrics
    """
    try:
        db_manager = await get_mongodb_manager()
        budget_manager = BudgetManager(db_manager)

        summary = await budget_manager.get_budget_summary(
            user_id=user_id,
            project_id=project_id,
        )

        return BudgetStatusResponse(**summary)

    except Exception as e:
        logger.error("budget_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get budget status: {str(e)}")


@router.get("/budgets/{budget_id}")
async def get_budget(budget_id: str) -> Dict[str, Any]:
    """Get a specific budget by ID.

    Args:
        budget_id: Budget ID

    Returns:
        Budget details
    """
    try:
        db_manager = await get_mongodb_manager()
        budget_repo = BudgetRepository(db_manager)

        budget = await budget_repo.get_budget(budget_id)

        if not budget:
            raise HTTPException(status_code=404, detail=f"Budget {budget_id} not found")

        return {
            "budget_id": str(budget.id),
            "budget_name": budget.budget_name,
            "user_id": budget.user_id,
            "project_id": budget.project_id,
            "provider": budget.provider,
            "limits": {
                "daily": budget.daily_limit,
                "weekly": budget.weekly_limit,
                "monthly": budget.monthly_limit,
            },
            "spent": {
                "daily": budget.daily_spent,
                "weekly": budget.weekly_spent,
                "monthly": budget.monthly_spent,
            },
            "thresholds": {
                "warning": budget.warning_threshold,
                "critical": budget.critical_threshold,
            },
            "alert_status": {
                "warning_triggered": budget.warning_triggered,
                "critical_triggered": budget.critical_triggered,
                "budget_exceeded": budget.budget_exceeded,
            },
            "is_active": budget.is_active,
            "created_at": budget.created_at.isoformat(),
            "updated_at": budget.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("budget_retrieval_failed", error=str(e), budget_id=budget_id)
        raise HTTPException(status_code=500, detail=f"Failed to get budget: {str(e)}")


@router.get("/alerts")
async def get_budget_alerts(
    budget_id: Optional[str] = Query(None, description="Filter by budget ID"),
    limit: int = Query(10, description="Maximum number of alerts", ge=1, le=100),
) -> Dict[str, Any]:
    """Get recent budget alerts.

    Args:
        budget_id: Optional budget ID filter
        limit: Maximum number of alerts to return

    Returns:
        List of budget alerts
    """
    try:
        db_manager = await get_mongodb_manager()
        alert_repo = BudgetAlertRepository(db_manager)

        alerts = await alert_repo.get_recent_alerts(
            budget_id=budget_id,
            limit=limit,
        )

        return {
            "alerts": [
                {
                    "alert_id": str(alert.id),
                    "budget_id": str(alert.budget_id),
                    "alert_type": alert.alert_type,
                    "threshold_type": alert.threshold_type,
                    "limit_usd": alert.limit_usd,
                    "spent_usd": alert.spent_usd,
                    "utilization_percent": alert.utilization_percent,
                    "provider": alert.provider,
                    "notification_sent": alert.notification_sent,
                    "created_at": alert.created_at.isoformat(),
                }
                for alert in alerts
            ],
            "total_alerts": len(alerts),
        }

    except Exception as e:
        logger.error("alert_retrieval_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/projections")
async def get_cost_projections(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
) -> Dict[str, Any]:
    """Get cost projections based on recent usage.

    Args:
        user_id: Optional user ID filter
        project_id: Optional project ID filter
        provider: Optional provider filter

    Returns:
        Cost projections for daily/weekly/monthly periods
    """
    try:
        db_manager = await get_mongodb_manager()
        cost_repo = CostRecordRepository(db_manager)

        # Get last 7 days of costs for projection
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        total_cost_7d = await cost_repo.get_total_cost(
            user_id=user_id,
            project_id=project_id,
            provider=provider,
            start_date=start_date,
            end_date=end_date,
        )

        # Calculate daily average and project
        daily_avg = total_cost_7d / 7
        weekly_projection = daily_avg * 7
        monthly_projection = daily_avg * 30
        yearly_projection = daily_avg * 365

        return {
            "based_on_days": 7,
            "daily_average": round(daily_avg, 4),
            "projections": {
                "weekly": round(weekly_projection, 2),
                "monthly": round(monthly_projection, 2),
                "yearly": round(yearly_projection, 2),
            },
            "warning": "Projections are estimates based on recent usage patterns",
        }

    except Exception as e:
        logger.error("cost_projection_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cost projections: {str(e)}")
