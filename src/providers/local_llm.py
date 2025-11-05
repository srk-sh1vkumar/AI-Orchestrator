"""Local LLM provider integration (Ollama)."""

import time
from typing import List, Optional, Dict, Any, AsyncIterator
import httpx
from src.providers.base import BaseLLMProvider
from src.models.schemas import LLMResponse, LLMProvider, Message, ToolCall, StreamChunk
from src.core.config import settings


class LocalLLMProvider(BaseLLMProvider):
    """Local LLM provider for privacy-focused incident analysis."""

    def __init__(self) -> None:
        """Initialize local LLM provider."""
        super().__init__(LLMProvider.LOCAL)
        self.base_url = settings.local_llm_base_url
        self.model = settings.local_llm_model
        self.timeout = settings.local_llm_timeout

    async def _complete_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 4096,
    ) -> LLMResponse:
        """Generate a completion using local LLM.

        Args:
            messages: Conversation messages
            tools: Available tools (not supported by Ollama)
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Returns:
            LLMResponse
        """
        start_time = time.time()

        try:
            # Format messages for Ollama
            formatted_messages = self.format_messages(messages)

            # Add system message for incident analysis role
            formatted_messages.insert(
                0,
                {
                    "role": "system",
                    "content": """You are a specialized AI for incident analysis:
                    - Analyze logs, metrics, and timelines
                    - Identify root causes and contributing factors
                    - Detect patterns in system behavior
                    - Investigate security incidents
                    - Analyze performance issues
                    - Stay local for privacy and security

                    Provide thorough, actionable analysis.""",
                },
            )

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

            execution_time = time.time() - start_time

            content = data.get("message", {}).get("content", "")

            self.logger.info("completion_generated", time=execution_time)

            return LLMResponse(
                provider=self.provider,
                content=content,
                tool_calls=[],
                tokens_used=None,
                execution_time=execution_time,
                metadata={"model": self.model},
            )

        except httpx.TimeoutException:
            self.logger.error("completion_timeout")
            raise
        except Exception as e:
            self.logger.error("completion_failed", error=str(e))
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
        """Check if local LLM is accessible.

        Returns:
            True if healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False
