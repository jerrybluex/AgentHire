"""
Idempotency Middleware
防止重复请求对数据造成影响
"""

import hashlib
import json
from datetime import timedelta
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

IDEMPOTENCY_HEADER = "X-Idempotency-Key"
IDEMPOTENCY_CACHE_TTL = timedelta(hours=24)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    幂等性中间件。
    
    对于 POST/PUT/PATCH/DELETE 请求，检查 Idempotency Key。
    如果已处理过，直接返回缓存结果。
    """

    def __init__(self, app, redis_client=None):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next):
        # 只对写请求检查幂等性
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)

        # 获取 Idempotency Key
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            # 没有 Key，允许请求通过（不强制）
            return await call_next(request)

        # 计算缓存 Key
        cache_key = f"idempotency:{hashlib.sha256(idempotency_key.encode()).hexdigest()}"

        # 如果有 Redis，尝试获取缓存
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    cached_data = json.loads(cached)
                    return Response(
                        content=cached_data["body"],
                        status_code=cached_data["status_code"],
                        headers=cached_data.get("headers", {}),
                    )
            except Exception:
                # Redis 出错，继续处理请求
                pass

        # 处理请求
        response = await call_next(request)

        # 只有成功响应（2xx）才缓存
        if 200 <= response.status_code < 300 and self.redis:
            try:
                # 读取响应体
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # 构建缓存数据
                cache_data = {
                    "body": body.decode(),
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                }

                # 存入 Redis
                await self.redis.setex(
                    cache_key,
                    int(IDEMPOTENCY_CACHE_TTL.total_seconds()),
                    json.dumps(cache_data),
                )

                # 返回新响应（因为原响应体已被消费）
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=response.headers,
                )
            except Exception:
                pass

        return response
