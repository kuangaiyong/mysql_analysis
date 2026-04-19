"""
AI 诊断 API 路由
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import json
from decimal import Decimal

from app.database import SessionLocal, get_session as get_db
from app.crud import task as task_crud
from app.services.ai.ai_diagnostic_service import AIDiagnosticService, get_ai_service
from app.services.ai.cache import get_cache
from app.services.ai.task_executor import submit_task
from app.services.ai.utils import DecimalEncoder, safe_jsonify
from app.config import settings
from app.crud import diagnosis as diagnosis_crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai-diagnostic"])


# ==================== 请求/响应模型 ====================

class ChatRequest(BaseModel):
    """对话请求"""
    connection_id: int = Field(..., description="MySQL 连接 ID")
    question: str = Field(..., description="用户问题")
    history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")
    depth: Optional[str] = Field("standard", description="采集深度: quick/standard/deep")
    session_id: Optional[int] = Field(None, description="会话 ID（为空则自动创建）")


class ChatResponse(BaseModel):
    """对话响应"""
    success: bool
    answer: str
    context_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    cached: bool = False


class OptimizeSQLRequest(BaseModel):
    """SQL 优化请求"""
    connection_id: int = Field(..., description="MySQL 连接 ID")
    sql: str = Field(..., description="待优化的 SQL 语句")


class OptimizeSQLResponse(BaseModel):
    """SQL 优化响应"""
    success: bool
    original_sql: str
    optimization: Optional[Dict[str, Any]] = None
    explain_before: Optional[Dict[str, Any]] = None
    explain_after: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider: Optional[str] = None


class ExplainRequest(BaseModel):
    """EXPLAIN 解读请求"""
    sql: str = Field(..., description="SQL 语句")
    explain_result: Dict[str, Any] = Field(..., description="EXPLAIN 执行结果")


class ExplainResponse(BaseModel):
    """EXPLAIN 解读响应"""
    success: bool
    sql: str
    interpretation: Optional[str] = None
    original_explain: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider: Optional[str] = None


class ExplainAnalyzeRequest(BaseModel):
    """EXPLAIN 优化分析请求（自动执行 EXPLAIN 并由 AI 分析）"""
    connection_id: int = Field(..., description="MySQL 连接 ID")
    sql: str = Field(..., description="待执行 EXPLAIN 的 SQL 语句")


class ConnectionOnlyRequest(BaseModel):
    """仅需连接 ID 的请求"""
    connection_id: int = Field(..., description="MySQL 连接 ID")


class QuickDiagnosisRequest(BaseModel):
    """快速诊断请求"""
    connection_id: int = Field(..., description="MySQL 连接 ID")
    question_type: str = Field(
        ..., 
        description="问题类型: slow_database, config_issues, slow_queries, index_suggestions, buffer_pool, lock_analysis, connection_health, io_bottleneck"
    )


class ExecuteSQLRequest(BaseModel):
    """SQL 执行请求"""
    connection_id: int = Field(..., description="MySQL 连接 ID")
    sql: str = Field(..., description="待执行的 SQL 语句")


class ClassifySQLRequest(BaseModel):
    """SQL 安全分类请求"""
    sql: str = Field(..., description="待分类的 SQL 语句")


class AIStatusResponse(BaseModel):
    """AI 状态响应"""
    enabled: bool
    provider: str
    model: str
    cache_enabled: bool
    rate_limit: int


# ==================== 问题类型映射 ====================

QUESTION_TYPE_MAPPING = {
    "slow_database": "为什么数据库变慢了？",
    "config_issues": "请分析当前 MySQL 配置存在的问题",
    "slow_queries": "请分析 Top 5 慢查询及其优化建议",
    "index_suggestions": "请分析当前数据库需要添加哪些索引",
    "buffer_pool": "请分析 Buffer Pool 使用情况和优化建议",
    "lock_analysis": "请分析当前的锁等待情况",
    "connection_health": "请分析当前连接健康状态",
    "io_bottleneck": "请分析当前 I/O 瓶颈",
}


TASK_ROUTE_MAPPING = {
    "health_report": "health-report",
    "index_advisor": "index-advisor",
    "lock_analysis": "lock-analysis",
    "slow_query_patrol": "slow-query-patrol",
    "config_tuning": "config-tuning",
    "capacity_prediction": "capacity-prediction",
}


def _create_compat_task(db: Session, connection_id: int, task_type: str):
    task = task_crud.create_task(
        db=db,
        connection_id=connection_id,
        task_type=task_type,
        payload={"connection_id": connection_id},
        payload_summary={"connection_id": connection_id},
        source_page=TASK_ROUTE_MAPPING.get(task_type, "task-center"),
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
    submit_task(task.id)
    return task


async def _stream_task_compat(request: Request, db: Session, connection_id: int, task_type: str):
    task = _create_compat_task(db, connection_id, task_type)

    async def event_generator():
        last_seq = 0
        while True:
            if await request.is_disconnected():
                return

            db_session = SessionLocal()
            try:
                task_db = task_crud.get_task(db_session, task.id)
                if not task_db:
                    yield _format_sse_event("error", {"message": "任务不存在"})
                    return

                events = task_crud.list_task_events(db_session, task.id, after_seq=last_seq, limit=200)
                for event in events:
                    last_seq = event.seq
                    payload = {}
                    if event.event_json:
                        try:
                            payload = json.loads(event.event_json)
                        except json.JSONDecodeError:
                            payload = {"message": event.event_json}

                    event_type = event.event_type
                    if event_type == "status_changed":
                        if task_db.status == "failed":
                            yield _format_sse_event("error", {"message": task_db.error_message or "任务失败"})
                            return
                        if task_db.status == "cancelled":
                            yield _format_sse_event("error", {"message": "任务已取消"})
                            return
                        continue

                    if event_type in {"status", "context", "analysis", "progress", "dimension", "dimension_complete", "chunk"}:
                        yield _format_sse_event(event_type, payload)
                    elif event_type == "result_ready" and task_db.result_json:
                        try:
                            result = json.loads(task_db.result_json)
                            raw = result.get("raw", result)
                        except json.JSONDecodeError:
                            raw = {"message": task_db.result_json}
                        yield _format_sse_event("result", safe_jsonify(raw))
                        return
                    elif event_type == "error":
                        yield _format_sse_event("error", payload or {"message": task_db.error_message or "任务失败"})
                        return

                if task_db.status == "success" and task_db.result_json:
                    try:
                        result = json.loads(task_db.result_json)
                        raw = result.get("raw", result)
                    except json.JSONDecodeError:
                        raw = {"message": task_db.result_json}
                    yield _format_sse_event("result", safe_jsonify(raw))
                    return

                if task_db.status == "failed":
                    yield _format_sse_event("error", {"message": task_db.error_message or "任务失败"})
                    return

                if task_db.status == "cancelled":
                    yield _format_sse_event("error", {"message": "任务已取消"})
                    return
            finally:
                db_session.close()

            await asyncio.sleep(settings.task_stream_poll_interval)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ==================== API 端点 ====================

@router.get("/status", response_model=AIStatusResponse)
async def get_ai_status():
    """获取 AI 服务状态"""
    model_map = {
        "kimi": settings.kimi_model,
        "zhipu": settings.zhipu_model,
        "openai": settings.openai_model,
        "claude": settings.claude_model,
    }
    return AIStatusResponse(
        enabled=settings.ai_enabled,
        provider=settings.ai_provider,
        model=model_map.get(settings.ai_provider, "unknown"),
        cache_enabled=settings.ai_cache_enabled,
        rate_limit=settings.ai_rate_limit_requests
    )


@router.post("/chat")
async def ai_chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """AI 诊断对话"""
    try:
        # 尝试从缓存获取
        if settings.ai_cache_enabled and not request.history:
            cache = get_cache()
            cached_response = cache.get_sync(
                connection_id=request.connection_id,
                question=request.question
            )
            if cached_response:
                logger.info(f"从缓存返回响应")
                # 缓存结构是 {"response": {...}, "cached_at": ..., ...}，需要解包
                result = cached_response.get("response", cached_response)
                result["cached"] = True
                return JSONResponse(content=safe_jsonify(result))
        
        service = get_ai_service()
        result = await service.diagnose(
            db=db,
            connection_id=request.connection_id,
            question=request.question,
            history=request.history,
            depth=request.depth or "standard"
        )
        
        # 缓存成功的响应
        if settings.ai_cache_enabled and result.get("success") and not request.history:
            cache = get_cache()
            cache.set_sync(
                connection_id=request.connection_id,
                question=request.question,
                response=result
            )
        
        result["cached"] = False
        return JSONResponse(content=safe_jsonify(result))
        
    except Exception as e:
        logger.error(f"AI 对话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 服务异常: {str(e)}"
        )


@router.post("/optimize-sql")
async def optimize_sql(
    request: OptimizeSQLRequest,
    db: Session = Depends(get_db)
):
    """SQL 优化建议"""
    try:
        service = get_ai_service()
        result = await service.optimize_sql(
            db=db,
            connection_id=request.connection_id,
            sql=request.sql
        )
        return JSONResponse(content=safe_jsonify(result))
    except Exception as e:
        logger.error(f"SQL 优化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 服务异常: {str(e)}"
        )


@router.post("/explain-interpret")
async def explain_interpret(request: ExplainRequest):
    """EXPLAIN 结果解读"""
    try:
        service = get_ai_service()
        result = await service.explain_interpret(
            sql=request.sql,
            explain_result=request.explain_result
        )
        return JSONResponse(content=safe_jsonify(result))
    except Exception as e:
        logger.error(f"EXPLAIN 解读失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 服务异常: {str(e)}"
        )


@router.post("/explain-analyze")
async def explain_analyze(
    request: ExplainAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """执行 EXPLAIN 并由 AI 进行优化分析"""
    from app.services.ai.context_builder import AIContextBuilder
    try:
        # 执行 EXPLAIN
        context_builder = AIContextBuilder(db, request.connection_id)
        connector = context_builder._get_connector()
        # 去掉开头的 EXPLAIN 关键字（如果有）
        sql_clean = request.sql.strip()
        sql_lower = sql_clean.lower()
        if sql_lower.startswith("explain"):
            sql_to_explain = sql_clean[len("explain"):].strip()
        else:
            sql_to_explain = sql_clean
        explain_rows = connector.execute_query(f"EXPLAIN {sql_to_explain}")
        explain_result = {"rows": explain_rows}
        context_builder.close()

        # AI 分析
        service = get_ai_service()
        result = await service.explain_interpret(
            sql=sql_to_explain,
            explain_result=explain_result
        )
        return JSONResponse(content=safe_jsonify(result))
    except Exception as e:
        logger.error(f"EXPLAIN 优化分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 服务异常: {str(e)}"
        )


@router.post("/quick-diagnosis")
async def quick_diagnosis(
    request: QuickDiagnosisRequest,
    db: Session = Depends(get_db)
):
    """快速诊断"""
    try:
        service = get_ai_service()
        result = await service.diagnose(
            db=db,
            connection_id=request.connection_id,
            question=QUESTION_TYPE_MAPPING.get(request.question_type, "请分析当前数据库状态"),
            history=None
        )
        
        return JSONResponse(content=safe_jsonify(result))
    except Exception as e:
        logger.error(f"快速诊断失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 服务异常: {str(e)}"
        )



# ==================== SQL 执行端点 ====================

@router.post("/classify-sql")
async def classify_sql_endpoint(request: ClassifySQLRequest):
    """SQL 安全分类"""
    from app.services.sql_executor import classify_sql
    result = classify_sql(request.sql)
    return {
        "risk_level": result.risk_level.value,
        "risk_label": result.risk_label,
        "risk_color": result.risk_color,
        "description": result.description,
        "rollback_sql": result.rollback_sql,
        "impact": result.impact,
        "requires_confirmation": result.requires_confirmation,
    }


@router.post("/execute-sql")
async def execute_sql_endpoint(
    request: ExecuteSQLRequest,
    db: Session = Depends(get_db),
):
    """
    执行 SQL（带安全分类校验）

    流程：分类 → 拒绝 forbidden → 执行 → 返回结果
    """
    from app.services.sql_executor import classify_sql, execute_sql_on_connection, RiskLevel

    # 安全分类
    classification = classify_sql(request.sql)

    if classification.risk_level == RiskLevel.FORBIDDEN:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": f"禁止执行: {classification.description}",
                "risk_level": classification.risk_level.value,
                "risk_label": classification.risk_label,
            }
        )

    # 执行
    result = await execute_sql_on_connection(
        connection_id=request.connection_id,
        sql=request.sql,
        db_session=db,
    )

    # 附加分类信息
    result["risk_level"] = classification.risk_level.value
    result["risk_label"] = classification.risk_label
    result["rollback_sql"] = classification.rollback_sql

    if result["success"]:
        return JSONResponse(content=safe_jsonify(result))
    else:
        return JSONResponse(status_code=400, content=result)


# ==================== SSE 辅助函数 ====================

def _format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """
    格式化 SSE 事件
    
    Args:
        event_type: 事件类型 (status, context, analysis, result, error)
        data: 事件数据
    
    Returns:
        格式化后的 SSE 字符串
    """
    json_str = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {json_str}\n\n"


async def _sse_event_generator(
    request: Any,  # Request 对象
    event_type: str,
    data: Dict[str, Any]
):
    """
    SSE 事件生成器，检测客户端断开
    
    Args:
        request: FastAPI Request 对象
        event_type: 事件类型
        data: 事件数据
    """
    if await request.is_disconnected():
        return
    yield _format_sse_event(event_type, data)


# ==================== SSE 端点 ====================

@router.post("/chat/stream")
async def ai_chat_stream(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    AI 诊断对话 - SSE 流式响应

    发送事件序列：status -> context -> analysis -> result
    """
    async def event_generator():
        try:
            service = get_ai_service()

            # 使用 diagnose_stream 真流式生成器
            async for event_type, data in service.diagnose_stream(
                db=db,
                connection_id=chat_request.connection_id,
                question=chat_request.question,
                history=chat_request.history,
                depth=chat_request.depth or "standard"
            ):
                if await request.is_disconnected():
                    return
                yield _format_sse_event(event_type, safe_jsonify(data) if event_type == "result" else data)

        except Exception as e:
            logger.error(f"SSE 流式响应错误: {e}")
            yield _format_sse_event("error", {"message": str(e)})
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@router.post("/quick-diagnosis/stream")
async def quick_diagnosis_stream(
    request: Request,
    quick_request: QuickDiagnosisRequest,
    db: Session = Depends(get_db)
):
    """
    快速诊断 SSE 流式响应端点
    
    发送事件序列：status -> context -> analysis -> result
    """
    async def event_generator():
        try:
            # 映射 question类型
            question = QUESTION_TYPE_MAPPING.get(
                quick_request.question_type, 
                "请分析当前数据库状态"
            )
            
            service = get_ai_service()
            
            # 使用 diagnose_stream 异步生成器
            async for event_type, data in service.diagnose_stream(
                db=db,
                connection_id=quick_request.connection_id,
                question=question
            ):
                if await request.is_disconnected():
                    return
                yield _format_sse_event(event_type, data)
                
        except Exception as e:
            logger.error(f"快速诊断 SSE 流式响应错误: {e}")
            yield _format_sse_event("error", {"message": str(e)})
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# ==================== SQL 优化 SSE 端点 ====================

@router.post("/optimize-sql/stream")
async def optimize_sql_stream(
    request: Request,
    optimize_request: OptimizeSQLRequest,
    db: Session = Depends(get_db)
):
    """
    SQL 优化建议 - SSE 流式响应
    """
    async def event_generator():
        try:
            service = get_ai_service()

            # 使用 optimize_sql_stream 真流式生成器
            async for event_type, data in service.optimize_sql_stream(
                db=db,
                connection_id=optimize_request.connection_id,
                sql=optimize_request.sql
            ):
                if await request.is_disconnected():
                    return
                yield _format_sse_event(event_type, safe_jsonify(data) if event_type == "result" else data)

        except Exception as e:
            logger.error(f"SQL 优化 SSE 流式响应错误: {e}")
            yield _format_sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# ==================== 会话管理请求/响应模型 ====================

class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    connection_id: int = Field(..., description="MySQL 连接 ID")
    session_type: str = Field("chat", description="会话类型: chat/quick")
    title: str = Field("新对话", description="会话标题")


class UpdateSessionRequest(BaseModel):
    """更新会话请求"""
    title: str = Field(..., description="新标题")


class SessionResponse(BaseModel):
    """会话响应"""
    id: int
    connection_id: int
    session_type: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    session_id: int
    role: str
    content: str
    context_snapshot: Optional[str] = None
    created_at: datetime


class SessionDetailResponse(BaseModel):
    """会话详情响应（含消息列表）"""
    session: SessionResponse
    messages: List[MessageResponse]


# ==================== 会话管理端点 ====================

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db)
):
    """创建诊断会话"""
    session = diagnosis_crud.create_session(
        db=db,
        connection_id=request.connection_id,
        session_type=request.session_type,
        title=request.title,
    )
    msg_count = diagnosis_crud.count_messages(db, session.id)
    return SessionResponse(
        id=session.id,
        connection_id=session.connection_id,
        session_type=session.session_type,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=msg_count,
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    connection_id: int = Query(..., description="MySQL 连接 ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取会话列表"""
    sessions = diagnosis_crud.get_sessions(db, connection_id, limit, offset)
    result = []
    for s in sessions:
        msg_count = diagnosis_crud.count_messages(db, s.id)
        result.append(SessionResponse(
            id=s.id,
            connection_id=s.connection_id,
            session_type=s.session_type,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=msg_count,
        ))
    return result


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
):
    """获取会话详情（含消息列表）"""
    session = diagnosis_crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = diagnosis_crud.get_session_messages(db, session_id)
    msg_count = len(messages)
    return SessionDetailResponse(
        session=SessionResponse(
            id=session.id,
            connection_id=session.connection_id,
            session_type=session.session_type,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=msg_count,
        ),
        messages=[
            MessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                context_snapshot=m.context_snapshot,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    request: UpdateSessionRequest,
    db: Session = Depends(get_db),
):
    """更新会话标题"""
    session = diagnosis_crud.update_session_title(db, session_id, request.title)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    msg_count = diagnosis_crud.count_messages(db, session.id)
    return SessionResponse(
        id=session.id,
        connection_id=session.connection_id,
        session_type=session.session_type,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=msg_count,
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """删除会话"""
    ok = diagnosis_crud.delete_session(db, session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"success": True, "message": "会话已删除"}


# ==================== 带会话持久化的对话 SSE 端点 ====================

@router.post("/chat-with-session/stream")
async def ai_chat_with_session_stream(
    request: Request,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    AI 诊断对话（带会话持久化）- SSE 流式响应

    若 session_id 为空则自动创建会话，自动保存 user/assistant 消息。
    """
    async def event_generator():
        session_id = chat_request.session_id
        try:
            # 自动创建会话
            if not session_id:
                title = chat_request.question[:50] if chat_request.question else "新对话"
                session_obj = diagnosis_crud.create_session(
                    db=db,
                    connection_id=chat_request.connection_id,
                    session_type="chat",
                    title=title,
                )
                session_id = session_obj.id
                yield _format_sse_event("session", {"session_id": session_id, "title": title})

            # 保存用户消息
            diagnosis_crud.add_message(
                db=db,
                session_id=session_id,
                role="user",
                content=chat_request.question,
            )

            # 从数据库加载历史消息作为上下文
            db_messages = diagnosis_crud.get_session_messages(db, session_id, limit=50)
            history = [
                {"role": m.role, "content": m.content}
                for m in db_messages[:-1]  # 排除刚保存的当前消息
            ] if len(db_messages) > 1 else None

            service = get_ai_service()
            full_answer = ""

            async for event_type, data in service.diagnose_stream(
                db=db,
                connection_id=chat_request.connection_id,
                question=chat_request.question,
                history=history,
                depth=chat_request.depth or "standard",
            ):
                if await request.is_disconnected():
                    return
                if event_type == "result":
                    data = safe_jsonify(data)
                    data["session_id"] = session_id
                    full_answer = data.get("answer", "")
                yield _format_sse_event(event_type, data)

            # 保存 AI 回复
            if full_answer:
                diagnosis_crud.add_message(
                    db=db,
                    session_id=session_id,
                    role="assistant",
                    content=full_answer,
                )

        except Exception as e:
            logger.error(f"带会话的 SSE 流式响应错误: {e}")
            yield _format_sse_event("error", {"message": str(e), "session_id": session_id})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# ==================== 健康报告请求/响应模型 ====================

class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    connection_id: int = Field(..., description="MySQL 连接 ID")


class ReportResponse(BaseModel):
    """报告响应"""
    id: int
    connection_id: int
    report_type: str
    health_score: int
    created_at: datetime


class ReportDetailResponse(BaseModel):
    """报告详情响应"""
    id: int
    connection_id: int
    report_type: str
    health_score: int
    content: Dict[str, Any]
    dimensions: List[Dict[str, Any]]
    created_at: datetime


# ==================== 健康报告端点 ====================

@router.post("/reports/generate/stream")
async def generate_report_stream(
    request: Request,
    report_request: GenerateReportRequest,
    db: Session = Depends(get_db),
):
    """生成健康巡检报告 - SSE 流式响应"""
    return await _stream_task_compat(request, db, report_request.connection_id, "health_report")


@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    connection_id: int = Query(..., description="MySQL 连接 ID"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取报告列表"""
    reports = diagnosis_crud.get_reports(db, connection_id, limit)
    return [
        ReportResponse(
            id=r.id,
            connection_id=r.connection_id,
            report_type=r.report_type,
            health_score=r.health_score,
            created_at=r.created_at,
        )
        for r in reports
    ]


@router.get("/reports/{report_id}")
async def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
):
    """获取报告详情"""
    report = diagnosis_crud.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return JSONResponse(content=safe_jsonify({
        "id": report.id,
        "connection_id": report.connection_id,
        "report_type": report.report_type,
        "health_score": report.health_score,
        "content": json.loads(report.content_json) if report.content_json else {},
        "dimensions": json.loads(report.dimensions_json) if report.dimensions_json else [],
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }))


@router.delete("/reports/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    """删除报告"""
    ok = diagnosis_crud.delete_report(db, report_id)
    if not ok:
        raise HTTPException(status_code=404, detail="报告不存在")
    return {"success": True, "message": "报告已删除"}


@router.get("/reports/{report_id}/export")
async def export_report_markdown(
    report_id: int,
    db: Session = Depends(get_db),
):
    """导出报告为 Markdown"""
    from app.services.ai.health_report_service import HealthReportService

    report = diagnosis_crud.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    md_content = HealthReportService.export_to_markdown(report)
    return PlainTextResponse(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="health-report-{report_id}.md"'
        }
    )


# ==================== EXPLAIN 分析 SSE 端点 ====================

@router.post("/explain-analyze/stream")
async def explain_analyze_stream(
    request: Request,
    explain_request: ExplainAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """执行 EXPLAIN 并由 AI 进行流式分析"""
    from app.services.ai.context_builder import AIContextBuilder

    async def event_generator():
        context_builder = None
        try:
            yield _format_sse_event("status", {"message": "正在执行 EXPLAIN...", "step": "explain"})

            context_builder = AIContextBuilder(db, explain_request.connection_id)
            connector = context_builder._get_connector()

            sql_clean = explain_request.sql.strip()
            sql_lower = sql_clean.lower()
            if sql_lower.startswith("explain"):
                sql_to_explain = sql_clean[len("explain"):].strip()
            else:
                sql_to_explain = sql_clean

            explain_rows = connector.execute_query(f"EXPLAIN {sql_to_explain}")
            explain_result = {"rows": explain_rows}
            context_builder.close()
            context_builder = None

            yield _format_sse_event("context", {
                "message": "EXPLAIN 执行完成",
                "explain_result": safe_jsonify(explain_result),
            })

            service = get_ai_service()
            async for event_type, data in service.explain_interpret_stream(
                sql=sql_to_explain,
                explain_result=explain_result,
            ):
                if await request.is_disconnected():
                    return
                yield _format_sse_event(event_type, safe_jsonify(data) if event_type == "result" else data)

        except Exception as e:
            logger.error(f"EXPLAIN 分析 SSE 错误: {e}")
            yield _format_sse_event("error", {"message": str(e)})
        finally:
            if context_builder:
                context_builder.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# ==================== SQL 优化历史记录端点 ====================

class SqlOptRecordResponse(BaseModel):
    """SQL 优化记录响应"""
    id: int
    connection_id: int
    original_sql: str
    created_at: datetime


@router.get("/sql-optimization-records", response_model=List[SqlOptRecordResponse])
async def list_sql_optimization_records(
    connection_id: int = Query(..., description="MySQL 连接 ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """获取 SQL 优化历史记录列表"""
    records = diagnosis_crud.get_sql_optimization_records(db, connection_id, limit)
    return [
        SqlOptRecordResponse(
            id=r.id,
            connection_id=r.connection_id,
            original_sql=r.original_sql,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/sql-optimization-records/{record_id}")
async def get_sql_optimization_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """获取 SQL 优化记录详情"""
    record = diagnosis_crud.get_sql_optimization_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return JSONResponse(content=safe_jsonify({
        "id": record.id,
        "connection_id": record.connection_id,
        "original_sql": record.original_sql,
        "result": json.loads(record.result_json) if record.result_json else {},
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }))


@router.delete("/sql-optimization-records/{record_id}")
async def delete_sql_optimization_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """删除 SQL 优化记录"""
    ok = diagnosis_crud.delete_sql_optimization_record(db, record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"success": True, "message": "记录已删除"}


@router.post("/sql-optimization-records/save")
async def save_sql_optimization_record(
    request: Request,
    db: Session = Depends(get_db),
):
    """手动保存 SQL 优化记录"""
    body = await request.json()
    connection_id = body.get("connection_id")
    original_sql = body.get("original_sql", "")
    result = body.get("result", {})
    if not connection_id or not original_sql:
        raise HTTPException(status_code=400, detail="缺少 connection_id 或 original_sql")
    record = diagnosis_crud.create_sql_optimization_record(
        db=db,
        connection_id=connection_id,
        original_sql=original_sql,
        result_json=json.dumps(result, ensure_ascii=False),
    )
    return {"success": True, "id": record.id}


# ==================== EXPLAIN 分析历史记录端点 ====================

class ExplainRecordResponse(BaseModel):
    """EXPLAIN 分析记录响应"""
    id: int
    connection_id: int
    sql: str
    created_at: datetime


@router.get("/explain-analysis-records", response_model=List[ExplainRecordResponse])
async def list_explain_analysis_records(
    connection_id: int = Query(..., description="MySQL 连接 ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """获取 EXPLAIN 分析历史记录列表"""
    records = diagnosis_crud.get_explain_analysis_records(db, connection_id, limit)
    return [
        ExplainRecordResponse(
            id=r.id,
            connection_id=r.connection_id,
            sql=r.sql,
            created_at=r.created_at,
        )
        for r in records
    ]


@router.get("/explain-analysis-records/{record_id}")
async def get_explain_analysis_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """获取 EXPLAIN 分析记录详情"""
    record = diagnosis_crud.get_explain_analysis_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    return JSONResponse(content=safe_jsonify({
        "id": record.id,
        "connection_id": record.connection_id,
        "sql": record.sql,
        "result": json.loads(record.result_json) if record.result_json else {},
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }))


@router.delete("/explain-analysis-records/{record_id}")
async def delete_explain_analysis_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """删除 EXPLAIN 分析记录"""
    ok = diagnosis_crud.delete_explain_analysis_record(db, record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"success": True, "message": "记录已删除"}


@router.post("/explain-analysis-records/save")
async def save_explain_analysis_record(
    request: Request,
    db: Session = Depends(get_db),
):
    """手动保存 EXPLAIN 分析记录"""
    body = await request.json()
    connection_id = body.get("connection_id")
    sql = body.get("sql", "")
    result = body.get("result", {})
    if not connection_id or not sql:
        raise HTTPException(status_code=400, detail="缺少 connection_id 或 sql")
    record = diagnosis_crud.create_explain_analysis_record(
        db=db,
        connection_id=connection_id,
        sql=sql,
        result_json=json.dumps(result, ensure_ascii=False),
    )
    return {"success": True, "id": record.id}


# ==================== 5 个新 AI 模块 SSE 端点 ====================

def _make_analysis_sse_endpoint(service_method_name: str, label: str):
    """工厂函数：创建通用分析 SSE 端点"""
    task_type_map = {
        "index_advisor_stream": "index_advisor",
        "lock_analysis_stream": "lock_analysis",
        "slow_query_patrol_stream": "slow_query_patrol",
        "config_tuning_stream": "config_tuning",
        "capacity_prediction_stream": "capacity_prediction",
    }

    async def endpoint(
        request: Request,
        body: ConnectionOnlyRequest,
        db: Session = Depends(get_db),
    ):
        task_type = task_type_map.get(service_method_name, "index_advisor")
        return await _stream_task_compat(request, db, body.connection_id, task_type)
    endpoint.__doc__ = f"{label} - SSE 流式响应"
    return endpoint


router.post("/index-advisor/stream")(_make_analysis_sse_endpoint("index_advisor_stream", "索引顾问"))
router.post("/lock-analysis/stream")(_make_analysis_sse_endpoint("lock_analysis_stream", "锁分析"))
router.post("/slow-query-patrol/stream")(_make_analysis_sse_endpoint("slow_query_patrol_stream", "慢查询巡检"))
router.post("/config-tuning/stream")(_make_analysis_sse_endpoint("config_tuning_stream", "配置调优"))
router.post("/capacity-prediction/stream")(_make_analysis_sse_endpoint("capacity_prediction_stream", "容量预测"))
