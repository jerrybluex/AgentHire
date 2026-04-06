"""
Discovery Service
Agent 自主发现 API - 平台不做匹配算法，由 Agent 自己判断

不再计算 match_score，所有筛选/过滤由 Agent 自主完成

注意: 核心 DiscoveryService 已迁移到 discovery_service.py
此文件保留以保持向后兼容
"""

# 重新导出 discovery_service 中的类和实例
from app.services.discovery_service import (
    DiscoveryService,
    discovery_service,
    job_to_dict,
    profile_to_dict,
)

__all__ = [
    "DiscoveryService",
    "discovery_service",
    "job_to_dict",
    "profile_to_dict",
]
