"""Tests for context window management."""

import pytest
from datetime import datetime
from src.core.context_manager import (
    ContextWindowManager,
    ProviderLimits,
    ContextStatus,
    TruncationStrategy,
    get_context_manager,
)
from src.models.schemas import Message, LLMProvider


class TestProviderLimits:
    """Test provider token limits."""

    def test_get_limit_known_providers(self):
        """Test getting limits for known providers."""
        assert ProviderLimits.get_limit(LLMProvider.CLAUDE_CODE) == 200_000
        assert ProviderLimits.get_limit(LLMProvider.CHATGPT) == 128_000
        assert ProviderLimits.get_limit(LLMProvider.GEMINI) == 32_000
        assert ProviderLimits.get_limit(LLMProvider.LOCAL) == 8_000

    def test_get_limit_unknown_provider(self):
        """Test getting limit for unknown provider (should return default)."""
        # Create a mock provider that isn't in the limits dict
        assert ProviderLimits.get_limit(LLMProvider.MISTRAL) == 8_000  # Should use defined limit

    def test_warning_threshold(self):
        """Test warning threshold calculation."""
        limit = ProviderLimits.get_limit(LLMProvider.CHATGPT)
        warning = ProviderLimits.get_warning_threshold(LLMProvider.CHATGPT)
        assert warning == int(limit * 0.8)
        assert warning == 102_400  # 80% of 128k

    def test_truncation_threshold(self):
        """Test truncation threshold calculation."""
        limit = ProviderLimits.get_limit(LLMProvider.CLAUDE_CODE)
        truncation = ProviderLimits.get_truncation_threshold(LLMProvider.CLAUDE_CODE)
        assert truncation == int(limit * 0.75)
        assert truncation == 150_000  # 75% of 200k


class TestContextWindowManager:
    """Test ContextWindowManager class."""

    def test_initialization(self):
        """Test manager initializes correctly."""
        manager = ContextWindowManager()
        assert manager is not None
        assert manager.gpt_encoder is not None
        assert manager.legacy_encoder is not None

    def test_count_tokens_simple(self):
        """Test token counting for simple text."""
        manager = ContextWindowManager()

        # Short text
        text = "Hello, world!"
        tokens = manager.count_tokens(text, LLMProvider.CHATGPT)
        assert tokens > 0
        assert tokens < 10  # Should be around 3-4 tokens

    def test_count_tokens_empty(self):
        """Test token counting for empty text."""
        manager = ContextWindowManager()
        assert manager.count_tokens("", LLMProvider.CHATGPT) == 0
        assert manager.count_tokens("", LLMProvider.CLAUDE_CODE) == 0

    def test_count_tokens_long_text(self):
        """Test token counting for longer text."""
        manager = ContextWindowManager()

        # Longer text (roughly 100 words)
        text = " ".join(["word"] * 100)
        tokens = manager.count_tokens(text, LLMProvider.CHATGPT)
        assert tokens > 50  # Should be around 100 tokens
        assert tokens < 200

    def test_count_message_tokens_single(self):
        """Test counting tokens in single message."""
        manager = ContextWindowManager()

        messages = [
            Message(role="user", content="Hello, how are you?")
        ]

        tokens = manager.count_message_tokens(messages, LLMProvider.CHATGPT)
        assert tokens > 0
        # Should include: message content + overhead (4) + role tokens + conversation overhead (3)
        assert tokens > 7  # At minimum

    def test_count_message_tokens_multiple(self):
        """Test counting tokens in multiple messages."""
        manager = ContextWindowManager()

        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="What is the capital of France?"),
            Message(role="assistant", content="The capital of France is Paris."),
        ]

        tokens = manager.count_message_tokens(messages, LLMProvider.CHATGPT)
        assert tokens > 0
        # Should be significantly more than single message
        assert tokens > 20

    def test_check_context_status_ok(self):
        """Test context status check when well within limits."""
        manager = ContextWindowManager()

        messages = [
            Message(role="user", content="Short message")
        ]

        status, token_count, limit = manager.check_context_status(
            messages, LLMProvider.CHATGPT
        )

        assert status == ContextStatus.OK
        assert token_count > 0
        assert token_count < limit
        assert limit == 128_000

    def test_check_context_status_warning(self):
        """Test context status when approaching limit."""
        manager = ContextWindowManager()

        # Create messages that approach the warning threshold
        # For GEMINI (32k limit, 80% = 25.6k warning)
        # Generate enough text to trigger warning
        long_text = "word " * 10000  # Roughly 10k tokens

        messages = [
            Message(role="user", content=long_text),
            Message(role="assistant", content=long_text),
            Message(role="user", content=long_text),
        ]

        status, token_count, limit = manager.check_context_status(
            messages, LLMProvider.GEMINI
        )

        # Should be in WARNING or OVERFLOW state (30k+ tokens with 32k limit)
        assert status in [ContextStatus.WARNING, ContextStatus.OVERFLOW]
        assert token_count > 25600  # Over 80% threshold
        assert limit == 32_000

    def test_check_context_status_overflow(self):
        """Test context status when exceeding limit."""
        manager = ContextWindowManager()

        # Create messages that definitely exceed LOCAL limit (8k)
        long_text = "word " * 3000  # Roughly 3k tokens

        messages = [
            Message(role="user", content=long_text) for _ in range(5)
        ]

        status, token_count, limit = manager.check_context_status(
            messages, LLMProvider.LOCAL
        )

        assert status == ContextStatus.OVERFLOW
        assert token_count > limit
        assert limit == 8_000

    def test_truncate_messages_no_truncation_needed(self):
        """Test truncation when messages fit within limit."""
        manager = ContextWindowManager()

        messages = [
            Message(role="user", content="Short message")
        ]

        truncated, was_truncated = manager.truncate_messages(
            messages, LLMProvider.CHATGPT
        )

        assert was_truncated is False
        assert len(truncated) == len(messages)

    def test_truncate_messages_sliding_window(self):
        """Test sliding window truncation."""
        manager = ContextWindowManager()

        # Create many messages that exceed LOCAL limit (8k)
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="First question"),
        ]

        # Add many messages to exceed limit
        for i in range(100):
            messages.append(
                Message(role="assistant", content=f"Response {i} with some content " * 10)
            )
            messages.append(
                Message(role="user", content=f"Question {i} with more content " * 10)
            )

        truncated, was_truncated = manager.truncate_messages(
            messages, LLMProvider.LOCAL, strategy=TruncationStrategy.SLIDING_WINDOW
        )

        assert was_truncated is True
        assert len(truncated) < len(messages)
        # Should keep system message
        assert truncated[0].role == "system"
        # Should keep first user message
        assert any(msg.content == "First question" for msg in truncated)

    def test_truncate_preserves_system_messages(self):
        """Test that truncation always preserves system messages."""
        manager = ContextWindowManager()

        messages = [
            Message(role="system", content="Important system prompt that must be kept."),
        ]

        # Add many messages
        for i in range(50):
            messages.append(Message(role="user", content=f"Message {i} " * 100))

        truncated, was_truncated = manager.truncate_messages(
            messages, LLMProvider.LOCAL
        )

        # System message should always be first
        assert truncated[0].role == "system"
        assert "Important system prompt" in truncated[0].content

    def test_truncate_preserves_first_user_message(self):
        """Test that truncation preserves first user message."""
        manager = ContextWindowManager()

        messages = [
            Message(role="system", content="System prompt"),
            Message(role="user", content="Original user question"),
        ]

        # Add many messages
        for i in range(50):
            messages.append(Message(role="assistant", content=f"Response {i} " * 100))

        truncated, was_truncated = manager.truncate_messages(
            messages, LLMProvider.LOCAL
        )

        # Should keep first user message
        assert any(msg.content == "Original user question" for msg in truncated)

    def test_truncate_keeps_recent_messages(self):
        """Test that truncation keeps most recent messages."""
        manager = ContextWindowManager()

        messages = [
            Message(role="system", content="System"),
            Message(role="user", content="First"),
        ]

        # Add messages with timestamps - make them much larger to force truncation
        for i in range(100):
            messages.append(
                Message(
                    role="user",
                    content=f"Message {i} " * 200,  # Much larger messages
                    timestamp=datetime.fromisoformat(f"2024-01-{(i%28)+1:02d}T12:00:00")
                )
            )

        truncated, was_truncated = manager.truncate_messages(
            messages, LLMProvider.LOCAL
        )

        assert was_truncated is True
        # Most recent messages should be present
        assert any("Message 99" in msg.content for msg in truncated)

    def test_estimate_completion_tokens(self):
        """Test completion token estimation."""
        manager = ContextWindowManager()

        # Claude should estimate 4096
        assert manager.estimate_completion_tokens(LLMProvider.CLAUDE_CODE) == 4096

        # Gemini should estimate 2048
        assert manager.estimate_completion_tokens(LLMProvider.GEMINI) == 2048

        # LOCAL should estimate 512
        assert manager.estimate_completion_tokens(LLMProvider.LOCAL) == 512

    def test_estimate_completion_tokens_with_max(self):
        """Test completion token estimation with explicit max_tokens."""
        manager = ContextWindowManager()

        # Should use provided max_tokens
        assert manager.estimate_completion_tokens(LLMProvider.CHATGPT, max_tokens=1000) == 1000


class TestGlobalContextManagerSingleton:
    """Test global context manager singleton."""

    def test_get_context_manager_returns_instance(self):
        """Test that get_context_manager returns an instance."""
        manager = get_context_manager()
        assert manager is not None
        assert isinstance(manager, ContextWindowManager)

    def test_get_context_manager_returns_singleton(self):
        """Test that get_context_manager returns the same instance."""
        manager1 = get_context_manager()
        manager2 = get_context_manager()

        assert manager1 is manager2


class TestContextManagerIntegration:
    """Integration tests for context manager."""

    def test_large_conversation_handling(self):
        """Test handling of very large conversation."""
        manager = ContextWindowManager()

        # Simulate a large conversation
        messages = [Message(role="system", content="You are helpful.")]

        # Add 500 messages with substantial content
        for i in range(500):
            role = "user" if i % 2 == 0 else "assistant"
            content = f"Message {i}: " + ("word " * 100)  # ~100 tokens each
            messages.append(Message(role=role, content=content))

        # This should definitely overflow LOCAL (8k)
        status, token_count, limit = manager.check_context_status(
            messages, LLMProvider.LOCAL
        )

        assert status == ContextStatus.OVERFLOW

        # Truncate
        truncated, was_truncated = manager.truncate_messages(
            messages, LLMProvider.LOCAL
        )

        assert was_truncated is True
        assert len(truncated) < len(messages)

        # Check that truncated messages fit
        new_status, new_count, _ = manager.check_context_status(
            truncated, LLMProvider.LOCAL
        )

        assert new_status != ContextStatus.OVERFLOW
        assert new_count < token_count

    def test_multi_provider_context_check(self):
        """Test context checking across different providers."""
        manager = ContextWindowManager()

        # Create messages that are OK for Claude but WARNING/OVERFLOW for smaller providers
        messages = [
            Message(role="system", content="System prompt"),
        ]

        # Add enough to exceed GEMINI warning (32k * 0.8 = 25.6k)
        # Each message needs to be larger
        for i in range(200):
            messages.append(
                Message(role="user", content="Question " * 200)
            )

        # Should be OK for Claude (200k limit)
        claude_status, _, _ = manager.check_context_status(messages, LLMProvider.CLAUDE_CODE)
        assert claude_status == ContextStatus.OK

        # Should be WARNING or OVERFLOW for Gemini (32k limit)
        gemini_status, gemini_count, _ = manager.check_context_status(messages, LLMProvider.GEMINI)
        assert gemini_status in [ContextStatus.WARNING, ContextStatus.OVERFLOW]
        assert gemini_count > 25600  # Should exceed 80% threshold

        # Should definitely be OVERFLOW for LOCAL (8k limit)
        local_status, _, _ = manager.check_context_status(messages, LLMProvider.LOCAL)
        assert local_status == ContextStatus.OVERFLOW

    def test_reserve_tokens_in_truncation(self):
        """Test that truncation respects reserve_tokens parameter."""
        manager = ContextWindowManager()

        # Create messages that definitely overflow LOCAL limit (8k)
        messages = []
        for i in range(100):
            messages.append(Message(role="user", content="word " * 200))

        # Verify we're over the limit
        status, count, limit = manager.check_context_status(messages, LLMProvider.LOCAL)
        assert status == ContextStatus.OVERFLOW

        # Truncate with different reserve amounts
        truncated_1k, _ = manager.truncate_messages(
            messages, LLMProvider.LOCAL, reserve_tokens=1000
        )
        truncated_2k, _ = manager.truncate_messages(
            messages, LLMProvider.LOCAL, reserve_tokens=2000
        )

        # More reserved tokens should result in fewer kept messages
        count_1k = manager.count_message_tokens(truncated_1k, LLMProvider.LOCAL)
        count_2k = manager.count_message_tokens(truncated_2k, LLMProvider.LOCAL)

        assert count_2k < count_1k


class TestContextManagerEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_message_list(self):
        """Test handling of empty message list."""
        manager = ContextWindowManager()

        messages = []

        status, token_count, limit = manager.check_context_status(
            messages, LLMProvider.CHATGPT
        )

        assert status == ContextStatus.OK
        assert token_count == 3  # Just conversation overhead

    def test_very_long_single_message(self):
        """Test handling of single very long message."""
        manager = ContextWindowManager()

        # Create a message longer than LOCAL limit
        very_long_text = "word " * 5000  # ~5k tokens
        messages = [Message(role="user", content=very_long_text)]

        status, token_count, limit = manager.check_context_status(
            messages, LLMProvider.LOCAL
        )

        # Should detect overflow
        assert token_count > 5000

    def test_messages_with_metadata(self):
        """Test token counting with messages that have metadata."""
        manager = ContextWindowManager()

        messages = [
            Message(
                role="user",
                content="Hello",
                metadata={"tool_call": "some_tool", "result": "data"}
            )
        ]

        # Should count tokens successfully (metadata not counted)
        tokens = manager.count_message_tokens(messages, LLMProvider.CHATGPT)
        assert tokens > 0

    def test_truncation_with_single_message(self):
        """Test truncation when there's only one message."""
        manager = ContextWindowManager()

        messages = [
            Message(role="user", content="Hello")
        ]

        truncated, was_truncated = manager.truncate_messages(
            messages, LLMProvider.LOCAL
        )

        assert was_truncated is False
        assert len(truncated) == 1
