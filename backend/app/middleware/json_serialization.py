"""
全局 JSON 序列化中间件
自动处理 Decimal 类型和其他非标准 JSON 类型
"""

import json
from decimal import Decimal
from datetime import datetime, date
from typing import Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class UniversalEncoder(json.JSONEncoder):
    """通用 JSON 编码器，处理所有非标准类型"""
    
    def default(self, obj: Any) -> Any:
        # Decimal -> float
        if isinstance(obj, Decimal):
            return float(obj)
        
        # datetime -> ISO 格式字符串
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # date -> ISO 格式字符串
        if isinstance(obj, date):
            return obj.isoformat()
        
        # bytes -> hex 字符串
        if isinstance(obj, bytes):
            return obj.hex()
        
        # set -> list
        if isinstance(obj, set):
            return list(obj)
        
        # 其他类型 -> str
        return str(obj)


def safe_serialize(data: Any) -> Any:
    """
    安全序列化数据，确保所有类型都能被 JSON 序列化
    
    Args:
        data: 任意数据
    
    Returns:
        JSON 兼容的数据
    """
    try:
        json_str = json.dumps(data, cls=UniversalEncoder)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"序列化失败: {e}")
        return {
            "error": "Serialization failed",
            "original_type": type(data).__name__
        }


class JSONSerializationMiddleware(BaseHTTPMiddleware):
    """
    JSON 序列化中间件
    自动处理响应数据中的非标准类型
    """
    
    async def dispatch(self, request: Request, call_next):
        # 调用下一个处理器
        response = await call_next(request)
        
        # 只处理 JSON 响应
        if response.headers.get("content-type") == "application/json":
            # 读取响应体
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                # 解析 JSON
                data = json.loads(body)
                
                # 重新序列化（处理非标准类型）
                safe_data = safe_serialize(data)
                
                # 复制 headers 但移除 Content-Length（让框架重新计算）
                new_headers = dict(response.headers)
                new_headers.pop("content-length", None)
                
                # 返回新的响应
                return Response(
                    content=json.dumps(safe_data),
                    status_code=response.status_code,
                    headers=new_headers,
                    media_type="application/json"
                )
            except Exception as e:
                logger.error(f"中间件序列化失败: {e}")
                # 复制 headers 但移除 Content-Length
                new_headers = dict(response.headers)
                new_headers.pop("content-length", None)
                # 返回原始响应
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=new_headers,
                    media_type="application/json"
                )
        
        return response
