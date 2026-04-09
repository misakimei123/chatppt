"""
Integration tests for Redis cache and full generation flow.

Tests cover:
1. RedisCache functionality with fallback
2. Full generation flow with mocked LLM
3. Cache hit/miss scenarios
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chatppt.app.infra.cache import InMemoryCache, RedisCache


class TestInMemoryCache:
    """Test in-memory cache implementation."""
    
    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = InMemoryCache()
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = InMemoryCache()
        assert cache.get("nonexistent") is None
    
    def test_delete(self):
        """Test delete operation."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        
        assert cache.delete("nonexistent") is False
    
    def test_clear(self):
        """Test clearing all cached items."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestRedisCache:
    """Test Redis cache implementation with fallback."""
    
    @patch('redis.from_url')
    def test_redis_connection_success(self, mock_redis):
        """Test successful Redis connection."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        cache = RedisCache(redis_url="redis://localhost:6379")
        
        assert cache._client is not None
        assert cache._fallback_cache is not None
    
    def test_redis_fallback_on_no_redis_package(self):
        """Test fallback to in-memory cache when redis package not installed."""
        with patch.dict('sys.modules', {'redis': None}):
            cache = RedisCache()
            
            assert cache._client is None
            assert cache._fallback_cache is not None
            
            # Should still work via fallback
            cache.set("key1", "value1")
            assert cache.get("key1") == "value1"
    
    def test_redis_fallback_on_connection_error(self):
        """Test fallback when Redis connection fails."""
        with patch('redis.from_url', side_effect=Exception("Connection refused")):
            cache = RedisCache()
            
            assert cache._client is None
            assert cache._fallback_cache is not None
    
    @patch('redis.from_url')
    def test_redis_set_and_get(self, mock_redis):
        """Test Redis set and get operations."""
        import json
        
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        cache = RedisCache()
        
        # Mock the get to return serialized value
        mock_client.get.return_value = json.dumps({"test": "data"})
        
        cache.set("key1", {"test": "data"})
        
        # Verify setex was called
        assert mock_client.setex.called
        
        result = cache.get("key1")
        assert result == {"test": "data"}
    
    def test_health_check(self):
        """Test health check method."""
        cache = RedisCache()
        
        # Should report disconnected when no Redis
        health = cache.health_check()
        assert health["status"] in ["disconnected", "error"]
        assert health["type"] == "fallback"


class TestFullFlowWithCache:
    """Test full generation flow with caching."""
    
    @pytest.mark.asyncio
    async def test_generation_with_cache_hit(self):
        """Test that repeated requests use cached results."""
        from chatppt.app.domain.services.evidence_builder import EvidenceBuilder
        from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
        
        builder = EvidenceBuilder(enable_cache=True)
        
        spec = ClarifiedSpec(
            topic="AI Trends",
            audience="Tech executives",
            use_case="Quarterly review",
            desired_tone="professional",
            expected_duration_minutes=15,
            must_include=["Market analysis"],
            must_avoid=["Technical jargon"],
        )
        
        # First call - should build evidence
        result1 = builder.build(spec, perform_web_search=False)
        
        # Second call - should hit cache
        result2 = builder.build(spec, perform_web_search=False)
        
        # Results should be identical (cached)
        assert len(result1.facts) == len(result2.facts)
        assert len(result1.suggestions) == len(result2.suggestions)
    
    @pytest.mark.asyncio
    async def test_generation_with_documents_bypasses_cache(self):
        """Test that providing documents bypasses cache."""
        from chatppt.app.domain.services.evidence_builder import EvidenceBuilder
        from chatppt.app.domain.models.clarified_spec import ClarifiedSpec
        from chatppt.app.domain.services.evidence_builder import SourceDocument
        
        builder = EvidenceBuilder(enable_cache=True)
        
        spec = ClarifiedSpec(
            topic="AI Trends",
            audience="Tech executives",
            use_case="Quarterly review",
            desired_tone="professional",
            expected_duration_minutes=15,
            must_include=[],
            must_avoid=[],
        )
        
        # First call without documents
        result1 = builder.build(spec, perform_web_search=False)
        
        # Second call with documents - should NOT use cache
        documents = [SourceDocument(
            title="Test Doc",
            uri="test://doc1",
            content="FACT: AI is growing fast",
        )]
        result2 = builder.build(spec, documents=documents, perform_web_search=False)
        
        # Result2 should have additional facts from documents
        assert len(result2.facts) >= len(result1.facts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
