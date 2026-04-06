"""
API version 1 router aggregation.
Combines all v1 endpoints under /api/v1 prefix.
"""

from fastapi import APIRouter

from app.api.v1 import skill, profiles, jobs, discover, enterprise, health, agents, webhook, a2a, billing, export, users, claim, stats, upload, applications

api_router = APIRouter(prefix="/v1")

# Include all v1 routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(skill.router, prefix="/skill", tags=["skill"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(discover.router, prefix="/discover", tags=["discover"])
api_router.include_router(enterprise.router, prefix="/enterprise", tags=["enterprise"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(webhook.router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(a2a.router, prefix="/a2a", tags=["a2a"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(claim.router, prefix="/claim", tags=["claim"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
