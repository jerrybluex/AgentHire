"""
File Upload API - Chunked and Resumable Upload

支持:
- 断点续传: 上传中断后可从中断点继续
- 分片上传: 大文件分片上传，最后合并
- 验证: 时间戳 + hash 验证

流程:
1. 初始化上传 -> 获取 upload_id
2. 上传分片 -> 逐个上传分片
3. 完成上传 -> 合并分片并验证
4. 取消上传 -> 清理临时数据
"""

import hashlib
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Query, status
from pydantic import BaseModel, Field

from app.core.cache import get_cache, CacheManager

logger = logging.getLogger(__name__)
router = APIRouter()

# Configuration
UPLOAD_DIR = Path("./uploads")
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB per chunk
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB max file size
MAX_CHUNKS = 100

# Ensure upload directory exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Request/Response Models
# =============================================================================

class InitUploadResponse(BaseModel):
    """初始化上传响应"""
    success: bool = True
    upload_id: str = Field(description="唯一上传ID，用于后续操作")
    chunk_size: int = Field(description="分片大小（字节）")
    total_chunks: int = Field(description="总分片数")
    expires_at: str = Field(description="上传过期时间")


class UploadChunkResponse(BaseModel):
    """上传分片响应"""
    success: bool = True
    chunk_index: int = Field(description="当前分片索引")
    chunks_uploaded: int = Field(description="已上传分片数")
    total_chunks: int = Field(description="总分片数")


class CompleteUploadResponse(BaseModel):
    """完成上传响应"""
    success: bool = True
    file_id: str = Field(description="文件ID")
    file_path: str = Field(description="文件路径")
    file_size: int = Field(description="文件大小")
    content_hash: str = Field(description="文件内容Hash (SHA256)")


class UploadStatusResponse(BaseModel):
    """上传状态响应"""
    success: bool = True
    upload_id: str
    filename: str
    total_chunks: int
    chunks_uploaded: int
    uploaded_indices: list[int]
    metadata: dict


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str
    detail: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def generate_upload_id(filename: str, timestamp: int, client_hash: str) -> str:
    """
    Generate a unique upload ID.

    Format: upload_{timestamp}_{hash}
    """
    hash_part = hashlib.sha256(f"{filename}:{timestamp}:{client_hash}".encode()).hexdigest()[:16]
    return f"upload_{timestamp}_{hash_part}"


def compute_file_hash(data: bytes) -> str:
    """Compute SHA256 hash of file data."""
    return hashlib.sha256(data).hexdigest()


def compute_chunk_hash(data: bytes) -> str:
    """Compute SHA256 hash of chunk data."""
    return hashlib.sha256(data).hexdigest()


def get_upload_temp_dir(upload_id: str) -> Path:
    """Get temporary directory for storing chunks."""
    return UPLOAD_DIR / "temp" / upload_id


def get_final_file_path(upload_id: str, filename: str) -> Path:
    """Get final file path after merge."""
    return UPLOAD_DIR / "final" / upload_id[:2] / filename


# =============================================================================
# API Endpoints
# =============================================================================

@router.post(
    "/init",
    response_model=InitUploadResponse,
    summary="初始化上传",
    description="开始一个新的分片上传，返回 upload_id",
)
async def init_upload(
    filename: str = Query(..., description="文件名"),
    file_size: int = Query(..., description="文件大小（字节）", gt=0),
    content_type: str = Query(..., description="文件类型"),
    client_hash: str = Query(..., description="客户端计算的完整文件Hash (SHA256)"),
    timestamp: int = Query(..., description="客户端时间戳（秒）"),
    cache: CacheManager = Depends(get_cache),
):
    """
    Initialize a new chunked upload.

    Args:
        filename: Original filename
        file_size: Total file size in bytes
        content_type: MIME type
        client_hash: Pre-computed SHA256 hash of complete file
        timestamp: Client timestamp for validation

    Returns:
        upload_id and chunk configuration
    """
    # Validate timestamp (within 1 hour)
    current_time = int(time.time())
    if abs(current_time - timestamp) > 3600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timestamp expired or invalid"
        )

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Max size is {MAX_FILE_SIZE} bytes"
        )

    # Calculate total chunks
    total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
    if total_chunks > MAX_CHUNKS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many chunks. Max is {MAX_CHUNKS}"
        )

    # Generate upload ID
    upload_id = generate_upload_id(filename, timestamp, client_hash)

    # Save metadata to cache
    metadata = {
        "filename": filename,
        "file_size": file_size,
        "content_type": content_type,
        "expected_hash": client_hash,
        "total_chunks": total_chunks,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "chunks_uploaded": 0,
    }

    success = await cache.save_upload_metadata(upload_id, metadata)
    if not success:
        logger.error(f"Failed to save upload metadata for {upload_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize upload"
        )

    # Create temp directory for chunks
    temp_dir = get_upload_temp_dir(upload_id)
    temp_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initialized upload {upload_id}: {filename}, {total_chunks} chunks")

    return InitUploadResponse(
        success=True,
        upload_id=upload_id,
        chunk_size=CHUNK_SIZE,
        total_chunks=total_chunks,
        expires_at=metadata["created_at"],  # TODO: add expiration time
    )


@router.post(
    "/chunk",
    response_model=UploadChunkResponse,
    summary="上传分片",
    description="上传单个分片，支持断点续传",
)
async def upload_chunk(
    upload_id: str = Query(..., description="上传ID"),
    chunk_index: int = Query(..., description="分片索引 (0-based)"),
    chunk_hash: str = Query(..., description="分片Hash (SHA256)"),
    chunk: UploadFile = File(..., description="分片内容"),
    cache: CacheManager = Depends(get_cache),
):
    """
    Upload a single chunk.

    Args:
        upload_id: Upload identifier from init
        chunk_index: 0-based chunk index
        chunk_hash: SHA256 hash of chunk for verification
        chunk: Binary chunk data

    Returns:
        Upload progress status
    """
    # Get upload metadata
    metadata = await cache.get_upload_metadata(upload_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found or expired"
        )

    total_chunks = metadata["total_chunks"]

    # Validate chunk index
    if chunk_index < 0 or chunk_index >= total_chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chunk index. Must be 0-{total_chunks - 1}"
        )

    # Read chunk data
    data = await chunk.read()

    # Verify chunk size
    expected_size = CHUNK_SIZE if chunk_index < total_chunks - 1 else (
        metadata["file_size"] % CHUNK_SIZE or CHUNK_SIZE
    )
    if len(data) != expected_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid chunk size. Expected {expected_size}, got {len(data)}"
        )

    # Verify chunk hash
    computed_hash = compute_chunk_hash(data)
    if computed_hash != chunk_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chunk hash mismatch"
        )

    # Save chunk to temp directory
    temp_dir = get_upload_temp_dir(upload_id)
    chunk_path = temp_dir / f"chunk_{chunk_index:04d}"

    try:
        with open(chunk_path, "wb") as f:
            f.write(data)
    except IOError as e:
        logger.error(f"Failed to save chunk {chunk_index} for {upload_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save chunk"
        )

    # Also save to Redis for distributed scenarios (optional)
    await cache.save_upload_chunk(upload_id, chunk_index, data)

    # Update chunks uploaded count
    uploaded_chunks = await cache.get_uploaded_chunks(upload_id)
    metadata["chunks_uploaded"] = len(uploaded_chunks)
    await cache.save_upload_metadata(upload_id, metadata)

    logger.debug(f"Uploaded chunk {chunk_index + 1}/{total_chunks} for {upload_id}")

    return UploadChunkResponse(
        success=True,
        chunk_index=chunk_index,
        chunks_uploaded=len(uploaded_chunks),
        total_chunks=total_chunks,
    )


@router.post(
    "/complete",
    response_model=CompleteUploadResponse,
    summary="完成上传",
    description="合并所有分片并验证文件完整性",
)
async def complete_upload(
    upload_id: str = Query(..., description="上传ID"),
    cache: CacheManager = Depends(get_cache),
):
    """
    Complete the upload by merging all chunks and verifying hash.

    Args:
        upload_id: Upload identifier

    Returns:
        Final file information
    """
    # Get metadata
    metadata = await cache.get_upload_metadata(upload_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found or expired"
        )

    temp_dir = get_upload_temp_dir(upload_id)
    total_chunks = metadata["total_chunks"]

    # Verify all chunks are uploaded
    uploaded_indices = await cache.get_uploaded_chunks(upload_id)
    if len(uploaded_indices) != total_chunks:
        missing = set(range(total_chunks)) - set(uploaded_indices)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing chunks: {sorted(missing)}"
        )

    # Merge chunks
    final_path = get_final_file_path(upload_id, metadata["filename"])
    final_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(final_path, "wb") as outfile:
            for i in range(total_chunks):
                chunk_path = temp_dir / f"chunk_{i:04d}"
                if not chunk_path.exists():
                    # Try to get from cache
                    chunk_data = await cache.get_upload_chunk(upload_id, i)
                    if chunk_data:
                        outfile.write(chunk_data)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Chunk {i} not found"
                        )
                else:
                    with open(chunk_path, "rb") as infile:
                        outfile.write(infile.read())

        # Verify final file hash
        file_size = final_path.stat().st_size
        with open(final_path, "rb") as f:
            file_hash = compute_file_hash(f.read())

        if file_hash != metadata["expected_hash"]:
            # Hash mismatch - delete invalid file
            final_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File hash mismatch after merge"
            )

    except IOError as e:
        logger.error(f"Failed to merge chunks for {upload_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to merge chunks"
        )

    # Cleanup temp files and cache
    await _cleanup_upload(upload_id, cache)

    # Generate file ID
    file_id = f"file_{int(time.time())}_{file_hash[:16]}"

    logger.info(f"Completed upload {upload_id}: {final_path}")

    return CompleteUploadResponse(
        success=True,
        file_id=file_id,
        file_path=str(final_path),
        file_size=file_size,
        content_hash=file_hash,
    )


@router.get(
    "/status/{upload_id}",
    response_model=UploadStatusResponse,
    summary="查询上传状态",
    description="查询已上传的分片列表，用于断点续传",
)
async def get_upload_status(
    upload_id: str,
    cache: CacheManager = Depends(get_cache),
):
    """
    Get upload status for resumable upload.

    Args:
        upload_id: Upload identifier

    Returns:
        Current upload progress
    """
    metadata = await cache.get_upload_metadata(upload_id)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found or expired"
        )

    uploaded_indices = await cache.get_uploaded_chunks(upload_id)

    return UploadStatusResponse(
        success=True,
        upload_id=upload_id,
        filename=metadata["filename"],
        total_chunks=metadata["total_chunks"],
        chunks_uploaded=len(uploaded_indices),
        uploaded_indices=uploaded_indices,
        metadata=metadata,
    )


@router.post(
    "/cancel",
    summary="取消上传",
    description="取消上传并清理临时文件",
)
async def cancel_upload(
    upload_id: str = Query(..., description="上传ID"),
    cache: CacheManager = Depends(get_cache),
):
    """
    Cancel an upload and cleanup.

    Args:
        upload_id: Upload identifier
    """
    # Delete from cache
    await cache.delete_upload_chunks(upload_id)
    await cache.delete_upload_metadata(upload_id)

    # Delete temp files
    temp_dir = get_upload_temp_dir(upload_id)
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)

    logger.info(f"Cancelled upload {upload_id}")

    return {"success": True, "message": "Upload cancelled"}


# Internal cleanup helper for use in complete_upload
async def _cleanup_upload(upload_id: str, cache: CacheManager):
    """Internal cleanup implementation."""
    await cache.delete_upload_chunks(upload_id)
    await cache.delete_upload_metadata(upload_id)

    temp_dir = get_upload_temp_dir(upload_id)
    if temp_dir.exists():
        import shutil
        shutil.rmtree(temp_dir)
