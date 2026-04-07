"""
单元测试：Decimal 序列化和 AI 服务
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime, date
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.middleware.json_serialization import UniversalEncoder, safe_serialize
from app.core.detailed_logging import log_error_with_context
import logging


class TestDecimalSerialization:
    """测试 Decimal 序列化"""
    
    def test_decimal_to_float(self):
        """测试 Decimal 转换为 float"""
        data = {"value": Decimal("123.45")}
        result = safe_serialize(data)
        
        assert result["value"] == 123.45
        assert isinstance(result["value"], float)
    
    def test_nested_decimal(self):
        """测试嵌套的 Decimal"""
        data = {
            "level1": {
                "level2": {
                    "value": Decimal("999.99")
                }
            }
        }
        result = safe_serialize(data)
        
        assert result["level1"]["level2"]["value"] == 999.99
        assert isinstance(result["level1"]["level2"]["value"], float)
    
    def test_list_of_decimals(self):
        """测试 Decimal 列表"""
        data = {
            "values": [Decimal("1.1"), Decimal("2.2"), Decimal("3.3")]
        }
        result = safe_serialize(data)
        
        assert result["values"] == [1.1, 2.2, 3.3]
        assert all(isinstance(v, float) for v in result["values"])
    
    def test_datetime_serialization(self):
        """测试 datetime 序列化"""
        now = datetime.now()
        data = {"timestamp": now}
        result = safe_serialize(data)
        
        assert isinstance(result["timestamp"], str)
        assert "T" in result["timestamp"]  # ISO 格式
    
    def test_date_serialization(self):
        """测试 date 序列化"""
        today = date.today()
        data = {"date": today}
        result = safe_serialize(data)
        
        assert isinstance(result["date"], str)
        assert "-" in result["date"]  # YYYY-MM-DD
    
    def test_mixed_types(self):
        """测试混合类型"""
        data = {
            "decimal": Decimal("123.45"),
            "datetime": datetime.now(),
            "date": date.today(),
            "string": "hello",
            "int": 123,
            "float": 45.67,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "bytes": b"test",
            "set": {1, 2, 3}
        }
        
        # 应该不抛出异常
        result = safe_serialize(data)
        
        assert isinstance(result["decimal"], float)
        assert isinstance(result["datetime"], str)
        assert isinstance(result["date"], str)
        assert isinstance(result["bytes"], str)
        assert isinstance(result["set"], list)


class TestDetailedLogging:
    """测试详细日志功能"""
    
    def test_log_error_with_context(self, caplog):
        """测试带上下文的错误日志"""
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.ERROR)
        
        try:
            # 故意制造错误
            result = 1 / 0
        except Exception as e:
            context = {
                "operation": "division",
                "operands": [1, 0]
            }
            
            with caplog.at_level(logging.ERROR):
                log_error_with_context(
                    logger,
                    "计算错误",
                    e,
                    context
                )
        
        # 验证日志包含必要信息
        assert len(caplog.records) > 0
        assert any("计算错误" in record.message for record in caplog.records)


class TestAIDiagnosticService:
    """测试 AI 诊断服务（Mock）"""
    
    @pytest.mark.asyncio
    async def test_diagnose_with_decimals(self):
        """测试诊断服务处理 Decimal 数据"""
        from app.services.ai.ai_diagnostic_service import AIDiagnosticService
        
        # Mock 数据（包含 Decimal）
        mock_context = {
            "performance_metrics": {
                "buffer_pool_size": Decimal("134217728"),
                "buffer_pool_hit_rate": Decimal("97.35"),
                "innodb_io_wait": Decimal("389.38"),
            },
            "slow_queries": [
                {
                    "query_time": Decimal("10.5"),
                    "rows_examined": Decimal("1000000"),
                }
            ]
        }
        
        # 测试序列化
        result = safe_serialize(mock_context)
        
        # 验证所有 Decimal 都被转换
        assert isinstance(result["performance_metrics"]["buffer_pool_size"], float)
        assert isinstance(result["performance_metrics"]["buffer_pool_hit_rate"], float)
        assert isinstance(result["slow_queries"][0]["query_time"], float)
    
    @pytest.mark.asyncio
    async def test_response_serialization(self):
        """测试响应序列化"""
        # 模拟服务返回的数据
        service_response = {
            "success": True,
            "answer": "诊断结果...",
            "context_summary": {
                "connection_id": 10,
                "database": "mysql_demo",
                "metrics": {
                    "value": Decimal("123.45")  # 故意添加 Decimal
                }
            },
            "provider": "zhipu"
        }
        
        # 测试序列化
        result = safe_serialize(service_response)
        
        # 验证可以序列化为 JSON
        json_str = json.dumps(result)
        assert len(json_str) > 0
        
        # 验证可以反序列化
        parsed = json.loads(json_str)
        assert parsed["success"] is True
        assert isinstance(parsed["context_summary"]["metrics"]["value"], float)


class TestMySQLConnector:
    """测试 MySQL 连接器的 Decimal 转换"""
    
    def test_convert_decimals(self):
        """测试 Decimal 转换函数"""
        from app.services.mysql_connector import _convert_decimals
        
        # 测试简单 Decimal
        assert _convert_decimals(Decimal("123.45")) == 123.45
        
        # 测试嵌套结构
        data = {
            "metrics": {
                "value": Decimal("999.99"),
                "nested": {
                    "another": Decimal("111.11")
                }
            },
            "list": [Decimal("1.1"), Decimal("2.2")]
        }
        
        result = _convert_decimals(data)
        
        assert result["metrics"]["value"] == 999.99
        assert isinstance(result["metrics"]["value"], float)
        assert result["metrics"]["nested"]["another"] == 111.11
        assert result["list"] == [1.1, 2.2]


# 运行测试的命令
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
