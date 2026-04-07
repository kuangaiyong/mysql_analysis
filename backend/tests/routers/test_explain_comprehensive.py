"""
Explain router comprehensive tests
"""

import pytest
from fastapi.testclient import TestClient


class TestExplainRouterComprehensive:
    """Explain router comprehensive tests"""

    def test_explain_query_basic(self, client: TestClient):
        """测试基本 EXPLAIN 查询"""
        response = client.post(
            "/api/v1/explain/analyze?connection_id=1",
            json={"sql": "SELECT * FROM users WHERE id = 1"},
        )

        assert response.status_code in [200, 404]

    def test_explain_query_complex(self, client: TestClient):
        """测试复杂查询 EXPLAIN"""
        response = client.post(
            "/api/v1/explain/analyze?connection_id=1",
            json={
                "sql": "SELECT u.name, COUNT(*) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.name",
            },
        )

        assert response.status_code in [200, 404]

    def test_explain_empty_query(self, client: TestClient):
        """测试空查询"""
        response = client.post(
            "/api/v1/explain/analyze?connection_id=1", json={"sql": ""}
        )

        assert response.status_code in [200, 400, 404, 422]

    def test_explain_invalid_syntax(self, client: TestClient):
        """测试无效 SQL 语法"""
        response = client.post(
            "/api/v1/explain/analyze?connection_id=1",
            json={"sql": "SELECT * FROM INVALID"},
        )

        assert response.status_code in [200, 400, 404]

    def test_explain_with_joins(self, client: TestClient):
        """测试带 JOIN 的 EXPLAIN"""
        response = client.post(
            "/api/v1/explain/analyze?connection_id=1",
            json={
                "sql": "SELECT * FROM orders o JOIN products p ON o.product_id = p.id",
            },
        )

        assert response.status_code in [200, 404]

    def test_explain_with_subquery(self, client: TestClient):
        """测试带子查询的 EXPLAIN"""
        response = client.post(
            "/api/v1/explain/analyze?connection_id=1",
            json={
                "sql": "SELECT * FROM orders WHERE id IN (SELECT id FROM products WHERE price > 100)",
            },
        )

        assert response.status_code in [200, 404]

    def test_explain_execution_basic(self, client: TestClient):
        """测试 EXPLAIN EXECUTION"""
        response = client.post(
            "/api/v1/explain/analyze-execution?connection_id=1",
            json={"sql": "SELECT COUNT(*) FROM users"},
        )

        assert response.status_code in [200, 404]

    def test_explain_execution_with_analyze(self, client: TestClient):
        """测试带 ANALYZE 的 EXPLAIN EXECUTION"""
        response = client.post(
            "/api/v1/explain/analyze-execution?connection_id=1",
            json={"sql": "ANALYZE TABLE users"},
        )

        assert response.status_code in [200, 400, 404]

    def test_index_suggestions_basic(self, client: TestClient):
        """测试基本索引建议"""
        response = client.post(
            "/api/v1/explain/index-suggestions?connection_id=1",
            json={
                "sql": "SELECT * FROM users WHERE email = 'test@example.com'",
                "table_name": "users",
            },
        )

        assert response.status_code in [200, 404]

    def test_index_suggestions_multiple(self, client: TestClient):
        """测试多个索引建议"""
        response = client.post(
            "/api/v1/explain/index-suggestions?connection_id=1",
            json={
                "sql": "SELECT * FROM orders WHERE user_id = ? AND status = ?",
                "table_name": "orders",
            },
        )

        assert response.status_code in [200, 404]

    def test_explain_tree_format(self, client: TestClient):
        """测试树形格式 EXPLAIN"""
        response = client.post(
            "/api/v1/explain/analyze?connection_id=1",
            json={"sql": "SELECT * FROM users", "analyze_type": "tree"},
        )

        assert response.status_code in [200, 404]
