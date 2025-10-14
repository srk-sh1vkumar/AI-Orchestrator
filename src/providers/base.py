"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from src.models.schemas import LLMResponse, ToolCall, Message, LLMProvider
import structlog

logger = structlog.get_logger()


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""

    def __init__(self, provider: LLMProvider) -> None:
        """Initialize the provider.

        Args:
            provider: Provider type
        """
        self.provider = provider
        self.logger = logger.bind(provider=provider.value)

    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a completion.

        Args:
            messages: Conversation messages
            tools: Available tools for function calling
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse
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
