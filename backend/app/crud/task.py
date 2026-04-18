"""
分析任务 CRUD 操作
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.task import AnalysisTask


TASK_TYPE_TITLES = {
    "health_report": "健康巡检报告",
    "index_advisor": "AI 索引顾问",
    "lock_analysis": "AI 锁分析",
    "slow_query_patrol": "AI 慢查询巡检",
    "config_tuning": "AI 配置调优",
    "capacity_prediction": "AI 容量预测",
}


def create_task(
    db: Session,
    connection_id: int,
    task_type: str,
    title: Optional[str] = None,
) -> AnalysisTask:
    """创建分析任务"""
    if not title:
        title = TASK_TYPE_TITLES.get(task_type, task_type)
    task = AnalysisTask(
        connection_id=connection_id,
        task_type=task_type,
        title=title,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Optional[AnalysisTask]:
    """获取单个任务"""
    return db.execute(
        select(AnalysisTask).where(AnalysisTask.id == task_id)
    ).scalar_one_or_none()


def get_tasks(
    db: Session,
    connection_id: Optional[int] = None,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[AnalysisTask]:
    """获取任务列表（按创建时间倒序）"""
    query = select(AnalysisTask)
    if connection_id is not None:
        query = query.where(AnalysisTask.connection_id == connection_id)
    if task_type:
        query = query.where(AnalysisTask.task_type == task_type)
    if status:
        query = query.where(AnalysisTask.status == status)
    query = query.order_by(AnalysisTask.created_at.desc()).offset(offset).limit(limit)
    return list(db.execute(query).scalars().all())


def count_tasks(
    db: Session,
    connection_id: Optional[int] = None,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
) -> int:
    """统计任务数量"""
    query = select(func.count(AnalysisTask.id))
    if connection_id is not None:
        query = query.where(AnalysisTask.connection_id == connection_id)
    if task_type:
        query = query.where(AnalysisTask.task_type == task_type)
    if status:
        query = query.where(AnalysisTask.status == status)
    return db.execute(query).scalar() or 0


def update_task_status(
    db: Session,
    task_id: int,
    status: str,
    error_message: Optional[str] = None,
    result_json: Optional[str] = None,
) -> Optional[AnalysisTask]:
    """更新任务状态"""
    task = get_task(db, task_id)
    if not task:
        return None
    task.status = status
    if status == "running" and not task.started_at:
        task.started_at = datetime.utcnow()
    if status in ("success", "failed", "cancelled"):
        task.completed_at = datetime.utcnow()
    if error_message is not None:
        task.error_message = error_message
    if result_json is not None:
        task.result_json = result_json
    db.commit()
    db.refresh(task)
    return task


def update_task_progress(
    db: Session,
    task_id: int,
    progress: int,
    message: str = "",
) -> Optional[AnalysisTask]:
    """更新任务进度"""
    task = get_task(db, task_id)
    if not task:
        return None
    task.progress = min(progress, 100)
    task.progress_message = message
    db.commit()
    db.refresh(task)
    return task


def increment_retry(db: Session, task_id: int) -> Optional[AnalysisTask]:
    """增加重试计数并重置状态为 pending"""
    task = get_task(db, task_id)
    if not task:
        return None
    if task.retry_count >= task.max_retries:
        return None
    task.retry_count += 1
    task.status = "pending"
    task.progress = 0
    task.progress_message = ""
    task.error_message = None
    task.started_at = None
    task.completed_at = None
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int) -> bool:
    """删除任务"""
    task = get_task(db, task_id)
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True
