"""
Celery应用配置
"""

from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "mysql_analysis",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.beat_schedule = {
    "cleanup-config-analyses-daily": {
        "task": "cleanup_old_config_analyses",
        "schedule": crontab(hour=3, minute=0),
    },
}
