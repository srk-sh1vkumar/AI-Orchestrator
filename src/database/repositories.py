"""Repository layer for database operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from src.database.mongodb import MongoDBManager
from src.database.models import (
    ConversationDocument,
    MessageDocument,
    ToolExecutionDocument,
    ContextEventDocument,
    ProviderMetricDocument,
    ConversationMetrics,
    CostRecordDocument,
    BudgetDocument,
    BudgetAlertDocument,
)
import structlog

logger = structlog.get_logger()


class ConversationRepository:
    """Repository for conversation operations."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize conversation repository.

        Args:
            db_manager: MongoDB manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("conversations")
        self.logger = logger.bind(component="conversation_repository")

    async def create_conversation(
        self,
        provider_used: str,
        routing_decision: Dict[str, Any],
        user_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> ConversationDocument:
        """Create a new conversation.

        Args:
            provider_used: LLM provider used
            routing_decision: Routing decision dict
            user_id: Optional user ID
            title: Optional conversation title

        Returns:
            Created conversation document
        """
        conversation = ConversationDocument(
            user_id=user_id,
            title=title,
            provider_used=provider_used,
            routing_decision=routing_decision,
        )

        result = await self.collection.insert_one(conversation.dict(by_alias=True, exclude={"id"}))
        conversation.id = result.inserted_id

        self.logger.info(
            "conversation_created",
            conversation_id=str(conversation.id),
            provider=provider_used,
        )

        return conversation

    async def get_conversation(
        self, conversation_id: str
    ) -> Optional[ConversationDocument]:
        """Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation document or None
        """
        doc = await self.collection.find_one({"_id": ObjectId(conversation_id)})
        if doc:
            return ConversationDocument(**doc)
        return None

    async def update_conversation_metrics(
        self, conversation_id: str, metrics: ConversationMetrics
    ) -> bool:
        """Update conversation metrics.

        Args:
            conversation_id: Conversation ID
            metrics: Updated metrics

        Returns:
            True if updated successfully
        """
        result = await self.collection.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$set": {
                    "metrics": metrics.dict(),
                    "updated_at": datetime.utcnow(),
                }
            },
        )

        return result.modified_count > 0

    async def list_conversations(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[ConversationDocument]:
        """List conversations with filters.

        Args:
            user_id: Filter by user ID
            status: Filter by status
            limit: Max results
            skip: Skip results

        Returns:
            List of conversations
        """
        query = {}
        if user_id:
            query["user_id"] = user_id
        if status:
            query["status"] = status

        cursor = self.collection.find(query).sort("created_at", -1).limit(limit).skip(skip)
        docs = await cursor.to_list(length=limit)

        return [ConversationDocument(**doc) for doc in docs]


class MessageRepository:
    """Repository for message operations."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize message repository.

        Args:
            db_manager: MongoDB manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("messages")
        self.logger = logger.bind(component="message_repository")

    async def create_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        token_count: Optional[int] = None,
        cost_usd: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MessageDocument:
        """Create a new message.

        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant/system)
            content: Message content
            provider: LLM provider
            model: Model used
            token_count: Token count
            cost_usd: Cost in USD
            metadata: Additional metadata

        Returns:
            Created message document
        """
        message = MessageDocument(
            conversation_id=ObjectId(conversation_id),
            role=role,
            content=content,
            provider=provider,
            model=model,
            token_count=token_count,
            cost_usd=cost_usd,
            metadata=metadata or {},
        )

        result = await self.collection.insert_one(message.dict(by_alias=True, exclude={"id"}))
        message.id = result.inserted_id

        self.logger.info(
            "message_created",
            message_id=str(message.id),
            conversation_id=conversation_id,
            role=role,
        )

        return message

    async def get_conversation_messages(
        self, conversation_id: str, limit: Optional[int] = None
    ) -> List[MessageDocument]:
        """Get all messages for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Optional limit

        Returns:
            List of messages
        """
        query = {"conversation_id": ObjectId(conversation_id)}
        cursor = self.collection.find(query).sort("created_at", 1)

        if limit:
            cursor = cursor.limit(limit)

        docs = await cursor.to_list(length=limit or 1000)
        return [MessageDocument(**doc) for doc in docs]


class ToolExecutionRepository:
    """Repository for tool execution operations."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize tool execution repository.

        Args:
            db_manager: MongoDB manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("tool_executions")
        self.logger = logger.bind(component="tool_execution_repository")

    async def create_tool_execution(
        self,
        conversation_id: str,
        tool_type: str,
        operation: str,
        success: bool,
        execution_time_ms: int,
        message_id: Optional[str] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ) -> ToolExecutionDocument:
        """Create a tool execution record.

        Args:
            conversation_id: Conversation ID
            tool_type: Tool type
            operation: Operation performed
            success: Whether execution was successful
            execution_time_ms: Execution time in ms
            message_id: Optional message ID
            result: Optional result data
            error: Optional error message

        Returns:
            Created tool execution document
        """
        tool_execution = ToolExecutionDocument(
            conversation_id=ObjectId(conversation_id),
            message_id=ObjectId(message_id) if message_id else None,
            tool_type=tool_type,
            operation=operation,
            success=success,
            result=result,
            error=error,
            execution_time_ms=execution_time_ms,
        )

        result_doc = await self.collection.insert_one(
            tool_execution.dict(by_alias=True, exclude={"id"})
        )
        tool_execution.id = result_doc.inserted_id

        self.logger.info(
            "tool_execution_created",
            execution_id=str(tool_execution.id),
            tool_type=tool_type,
            success=success,
        )

        return tool_execution


class ContextEventRepository:
    """Repository for context event operations."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize context event repository.

        Args:
            db_manager: MongoDB manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("context_events")
        self.logger = logger.bind(component="context_event_repository")

    async def create_context_event(
        self,
        conversation_id: str,
        event_type: str,
        provider: str,
        token_count: int,
        limit: int,
        utilization_percent: float,
        truncation_strategy: Optional[str] = None,
        messages_removed: Optional[int] = None,
    ) -> ContextEventDocument:
        """Create a context event record.

        Args:
            conversation_id: Conversation ID
            event_type: Event type (check/truncation/overflow/warning)
            provider: LLM provider
            token_count: Current token count
            limit: Token limit
            utilization_percent: Utilization percentage
            truncation_strategy: Optional truncation strategy
            messages_removed: Optional number of messages removed

        Returns:
            Created context event document
        """
        context_event = ContextEventDocument(
            conversation_id=ObjectId(conversation_id),
            event_type=event_type,
            provider=provider,
            token_count=token_count,
            limit=limit,
            utilization_percent=utilization_percent,
            truncation_strategy=truncation_strategy,
            messages_removed=messages_removed,
        )

        result = await self.collection.insert_one(
            context_event.dict(by_alias=True, exclude={"id"})
        )
        context_event.id = result.inserted_id

        self.logger.info(
            "context_event_created",
            event_id=str(context_event.id),
            event_type=event_type,
            provider=provider,
        )

        return context_event


class ProviderMetricRepository:
    """Repository for provider metric operations."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize provider metric repository.

        Args:
            db_manager: MongoDB manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("provider_metrics")
        self.logger = logger.bind(component="provider_metric_repository")

    async def create_metric(
        self,
        provider: str,
        metric_type: str,
        value: float,
        unit: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderMetricDocument:
        """Create a provider metric record.

        Args:
            provider: LLM provider
            metric_type: Metric type (request/success/failure/latency/tokens/cost)
            value: Metric value
            unit: Optional unit
            metadata: Optional metadata

        Returns:
            Created provider metric document
        """
        metric = ProviderMetricDocument(
            provider=provider,
            metric_type=metric_type,
            value=value,
            unit=unit,
            metadata=metadata or {},
        )

        result = await self.collection.insert_one(metric.dict(by_alias=True, exclude={"id"}))
        metric.id = result.inserted_id

        return metric


class CostRecordRepository:
    """Repository for cost tracking operations."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize cost record repository.

        Args:
            db_manager: MongoDB manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("cost_records")
        self.logger = logger.bind(component="cost_record_repository")

    async def record_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        input_cost: float,
        output_cost: float,
        conversation_id: Optional[ObjectId] = None,
        message_id: Optional[ObjectId] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        category: Optional[str] = None,
        request_type: Optional[str] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostRecordDocument:
        """Record a cost event.

        Args:
            provider: LLM provider
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            input_cost: Cost for input tokens (USD)
            output_cost: Cost for output tokens (USD)
            conversation_id: Optional conversation ID
            message_id: Optional message ID
            user_id: Optional user ID
            project_id: Optional project ID
            category: Optional task category
            request_type: Optional request type
            success: Whether request was successful
            metadata: Optional additional metadata

        Returns:
            Created cost record document
        """
        cost_record = CostRecordDocument(
            conversation_id=conversation_id,
            message_id=message_id,
            user_id=user_id,
            project_id=project_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            category=category,
            request_type=request_type,
            success=success,
            metadata=metadata or {},
        )

        result = await self.collection.insert_one(
            cost_record.dict(by_alias=True, exclude={"id"})
        )
        cost_record.id = result.inserted_id

        self.logger.info(
            "cost_recorded",
            provider=provider,
            model=model,
            total_cost=cost_record.total_cost,
            total_tokens=cost_record.total_tokens,
        )

        return cost_record

    async def get_total_cost(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        provider: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> float:
        """Get total cost for given criteria.

        Args:
            user_id: Filter by user ID
            project_id: Filter by project ID
            provider: Filter by provider
            start_date: Filter from this date
            end_date: Filter until this date

        Returns:
            Total cost in USD
        """
        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id
        if project_id:
            query["project_id"] = project_id
        if provider:
            query["provider"] = provider
        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lte"] = end_date

        pipeline = [{"$match": query}, {"$group": {"_id": None, "total": {"$sum": "$total_cost"}}}]

        result = await self.collection.aggregate(pipeline).to_list(length=1)
        return result[0]["total"] if result else 0.0

    async def get_cost_breakdown(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get cost breakdown by provider and model.

        Args:
            user_id: Filter by user ID
            project_id: Filter by project ID
            start_date: Filter from this date
            end_date: Filter until this date

        Returns:
            List of cost breakdowns
        """
        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id
        if project_id:
            query["project_id"] = project_id
        if start_date or end_date:
            query["created_at"] = {}
            if start_date:
                query["created_at"]["$gte"] = start_date
            if end_date:
                query["created_at"]["$lte"] = end_date

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": {"provider": "$provider", "model": "$model"},
                    "total_cost": {"$sum": "$total_cost"},
                    "total_tokens": {"$sum": "$total_tokens"},
                    "request_count": {"$sum": 1},
                }
            },
            {"$sort": {"total_cost": -1}},
        ]

        results = await self.collection.aggregate(pipeline).to_list(length=None)
        return [
            {
                "provider": r["_id"]["provider"],
                "model": r["_id"]["model"],
                "total_cost": r["total_cost"],
                "total_tokens": r["total_tokens"],
                "request_count": r["request_count"],
            }
            for r in results
        ]


class BudgetRepository:
    """Repository for budget management operations."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize budget repository.

        Args:
            db_manager: MongoDB manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("budgets")
        self.logger = logger.bind(component="budget_repository")

    async def create_budget(
        self,
        budget_name: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        provider: Optional[str] = None,
        daily_limit: Optional[float] = None,
        weekly_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.95,
        alert_email: Optional[str] = None,
        alert_webhook: Optional[str] = None,
    ) -> BudgetDocument:
        """Create a new budget.

        Args:
            budget_name: Name of the budget
            user_id: Optional user ID
            project_id: Optional project ID
            provider: Optional provider (None = all providers)
            daily_limit: Optional daily spending limit (USD)
            weekly_limit: Optional weekly spending limit (USD)
            monthly_limit: Optional monthly spending limit (USD)
            warning_threshold: Warning threshold (0.0-1.0)
            critical_threshold: Critical threshold (0.0-1.0)
            alert_email: Optional email for alerts
            alert_webhook: Optional webhook URL for alerts

        Returns:
            Created budget document
        """
        budget = BudgetDocument(
            budget_name=budget_name,
            user_id=user_id,
            project_id=project_id,
            provider=provider,
            daily_limit=daily_limit,
            weekly_limit=weekly_limit,
            monthly_limit=monthly_limit,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            alert_email=alert_email,
            alert_webhook=alert_webhook,
        )

        result = await self.collection.insert_one(budget.dict(by_alias=True, exclude={"id"}))
        budget.id = result.inserted_id

        self.logger.info(
            "budget_created",
            budget_id=str(budget.id),
            budget_name=budget_name,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
        )

        return budget

    async def get_budget(self, budget_id: str) -> Optional[BudgetDocument]:
        """Get budget by ID.

        Args:
            budget_id: Budget ID

        Returns:
            Budget document or None
        """
        doc = await self.collection.find_one({"_id": ObjectId(budget_id)})
        if doc:
            return BudgetDocument(**doc)
        return None

    async def get_active_budgets(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> List[BudgetDocument]:
        """Get active budgets matching criteria.

        Args:
            user_id: Filter by user ID
            project_id: Filter by project ID
            provider: Filter by provider

        Returns:
            List of active budgets
        """
        query: Dict[str, Any] = {"is_active": True}
        if user_id:
            query["user_id"] = user_id
        if project_id:
            query["project_id"] = project_id
        if provider:
            query["provider"] = provider

        docs = await self.collection.find(query).to_list(length=None)
        return [BudgetDocument(**doc) for doc in docs]

    async def update_budget_spent(
        self,
        budget_id: str,
        daily_spent: Optional[float] = None,
        weekly_spent: Optional[float] = None,
        monthly_spent: Optional[float] = None,
    ) -> bool:
        """Update budget spent amounts.

        Args:
            budget_id: Budget ID
            daily_spent: New daily spent amount
            weekly_spent: New weekly spent amount
            monthly_spent: New monthly spent amount

        Returns:
            True if updated successfully
        """
        update_fields: Dict[str, Any] = {"updated_at": datetime.utcnow()}
        if daily_spent is not None:
            update_fields["daily_spent"] = daily_spent
        if weekly_spent is not None:
            update_fields["weekly_spent"] = weekly_spent
        if monthly_spent is not None:
            update_fields["monthly_spent"] = monthly_spent

        result = await self.collection.update_one(
            {"_id": ObjectId(budget_id)}, {"$set": update_fields}
        )
        return result.modified_count > 0

    async def update_alert_status(
        self,
        budget_id: str,
        warning_triggered: Optional[bool] = None,
        critical_triggered: Optional[bool] = None,
        budget_exceeded: Optional[bool] = None,
    ) -> bool:
        """Update budget alert status.

        Args:
            budget_id: Budget ID
            warning_triggered: Warning alert triggered
            critical_triggered: Critical alert triggered
            budget_exceeded: Budget exceeded

        Returns:
            True if updated successfully
        """
        update_fields: Dict[str, Any] = {"updated_at": datetime.utcnow()}
        if warning_triggered is not None:
            update_fields["warning_triggered"] = warning_triggered
        if critical_triggered is not None:
            update_fields["critical_triggered"] = critical_triggered
        if budget_exceeded is not None:
            update_fields["budget_exceeded"] = budget_exceeded

        result = await self.collection.update_one(
            {"_id": ObjectId(budget_id)}, {"$set": update_fields}
        )
        return result.modified_count > 0


class BudgetAlertRepository:
    """Repository for budget alert operations."""

    def __init__(self, db_manager: MongoDBManager):
        """Initialize budget alert repository.

        Args:
            db_manager: MongoDB manager instance
        """
        self.db_manager = db_manager
        self.collection = db_manager.get_collection("budget_alerts")
        self.logger = logger.bind(component="budget_alert_repository")

    async def create_alert(
        self,
        budget_id: ObjectId,
        alert_type: str,
        threshold_type: str,
        limit_usd: float,
        spent_usd: float,
        utilization_percent: float,
        provider: Optional[str] = None,
        notification_sent: bool = False,
        notification_channel: Optional[str] = None,
        notification_error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BudgetAlertDocument:
        """Create a budget alert.

        Args:
            budget_id: Budget ID
            alert_type: Alert type (warning/critical/exceeded)
            threshold_type: Threshold type (daily/weekly/monthly)
            limit_usd: Budget limit in USD
            spent_usd: Amount spent in USD
            utilization_percent: Budget utilization percentage
            provider: Optional provider
            notification_sent: Whether notification was sent
            notification_channel: Notification channel used
            notification_error: Notification error if any
            metadata: Optional additional metadata

        Returns:
            Created budget alert document
        """
        alert = BudgetAlertDocument(
            budget_id=budget_id,
            alert_type=alert_type,
            threshold_type=threshold_type,
            limit_usd=limit_usd,
            spent_usd=spent_usd,
            utilization_percent=utilization_percent,
            provider=provider,
            notification_sent=notification_sent,
            notification_channel=notification_channel,
            notification_error=notification_error,
            metadata=metadata or {},
        )

        result = await self.collection.insert_one(alert.dict(by_alias=True, exclude={"id"}))
        alert.id = result.inserted_id

        self.logger.warning(
            "budget_alert_created",
            budget_id=str(budget_id),
            alert_type=alert_type,
            threshold_type=threshold_type,
            utilization=utilization_percent,
        )

        return alert

    async def get_recent_alerts(
        self,
        budget_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[BudgetAlertDocument]:
        """Get recent budget alerts.

        Args:
            budget_id: Optional budget ID filter
            limit: Maximum number of alerts to return

        Returns:
            List of budget alerts
        """
        query: Dict[str, Any] = {}
        if budget_id:
            query["budget_id"] = ObjectId(budget_id)

        docs = await self.collection.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
        return [BudgetAlertDocument(**doc) for doc in docs]
