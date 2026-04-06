"""
Unit tests for the cache layer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


class TestCacheManager:
    """Tests for CacheManager class."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        mock = MagicMock()
        mock.get = AsyncMock(return_value=None)
        mock.setex = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=1)
        mock.scan_iter = MagicMock(return_value=iter([]))
        mock.ping = AsyncMock(return_value=True)
        mock.close = AsyncMock()
        return mock

    @pytest.fixture
    def cache_manager(self, mock_redis_client):
        """Create a CacheManager with mocked Redis."""
        from app.core.cache import CacheManager

        manager = CacheManager()
        manager._client = mock_redis_client
        manager._connected = True
        return manager

    # ========================================================================
    # Basic Operations Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_connected(self):
        """Test get returns None when cache is not connected."""
        from app.core.cache import CacheManager

        manager = CacheManager()
        manager._connected = False

        result = await manager.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_when_key_not_found(self, cache_manager, mock_redis_client):
        """Test get returns None when key doesn't exist."""
        mock_redis_client.get.return_value = None

        result = await cache_manager.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_decoded_value(self, cache_manager, mock_redis_client):
        """Test get returns decoded JSON value."""
        test_data = {"foo": "bar", "count": 42}
        mock_redis_client.get.return_value = json.dumps(test_data)

        result = await cache_manager.get("test_key")
        assert result == test_data

    @pytest.mark.asyncio
    async def test_set_stores_json_serialized(self, cache_manager, mock_redis_client):
        """Test set stores JSON serialized value."""
        test_data = {"foo": "bar", "count": 42}

        result = await cache_manager.set("test_key", test_data, ttl=60)

        assert result is True
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 60
        assert json.loads(call_args[0][2]) == test_data

    @pytest.mark.asyncio
    async def test_set_returns_false_when_not_connected(self):
        """Test set returns False when cache is not connected."""
        from app.core.cache import CacheManager

        manager = CacheManager()
        manager._connected = False

        result = await manager.set("test_key", {"data": "value"}, ttl=60)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_removes_key(self, cache_manager, mock_redis_client):
        """Test delete removes a key."""
        mock_redis_client.delete.return_value = 1

        result = await cache_manager.delete("test_key")

        assert result is True
        mock_redis_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_pattern_removes_matching_keys(self, cache_manager, mock_redis_client):
        """Test delete_pattern removes all matching keys."""
        keys = ["discover:jobs:abc123", "discover:jobs:def456"]
        mock_redis_client.scan_iter.return_value = iter(keys)
        mock_redis_client.delete.return_value = 2

        result = await cache_manager.delete_pattern("discover:jobs:*")

        assert result == 2
        mock_redis_client.delete.assert_called_once_with(*keys)

    # ========================================================================
    # Discovery Cache Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_get_discover_jobs_returns_cached(self, cache_manager, mock_redis_client):
        """Test get_discover_jobs returns cached result."""
        cached_jobs = [
            {"id": "job1", "title": "Backend Engineer"},
            {"id": "job2", "title": "Frontend Engineer"},
        ]
        mock_redis_client.get.return_value = json.dumps(cached_jobs)

        result = await cache_manager.get_discover_jobs(
            skills=["Go", "Python"],
            city="上海",
            limit=20,
            offset=0,
        )

        assert result == cached_jobs
        # Verify the key contains the expected components
        call_args = mock_redis_client.get.call_args[0][0]
        assert "discover:jobs" in call_args

    @pytest.mark.asyncio
    async def test_set_discover_jobs_caches_result(self, cache_manager, mock_redis_client):
        """Test set_discover_jobs caches the result."""
        jobs = [{"id": "job1", "title": "Backend Engineer"}]

        result = await cache_manager.set_discover_jobs(
            data=jobs,
            skills=["Go"],
            city="北京",
            limit=10,
            offset=5,
        )

        assert result is True
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        # Verify TTL is 60 seconds (DISCOVER_TTL)
        assert call_args[0][1] == 60

    @pytest.mark.asyncio
    async def test_get_discover_profiles_returns_cached(self, cache_manager, mock_redis_client):
        """Test get_discover_profiles returns cached result."""
        cached_profiles = [
            {"id": "prof1", "nickname": "张三"},
            {"id": "prof2", "nickname": "李四"},
        ]
        mock_redis_client.get.return_value = json.dumps(cached_profiles)

        result = await cache_manager.get_discover_profiles(
            skills=["Go", "Kubernetes"],
            city="上海",
            limit=20,
            offset=0,
        )

        assert result == cached_profiles

    @pytest.mark.asyncio
    async def test_set_discover_profiles_caches_result(self, cache_manager, mock_redis_client):
        """Test set_discover_profiles caches the result."""
        profiles = [{"id": "prof1", "nickname": "测试"}]

        result = await cache_manager.set_discover_profiles(
            data=profiles,
            skills=["Python"],
            city="深圳",
            limit=15,
            offset=0,
        )

        assert result is True
        mock_redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_discover_cache(self, cache_manager, mock_redis_client):
        """Test invalidate_discover_cache removes all discover keys."""
        # Track deleted keys
        deleted_keys = []

        async def mock_scan_iter(match):
            if "jobs" in match:
                return iter(["discover:jobs:abc", "discover:jobs:def"])
            else:
                return iter(["discover:profiles:xyz"])

        async def mock_delete(*keys):
            deleted_keys.extend(keys)
            return len(keys)

        mock_redis_client.scan_iter = mock_scan_iter
        mock_redis_client.delete = mock_delete

        count = await cache_manager.invalidate_discover_cache()

        assert count == 3  # 2 job keys + 1 profile key

    # ========================================================================
    # Upload Chunk Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_save_upload_chunk(self, cache_manager, mock_redis_client):
        """Test saving an upload chunk."""
        upload_id = "upload_123"
        chunk_index = 0
        chunk_data = b"chunk content here"

        result = await cache_manager.save_upload_chunk(upload_id, chunk_index, chunk_data)

        assert result is True
        call_args = mock_redis_client.setex.call_args
        assert f"{upload_id}:{chunk_index}" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_upload_chunk(self, cache_manager, mock_redis_client):
        """Test getting an upload chunk."""
        upload_id = "upload_123"
        chunk_index = 0
        chunk_data = b"stored chunk data"
        mock_redis_client.get.return_value = chunk_data

        result = await cache_manager.get_upload_chunk(upload_id, chunk_index)

        assert result == chunk_data

    @pytest.mark.asyncio
    async def test_get_uploaded_chunks(self, cache_manager, mock_redis_client):
        """Test getting list of uploaded chunk indices."""
        upload_id = "upload_123"

        async def mock_scan_iter(match):
            return iter([
                f"upload:chunk:{upload_id}:0",
                f"upload:chunk:{upload_id}:2",
                f"upload:chunk:{upload_id}:5",
            ])

        mock_redis_client.scan_iter = mock_scan_iter

        result = await cache_manager.get_uploaded_chunks(upload_id)

        assert result == [0, 2, 5]

    @pytest.mark.asyncio
    async def test_delete_upload_chunks(self, cache_manager, mock_redis_client):
        """Test deleting all chunks for an upload."""
        upload_id = "upload_123"

        async def mock_scan_iter(match):
            return iter([
                f"upload:chunk:{upload_id}:0",
                f"upload:chunk:{upload_id}:1",
            ])

        mock_redis_client.scan_iter = mock_scan_iter
        mock_redis_client.delete.return_value = 2

        result = await cache_manager.delete_upload_chunks(upload_id)

        assert result == 2

    @pytest.mark.asyncio
    async def test_save_upload_metadata(self, cache_manager, mock_redis_client):
        """Test saving upload metadata."""
        upload_id = "upload_123"
        metadata = {
            "filename": "test.pdf",
            "file_size": 1024000,
            "total_chunks": 3,
            "expected_hash": "abc123",
        }

        result = await cache_manager.save_upload_metadata(upload_id, metadata)

        assert result is True
        call_args = mock_redis_client.setex.call_args
        assert upload_id in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_upload_metadata(self, cache_manager, mock_redis_client):
        """Test getting upload metadata."""
        upload_id = "upload_123"
        metadata = {
            "filename": "test.pdf",
            "file_size": 1024000,
        }
        mock_redis_client.get.return_value = json.dumps(metadata)

        result = await cache_manager.get_upload_metadata(upload_id)

        assert result == metadata

    @pytest.mark.asyncio
    async def test_delete_upload_metadata(self, cache_manager, mock_redis_client):
        """Test deleting upload metadata."""
        upload_id = "upload_123"
        mock_redis_client.delete.return_value = 1

        result = await cache_manager.delete_upload_metadata(upload_id)

        assert result is True

    # ========================================================================
    # Cache Key Generation Tests
    # ========================================================================

    def test_make_hash_creates_consistent_hash(self, cache_manager):
        """Test that _make_hash creates consistent hashes."""
        data = "test data"

        hash1 = cache_manager._make_hash(data)
        hash2 = cache_manager._make_hash(data)

        assert hash1 == hash2
        assert len(hash1) == 16  # First 16 chars of SHA256

    def test_make_hash_different_for_different_inputs(self, cache_manager):
        """Test that different inputs produce different hashes."""
        hash1 = cache_manager._make_hash("data1")
        hash2 = cache_manager._make_hash("data2")

        assert hash1 != hash2

    def test_discover_jobs_cache_key_is_deterministic(self, cache_manager):
        """Test discover_jobs cache key is same for same params."""
        params = {
            "skills": ["Go", "Python"],
            "city": "上海",
            "limit": 20,
            "offset": 0,
        }

        key1 = cache_manager._discover_jobs_cache_key(**params)
        key2 = cache_manager._discover_jobs_cache_key(**params)

        assert key1 == key2

    def test_discover_jobs_cache_key_sorts_skills(self, cache_manager):
        """Test discover_jobs cache key is same regardless of skill order."""
        key1 = cache_manager._discover_jobs_cache_key(
            skills=["Go", "Python"],
            city="上海",
        )
        key2 = cache_manager._discover_jobs_cache_key(
            skills=["Python", "Go"],
            city="上海",
        )

        assert key1 == key2

    def test_discover_jobs_cache_key_different_for_different_params(self, cache_manager):
        """Test different params produce different cache keys."""
        key1 = cache_manager._discover_jobs_cache_key(city="上海")
        key2 = cache_manager._discover_jobs_cache_key(city="北京")

        assert key1 != key2


class TestCacheIntegration:
    """Integration-style tests for cache with real JSON serialization."""

    @pytest.fixture
    def cache_manager(self):
        """Create a CacheManager for testing JSON serialization."""
        from app.core.cache import CacheManager

        manager = CacheManager()
        manager._connected = True
        manager._client = MagicMock()
        return manager

    def test_serializes_datetime_objects(self, cache_manager):
        """Test that datetime objects in data are properly serialized."""
        from datetime import datetime, timezone

        data = {
            "created_at": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "name": "Test",
        }

        # Should not raise
        serialized = json.dumps(data, default=str)
        assert "2024-01-15" in serialized

    def test_serializes_nested_data(self, cache_manager):
        """Test that nested data structures are properly serialized."""
        data = {
            "profile": {
                "name": "张三",
                "skills": [
                    {"name": "Go", "level": "expert"},
                    {"name": "Python", "level": "intermediate"},
                ],
            },
            "count": 42,
        }

        serialized = json.dumps(data, default=str)
        deserialized = json.loads(serialized)

        assert deserialized["profile"]["name"] == "张三"
        assert len(deserialized["profile"]["skills"]) == 2
