"""
任务执行器

在后台线程池中运行 AI 分析任务，收集流式输出并存储结果。
"""

import asyncio
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Any, Optional, Callable

from sqlalchemy.orm import Session

from app.crud import task as task_crud
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# 全局线程池（最多 3 个并发分析任务）
_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="task-worker")

# 任务进度缓存：task_id -> {"progress": int, "message": str, "chunks": list[str]}
_progress_cache: Dict[int, Dict[str, Any]] = {}
_progress_lock = threading.Lock()


def get_progress(task_id: int) -> Optional[Dict[str, Any]]:
    """获取任务的实时进度（内存缓存）"""
    with _progress_lock:
        return _progress_cache.get(task_id)


def _update_progress(task_id: int, progress: int, message: str = "", chunk: str = ""):
    """更新内存中的进度缓存"""
    with _progress_lock:
        if task_id not in _progress_cache:
            _progress_cache[task_id] = {"progress": 0, "message": "", "chunks": []}
        entry = _progress_cache[task_id]
        entry["progress"] = progress
        entry["message"] = message
        if chunk:
            entry["chunks"].append(chunk)


def _cleanup_progress(task_id: int):
    """清理进度缓存（任务完成 60 秒后）"""
    import time

    def _do_cleanup():
        time.sleep(60)
        with _progress_lock:
            _progress_cache.pop(task_id, None)

    threading.Thread(target=_do_cleanup, daemon=True).start()


async def _run_analysis_stream(
    task_id: int,
    stream_generator,
):
    """
    消费流式生成器，收集结果并更新进度。

    stream_generator 是一个 async generator，yield (event_type, data) 元组。
    """
    chunks = []
    result_data = None
    error_msg = None
    total_steps = 1
    current_step = 0

    try:
        async for event_type, data in stream_generator:
            if event_type == "progress":
                # 健康报告特有的多维度进度
                total_steps = data.get("total", 1)
                current_step = data.get("current", 0)
                pct = int(current_step / total_steps * 80) if total_steps > 0 else 0
                _update_progress(task_id, pct, data.get("status", data.get("dimension", "")))

            elif event_type == "status":
                _update_progress(task_id, 5, data.get("message", ""))

            elif event_type == "context":
                _update_progress(task_id, 20, data.get("message", "数据收集完成"))

            elif event_type == "analysis":
                _update_progress(task_id, 30, data.get("message", "AI 分析中..."))

            elif event_type == "chunk":
                chunks.append(data.get("text", ""))
                # 流式输出期间进度在 30-90 之间
                _update_progress(task_id, min(30 + len(chunks) % 60, 90), "AI 分析中...", data.get("text", ""))

            elif event_type in ("dimension", "dimension_complete"):
                # 健康报告维度完成/分析中
                dim_name = data.get("dimension", data.get("name", ""))
                dim_status = data.get("status", "")
                pct = int(data.get("current", 0) / max(data.get("total", 1), 1) * 80)
                _update_progress(task_id, min(pct, 90), f"{dim_name}: {dim_status}" if dim_status else f"已完成: {dim_name}")

            elif event_type == "result":
                result_data = data
                _update_progress(task_id, 95, "分析完成，正在保存...")

            elif event_type == "error":
                error_msg = data.get("message", "未知错误")

    except Exception as e:
        logger.error(f"[TaskExecutor] task_id={task_id} 执行异常: {e}", exc_info=True)
        error_msg = str(e)

    return result_data, error_msg


def _worker_thread(task_id: int, task_type: str, connection_id: int):
    """
    在独立线程中运行分析任务。

    创建新的事件循环和数据库会话。
    """
    db = SessionLocal()
    try:
        # 更新状态为 running
        task_crud.update_task_status(db, task_id, "running")
        _update_progress(task_id, 1, "任务启动中...")

        # 创建流式生成器
        stream = _create_stream(task_type, db, connection_id)
        if stream is None:
            task_crud.update_task_status(db, task_id, "failed", error_message=f"未知任务类型: {task_type}")
            return

        # 在新事件循环中运行异步流
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result_data, error_msg = loop.run_until_complete(
                _run_analysis_stream(task_id, stream)
            )
        finally:
            loop.close()

        # 保存结果
        if error_msg:
            task_crud.update_task_status(db, task_id, "failed", error_message=error_msg)
            _update_progress(task_id, 100, f"失败: {error_msg}")
        else:
            result_json = json.dumps(result_data, ensure_ascii=False) if result_data else None
            task_crud.update_task_status(db, task_id, "success", result_json=result_json)
            _update_progress(task_id, 100, "完成")

    except Exception as e:
        logger.error(f"[TaskExecutor] worker 异常 task_id={task_id}: {e}", exc_info=True)
        try:
            task_crud.update_task_status(db, task_id, "failed", error_message=str(e))
        except Exception:
            pass
        _update_progress(task_id, 100, f"失败: {e}")
    finally:
        db.close()
        _cleanup_progress(task_id)


def _create_stream(task_type: str, db: Session, connection_id: int):
    """根据任务类型创建对应的流式生成器"""
    if task_type == "health_report":
        from app.services.ai.health_report_service import HealthReportService
        service = HealthReportService()
        return service.generate_report_stream(db=db, connection_id=connection_id)
    else:
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
        return method(db=db, connection_id=connection_id)


def submit_task(task_id: int, task_type: str, connection_id: int):
    """提交任务到线程池执行"""
    _executor.submit(_worker_thread, task_id, task_type, connection_id)
