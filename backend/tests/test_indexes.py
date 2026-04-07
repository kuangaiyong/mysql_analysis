"""
索引管理测试
测试索引的创建、删除和使用分析相关API端点
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


def test_get_table_indexes(client: TestClient, test_connection):
    """测试获取表的索引列表"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.get_table_indexes_with_stats.return_value = [
                {
                    "Key_name": "PRIMARY",
                    "Column_name": "id",
                    "Index_type": "BTREE",
                    "Non_unique": 0,
                    "Cardinality": 100,
                },
                {
                    "Key_name": "idx_username",
                    "Column_name": "username",
                    "Index_type": "BTREE",
                    "Non_unique": 1,
                    "Cardinality": 50,
                },
            ]
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/indexes/{test_connection.id}/tables/users/indexes"
            )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_table_indexes_connection_not_found(client: TestClient):
    """测试获取索引列表 - 连接不存在"""
    response = client.get("/api/v1/indexes/99999/tables/users/indexes")
    assert response.status_code == 404


def test_get_table_indexes_exception(client: TestClient, test_connection):
    """测试获取索引列表 - 服务异常"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.get_table_indexes_with_stats.side_effect = Exception(
                "数据库错误"
            )
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/indexes/{test_connection.id}/tables/users/indexes"
            )

    assert response.status_code == 500


def test_create_index(client: TestClient, test_connection):
    """测试创建索引"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.create_index.return_value = None
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/indexes/{test_connection.id}/indexes",
                json={
                    "table_name": "users",
                    "index_name": "idx_email",
                    "columns": ["email"],
                    "unique": False,
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_create_index_unique(client: TestClient, test_connection):
    """测试创建唯一索引"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.create_index.return_value = None
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/indexes/{test_connection.id}/indexes",
                json={
                    "table_name": "users",
                    "index_name": "idx_username_unique",
                    "columns": ["username"],
                    "unique": True,
                },
            )

    assert response.status_code == 200


def test_create_index_multi_column(client: TestClient, test_connection):
    """测试创建多列索引"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.create_index.return_value = None
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/indexes/{test_connection.id}/indexes",
                json={
                    "table_name": "users",
                    "index_name": "idx_name_email",
                    "columns": ["first_name", "last_name", "email"],
                    "unique": False,
                },
            )

    assert response.status_code == 200


def test_create_index_connection_not_found(client: TestClient):
    """测试创建索引 - 连接不存在"""
    response = client.post(
        "/api/v1/indexes/99999/indexes",
        json={"table_name": "users", "index_name": "idx_test", "columns": ["test"]},
    )
    assert response.status_code == 404


def test_delete_index(client: TestClient, test_connection):
    """测试删除索引"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.drop_index.return_value = None
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.delete(
                f"/api/v1/indexes/{test_connection.id}/indexes/users/idx_test"
            )

    assert response.status_code == 204


def test_delete_primary_index(client: TestClient, test_connection):
    """测试删除PRIMARY索引（应该失败）"""
    response = client.delete(
        f"/api/v1/indexes/{test_connection.id}/indexes/users/PRIMARY"
    )
    assert response.status_code == 400
    assert "不能删除主键索引" in response.json()["detail"]


def test_delete_index_connection_not_found(client: TestClient):
    """测试删除索引 - 连接不存在"""
    response = client.delete("/api/v1/indexes/99999/indexes/users/idx_test")
    assert response.status_code == 404


def test_analyze_index_usage(client: TestClient, test_connection):
    """测试分析索引使用率"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_index_usage.return_value = {
                "index_statistics": [
                    {"index": "idx_username", "table": "users", "selectivity": 85.5}
                ],
                "unused_indexes": [],
                "low_selectivity_indexes": [],
            }
            mock_analyzer_instance.get_index_usage_stats.return_value = []
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/indexes/{test_connection.id}/indexes/analyze"
            )

    assert response.status_code == 200
    data = response.json()
    assert "total_indexes" in data
    assert "unused_indexes" in data
    assert "analyzed_at" in data


def test_analyze_index_usage_connection_not_found(client: TestClient):
    """测试分析索引使用率 - 连接不存在"""
    response = client.post("/api/v1/indexes/99999/indexes/analyze")
    assert response.status_code == 404


def test_detect_redundant_indexes(client: TestClient, test_connection):
    """测试检测冗余索引"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance._find_duplicate_indexes.return_value = [
                {
                    "table": "users",
                    "columns": "username, email, phone",
                    "reason": "存在前导列相同的索引",
                }
            ]
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/indexes/{test_connection.id}/indexes/redundant"
            )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_detect_redundant_indexes_connection_not_found(client: TestClient):
    """测试检测冗余索引 - 连接不存在"""
    response = client.post("/api/v1/indexes/99999/indexes/redundant")
    assert response.status_code == 404


def test_create_index_exception(client: TestClient, test_connection):
    """测试创建索引 - 服务异常"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.create_index.side_effect = Exception("索引已存在")
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/indexes/{test_connection.id}/indexes",
                json={
                    "table_name": "users",
                    "index_name": "idx_test",
                    "columns": ["test"],
                },
            )

    assert response.status_code == 500


@pytest.mark.parametrize("table_name", ["users", "products", "orders"])
def test_get_indexes_various_tables(client: TestClient, test_connection, table_name):
    """测试获取不同表的索引"""
    with patch("app.routers.index.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.get_table_indexes_with_stats.return_value = []
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/indexes/{test_connection.id}/tables/{table_name}/indexes"
            )

    assert response.status_code == 200
