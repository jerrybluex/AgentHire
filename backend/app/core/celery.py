"""
AgentHire Celery Configuration
异步任务队列配置
"""

from celery import Celery
from app.config import settings

# 创建Celery应用实例
celery_app = Celery(
    "agenthire",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.resume_parse",  # 简历解析任务
        "app.tasks.matching",      # 定时清理任务
        "app.tasks.notification",  # 通知任务
    ],
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # 时区设置
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务结果过期时间
    result_expires=3600 * 24,  # 24小时

    # 任务追踪
    task_track_started=True,

    # 工作进程设置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,

    # 任务路由
    task_routes={
        "app.tasks.resume_parse.*": {"queue": "resume"},
        "app.tasks.matching.*": {"queue": "default"},
        "app.tasks.notification.*": {"queue": "notification"},
    },

    # 任务默认队列
    task_default_queue="default",

    # 定时任务（beat）
    beat_schedule={
        "cleanup-expired-jobs": {
            "task": "app.tasks.matching.cleanup_expired_jobs",
            "schedule": 3600 * 6,  # 每6小时
        },
        "process-pending-resumes": {
            "task": "app.tasks.resume_parse.process_pending_resumes",
            "schedule": 60,  # 每分钟
        },
    },
)


def get_celery_app():
    """获取Celery应用实例"""
    return celery_app
