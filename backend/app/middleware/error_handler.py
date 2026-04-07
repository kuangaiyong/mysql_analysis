"""
全局错误处理中间件
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback
from typing import Any, Callable
from datetime import datetime, timezone


logger = logging.getLogger(__name__)


class ErrorHandler:
    """全局错误处理器"""

    debug_mode: bool

    def __init__(self, debug_mode: bool = False) -> None:
        """初始化错误处理器"""
        self.debug_mode = debug_mode

    async def __call__(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        处理所有异常并返回统一格式的错误响应

        Args:
            request: FastAPI请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            JSON响应对象
        """
        try:
            response = await call_next(request)
            return response
        except StarletteHTTPException as e:
            logger.error(f"HTTP Exception: {e.status_code} - {e.detail}")
            if self.debug_mode:
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "success": False,
                        "error": {
                            "code": str(e.status_code),
                            "message": e.detail,
                            "detail": getattr(e, "detail", ""),
                            "traceback": traceback.format_exc(),
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
            else:
                return JSONResponse(
                    status_code=e.status_code,
                    content={
                        "success": False,
                        "error": {
                            "code": str(e.status_code),
                            "message": e.detail,
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
        except SQLAlchemyError as e:
            logger.error(f"Database Error: {str(e)}")
            if self.debug_mode:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "error": {
                            "code": "DATABASE_ERROR",
                            "message": "数据库操作失败",
                            "detail": str(e),
                            "traceback": traceback.format_exc(),
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "error": {
                            "code": "DATABASE_ERROR",
                            "message": "数据库操作失败",
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}\n{traceback.format_exc()}")
            if self.debug_mode:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "服务器内部错误",
                            "detail": str(e),
                            "traceback": traceback.format_exc(),
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "服务器内部错误",
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )


def create_error_handler(debug_mode: bool = False) -> ErrorHandler:
    """创建错误处理器实例"""
    return ErrorHandler(debug_mode=debug_mode)
