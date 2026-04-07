"""
AI 请求限流中间件

基于 Redis 的滑动窗口限流算法
"""

import time
import logging
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings

logger = logging.getLogger(__name__)


class AIRateLimiter:
    """
    AI 请求限流器
    
    使用滑动窗口算法限制 AI 请求频率
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 3600,
        redis_client: Optional[object] = None
    ):
        """
        初始化限流器
        
        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
            redis_client: Redis 客户端（可选，不提供则使用内存存储）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis = redis_client
        self._memory_store: dict = {}  # 内存存储（无 Redis 时使用）
    
    def _get_redis_key(self, client_id: str) -> str:
        """获取 Redis 键"""
        return f"ai_rate_limit:{client_id}"
    
    async def is_allowed(self, client_id: str) -> tuple[bool, int, int]:
        """
        检查请求是否允许
        
        Args:
            client_id: 客户端标识（可以是用户 ID 或 IP）
        
        Returns:
            (是否允许, 剩余请求数, 重置时间秒数)
        """
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        if self.redis:
            return await self._check_with_redis(client_id, current_time, window_start)
        else:
            return self._check_with_memory(client_id, current_time, window_start)
    
    async def _check_with_redis(
        self, 
        client_id: str, 
        current_time: float,
        window_start: float
    ) -> tuple[bool, int, int]:
        """使用 Redis 检查"""
        try:
            key = self._get_redis_key(client_id)
            
            # 移除过期的请求记录
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # 获取当前窗口内的请求数
            request_count = await self.redis.zcard(key)
            
            if request_count >= self.max_requests:
                # 获取最早的请求时间，计算重置时间
                oldest = await self.redis.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1] + self.window_seconds - current_time)
                else:
                    reset_time = self.window_seconds
                return False, 0, reset_time
            
            # 添加当前请求
            await self.redis.zadd(key, {str(current_time): current_time})
            await self.redis.expire(key, self.window_seconds)
            
            remaining = self.max_requests - request_count - 1
            return True, remaining, self.window_seconds
            
        except Exception as e:
            logger.error(f"Redis 限流检查失败: {e}")
            # Redis 失败时允许请求通过
            return True, self.max_requests, self.window_seconds
    
    def _check_with_memory(
        self, 
        client_id: str, 
        current_time: float,
        window_start: float
    ) -> tuple[bool, int, int]:
        """使用内存检查"""
        if client_id not in self._memory_store:
            self._memory_store[client_id] = []
        
        # 移除过期记录
        self._memory_store[client_id] = [
            ts for ts in self._memory_store[client_id] 
            if ts > window_start
        ]
        
        request_count = len(self._memory_store[client_id])
        
        if request_count >= self.max_requests:
            oldest = min(self._memory_store[client_id]) if self._memory_store[client_id] else current_time
            reset_time = int(oldest + self.window_seconds - current_time)
            return False, 0, reset_time
        
        # 添加当前请求
        self._memory_store[client_id].append(current_time)
        
        remaining = self.max_requests - request_count - 1
        return True, remaining, self.window_seconds
    
    async def reset(self, client_id: str) -> None:
        """重置客户端的限流计数"""
        if self.redis:
            key = self._get_redis_key(client_id)
            await self.redis.delete(key)
        else:
            self._memory_store.pop(client_id, None)


# 全局限流器实例
_rate_limiter: Optional[AIRateLimiter] = None


def get_rate_limiter() -> AIRateLimiter:
    """获取限流器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        # 尝试获取 Redis 客户端
        redis_client = None
        try:
            from app.database import get_redis
            redis_client = get_redis()
        except:
            pass
        
        _rate_limiter = AIRateLimiter(
            max_requests=settings.ai_rate_limit_requests,
            window_seconds=3600,  # 1 小时
            redis_client=redis_client
        )
    return _rate_limiter


async def ai_rate_limit_middleware(request: Request, call_next: Callable):
    """
    AI 请求限流中间件
    
    仅对 /api/v1/ai/* 路径生效
    """
    # 只对 AI 相关路径限流
    if not request.url.path.startswith("/api/v1/ai"):
        return await call_next(request)
    
    # 获取客户端标识
    # 优先使用用户 ID，其次使用 IP
    client_id = None
    
    # 尝试从认证信息获取用户 ID
    if hasattr(request.state, "user") and request.state.user:
        client_id = f"user:{request.state.user.get('id', '')}"
    
    # 使用 IP 作为备选
    if not client_id:
        client_ip = request.client.host if request.client else "unknown"
        client_id = f"ip:{client_ip}"
    
    # 检查限流
    limiter = get_rate_limiter()
    allowed, remaining, reset_time = await limiter.is_allowed(client_id)
    
    if not allowed:
        logger.warning(f"AI 请求被限流: {client_id}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "success": False,
                "error": "请求过于频繁，请稍后再试",
                "detail": f"已达到每小时 {settings.ai_rate_limit_requests} 次请求限制",
                "reset_after_seconds": reset_time
            },
            headers={
                "X-RateLimit-Limit": str(settings.ai_rate_limit_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(reset_time)
            }
        )
    
    # 添加限流信息到响应头
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(settings.ai_rate_limit_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset_time)
    
    return response
