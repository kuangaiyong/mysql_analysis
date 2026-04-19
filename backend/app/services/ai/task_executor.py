"""
统一任务执行器

负责：
1. 本地执行兜底（T0）
2. Celery Worker 执行（T1）
3. 事件写库、取消协作、心跳维护
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.crud import task as task_crud
from app.database import SessionLocal

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="task-worker")

EVENT_STREAM_TIMEOUT_SECONDS = 3600


def get_worker_id() -> str:
    """生成当前 worker 标识"""
    return f"{socket.gethostname()}:{os.getpid()}"


def _build_task_envelope(task_type: str, raw_result: Dict[str, Any]) -> Dict[str, Any]:
    structured = raw_result.get("structured") or {}

    if task_type == "health_report":
        return {
            "task_type": task_type,
            "renderer_key": "health_report",
            "schema_version": 1,
            "summary": f"健康评分 {raw_result.get('health_score', 0)} 分",
            "structured": {
                "health_score": raw_result.get("health_score", 0),
                "dimensions": raw_result.get("dimensions", []),
                "issues": raw_result.get("issues", []),
                "report_id": raw_result.get("report_id"),
                "content": raw_result.get("content", {}),
            },
            "meta": {
                "result_saved": raw_result.get("report_id") is not None,
            },
            "raw": raw_result,
        }

    summary = structured.get("summary") or raw_result.get("answer", "")[:200]
    renderer_key = task_type if task_type != "capacity_prediction" else "capacity_assessment"
    return {
        "task_type": task_type,
        "renderer_key": renderer_key,
        "schema_version": 1,
        "summary": summary,
        "structured": structured,
        "meta": {
            "provider": raw_result.get("provider"),
            "pre_analysis": raw_result.get("pre_analysis"),
        },
        "raw": raw_result,
    }


def _derive_progress(event_type: str, data: Dict[str, Any], chunk_count: int, task_type: str) -> tuple[int, str, str]:
    stage_code = data.get("step") or event_type
    message = data.get("message") or data.get("status") or data.get("dimension") or "处理中"

    if event_type == "progress":
        total = max(int(data.get("total", 1) or 1), 1)
        current = int(data.get("current", 0) or 0)
        progress = int(current / total * 80)
        return max(progress, 0), "progress", message

    if event_type == "status":
        return 5, stage_code or "status", message

    if event_type == "context":
        return 20, "context", message

    if event_type == "analysis":
        return 30, "analysis", message

    if event_type == "chunk":
        return min(30 + (chunk_count % 60), 90), "analysis", "AI 分析中..."

    if event_type in {"dimension", "dimension_complete"} and task_type == "health_report":
        progress = int(data.get("current", 0) / max(int(data.get("total", 1) or 1), 1) * 80)
        name = data.get("dimension") or data.get("name") or "维度分析"
        return min(progress, 90), "dimension", data.get("status") or f"已完成: {name}"

    if event_type == "result":
        return 95, "saving", "分析完成，正在保存..."

    if event_type == "error":
        return 100, "failed", data.get("message") or "任务失败"

    return 10, stage_code or "processing", message


def _get_payload_from_task(task) -> Dict[str, Any]:
    payload = task_crud.parse_json_field(task.payload_json)
    return payload or {}


def _normalize_task_payload(task_type: str, connection_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(payload)
    normalized.setdefault("connection_id", connection_id)
    normalized.setdefault("task_type", task_type)
    return normalized


def _create_stream(task, db: Session):
    task_type = task.task_type
    payload = _normalize_task_payload(task.task_type, task.connection_id, _get_payload_from_task(task))

    if task_type == "health_report":
        from app.services.ai.health_report_service import HealthReportService

        service = HealthReportService()
        return service.generate_report_stream(db=db, connection_id=payload["connection_id"])

    from app.services.ai.ai_diagnostic_service import AIDiagnosticService

    service = AIDiagnosticService()
    method_map = {
        "index_advisor": service.index_advisor_stream,
        "lock_analysis": service.lock_analysis_stream,
        "slow_query_patrol": service.slow_query_patrol_stream,
        "config_tuning": service.config_tuning_stream,
        "capacity_prediction": service.capacity_prediction_stream,
    }
    method = method_map.get(task_type)
    if method is None:
        return None
    return method(db=db, connection_id=payload["connection_id"])


async def _run_analysis_stream(task_id: int, task_type: str, db: Session, stream_generator):
    """消费流式生成器并写入任务进度与事件"""
    chunk_count = 0
    result_data = None
    error_msg = None

    async for event_type, data in stream_generator:
        data = data or {}

        if task_crud.is_cancel_requested(db, task_id):
            task_crud.mark_task_cancelled(db, task_id, "任务已取消")
            return None, "任务已取消"

        if event_type == "chunk":
            chunk_count += 1

        progress, stage_code, message = _derive_progress(event_type, data, chunk_count, task_type)

        if event_type == "error":
            error_msg = data.get("message") or "未知错误"
            task_crud.update_task_progress(
                db,
                task_id,
                progress,
                message,
                stage_code=stage_code,
                event_type="error",
                event_payload=data,
            )
            break

        if event_type == "result":
            result_data = data
            task_crud.update_task_progress(
                db,
                task_id,
                progress,
                message,
                stage_code=stage_code,
                event_type="result_ready",
                event_payload={"message": message},
            )
            continue

        event_payload = dict(data)
        if event_type == "chunk":
            event_payload = {"text": data.get("text", "")[:500], "message": message}

        task_crud.update_task_progress(
            db,
            task_id,
            progress,
            message,
            stage_code=stage_code,
            event_type=event_type,
            event_payload=event_payload,
        )

        if event_type in {"chunk", "dimension", "dimension_complete"}:
            task_crud.update_task_heartbeat(db, task_id)

    return result_data, error_msg


def _finish_task(db: Session, task_id: int, task_type: str, result_data: Optional[Dict[str, Any]], error_msg: Optional[str]) -> None:
    if task_crud.is_cancel_requested(db, task_id):
        task_crud.mark_task_cancelled(db, task_id, "任务已取消")
        return

    if error_msg:
        status = "cancelled" if error_msg == "任务已取消" else "failed"
        task_crud.update_task_status(
            db,
            task_id,
            status,
            error_code="TASK_EXECUTION_ERROR" if status == "failed" else None,
            error_message=None if status == "cancelled" else error_msg,
            progress=100 if status == "failed" else None,
            stage_code=status,
            stage_message="任务已取消" if status == "cancelled" else f"任务失败：{error_msg}",
            force=True,
        )
        return

    envelope = _build_task_envelope(task_type, result_data or {})
    task_crud.update_task_result(db, task_id, envelope)


def execute_task_sync(task_id: int) -> None:
    """同步执行任务，供本地线程池和 Celery 共用"""
    db = SessionLocal()
    worker_id = get_worker_id()
    loop = None

    try:
        task = task_crud.get_task(db, task_id)
        if not task:
            return

        if task.status in {"cancelled", "success"}:
            return

        task_crud.update_task_status(
            db,
            task_id,
            "running",
            progress=max(task.progress or 0, 1),
            stage_code="running",
            stage_message="任务启动中...",
            worker_id=worker_id,
            force=True,
        )

        stream = _create_stream(task, db)
        if stream is None:
            task_crud.update_task_status(
                db,
                task_id,
                "failed",
                error_code="TASK_TYPE_UNSUPPORTED",
                error_message=f"未知任务类型: {task.task_type}",
                progress=100,
                stage_code="failed",
                stage_message="任务类型不支持",
                force=True,
            )
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result_data, error_msg = loop.run_until_complete(
            _run_analysis_stream(task_id, task.task_type, db, stream)
        )

        if inspect.isasyncgen(stream):
            loop.run_until_complete(stream.aclose())

        _finish_task(db, task_id, task.task_type, result_data, error_msg)
    except Exception as exc:
        logger.error("[TaskExecutor] task_id=%s 执行异常: %s", task_id, exc, exc_info=True)
        try:
            task_crud.update_task_status(
                db,
                task_id,
                "failed",
                error_code="TASK_EXECUTION_EXCEPTION",
                error_message=str(exc),
                progress=100,
                stage_code="failed",
                stage_message=f"任务失败：{exc}",
                force=True,
            )
        except Exception:
            logger.exception("[TaskExecutor] 标记任务失败时异常")
    finally:
        if loop is not None:
            loop.close()
        db.close()


def _worker_thread(task_id: int) -> None:
    execute_task_sync(task_id)


def _submit_local_task(task_id: int) -> None:
    _executor.submit(_worker_thread, task_id)


def submit_task(task_id: int, task_type: Optional[str] = None, connection_id: Optional[int] = None) -> str:
    """提交任务，优先 Celery，失败时回退本地执行"""
    del task_type, connection_id

    mode = settings.task_execution_mode.lower()
    use_celery = mode in {"auto", "celery"}

    if use_celery:
        try:
            from app.tasks.analysis_worker import run_analysis_task

            run_analysis_task.delay(task_id)
            return "celery"
        except Exception as exc:
            logger.warning("[TaskExecutor] Celery 提交失败，回退本地执行: %s", exc)
            if mode == "celery":
                raise

    _submit_local_task(task_id)
    return "local"


def get_progress(task_id: int) -> Optional[Dict[str, Any]]:
    """从数据库读取任务快照进度"""
    db = SessionLocal()
    try:
        task = task_crud.get_task(db, task_id)
        if not task:
            return None
        return {
            "progress": task.progress,
            "message": task.progress_message or task.stage_message or "",
            "stage_code": task.stage_code,
            "status": task.status,
        }
    finally:
        db.close()


def reconcile_stale_tasks() -> int:
    """启动时修复超时任务"""
    db = SessionLocal()
    count = 0
    try:
        stale_tasks = task_crud.get_stale_tasks(db, settings.task_stale_timeout_seconds)
        for task in stale_tasks:
            task_crud.update_task_status(
                db,
                task.id,
                "failed",
                error_code="TASK_HEARTBEAT_TIMEOUT",
                error_message="任务心跳超时，已标记失败",
                progress=task.progress,
                stage_code="failed",
                stage_message="任务心跳超时",
                force=True,
            )
            count += 1
        return count
    finally:
        db.close()
