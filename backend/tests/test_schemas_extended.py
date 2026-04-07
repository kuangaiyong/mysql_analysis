"""
Alert Schema 补充测试
"""

import pytest
from decimal import Decimal
from app.schemas.alert import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertHistoryCreate,
    AlertStatus,
)


class TestAlertRuleCreate:
    """告警规则创建Schema测试"""

    def test_minimal_alert_rule(self):
        """测试最小告警规则"""
        alert_rule = AlertRuleCreate(
            connection_id=1,
            rule_name="Test Alert",
            metric_name="cpu_usage",
            condition_operator=">",
            threshold_value=Decimal("80.0"),
            severity="warning",
        )

        assert alert_rule.connection_id == 1
        assert alert_rule.rule_name == "Test Alert"
        assert alert_rule.is_enabled is True

    def test_alert_rule_with_notification_channels(self):
        """测试带通知渠道的告警规则"""
        alert_rule = AlertRuleCreate(
            connection_id=1,
            rule_name="Test Alert",
            metric_name="cpu_usage",
            condition_operator=">",
            threshold_value=Decimal("80.0"),
            severity="critical",
            time_window=60,
            notification_channels={"email": ["test@example.com"], "slack": "#alerts"},
        )

        assert alert_rule.notification_channels is not None
        assert "email" in alert_rule.notification_channels

    def test_alert_rule_all_severities(self):
        """测试所有严重性级别"""
        severities = ["low", "warning", "critical"]

        for severity in severities:
            alert_rule = AlertRuleCreate(
                connection_id=1,
                rule_name=f"Test {severity}",
                metric_name="cpu_usage",
                condition_operator=">",
                threshold_value=Decimal("80.0"),
                severity=severity,
            )

            assert alert_rule.severity == severity

    def test_alert_rule_all_operators(self):
        """测试所有操作符"""
        operators = [">", ">=", "<", "<=", "="]

        for operator in operators:
            alert_rule = AlertRuleCreate(
                connection_id=1,
                rule_name=f"Test {operator}",
                metric_name="cpu_usage",
                condition_operator=operator,
                threshold_value=Decimal("80.0"),
                severity="warning",
            )

            assert alert_rule.condition_operator == operator


class TestAlertRuleUpdate:
    """告警规则更新Schema测试"""

    def test_update_threshold(self):
        """测试更新阈值"""
        update = AlertRuleUpdate(threshold_value=Decimal("90.0"))

        assert update.threshold_value == Decimal("90.0")

    def test_update_status(self):
        """测试更新状态"""
        update = AlertRuleUpdate(is_enabled=False)

        assert update.is_enabled is False

    def test_update_all_fields(self):
        """测试更新所有字段"""
        update = AlertRuleUpdate(
            rule_name="Updated Alert",
            threshold_value=Decimal("95.0"),
            time_window=120,
            severity="critical",
            is_enabled=True,
            notification_channels={"email": ["updated@example.com"]},
        )

        assert update.rule_name == "Updated Alert"
        assert update.time_window == 120


class TestAlertHistoryCreate:
    """告警历史创建Schema测试"""

    def test_minimal_alert_history(self):
        """测试最小告警历史"""
        alert_history = AlertHistoryCreate(
            alert_rule_id=1,
            connection_id=1,
            metric_value=Decimal("85.5"),
            message="Alert triggered",
        )

        assert alert_history.status == "active"

    def test_alert_history_with_all_fields(self):
        """测试完整告警历史"""
        from datetime import datetime

        alert_history = AlertHistoryCreate(
            alert_rule_id=1,
            connection_id=1,
            alert_time=datetime(2025, 1, 23, 10, 0, 0),
            metric_value=92.3,
            message="CPU exceeded threshold",
            status=AlertStatus.RESOLVED,
            resolved_at=datetime(2025, 1, 23, 10, 5, 0),
        )

        assert alert_history.metric_value == 92.3
        assert alert_history.resolved_at is not None

    def test_all_status_values(self):
        """测试所有状态值"""
        statuses = ["active", "resolved", "ignored"]

        for status in statuses:
            alert_history = AlertHistoryCreate(
                alert_rule_id=1,
                connection_id=1,
                metric_value=Decimal("85.0"),
                message="Test",
                status=status,
            )

            assert alert_history.status == status
