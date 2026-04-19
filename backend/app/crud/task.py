"""
统一任务中心 CRUD 操作
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.task import AnalysisTask, AnalysisTaskEvent


TASK_TYPE_TITLES = {
    "health_report": "健康巡检报告",
    "index_advisor": "AI 索引顾问",
    "lock_analysis": "AI 锁分析",
    "slow_query_patrol": "AI 慢查询巡检",
    "config_tuning": "AI 配置调优",
    "capacity_prediction": "容量风险评估",
}

ACTIVE_STATUSES = {"pending", "queued", "running", "retry_waiting", "cancel_requested"}
FINAL_STATUSES = {"success", "failed", "cancelled", "timed_out"}


def coerce_task_status(status: Optional[str]) -> Optional[str]:
    """兼容旧状态别名"""
    if status is None:
        return None
    mapping = {
        "created": "pending",
        "queued": "queued",
        "succeeded": "success",
        "timeout": "timed_out",
    }
    return mapping.get(status, status)


def _json_dumps(value: Optional[Dict[str, Any]]) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def create_task(
    db: Session,
    connection_id: int,
    task_type: str,
    title: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    payload_summary: Optional[Dict[str, Any]] = None,
    source_page: Optional[str] = None,
    created_by: Optional[int] = None,
    idempotency_key: Optional[str] = None,
) -> AnalysisTask:
    """创建分析任务"""
    task = AnalysisTask(
        connection_id=connection_id,
        task_type=task_type,
        title=title or TASK_TYPE_TITLES.get(task_type, task_type),
        status=coerce_task_status("pending"),
        payload_json=_json_dumps(payload),
        payload_summary_json=_json_dumps(payload_summary),
        source_page=source_page,
        created_by=created_by,
        idempotency_key=idempotency_key,
        progress=0,
        stage_code="pending",
        stage_message="等待调度",
        progress_message="等待调度",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    append_task_event(
        db,
        task.id,
        event_type="task_created",
        progress=0,
        stage_code="pending",
        event_payload={
            "message": "任务已创建",
            "task_type": task.task_type,
            "title": task.title,
        },
    )
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
    """获取任务列表"""
    query = select(AnalysisTask)
    if connection_id is not None:
        query = query.where(AnalysisTask.connection_id == connection_id)
    if task_type:
        query = query.where(AnalysisTask.task_type == task_type)
    normalized_status = coerce_task_status(status)
    if normalized_status:
        query = query.where(AnalysisTask.status == normalized_status)
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
    normalized_status = coerce_task_status(status)
    if normalized_status:
        query = query.where(AnalysisTask.status == normalized_status)
    return db.execute(query).scalar() or 0


def get_task_counts_by_status(
    db: Session,
    connection_id: Optional[int] = None,
) -> Dict[str, int]:
    """按状态统计任务数量"""
    query = select(AnalysisTask.status, func.count(AnalysisTask.id)).group_by(AnalysisTask.status)
    if connection_id is not None:
        query = query.where(AnalysisTask.connection_id == connection_id)

    rows = db.execute(query).all()
    counts = {status: count for status, count in rows}
    counts.setdefault("total", sum(counts.values()))
    return counts


def _next_event_seq(db: Session, task_id: int) -> int:
    current = db.execute(
        select(func.max(AnalysisTaskEvent.seq)).where(AnalysisTaskEvent.task_id == task_id)
    ).scalar()
    return (current or 0) + 1


def append_task_event(
    db: Session,
    task_id: int,
    event_type: str,
    progress: Optional[int] = None,
    stage_code: Optional[str] = None,
    event_payload: Optional[Dict[str, Any]] = None,
    commit: bool = True,
) -> AnalysisTaskEvent:
    """追加任务事件"""
    event = AnalysisTaskEvent(
        task_id=task_id,
        seq=_next_event_seq(db, task_id),
        event_type=event_type,
        progress=progress,
        stage_code=stage_code,
        event_json=_json_dumps(event_payload),
    )
    db.add(event)
    if commit:
        db.commit()
        db.refresh(event)
    return event


def list_task_events(db: Session, task_id: int, after_seq: int = 0, limit: int = 200) -> List[AnalysisTaskEvent]:
    """获取任务事件列表"""
    query = (
        select(AnalysisTaskEvent)
        .where(AnalysisTaskEvent.task_id == task_id)
        .where(AnalysisTaskEvent.seq > after_seq)
        .order_by(AnalysisTaskEvent.seq.asc())
        .limit(limit)
    )
    return list(db.execute(query).scalars().all())


def update_task_status(
    db: Session,
    task_id: int,
    status: str,
    *,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    result_json: Optional[str] = None,
    stage_code: Optional[str] = None,
    stage_message: Optional[str] = None,
    progress: Optional[int] = None,
    worker_id: Optional[str] = None,
    force: bool = False,
) -> Optional[AnalysisTask]:
    """更新任务状态"""
    status = coerce_task_status(status) or "pending"
    task = get_task(db, task_id)
    if not task:
        return None

    if not force and task.status in FINAL_STATUSES and status not in FINAL_STATUSES:
        return task

    if not force and task.status == "cancel_requested" and status in {"success", "failed"}:
        status = "cancelled"

    task.status = status
    if progress is not None:
        task.progress = max(0, min(progress, 100))
    if stage_code is not None:
        task.stage_code = stage_code
    if stage_message is not None:
        task.stage_message = stage_message
        task.progress_message = stage_message
    if worker_id is not None:
        task.worker_id = worker_id
    if status == "running" and not task.started_at:
        now = datetime.utcnow()
        task.started_at = now
        task.heartbeat_at = now
    if status in FINAL_STATUSES:
        task.completed_at = datetime.utcnow()
        if progress is None:
            task.progress = 100 if status == "success" else task.progress
    if status == "cancel_requested":
        task.cancel_requested_at = datetime.utcnow()
    if error_code is not None:
        task.error_code = error_code
    if error_message is not None:
        task.error_message = error_message
    if result_json is not None:
        task.result_json = result_json

    db.commit()
    db.refresh(task)

    event_payload: Dict[str, Any] = {
        "status": task.status,
        "message": task.stage_message or task.progress_message or "",
    }
    if error_code:
        event_payload["error_code"] = error_code
    if error_message:
        event_payload["error_message"] = error_message

    append_task_event(
        db,
        task_id,
        event_type="status_changed",
        progress=task.progress,
        stage_code=task.stage_code,
        event_payload=event_payload,
    )
    return task


def update_task_progress(
    db: Session,
    task_id: int,
    progress: int,
    message: str = "",
    *,
    stage_code: Optional[str] = None,
    event_type: str = "progress",
    event_payload: Optional[Dict[str, Any]] = None,
    heartbeat: bool = True,
) -> Optional[AnalysisTask]:
    """更新任务进度"""
    task = get_task(db, task_id)
    if not task:
        return None

    task.progress = max(0, min(progress, 100))
    task.progress_message = message
    if stage_code is not None:
        task.stage_code = stage_code
    if message:
        task.stage_message = message
    if heartbeat:
        task.heartbeat_at = datetime.utcnow()

    db.commit()
    db.refresh(task)

    payload = dict(event_payload or {})
    payload.setdefault("message", message)
    append_task_event(
        db,
        task_id,
        event_type=event_type,
        progress=task.progress,
        stage_code=task.stage_code,
        event_payload=payload,
    )
    return task


def update_task_result(
    db: Session,
    task_id: int,
    result: Dict[str, Any],
    *,
    schema_version: int = 1,
    status: str = "success",
) -> Optional[AnalysisTask]:
    """更新任务结果"""
    task = get_task(db, task_id)
    if not task:
        return None

    task.result_json = json.dumps(result, ensure_ascii=False)
    task.result_schema_version = schema_version
    db.commit()
    db.refresh(task)
    return update_task_status(
        db,
        task_id,
        status,
        progress=100,
        stage_code="completed",
        stage_message="任务已完成",
    )


def request_cancel(db: Session, task_id: int) -> Optional[AnalysisTask]:
    """请求取消任务"""
    task = get_task(db, task_id)
    if not task:
        return None

    if task.status in FINAL_STATUSES:
        return task

    target_status = "cancel_requested" if task.status == "running" else "cancelled"
    return update_task_status(
        db,
        task_id,
        target_status,
        stage_code="cancel_requested",
        stage_message="任务取消中" if target_status == "cancel_requested" else "任务已取消",
        force=True,
    )


def mark_task_cancelled(db: Session, task_id: int, message: str = "任务已取消") -> Optional[AnalysisTask]:
    """将任务标记为取消完成"""
    return update_task_status(
        db,
        task_id,
        "cancelled",
        stage_code="cancelled",
        stage_message=message,
        force=True,
    )


def increment_retry(db: Session, task_id: int) -> Optional[AnalysisTask]:
    """重试任务，重置状态"""
    task = get_task(db, task_id)
    if not task or task.retry_count >= task.max_retries:
        return None

    task.retry_count += 1
    task.status = "pending"
    task.progress = 0
    task.stage_code = "pending"
    task.stage_message = "等待重新调度"
    task.progress_message = "等待重新调度"
    task.error_code = None
    task.error_message = None
    task.result_json = None
    task.started_at = None
    task.completed_at = None
    task.cancel_requested_at = None
    task.heartbeat_at = None
    db.commit()
    db.refresh(task)

    append_task_event(
        db,
        task_id,
        event_type="retry_requested",
        progress=0,
        stage_code="pending",
        event_payload={
            "message": "任务已重新提交",
            "retry_count": task.retry_count,
        },
    )
    return task


def update_task_heartbeat(db: Session, task_id: int, worker_id: Optional[str] = None) -> Optional[AnalysisTask]:
    """更新任务心跳"""
    task = get_task(db, task_id)
    if not task:
        return None

    task.heartbeat_at = datetime.utcnow()
    if worker_id is not None:
        task.worker_id = worker_id
    db.commit()
    db.refresh(task)
    return task


def get_stale_tasks(db: Session, timeout_seconds: int) -> List[AnalysisTask]:
    """获取心跳超时的任务"""
    expire_before = datetime.utcnow() - timedelta(seconds=timeout_seconds)
    query = (
        select(AnalysisTask)
        .where(AnalysisTask.status == "running")
        .where(AnalysisTask.heartbeat_at.is_not(None))
        .where(AnalysisTask.heartbeat_at < expire_before)
    )
    return list(db.execute(query).scalars().all())


def get_pending_or_active_tasks(db: Session) -> List[AnalysisTask]:
    """获取待执行或执行中的任务"""
    query = (
        select(AnalysisTask)
        .where(AnalysisTask.status.in_(tuple(ACTIVE_STATUSES)))
        .order_by(AnalysisTask.created_at.asc())
    )
    return list(db.execute(query).scalars().all())


def delete_task(db: Session, task_id: int) -> bool:
    """删除任务及事件"""
    task = get_task(db, task_id)
    if not task:
        return False

    db.execute(select(AnalysisTaskEvent).where(AnalysisTaskEvent.task_id == task_id))
    events = list_task_events(db, task_id, after_seq=0, limit=100000)
    for event in events:
        db.delete(event)
    db.delete(task)
    db.commit()
    return True


def is_cancel_requested(db: Session, task_id: int) -> bool:
    """判断任务是否已请求取消"""
    task = get_task(db, task_id)
    if not task:
        return False
    return task.status in {"cancel_requested", "cancelled"}


def parse_json_field(value: Optional[str]) -> Optional[Dict[str, Any]]:
    """解析 JSON 字段"""
    if not value:
        return None
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None
