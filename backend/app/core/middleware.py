"""
Core middleware configuration for FastAPI application.
Includes CORS, logging, error handling, and request ID tracking.
"""

import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID header to request and response."""
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details and timing."""
        start_time = time.time()

        # Get request ID from request state
        request_id = getattr(request.state, "request_id", "unknown")

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log request details
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        # Use print for now, will integrate with proper logger later
        print(f"[REQUEST] {log_data}")

        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application."""
    settings = get_settings()

    # Request ID middleware (first to ensure ID is available)
    app.add_middleware(RequestIDMiddleware)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
        allow_credentials=settings.cors.allow_credentials,
        max_age=settings.cors.max_age,
    )

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Logging middleware
    app.add_middleware(LoggingMiddleware)

    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
