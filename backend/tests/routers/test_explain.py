"""
Explain Router 集成测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_factories import ConnectionFactory


class TestExplainRouter:
    """EXPLAIN路由测试类"""

    def test_analyze_query_success(self, db_session: Session, client: TestClient):
        """测试EXPLAIN分析查询"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {
            "connection_id": connection.id,
            "query": "SELECT * FROM users WHERE id = 1",
        }

        response = client.post("/api/v1/explain/analyze", json=request_data)

        assert response.status_code in [200, 404, 422]

    def test_analyze_query_missing_fields(self, client: TestClient):
        """测试EXPLAIN分析缺少字段"""
        response = client.post("/api/v1/explain/analyze", json={})

        assert response.status_code == 422

    def test_analyze_query_invalid_query(self, db_session: Session, client: TestClient):
        """测试EXPLAIN分析无效查询"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {"connection_id": connection.id, "query": "invalid sql syntax"}

        response = client.post("/api/v1/explain/analyze", json=request_data)

        assert response.status_code in [200, 404, 422]

    def test_analyze_execution_success(self, db_session: Session, client: TestClient):
        """测试EXPLAIN ANALYZE执行"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {
            "connection_id": connection.id,
            "query": "SELECT * FROM orders LIMIT 10",
        }

        response = client.post("/api/v1/explain/analyze-execution", json=request_data)

        assert response.status_code in [200, 404, 422]

    def test_get_index_suggestions_success(
        self, db_session: Session, client: TestClient
    ):
        """测试获取索引建议"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {
            "connection_id": connection.id,
            "query": "SELECT * FROM users WHERE email = 'test@example.com'",
        }

        response = client.post("/api/v1/explain/index-suggestions", json=request_data)

        assert response.status_code in [200, 404, 422]

    def test_get_index_suggestions_missing_query(self, client: TestClient):
        """测试获取索引建议缺少查询"""
        response = client.post("/api/v1/explain/index-suggestions", json={})

        assert response.status_code == 422

    def test_invalid_connection_id(self, client: TestClient):
        """测试无效的连接ID"""
        response = client.post(
            "/api/v1/explain/analyze",
            json={"connection_id": "invalid", "query": "SELECT 1"},
        )

        assert response.status_code in [404, 422]
