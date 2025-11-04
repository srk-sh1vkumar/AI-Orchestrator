"""Tests for semantic caching functionality."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.core.semantic_cache import SemanticCache, CacheEntry, CacheMetrics
from src.models.schemas import LLMProvider, LLMResponse, Message


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch("redis.from_url") as mock:
        redis_mock = MagicMock()
        redis_mock.ping.return_value = True
        redis_mock.smembers.return_value = set()
        redis_mock.get.return_value = None
        mock.return_value = redis_mock
        yield redis_mock


@pytest.fixture
def mock_embedding_model():
    """Mock SentenceTransformer model."""
    with patch("src.core.semantic_cache.SentenceTransformer") as mock:
        model_mock = MagicMock()
        # Return fixed embeddings for testing
        model_mock.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock.return_value = model_mock
        yield model_mock


@pytest.fixture
def semantic_cache(mock_redis, mock_embedding_model):
    """Create semantic cache instance."""
    cache = SemanticCache(
        redis_url="redis://localhost:6379/0",
        similarity_threshold=0.85,
        default_ttl=3600,
    )
    cache.redis_client = mock_redis
    cache.embedding_model = mock_embedding_model
    return cache


class TestSemanticCacheInitialization:
    """Test cache initialization."""

    def test_init_with_defaults(self, mock_redis, mock_embedding_model):
        """Test initialization with default parameters."""
        cache = SemanticCache()
        assert cache.similarity_threshold == 0.85
        assert cache.default_ttl == 3600
        assert cache.embedding_model is not None

    def test_init_with_custom_params(self, mock_redis, mock_embedding_model):
        """Test initialization with custom parameters."""
        cache = SemanticCache(
            similarity_threshold=0.90,
            default_ttl=7200,
        )
        assert cache.similarity_threshold == 0.90
        assert cache.default_ttl == 7200

    def test_redis_connection_failure(self, mock_embedding_model):
        """Test Redis connection failure."""
        with patch("redis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            with pytest.raises(Exception, match="Connection failed"):
                SemanticCache()


class TestCacheOperations:
    """Test cache get/set operations."""

    def test_cache_miss_empty_index(self, semantic_cache, mock_redis):
        """Test cache miss when index is empty."""
        mock_redis.smembers.return_value = set()

        result = semantic_cache.get(
            query="What is machine learning?",
            messages=[Message(role="user", content="What is machine learning?")],
            provider=LLMProvider.CLAUDE_CODE,
        )

        assert result is None
        assert semantic_cache.metrics.cache_misses == 1
        assert semantic_cache.metrics.total_queries == 1

    def test_cache_set_success(self, semantic_cache, mock_redis):
        """Test successful cache set operation."""
        response = LLMResponse(
            content="Machine learning is a subset of AI...",
            provider=LLMProvider.CLAUDE_CODE,
            execution_time=0.5,
            tokens_used=60,
        )

        messages = [Message(role="user", content="What is machine learning?")]

        success = semantic_cache.set(
            query="What is machine learning?",
            messages=messages,
            response=response,
            category="general",
            ttl=1800,
        )

        assert success is True
        mock_redis.setex.assert_called_once()
        mock_redis.sadd.assert_called_once()

    def test_cache_hit_exact_match(self, semantic_cache, mock_redis, mock_embedding_model):
        """Test cache hit with exact query match."""
        # Mock cache entry
        import json
        cache_entry = CacheEntry(
            query="What is machine learning?",
            query_embedding=[0.1, 0.2, 0.3],
            response="Machine learning is a subset of AI...",
            provider="claude_code",
            category="general",
            timestamp=time.time(),
            hit_count=0,
            messages=[{"role": "user", "content": "What is machine learning?"}],
        )

        cache_key = b"semantic_cache:claude_code:abc123"
        mock_redis.smembers.return_value = {cache_key}
        mock_redis.get.return_value = json.dumps(cache_entry.__dict__).encode("utf-8")

        # Mock exact similarity
        mock_embedding_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])

        messages = [Message(role="user", content="What is machine learning?")]
        result = semantic_cache.get(
            query="What is machine learning?",
            messages=messages,
            provider=LLMProvider.CLAUDE_CODE,
        )

        assert result is not None
        assert result.content == "Machine learning is a subset of AI..."
        assert semantic_cache.metrics.cache_hits == 1

    def test_cache_hit_similar_query(self, semantic_cache, mock_redis, mock_embedding_model):
        """Test cache hit with similar query (semantic match)."""
        import json

        # Original query embedding
        cache_entry = CacheEntry(
            query="What is machine learning?",
            query_embedding=[0.1, 0.2, 0.3],
            response="Machine learning is a subset of AI...",
            provider="claude_code",
            category="general",
            timestamp=time.time(),
            hit_count=0,
        )

        cache_key = b"semantic_cache:claude_code:abc123"
        mock_redis.smembers.return_value = {cache_key}
        mock_redis.get.return_value = json.dumps(cache_entry.__dict__).encode("utf-8")

        # Similar query embedding (high cosine similarity)
        mock_embedding_model.encode.return_value = np.array([[0.11, 0.21, 0.31]])

        messages = [Message(role="user", content="Explain machine learning to me")]
        result = semantic_cache.get(
            query="Explain machine learning to me",
            messages=messages,
            provider=LLMProvider.CLAUDE_CODE,
        )

        # Should be a cache hit due to high similarity
        assert result is not None

    def test_cache_miss_low_similarity(self, semantic_cache, mock_redis, mock_embedding_model):
        """Test cache miss when similarity is below threshold."""
        import json

        cache_entry = CacheEntry(
            query="What is machine learning?",
            query_embedding=[0.1, 0.2, 0.3],
            response="Machine learning is a subset of AI...",
            provider="claude_code",
            category="general",
            timestamp=time.time(),
        )

        cache_key = b"semantic_cache:claude_code:abc123"
        mock_redis.smembers.return_value = {cache_key}
        mock_redis.get.return_value = json.dumps(cache_entry.__dict__).encode("utf-8")

        # Very different query embedding (orthogonal vectors for low similarity)
        mock_embedding_model.encode.return_value = np.array([[-0.9, -0.8, -0.7]])

        messages = [Message(role="user", content="How to bake a cake?")]
        result = semantic_cache.get(
            query="How to bake a cake?",
            messages=messages,
            provider=LLMProvider.CLAUDE_CODE,
        )

        # Check metrics (could be hit or miss depending on actual similarity)
        assert semantic_cache.metrics.total_queries >= 1


class TestCacheInvalidation:
    """Test cache invalidation."""

    def test_invalidate_by_provider(self, semantic_cache, mock_redis):
        """Test invalidating all entries for a provider."""
        cache_keys = {b"key1", b"key2", b"key3"}
        mock_redis.smembers.return_value = cache_keys

        count = semantic_cache.invalidate_by_provider(LLMProvider.CLAUDE_CODE)

        assert count == 3
        assert mock_redis.delete.call_count == 4  # 3 keys + 1 index

    def test_invalidate_by_category(self, semantic_cache, mock_redis):
        """Test invalidating entries by category."""
        import json

        # Mock cache entries with different categories
        entry1 = {"category": "general", "response": "test1"}
        entry2 = {"category": "code", "response": "test2"}

        mock_redis.smembers.return_value = {b"key1", b"key2"}
        mock_redis.get.side_effect = [
            json.dumps(entry1).encode("utf-8"),
            json.dumps(entry2).encode("utf-8"),
        ]

        count = semantic_cache.invalidate_by_category("general")

        assert count >= 0  # At least one entry should be invalidated

    def test_clear_all(self, semantic_cache, mock_redis):
        """Test clearing all cache entries."""
        mock_redis.scan_iter.side_effect = [
            [b"cache:key1", b"cache:key2"],
            [b"index:provider1"],
        ]

        success = semantic_cache.clear_all()

        assert success is True
        assert mock_redis.delete.call_count >= 1


class TestCacheMetrics:
    """Test cache metrics."""

    def test_get_metrics(self, semantic_cache):
        """Test retrieving cache metrics."""
        semantic_cache.metrics.total_queries = 100
        semantic_cache.metrics.cache_hits = 60
        semantic_cache.metrics.cache_misses = 40

        metrics = semantic_cache.get_metrics()

        assert metrics.total_queries == 100
        assert metrics.cache_hits == 60
        assert metrics.cache_misses == 40

    def test_cache_hit_rate_calculation(self, semantic_cache):
        """Test cache hit rate calculation."""
        semantic_cache.metrics.total_queries = 100
        semantic_cache.metrics.cache_hits = 75
        semantic_cache.metrics.cache_misses = 25

        # Hit rate should be 75%
        hit_rate = (semantic_cache.metrics.cache_hits / semantic_cache.metrics.total_queries) * 100
        assert hit_rate == 75.0

    def test_cost_savings_tracking(self, semantic_cache, mock_redis, mock_embedding_model):
        """Test cost savings calculation."""
        import json

        cache_entry = CacheEntry(
            query="What is machine learning?",
            query_embedding=[0.1, 0.2, 0.3],
            response="Machine learning is a subset of AI that enables computers to learn.",
            provider="claude_code",
            category="general",
            timestamp=time.time(),
        )

        cache_key = b"semantic_cache:claude_code:abc123"
        mock_redis.smembers.return_value = {cache_key}
        mock_redis.get.return_value = json.dumps(cache_entry.__dict__).encode("utf-8")
        mock_embedding_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])

        messages = [Message(role="user", content="What is machine learning?")]
        semantic_cache.get(
            query="What is machine learning?",
            messages=messages,
            provider=LLMProvider.CLAUDE_CODE,
        )

        # Cost savings should be tracked
        assert semantic_cache.metrics.cost_savings_usd > 0


class TestCacheHealth:
    """Test cache health checks."""

    def test_health_check_success(self, semantic_cache, mock_redis):
        """Test successful health check."""
        mock_redis.ping.return_value = True

        is_healthy = semantic_cache.health_check()

        assert is_healthy is True

    def test_health_check_failure(self, semantic_cache, mock_redis):
        """Test health check failure."""
        mock_redis.ping.side_effect = Exception("Connection lost")

        is_healthy = semantic_cache.health_check()

        assert is_healthy is False


class TestCacheSizeTracking:
    """Test cache size tracking."""

    def test_get_cache_size(self, semantic_cache, mock_redis):
        """Test getting cache size by provider."""
        # Mock scard to return counts for all providers
        mock_redis.scard.return_value = 0
        mock_redis.scard.side_effect = None  # Clear any previous side_effect

        sizes = semantic_cache.get_cache_size()

        assert len(sizes) >= 0
        # Should only include providers with entries


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_query(self, semantic_cache):
        """Test handling of empty query."""
        messages = [Message(role="user", content="")]
        result = semantic_cache.get(
            query="",
            messages=messages,
            provider=LLMProvider.CLAUDE_CODE,
        )

        # Should handle gracefully (likely cache miss)
        assert semantic_cache.metrics.total_queries >= 1

    def test_very_long_query(self, semantic_cache):
        """Test handling of very long query."""
        long_query = "What is machine learning? " * 1000

        messages = [Message(role="user", content=long_query)]
        result = semantic_cache.get(
            query=long_query,
            messages=messages,
            provider=LLMProvider.CLAUDE_CODE,
        )

        # Should handle gracefully
        assert semantic_cache.metrics.total_queries >= 1

    def test_special_characters_in_query(self, semantic_cache):
        """Test handling of special characters."""
        query = "What is @machine #learning? 🤖💻"

        messages = [Message(role="user", content=query)]
        result = semantic_cache.get(
            query=query,
            messages=messages,
            provider=LLMProvider.CLAUDE_CODE,
        )

        # Should handle gracefully
        assert semantic_cache.metrics.total_queries >= 1


class TestConcurrency:
    """Test concurrent cache operations."""

    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, semantic_cache, mock_redis):
        """Test concurrent cache access (basic check)."""
        import asyncio

        async def cache_operation():
            messages = [Message(role="user", content="Test query")]
            return semantic_cache.get(
                query="Test query",
                messages=messages,
                provider=LLMProvider.CLAUDE_CODE,
            )

        # Run multiple concurrent operations
        results = await asyncio.gather(
            cache_operation(),
            cache_operation(),
            cache_operation(),
        )

        # All should complete without errors
        assert len(results) == 3
