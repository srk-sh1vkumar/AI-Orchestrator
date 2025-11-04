"""Context window management with token counting and smart truncation."""

from typing import List, Dict, Optional, Tuple
from enum import Enum
import tiktoken
from src.models.schemas import Message, LLMProvider
import structlog

logger = structlog.get_logger()


class TruncationStrategy(str, Enum):
    """Strategy for handling context window overflow."""
    SLIDING_WINDOW = "sliding_window"  # Keep recent messages
    SUMMARIZE = "summarize"  # Summarize old messages
    HYBRID = "hybrid"  # Sliding window + summarization


class ContextStatus(str, Enum):
    """Status of context window."""
    OK = "ok"  # Well within limits
    WARNING = "warning"  # Approaching limits (>80%)
    OVERFLOW = "overflow"  # Exceeds limits
    TRUNCATED = "truncated"  # Was truncated


class ProviderLimits:
    """Token limits for each provider."""

    LIMITS: Dict[LLMProvider, int] = {
        LLMProvider.CLAUDE_CODE: 200_000,  # Claude 3 Opus/Sonnet
        LLMProvider.CLAUDE: 200_000,
        LLMProvider.CHATGPT: 128_000,  # GPT-4 Turbo
        LLMProvider.GEMINI: 32_000,   # Gemini Pro
        LLMProvider.LOCAL: 8_000,     # Typical local model
        LLMProvider.MISTRAL: 8_000,
        LLMProvider.LLAMA2: 4_096,
        LLMProvider.CODELLAMA: 16_000,
    }

    # Warning threshold (80% of limit)
    WARNING_THRESHOLD = 0.8

    # Truncation threshold (when to start truncating)
    TRUNCATION_THRESHOLD = 0.75

    @classmethod
    def get_limit(cls, provider: LLMProvider) -> int:
        """Get token limit for provider."""
        return cls.LIMITS.get(provider, 4096)  # Default 4k for unknown

    @classmethod
    def get_warning_threshold(cls, provider: LLMProvider) -> int:
        """Get warning threshold tokens."""
        return int(cls.get_limit(provider) * cls.WARNING_THRESHOLD)

    @classmethod
    def get_truncation_threshold(cls, provider: LLMProvider) -> int:
        """Get truncation threshold tokens."""
        return int(cls.get_limit(provider) * cls.TRUNCATION_THRESHOLD)


class ContextWindowManager:
    """Manages context windows with token counting and smart truncation."""

    def __init__(self):
        """Initialize context manager."""
        self.logger = logger.bind(component="context_manager")
        self._init_encoders()

    def _init_encoders(self):
        """Initialize tokenizer encoders."""
        try:
            # Use cl100k_base for GPT-4, GPT-3.5-turbo
            self.gpt_encoder = tiktoken.get_encoding("cl100k_base")
            # Use p50k_base for older models
            self.legacy_encoder = tiktoken.get_encoding("p50k_base")
            self.logger.info("encoders_initialized")
        except Exception as e:
            self.logger.error("encoder_initialization_failed", error=str(e))
            # Fallback: approximate with simple word count
            self.gpt_encoder = None
            self.legacy_encoder = None

    def count_tokens(
        self,
        text: str,
        provider: LLMProvider = LLMProvider.CHATGPT
    ) -> int:
        """Count tokens in text for given provider.

        Args:
            text: Text to count tokens for
            provider: LLM provider (affects tokenizer used)

        Returns:
            Token count
        """
        if not text:
            return 0

        try:
            # Use appropriate encoder based on provider
            if provider in [LLMProvider.CHATGPT, LLMProvider.CLAUDE_CODE, LLMProvider.CLAUDE]:
                if self.gpt_encoder:
                    return len(self.gpt_encoder.encode(text))
            else:
                if self.legacy_encoder:
                    return len(self.legacy_encoder.encode(text))

            # Fallback: approximate as 4 chars per token
            return len(text) // 4

        except Exception as e:
            self.logger.warning("token_counting_failed", error=str(e))
            # Fallback approximation
            return len(text) // 4

    def count_message_tokens(
        self,
        messages: List[Message],
        provider: LLMProvider = LLMProvider.CHATGPT
    ) -> int:
        """Count total tokens in message list.

        Args:
            messages: List of messages
            provider: LLM provider

        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            # Count message content
            total += self.count_tokens(msg.content, provider)
            # Add overhead for message formatting (~4 tokens per message)
            total += 4
            # Add role tokens
            total += self.count_tokens(msg.role, provider)

        # Add conversation overhead
        total += 3

        return total

    def check_context_status(
        self,
        messages: List[Message],
        provider: LLMProvider
    ) -> Tuple[ContextStatus, int, int]:
        """Check if messages fit within provider's context window.

        Args:
            messages: Message list
            provider: LLM provider

        Returns:
            Tuple of (status, token_count, limit)
        """
        token_count = self.count_message_tokens(messages, provider)
        limit = ProviderLimits.get_limit(provider)
        warning_threshold = ProviderLimits.get_warning_threshold(provider)

        if token_count > limit:
            status = ContextStatus.OVERFLOW
        elif token_count > warning_threshold:
            status = ContextStatus.WARNING
        else:
            status = ContextStatus.OK

        self.logger.info(
            "context_status_checked",
            provider=provider.value,
            token_count=token_count,
            limit=limit,
            utilization=f"{(token_count/limit)*100:.1f}%",
            status=status.value
        )

        return status, token_count, limit

    def truncate_messages(
        self,
        messages: List[Message],
        provider: LLMProvider,
        strategy: TruncationStrategy = TruncationStrategy.SLIDING_WINDOW,
        reserve_tokens: int = 1000
    ) -> Tuple[List[Message], bool]:
        """Truncate messages to fit within context window.

        Args:
            messages: Message list
            provider: LLM provider
            strategy: Truncation strategy
            reserve_tokens: Tokens to reserve for response

        Returns:
            Tuple of (truncated_messages, was_truncated)
        """
        limit = ProviderLimits.get_limit(provider)
        target_tokens = limit - reserve_tokens
        current_tokens = self.count_message_tokens(messages, provider)

        if current_tokens <= target_tokens:
            return messages, False

        self.logger.warning(
            "context_truncation_required",
            provider=provider.value,
            current_tokens=current_tokens,
            target_tokens=target_tokens,
            message_count=len(messages),
            strategy=strategy.value
        )

        if strategy == TruncationStrategy.SLIDING_WINDOW:
            return self._truncate_sliding_window(messages, provider, target_tokens)
        elif strategy == TruncationStrategy.SUMMARIZE:
            return self._truncate_with_summarization(messages, provider, target_tokens)
        elif strategy == TruncationStrategy.HYBRID:
            return self._truncate_hybrid(messages, provider, target_tokens)

        # Default to sliding window
        return self._truncate_sliding_window(messages, provider, target_tokens)

    def _truncate_sliding_window(
        self,
        messages: List[Message],
        provider: LLMProvider,
        target_tokens: int
    ) -> Tuple[List[Message], bool]:
        """Truncate using sliding window (keep most recent).

        Args:
            messages: Message list
            provider: LLM provider
            target_tokens: Target token count

        Returns:
            Tuple of (truncated_messages, was_truncated)
        """
        if not messages:
            return messages, False

        # Always keep system messages and first user message
        system_messages = [m for m in messages if m.role == "system"]
        first_user = next((m for m in messages if m.role == "user"), None)
        other_messages = [m for m in messages if m.role != "system" and m != first_user]

        # Start with system messages and first user message
        kept_messages = system_messages.copy()
        if first_user:
            kept_messages.append(first_user)

        # Add most recent messages until we hit token limit
        current_tokens = self.count_message_tokens(kept_messages, provider)

        for msg in reversed(other_messages):
            msg_tokens = self.count_tokens(msg.content, provider) + 4
            if current_tokens + msg_tokens <= target_tokens:
                kept_messages.insert(len(system_messages) + (1 if first_user else 0), msg)
                current_tokens += msg_tokens
            else:
                break

        # Restore chronological order for non-system messages
        result = system_messages + sorted(
            [m for m in kept_messages if m.role != "system"],
            key=lambda x: x.timestamp
        )

        was_truncated = len(result) < len(messages)

        if was_truncated:
            self.logger.info(
                "messages_truncated",
                original_count=len(messages),
                kept_count=len(result),
                removed_count=len(messages) - len(result)
            )

        return result, was_truncated

    def _truncate_with_summarization(
        self,
        messages: List[Message],
        provider: LLMProvider,
        target_tokens: int
    ) -> Tuple[List[Message], bool]:
        """Truncate with summarization of old messages.

        Note: This is a placeholder. Full implementation would use an LLM
        to summarize old messages.

        Args:
            messages: Message list
            provider: LLM provider
            target_tokens: Target token count

        Returns:
            Tuple of (truncated_messages, was_truncated)
        """
        # For now, fall back to sliding window
        # Full implementation would:
        # 1. Take old messages (beyond sliding window)
        # 2. Send to Claude for summarization
        # 3. Replace old messages with summary message
        # 4. Keep recent messages as-is

        self.logger.warning(
            "summarization_not_implemented",
            note="Falling back to sliding window"
        )

        return self._truncate_sliding_window(messages, provider, target_tokens)

    def _truncate_hybrid(
        self,
        messages: List[Message],
        provider: LLMProvider,
        target_tokens: int
    ) -> Tuple[List[Message], bool]:
        """Hybrid truncation: summarize old, keep recent.

        Args:
            messages: Message list
            provider: LLM provider
            target_tokens: Target token count

        Returns:
            Tuple of (truncated_messages, was_truncated)
        """
        # For now, use sliding window
        # Full implementation would combine both strategies
        return self._truncate_sliding_window(messages, provider, target_tokens)

    def estimate_completion_tokens(
        self,
        provider: LLMProvider,
        max_tokens: Optional[int] = None
    ) -> int:
        """Estimate tokens needed for completion.

        Args:
            provider: LLM provider
            max_tokens: Maximum tokens requested for completion

        Returns:
            Estimated token count for completion
        """
        if max_tokens:
            return max_tokens

        # Default estimates based on provider
        defaults = {
            LLMProvider.CLAUDE_CODE: 4096,
            LLMProvider.CLAUDE: 4096,
            LLMProvider.CHATGPT: 4096,
            LLMProvider.GEMINI: 2048,
            LLMProvider.LOCAL: 512,
        }

        return defaults.get(provider, 1024)


# Global instance
_context_manager: Optional[ContextWindowManager] = None


def get_context_manager() -> ContextWindowManager:
    """Get global context manager instance (singleton)."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextWindowManager()
    return _context_manager
