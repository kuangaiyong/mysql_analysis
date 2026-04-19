"""
统一任务中心 API 路由
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import task as task_crud
from app.database import SessionLocal, get_session as get_db
from app.services.ai.task_executor import get_progress, submit_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["任务管理"])

VALID_TASK_TYPES = {
    "health_report",
    "index_advisor",
    "lock_analysis",
    "slow_query_patrol",
    "config_tuning",
    "capacity_prediction",
}


class CreateTaskRequest(BaseModel):
    """创建任务请求"""

    connection_id: int
    task_type: str
    title: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    source_page: Optional[str] = None


def _get_user_id_from_request(request: Request) -> Optional[int]:
    user = getattr(request.state, "user", None)
    if isinstance(user, dict):
        user_id = user.get("user_id")
        if user_id is not None:
            try:
                return int(user_id)
            except (TypeError, ValueError):
                return None

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    try:
        from app.core.auth import decode_access_token

        token = auth_header.split()[1]
        payload = decode_access_token(token) or {}
        user_id = payload.get("user_id")
        return int(user_id) if user_id is not None else None
    except Exception:
        return None


def _task_to_dict(task) -> Dict[str, Any]:
    payload_summary = task_crud.parse_json_field(task.payload_summary_json)
    return {
        "id": task.id,
        "connection_id": task.connection_id,
        "task_type": task.task_type,
        "status": task.status,
        "title": task.title,
        "progress": task.progress,
        "stage_code": task.stage_code,
        "stage_message": task.stage_message or "",
        "progress_message": task.progress_message or "",
        "result_json": task.result_json,
        "result_schema_version": task.result_schema_version,
        "error_code": task.error_code,
        "error_message": task.error_message,
        "retry_count": task.retry_count,
        "max_retries": task.max_retries,
        "source_page": task.source_page,
        "payload_summary": payload_summary,
        "worker_id": task.worker_id,
        "heartbeat_at": task.heartbeat_at.isoformat() if task.heartbeat_at else None,
        "cancel_requested_at": task.cancel_requested_at.isoformat() if task.cancel_requested_at else None,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def _event_to_dict(event) -> Dict[str, Any]:
    payload: Any = None
    if event.event_json:
        try:
            payload = json.loads(event.event_json)
        except json.JSONDecodeError:
            payload = event.event_json
    return {
        "id": event.id,
        "task_id": event.task_id,
        "seq": event.seq,
        "event_type": event.event_type,
        "progress": event.progress,
        "stage_code": event.stage_code,
        "event": payload,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


@router.post("")
def create_task(
    body: CreateTaskRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """创建并启动分析任务"""
    if body.task_type not in VALID_TASK_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的任务类型: {body.task_type}")

    user_id = _get_user_id_from_request(request)
    task = task_crud.create_task(
        db=db,
        connection_id=body.connection_id,
        task_type=body.task_type,
        title=body.title,
        payload=body.payload,
        payload_summary=body.payload or {"connection_id": body.connection_id},
        source_page=body.source_page,
        created_by=user_id,
    )
    task = task_crud.update_task_status(
        db,
        task.id,
        "queued",
        progress=0,
        stage_code="queued",
        stage_message="任务已入队",
        force=True,
    ) or task
    executor = submit_task(task.id)

    task = task_crud.get_task(db, task.id) or task
    return {
        "success": True,
        "executor": executor,
        "data": _task_to_dict(task),
    }


@router.get("")
def list_tasks(
    connection_id: Optional[int] = Query(None),
    task_type: Optional[str] = Query(None),
    task_status: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取任务列表"""
    tasks = task_crud.get_tasks(
        db,
        connection_id=connection_id,
        task_type=task_type,
        status=task_status,
        limit=limit,
        offset=offset,
    )
    total = task_crud.count_tasks(
        db,
        connection_id=connection_id,
        task_type=task_type,
        status=task_status,
    )
    stats = task_crud.get_task_counts_by_status(db, connection_id=connection_id)
    return {
        "success": True,
        "data": [_task_to_dict(task) for task in tasks],
        "total": total,
        "stats": stats,
        "summary": {
            "queued": stats.get("queued", 0),
            "running": stats.get("running", 0),
            "failed": stats.get("failed", 0),
            "completed": stats.get("success", 0),
            "cancelled": stats.get("cancelled", 0),
        },
    }


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情"""
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    data = _task_to_dict(task)
    progress = get_progress(task_id)
    if progress is not None:
        data["live_progress"] = progress["progress"]
        data["live_message"] = progress["message"]
    return {"success": True, "data": data}


@router.get("/{task_id}/events")
def list_task_events(
    task_id: int,
    after_seq: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """获取任务事件历史"""
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    events = task_crud.list_task_events(db, task_id, after_seq=after_seq, limit=limit)
    return {
        "success": True,
        "data": [_event_to_dict(event) for event in events],
    }


@router.get("/{task_id}/events/stream")
async def stream_task_events(
    task_id: int,
    request: Request,
    after_seq: int = Query(0, ge=0),
):
    """任务事件实时流"""
    db = SessionLocal()
    try:
        task = task_crud.get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
    finally:
        db.close()

    async def event_generator():
        last_seq = after_seq
        while True:
            if await request.is_disconnected():
                break

            db_session = SessionLocal()
            try:
                events = task_crud.list_task_events(db_session, task_id, after_seq=last_seq, limit=200)
                for event in events:
                    payload = json.dumps(_event_to_dict(event), ensure_ascii=False)
                    last_seq = max(last_seq, event.seq)
                    yield f"event: event\ndata: {payload}\n\n"

                task = task_crud.get_task(db_session, task_id)
                if not task:
                    yield 'event: error\ndata: {"message": "任务不存在"}\n\n'
                    break

                if task.status in task_crud.FINAL_STATUSES and (not events or last_seq >= (events[-1].seq if events else last_seq)):
                    payload = json.dumps({
                        "task_id": task_id,
                        "status": task.status,
                        "progress": task.progress,
                        "message": task.progress_message or task.stage_message or "",
                    }, ensure_ascii=False)
                    yield f"event: complete\ndata: {payload}\n\n"
                    break
            finally:
                db_session.close()

            await asyncio.sleep(settings.task_stream_poll_interval)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{task_id}/progress")
async def task_progress_sse(task_id: int, request: Request):
    """兼容旧版进度 SSE，内部转为事件流"""

    async def event_generator():
        last_seq = 0
        while True:
            if await request.is_disconnected():
                break

            db_session = SessionLocal()
            try:
                task = task_crud.get_task(db_session, task_id)
                if not task:
                    yield 'event: error\ndata: {"message": "任务不存在"}\n\n'
                    break

                progress = get_progress(task_id) or {
                    "progress": task.progress,
                    "message": task.progress_message or task.stage_message or "",
                }

                if task.progress != last_seq or task.status in task_crud.FINAL_STATUSES:
                    payload = json.dumps({
                        "task_id": task_id,
                        "status": task.status,
                        "progress": progress["progress"],
                        "message": progress["message"],
                    }, ensure_ascii=False)
                    yield f"event: progress\ndata: {payload}\n\n"
                    last_seq = task.progress

                if task.status in task_crud.FINAL_STATUSES:
                    payload = json.dumps({
                        "task_id": task_id,
                        "status": task.status,
                        "progress": task.progress,
                        "message": progress["message"],
                    }, ensure_ascii=False)
                    yield f"event: complete\ndata: {payload}\n\n"
                    break
            finally:
                db_session.close()

            await asyncio.sleep(settings.task_stream_poll_interval)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{task_id}/retry")
def retry_task(task_id: int, db: Session = Depends(get_db)):
    """重试失败或超时任务"""
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in {"failed", "timed_out", "cancelled"}:
        raise HTTPException(status_code=400, detail="当前状态不支持重试")

    task = task_crud.increment_retry(db, task_id)
    if not task:
        raise HTTPException(status_code=400, detail="已达到最大重试次数")
    task = task_crud.update_task_status(
        db,
        task.id,
        "queued",
        progress=0,
        stage_code="queued",
        stage_message="任务已重新入队",
        force=True,
    ) or task
    executor = submit_task(task.id)
    return {"success": True, "executor": executor, "data": _task_to_dict(task)}


@router.post("/{task_id}/cancel")
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    """请求取消任务"""
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status in task_crud.FINAL_STATUSES:
        raise HTTPException(status_code=400, detail="任务已结束，无法取消")

    updated = task_crud.request_cancel(db, task_id)
    return {
        "success": True,
        "message": "任务已取消" if updated and updated.status == "cancelled" else "已提交取消请求",
        "data": _task_to_dict(updated or task),
    }


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除已结束任务"""
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in task_crud.FINAL_STATUSES:
        raise HTTPException(status_code=400, detail="进行中的任务不能删除")
    if not task_crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "message": "任务已删除"}
