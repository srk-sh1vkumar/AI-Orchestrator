"""Rate limiting implementation using token bucket algorithm."""

import time
from typing import Dict, Optional
from threading import Lock
from datetime import datetime, date
import structlog

logger = structlog.get_logger()


class TokenBucket:
    """Token bucket implementation for rate limiting.

    The token bucket algorithm allows a certain number of tokens (requests)
    per time window, with burst capacity.
    """

    def __init__(self, rate: int, per: float = 60.0, burst: Optional[int] = None):
        """Initialize token bucket.

        Args:
            rate: Number of tokens to add per time period
            per: Time period in seconds (default: 60s = 1 minute)
            burst: Maximum burst capacity (default: same as rate)
        """
        self.rate = rate
        self.per = per
        self.burst = burst or rate
        self.tokens = float(self.burst)
        self.last_update = time.time()
        self.lock = Lock()

        logger.info(
            "token_bucket_created",
            rate=rate,
            per=per,
            burst=self.burst
        )

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        tokens_to_add = (elapsed / self.per) * self.rate
        self.tokens = min(self.burst, self.tokens + tokens_to_add)
        self.last_update = now

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume (default: 1)

        Returns:
            True if tokens were consumed, False if rate limited
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    def get_available_tokens(self) -> float:
        """Get current number of available tokens.

        Returns:
            Number of tokens currently available
        """
        with self.lock:
            self._refill()
            return self.tokens


class DailyQuotaTracker:
    """Track daily API quotas for providers with daily limits."""

    def __init__(self):
        """Initialize daily quota tracker."""
        self.quotas: Dict[str, Dict[str, any]] = {}
        self.lock = Lock()

    def configure_daily_quota(self, provider: str, daily_limit: int):
        """Configure daily quota for a provider.

        Args:
            provider: Provider name
            daily_limit: Maximum requests allowed per day
        """
        with self.lock:
            self.quotas[provider] = {
                "limit": daily_limit,
                "used": 0,
                "date": date.today().isoformat()
            }
            logger.info(
                "daily_quota_configured",
                provider=provider,
                daily_limit=daily_limit
            )

    def consume(self, provider: str) -> bool:
        """Try to consume one request from daily quota.

        Args:
            provider: Provider name

        Returns:
            True if quota available, False if exhausted
        """
        with self.lock:
            # Provider not tracked - allow request
            if provider not in self.quotas:
                return True

            quota = self.quotas[provider]
            today = date.today().isoformat()

            # Reset quota if new day
            if quota["date"] != today:
                quota["used"] = 0
                quota["date"] = today
                logger.info(
                    "daily_quota_reset",
                    provider=provider,
                    limit=quota["limit"]
                )

            # Check if quota available
            if quota["used"] >= quota["limit"]:
                logger.warning(
                    "daily_quota_exceeded",
                    provider=provider,
                    used=quota["used"],
                    limit=quota["limit"]
                )
                return False

            # Consume quota
            quota["used"] += 1
            return True

    def get_quota_stats(self, provider: str) -> Dict[str, any]:
        """Get daily quota statistics for a provider.

        Args:
            provider: Provider name

        Returns:
            Dict with limit, used, remaining
        """
        with self.lock:
            if provider not in self.quotas:
                return {}

            quota = self.quotas[provider]
            today = date.today().isoformat()

            # Reset if new day
            if quota["date"] != today:
                quota["used"] = 0
                quota["date"] = today

            return {
                "daily_limit": quota["limit"],
                "daily_used": quota["used"],
                "daily_remaining": quota["limit"] - quota["used"],
                "date": quota["date"]
            }

    def set_quota_used(self, provider: str, used: int):
        """Manually set quota usage (for testing/recovery).

        Args:
            provider: Provider name
            used: Number of requests already used today
        """
        with self.lock:
            if provider in self.quotas:
                self.quotas[provider]["used"] = used
                logger.info(
                    "daily_quota_manually_set",
                    provider=provider,
                    used=used
                )


class RateLimiter:
    """Multi-provider rate limiter with per-provider limits.

    Implements local (per-instance) rate limiting using token bucket algorithm.
    Each provider has its own bucket based on configured limits.
    Also tracks daily quotas for providers with daily limits (e.g., Gemini free tier).
    """

    def __init__(self):
        """Initialize rate limiter."""
        self.buckets: Dict[str, TokenBucket] = {}
        self.daily_quotas = DailyQuotaTracker()
        self.logger = logger.bind(component="rate_limiter")

    def configure_provider(
        self,
        provider: str,
        requests_per_minute: int,
        burst: Optional[int] = None
    ) -> None:
        """Configure rate limit for a provider.

        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            requests_per_minute: Maximum requests per minute
            burst: Maximum burst capacity (default: same as rate)
        """
        self.buckets[provider] = TokenBucket(
            rate=requests_per_minute,
            per=60.0,  # 1 minute
            burst=burst
        )

        self.logger.info(
            "provider_rate_limit_configured",
            provider=provider,
            rpm=requests_per_minute,
            burst=burst or requests_per_minute
        )

    def check_limit(self, provider: str) -> bool:
        """Check if a request is allowed for a provider.

        Checks both per-minute rate limits and daily quotas.

        Args:
            provider: Provider name

        Returns:
            True if request is allowed, False if rate limited or quota exhausted
        """
        # Check daily quota first (if configured)
        if not self.daily_quotas.consume(provider):
            self.logger.warning(
                "daily_quota_exceeded",
                provider=provider
            )
            return False

        # If no bucket configured for provider, allow request
        if provider not in self.buckets:
            self.logger.warning(
                "no_rate_limit_configured",
                provider=provider
            )
            return True

        bucket = self.buckets[provider]
        allowed = bucket.consume(tokens=1)

        if not allowed:
            self.logger.warning(
                "rate_limit_exceeded",
                provider=provider,
                available_tokens=bucket.get_available_tokens()
            )

        return allowed

    def get_provider_stats(self, provider: str) -> Dict[str, float]:
        """Get current rate limit statistics for a provider.

        Args:
            provider: Provider name

        Returns:
            Dict with rate, burst, available_tokens, and daily quota stats
        """
        stats = {}

        # Add per-minute rate limit stats
        if provider in self.buckets:
            bucket = self.buckets[provider]
            stats.update({
                "rate_per_minute": bucket.rate,
                "burst_capacity": bucket.burst,
                "available_tokens": bucket.get_available_tokens()
            })

        # Add daily quota stats
        daily_stats = self.daily_quotas.get_quota_stats(provider)
        if daily_stats:
            stats.update(daily_stats)

        return stats

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get rate limit statistics for all providers.

        Returns:
            Dict mapping provider names to their stats
        """
        return {
            provider: self.get_provider_stats(provider)
            for provider in self.buckets.keys()
        }


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance.

    Returns:
        Global RateLimiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        _rate_limiter = RateLimiter()

        # Configure default limits for known providers
        # These can be overridden via environment variables
        _rate_limiter.configure_provider("openai", requests_per_minute=3500)
        _rate_limiter.configure_provider("chatgpt", requests_per_minute=3500)  # Alias for openai
        _rate_limiter.configure_provider("anthropic", requests_per_minute=4000)
        _rate_limiter.configure_provider("claude_code", requests_per_minute=4000)  # Alias for anthropic
        _rate_limiter.configure_provider("claude", requests_per_minute=4000)  # Alias for anthropic
        _rate_limiter.configure_provider("google", requests_per_minute=1500)
        _rate_limiter.configure_provider("gemini", requests_per_minute=1500)  # Alias for google
        _rate_limiter.configure_provider("local", requests_per_minute=100)

        # Configure daily quotas for free tier providers
        _rate_limiter.daily_quotas.configure_daily_quota("google", daily_limit=1500)  # gemini-1.5-flash free tier (1500/day)
        _rate_limiter.daily_quotas.configure_daily_quota("gemini", daily_limit=1500)  # Alias for google
        _rate_limiter.daily_quotas.configure_daily_quota("openai", daily_limit=200)  # gpt-4o-mini free tier
        _rate_limiter.daily_quotas.configure_daily_quota("chatgpt", daily_limit=200)  # Alias for openai
        _rate_limiter.daily_quotas.configure_daily_quota("anthropic", daily_limit=1000)  # claude-3-haiku free tier
        _rate_limiter.daily_quotas.configure_daily_quota("claude_code", daily_limit=1000)  # Alias for anthropic
        _rate_limiter.daily_quotas.configure_daily_quota("claude", daily_limit=1000)  # Alias for anthropic

        logger.info("global_rate_limiter_initialized")

    return _rate_limiter
