"""Core orchestration engine with fallback and collaboration support."""

import time
from typing import List, Optional, Dict, Any
from dataclasses import asdict
from src.models.schemas import (
    ChatRequest,
    ChatResponse,
    LLMProvider,
    RoutingDecision,
    FallbackEvent,
    QualityCheck,
    Message,
    LLMResponse,
    ToolResult,
)
from src.core.routing import TaskRouter
from src.core.quality import QualityChecker
from src.providers.base import BaseLLMProvider
from src.providers.claude_code import ClaudeCodeProvider
from src.providers.chatgpt import ChatGPTProvider
from src.providers.gemini import GeminiProvider
from src.providers.claude import ClaudeProvider
from src.providers.local_llm import LocalLLMProvider
from src.tools.manager import ToolManager
from src.core.config import settings
from src.core.context_manager import get_context_manager, ContextStatus, TruncationStrategy
from src.core.semantic_cache import get_semantic_cache
from src.core.rate_limiter import get_rate_limiter
from src.core.collaboration_manager import get_collaboration_manager, CollaborationManager, CollaborationPlan
from src.core.conversation_state import get_state_manager, ConversationStateManager
from src.core.registry import get_provider_registry, ProviderRegistry
from src.database.mongodb import get_mongodb_manager, MongoDBManager
from src.database.repositories import (
    ConversationRepository,
    MessageRepository,
    ToolExecutionRepository,
    ContextEventRepository,
)
from src.core.budget_manager import BudgetManager
import structlog

# Import metrics if available
try:
    from src.api.main import (
        context_window_status,
        context_window_truncations,
        context_window_tokens,
        context_window_utilization,
        rate_limit_counter,
    )
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = structlog.get_logger()


class Orchestrator:
    """Main orchestration engine for LLM routing and task execution."""

    def __init__(self, enable_cache: bool = True, enable_persistence: bool = True) -> None:
        """Initialize the orchestrator.

        Args:
            enable_cache: Enable semantic caching (default: True)
            enable_persistence: Enable conversation persistence to MongoDB (default: True)
        """
        self.logger = logger.bind(component="orchestrator")
        self.router = TaskRouter()
        self.quality_checker = QualityChecker()
        self.tool_manager = ToolManager()
        self.context_manager = get_context_manager()
        self.rate_limiter = get_rate_limiter()
        self.collaboration_manager = get_collaboration_manager()
        self.state_manager: ConversationStateManager = get_state_manager()

        # Initialize semantic cache if enabled
        self.enable_cache = enable_cache
        self.cache = None
        if enable_cache:
            try:
                self.cache = get_semantic_cache(
                    similarity_threshold=getattr(settings, "cache_similarity_threshold", 0.85),
                    default_ttl=getattr(settings, "cache_default_ttl", 3600),
                )
                self.logger.info("semantic_cache_enabled")
            except Exception as e:
                self.logger.warning("semantic_cache_initialization_failed", error=str(e))
                self.enable_cache = False

        # Initialize MongoDB persistence (async, done in process_request)
        self.enable_persistence = enable_persistence
        self.db_manager: Optional[MongoDBManager] = None
        self.conv_repo: Optional[ConversationRepository] = None
        self.msg_repo: Optional[MessageRepository] = None
        self.tool_exec_repo: Optional[ToolExecutionRepository] = None
        self.context_event_repo: Optional[ContextEventRepository] = None
        self.budget_manager: Optional[BudgetManager] = None

        # Initialize providers via registry (falls back to hardcoded if config missing)
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.provider_registry: ProviderRegistry = get_provider_registry()
        self._init_providers()

    def _get_rate_limiter_provider_name(self, provider: LLMProvider) -> str:
        """Map LLMProvider enum to rate limiter provider name.

        Args:
            provider: LLMProvider enum value

        Returns:
            Rate limiter provider name
        """
        # Map LLMProvider enum values to rate limiter provider names
        mapping = {
            LLMProvider.CHATGPT: "openai",
            LLMProvider.CLAUDE: "anthropic",
            LLMProvider.CLAUDE_CODE: "anthropic",
            LLMProvider.GEMINI: "google",
            LLMProvider.LOCAL: "local",
        }
        return mapping.get(provider, provider.value)

    def _init_providers(self) -> None:
        """Initialize providers from registry config; fall back to hardcoded defaults."""
        registry_providers = self.provider_registry.active_providers()

        if registry_providers:
            self.providers = registry_providers
            self.logger.info(
                "providers_loaded_from_registry",
                count=len(registry_providers),
                names=[p.value for p in registry_providers],
            )
            return

        # Registry config missing or empty — use hardcoded defaults
        self.logger.warning("registry_empty_using_defaults")
        if settings.anthropic_api_key:
            self.providers[LLMProvider.CLAUDE_CODE] = ClaudeCodeProvider()
            self.providers[LLMProvider.CLAUDE] = ClaudeProvider()
        if settings.openai_api_key:
            self.providers[LLMProvider.CHATGPT] = ChatGPTProvider()
        if settings.google_api_key:
            self.providers[LLMProvider.GEMINI] = GeminiProvider()
        if settings.local_llm_enabled:
            self.providers[LLMProvider.LOCAL] = LocalLLMProvider()
        self.logger.info("default_providers_initialized", count=len(self.providers))

    async def _init_persistence(self) -> None:
        """Initialize MongoDB persistence layer (async)."""
        if not self.enable_persistence or self.db_manager is not None:
            return

        try:
            self.db_manager = await get_mongodb_manager()
            self.conv_repo = ConversationRepository(self.db_manager)
            self.msg_repo = MessageRepository(self.db_manager)
            self.tool_exec_repo = ToolExecutionRepository(self.db_manager)
            self.context_event_repo = ContextEventRepository(self.db_manager)
            self.budget_manager = BudgetManager(self.db_manager)
            self.logger.info("mongodb_persistence_initialized")
        except Exception as e:
            self.logger.error("mongodb_initialization_failed", error=str(e))
            self.enable_persistence = False

    async def process_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request with routing, fallback, and tool execution.

        Args:
            request: Chat request

        Returns:
            ChatResponse
        """
        start_time = time.time()
        fallback_events: List[FallbackEvent] = []

        try:
            # Initialize persistence layer if enabled
            await self._init_persistence()

            # Route the request
            routing_decision = self.router.route(
                message=request.message,
                explicit_provider=request.explicit_provider,
                enable_collaboration=request.enable_collaboration,
            )

            self.logger.info(
                "request_routed",
                provider=routing_decision.provider,
                category=routing_decision.category,
                confidence=routing_decision.confidence,
            )

            # Create conversation in database
            conversation_id = None
            if self.enable_persistence and self.conv_repo:
                try:
                    conversation = await self.conv_repo.create_conversation(
                        provider_used=routing_decision.provider.value,
                        routing_decision={
                            "provider": routing_decision.provider.value,
                            "category": routing_decision.category.value,
                            "confidence": routing_decision.confidence,
                            "reasoning": routing_decision.reasoning or "",
                            "requires_collaboration": routing_decision.requires_collaboration,
                        },
                        title=request.message[:100],  # First 100 chars as title
                    )
                    conversation_id = str(conversation.id)
                    self.logger.info("conversation_persisted", conversation_id=conversation_id)
                except Exception as e:
                    self.logger.error("conversation_persistence_failed", error=str(e))

            # Save user message
            if self.enable_persistence and self.msg_repo and conversation_id:
                try:
                    await self.msg_repo.create_message(
                        conversation_id=conversation_id,
                        role="user",
                        content=request.message,
                    )
                except Exception as e:
                    self.logger.error("message_persistence_failed", error=str(e))

            # Check cache if enabled (skip for tool-enabled requests)
            cache_hit = False
            if self.enable_cache and self.cache and not request.enable_tools:
                messages = [Message(role="user", content=request.message)]
                cached_response = self.cache.get(
                    query=request.message,
                    messages=messages,
                    provider=routing_decision.provider,
                )

                if cached_response:
                    cache_hit = True
                    execution_time = time.time() - start_time

                    self.logger.info(
                        "cache_hit_returned",
                        provider=routing_decision.provider.value,
                        execution_time=f"{execution_time:.3f}s",
                    )

                    return ChatResponse(
                        message=cached_response.content,
                        provider=routing_decision.provider,
                        routing_decision=routing_decision,
                        execution_time=execution_time,
                        tool_results=[],
                        fallback_events=[],
                    )

            # Handle collaboration if needed
            if routing_decision.requires_collaboration and routing_decision.collaboration_plan:
                return await self._handle_collaboration(
                    request, routing_decision, start_time
                )

            # Prepare messages
            messages = [Message(role="user", content=request.message)]

            # Get available tools if enabled
            tools = None
            if request.enable_tools:
                tools = self.tool_manager.get_tool_definitions()

            # Try primary provider with fallback chain
            response, provider_used, fallback_events = await self._execute_with_fallback(
                messages, routing_decision, tools, conversation_id
            )

            # Execute tool calls if any
            tool_results: List[ToolResult] = []
            if response.tool_calls:
                tool_results = await self.tool_manager.execute_tools(response.tool_calls)

                # Persist tool executions
                if self.enable_persistence and self.tool_exec_repo and conversation_id:
                    for tool_result in tool_results:
                        try:
                            await self.tool_exec_repo.create_tool_execution(
                                conversation_id=conversation_id,
                                tool_type=tool_result.tool_type.value,
                                operation=tool_result.operation,
                                success=tool_result.success,
                                execution_time_ms=int(tool_result.execution_time * 1000) if tool_result.execution_time is not None else 0,
                                result=tool_result.result if tool_result.success else None,
                                error=tool_result.error if not tool_result.success else None,
                            )
                        except Exception as e:
                            self.logger.error("tool_execution_persistence_failed", error=str(e))

                # If tools were executed, get final response from LLM
                messages.append(
                    Message(
                        role="assistant",
                        content=response.content,
                        provider=provider_used,
                    )
                )

                # Add tool results to conversation
                tool_results_text = "\n\n".join(
                    [
                        f"Tool: {tr.tool_type.value}\nOperation: {tr.operation}\n"
                        f"Success: {tr.success}\nResult: {tr.result}"
                        for tr in tool_results
                    ]
                )
                messages.append(
                    Message(role="user", content=f"Tool results:\n{tool_results_text}")
                )

                # Get final response after tool execution
                final_response, _, _ = await self._execute_with_fallback(
                    messages, routing_decision, None, conversation_id
                )
                response = final_response

            # Quality check
            quality_check = None
            if settings.quality_check_enabled:
                quality_check = self.quality_checker.check(response)
                self.logger.info("quality_check_completed", passed=quality_check.passed)

            # Cache response if enabled and not from cache (skip if tools were used)
            if (
                self.enable_cache
                and self.cache
                and not cache_hit
                and not tool_results
                and quality_check
                and quality_check.passed
            ):
                self.cache.set(
                    query=request.message,
                    messages=messages,
                    response=response,
                    category=routing_decision.category.value,
                )

            execution_time = time.time() - start_time

            # Persist assistant response
            if self.enable_persistence and self.msg_repo and conversation_id:
                try:
                    await self.msg_repo.create_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=response.content,
                        provider=provider_used.value,
                        model=getattr(response, "model", None),
                        token_count=getattr(response, "tokens_used", None),
                        cost_usd=getattr(response, "cost", None),
                        metadata={
                            "cache_hit": cache_hit,
                            "quality_passed": quality_check.passed if quality_check else None,
                            "tool_calls": len(tool_results) if tool_results else 0,
                        },
                    )
                except Exception as e:
                    self.logger.error("assistant_message_persistence_failed", error=str(e))

            # Update conversation metrics
            if self.enable_persistence and self.conv_repo and conversation_id:
                try:
                    from src.database.models import ConversationMetrics

                    metrics = ConversationMetrics(
                        message_count=2 + len(tool_results),  # user + assistant + tool results
                        total_tokens=getattr(response, "tokens_used", 0),
                        total_cost_usd=getattr(response, "cost", 0.0),
                        execution_time_ms=int(execution_time * 1000),
                    )
                    await self.conv_repo.update_conversation_metrics(
                        conversation_id, metrics
                    )
                except Exception as e:
                    self.logger.error("conversation_metrics_update_failed", error=str(e))

            # Track cost and check budgets
            if self.enable_persistence and self.budget_manager:
                try:
                    # Extract token counts - handle case where we only have total tokens
                    tokens_used = getattr(response, "tokens_used", None)
                    if tokens_used is None:
                        tokens_used = 0
                    # Estimate input/output split if not available (typical 60/40 split)
                    input_tokens = int(tokens_used * 0.6)
                    output_tokens = int(tokens_used * 0.4)

                    # Get model name from metadata or use default
                    model_name = None
                    if hasattr(response, "metadata") and response.metadata:
                        model_name = response.metadata.get("model")

                    # Fallback to provider default model if not specified
                    if not model_name:
                        provider_obj = self.providers.get(provider_used)
                        if provider_obj and hasattr(provider_obj, "model"):
                            model_name = provider_obj.model
                        else:
                            model_name = "unknown"

                    # Record cost and check budgets
                    cost_result = await self.budget_manager.record_and_check_cost(
                        provider=provider_used.value,
                        model=model_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        conversation_id=conversation_id,
                        message_id=None,  # We don't have message ID here yet
                        user_id=request.context.get("user_id") if request.context else None,
                        project_id=request.context.get("project_id") if request.context else None,
                        category=routing_decision.category.value,
                        request_type="chat",
                        success=quality_check.passed if quality_check else True,
                    )

                    # Log budget alerts if any
                    if cost_result["budget_status"]["alerts_triggered"]:
                        self.logger.warning(
                            "budget_alerts_triggered",
                            alerts=cost_result["budget_status"]["alerts_triggered"],
                            total_cost=cost_result["total_cost"],
                        )

                except Exception as e:
                    self.logger.error("cost_tracking_failed", error=str(e))

            return ChatResponse(
                message=response.content,
                provider=provider_used,
                routing_decision=routing_decision,
                tool_results=tool_results,
                fallback_events=fallback_events,
                quality_check=quality_check,
                execution_time=execution_time,
            )

        except Exception as e:
            self.logger.error("request_processing_failed", error=str(e))
            raise

    async def _execute_with_fallback(
        self,
        messages: List[Message],
        routing_decision: RoutingDecision,
        tools: Optional[List[Dict[str, Any]]],
        conversation_id: Optional[str] = None,
    ) -> tuple[LLMResponse, LLMProvider, List[FallbackEvent]]:
        """Execute LLM request with fallback chain.

        Args:
            messages: Conversation messages
            routing_decision: Routing decision
            tools: Available tools
            conversation_id: Optional conversation ID for persistence

        Returns:
            Tuple of (response, provider_used, fallback_events)
        """
        fallback_events: List[FallbackEvent] = []
        providers_to_try = [routing_decision.provider] + routing_decision.fallback_providers

        last_error: Optional[Exception] = None

        # Check context window and truncate if needed for primary provider
        provider = routing_decision.provider
        status, token_count, limit = self.context_manager.check_context_status(
            messages, provider
        )

        utilization_pct = (token_count / limit) * 100

        self.logger.info(
            "context_window_check",
            provider=provider.value,
            token_count=token_count,
            limit=limit,
            status=status.value,
            utilization=f"{utilization_pct:.1f}%",
        )

        # Record context metrics
        if METRICS_AVAILABLE:
            context_window_status.labels(
                provider=provider.value, status=status.value
            ).inc()
            context_window_tokens.labels(provider=provider.value).set(token_count)
            context_window_utilization.labels(provider=provider.value).set(utilization_pct)

        # Persist context event
        if self.enable_persistence and self.context_event_repo and conversation_id:
            try:
                event_type = {
                    ContextStatus.OK: "check",
                    ContextStatus.WARNING: "warning",
                    ContextStatus.OVERFLOW: "overflow",
                }.get(status, "check")

                await self.context_event_repo.create_context_event(
                    conversation_id=conversation_id,
                    event_type=event_type,
                    provider=provider.value,
                    token_count=token_count,
                    limit=limit,
                    utilization_percent=utilization_pct,
                )
            except Exception as e:
                self.logger.error("context_event_persistence_failed", error=str(e))

        # Truncate if approaching or exceeding limits
        messages_removed = 0
        if status in [ContextStatus.WARNING, ContextStatus.OVERFLOW]:
            # Reserve tokens for response
            reserve_tokens = self.context_manager.estimate_completion_tokens(provider)
            original_message_count = len(messages)
            messages, was_truncated = self.context_manager.truncate_messages(
                messages, provider, reserve_tokens=reserve_tokens
            )
            messages_removed = original_message_count - len(messages)

            if was_truncated:
                self.logger.warning(
                    "context_truncated",
                    provider=provider.value,
                    original_tokens=token_count,
                    new_message_count=len(messages),
                )

                # Record truncation metric
                if METRICS_AVAILABLE:
                    context_window_truncations.labels(
                        provider=provider.value,
                        strategy=TruncationStrategy.SLIDING_WINDOW.value,
                    ).inc()

                # Persist truncation event
                if self.enable_persistence and self.context_event_repo and conversation_id:
                    try:
                        await self.context_event_repo.create_context_event(
                            conversation_id=conversation_id,
                            event_type="truncation",
                            provider=provider.value,
                            token_count=token_count,
                            limit=limit,
                            utilization_percent=utilization_pct,
                            truncation_strategy=TruncationStrategy.SLIDING_WINDOW.value,
                            messages_removed=messages_removed,
                        )
                    except Exception as e:
                        self.logger.error("truncation_event_persistence_failed", error=str(e))

        for provider in providers_to_try:
            if provider not in self.providers:
                self.logger.warning("provider_not_available", provider=provider)
                continue

            # Check rate limit before making request
            rate_limiter_provider = self._get_rate_limiter_provider_name(provider)
            if not self.rate_limiter.check_limit(rate_limiter_provider):
                self.logger.warning(
                    "rate_limit_exceeded_skipping_provider",
                    provider=provider.value,
                    rate_limiter_provider=rate_limiter_provider
                )

                # Record rate limit metric
                if METRICS_AVAILABLE:
                    rate_limit_counter.labels(provider=provider.value).inc()

                # If rate limited, treat it as an error and try next provider
                last_error = Exception(f"Rate limit exceeded for {provider.value}")

                # Log fallback event if not first provider
                if provider != routing_decision.provider:
                    fallback_events.append(
                        FallbackEvent(
                            from_provider=providers_to_try[
                                providers_to_try.index(provider) - 1
                            ],
                            to_provider=provider,
                            reason=f"Rate limit exceeded for {provider.value}",
                            category=routing_decision.category,
                        )
                    )
                continue

            try:
                provider_instance = self.providers[provider]
                response = await provider_instance.complete(messages=messages, tools=tools)

                # Check quality if not first provider (fallback occurred)
                if provider != routing_decision.provider:
                    quality = self.quality_checker.check(response)
                    if not quality.passed:
                        self.logger.warning(
                            "fallback_quality_check_failed",
                            provider=provider,
                            score=quality.score,
                        )
                        continue

                return response, provider, fallback_events

            except Exception as e:
                self.logger.error("provider_failed", provider=provider, error=str(e))
                last_error = e

                # Auto-detect daily quota exhaustion from 429 errors
                error_str = str(e).lower()
                if "429" in error_str or "quota exceeded" in error_str or "quota_exceeded" in error_str:
                    self.logger.warning(
                        "daily_quota_exhaustion_detected",
                        provider=provider.value,
                        error_snippet=str(e)[:200]
                    )
                    # Mark provider as exhausted for today
                    rate_limiter_provider = self._get_rate_limiter_provider_name(provider)
                    # Get current quota limit to set as "used"
                    stats = self.rate_limiter.get_provider_stats(rate_limiter_provider)
                    if "daily_limit" in stats:
                        self.rate_limiter.daily_quotas.set_quota_used(
                            rate_limiter_provider,
                            stats["daily_limit"]  # Set to max (exhausted)
                        )
                        self.logger.info(
                            "daily_quota_auto_updated",
                            provider=rate_limiter_provider,
                            used=stats["daily_limit"],
                            limit=stats["daily_limit"]
                        )

                # Log fallback event
                if provider != routing_decision.provider:
                    fallback_events.append(
                        FallbackEvent(
                            from_provider=providers_to_try[
                                providers_to_try.index(provider) - 1
                            ],
                            to_provider=provider,
                            reason=str(e),
                            category=routing_decision.category,
                        )
                    )

        # All providers failed
        raise Exception(f"All providers failed. Last error: {last_error}")

    async def _handle_collaboration(
        self,
        request: ChatRequest,
        routing_decision: RoutingDecision,
        start_time: float,
    ) -> ChatResponse:
        """Handle multi-LLM collaboration using advanced collaboration patterns.

        Args:
            request: Chat request
            routing_decision: Routing decision with collaboration plan
            start_time: Request start time

        Returns:
            ChatResponse
        """
        if not routing_decision.collaboration_plan:
            raise ValueError("Collaboration plan is required")

        # For backward compatibility: convert simple list of providers to tasks
        # This handles old-style collaboration_plan from router
        from src.core.collaboration_manager import AgentTask, CollaborationPattern

        tasks = []
        for idx, provider in enumerate(routing_decision.collaboration_plan):
            task = AgentTask(
                agent=provider,
                instruction=(
                    f"Complete step {idx + 1} of multi-agent task: {request.message}"
                ),
                task_id=f"step_{idx + 1}",
                depends_on=[f"step_{idx}"] if idx > 0 else [],
            )
            tasks.append(task)

        # Create collaboration plan (default to sequential pattern)
        plan = CollaborationPlan(
            pattern=CollaborationPattern.SEQUENTIAL,
            tasks=tasks,
            original_request=request.message,
        )

        self.logger.info(
            "collaboration_started",
            pattern=plan.pattern.value,
            task_count=len(plan.tasks),
        )

        # Execute collaboration plan
        results = await self.collaboration_manager.execute_plan(plan, self.providers)

        # Build final response from all task results
        collaboration_steps = []
        accumulated_response = ""

        for task in plan.tasks:
            if task.result:
                collaboration_steps.append(
                    {
                        "step": int(task.task_id.split("_")[1]),
                        "provider": task.agent.value,
                        "response": task.result.content,
                        "tool_calls": len(task.result.tool_calls) if task.result.tool_calls else 0,
                        "status": task.status,
                        "execution_time": (
                            (task.completed_at - task.started_at).total_seconds()
                            if task.completed_at and task.started_at
                            else 0
                        ),
                    }
                )
                accumulated_response += f"\n\n[{task.agent.value}]: {task.result.content}"

        execution_time = time.time() - start_time

        # Estimate handoff latency
        handoff_latency = self.collaboration_manager.estimate_handoff_latency(plan)

        self.logger.info(
            "collaboration_completed",
            pattern=plan.pattern.value,
            total_steps=len(plan.tasks),
            successful_steps=sum(1 for t in plan.tasks if t.status == "completed"),
            total_time=f"{execution_time:.2f}s",
            estimated_handoff_latency=f"{handoff_latency:.2f}s",
        )

        return ChatResponse(
            message=accumulated_response.strip(),
            provider=routing_decision.collaboration_plan[-1],  # Last provider
            routing_decision=routing_decision,
            collaboration_steps=collaboration_steps,
            execution_time=execution_time,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers, tools, and cache.

        Returns:
            Health status dict
        """
        provider_health: Dict[str, Dict[str, Any]] = {}

        for provider, instance in self.providers.items():
            try:
                is_healthy = await instance.health_check()
                provider_health[provider.value] = {
                    "healthy": is_healthy,
                    "configured": True
                }
            except Exception as e:
                self.logger.error("health_check_failed", provider=provider, error=str(e))
                provider_health[provider.value] = {
                    "healthy": False,
                    "configured": True,
                    "error": str(e)
                }

        tool_health = await self.tool_manager.health_check()

        # Check cache health
        cache_health = False
        cache_metrics = None
        if self.enable_cache and self.cache:
            try:
                cache_health = self.cache.health_check()
                if cache_health:
                    cache_metrics = self.cache.get_metrics()
            except Exception as e:
                self.logger.error("cache_health_check_failed", error=str(e))

        # Check database health
        database_health = False
        if self.enable_persistence:
            try:
                await self._init_persistence()
                if self.db_manager:
                    database_health = await self.db_manager.health_check()
            except Exception as e:
                self.logger.error("database_health_check_failed", error=str(e))

        overall_status = "healthy"
        provider_statuses = [p["healthy"] for p in provider_health.values()]
        if not any(provider_statuses) or (self.enable_persistence and not database_health):
            overall_status = "unhealthy"
        elif not all(provider_statuses):
            overall_status = "degraded"

        return {
            "status": overall_status,
            "providers": provider_health,
            "tools": tool_health,
            "cache": {
                "enabled": self.enable_cache,
                "healthy": cache_health,
                "metrics": asdict(cache_metrics) if cache_metrics else None,
            },
            "database": {
                "enabled": self.enable_persistence,
                "healthy": database_health,
            },
        }
