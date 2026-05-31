"""vLLM provider integration for high-performance local LLM inference.

Enhancement 017: Production Architecture - Phase 1.

vLLM provides OpenAI-compatible API with optimized inference performance.
"""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
import httpx
from src.providers.base import BaseLLMProvider
from src.models.schemas import LLMResponse, LLMProvider, Message, ToolCall, StreamChunk
from src.core.config import settings
from src.core.tracing import trace_llm_request, set_span_error, add_event_to_current_span


class VLLMProvider(BaseLLMProvider):
    """vLLM provider for high-performance local LLM inference.

    vLLM provides:
    - OpenAI-compatible API
    - Optimized inference with PagedAttention
    - Native streaming support
    - Multi-model serving
    - GPU acceleration
    """

    def __init__(self) -> None:
        """Initialize vLLM provider."""
        super().__init__(LLMProvider.VLLM)
        self.base_url = settings.vllm_base_url or "http://localhost:8001"
        self.model = settings.vllm_model or "meta-llama/Llama-2-13b-chat-hf"
        self.timeout = settings.vllm_timeout or 120.0
        self.max_retries = 3

    async def _complete_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
    ) -> LLMResponse:
        """Generate a completion using vLLM.

        Args:
            messages: Conversation messages
            tools: Available tools (not supported by vLLM currently)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPStatusError: If API returns error status
        """
        start_time = time.time()

        # Enhancement 005: OpenTelemetry distributed tracing
        with trace_llm_request("vllm", self.model) as span:
            try:
                # Add tracing attributes
                span.set_attribute("llm.temperature", temperature)
                span.set_attribute("llm.max_tokens", max_tokens)
                span.set_attribute("llm.message_count", len(messages))
                span.set_attribute("llm.backend", "vllm")

                # Format messages for vLLM (OpenAI-compatible format)
                formatted_messages = self.format_messages(messages)

                # Add system message for general-purpose tasks
                if not any(msg["role"] == "system" for msg in formatted_messages):
                    formatted_messages.insert(
                        0,
                        {
                            "role": "system",
                            "content": """You are a helpful, accurate, and efficient AI assistant.
                            - Provide clear and concise responses
                            - Focus on accuracy and correctness
                            - Explain complex concepts simply
                            - Follow best practices and conventions
                            - Adapt your response style to the task

                            Deliver high-quality, actionable responses.""",
                        },
                    )

                add_event_to_current_span("vllm_api_request_start")

                # vLLM uses OpenAI-compatible chat completions endpoint
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/v1/chat/completions",
                        json={
                            "model": self.model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "stream": False,
                        },
                        headers={
                            "Content-Type": "application/json",
                        },
                    )

                    response.raise_for_status()
                    data = response.json()

                add_event_to_current_span("vllm_api_request_complete")

                execution_time = time.time() - start_time

                # Extract response from OpenAI-compatible format
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content", "")

                # Extract token usage
                usage = data.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

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
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
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
                        "backend": "vllm",
                        "finish_reason": choice.get("finish_reason", "stop"),
                    },
                )

            except httpx.TimeoutException as e:
                set_span_error(e)
                span.set_attribute("error.type", "TimeoutException")
                span.set_attribute("error.message", f"Request timeout after {self.timeout}s")
                self.logger.error(
                    "completion_timeout",
                    model=self.model,
                    timeout=self.timeout
                )
                raise
            except httpx.HTTPStatusError as e:
                set_span_error(e)
                span.set_attribute("error.type", "HTTPStatusError")
                span.set_attribute("error.message", str(e))
                span.set_attribute("error.status_code", e.response.status_code)
                self.logger.error(
                    "completion_http_error",
                    error=str(e),
                    status_code=e.response.status_code,
                    model=self.model
                )
                raise
            except Exception as e:
                set_span_error(e)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                self.logger.error(
                    "completion_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    model=self.model
                )
                raise

    async def _stream_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream completion using vLLM's native streaming.

        vLLM supports native streaming via Server-Sent Events (SSE).

        Args:
            messages: Conversation messages
            tools: Available tools (not supported)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            StreamChunk: Incremental response chunks
        """
        start_time = time.time()
        accumulated_content = ""
        total_tokens = None

        with trace_llm_request("vllm_stream", self.model) as span:
            try:
                # Add tracing attributes
                span.set_attribute("llm.temperature", temperature)
                span.set_attribute("llm.max_tokens", max_tokens or 4096)
                span.set_attribute("llm.message_count", len(messages))
                span.set_attribute("llm.streaming", True)

                # Format messages
                formatted_messages = self.format_messages(messages)

                # Add system message if not present
                if not any(msg["role"] == "system" for msg in formatted_messages):
                    formatted_messages.insert(
                        0,
                        {
                            "role": "system",
                            "content": "You are a helpful AI assistant. Provide clear and accurate responses.",
                        },
                    )

                add_event_to_current_span("vllm_stream_request_start")

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/v1/chat/completions",
                        json={
                            "model": self.model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens or 4096,
                            "stream": True,
                        },
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "text/event-stream",
                        },
                    ) as response:
                        response.raise_for_status()

                        # Process SSE stream
                        async for line in response.aiter_lines():
                            if not line or line.startswith(":"):
                                continue

                            if line.startswith("data: "):
                                data_str = line[6:]  # Remove "data: " prefix

                                if data_str == "[DONE]":
                                    break

                                try:
                                    import json
                                    data = json.loads(data_str)

                                    # Extract delta content
                                    choice = data.get("choices", [{}])[0]
                                    delta = choice.get("delta", {})
                                    content = delta.get("content", "")

                                    if content:
                                        accumulated_content += content
                                        yield StreamChunk(
                                            provider=self.provider,
                                            content=content,
                                            is_final=False,
                                        )

                                    # Check for usage info in final chunk
                                    usage = data.get("usage")
                                    if usage:
                                        total_tokens = usage.get("total_tokens")

                                except json.JSONDecodeError as e:
                                    self.logger.warning(
                                        "stream_parse_error",
                                        error=str(e),
                                        line=data_str[:100]
                                    )
                                    continue

                add_event_to_current_span("vllm_stream_request_complete")

                execution_time = time.time() - start_time

                # Add final metrics
                span.set_attribute("llm.execution_time_ms", int(execution_time * 1000))
                if total_tokens:
                    span.set_attribute("llm.tokens.total", total_tokens)

                # Send final chunk with metadata
                yield StreamChunk(
                    provider=self.provider,
                    content="",
                    is_final=True,
                    tokens_used=total_tokens,
                    metadata={
                        "model": self.model,
                        "backend": "vllm",
                        "execution_time": execution_time,
                        "content_length": len(accumulated_content),
                    },
                )

                self.logger.info(
                    "stream_completed",
                    time=execution_time,
                    model=self.model,
                    tokens=total_tokens,
                    content_length=len(accumulated_content),
                )

            except Exception as e:
                set_span_error(e)
                self.logger.error(
                    "streaming_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    model=self.model
                )
                # Send error chunk
                yield StreamChunk(
                    provider=self.provider,
                    content="",
                    is_final=True,
                    metadata={"error": str(e), "error_type": type(e).__name__},
                )
                raise

    async def health_check(self) -> bool:
        """Check if vLLM server is accessible and healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to get models endpoint
                response = await client.get(f"{self.base_url}/v1/models")

                if response.status_code != 200:
                    self.logger.warning(
                        "health_check_failed",
                        status_code=response.status_code,
                        reason="Models endpoint returned non-200 status"
                    )
                    return False

                # Verify our model is available
                data = response.json()
                models = data.get("data", [])
                model_ids = [model.get("id") for model in models]

                if self.model not in model_ids:
                    self.logger.warning(
                        "vllm_model_not_found",
                        expected_model=self.model,
                        available_models=model_ids,
                        message=f"Model '{self.model}' not found in vLLM server"
                    )
                    return False

                self.logger.info(
                    "health_check_passed",
                    model=self.model,
                    available_models=len(model_ids)
                )
                return True

        except httpx.TimeoutException:
            self.logger.error(
                "health_check_timeout",
                message="vLLM server did not respond within 5 seconds"
            )
            return False
        except httpx.ConnectError:
            self.logger.error(
                "health_check_connection_error",
                message=f"Could not connect to vLLM server at {self.base_url}"
            )
            return False
        except Exception as e:
            self.logger.error(
                "health_check_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return False
