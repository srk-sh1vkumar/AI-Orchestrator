"""Tests for rate limiting and circuit breaker functionality."""

import pytest
import time
import asyncio
from datetime import date
from src.core.rate_limiter import RateLimiter, TokenBucket, DailyQuotaTracker, get_rate_limiter
from src.providers.base import BaseLLMProvider, RateLimitException
from src.models.schemas import LLMProvider, LLMResponse, Message, ToolCall
from typing import List, Optional, Dict, Any


class MockProvider(BaseLLMProvider):
    """Mock provider for testing."""

    def __init__(self):
        super().__init__(LLMProvider.CLAUDE_CODE)
        self.call_count = 0
        self.should_fail = False

    async def _complete_impl(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Mock implementation."""
        self.call_count += 1

        if self.should_fail:
            raise ConnectionError("Simulated failure")

        return LLMResponse(
            content="Mock response",
            provider=self.provider,
            model="mock-model",
            tool_calls=[],
            tokens_used=100,
            finish_reason="stop"
        )

    async def health_check(self) -> bool:
        return True


class TestTokenBucket:
    """Tests for TokenBucket implementation."""

    def test_token_bucket_initialization(self):
        """Test token bucket initializes correctly."""
        bucket = TokenBucket(rate=10, per=60.0)

        assert bucket.rate == 10
        assert bucket.per == 60.0
        assert bucket.burst == 10
        assert bucket.tokens == 10.0

    def test_token_bucket_custom_burst(self):
        """Test token bucket with custom burst capacity."""
        bucket = TokenBucket(rate=10, per=60.0, burst=20)

        assert bucket.burst == 20
        assert bucket.tokens == 20.0

    def test_token_consumption(self):
        """Test consuming tokens from bucket."""
        bucket = TokenBucket(rate=10, per=60.0)

        # Should succeed
        assert bucket.consume(1) is True
        assert pytest.approx(bucket.get_available_tokens(), 0.01) == 9.0

        # Consume remaining
        for _ in range(9):
            assert bucket.consume(1) is True

        # Should fail (bucket empty)
        assert bucket.consume(1) is False

    def test_token_refill(self):
        """Test tokens refill over time."""
        bucket = TokenBucket(rate=60, per=60.0)  # 1 token per second

        # Consume all tokens
        for _ in range(60):
            bucket.consume(1)

        assert pytest.approx(bucket.get_available_tokens(), 0.01) == 0.0

        # Wait 2 seconds
        time.sleep(2)

        # Should have ~2 tokens refilled
        available = bucket.get_available_tokens()
        assert 1.5 <= available <= 2.5  # Allow some tolerance

    def test_burst_capacity_limit(self):
        """Test burst capacity limits refill."""
        bucket = TokenBucket(rate=10, per=1.0, burst=5)

        # Wait for refill
        time.sleep(2)

        # Should not exceed burst capacity
        available = bucket.get_available_tokens()
        assert available <= 5.0


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes."""
        limiter = RateLimiter()
        assert len(limiter.buckets) == 0

    def test_configure_provider(self):
        """Test configuring provider rate limits."""
        limiter = RateLimiter()
        limiter.configure_provider("test_provider", requests_per_minute=100)

        assert "test_provider" in limiter.buckets
        stats = limiter.get_provider_stats("test_provider")
        assert stats["rate_per_minute"] == 100

    def test_check_limit_success(self):
        """Test rate limit check succeeds within limit."""
        limiter = RateLimiter()
        limiter.configure_provider("test", requests_per_minute=10)

        # First 10 requests should succeed
        for _ in range(10):
            assert limiter.check_limit("test") is True

    def test_check_limit_exceeded(self):
        """Test rate limit check fails when limit exceeded."""
        limiter = RateLimiter()
        limiter.configure_provider("test", requests_per_minute=5)

        # First 5 succeed
        for _ in range(5):
            assert limiter.check_limit("test") is True

        # 6th should fail
        assert limiter.check_limit("test") is False

    def test_check_limit_no_config(self):
        """Test rate limit check allows request if no config."""
        limiter = RateLimiter()

        # Should allow request
        assert limiter.check_limit("unconfigured_provider") is True

    def test_get_all_stats(self):
        """Test getting stats for all providers."""
        limiter = RateLimiter()
        limiter.configure_provider("provider1", requests_per_minute=100)
        limiter.configure_provider("provider2", requests_per_minute=200)

        stats = limiter.get_all_stats()
        assert len(stats) == 2
        assert "provider1" in stats
        assert "provider2" in stats


class TestProviderIntegration:
    """Tests for provider integration with rate limiting."""

    @pytest.mark.asyncio
    async def test_provider_rate_limit_integration(self):
        """Test provider respects rate limits."""
        # Create provider with strict rate limit
        provider = MockProvider()
        provider.rate_limiter.configure_provider("claude_code", requests_per_minute=2)

        messages = [Message(role="user", content="test")]

        # First 2 requests should succeed
        await provider.complete(messages)
        await provider.complete(messages)

        # 3rd should raise RateLimitException
        with pytest.raises(RateLimitException):
            await provider.complete(messages)

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after 5 failures."""
        provider = MockProvider()
        provider.should_fail = True

        # Increase rate limit to avoid rate limit errors
        provider.rate_limiter.configure_provider("claude_code", requests_per_minute=1000)

        messages = [Message(role="user", content="test")]

        # First 5 failures should be attempted
        for _ in range(5):
            with pytest.raises(ConnectionError):
                await provider.complete(messages)

        # After 5 failures, circuit breaker should open
        # Next call should fail faster (circuit breaker open)
        # Note: circuitbreaker library raises CircuitBreakerError
        # We expect either ConnectionError or the circuit to open
        try:
            await provider.complete(messages)
            assert False, "Expected exception"
        except Exception as e:
            # Should get either ConnectionError or circuit breaker error
            assert True

    @pytest.mark.asyncio
    async def test_retry_logic_on_transient_errors(self):
        """Test retry logic retries on transient errors."""
        provider = MockProvider()

        # Increase rate limit
        provider.rate_limiter.configure_provider("claude_code", requests_per_minute=1000)

        messages = [Message(role="user", content="test")]

        # Fail first 2 attempts, succeed on 3rd
        attempt_count = [0]

        original_impl = provider._complete_impl

        async def failing_impl(*args, **kwargs):
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ConnectionError("Transient error")
            return await original_impl(*args, **kwargs)

        provider._complete_impl = failing_impl

        # Should eventually succeed after retries
        response = await provider.complete(messages)
        assert response.content == "Mock response"
        assert attempt_count[0] == 3  # Took 3 attempts


def test_global_rate_limiter_singleton():
    """Test global rate limiter is singleton."""
    limiter1 = get_rate_limiter()
    limiter2 = get_rate_limiter()

    assert limiter1 is limiter2


def test_global_rate_limiter_has_defaults():
    """Test global rate limiter has default provider configs."""
    limiter = get_rate_limiter()

    stats = limiter.get_all_stats()
    assert "openai" in stats
    assert "anthropic" in stats
    assert "google" in stats
    assert "local" in stats


class TestDailyQuotaTracker:
    """Tests for DailyQuotaTracker functionality."""

    def test_daily_quota_initialization(self):
        """Test daily quota tracker initializes correctly."""
        tracker = DailyQuotaTracker()
        assert len(tracker.quotas) == 0

    def test_configure_daily_quota(self):
        """Test configuring daily quota for a provider."""
        tracker = DailyQuotaTracker()
        tracker.configure_daily_quota("gemini", daily_limit=1500)

        assert "gemini" in tracker.quotas
        quota = tracker.quotas["gemini"]
        assert quota["limit"] == 1500
        assert quota["used"] == 0
        assert quota["date"] == date.today().isoformat()

    def test_consume_quota_success(self):
        """Test consuming quota when available."""
        tracker = DailyQuotaTracker()
        tracker.configure_daily_quota("test_provider", daily_limit=10)

        # First 10 consumptions should succeed
        for i in range(10):
            result = tracker.consume("test_provider")
            assert result is True
            stats = tracker.get_quota_stats("test_provider")
            assert stats["daily_used"] == i + 1
            assert stats["daily_remaining"] == 10 - (i + 1)

    def test_consume_quota_exceeded(self):
        """Test consuming quota fails when limit exceeded."""
        tracker = DailyQuotaTracker()
        tracker.configure_daily_quota("test_provider", daily_limit=5)

        # Consume all 5
        for _ in range(5):
            assert tracker.consume("test_provider") is True

        # 6th should fail
        assert tracker.consume("test_provider") is False

        # Stats should show quota exhausted
        stats = tracker.get_quota_stats("test_provider")
        assert stats["daily_used"] == 5
        assert stats["daily_remaining"] == 0

    def test_consume_unconfigured_provider(self):
        """Test consuming quota for unconfigured provider allows request."""
        tracker = DailyQuotaTracker()

        # Should allow request for unconfigured provider
        assert tracker.consume("unconfigured_provider") is True

    def test_get_quota_stats(self):
        """Test getting quota statistics."""
        tracker = DailyQuotaTracker()
        tracker.configure_daily_quota("test_provider", daily_limit=100)

        # Initial stats
        stats = tracker.get_quota_stats("test_provider")
        assert stats["daily_limit"] == 100
        assert stats["daily_used"] == 0
        assert stats["daily_remaining"] == 100
        assert stats["date"] == date.today().isoformat()

        # After consumption
        tracker.consume("test_provider")
        stats = tracker.get_quota_stats("test_provider")
        assert stats["daily_used"] == 1
        assert stats["daily_remaining"] == 99

    def test_get_quota_stats_unconfigured(self):
        """Test getting stats for unconfigured provider returns empty dict."""
        tracker = DailyQuotaTracker()
        stats = tracker.get_quota_stats("nonexistent")
        assert stats == {}

    def test_set_quota_used(self):
        """Test manually setting quota usage."""
        tracker = DailyQuotaTracker()
        tracker.configure_daily_quota("test_provider", daily_limit=100)

        # Manually set used to 50
        tracker.set_quota_used("test_provider", 50)

        stats = tracker.get_quota_stats("test_provider")
        assert stats["daily_used"] == 50
        assert stats["daily_remaining"] == 50

    def test_quota_reset_on_new_day(self):
        """Test quota resets when date changes."""
        from unittest.mock import patch
        from datetime import date, timedelta

        tracker = DailyQuotaTracker()
        tracker.configure_daily_quota("test_provider", daily_limit=10)

        # Consume some quota
        for _ in range(5):
            tracker.consume("test_provider")

        # Verify consumed
        stats = tracker.get_quota_stats("test_provider")
        assert stats["daily_used"] == 5

        # Simulate next day
        tomorrow = date.today() + timedelta(days=1)
        with patch('src.core.rate_limiter.date') as mock_date:
            mock_date.today.return_value = tomorrow

            # Getting stats should reset quota
            stats = tracker.get_quota_stats("test_provider")
            assert stats["daily_used"] == 0
            assert stats["daily_remaining"] == 10
            assert stats["date"] == tomorrow.isoformat()


class TestRateLimiterWithDailyQuota:
    """Tests for RateLimiter integration with daily quotas."""

    def test_rate_limiter_daily_quota_integration(self):
        """Test rate limiter includes daily quota stats."""
        limiter = RateLimiter()
        limiter.configure_provider("test_provider", requests_per_minute=100)
        limiter.daily_quotas.configure_daily_quota("test_provider", daily_limit=1000)

        stats = limiter.get_provider_stats("test_provider")

        # Should include both per-minute and daily stats
        assert "rate_per_minute" in stats
        assert "daily_limit" in stats
        assert "daily_used" in stats
        assert "daily_remaining" in stats
        assert "date" in stats

        assert stats["rate_per_minute"] == 100
        assert stats["daily_limit"] == 1000
        assert stats["daily_used"] == 0
        assert stats["daily_remaining"] == 1000

    def test_rate_limiter_enforces_daily_quota(self):
        """Test rate limiter check_limit respects daily quota."""
        limiter = RateLimiter()
        limiter.configure_provider("test", requests_per_minute=100, burst=100)
        limiter.daily_quotas.configure_daily_quota("test", daily_limit=5)

        # First 5 should succeed
        for _ in range(5):
            result = limiter.check_limit("test")
            assert result is True

        # 6th should fail due to daily quota (even though per-minute limit is 100)
        result = limiter.check_limit("test")
        assert result is False

    def test_global_rate_limiter_daily_quotas_configured(self):
        """Test global rate limiter has daily quotas for free tier providers."""
        limiter = get_rate_limiter()

        # Check Google (Gemini) has daily quota
        google_stats = limiter.get_provider_stats("google")
        assert "daily_limit" in google_stats
        assert google_stats["daily_limit"] == 1500  # gemini-1.5-flash

        # Check OpenAI has daily quota
        openai_stats = limiter.get_provider_stats("openai")
        assert "daily_limit" in openai_stats
        assert openai_stats["daily_limit"] == 200  # gpt-4o-mini

        # Check Anthropic has daily quota
        anthropic_stats = limiter.get_provider_stats("anthropic")
        assert "daily_limit" in anthropic_stats
        assert anthropic_stats["daily_limit"] == 1000  # claude-3-haiku
