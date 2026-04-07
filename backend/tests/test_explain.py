"""
EXPLAIN分析测试
测试SQL EXPLAIN分析和索引建议相关API端点
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


def test_explain_query_traditional(client: TestClient, test_connection):
    """测试EXPLAIN分析 - 传统格式"""
    with patch("app.routers.explain.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_query.return_value = {
                "type": "traditional",
                "query": "SELECT * FROM users WHERE id = 1",
                "result": [
                    {
                        "id": 1,
                        "select_type": "SIMPLE",
                        "table": "users",
                        "type": "const",
                        "rows": 1,
                    }
                ],
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/explain/analyze?connection_id={test_connection.id}",
                json={
                    "sql": "SELECT * FROM users WHERE id = 1",
                    "analyze_type": "traditional",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert "type" in data
    assert "query" in data
    assert "result" in data


def test_explain_query_json(client: TestClient, test_connection):
    """测试EXPLAIN分析 - JSON格式"""
    with patch("app.routers.explain.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_query.return_value = {
                "type": "json",
                "query": "SELECT * FROM users",
                "result": {},
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/explain/analyze?connection_id={test_connection.id}",
                json={"sql": "SELECT * FROM users", "analyze_type": "json"},
            )

    assert response.status_code == 200


def test_explain_query_tree(client: TestClient, test_connection):
    """测试EXPLAIN分析 - TREE格式"""
    with patch("app.routers.explain.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_query.return_value = {
                "type": "tree",
                "query": "SELECT * FROM users",
                "result": {},
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/explain/analyze?connection_id={test_connection.id}",
                json={"sql": "SELECT * FROM users", "analyze_type": "tree"},
            )

    assert response.status_code == 200


def test_explain_query_connection_not_found(client: TestClient):
    """测试EXPLAIN分析 - 连接不存在"""
    with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.analyze_query.return_value = {}
        mock_analyzer.return_value = mock_analyzer_instance

        response = client.post(
            "/api/v1/explain/analyze?connection_id=99999",
            json={"sql": "SELECT * FROM users", "analyze_type": "traditional"},
        )

    assert response.status_code == 404


def test_explain_query_exception(client: TestClient, test_connection):
    """测试EXPLAIN分析 - 服务异常"""
    with patch("app.routers.explain.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_query.side_effect = Exception("分析失败")
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/explain/analyze?connection_id={test_connection.id}",
                json={"sql": "SELECT * FROM users", "analyze_type": "traditional"},
            )

    assert response.status_code == 500


def test_explain_analyze_execution(client: TestClient, test_connection):
    """测试EXPLAIN ANALYZE执行"""
    with patch("app.routers.explain.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.explain_analyze.return_value = {
                "execution_plan": [],
                "actual_cost": 100,
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/explain/analyze-execution?connection_id={test_connection.id}",
                json={
                    "sql": "SELECT * FROM users WHERE id = 1",
                    "database_name": "test_db",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert "execution_plan" in data


def test_explain_analyze_execution_connection_not_found(client: TestClient):
    """测试EXPLAIN ANALYZE - 连接不存在"""
    with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.explain_analyze.return_value = {}
        mock_analyzer.return_value = mock_analyzer_instance

        response = client.post(
            "/api/v1/explain/analyze-execution?connection_id=99999",
            json={"sql": "SELECT * FROM users", "database_name": "test_db"},
        )

    assert response.status_code == 404


def test_get_index_suggestions(client: TestClient, test_connection):
    """测试获取索引建议"""
    with patch("app.routers.explain.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.get_index_suggestions.return_value = {
                "existing_indexes": [],
                "table_columns": [],
                "suggestions": ["建议添加索引 idx_username (username) - WHERE条件使用"],
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/explain/index-suggestions?connection_id={test_connection.id}",
                json={
                    "sql": "SELECT * FROM users WHERE username = 'test'",
                    "table_name": "users",
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_get_index_suggestions_connection_not_found(client: TestClient):
    """测试获取索引建议 - 连接不存在"""
    with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.get_index_suggestions.return_value = {"suggestions": []}
        mock_analyzer.return_value = mock_analyzer_instance

        response = client.post(
            "/api/v1/explain/index-suggestions?connection_id=99999",
            json={"sql": "SELECT * FROM users", "table_name": "users"},
        )

    assert response.status_code == 404


def test_explain_with_database_name(client: TestClient, test_connection):
    """测试EXPLAIN分析 - 指定数据库名"""
    with patch("app.routers.explain.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_query.return_value = {
                "type": "traditional",
                "query": "SELECT * FROM products",
                "result": [],
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/explain/analyze?connection_id={test_connection.id}",
                json={
                    "sql": "SELECT * FROM products",
                    "analyze_type": "traditional",
                    "database_name": "production",
                },
            )

    assert response.status_code == 200


@pytest.mark.parametrize("analyze_type", ["traditional", "json", "tree"])
def test_explain_various_types(client: TestClient, test_connection, analyze_type):
    """测试各种EXPLAIN分析类型"""
    with patch("app.routers.explain.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.explain.ExplainAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_query.return_value = {
                "type": analyze_type,
                "query": "SELECT 1",
                "result": [],
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/explain/analyze?connection_id={test_connection.id}",
                json={"sql": "SELECT 1", "analyze_type": analyze_type},
            )

    assert response.status_code == 200
