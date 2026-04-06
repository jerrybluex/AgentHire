"""
Redis Cache Layer for AgentHire
Provides caching for hot data like Discovery API results.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import get_settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis cache manager with TTL and active invalidation support.

    Features:
    - Connection pooling
    - TTL-based expiration
    - Active cache invalidation
    - JSON serialization for complex data
    - Cache key naming convention
    """

    # Cache key prefixes
    PREFIX_DISCOVER_JOBS = "discover:jobs"
    PREFIX_DISCOVER_PROFILES = "discover:profiles"
    PREFIX_UPLOAD_CHUNK = "upload:chunk"
    PREFIX_UPLOAD_META = "upload:meta"

    # Default TTL values (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    DISCOVER_TTL = 60  # 1 minute for discovery data
    UPLOAD_CHUNK_TTL = 3600  # 1 hour for upload chunks
    UPLOAD_META_TTL = 86400  # 24 hours for upload metadata

    def __init__(self):
        self._client: Optional[Redis] = None
        self._connected = False

    @property
    def client(self) -> Redis:
        """Get or create Redis client."""
        if self._client is None:
            settings = get_settings()
            self._client = redis.from_url(
                str(settings.redis.url),
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def connect(self) -> None:
        """Initialize Redis connection."""
        try:
            await self.client.ping()
            self._connected = True
            logger.info("Redis cache connected successfully")
        except RedisError as e:
            logger.warning(f"Redis connection failed: {e}. Cache will be disabled.")
            self._connected = False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._connected = False
            logger.info("Redis cache connection closed")

    def _make_hash(self, data: str) -> str:
        """Create SHA256 hash of string data for cache key generation."""
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _make_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from prefix and parameters.

        Format: prefix:hash(args:kwargs)
        """
        parts = [prefix]
        if args:
            parts.append(f"args:{','.join(str(a) for a in args)}")
        if kwargs:
            sorted_kvs = sorted(f"{k}={v}" for k, v in kwargs.items())
            parts.append(f"kwargs:{','.join(sorted_kvs)}")
        key_data = ":".join(parts)
        return f"{prefix}:{self._make_hash(key_data)}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/error
        """
        if not self._connected:
            return None
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except RedisError as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Cache value decode error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = DEFAULT_TTL,
    ) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            return False
        try:
            serialized = json.dumps(value, default=str)
            await self.client.setex(key, ttl, serialized)
            return True
        except RedisError as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Cache serialization error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        if not self._connected:
            return False
        try:
            result = await self.client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Key pattern (e.g., "discover:jobs:*")

        Returns:
            Number of keys deleted
        """
        if not self._connected:
            return 0
        try:
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def invalidate_discover_cache(self) -> int:
        """
        Invalidate all discovery cache entries.
        Should be called when job or profile data changes.

        Returns:
            Number of cache entries invalidated
        """
        count = 0
        count += await self.delete_pattern(f"{self.PREFIX_DISCOVER_JOBS}:*")
        count += await self.delete_pattern(f"{self.PREFIX_DISCOVER_PROFILES}:*")
        logger.info(f"Invalidated {count} discovery cache entries")
        return count

    # -------------------------------------------------------------------------
    # Discovery API Caching
    # -------------------------------------------------------------------------

    def _discover_jobs_cache_key(
        self,
        skills: Optional[list[str]] = None,
        city: Optional[str] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        experience_years: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> str:
        """Generate cache key for discover_jobs."""
        # Sort skills for consistent hashing
        skills_str = ",".join(sorted(skills)) if skills else ""
        return self._make_cache_key(
            self.PREFIX_DISCOVER_JOBS,
            skills=skills_str,
            city=city,
            min_salary=min_salary,
            max_salary=max_salary,
            experience_years=experience_years,
            limit=limit,
            offset=offset,
        )

    async def get_discover_jobs(
        self,
        skills: Optional[list[str]] = None,
        city: Optional[str] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        experience_years: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Optional[list[dict]]:
        """Get cached discover_jobs result."""
        key = self._discover_jobs_cache_key(
            skills, city, min_salary, max_salary, experience_years, limit, offset
        )
        return await self.get(key)

    async def set_discover_jobs(
        self,
        data: list[dict],
        skills: Optional[list[str]] = None,
        city: Optional[str] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        experience_years: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> bool:
        """Cache discover_jobs result."""
        key = self._discover_jobs_cache_key(
            skills, city, min_salary, max_salary, experience_years, limit, offset
        )
        return await self.set(key, data, ttl=self.DISCOVER_TTL)

    def _discover_profiles_cache_key(
        self,
        skills: Optional[list[str]] = None,
        city: Optional[str] = None,
        min_experience: Optional[int] = None,
        max_salary_expectation: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> str:
        """Generate cache key for discover_profiles."""
        skills_str = ",".join(sorted(skills)) if skills else ""
        return self._make_cache_key(
            self.PREFIX_DISCOVER_PROFILES,
            skills=skills_str,
            city=city,
            min_experience=min_experience,
            max_salary_expectation=max_salary_expectation,
            limit=limit,
            offset=offset,
        )

    async def get_discover_profiles(
        self,
        skills: Optional[list[str]] = None,
        city: Optional[str] = None,
        min_experience: Optional[int] = None,
        max_salary_expectation: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Optional[list[dict]]:
        """Get cached discover_profiles result."""
        key = self._discover_profiles_cache_key(
            skills, city, min_experience, max_salary_expectation, limit, offset
        )
        return await self.get(key)

    async def set_discover_profiles(
        self,
        data: list[dict],
        skills: Optional[list[str]] = None,
        city: Optional[str] = None,
        min_experience: Optional[int] = None,
        max_salary_expectation: Optional[int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> bool:
        """Cache discover_profiles result."""
        key = self._discover_profiles_cache_key(
            skills, city, min_experience, max_salary_expectation, limit, offset
        )
        return await self.set(key, data, ttl=self.DISCOVER_TTL)

    # -------------------------------------------------------------------------
    # Upload Chunk Management
    # -------------------------------------------------------------------------

    async def save_upload_chunk(
        self,
        upload_id: str,
        chunk_index: int,
        data: bytes,
    ) -> bool:
        """
        Save an uploaded chunk.

        Args:
            upload_id: Unique upload identifier
            chunk_index: Index of this chunk
            data: Chunk binary data

        Returns:
            True if successful
        """
        key = f"{self.PREFIX_UPLOAD_CHUNK}:{upload_id}:{chunk_index}"
        try:
            await self.client.setex(key, self.UPLOAD_CHUNK_TTL, data)
            return True
        except RedisError as e:
            logger.error(f"Failed to save chunk {chunk_index} for {upload_id}: {e}")
            return False

    async def get_upload_chunk(
        self,
        upload_id: str,
        chunk_index: int,
    ) -> Optional[bytes]:
        """
        Get a saved upload chunk.

        Args:
            upload_id: Unique upload identifier
            chunk_index: Index of the chunk

        Returns:
            Chunk data or None
        """
        key = f"{self.PREFIX_UPLOAD_CHUNK}:{upload_id}:{chunk_index}"
        try:
            return await self.client.get(key)
        except RedisError as e:
            logger.error(f"Failed to get chunk {chunk_index} for {upload_id}: {e}")
            return None

    async def get_uploaded_chunks(self, upload_id: str) -> list[int]:
        """
        Get list of uploaded chunk indices for an upload.

        Args:
            upload_id: Unique upload identifier

        Returns:
            List of chunk indices that have been uploaded
        """
        pattern = f"{self.PREFIX_UPLOAD_CHUNK}:{upload_id}:*"
        indices = []
        try:
            async for key in self.client.scan_iter(match=pattern):
                # Extract chunk index from key: upload:chunk:upload_id:index
                parts = key.split(":")
                if len(parts) == 4:
                    indices.append(int(parts[3]))
            return sorted(indices)
        except RedisError as e:
            logger.error(f"Failed to get chunks for {upload_id}: {e}")
            return []

    async def delete_upload_chunks(self, upload_id: str) -> int:
        """
        Delete all chunks for an upload.

        Args:
            upload_id: Unique upload identifier

        Returns:
            Number of chunks deleted
        """
        return await self.delete_pattern(f"{self.PREFIX_UPLOAD_CHUNK}:{upload_id}:*")

    async def save_upload_metadata(
        self,
        upload_id: str,
        metadata: dict,
    ) -> bool:
        """
        Save upload metadata.

        Args:
            upload_id: Unique upload identifier
            metadata: Metadata dict with fields like:
                - total_chunks: int
                - file_size: int
                - filename: str
                - content_type: str
                - expected_hash: str
                - created_at: str

        Returns:
            True if successful
        """
        key = f"{self.PREFIX_UPLOAD_META}:{upload_id}"
        return await self.set(key, metadata, ttl=self.UPLOAD_META_TTL)

    async def get_upload_metadata(self, upload_id: str) -> Optional[dict]:
        """
        Get upload metadata.

        Args:
            upload_id: Unique upload identifier

        Returns:
            Metadata dict or None
        """
        key = f"{self.PREFIX_UPLOAD_META}:{upload_id}"
        return await self.get(key)

    async def delete_upload_metadata(self, upload_id: str) -> bool:
        """
        Delete upload metadata.

        Args:
            upload_id: Unique upload identifier

        Returns:
            True if deleted
        """
        key = f"{self.PREFIX_UPLOAD_META}:{upload_id}"
        return await self.delete(key)


# Global cache manager instance
cache_manager = CacheManager()


async def get_cache() -> CacheManager:
    """Get the cache manager instance."""
    return cache_manager
