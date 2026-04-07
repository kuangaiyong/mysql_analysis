"""
Alert schema tests - Match actual schema
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestAlertSchema:
    """Alert schema tests"""

    def test_alert_rule_create_all_fields(self):
        """Test alert rule create with all fields"""
        from app.schemas.alert import AlertRuleCreate

        alert = AlertRuleCreate(
            connection_id=1,
            rule_name="Critical CPU Alert",
            metric_name="cpu_usage",
            condition_operator=">",
            threshold_value=95.0,
            time_window=120,
            severity="critical",
            notification_channels={"email": ["admin@example.com"], "slack": "#alerts"},
        )

        assert alert.connection_id == 1
        assert alert.severity == "critical"
        assert alert.time_window == 120

    def test_alert_rule_minimal(self):
        """Test alert rule create minimal"""
        from app.schemas.alert import AlertRuleCreate

        alert = AlertRuleCreate(
            connection_id=1,
            rule_name="Simple Alert",
            metric_name="memory_usage",
            condition_operator=">",
            threshold_value=50.0,
            time_window=60,
            severity="warning",
            notification_channels=None,
        )

        assert alert.metric_name == "memory_usage"

    def test_alert_rule_all_operators(self):
        """Test alert rule all operators"""
        from app.schemas.alert import AlertRuleCreate

        operators = [">", ">=", "<", "<=", "="]
        for op in operators:
            alert = AlertRuleCreate(
                connection_id=1,
                rule_name=f"Alert {op}",
                metric_name="cpu",
                condition_operator=op,
                threshold_value=80.0,
                time_window=60,
                severity="info",
                notification_channels=None,
            )
            assert alert.condition_operator == op

    def test_alert_rule_validation_min_length(self):
        """Test alert rule name min length validation"""
        from app.schemas.alert import AlertRuleCreate

        with pytest.raises(ValidationError):
            AlertRuleCreate(
                connection_id=1,
                rule_name="",  # Empty name
                metric_name="cpu",
                condition_operator=">",
                threshold_value=80.0,
                time_window=60,
                severity="warning",
            )

    def test_alert_rule_validation_max_length(self):
        """Test alert rule name max length validation"""
        from app.schemas.alert import AlertRuleCreate

        with pytest.raises(ValidationError):
            AlertRuleCreate(
                connection_id=1,
                rule_name="a" * 101,  # Too long
                metric_name="cpu",
                condition_operator=">",
                threshold_value=80.0,
                time_window=60,
                severity="warning",
            )

    def test_alert_rule_response(self):
        """Test alert rule response model"""
        from app.schemas.alert import AlertRuleResponse

        alert = AlertRuleResponse(
            id=1,
            connection_id=1,
            rule_name="Test Alert",
            metric_name="cpu_usage",
            condition_operator=">",
            threshold_value=90.0,
            time_window=120,
            severity="critical",
            notification_channels={"email": ["admin@example.com"]},
            is_enabled=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert alert.id == 1
        assert alert.is_enabled is True
        assert alert.created_at is not None

    def test_alert_rule_update_all_fields(self):
        """Test alert rule update with all fields"""
        from app.schemas.alert import AlertRuleUpdate

        update = AlertRuleUpdate(
            rule_name="Updated Rule",
            metric_name="memory_usage",
            condition_operator="<",
            threshold_value=90.0,
            time_window=300,
            severity="critical",
            is_enabled=False,
            notification_channels={"email": ["updated@example.com"]},
        )

        assert update.rule_name == "Updated Rule"
        assert update.severity == "critical"
        assert update.is_enabled is False

    def test_alert_rule_update_partial(self):
        """Test alert rule update partial"""
        from app.schemas.alert import AlertRuleUpdate

        update = AlertRuleUpdate(rule_name="Partial Update", threshold_value=85.0)

        assert update.rule_name == "Partial Update"

    def test_alert_rule_update_none_values(self):
        """Test alert rule update with None values"""
        from app.schemas.alert import AlertRuleUpdate

        update = AlertRuleUpdate(threshold_value=None, is_enabled=None)

        assert update.threshold_value is None
        assert update.is_enabled is None

    def test_alert_rule_update_all_optional(self):
        """Test alert rule update with all None"""
        from app.schemas.alert import AlertRuleUpdate

        update = AlertRuleUpdate()
        assert update.rule_name is None
        assert update.metric_name is None

    def test_alert_history_response_basic(self):
        """Test alert history response basic"""
        from app.schemas.alert import AlertHistoryResponse

        history = AlertHistoryResponse(
            id=1,
            alert_rule_id=1,
            connection_id=1,
            alert_time=datetime.now(),
            metric_value=95.5,
            message="CPU usage exceeded threshold",
            status="active",
        )

        assert history.id == 1
        assert history.metric_value == 95.5
        assert history.status == "active"

    def test_alert_history_response_with_resolved(self):
        """Test alert history with resolved time"""
        from app.schemas.alert import AlertHistoryResponse

        now = datetime.now()
        history = AlertHistoryResponse(
            id=1,
            alert_rule_id=1,
            connection_id=1,
            alert_time=now,
            metric_value=95.5,
            message="Alert triggered",
            status="resolved",
            resolved_at=datetime.now(),
        )

        assert history.status == "resolved"
        assert history.resolved_at is not None

    def test_alert_history_all_fields(self):
        """Test alert history with all fields"""
        from app.schemas.alert import AlertHistoryResponse

        history = AlertHistoryResponse(
            id=1,
            alert_rule_id=1,
            connection_id=1,
            alert_time=datetime.now(),
            metric_value=90.0,
            message="Threshold exceeded",
            status="active",
            resolved_at=None,
        )

        assert history.alert_rule_id == 1
        assert history.connection_id == 1
        assert history.resolved_at is None

    def test_notification_channels_dict(self):
        """Test notification channels as dict"""
        from app.schemas.alert import AlertRuleCreate

        channels = {
            "email": ["admin@example.com", "ops@example.com"],
            "slack": "#alerts",
            "webhook": "https://example.com/webhook",
        }

        alert = AlertRuleCreate(
            connection_id=1,
            rule_name="Multi-channel Alert",
            metric_name="cpu",
            condition_operator=">",
            threshold_value=80.0,
            time_window=60,
            severity="warning",
            notification_channels=channels,
        )

        assert len(alert.notification_channels["email"]) == 2
        assert alert.notification_channels["slack"] == "#alerts"

    def test_notification_channels_none(self):
        """Test notification channels can be None in Update"""
        from app.schemas.alert import AlertRuleUpdate

        update = AlertRuleUpdate(notification_channels=None)

        assert update.notification_channels is None

    def test_threshold_value_float(self):
        """Test threshold value as float"""
        from app.schemas.alert import AlertRuleCreate

        alert = AlertRuleCreate(
            connection_id=1,
            rule_name="Float Threshold",
            metric_name="cpu",
            condition_operator=">",
            threshold_value=85.75,
            time_window=60,
            severity="warning",
        )

        assert alert.threshold_value == 85.75

    def test_time_window_int(self):
        """Test time window as integer"""
        from app.schemas.alert import AlertRuleCreate

        alert = AlertRuleCreate(
            connection_id=1,
            rule_name="Time Window",
            metric_name="cpu",
            condition_operator=">",
            threshold_value=80.0,
            time_window=300,
            severity="warning",
        )

        assert alert.time_window == 300

    def test_severity_levels(self):
        """Test different severity levels"""
        from app.schemas.alert import AlertRuleCreate

        severities = ["critical", "warning", "info", "low"]
        for sev in severities:
            alert = AlertRuleCreate(
                connection_id=1,
                rule_name=f"Severity {sev}",
                metric_name="cpu",
                condition_operator=">",
                threshold_value=80.0,
                time_window=60,
                severity=sev,
            )
            assert alert.severity == sev

    def test_metric_name_values(self):
        """Test various metric names"""
        from app.schemas.alert import AlertRuleCreate

        metrics = ["cpu_usage", "memory_usage", "disk_usage", "qps", "connections"]
        for metric in metrics:
            alert = AlertRuleCreate(
                connection_id=1,
                rule_name=f"Metric {metric}",
                metric_name=metric,
                condition_operator=">",
                threshold_value=80.0,
                time_window=60,
                severity="warning",
            )
            assert alert.metric_name == metric

    def test_from_attributes(self):
        """Test from_attributes config for response models"""
        from app.schemas.alert import AlertRuleResponse, AlertHistoryResponse

        # Test that these models support from_attributes
        assert AlertRuleResponse.model_config.get("from_attributes", False) is True
        assert AlertHistoryResponse.model_config.get("from_attributes", False) is True

    def test_model_serialization(self):
        """Test model serialization to dict"""
        from app.schemas.alert import AlertRuleCreate

        alert = AlertRuleCreate(
            connection_id=1,
            rule_name="Serialization Test",
            metric_name="cpu",
            condition_operator=">",
            threshold_value=80.0,
            time_window=60,
            severity="warning",
        )

        alert_dict = alert.model_dump()
        assert alert_dict["connection_id"] == 1
        assert alert_dict["rule_name"] == "Serialization Test"

    def test_model_json_serialization(self):
        """Test model JSON serialization"""
        from app.schemas.alert import AlertRuleCreate
        import json

        alert = AlertRuleCreate(
            connection_id=1,
            rule_name="JSON Test",
            metric_name="cpu",
            condition_operator=">",
            threshold_value=80.0,
            time_window=60,
            severity="warning",
        )

        json_str = alert.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["rule_name"] == "JSON Test"

    def test_multiple_updates(self):
        """Test multiple field updates"""
        from app.schemas.alert import AlertRuleUpdate

        update = AlertRuleUpdate(
            rule_name="Updated",
            metric_name="new_metric",
            condition_operator="<=",
            threshold_value=75.0,
            time_window=180,
            severity="info",
            is_enabled=True,
        )

        assert update.rule_name == "Updated"
        assert update.metric_name == "new_metric"
        assert update.is_enabled is True

    def test_empty_notification_channels(self):
        """Test empty notification channels dict"""
        from app.schemas.alert import AlertRuleCreate

        alert = AlertRuleCreate(
            connection_id=1,
            rule_name="Empty Channels",
            metric_name="cpu",
            condition_operator=">",
            threshold_value=80.0,
            time_window=60,
            severity="warning",
            notification_channels={},
        )

        assert alert.notification_channels == {}

    def test_field_descriptions(self):
        """Test field descriptions exist"""
        from app.schemas.alert import AlertRuleCreate

        # Access field descriptions through model_fields
        fields = AlertRuleCreate.model_fields
        assert "rule_name" in fields
        assert "metric_name" in fields
        assert "condition_operator" in fields

    def test_connection_id_required(self):
        """Test connection_id is required"""
        from app.schemas.alert import AlertRuleCreate

        with pytest.raises(ValidationError):
            AlertRuleCreate(
                # Missing connection_id
                rule_name="Test",
                metric_name="cpu",
                condition_operator=">",
                threshold_value=80.0,
                time_window=60,
                severity="warning",
            )

    def test_required_fields_validation(self):
        """Test required fields validation"""
        from app.schemas.alert import AlertRuleCreate
        from pydantic import ValidationError

        # Required fields (no defaults)
        required_fields = [
            "connection_id",
            "rule_name",
            "metric_name",
            "threshold_value",
        ]

        # Test missing each required field
        for field in required_fields:
            data = {
                "connection_id": 1,
                "rule_name": "Test",
                "metric_name": "cpu",
                "condition_operator": ">",
                "threshold_value": 80.0,
                "severity": "warning",
            }
            del data[field]

            with pytest.raises(ValidationError):
                AlertRuleCreate(**data)

    def test_alert_response_datetime_fields(self):
        """Test datetime fields in response"""
        from app.schemas.alert import AlertRuleResponse
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        response = AlertRuleResponse(
            id=1,
            connection_id=1,
            rule_name="Test",
            metric_name="cpu",
            condition_operator=">",
            threshold_value=80.0,
            time_window=60,
            severity="warning",
            is_enabled=True,
            created_at=now,
            updated_at=now,
        )

        assert response.created_at == now
        assert response.updated_at == now
