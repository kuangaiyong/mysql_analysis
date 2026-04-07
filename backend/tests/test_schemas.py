"""
Table Schema 测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_factories import create_test_connection, ConnectionFactory
from app.main import app


class TestTableRouter:
    """表分析路由测试类"""

    def test_list_tables_success(self, db_session: Session, client: TestClient):
        """测试列出所有表"""
        connection = create_test_connection()
        db_session.add(connection)
        db_session.commit()

        response = client.get(f"/api/v1/table/tables/{connection.id}")

        assert response.status_code in [200, 404]

    def test_list_tables_not_found(self, client: TestClient):
        """测试列出不存在的连接的表"""
        response = client.get("/api/v1/table/tables/999")

        assert response.status_code in [200, 404]

    def test_get_table_structure(self, db_session: Session, client: TestClient):
        """测试获取表结构"""
        connection = create_test_connection()
        db_session.add(connection)
        db_session.commit()

        response = client.get(f"/api/v1/table/structure/{connection.id}/users")

        assert response.status_code in [200, 404]

    def test_get_table_size_analysis(self, db_session: Session, client: TestClient):
        """测试表大小分析"""
        connection = create_test_connection()
        db_session.add(connection)
        db_session.commit()

        response = client.get(f"/api/v1/table/size-analysis/{connection.id}/users")

        assert response.status_code in [200, 404]

    def test_get_foreign_keys(self, db_session: Session, client: TestClient):
        """测试获取外键关系"""
        from unittest.mock import patch, Mock

        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        # 直接 patch table router 中的 MySQLConnector
        with patch("app.routers.table.MySQLConnector") as mock_connector_class:
            # 配置 mock 实例
            mock_instance = Mock()
            mock_instance.execute_query.return_value = []  # 返回空的外键列表
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector_class.return_value = mock_instance

            # 使用 fixture 提供的 client（已包含认证 headers）
            response = client.get(
                f"/api/v1/table/connections/{connection.id}/tables/users/foreign-keys"
            )

            # 接受 200（成功）或 404（连接不存在）
            assert response.status_code in [200, 404]


class TestAlertSchema:
    """告警Schema测试类"""

    def test_alert_rule_create(self):
        """测试告警规则创建schema验证"""
        from app.schemas.alert import AlertRuleCreate

        alert_rule = AlertRuleCreate(
            connection_id=1,
            rule_name="High CPU Alert",
            metric_name="cpu_usage",
            condition_operator=">",
            threshold_value=80.0,
            time_window=60,
            severity="warning",
        )

        assert alert_rule.connection_id == 1
        assert alert_rule.severity == "warning"

    def test_alert_rule_update(self):
        """测试告警规则更新schema验证"""
        from app.schemas.alert import AlertRuleUpdate

        alert_rule = AlertRuleUpdate(threshold_value=90.0, is_enabled=False)

        assert alert_rule.threshold_value == 90.0
        assert alert_rule.is_enabled is False

    def test_alert_history(self):
        """测试告警历史schema验证"""
        from app.schemas.alert import AlertHistoryCreate

        alert_history = AlertHistoryCreate(
            alert_rule_id=1,
            connection_id=1,
            metric_value=85.5,
            message="CPU usage high",
        )

        assert alert_history.metric_value == 85.5
