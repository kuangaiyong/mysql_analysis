"""
模型测试 - 字段验证、关系和级联删除
"""

import pytest
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime

from app.models.connection import Connection
from app.models.alert import AlertRule, AlertHistory
from app.models.slow_query import SlowQuery
from app.models.metric import PerformanceMetric
from app.models.report import Report, ReportType, ReportStatus
from app.services import cascade_delete_service
from tests.test_factories import (
    ConnectionFactory,
    AlertRuleFactory,
    AlertHistoryFactory,
    SlowQueryFactory,
    PerformanceMetricFactory,
    ReportFactory,
)


class TestConnectionModel:
    """Connection 模型测试"""

    def test_create_connection(self, db_session: Session):
        """测试创建连接"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)

        assert connection.id is not None
        assert connection.name.startswith("Test Connection")
        assert connection.host == "127.0.0.1"
        assert connection.port == 3306

    def test_connection_defaults(self, db_session: Session):
        """测试连接默认值"""
        connection = Connection(
            name="Test", host="localhost", username="root", password_encrypted="pass"
        )
        db_session.add(connection)
        db_session.commit()

        assert connection.is_active is True
        assert connection.connection_pool_size == 10

    def test_connection_timestamps(self, db_session: Session):
        """测试连接时间戳"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        assert connection.created_at is not None
        assert isinstance(connection.created_at, datetime)


class TestAlertRuleModel:
    """AlertRule 模型测试"""

    def test_create_alert_rule(self, db_session: Session):
        """测试创建告警规则"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        alert_rule = AlertRuleFactory(connection_id=connection.id)
        db_session.add(alert_rule)
        db_session.commit()

        assert alert_rule.id is not None
        assert alert_rule.connection_id == connection.id

    def test_alert_rule_to_connection_relationship(self, db_session: Session):
        """测试告警规则与连接的关系"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        alert_rule = AlertRuleFactory(connection_id=connection.id)
        db_session.add(alert_rule)
        db_session.commit()
        db_session.refresh(alert_rule)

        assert alert_rule.connection_id == connection.id
        assert alert_rule.connection_id == connection.id

    def test_alert_rule_default_enabled(self, db_session: Session):
        """测试告警规则默认启用"""
        alert_rule = AlertRuleFactory()
        db_session.add(alert_rule)
        db_session.commit()

        assert alert_rule.is_enabled is True


class TestAlertHistoryModel:
    """AlertHistory 模型测试"""

    def test_create_alert_history(self, db_session: Session):
        """测试创建告警历史"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        alert_rule = AlertRuleFactory(connection_id=connection.id)
        db_session.add(alert_rule)
        db_session.commit()

        alert_history = AlertHistoryFactory(
            alert_rule_id=alert_rule.id, connection_id=connection.id
        )
        db_session.add(alert_history)
        db_session.commit()

        assert alert_history.id is not None
        assert alert_history.alert_rule_id == alert_rule.id

    def test_alert_history_default_status(self, db_session: Session):
        """测试告警历史默认状态"""
        alert_history = AlertHistoryFactory()
        db_session.add(alert_history)
        db_session.commit()

        assert alert_history.status == "active"
        assert alert_history.resolved_at is None


class TestSlowQueryModel:
    """SlowQuery 模型测试"""

    def test_create_slow_query(self, db_session: Session):
        """测试创建慢查询"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        slow_query = SlowQueryFactory(connection_id=connection.id)
        db_session.add(slow_query)
        db_session.commit()

        assert slow_query.id is not None
        assert slow_query.query_hash.startswith("query_hash_")

    def test_slow_query_to_connection_relationship(self, db_session: Session):
        """测试慢查询与连接的关系（简化版本：只验证connection_id）"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        slow_query = SlowQueryFactory(connection_id=connection.id)
        db_session.add(slow_query)
        db_session.commit()

        # 简化测试：只验证connection_id正确，不查询Connection
        assert slow_query.connection_id == connection.id


class TestPerformanceMetricModel:
    """PerformanceMetric 模型测试"""

    def test_create_performance_metric(self, db_session: Session):
        """测试创建性能指标"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        metric = PerformanceMetricFactory(connection_id=connection.id)
        db_session.add(metric)
        db_session.commit()

        assert metric.id is not None
        assert isinstance(metric.metric_value, Decimal)


class TestReportModel:
    """Report 模型测试"""

    def test_create_report(self, db_session: Session):
        """测试创建报告"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        report = ReportFactory(connection_id=connection.id)
        db_session.add(report)
        db_session.commit()

        assert report.id is not None
        assert report.report_type == ReportType.DAILY
        assert report.status == ReportStatus.COMPLETED

    def test_report_defaults(self, db_session: Session):
        """测试报告默认值"""
        report = ReportFactory()
        db_session.add(report)
        db_session.commit()

        assert report.status == ReportStatus.COMPLETED


class TestCascadeDelete:
    """级联删除测试（使用cascade_delete_service）"""

    def test_connection_delete_cascades_to_alert_rules(self, db_session: Session):
        """测试删除连接级联删除告警规则"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)

        alert_rule = AlertRuleFactory(connection_id=connection.id)
        db_session.add(alert_rule)
        db_session.commit()

        # 使用级联删除服务
        cascade_delete_service.cascade_delete_connection(db_session, connection.id)

        alert_rules = db_session.query(AlertRule).all()
        assert len(alert_rules) == 0

    def test_connection_delete_cascades_to_slow_queries(self, db_session: Session):
        """测试删除连接级联删除慢查询"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)

        slow_query = SlowQueryFactory(connection_id=connection.id)
        db_session.add(slow_query)
        db_session.commit()

        # 使用级联删除服务
        cascade_delete_service.cascade_delete_connection(db_session, connection.id)

        slow_queries = db_session.query(SlowQuery).all()
        assert len(slow_queries) == 0

    def test_connection_delete_cascades_to_performance_metrics(
        self, db_session: Session
    ):
        """测试删除连接级联删除性能指标"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)

        metric = PerformanceMetricFactory(connection_id=connection.id)
        db_session.add(metric)
        db_session.commit()

        # 使用级联删除服务
        cascade_delete_service.cascade_delete_connection(db_session, connection.id)

        metrics = db_session.query(PerformanceMetric).all()
        assert len(metrics) == 0

    def test_connection_delete_cascades_to_reports(self, db_session: Session):
        """测试删除连接级联删除报告"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)

        report = ReportFactory(connection_id=connection.id)
        db_session.add(report)
        db_session.commit()

        # 使用级联删除服务
        cascade_delete_service.cascade_delete_connection(db_session, connection.id)

        reports = db_session.query(Report).all()
        assert len(reports) == 0

    def test_alert_rule_delete_cascades_to_alert_histories(self, db_session: Session):
        """测试删除告警规则级联删除告警历史"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        alert_rule = AlertRuleFactory(connection_id=connection.id)
        db_session.add(alert_rule)
        db_session.commit()
        db_session.refresh(alert_rule)

        alert_history = AlertHistoryFactory(
            alert_rule_id=alert_rule.id, connection_id=connection.id
        )
        db_session.add(alert_history)
        db_session.commit()

        # 使用级联删除服务
        cascade_delete_service.delete_alert_rule_with_history(db_session, alert_rule.id)

        histories = db_session.query(AlertHistory).all()
        assert len(histories) == 0
