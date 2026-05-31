"""Cost tracking service for LLM requests.

Enhancement 007: Cost Tracking & Budget Alerts
- Integrate cost calculator with MongoDB storage
- Real-time budget monitoring and alerts
- Cost-aware provider recommendations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import structlog

from src.core.cost_calculator import CostCalculator, CostBreakdown
from src.database.repositories import (
    CostRecordRepository,
    BudgetRepository,
    BudgetAlertRepository,
)
from src.database.models import BudgetDocument

logger = structlog.get_logger()


class BudgetAlert:
    """Budget alert details."""

    def __init__(
        self,
        alert_type: str,
        threshold_type: str,
        budget_name: str,
        limit: float,
        spent: float,
        utilization: float,
    ):
        self.alert_type = alert_type
        self.threshold_type = threshold_type
        self.budget_name = budget_name
        self.limit = limit
        self.spent = spent
        self.utilization = utilization


class CostTrackingService:
    """Service for tracking costs and managing budgets."""

    def __init__(
        self,
        cost_repo: CostRecordRepository,
        budget_repo: BudgetRepository,
        alert_repo: BudgetAlertRepository,
    ):
        """Initialize cost tracking service.

        Args:
            cost_repo: Cost record repository
            budget_repo: Budget repository
            alert_repo: Budget alert repository
        """
        self.cost_repo = cost_repo
        self.budget_repo = budget_repo
        self.alert_repo = alert_repo
        self.logger = logger.bind(component="cost_tracking_service")

    async def track_request_cost(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        model: Optional[str] = None,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        request_type: str = "chat",
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostBreakdown:
        """Track cost for an LLM request.

        Args:
            provider: LLM provider
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Optional model name
            conversation_id: Optional conversation ID
            message_id: Optional message ID
            user_id: Optional user ID
            project_id: Optional project ID
            category: Optional task category
            request_type: Request type (chat/tool_execution/collaboration)
            success: Whether request was successful
            metadata: Optional additional metadata

        Returns:
            CostBreakdown with detailed cost information
        """
        # Calculate cost using cost calculator
        breakdown = CostCalculator.calculate_cost(provider, input_tokens, output_tokens, model)

        # Store cost record in MongoDB
        await self.cost_repo.record_cost(
            provider=breakdown.provider,
            model=breakdown.model,
            input_tokens=breakdown.input_tokens,
            output_tokens=breakdown.output_tokens,
            input_cost=breakdown.input_cost,
            output_cost=breakdown.output_cost,
            conversation_id=ObjectId(conversation_id) if conversation_id else None,
            message_id=ObjectId(message_id) if message_id else None,
            user_id=user_id,
            project_id=project_id,
            category=category,
            request_type=request_type,
            success=success,
            metadata=metadata,
        )

        self.logger.info(
            "request_cost_tracked",
            provider=provider,
            model=breakdown.model,
            total_cost=breakdown.total_cost,
            total_tokens=breakdown.total_tokens,
            user_id=user_id,
            project_id=project_id,
        )

        # Check budgets and trigger alerts if needed
        if user_id or project_id:
            await self._check_budgets(
                user_id=user_id,
                project_id=project_id,
                provider=provider,
                cost_added=breakdown.total_cost,
            )

        return breakdown

    async def _check_budgets(
        self,
        user_id: Optional[str],
        project_id: Optional[str],
        provider: str,
        cost_added: float,
    ) -> None:
        """Check budgets and trigger alerts if thresholds exceeded.

        Args:
            user_id: User ID
            project_id: Project ID
            provider: Provider name
            cost_added: Cost just added
        """
        # Get active budgets for this user/project/provider
        budgets = await self.budget_repo.get_active_budgets(
            user_id=user_id, project_id=project_id, provider=provider
        )

        # Also check global budgets (provider=None)
        global_budgets = await self.budget_repo.get_active_budgets(
            user_id=user_id, project_id=project_id, provider=None
        )
        budgets.extend(global_budgets)

        now = datetime.utcnow()

        for budget in budgets:
            # Calculate current spent amounts
            daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            weekly_start = daily_start - timedelta(days=now.weekday())
            monthly_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Get spent amounts from cost records
            daily_spent = await self.cost_repo.get_total_cost(
                user_id=user_id,
                project_id=project_id,
                provider=budget.provider,
                start_date=daily_start,
                end_date=now,
            )

            weekly_spent = await self.cost_repo.get_total_cost(
                user_id=user_id,
                project_id=project_id,
                provider=budget.provider,
                start_date=weekly_start,
                end_date=now,
            )

            monthly_spent = await self.cost_repo.get_total_cost(
                user_id=user_id,
                project_id=project_id,
                provider=budget.provider,
                start_date=monthly_start,
                end_date=now,
            )

            # Update budget spent amounts
            await self.budget_repo.update_budget_spent(
                budget_id=str(budget.id),
                daily_spent=daily_spent,
                weekly_spent=weekly_spent,
                monthly_spent=monthly_spent,
            )

            # Check thresholds and create alerts
            await self._check_threshold(
                budget=budget,
                threshold_type="daily",
                limit=budget.daily_limit,
                spent=daily_spent,
            )

            await self._check_threshold(
                budget=budget,
                threshold_type="weekly",
                limit=budget.weekly_limit,
                spent=weekly_spent,
            )

            await self._check_threshold(
                budget=budget,
                threshold_type="monthly",
                limit=budget.monthly_limit,
                spent=monthly_spent,
            )

    async def _check_threshold(
        self,
        budget: BudgetDocument,
        threshold_type: str,
        limit: Optional[float],
        spent: float,
    ) -> None:
        """Check if budget threshold is exceeded.

        Args:
            budget: Budget document
            threshold_type: Threshold type (daily/weekly/monthly)
            limit: Budget limit
            spent: Amount spent
        """
        if limit is None or limit == 0:
            return

        utilization = (spent / limit) * 100.0

        # Check if exceeded
        if spent >= limit:
            if not budget.budget_exceeded:
                await self._create_alert(
                    budget=budget,
                    alert_type="exceeded",
                    threshold_type=threshold_type,
                    limit=limit,
                    spent=spent,
                    utilization=utilization,
                )
                await self.budget_repo.update_alert_status(
                    budget_id=str(budget.id), budget_exceeded=True
                )

        # Check critical threshold
        elif utilization >= (budget.critical_threshold * 100):
            if not budget.critical_triggered:
                await self._create_alert(
                    budget=budget,
                    alert_type="critical",
                    threshold_type=threshold_type,
                    limit=limit,
                    spent=spent,
                    utilization=utilization,
                )
                await self.budget_repo.update_alert_status(
                    budget_id=str(budget.id), critical_triggered=True
                )

        # Check warning threshold
        elif utilization >= (budget.warning_threshold * 100):
            if not budget.warning_triggered:
                await self._create_alert(
                    budget=budget,
                    alert_type="warning",
                    threshold_type=threshold_type,
                    limit=limit,
                    spent=spent,
                    utilization=utilization,
                )
                await self.budget_repo.update_alert_status(
                    budget_id=str(budget.id), warning_triggered=True
                )

    async def _create_alert(
        self,
        budget: BudgetDocument,
        alert_type: str,
        threshold_type: str,
        limit: float,
        spent: float,
        utilization: float,
    ) -> None:
        """Create a budget alert.

        Args:
            budget: Budget document
            alert_type: Alert type (warning/critical/exceeded)
            threshold_type: Threshold type (daily/weekly/monthly)
            limit: Budget limit
            spent: Amount spent
            utilization: Utilization percentage
        """
        # Create alert in database
        await self.alert_repo.create_alert(
            budget_id=budget.id,
            alert_type=alert_type,
            threshold_type=threshold_type,
            limit_usd=limit,
            spent_usd=spent,
            utilization_percent=utilization,
            provider=budget.provider,
            notification_sent=False,  # Will be sent by notification service
            metadata={
                "budget_name": budget.budget_name,
                "user_id": budget.user_id,
                "project_id": budget.project_id,
            },
        )

        self.logger.warning(
            "budget_threshold_exceeded",
            budget_name=budget.budget_name,
            alert_type=alert_type,
            threshold_type=threshold_type,
            limit=limit,
            spent=spent,
            utilization=utilization,
        )

        # TODO: Send notification (email/webhook) via notification service
        # This will be implemented in a separate notification module

    async def get_cost_summary(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        provider: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get cost summary for given criteria.

        Args:
            user_id: Filter by user ID
            project_id: Filter by project ID
            provider: Filter by provider
            days: Number of days to include (default 30)

        Returns:
            Cost summary dictionary
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        total_cost = await self.cost_repo.get_total_cost(
            user_id=user_id,
            project_id=project_id,
            provider=provider,
            start_date=start_date,
        )

        breakdown = await self.cost_repo.get_cost_breakdown(
            user_id=user_id, project_id=project_id, start_date=start_date
        )

        return {
            "total_cost": round(total_cost, 4),
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "breakdown_by_provider": breakdown,
        }

    async def get_budget_status(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get budget status for user/project.

        Args:
            user_id: Filter by user ID
            project_id: Filter by project ID

        Returns:
            List of budget statuses
        """
        budgets = await self.budget_repo.get_active_budgets(
            user_id=user_id, project_id=project_id
        )

        statuses = []
        for budget in budgets:
            # Calculate utilization percentages
            daily_util = (
                (budget.daily_spent / budget.daily_limit * 100)
                if budget.daily_limit
                else None
            )
            weekly_util = (
                (budget.weekly_spent / budget.weekly_limit * 100)
                if budget.weekly_limit
                else None
            )
            monthly_util = (
                (budget.monthly_spent / budget.monthly_limit * 100)
                if budget.monthly_limit
                else None
            )

            statuses.append(
                {
                    "budget_id": str(budget.id),
                    "budget_name": budget.budget_name,
                    "provider": budget.provider or "all",
                    "daily": {
                        "limit": budget.daily_limit,
                        "spent": budget.daily_spent,
                        "utilization": round(daily_util, 2) if daily_util else None,
                    },
                    "weekly": {
                        "limit": budget.weekly_limit,
                        "spent": budget.weekly_spent,
                        "utilization": round(weekly_util, 2) if weekly_util else None,
                    },
                    "monthly": {
                        "limit": budget.monthly_limit,
                        "spent": budget.monthly_spent,
                        "utilization": round(monthly_util, 2) if monthly_util else None,
                    },
                    "alerts": {
                        "warning_triggered": budget.warning_triggered,
                        "critical_triggered": budget.critical_triggered,
                        "budget_exceeded": budget.budget_exceeded,
                    },
                }
            )

        return statuses

    async def recommend_cheapest_provider(
        self,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        exclude_exceeded_budgets: bool = True,
    ) -> Optional[str]:
        """Recommend cheapest provider considering budgets.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            user_id: User ID
            project_id: Project ID
            exclude_exceeded_budgets: Exclude providers that exceeded budgets

        Returns:
            Recommended provider or None
        """
        # Get all available providers
        all_providers = list(CostCalculator.DEFAULT_MODELS.keys())

        # Filter out providers with exceeded budgets
        if exclude_exceeded_budgets and (user_id or project_id):
            available_providers = []
            for provider in all_providers:
                budgets = await self.budget_repo.get_active_budgets(
                    user_id=user_id, project_id=project_id, provider=provider
                )

                # Check if any budget is exceeded
                budget_ok = True
                for budget in budgets:
                    if budget.budget_exceeded:
                        budget_ok = False
                        break

                if budget_ok:
                    available_providers.append(provider)

            if not available_providers:
                self.logger.warning(
                    "no_providers_available_under_budget",
                    user_id=user_id,
                    project_id=project_id,
                )
                return None
        else:
            available_providers = all_providers

        # Find cheapest provider among available ones
        cheapest_provider, cost = CostCalculator.get_cheapest_provider(
            input_tokens, output_tokens, available_providers
        )

        self.logger.info(
            "cheapest_provider_recommended",
            provider=cheapest_provider,
            estimated_cost=cost,
            available_providers=available_providers,
        )

        return cheapest_provider
