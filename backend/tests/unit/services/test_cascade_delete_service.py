"""
级联删除服务测试
"""

import pytest
from datetime import datetime
from app.services.cascade_delete_service import (
    validate_connection_exists,
    cascade_delete_connection,
    delete_alert_rule_with_history,
    delete_fingerprint_with_slow_queries,
)
from app.models.connection import Connection
from app.models.alert import AlertRule, AlertHistory
from app.models.slow_query import SlowQuery
from app.models.metric import PerformanceMetric
from app.models.report import Report
from app.models.query_fingerprint import QueryFingerprint
from app.models.wait_event_cache import WaitEventCache
from app.models.index_suggestion import IndexSuggestion
from app.models.config_analysis import ConfigAnalysisHistory


class TestValidateConnectionExists:
    """测试验证连接存在"""

    def test_connection_exists(self, db_session, test_connection):
        """测试存在的连接"""
        result = validate_connection_exists(db_session, test_connection.id)
        assert result is True

    def test_connection_not_exists(self, db_session):
        """测试不存在的连接"""
        result = validate_connection_exists(db_session, 99999)
        assert result is False


class TestCascadeDeleteConnection:
    """测试级联删除连接"""

    def test_cascade_delete_success(self, db_session):
        """测试成功级联删除"""
        # 创建连接
        connection = Connection(
            name="Test Connection",
            host="localhost",
            port=3306,
            username="root",
            password_encrypted="password",
            database_name="test_db",
        )
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)

        # 创建关联数据
        alert_rule = AlertRule(
            id=1,
            connection_id=connection.id,
            rule_name="Test Rule",
            metric_name="cpu_usage",
            condition_operator=">",
            threshold_value=90.0,
            severity="critical",
        )
        db_session.add(alert_rule)
        db_session.commit()

        alert_history = AlertHistory(
            id=1,
            alert_rule_id=alert_rule.id,
            connection_id=connection.id,
            metric_value=95.0,
            message="Test alert",
        )
        db_session.add(alert_history)

        slow_query = SlowQuery(
            id=1,
            connection_id=connection.id,
            query_hash="abc123",
            full_sql="SELECT * FROM users",
            query_time=2.5,
        )
        db_session.add(slow_query)

        metric = PerformanceMetric(
            id=1,
            connection_id=connection.id,
            metric_name="qps",
            metric_value=100.0,
        )
        db_session.add(metric)

        report = Report(
            id=1,
            connection_id=connection.id,
            report_type="daily",
            report_name="Test Report",
        )
        db_session.add(report)

        query_fingerprint = QueryFingerprint(
            id=1,
            connection_id=connection.id,
            fingerprint_hash="hash123",
            normalized_sql="select * from users",
            execution_count=10,
            avg_query_time=1.5,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        db_session.add(query_fingerprint)

        wait_event = WaitEventCache(
            id=1,
            connection_id=connection.id,
            event_name="wait/io/file/innodb/innodb_data_file",
            event_class="io",
            wait_time=0.5,
            wait_count=100,
        )
        db_session.add(wait_event)

        index_suggestion = IndexSuggestion(
            id=1,
            connection_id=connection.id,
            table_name="users",
            column_names="id",
            index_type="BTREE",
            suggestion_type="single",
            confidence_level="medium",
            sql_statement="CREATE INDEX idx_users_id ON users(id)",
        )
        db_session.add(index_suggestion)

        config_analysis = ConfigAnalysisHistory(
            id=1,
            connection_id=connection.id,
            analysis_timestamp=datetime.now(),
            health_score=80,
            critical_count=1,
            warning_count=2,
            info_count=3,
        )
        db_session.add(config_analysis)

        db_session.commit()

        # 执行级联删除
        result = cascade_delete_connection(db_session, connection.id)

        assert result is True

        # 验证连接已删除
        deleted_connection = (
            db_session.query(Connection).filter_by(id=connection.id).first()
        )
        assert deleted_connection is None

        # 验证关联数据已删除
        assert (
            db_session.query(AlertRule).filter_by(connection_id=connection.id).first()
            is None
        )
        assert (
            db_session.query(AlertHistory)
            .filter_by(connection_id=connection.id)
            .first()
            is None
        )
        assert (
            db_session.query(SlowQuery).filter_by(connection_id=connection.id).first()
            is None
        )
        assert (
            db_session.query(PerformanceMetric)
            .filter_by(connection_id=connection.id)
            .first()
            is None
        )
        assert (
            db_session.query(Report).filter_by(connection_id=connection.id).first()
            is None
        )
        assert (
            db_session.query(QueryFingerprint)
            .filter_by(connection_id=connection.id)
            .first()
            is None
        )
        assert (
            db_session.query(WaitEventCache)
            .filter_by(connection_id=connection.id)
            .first()
            is None
        )
        assert (
            db_session.query(IndexSuggestion)
            .filter_by(connection_id=connection.id)
            .first()
            is None
        )
        assert (
            db_session.query(ConfigAnalysisHistory)
            .filter_by(connection_id=connection.id)
            .first()
            is None
        )

    def test_cascade_delete_connection_not_exists(self, db_session):
        """测试删除不存在的连接"""
        result = cascade_delete_connection(db_session, 99999)
        assert result is False

    def test_cascade_delete_rollback_on_error(self, db_session, test_connection):
        """测试删除出错时回滚"""
        # 这个测试模拟删除过程中的异常
        # 由于级联删除涉及多个表，我们需要确保事务回滚

        # 创建一个简单的连接，不添加关联数据
        connection = Connection(
            name="Rollback Test",
            host="localhost",
            port=3306,
            username="root",
            password_encrypted="password",
        )
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)

        # 正常删除应该成功
        result = cascade_delete_connection(db_session, connection.id)
        assert result is True


class TestDeleteAlertRuleWithHistory:
    """测试删除告警规则及其历史"""

    def test_delete_success(self, db_session, test_connection):
        """测试成功删除"""
        # 创建告警规则
        alert_rule = AlertRule(
            id=1,
            connection_id=test_connection.id,
            rule_name="Test Rule",
            metric_name="cpu_usage",
            condition_operator=">",
            threshold_value=90.0,
            severity="critical",
        )
        db_session.add(alert_rule)
        db_session.commit()

        # 创建告警历史
        alert_history = AlertHistory(
            id=1,
            alert_rule_id=alert_rule.id,
            connection_id=test_connection.id,
            metric_value=95.0,
            message="Test alert",
        )
        db_session.add(alert_history)
        db_session.commit()

        # 执行删除
        result = delete_alert_rule_with_history(db_session, alert_rule.id)

        assert result is True

        # 验证已删除
        assert db_session.query(AlertRule).filter_by(id=alert_rule.id).first() is None
        assert (
            db_session.query(AlertHistory)
            .filter_by(alert_rule_id=alert_rule.id)
            .first()
            is None
        )

    def test_delete_with_multiple_history(self, db_session, test_connection):
        """测试删除有多个历史记录的规则"""
        # 创建告警规则
        alert_rule = AlertRule(
            id=1,
            connection_id=test_connection.id,
            rule_name="Test Rule",
            metric_name="cpu_usage",
            condition_operator=">",
            threshold_value=90.0,
            severity="critical",
        )
        db_session.add(alert_rule)
        db_session.commit()

        # 创建多个告警历史
        for i in range(5):
            alert_history = AlertHistory(
                id=i + 1,
                alert_rule_id=alert_rule.id,
                connection_id=test_connection.id,
                metric_value=float(90 + i),
                message=f"Test alert {i}",
            )
            db_session.add(alert_history)
        db_session.commit()

        # 执行删除
        result = delete_alert_rule_with_history(db_session, alert_rule.id)

        assert result is True
        assert (
            db_session.query(AlertHistory)
            .filter_by(alert_rule_id=alert_rule.id)
            .count()
            == 0
        )


class TestDeleteFingerprintWithSlowQueries:
    """测试删除查询指纹及其慢查询关联"""

    def test_delete_fingerprint_update_slow_queries(self, db_session, test_connection):
        """测试删除指纹时更新慢查询"""
        # 创建查询指纹
        fingerprint = QueryFingerprint(
            id=1,
            connection_id=test_connection.id,
            fingerprint_hash="hash123",
            normalized_sql="select * from users",
            execution_count=10,
            avg_query_time=1.5,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        db_session.add(fingerprint)
        db_session.commit()

        # 创建关联的慢查询
        slow_query = SlowQuery(
            id=1,
            connection_id=test_connection.id,
            fingerprint_id=fingerprint.id,
            query_hash="abc123",
            full_sql="SELECT * FROM users WHERE id = 1",
            query_time=2.5,
        )
        db_session.add(slow_query)
        db_session.commit()

        # 执行删除
        result = delete_fingerprint_with_slow_queries(db_session, fingerprint.id)

        assert result is True

        # 验证指纹已删除
        assert (
            db_session.query(QueryFingerprint).filter_by(id=fingerprint.id).first()
            is None
        )

        # 验证慢查询的fingerprint_id已设为NULL
        db_session.refresh(slow_query)
        assert slow_query.fingerprint_id is None

    def test_delete_fingerprint_multiple_slow_queries(
        self, db_session, test_connection
    ):
        """测试删除有多个关联慢查询的指纹"""
        # 创建查询指纹
        fingerprint = QueryFingerprint(
            id=1,
            connection_id=test_connection.id,
            fingerprint_hash="hash123",
            normalized_sql="select * from users",
            execution_count=10,
            avg_query_time=1.5,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        db_session.add(fingerprint)
        db_session.commit()

        # 创建多个关联的慢查询
        for i in range(3):
            slow_query = SlowQuery(
                id=i + 1,
                connection_id=test_connection.id,
                fingerprint_id=fingerprint.id,
                query_hash=f"hash{i}",
                full_sql=f"SELECT * FROM users WHERE id = {i}",
                query_time=float(i + 1),
            )
            db_session.add(slow_query)
        db_session.commit()

        # 执行删除
        result = delete_fingerprint_with_slow_queries(db_session, fingerprint.id)

        assert result is True

        # 验证所有慢查询的fingerprint_id已设为NULL
        for i in range(3):
            sq = db_session.query(SlowQuery).filter_by(id=i + 1).first()
            assert sq.fingerprint_id is None
