"""
统一分析任务 Celery Worker
"""

import logging

from app.services.ai.task_executor import execute_task_sync
from app.tasks.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="analysis.run", bind=True)
def run_analysis_task(self, task_id: int):
    """执行统一分析任务"""
    logger.info("[Celery] 开始执行分析任务 task_id=%s", task_id)
    execute_task_sync(task_id)
    return {"success": True, "task_id": task_id}
