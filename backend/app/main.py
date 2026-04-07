"""
AgentHire Backend - FastAPI Application Entry Point

AI Agent驱动的去中心化招聘平台后端服务
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.core.database import init_db, close_db
from app.core.middleware import setup_middleware
from app.core.exceptions import setup_exception_handlers
from app.api.v1.api import api_router
from app.core.cache import cache_manager

# Import models to register them with Base.metadata
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Environment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")

    # Initialize database connections (but not tables in production)
    # Tables should be created via Alembic migrations in production
    if not settings.is_production or settings.get("auto_create_tables", False):
        await init_db()
        print("Database tables created (development mode)")
    else:
        print("Skipping table creation - use Alembic migrations in production")

    # Initialize Redis connection
    await cache_manager.connect()

    yield

    # Shutdown
    print("Shutting down...")
    # Close Redis connection
    await cache_manager.close()
    # Close database connections
    await close_db()


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI Agent驱动的去中心化招聘平台后端服务",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Setup middleware
    setup_middleware(app)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include API routers
    app.include_router(api_router, prefix="/api")

    # Static files for uploads
    import os
    uploads_dir = "./uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

    # Root endpoint
    @app.get(
        "/",
        response_model=dict,
        status_code=status.HTTP_200_OK,
        summary="Root endpoint",
        description="Returns basic API information",
        tags=["root"],
    )
    async def root() -> dict:
        """Root endpoint returning API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "docs_url": "/docs" if settings.is_development else None,
        }

    # Health check at root level for convenience
    @app.get(
        "/health",
        response_model=dict,
        status_code=status.HTTP_200_OK,
        summary="Health check",
        description="Quick health check endpoint",
        tags=["health"],
    )
    async def health() -> dict:
        """Quick health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.app_version,
        }

    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=1 if settings.is_development else settings.workers,
    )
