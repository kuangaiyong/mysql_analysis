"""Redis缓存服务"""

import redis
import json
from typing import Optional, Any
from decimal import Decimal
from app.config import settings
from app.services.ai.utils import DecimalEncoder


class RedisCache:
    """Redis缓存客户端"""

    def __init__(self, host=None, port=None, db=None):
        """初始化Redis连接

        Args:
            host: Redis主机（可选，默认从settings读取）
            port: Redis端口（可选，默认从settings读取）
            db: Redis数据库（可选，默认从settings读取）
        """
        # 如果提供了参数，使用参数；否则从settings读取
        if host is not None:
            self.host = host
            self.port = port if port is not None else 6379
            self.db = db if db is not None else 0
            password = None
        else:
            redis_url = settings.redis_url
            redis_password = settings.redis_password

            # 解析Redis URL：支持多种格式
            # 1. redis://password@host:port/db 格式
            # 2. redis://host:port/db 格式
            # 3. host:port/db 格式 (不带协议)
            if "://" in redis_url:
                # 带 redis:// 协议的格式
                url_without_scheme = redis_url.split("://")[1]
                if "@" in url_without_scheme:
                    # redis://password@host:port/db 格式
                    parts = url_without_scheme.split("@")
                    password = (
                        parts[0] if len(parts) == 2 and len(parts[0]) > 0 else None
                    )
                    host_port_db = parts[1] if len(parts) == 2 else ""
                    host = (
                        host_port_db.split(":")[0]
                        if len(host_port_db) > 0
                        else "localhost"
                    )
                    port = (
                        int(host_port_db.split(":")[1].split("/")[0])
                        if len(host_port_db.split(":")) > 1
                        and len(host_port_db.split(":")[1].split("/")) > 0
                        else 6379
                    )
                    db = int(host_port_db.split("/")[1]) if "/" in host_port_db else 0
                else:
                    # redis://host:port/db 格式
                    parts = url_without_scheme.split(":")
                    host = parts[0]
                    port = int(parts[1].split("/")[0]) if len(parts[1]) > 0 else 6379
                    db = int(parts[1].split("/")[1]) if "/" in parts[1] else 0
                    password = None
            else:
                # 不带协议的 host:port 格式（如 localhost:6379）
                host_port_db = redis_url.split(":")
                host = host_port_db[0]
                port = int(host_port_db[1]) if len(host_port_db) > 0 else 6379
                db = int(host_port_db[1]) if len(host_port_db) > 1 else 0
                password = redis_password if redis_password else None

            self.host = host
            self.port = port
            self.db = db

        self.redis_client = redis.Redis(
            host=self.host,
            port=self.port,
            password=password,  # 使用解析出的密码
            db=self.db,
            decode_responses=False,
        )

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = self.redis_client.get(key)
            if value:
                import json

                try:
                    return json.loads(value)
                except:
                    return value.decode("utf-8") if isinstance(value, bytes) else value
            return None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存"""
        try:
            import json

            if not isinstance(value, (str, bytes)):
                value = json.dumps(value, cls=DecimalEncoder)
            self.redis_client.setex(key, ttl, value)
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            result = self.redis_client.delete(key)
            return result > 0
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.redis_client.exists(key) == 1
        except Exception:
            return False

    def get_metrics_cache_key(self, connection_id: int) -> str:
        """获取性能指标缓存键"""
        return f"metrics:connection:{connection_id}"

    def get_slow_queries_cache_key(self, connection_id: int) -> str:
        """获取慢查询缓存键"""
        return f"slow_queries:connection:{connection_id}"

    def get_cached_metrics(self, connection_id: int):
        """获取缓存的性能指标"""
        key = self.get_metrics_cache_key(connection_id)
        return self.get(key)

    def cache_metrics(self, connection_id: int, metrics: dict, ttl: int = 60) -> bool:
        """缓存性能指标"""
        key = self.get_metrics_cache_key(connection_id)
        return self.set(key, metrics, ttl)

    def invalidate_connection_cache(self, connection_id: int) -> None:
        """清除连接相关的缓存"""
        self.delete(self.get_metrics_cache_key(connection_id))
        self.delete(self.get_slow_queries_cache_key(connection_id))
