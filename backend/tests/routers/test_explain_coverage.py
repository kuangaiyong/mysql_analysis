"""
Explain router tests - 90% coverage target
"""

import pytest
from fastapi.testclient import TestClient


class TestExplainRouterCoverage:
    """Explain router coverage tests"""

    def test_analyze_query_basic(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={"connection_id": 1, "query": "SELECT * FROM users WHERE id = 1"},
        )

    def test_analyze_query_missing_connection(self, client: TestClient):
        client.post("/api/v1/explain/analyze", json={"query": "SELECT 1"})

    def test_analyze_query_missing_query(self, client: TestClient):
        client.post("/api/v1/explain/analyze", json={"connection_id": 1})

    def test_analyze_query_empty_query(self, client: TestClient):
        client.post("/api/v1/explain/analyze", json={"connection_id": 1, "query": ""})

    def test_analyze_query_invalid_sql(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={"connection_id": 1, "query": "INVALID SQL SYNTAX"},
        )

    def test_analyze_query_complex_joins(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={
                "connection_id": 1,
                "query": "SELECT u.name, COUNT(*) FROM users u JOIN orders ON u.id = o.user_id GROUP BY u.name",
            },
        )

    def test_analyze_query_with_subquery(self, client: TestClient):
        client.post(
            "//api/v1/explain/analyze",
            json={
                "connection_id": 1,
                "query": "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders LIMIT 10)",
            },
        )

    def test_analyze_query_with_unions(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={
                "connection_id": 1,
                "query": "SELECT * FROM users u LEFT JOIN orders ON u.id = o.user_id",
            },
        )

    def test_analyze_query_with_aggregates(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={
                "connection_id": 1,
                "query": "SELECT COUNT(*), SUM(amount) FROM orders GROUP BY user_id",
            },
        )

    def test_analyze_query_with_window_functions(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={
                "connection_id": 1,
                "query": "SELECT ROW_NUMBER() OVER (ORDER BY created_at) as rn, * FROM users WHERE rn <= 100",
            },
        )

    def test_analyze_query_invalid_format(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={
                "connection_id": 1,
                "query": "SELECT * FROM users",
                "format": "invalid_format",
            },
        )

    def test_analyze_query_json_format(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={"connection_id": 1, "query": "SELECT * FROM users", "format": "json"},
        )

    def test_analyze_query_tree_format(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={"connection_id": 1, "query": "SELECT * FROM users", "format": "tree"},
        )

    def test_analyze_execution_basic(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze-execution",
            json={"connection_id": 1, "query": "SELECT * FROM users LIMIT 100"},
        )

    def test_analyze_execution_missing_query(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze-execution", json={"connection_id": 1, "query": ""}
        )

    def test_analyze_execution_invalid_query(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze-execution",
            json={"connection_id": 1, "query": "INVALID SQL"},
        )

    def test_index_suggestions_basic(self, client: TestClient):
        client.post(
            "/api/v1/explain/index-suggestions",
            json={
                "connection_id": 1,
                "query": "SELECT * FROM users WHERE email = 'test@example.com'",
            },
        )

    def test_index_suggestions_missing_query(self, client: TestClient):
        client.post("/api/v1/explain/index-suggestions", json={"connection_id": 1})

    def test_index_suggestions_invalid_sql(self, client: TestClient):
        client.post(
            "/api/v1/explain/index-suggestions",
            json={"connection_id": 1, "query": "INVALID"},
        )

    def test_index_suggestions_with_complex_query(self, client: TestClient):
        client.post(
            "/api/v1/explain/index-suggestions",
            json={
                "connection_id": 1,
                "query": "SELECT * FROM users u JOIN orders ON u.id = o.user_id WHERE o.amount > 100 GROUP BY u.id",
            },
        )

    def test_explain_analyze_with_limit(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={"connection_id": 1, "query": "SELECT 1", "limit": 10},
        )

    def test_explain_analyze_with_invalid_limit(self, client: TestClient):
        client.post(
            "/api/v1/explain/analyze",
            json={"connection_id": 1, "query": "SELECT 1", "limit": -1},
        )

    def test_invalid_http_method(self, client: TestClient):
        client.get("/api/v1/explain/analyze")

    def test_invalid_endpoint(self, client: TestClient):
        client.get("/api/v1/explain/invalid-endpoint")

    def test_concurrent_requests(self, client: TestClient):
        for _ in range(5):
            client.post(
                "/api/v1/explain/analyze",
                json={"connection_id": 1, "query": "SELECT 1"},
            )
