"""DeepSeek-Coder provider integration (Ollama)."""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
import httpx
from src.providers.base import BaseLLMProvider
from src.models.schemas import LLMResponse, LLMProvider, Message, ToolCall, StreamChunk
from src.core.config import settings
from src.core.tracing import trace_llm_request, set_span_error, add_event_to_current_span


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek-Coder provider for code generation and analysis."""

    def __init__(self) -> None:
        """Initialize DeepSeek provider."""
        super().__init__(LLMProvider.DEEPSEEK)
        self.base_url = settings.local_llm_base_url  # Uses same Ollama instance
        self.model = "deepseek-coder:6.7b"
        self.timeout = settings.local_llm_timeout

    async def _complete_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
    ) -> LLMResponse:
        """Generate a completion using DeepSeek-Coder.

        Args:
            messages: Conversation messages
            tools: Available tools (not supported by Ollama)
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            LLMResponse
        """
        start_time = time.time()

        # Enhancement 005: OpenTelemetry distributed tracing
        with trace_llm_request("deepseek", self.model) as span:
            try:
                # Add tracing attributes
                span.set_attribute("llm.temperature", temperature)
                span.set_attribute("llm.max_tokens", max_tokens)
                span.set_attribute("llm.message_count", len(messages))

                # Format messages for Ollama
                formatted_messages = self.format_messages(messages)

                # Add code-specialized system message
                formatted_messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": """You are DeepSeek-Coder, a specialized AI for code generation and analysis:
                        - Write clean, production-ready code
                        - Follow language-specific best practices
                        - Include inline comments for complex logic
                        - Optimize for performance and maintainability
                        - Explain technical decisions
                        - Debug code issues thoroughly
                        - Suggest improvements and refactoring
                        - Focus on code quality and security

                        Provide concise, actionable code solutions.""",
                    },
                )

                add_event_to_current_span("deepseek_api_request_start")
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json={
                            "model": self.model,
                            "messages": formatted_messages,
                            "stream": False,
                            "options": {
                                "temperature": temperature,
                                "num_predict": max_tokens,
                            },
                        },
                    )

                    response.raise_for_status()
                    data = response.json()
                add_event_to_current_span("deepseek_api_request_complete")

                execution_time = time.time() - start_time

                content = data.get("message", {}).get("content", "")

                # Extract token usage from Ollama response
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                total_tokens = prompt_tokens + completion_tokens if (prompt_tokens and completion_tokens) else None

                # Add tracing metrics
                if prompt_tokens:
                    span.set_attribute("llm.tokens.input", prompt_tokens)
                if completion_tokens:
                    span.set_attribute("llm.tokens.output", completion_tokens)
                if total_tokens:
                    span.set_attribute("llm.tokens.total", total_tokens)
                span.set_attribute("llm.execution_time_ms", int(execution_time * 1000))
                span.set_attribute("llm.tool_calls_count", 0)

                self.logger.info(
                    "completion_generated",
                    time=execution_time,
                    model=self.model,
                    tokens=total_tokens,
                )

                return LLMResponse(
                    provider=self.provider,
                    content=content,
                    tool_calls=[],
                    tokens_used=total_tokens,
                    execution_time=execution_time,
                    metadata={
                        "model": self.model,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                    },
                )

            except httpx.TimeoutException as e:
                set_span_error(e)
                span.set_attribute("error.type", "TimeoutException")
                span.set_attribute("error.message", "Request timeout")
                self.logger.error("completion_timeout", model=self.model)
                raise
            except Exception as e:
                set_span_error(e)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                self.logger.error("completion_failed", error=str(e), model=self.model)
                raise


    async def _stream_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion using fallback implementation.

        This provider uses the fallback streaming which calls the blocking API
        and simulates streaming by chunking the response.

        Args:
            messages: Conversation messages
            tools: Available tools
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            StreamChunk: Simulated incremental response chunks
        """
        async for chunk in self._stream_impl_fallback(messages, tools, temperature, max_tokens):
            yield chunk

    async def health_check(self) -> bool:
        """Check if DeepSeek model is available in Ollama.

        Returns:
            True if healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return False

                # Check if deepseek-coder model is installed
                data = response.json()
                models = data.get("models", [])
                has_deepseek = any(
                    "deepseek-coder" in model.get("name", "").lower()
                    for model in models
                )

                if not has_deepseek:
                    self.logger.warning(
                        "deepseek_model_not_found",
                        message="deepseek-coder:6.7b not found in Ollama models"
                    )

                return has_deepseek
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False
