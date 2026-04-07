"""
AI 服务共享工具
"""

import json
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理 Decimal 类型"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def safe_json_dumps(data, **kwargs) -> str:
    """安全的 JSON 序列化，自动处理 Decimal"""
    kwargs.setdefault('ensure_ascii', False)
    return json.dumps(data, cls=DecimalEncoder, **kwargs)


def safe_jsonify(data):
    """将数据转换为 JSON 兼容格式（处理 Decimal 等特殊类型）"""
    return json.loads(safe_json_dumps(data))
