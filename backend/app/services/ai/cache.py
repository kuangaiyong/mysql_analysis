"""
AI 响应缓存服务

缓存 AI 诊断结果以减少 API 调用
"""

import json
import hashlib
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from app.config import settings
from app.services.ai.utils import DecimalEncoder

logger = logging.getLogger(__name__)


class AIResponseCache:
    """
    AI 响应缓存
    
    缓存相似问题的回答，减少 API 调用
    """
    
    def __init__(
        self,
        ttl_seconds: int = 3600,
        max_cache_size: int = 1000,
        redis_client: Optional[object] = None
    ):
        """
        初始化缓存
        
        Args:
            ttl_seconds: 缓存过期时间（秒）
            max_cache_size: 最大缓存条目数（内存模式）
            redis_client: Redis 客户端（可选）
        """
        self.ttl_seconds = ttl_seconds
        self.max_cache_size = max_cache_size
        self.redis = redis_client
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
    
    def _generate_cache_key(
        self,
        connection_id: int,
        question: str,
        context_hash: Optional[str] = None
    ) -> str:
        """
        生成缓存键
        
        Args:
            connection_id: 连接 ID
            question: 用户问题
            context_hash: 上下文哈希（可选）
        
        Returns:
            缓存键
        """
        # 标准化问题（去除多余空格、转小写）
        normalized_question = " ".join(question.lower().split())
        
        # 生成哈希
        content = f"{connection_id}:{normalized_question}"
        if context_hash:
            content += f":{context_hash}"
        
        return f"ai_cache:{hashlib.md5(content.encode()).hexdigest()}"
    
    def _get_context_hash(self, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        生成上下文哈希
        
        基于关键指标生成哈希，确保相同状态返回相同结果
        """
        if not context:
            return None
        
        # 只取关键指标
        key_metrics = {
            "bottleneck_type": context.get("wait_events", {}).get("bottleneck_type"),
            "config_issues_count": len(context.get("config_issues", [])),
            "slow_queries_count": len(context.get("slow_queries", [])),
        }
        
        return hashlib.md5(json.dumps(key_metrics, sort_keys=True, cls=DecimalEncoder).encode()).hexdigest()[:8]
    
    async def get(
        self,
        connection_id: int,
        question: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的响应
        
        Args:
            connection_id: 连接 ID
            question: 用户问题
            context: 上下文（用于生成上下文哈希）
        
        Returns:
            缓存的响应，如果不存在则返回 None
        """
        context_hash = self._get_context_hash(context)
        cache_key = self._generate_cache_key(connection_id, question, context_hash)
        
        if self.redis:
            return self._get_from_redis(cache_key)
        else:
            return self._get_from_memory(cache_key)
    
    async def set(
        self,
        connection_id: int,
        question: str,
        response: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> None:
        """
        设置缓存
        
        Args:
            connection_id: 连接 ID
            question: 用户问题
            response: AI 响应
            context: 上下文
            ttl: 过期时间（秒），默认使用实例配置
        """
        context_hash = self._get_context_hash(context)
        cache_key = self._generate_cache_key(connection_id, question, context_hash)
        
        cache_data = {
            "response": response,
            "cached_at": datetime.now().isoformat(),
            "question": question[:100],  # 保存前 100 字符用于调试
            "connection_id": connection_id,
        }
        
        if self.redis:
            self._set_to_redis(cache_key, cache_data, ttl or self.ttl_seconds)
        else:
            self._set_to_memory(cache_key, cache_data, ttl or self.ttl_seconds)
    
    def _get_from_redis(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从 Redis 获取缓存"""
        try:
            data = self.redis.get(cache_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis 缓存读取失败: {e}")
            return None
    
    def _set_to_redis(self, cache_key: str, data: Dict[str, Any], ttl: int) -> None:
        """设置 Redis 缓存"""
        try:
            self.redis.setex(cache_key, ttl, json.dumps(data, ensure_ascii=False, cls=DecimalEncoder))
        except Exception as e:
            logger.error(f"Redis 缓存写入失败: {e}")
    
    def _get_from_memory(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从内存获取缓存"""
        if cache_key not in self._memory_cache:
            return None
        
        cache_entry = self._memory_cache[cache_key]
        
        # 检查是否过期
        if time.time() > cache_entry.get("expires_at", 0):
            del self._memory_cache[cache_key]
            return None
        
        return cache_entry.get("data")
    
    def _set_to_memory(self, cache_key: str, data: Dict[str, Any], ttl: int) -> None:
        """设置内存缓存"""
        # 清理过期缓存
        self._cleanup_expired()
        
        # 检查缓存大小
        if len(self._memory_cache) >= self.max_cache_size:
            # 移除最旧的缓存
            oldest_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k].get("expires_at", 0)
            )
            del self._memory_cache[oldest_key]
        
        self._memory_cache[cache_key] = {
            "data": data,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
    
    def _cleanup_expired(self) -> None:
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if v.get("expires_at", 0) < current_time
        ]
        for key in expired_keys:
            del self._memory_cache[key]
    
    async def clear(self, connection_id: Optional[int] = None) -> None:
        """
        清除缓存
        
        Args:
            connection_id: 连接 ID（可选，不指定则清除所有）
        """
        if self.redis:
            if connection_id:
                # 清除特定连接的缓存
                pattern = f"ai_cache:*"
                # Redis SCAN 删除匹配的键
                cursor = 0
                while True:
                    cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        self.redis.delete(*keys)
                    if cursor == 0:
                        break
            else:
                # 清除所有 AI 缓存
                self.redis.flushdb()
        else:
            if connection_id:
                # 清除特定连接的缓存
                keys_to_delete = [
                    k for k in self._memory_cache.keys()
                ]
                for key in keys_to_delete:
                    del self._memory_cache[key]
            else:
                self._memory_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if self.redis:
            return {
                "type": "redis",
                "ttl": self.ttl_seconds,
            }
        else:
            self._cleanup_expired()
            return {
                "type": "memory",
                "size": len(self._memory_cache),
                "max_size": self.max_cache_size,
                "ttl": self.ttl_seconds,
            }
    
    # 同步方法（用于非异步环境）
    def get_sync(
        self,
        connection_id: int,
        question: str
    ) -> Optional[Dict[str, Any]]:
        """同步获取缓存"""
        cache_key = self._generate_cache_key(connection_id, question)
        return self._get_from_memory(cache_key)
    
    def set_sync(
        self,
        connection_id: int,
        question: str,
        response: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """同步设置缓存"""
        cache_key = self._generate_cache_key(connection_id, question)
        cache_data = {
            "response": response,
            "cached_at": datetime.now().isoformat(),
            "question": question[:100],
            "connection_id": connection_id,
        }
        self._set_to_memory(cache_key, cache_data, ttl or self.ttl_seconds)


# 全局缓存实例
_cache_instance: Optional[AIResponseCache] = None


def get_cache() -> AIResponseCache:
    """获取缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        # 尝试获取 Redis 客户端
        redis_client = None
        try:
            from app.database import get_redis
            redis_client = get_redis()
        except:
            pass
        
        _cache_instance = AIResponseCache(
            ttl_seconds=getattr(settings, 'ai_cache_ttl', 1800),  # 默认 30 分钟
            max_cache_size=1000,
            redis_client=redis_client
        )
    return _cache_instance
