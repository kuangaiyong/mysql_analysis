"""
FastAPI 主应用模块
"""

# ========== 全局 JSON 序列化补丁（修复 Decimal 序列化问题）==========
from decimal import Decimal
import json as _json

_original_dumps = _json.dumps

def _decimal_friendly_dumps(obj, **kwargs):
    """
    自定义 json.dumps，自动处理 Decimal 类型
    """
    def default(o):
        if isinstance(o, Decimal):
            return float(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    
    kwargs.setdefault('default', default)
    return _original_dumps(obj, **kwargs)

# 替换全局 json.dumps
_json.dumps = _decimal_friendly_dumps
# ========== 补丁结束 ==========

from fastapi import FastAPI, Request, status
from app.middleware.auth import AuthMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError
from app import config

# 修复 FastAPI 的 jsonable_encoder，使其能够处理 Decimal 类型
from fastapi.encoders import jsonable_encoder as _original_jsonable_encoder

def decimal_aware_jsonable_encoder(obj, **kwargs):
    """
    自定义 jsonable_encoder，处理 Decimal 类型
    """
    # 先转换为可序列化的格式
    def convert_decimals(o):
        if isinstance(o, Decimal):
            return float(o)
        elif isinstance(o, dict):
            return {k: convert_decimals(v) for k, v in o.items()}
        elif isinstance(o, (list, tuple)):
            return [convert_decimals(item) for item in o]
        return o
    
    converted = convert_decimals(obj)
    return _original_jsonable_encoder(converted, **kwargs)

# 替换 jsonable_encoder
import fastapi.encoders
fastapi.encoders.jsonable_encoder = decimal_aware_jsonable_encoder

settings = config.settings
from app.database import init_db
from app.routers import (
    auth,
    connections,
    ai_diagnostic
)
import logging
import traceback
from datetime import datetime, timezone

# 初始化日志系统（使用增强的详细日志）
from app.core.logging_config import app_logger
from app.core.detailed_logging import setup_detailed_logging
from app.middleware.json_serialization import JSONSerializationMiddleware

# 设置详细日志
setup_detailed_logging(settings.log_level)

logger = app_logger


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="MySQL AI 智能诊断系统",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 添加全局 JSON 序列化中间件（处理 Decimal 等类型）
app.add_middleware(JSONSerializationMiddleware)
logger.info("✅ 已添加全局 JSON 序列化中间件")


# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 认证中间件
app.add_middleware(AuthMiddleware)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unexpected Error: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "detail": str(exc) if settings.debug else None,
                "traceback": traceback.format_exc() if settings.debug else None,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库异常处理器"""
    logger.error(f"Database Error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "数据库操作失败",
                "detail": str(exc) if settings.debug else None,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    init_db()


# 连接管理路由
app.include_router(connections.router, prefix="/api/v1/connections", tags=["连接管理"])


# 认证路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])

# AI 诊断路由
app.include_router(ai_diagnostic.router)
