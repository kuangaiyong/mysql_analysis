"""
分析任务 API 路由
"""

import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_session as get_db
from app.crud import task as task_crud
from app.services.ai.task_executor import submit_task, get_progress

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["任务管理"])

VALID_TASK_TYPES = {
    "health_report", "index_advisor", "lock_analysis",
    "slow_query_patrol", "config_tuning", "capacity_prediction",
}


# ==================== 请求模型 ====================

class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    connection_id: int
    task_type: str
    title: Optional[str] = None


# ==================== 端点 ====================

@router.post("")
def create_task(body: CreateTaskRequest, db: Session = Depends(get_db)):
    """创建并启动分析任务"""
    if body.task_type not in VALID_TASK_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的任务类型: {body.task_type}")

    task = task_crud.create_task(
        db=db,
        connection_id=body.connection_id,
        task_type=body.task_type,
        title=body.title,
    )

    # 提交到后台线程池
    submit_task(task.id, task.task_type, task.connection_id)

    return {
        "success": True,
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
        db, connection_id=connection_id, task_type=task_type,
        status=task_status, limit=limit, offset=offset,
    )
    total = task_crud.count_tasks(
        db, connection_id=connection_id, task_type=task_type, status=task_status,
    )
    return {
        "success": True,
        "data": [_task_to_dict(t) for t in tasks],
        "total": total,
    }


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情"""
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    data = _task_to_dict(task)
    # 附加实时进度
    progress = get_progress(task_id)
    if progress:
        data["live_progress"] = progress["progress"]
        data["live_message"] = progress["message"]

    return {"success": True, "data": data}


@router.post("/{task_id}/retry")
def retry_task(task_id: int, db: Session = Depends(get_db)):
    """重试失败的任务"""
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "failed":
        raise HTTPException(status_code=400, detail="只有失败的任务可以重试")

    task = task_crud.increment_retry(db, task_id)
    if not task:
        raise HTTPException(status_code=400, detail="已达到最大重试次数")

    # 重新提交
    submit_task(task.id, task.task_type, task.connection_id)

    return {"success": True, "data": _task_to_dict(task)}


@router.post("/{task_id}/cancel")
def cancel_task(task_id: int, db: Session = Depends(get_db)):
    """取消任务"""
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail="只有进行中的任务可以取消")

    task_crud.update_task_status(db, task_id, "cancelled")
    return {"success": True, "message": "任务已取消"}


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务"""
    if not task_crud.delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "message": "任务已删除"}


@router.get("/{task_id}/progress")
async def task_progress_sse(task_id: int, request: Request, db: Session = Depends(get_db)):
    """任务实时进度 SSE 流"""
    task = task_crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    async def event_generator():
        last_progress = -1
        while True:
            if await request.is_disconnected():
                break

            # 检查数据库状态
            db_task = task_crud.get_task(db, task_id)
            if not db_task:
                yield f"event: error\ndata: {{\"message\": \"任务不存在\"}}\n\n"
                break

            progress_info = get_progress(task_id)
            current = progress_info["progress"] if progress_info else (100 if db_task.status in ("success", "failed", "cancelled") else 0)
            message = progress_info["message"] if progress_info else db_task.progress_message or ""

            if current != last_progress:
                last_progress = current
                data = json.dumps({
                    "task_id": task_id,
                    "status": db_task.status,
                    "progress": current,
                    "message": message,
                }, ensure_ascii=False)
                yield f"event: progress\ndata: {data}\n\n"

            if db_task.status in ("success", "failed", "cancelled"):
                final = json.dumps({
                    "task_id": task_id,
                    "status": db_task.status,
                    "progress": 100,
                    "message": "完成" if db_task.status == "success" else message,
                }, ensure_ascii=False)
                yield f"event: complete\ndata: {final}\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _task_to_dict(task) -> dict:
    """将 AnalysisTask ORM 对象转为字典"""
    return {
        "id": task.id,
        "connection_id": task.connection_id,
        "task_type": task.task_type,
        "status": task.status,
        "title": task.title,
        "progress": task.progress,
        "progress_message": task.progress_message or "",
        "result_json": task.result_json,
        "error_message": task.error_message,
        "retry_count": task.retry_count,
        "max_retries": task.max_retries,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
