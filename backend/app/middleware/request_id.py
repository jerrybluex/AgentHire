"""
Request ID Middleware
为每个请求添加唯一请求 ID，便于追踪和审计
"""

import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求添加唯一 Request ID"""

    async def dispatch(self, request: Request, call_next):
        # 获取或生成 Request ID
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:16]}"

        # 将 Request ID 存入 request state
        request.state.request_id = request_id

        # 处理请求
        response = await call_next(request)

        # 在响应头中添加 Request ID
        response.headers[REQUEST_ID_HEADER] = request_id

        return response


def get_request_id(request: Request) -> str:
    """从 request 中获取 Request ID"""
    return getattr(request.state, "request_id", "unknown")
