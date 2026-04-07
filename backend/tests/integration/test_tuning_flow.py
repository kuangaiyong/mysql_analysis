"""
调优功能端到端测试

测试SQL改写、InnoDB调优、索引建议的完整流程
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from tests.test_factories import ConnectionFactory


class TestTuningFlow:
    """调优功能端到端测试"""

    def test_sql_rewrite_flow(self, client: TestClient):
        """场景1: SQL改写建议流程"""
        # 1. 发送SQL改写请求
        response = client.post(
            "/api/v1/tuning/sql-rewrite",
            json={
                "sql": "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
            },
        )
        # 2. 验证返回
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        # 3. 验证建议包含JOIN改写
        assert any("JOIN" in str(s) for s in data["suggestions"])

    def test_innodb_tuning_flow(self, db_session, client: TestClient):
        """场景2: InnoDB调优建议流程"""
        # 创建测试连接
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        # Mock MySQLConnector和InnoDBTuner
        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            # Mock SHOW STATUS and SHOW VARIABLES results
            mock_instance.execute_query.side_effect = [
                [
                    {
                        "Variable_name": "Innodb_buffer_pool_read_requests",
                        "Value": "1000",
                    },
                    {
                        "Variable_name": "Innodb_buffer_pool_reads",
                        "Value": "100",
                    },
                ],
                [{"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"}],
            ]
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.InnoDBTuner") as mock_tuner:
                mock_tuner_instance = Mock()
                mock_tuner_instance.analyze_and_recommend.return_value = [
                    {
                        "param": "innodb_buffer_pool_size",
                        "current_value": "134217728",
                        "recommended_value": "268435456",
                        "reason": "Buffer Pool命中率较低",
                        "priority": "high",
                    }
                ]
                mock_tuner_instance._calculate_buffer_pool_hit_rate.return_value = 90.0
                mock_tuner.return_value = mock_tuner_instance

                response = client.get(f"/api/v1/tuning/innodb/{connection.id}")

                assert response.status_code == 200
                data = response.json()
                assert "recommendations" in data

    def test_index_suggestions_flow(self, db_session, client: TestClient):
        """场景3: 索引建议流程"""
        # 创建测试连接
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        with patch("app.routers.tuning.MySQLConnector") as mock_connector:
            mock_instance = Mock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance

            with patch("app.routers.tuning.IndexSuggestionEngine") as mock_engine:
                mock_engine_instance = Mock()
                mock_engine_instance.generate_index_recommendations_with_explain.return_value = [
                    {
                        "table": "users",
                        "columns": ["name"],
                        "index_type": "BTREE",
                        "reason": "WHERE条件列建议创建索引",
                    }
                ]
                mock_engine.return_value = mock_engine_instance

                response = client.post(
                    f"/api/v1/tuning/index-suggestions/{connection.id}",
                    json={"sql": "SELECT * FROM users WHERE name = 'test'"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "recommendations" in data
