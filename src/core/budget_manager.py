"""Budget management and alert system for cost tracking."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import structlog

from src.database.mongodb import MongoDBManager
from src.database.repositories import (
    CostRecordRepository,
    BudgetRepository,
    BudgetAlertRepository,
)
from src.database.models import BudgetDocument
from src.cost_estimator import get_model_pricing

logger = structlog.get_logger()


class BudgetManager:
    """Manages budget limits and alerts for LLM usage costs."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize budget manager.

        Args:
            db_manager: MongoDB manager instance
        """
        self.db_manager = db_manager
        self.cost_repo = CostRecordRepository(db_manager)
        self.budget_repo = BudgetRepository(db_manager)
        self.alert_repo = BudgetAlertRepository(db_manager)
        self.logger = logger.bind(component="budget_manager")

    async def record_and_check_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        conversation_id: Optional[ObjectId] = None,
        message_id: Optional[ObjectId] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        request_type: Optional[str] = None,
        success: bool = True,
    ) -> Dict[str, Any]:
        """Record cost and check against budgets.

        Args:
            provider: LLM provider
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            conversation_id: Optional conversation ID
            message_id: Optional message ID
            user_id: Optional user ID
            project_id: Optional project ID
            category: Optional task category
            request_type: Optional request type
            success: Whether request was successful

        Returns:
            Dictionary with cost record and budget status
        """
        # Calculate costs
        input_cost_per_1k, output_cost_per_1k = get_model_pricing(model)
        input_cost = (input_tokens / 1000.0) * input_cost_per_1k
        output_cost = (output_tokens / 1000.0) * output_cost_per_1k
        total_cost = input_cost + output_cost

        # Record cost
        cost_record = await self.cost_repo.record_cost(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            conversation_id=conversation_id,
            message_id=message_id,
            user_id=user_id,
            project_id=project_id,
            category=category,
            request_type=request_type,
            success=success,
        )

        # Check budgets
        budget_status = await self.check_budgets(
            user_id=user_id,
            project_id=project_id,
            provider=provider,
            cost=total_cost,
        )

        return {
            "cost_record_id": str(cost_record.id),
            "total_cost": total_cost,
            "total_tokens": input_tokens + output_tokens,
            "budget_status": budget_status,
        }

    async def check_budgets(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        provider: Optional[str] = None,
        cost: float = 0.0,
    ) -> Dict[str, Any]:
        """Check budgets and trigger alerts if needed.

        Args:
            user_id: User ID
            project_id: Project ID
            provider: Provider name
            cost: Cost to add to current spent

        Returns:
            Dictionary with budget status and alerts
        """
        # Get active budgets
        budgets = await self.budget_repo.get_active_budgets(
            user_id=user_id,
            project_id=project_id,
            provider=provider,
        )

        if not budgets:
            return {"budgets_checked": 0, "alerts_triggered": []}

        alerts_triggered = []

        for budget in budgets:
            # Update spent amounts (add new cost)
            now = datetime.utcnow()

            # Calculate current spent amounts from database
            daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            weekly_start = daily_start - timedelta(days=daily_start.weekday())
            monthly_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            daily_spent = await self.cost_repo.get_total_cost(
                user_id=budget.user_id,
                project_id=budget.project_id,
                provider=budget.provider,
                start_date=daily_start,
            ) + cost

            weekly_spent = await self.cost_repo.get_total_cost(
                user_id=budget.user_id,
                project_id=budget.project_id,
                provider=budget.provider,
                start_date=weekly_start,
            ) + cost

            monthly_spent = await self.cost_repo.get_total_cost(
                user_id=budget.user_id,
                project_id=budget.project_id,
                provider=budget.provider,
                start_date=monthly_start,
            ) + cost

            # Update budget spent amounts
            await self.budget_repo.update_budget_spent(
                budget_id=str(budget.id),
                daily_spent=daily_spent,
                weekly_spent=weekly_spent,
                monthly_spent=monthly_spent,
            )

            # Check each limit type
            for threshold_type, limit, spent in [
                ("daily", budget.daily_limit, daily_spent),
                ("weekly", budget.weekly_limit, weekly_spent),
                ("monthly", budget.monthly_limit, monthly_spent),
            ]:
                if limit is None:
                    continue

                utilization = (spent / limit) * 100 if limit > 0 else 0

                # Check if exceeded
                if spent > limit:
                    if not budget.budget_exceeded:
                        alert = await self._create_alert(
                            budget=budget,
                            alert_type="exceeded",
                            threshold_type=threshold_type,
                            limit_usd=limit,
                            spent_usd=spent,
                            utilization_percent=utilization,
                        )
                        alerts_triggered.append(alert)
                        await self.budget_repo.update_alert_status(
                            budget_id=str(budget.id),
                            budget_exceeded=True,
                        )

                # Check critical threshold
                elif utilization >= budget.critical_threshold * 100:
                    if not budget.critical_triggered:
                        alert = await self._create_alert(
                            budget=budget,
                            alert_type="critical",
                            threshold_type=threshold_type,
                            limit_usd=limit,
                            spent_usd=spent,
                            utilization_percent=utilization,
                        )
                        alerts_triggered.append(alert)
                        await self.budget_repo.update_alert_status(
                            budget_id=str(budget.id),
                            critical_triggered=True,
                        )

                # Check warning threshold
                elif utilization >= budget.warning_threshold * 100:
                    if not budget.warning_triggered:
                        alert = await self._create_alert(
                            budget=budget,
                            alert_type="warning",
                            threshold_type=threshold_type,
                            limit_usd=limit,
                            spent_usd=spent,
                            utilization_percent=utilization,
                        )
                        alerts_triggered.append(alert)
                        await self.budget_repo.update_alert_status(
                            budget_id=str(budget.id),
                            warning_triggered=True,
                        )

        return {
            "budgets_checked": len(budgets),
            "alerts_triggered": [
                {
                    "budget_id": str(alert.budget_id),
                    "alert_type": alert.alert_type,
                    "threshold_type": alert.threshold_type,
                    "utilization_percent": alert.utilization_percent,
                }
                for alert in alerts_triggered
            ],
        }

    async def _create_alert(
        self,
        budget: BudgetDocument,
        alert_type: str,
        threshold_type: str,
        limit_usd: float,
        spent_usd: float,
        utilization_percent: float,
    ):
        """Create and send budget alert.

        Args:
            budget: Budget document
            alert_type: Alert type (warning/critical/exceeded)
            threshold_type: Threshold type (daily/weekly/monthly)
            limit_usd: Budget limit
            spent_usd: Amount spent
            utilization_percent: Utilization percentage

        Returns:
            Created alert document
        """
        # Create alert record
        alert = await self.alert_repo.create_alert(
            budget_id=budget.id,
            alert_type=alert_type,
            threshold_type=threshold_type,
            limit_usd=limit_usd,
            spent_usd=spent_usd,
            utilization_percent=utilization_percent,
            provider=budget.provider,
        )

        # TODO: Implement notification sending (email/webhook)
        # For now, just log the alert
        self.logger.warning(
            "budget_alert",
            budget_name=budget.budget_name,
            alert_type=alert_type,
            threshold_type=threshold_type,
            utilization=f"{utilization_percent:.1f}%",
            spent=f"${spent_usd:.4f}",
            limit=f"${limit_usd:.2f}",
        )

        return alert

    async def get_budget_summary(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get budget summary and current utilization.

        Args:
            user_id: Optional user ID filter
            project_id: Optional project ID filter

        Returns:
            Dictionary with budget summary
        """
        budgets = await self.budget_repo.get_active_budgets(
            user_id=user_id,
            project_id=project_id,
        )

        summary = []
        for budget in budgets:
            budget_info = {
                "budget_id": str(budget.id),
                "budget_name": budget.budget_name,
                "provider": budget.provider or "all",
                "limits": {},
                "spent": {},
                "utilization": {},
                "alert_status": {
                    "warning_triggered": budget.warning_triggered,
                    "critical_triggered": budget.critical_triggered,
                    "budget_exceeded": budget.budget_exceeded,
                },
            }

            # Add limit/spent/utilization for each period
            for period, limit, spent in [
                ("daily", budget.daily_limit, budget.daily_spent),
                ("weekly", budget.weekly_limit, budget.weekly_spent),
                ("monthly", budget.monthly_limit, budget.monthly_spent),
            ]:
                if limit is not None:
                    budget_info["limits"][period] = limit
                    budget_info["spent"][period] = spent
                    budget_info["utilization"][period] = (
                        (spent / limit * 100) if limit > 0 else 0
                    )

            summary.append(budget_info)

        return {
            "budgets": summary,
            "total_budgets": len(summary),
        }

    async def reset_budget_periods(self) -> None:
        """Reset budget periods (called by scheduler).

        This should be called:
        - Daily at midnight for daily budgets
        - Weekly on Monday for weekly budgets
        - Monthly on 1st for monthly budgets
        """
        now = datetime.utcnow()

        # Get all active budgets
        budgets = await self.budget_repo.get_active_budgets()

        for budget in budgets:
            reset_daily = False
            reset_weekly = False
            reset_monthly = False

            # Check if we need to reset each period
            last_reset = budget.last_reset

            # Daily reset (if it's a new day)
            if now.day != last_reset.day:
                reset_daily = True

            # Weekly reset (if it's Monday and last reset was last week)
            if now.weekday() == 0 and (now - last_reset).days >= 7:
                reset_weekly = True

            # Monthly reset (if it's 1st and last reset was last month)
            if now.day == 1 and now.month != last_reset.month:
                reset_monthly = True

            # Perform resets
            if reset_daily or reset_weekly or reset_monthly:
                update_fields: Dict[str, Any] = {}

                if reset_daily and budget.daily_limit is not None:
                    update_fields["daily_spent"] = 0.0
                    update_fields["warning_triggered"] = False
                    update_fields["critical_triggered"] = False
                    update_fields["budget_exceeded"] = False

                if reset_weekly and budget.weekly_limit is not None:
                    update_fields["weekly_spent"] = 0.0

                if reset_monthly and budget.monthly_limit is not None:
                    update_fields["monthly_spent"] = 0.0

                if update_fields:
                    update_fields["last_reset"] = now
                    await self.budget_repo.update_budget_spent(
                        budget_id=str(budget.id),
                        **update_fields
                    )

                    self.logger.info(
                        "budget_reset",
                        budget_id=str(budget.id),
                        budget_name=budget.budget_name,
                        reset_daily=reset_daily,
                        reset_weekly=reset_weekly,
                        reset_monthly=reset_monthly,
                    )
