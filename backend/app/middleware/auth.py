"""
API路由保护中间件
保护所有 /api/v1/* 端点，验证JWT token
"""

import json
from typing import Callable, Awaitable

from starlette.types import ASGIApp, Receive, Scope, Send, Message


from app.core.auth import decode_access_token


# 公开路由列表（无需认证）
PUBLIC_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
    "/api/docs",
    "/api/redoc",
    "/openapi.json",
    "/api/health",
}


class AuthMiddleware:
    """
    认证中间件（纯ASGI实现）
    检查所有 /api/v1/* 请求的Authorization header
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        method = scope["method"]

        # OPTIONS 请求 (CORS preflight) 跳过认证
        if method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        # 跳过公开路由
        if path in PUBLIC_PATHS:
            await self.app(scope, receive, send)
            return

        # 只保护 /api/v1/* 路由
        if not path.startswith("/api/v1/"):
            await self.app(scope, receive, send)
            return

        # 检查 Authorization header
        headers = dict(scope["headers"])
        auth_header = headers.get(b"authorization", headers.get(b"Authorization"))

        if not auth_header:
            await self._unauthorized_response(send, "缺少认证令牌")
            return

        # 解码 header 值
        if isinstance(auth_header, bytes):
            auth_header = auth_header.decode("utf-8")

        # 验证 Bearer token 格式
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            await self._unauthorized_response(send, "无效的认证格式")
            return

        token = parts[1]

        # 验证 token
        payload = decode_access_token(token)
        if payload is None:
            await self._unauthorized_response(send, "无效或过期的令牌")
            return

        # Token 有效，继续请求
        await self.app(scope, receive, send)

    async def _unauthorized_response(self, send: Send, message: str) -> None:
        """返回401未授权响应"""
        body = json.dumps(
            {
                "success": False,
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": message,
                },
            }
        ).encode("utf-8")

        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(body)).encode()],
                    [b"www-authenticate", b"Bearer"],
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )
