"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncIterator
from src.models.schemas import LLMResponse, ToolCall, Message, LLMProvider, StreamChunk
from src.core.rate_limiter import get_rate_limiter
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

logger = structlog.get_logger()


class RateLimitException(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, provider: LLMProvider) -> None:
        """Initialize the provider.

        Args:
            provider: Provider type
        """
        self.provider = provider
        self.logger = logger.bind(provider=provider.value)
        self.rate_limiter = get_rate_limiter()

    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a completion with rate limiting and retry logic.

        Args:
            messages: Conversation messages
            tools: Available tools for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse

        Raises:
            RateLimitException: If rate limit is exceeded
            ConnectionError/TimeoutError: If provider is unavailable (will trigger fallback)
        """
        # Check rate limit before making request
        if not self.rate_limiter.check_limit(self.provider.value):
            self.logger.warning("rate_limit_exceeded", provider=self.provider.value)
            raise RateLimitException(f"Rate limit exceeded for {self.provider.value}")

        # Call the protected implementation with circuit breaker and retry
        return await self._complete_protected(messages, tools, temperature, max_tokens)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    async def _complete_protected(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Protected completion with retry logic.

        This method is wrapped with:
        - Retry logic: 3 attempts with exponential backoff (2s, 4s, 8s) for transient errors

        Args:
            messages: Conversation messages
            tools: Available tools for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse
        """
        # Delegate to the actual implementation
        return await self._complete_impl(messages, tools, temperature, max_tokens)

    @abstractmethod
    async def _complete_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Actual completion implementation (to be overridden by subclasses).

        Args:
            messages: Conversation messages
            tools: Available tools for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse
        """
        pass

    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream a completion with rate limiting.

        Args:
            messages: Conversation messages
            tools: Available tools for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            StreamChunk: Incremental response chunks

        Raises:
            RateLimitException: If rate limit is exceeded
            ConnectionError/TimeoutError: If provider is unavailable
        """
        # Check rate limit before making request
        if not self.rate_limiter.check_limit(self.provider.value):
            self.logger.warning("rate_limit_exceeded", provider=self.provider.value)
            raise RateLimitException(f"Rate limit exceeded for {self.provider.value}")

        # Stream from the actual implementation
        try:
            async for chunk in self._stream_impl(messages, tools, temperature, max_tokens):
                yield chunk
        except Exception as e:
            self.logger.error("streaming_error", error=str(e), provider=self.provider.value)
            # Send error chunk
            yield StreamChunk(
                provider=self.provider,
                content="",
                is_final=True,
                metadata={"error": str(e)}
            )
            raise

    @abstractmethod
    async def _stream_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Actual streaming implementation (to be overridden by subclasses).

        Args:
            messages: Conversation messages
            tools: Available tools for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            StreamChunk: Incremental response chunks
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass

    def format_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Format messages for the provider.

        Args:
            messages: List of messages

        Returns:
            Formatted messages
        """
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def _stream_impl_fallback(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Fallback streaming implementation for providers without native streaming.

        This simulates streaming by calling the blocking API and chunking the response.

        Args:
            messages: Conversation messages
            tools: Available tools for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            StreamChunk: Simulated incremental response chunks
        """
        # Call the blocking API
        response = await self._complete_impl(messages, tools, temperature, max_tokens)

        # Split response into chunks (simulate streaming)
        chunk_size = 10  # Words per chunk
        words = response.content.split()

        for i in range(0, len(words), chunk_size):
            chunk_words = words[i:i + chunk_size]
            content = " ".join(chunk_words)
            if i + chunk_size < len(words):
                content += " "  # Add space between chunks

            yield StreamChunk(
                provider=self.provider,
                content=content,
                is_final=False
            )

        # Send final chunk with metadata
        yield StreamChunk(
            provider=self.provider,
            content="",
            is_final=True,
            tokens_used=response.tokens_used,
            metadata=response.metadata or {}
        )
