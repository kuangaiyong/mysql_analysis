"""
Schema validation tests
"""

import pytest
from decimal import Decimal
from pydantic import ValidationError


class TestAlertSchemaValidation:
    """Alert schema validation tests"""

    def test_alert_rule_all_severities_valid(self):
        """测试所有有效的严重性级别"""
        from app.schemas.alert import AlertRuleCreate

        severities = ["low", "warning", "critical"]

        for severity in severities:
            alert = AlertRuleCreate(
                connection_id=1,
                rule_name=f"Test {severity}",
                metric_name="cpu_usage",
                condition_operator=">",
                threshold_value=Decimal("80.0"),
                severity=severity,
            )

            assert alert.severity == severity

    def test_all_operators_valid(self):
        """测试所有有效的操作符"""
        from app.schemas.alert import AlertRuleCreate

        operators = [">", ">=", "<", "<=", "="]

        for operator in operators:
            alert = AlertRuleCreate(
                connection_id=1,
                rule_name=f"Test {operator}",
                metric_name="cpu_usage",
                condition_operator=operator,
                threshold_value=Decimal("80.0"),
                severity="warning",
            )

            assert alert.condition_operator == operator

    def test_threshold_values(self):
        """测试阈值边界值"""
        from app.schemas.alert import AlertRuleCreate

        values = [0.0, 50.0, 80.0, 99.9, 100.0]

        for value in values:
            alert = AlertRuleCreate(
                connection_id=1,
                rule_name=f"Test {value}",
                metric_name="cpu_usage",
                condition_operator=">",
                threshold_value=Decimal(str(value)),
                severity="warning",
            )

            assert float(alert.threshold_value) == value

    def test_invalid_severity_raises_error(self):
        """测试无效严重性应该抛出错误"""
        from app.schemas.alert import AlertRuleCreate

        with pytest.raises(ValidationError):
            AlertRuleCreate(
                connection_id=1,
                rule_name="Test",
                metric_name="cpu_usage",
                condition_operator=">",
                threshold_value=Decimal("80.0"),
                severity="invalid_severity",
            )

    def test_negative_threshold(self):
        """测试负阈值（可能有效）"""
        from app.schemas.alert import AlertRuleCreate

        alert = AlertRuleCreate(
            connection_id=1,
            rule_name="Test Negative",
            metric_name="cpu_usage",
            condition_operator=">",
            threshold_value=Decimal("-10.0"),
            severity="warning",
        )

        assert alert.threshold_value == Decimal("-10.0")


class TestConnectionSchemaValidation:
    """Connection schema validation tests"""

    def test_valid_port_range(self):
        """测试有效端口范围"""
        from app.schemas.connection import ConnectionCreate

        ports = [1, 3306, 3307, 9999]

        for port in ports:
            conn = ConnectionCreate(
                name=f"Test Port {port}",
                host="localhost",
                port=port,
                username="test_user",
                password="test_password",
                database_name="test_db",
            )

            assert conn.port == port

    def test_connection_pool_size_range(self):
        """测试连接池大小范围"""
        from app.schemas.connection import ConnectionCreate

        pool_sizes = [1, 10, 50, 100]

        for size in pool_sizes:
            conn = ConnectionCreate(
                name=f"Test Pool {size}",
                host="localhost",
                port=3306,
                username="test_user",
                password="test_password",
                database_name="test_db",
                connection_pool_size=size,
            )

            assert conn.connection_pool_size == size

    def test_is_active_default(self):
        """测试 is_active 默认值"""
        from app.schemas.connection import ConnectionCreate

        conn = ConnectionCreate(
            name="Test",
            host="localhost",
            port=3306,
            username="test_user",
            password="test_password",
            database_name="test_db",
        )

        assert conn.is_active is True
