"""
测试数据工厂（不使用 factory_boy）
使用简单函数生成测试数据
"""

from datetime import datetime, timedelta
from decimal import Decimal

from app.models.connection import Connection
from app.models.alert import AlertRule, AlertHistory
from app.models.slow_query import SlowQuery
from app.models.metric import PerformanceMetric
from app.models.report import Report, ReportType, ReportStatus


_counter = 0


def get_next_id() -> int:
    """获取下一个 ID"""
    global _counter
    _counter += 1
    return _counter


def create_test_connection(**kwargs) -> Connection:
    """创建测试连接"""
    defaults = {
        "name": f"Test Connection {get_next_id()}",
        "host": "127.0.0.1",
        "port": 3306,
        "username": "test_user",
        "password_encrypted": "encrypted_password",
        "database_name": "test_db",
        "connection_pool_size": 10,
        "is_active": True,
    }
    defaults.update(kwargs)
    return Connection(**defaults)


def create_test_alert_rule(**kwargs) -> AlertRule:
    """创建测试告警规则"""
    defaults = {
        "connection_id": 1,
        "rule_name": f"Alert Rule {get_next_id()}",
        "metric_name": "cpu_usage",
        "condition_operator": ">",
        "threshold_value": Decimal("80.00"),
        "time_window": 60,
        "severity": "warning",
        "is_enabled": True,
        "notification_channels": {"email": ["test@example.com"]},
    }
    defaults.update(kwargs)
    return AlertRule(**defaults)


def create_test_alert_history(**kwargs) -> AlertHistory:
    """创建测试告警历史"""
    defaults = {
        "alert_rule_id": 1,
        "connection_id": 1,
        "alert_time": datetime.now(timezone.utc),
        "metric_value": Decimal("85.50"),
        "message": "High CPU usage detected",
        "status": "active",
        "resolved_at": None,
    }
    defaults.update(kwargs)
    return AlertHistory(**defaults)


def create_test_slow_query(**kwargs) -> SlowQuery:
    """创建测试慢查询"""
    defaults = {
        "connection_id": 1,
        "query_hash": f"query_hash_{get_next_id()}",
        "sql_digest": "SELECT * FROM users WHERE id = ?",
        "full_sql": "SELECT * FROM users WHERE id = 12345",
        "query_time": Decimal("1.500000"),
        "lock_time": Decimal("0.000100"),
        "rows_examined": 1000,
        "rows_sent": 100,
        "database_name": "test_db",
        "timestamp": datetime.now(timezone.utc),
        "execution_count": 1,
    }
    defaults.update(kwargs)
    return SlowQuery(**defaults)


def create_test_performance_metric(**kwargs) -> PerformanceMetric:
    """创建测试性能指标"""
    defaults = {
        "connection_id": 1,
        "metric_name": "qps",
        "metric_value": Decimal("100.50"),
        "collected_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return PerformanceMetric(**defaults)


def create_test_report(**kwargs) -> Report:
    """创建测试报告"""
    defaults = {
        "connection_id": 1,
        "report_type": ReportType.DAILY,
        "report_name": f"Daily Report {get_next_id()}",
        "description": "Daily performance analysis",
        "start_time": datetime.now(timezone.utc) - timedelta(days=1),
        "end_time": datetime.now(timezone.utc),
        "status": ReportStatus.COMPLETED,
        "file_path": "/reports/daily_001.pdf",
        "file_size": 1024000,
        "generated_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return Report(**defaults)


ConnectionFactory = create_test_connection
AlertRuleFactory = create_test_alert_rule
AlertHistoryFactory = create_test_alert_history
SlowQueryFactory = create_test_slow_query
PerformanceMetricFactory = create_test_performance_metric
ReportFactory = create_test_report


aliases = {
    "ConnectionFactory": create_test_connection,
    "AlertRuleFactory": create_test_alert_rule,
    "AlertHistoryFactory": create_test_alert_history,
    "SlowQueryFactory": create_test_slow_query,
    "PerformanceMetricFactory": create_test_performance_metric,
    "ReportFactory": create_test_report,
}
