from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache for development and testing."""
    
    def __init__(self, ttl_seconds: int = 3600):
        self._store: dict[str, object] = {}
        self._ttl = ttl_seconds
    
    def get(self, key: str) -> Any:
        """Get value from cache."""
        return self._store.get(key)
    
    def set(self, key: str, value: object, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL override."""
        self._store[key] = value
        logger.debug(f"Cached key: {key}")
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._store.clear()


class RedisCache:
    """
    Redis-backed cache for production use with support for:
    - TTL-based expiration
    - JSON serialization/deserialization
    - Connection pooling
    - Automatic fallback to in-memory cache on connection failure
    """
    
    def __init__(
        self,
        redis_url: str | None = None,
        prefix: str = "chatppt:",
        default_ttl: int = 3600,
        enable_fallback: bool = True,
    ):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.enable_fallback = enable_fallback
        self._client: Any = None
        self._fallback_cache: InMemoryCache | None = None
        
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Redis client with lazy loading."""
        try:
            import redis
            
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            self._client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
            
            if self.enable_fallback:
                self._fallback_cache = InMemoryCache(ttl_seconds=self.default_ttl)
                
        except ImportError:
            logger.warning("Redis package not installed. Falling back to in-memory cache.")
            self._client = None
            if self.enable_fallback:
                self._fallback_cache = InMemoryCache(ttl_seconds=self.default_ttl)
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using fallback cache.")
            self._client = None
            if self.enable_fallback:
                self._fallback_cache = InMemoryCache(ttl_seconds=self.default_ttl)
    
    def _make_key(self, key: str) -> str:
        """Add prefix to cache key."""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Any:
        """
        Get value from Redis cache.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized value or None if not found
        """
        full_key = self._make_key(key)
        
        if self._client is None:
            if self._fallback_cache:
                logger.debug(f"Using fallback cache for key: {key}")
                return self._fallback_cache.get(full_key)
            return None
        
        try:
            value = self._client.get(full_key)
            if value is None:
                return None
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize cached value for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            if self._fallback_cache:
                return self._fallback_cache.get(full_key)
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in Redis cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (optional, uses default if not specified)
            
        Returns:
            True if successful, False otherwise
        """
        full_key = self._make_key(key)
        ttl = ttl or self.default_ttl
        
        if self._client is None:
            if self._fallback_cache:
                logger.debug(f"Using fallback cache to set key: {key}")
                self._fallback_cache.set(full_key, value, ttl=ttl)
                return True
            return False
        
        try:
            serialized = json.dumps(value)
            self._client.setex(full_key, ttl, serialized)
            logger.debug(f"Cached key: {full_key} with TTL: {ttl}s")
            return True
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize value for key {key}: {e}")
            if self._fallback_cache:
                self._fallback_cache.set(full_key, value, ttl=ttl)
                return True
            return False
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            if self._fallback_cache:
                self._fallback_cache.set(full_key, value, ttl=ttl)
                return True
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        full_key = self._make_key(key)
        
        if self._client is None:
            if self._fallback_cache:
                return self._fallback_cache.delete(full_key)
            return False
        
        try:
            self._client.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            if self._fallback_cache:
                return self._fallback_cache.delete(full_key)
            return False
    
    def clear(self) -> None:
        """Clear all cached items with the configured prefix."""
        if self._client is None:
            if self._fallback_cache:
                self._fallback_cache.clear()
            return
        
        try:
            keys = self._client.keys(f"{self.prefix}*")
            if keys:
                self._client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached items")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            if self._fallback_cache:
                self._fallback_cache.clear()
    
    def health_check(self) -> dict[str, Any]:
        """Check Redis connection health."""
        if self._client is None:
            return {"status": "disconnected", "type": "fallback" if self._fallback_cache else "none"}
        
        try:
            self._client.ping()
            info = self._client.info("server")
            return {
                "status": "connected",
                "type": "redis",
                "version": info.get("redis_version", "unknown"),
            }
        except Exception as e:
            return {"status": "error", "type": "fallback" if self._fallback_cache else "none", "error": str(e)}
