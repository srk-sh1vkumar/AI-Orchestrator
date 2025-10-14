"""Core orchestration engine with fallback and collaboration support."""

import time
from typing import List, Optional, Dict, Any
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
import structlog

logger = structlog.get_logger()


class Orchestrator:
    """Main orchestration engine for LLM routing and task execution."""

    def __init__(self) -> None:
        """Initialize the orchestrator."""
        self.logger = logger.bind(component="orchestrator")
        self.router = TaskRouter()
        self.quality_checker = QualityChecker()
        self.tool_manager = ToolManager()

        # Initialize providers
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        """Initialize available LLM providers."""
        if settings.anthropic_api_key:
            self.providers[LLMProvider.CLAUDE_CODE] = ClaudeCodeProvider()
            self.providers[LLMProvider.CLAUDE] = ClaudeProvider()
            self.logger.info("claude_providers_initialized")

        if settings.openai_api_key:
            self.providers[LLMProvider.CHATGPT] = ChatGPTProvider()
            self.logger.info("chatgpt_provider_initialized")

        if settings.google_api_key:
            self.providers[LLMProvider.GEMINI] = GeminiProvider()
            self.logger.info("gemini_provider_initialized")

        if settings.local_llm_enabled:
            self.providers[LLMProvider.LOCAL] = LocalLLMProvider()
            self.logger.info("local_llm_provider_initialized")

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
                messages, routing_decision, tools
            )

            # Execute tool calls if any
            tool_results: List[ToolResult] = []
            if response.tool_calls:
                tool_results = await self.tool_manager.execute_tools(response.tool_calls)

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
                    messages, routing_decision, None
                )
                response = final_response

            # Quality check
            quality_check = None
            if settings.quality_check_enabled:
                quality_check = self.quality_checker.check(response)
                self.logger.info("quality_check_completed", passed=quality_check.passed)

            execution_time = time.time() - start_time

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
    ) -> tuple[LLMResponse, LLMProvider, List[FallbackEvent]]:
        """Execute LLM request with fallback chain.

        Args:
            messages: Conversation messages
            routing_decision: Routing decision
            tools: Available tools

        Returns:
            Tuple of (response, provider_used, fallback_events)
        """
        fallback_events: List[FallbackEvent] = []
        providers_to_try = [routing_decision.provider] + routing_decision.fallback_providers

        last_error: Optional[Exception] = None

        for provider in providers_to_try:
            if provider not in self.providers:
                self.logger.warning("provider_not_available", provider=provider)
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
        """Handle multi-LLM collaboration.

        Args:
            request: Chat request
            routing_decision: Routing decision with collaboration plan
            start_time: Request start time

        Returns:
            ChatResponse
        """
        if not routing_decision.collaboration_plan:
            raise ValueError("Collaboration plan is required")

        self.logger.info(
            "collaboration_started", providers=routing_decision.collaboration_plan
        )

        collaboration_steps: List[Dict[str, Any]] = []
        messages = [Message(role="user", content=request.message)]
        accumulated_context = ""

        for idx, provider in enumerate(routing_decision.collaboration_plan):
            if provider not in self.providers:
                self.logger.warning("collaboration_provider_unavailable", provider=provider)
                continue

            step_start = time.time()

            # Adjust prompt based on collaboration step
            if idx > 0:
                step_message = (
                    f"Previous step results:\n{accumulated_context}\n\n"
                    f"Now complete your part: {request.message}"
                )
                messages = [Message(role="user", content=step_message)]

            try:
                provider_instance = self.providers[provider]
                tools = self.tool_manager.get_tool_definitions() if request.enable_tools else None

                response = await provider_instance.complete(messages=messages, tools=tools)

                # Execute any tool calls
                tool_results: List[ToolResult] = []
                if response.tool_calls:
                    tool_results = await self.tool_manager.execute_tools(response.tool_calls)

                step_time = time.time() - step_start

                collaboration_steps.append(
                    {
                        "step": idx + 1,
                        "provider": provider.value,
                        "response": response.content,
                        "tool_calls": len(response.tool_calls),
                        "tool_results": len(tool_results),
                        "execution_time": step_time,
                    }
                )

                # Accumulate context for next step
                accumulated_context += f"\n\n[{provider.value}]: {response.content}"

                self.logger.info(
                    "collaboration_step_completed",
                    step=idx + 1,
                    provider=provider,
                    time=step_time,
                )

            except Exception as e:
                self.logger.error("collaboration_step_failed", provider=provider, error=str(e))
                raise

        execution_time = time.time() - start_time

        return ChatResponse(
            message=accumulated_context.strip(),
            provider=routing_decision.collaboration_plan[-1],  # Last provider
            routing_decision=routing_decision,
            collaboration_steps=collaboration_steps,
            execution_time=execution_time,
        )

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers and tools.

        Returns:
            Health status dict
        """
        provider_health: Dict[str, bool] = {}

        for provider, instance in self.providers.items():
            try:
                is_healthy = await instance.health_check()
                provider_health[provider.value] = is_healthy
            except Exception as e:
                self.logger.error("health_check_failed", provider=provider, error=str(e))
                provider_health[provider.value] = False

        tool_health = await self.tool_manager.health_check()

        overall_status = "healthy"
        if not any(provider_health.values()):
            overall_status = "unhealthy"
        elif not all(provider_health.values()):
            overall_status = "degraded"

        return {
            "status": overall_status,
            "providers": provider_health,
            "tools": tool_health,
        }
