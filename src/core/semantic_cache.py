"""Semantic caching layer using embeddings for similarity matching.

This module provides a Redis-based semantic cache that uses sentence embeddings
to match similar queries and return cached responses, reducing API costs and
improving response times.
"""

import time
import json
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

import redis
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import structlog

from src.models.schemas import LLMProvider, LLMResponse, Message
from src.core.config import settings

logger = structlog.get_logger()


@dataclass
class CacheEntry:
    """Cached LLM response with metadata."""

    query: str
    query_embedding: List[float]
    response: str
    provider: str
    category: str
    timestamp: float
    hit_count: int = 0
    messages: List[Dict[str, Any]] = None  # Full conversation context


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_similarity_searches: int = 0
    avg_similarity_search_time_ms: float = 0.0
    avg_cache_save_time_ms: float = 0.0
    cost_savings_usd: float = 0.0


class SemanticCache:
    """Semantic caching using Redis and sentence embeddings."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.85,
        default_ttl: int = 3600,
    ):
        """Initialize semantic cache.

        Args:
            redis_url: Redis connection URL (default: from settings)
            embedding_model: Sentence transformer model name
            similarity_threshold: Minimum cosine similarity for cache hit (0-1)
            default_ttl: Default cache TTL in seconds (default: 1 hour)
        """
        self.logger = logger.bind(component="semantic_cache")
        self.similarity_threshold = similarity_threshold
        self.default_ttl = default_ttl

        # Initialize Redis
        redis_url = redis_url or getattr(settings, "redis_url", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(
                redis_url, decode_responses=False, socket_timeout=5
            )
            self.redis_client.ping()
            self.logger.info("redis_connected", url=redis_url)
        except Exception as e:
            self.logger.error("redis_connection_failed", url=redis_url, error=str(e))
            raise

        # Initialize embedding model (reuse if already loaded globally)
        try:
            self.logger.info("loading_embedding_model", model=embedding_model)
            self.embedding_model = SentenceTransformer(embedding_model)
            self.logger.info("embedding_model_loaded", model=embedding_model)
        except Exception as e:
            self.logger.error("embedding_model_load_failed", error=str(e))
            raise

        # Metrics
        self.metrics = CacheMetrics()

        # Cache key prefixes
        self.CACHE_PREFIX = "semantic_cache:"
        self.INDEX_KEY = "semantic_cache:index"
        self.METRICS_KEY = "semantic_cache:metrics"

    def _generate_cache_key(self, query: str, provider: str) -> str:
        """Generate unique cache key from query and provider.

        Args:
            query: User query
            provider: LLM provider name

        Returns:
            Unique cache key
        """
        # Use hash of query + provider to create deterministic key
        content = f"{query}|{provider}"
        key_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{self.CACHE_PREFIX}{provider}:{key_hash}"

    def _encode_query(self, query: str) -> np.ndarray:
        """Encode query to embedding vector.

        Args:
            query: User query

        Returns:
            Embedding vector
        """
        return self.embedding_model.encode([query], convert_to_numpy=True)[0]

    def get(
        self,
        query: str,
        messages: List[Message],
        provider: LLMProvider,
    ) -> Optional[LLMResponse]:
        """Retrieve cached response using semantic similarity.

        Args:
            query: User query
            messages: Full conversation context
            provider: LLM provider

        Returns:
            Cached LLMResponse if found, None otherwise
        """
        start_time = time.time()
        self.metrics.total_queries += 1

        try:
            # Encode query
            query_embedding = self._encode_query(query)

            # Get all cache entries for this provider from index
            index_key = f"{self.INDEX_KEY}:{provider.value}"
            cache_keys = self.redis_client.smembers(index_key)

            if not cache_keys:
                self.metrics.cache_misses += 1
                self.logger.debug("cache_miss_empty_index", provider=provider.value)
                return None

            # Find most similar cached entry
            best_similarity = 0.0
            best_entry: Optional[CacheEntry] = None
            best_key: Optional[bytes] = None

            for cache_key in cache_keys:
                try:
                    cached_data = self.redis_client.get(cache_key)
                    if not cached_data:
                        # Entry expired or deleted
                        self.redis_client.srem(index_key, cache_key)
                        continue

                    entry_dict = json.loads(cached_data.decode("utf-8"))
                    cached_embedding = np.array(entry_dict["query_embedding"])

                    # Calculate similarity
                    similarity = cosine_similarity(
                        [query_embedding], [cached_embedding]
                    )[0][0]

                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_entry = CacheEntry(**entry_dict)
                        best_key = cache_key

                except Exception as e:
                    self.logger.warning(
                        "cache_entry_read_failed", key=cache_key, error=str(e)
                    )
                    continue

            # Check if best match exceeds threshold
            search_time = (time.time() - start_time) * 1000
            self.metrics.total_similarity_searches += 1
            self.metrics.avg_similarity_search_time_ms = (
                (self.metrics.avg_similarity_search_time_ms * (self.metrics.total_similarity_searches - 1))
                + search_time
            ) / self.metrics.total_similarity_searches

            if best_similarity >= self.similarity_threshold and best_entry:
                # Cache hit!
                self.metrics.cache_hits += 1

                # Increment hit count
                best_entry.hit_count += 1
                self.redis_client.setex(
                    best_key,
                    self.default_ttl,
                    json.dumps(asdict(best_entry)).encode("utf-8"),
                )

                self.logger.info(
                    "cache_hit",
                    provider=provider.value,
                    similarity=f"{best_similarity:.3f}",
                    threshold=self.similarity_threshold,
                    hit_count=best_entry.hit_count,
                    search_time_ms=f"{search_time:.2f}",
                )

                # Estimate cost savings (rough estimate)
                # Assume average: 1000 tokens = $0.01 for most providers
                estimated_tokens = len(best_entry.response.split()) * 1.3
                estimated_cost = (estimated_tokens / 1000) * 0.01
                self.metrics.cost_savings_usd += estimated_cost

                # Return cached response
                return LLMResponse(
                    content=best_entry.response,
                    provider=provider,
                    execution_time=0.0,  # Cached, no execution time
                    metadata={"cached": True, "similarity": best_similarity},
                )
            else:
                # Cache miss
                self.metrics.cache_misses += 1
                self.logger.debug(
                    "cache_miss_low_similarity",
                    provider=provider.value,
                    best_similarity=f"{best_similarity:.3f}",
                    threshold=self.similarity_threshold,
                    search_time_ms=f"{search_time:.2f}",
                )
                return None

        except Exception as e:
            self.logger.error("cache_get_failed", error=str(e))
            self.metrics.cache_misses += 1
            return None

    def set(
        self,
        query: str,
        messages: List[Message],
        response: LLMResponse,
        category: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache LLM response with semantic indexing.

        Args:
            query: User query
            messages: Full conversation context
            response: LLM response to cache
            category: Task category
            ttl: Cache TTL in seconds (default: use default_ttl)

        Returns:
            True if cached successfully, False otherwise
        """
        start_time = time.time()
        ttl = ttl or self.default_ttl

        try:
            # Encode query
            query_embedding = self._encode_query(query)

            # Create cache entry
            entry = CacheEntry(
                query=query,
                query_embedding=query_embedding.tolist(),
                response=response.content,
                provider=response.provider.value,
                category=category,
                timestamp=time.time(),
                hit_count=0,
                messages=[{"role": msg.role, "content": msg.content} for msg in messages],
            )

            # Generate cache key
            cache_key = self._generate_cache_key(query, response.provider.value)

            # Store in Redis with TTL
            self.redis_client.setex(
                cache_key, ttl, json.dumps(asdict(entry)).encode("utf-8")
            )

            # Add to provider index
            index_key = f"{self.INDEX_KEY}:{response.provider.value}"
            self.redis_client.sadd(index_key, cache_key)

            save_time = (time.time() - start_time) * 1000
            # Update average save time (handle first save)
            if self.metrics.total_queries > 0:
                self.metrics.avg_cache_save_time_ms = (
                    (self.metrics.avg_cache_save_time_ms * (self.metrics.total_queries - 1))
                    + save_time
                ) / self.metrics.total_queries
            else:
                self.metrics.avg_cache_save_time_ms = save_time

            self.logger.info(
                "cache_set",
                provider=response.provider.value,
                category=category,
                ttl=ttl,
                save_time_ms=f"{save_time:.2f}",
            )

            return True

        except Exception as e:
            self.logger.error("cache_set_failed", error=str(e))
            return False

    def invalidate_by_provider(self, provider: LLMProvider) -> int:
        """Invalidate all cache entries for a provider.

        Args:
            provider: LLM provider

        Returns:
            Number of entries invalidated
        """
        try:
            index_key = f"{self.INDEX_KEY}:{provider.value}"
            cache_keys = self.redis_client.smembers(index_key)

            count = 0
            for cache_key in cache_keys:
                self.redis_client.delete(cache_key)
                count += 1

            # Clear index
            self.redis_client.delete(index_key)

            self.logger.info("cache_invalidated", provider=provider.value, count=count)
            return count

        except Exception as e:
            self.logger.error("cache_invalidation_failed", error=str(e))
            return 0

    def invalidate_by_category(self, category: str) -> int:
        """Invalidate all cache entries for a category.

        Args:
            category: Task category

        Returns:
            Number of entries invalidated
        """
        try:
            count = 0
            # Iterate through all provider indexes
            for provider in LLMProvider:
                index_key = f"{self.INDEX_KEY}:{provider.value}"
                cache_keys = self.redis_client.smembers(index_key)

                for cache_key in cache_keys:
                    try:
                        cached_data = self.redis_client.get(cache_key)
                        if not cached_data:
                            continue

                        entry_dict = json.loads(cached_data.decode("utf-8"))
                        if entry_dict.get("category") == category:
                            self.redis_client.delete(cache_key)
                            self.redis_client.srem(index_key, cache_key)
                            count += 1

                    except Exception:
                        continue

            self.logger.info("cache_invalidated_by_category", category=category, count=count)
            return count

        except Exception as e:
            self.logger.error("cache_invalidation_failed", error=str(e))
            return 0

    def clear_all(self) -> bool:
        """Clear all cache entries.

        Returns:
            True if successful
        """
        try:
            # Delete all cache entries
            pattern = f"{self.CACHE_PREFIX}*"
            keys = list(self.redis_client.scan_iter(match=pattern))
            if keys:
                self.redis_client.delete(*keys)

            # Delete all indexes
            index_pattern = f"{self.INDEX_KEY}:*"
            index_keys = list(self.redis_client.scan_iter(match=index_pattern))
            if index_keys:
                self.redis_client.delete(*index_keys)

            self.logger.info("cache_cleared", total_keys=len(keys) + len(index_keys))
            return True

        except Exception as e:
            self.logger.error("cache_clear_failed", error=str(e))
            return False

    def get_metrics(self) -> CacheMetrics:
        """Get cache performance metrics.

        Returns:
            Cache metrics
        """
        # Calculate cache hit rate
        hit_rate = (
            (self.metrics.cache_hits / self.metrics.total_queries * 100)
            if self.metrics.total_queries > 0
            else 0.0
        )

        self.logger.info(
            "cache_metrics",
            total_queries=self.metrics.total_queries,
            cache_hits=self.metrics.cache_hits,
            cache_misses=self.metrics.cache_misses,
            hit_rate=f"{hit_rate:.1f}%",
            cost_savings=f"${self.metrics.cost_savings_usd:.2f}",
        )

        return self.metrics

    def get_cache_size(self) -> Dict[str, int]:
        """Get cache size by provider.

        Returns:
            Dict mapping provider to cache entry count
        """
        sizes = {}
        for provider in LLMProvider:
            index_key = f"{self.INDEX_KEY}:{provider.value}"
            count = self.redis_client.scard(index_key)
            if count > 0:
                sizes[provider.value] = count

        return sizes

    def health_check(self) -> bool:
        """Check cache health.

        Returns:
            True if healthy
        """
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            self.logger.error("cache_health_check_failed", error=str(e))
            return False


# Global cache instance
_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache(
    redis_url: Optional[str] = None,
    embedding_model: str = "all-MiniLM-L6-v2",
    similarity_threshold: float = 0.85,
    default_ttl: int = 3600,
) -> SemanticCache:
    """Get global semantic cache instance (singleton).

    Args:
        redis_url: Redis connection URL
        embedding_model: Sentence transformer model
        similarity_threshold: Minimum similarity for cache hit (0-1)
        default_ttl: Default cache TTL in seconds

    Returns:
        SemanticCache instance
    """
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache(
            redis_url=redis_url,
            embedding_model=embedding_model,
            similarity_threshold=similarity_threshold,
            default_ttl=default_ttl,
        )
    return _semantic_cache
