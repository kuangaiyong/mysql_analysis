"""
索引管理模块测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


def test_get_table_indexes_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取表索引列表成功"""
    with patch("app.routers.index.MySQLConnector"):
        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_instance = Mock()
            mock_instance.get_table_indexes_with_stats.return_value = [
                {
                    "Key_name": "idx_username",
                    "Column_name": "username",
                    "Index_type": "BTREE",
                    "Non_unique": 0,
                    "Cardinality": 1000,
                    "size_bytes": 16384,
                    "usage_count": 500,
                    "last_used": "2024-01-01",
                }
            ]
            mock_analyzer.return_value = mock_instance

            response = client.get(
                f"/api/v1/indexes/{test_connection.id}/tables/users/indexes"
            )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0



def test_get_table_indexes_connection_not_found(client: TestClient):
    """测试获取表索引列表 - 连接不存在"""
    response = client.get("/api/v1/indexes/99999/tables/users/indexes")
    assert response.status_code == 404


def test_get_table_indexes_empty_result(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取表索引列表 - 空结果"""
    with patch("app.routers.index.MySQLConnector"):
        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_instance = Mock()
            mock_instance.get_table_indexes_with_stats.return_value = []
            mock_analyzer.return_value = mock_instance

            response = client.get(
                f"/api/v1/indexes/{test_connection.id}/tables/users/indexes"
            )

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_create_index_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试创建索引成功"""
    with patch("app.routers.index.MySQLConnector"):
        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance

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


def test_create_index_connection_not_found(client: TestClient):
    """测试创建索引 - 连接不存在"""
    response = client.post(
        "/api/v1/indexes/99999/indexes",
        json={"table_name": "users", "index_name": "idx_email", "columns": ["email"]},
    )
    assert response.status_code == 404


def test_create_index_service_error(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试创建索引 - 服务异常"""
    with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.create_index.side_effect = Exception("数据库错误")
        mock_analyzer.return_value = mock_instance

        response = client.post(
            f"/api/v1/indexes/{test_connection.id}/indexes",
            json={
                "table_name": "users",
                "index_name": "idx_email",
                "columns": ["email"],
            },
        )

    assert response.status_code == 500
    assert "创建索引失败" in response.json()["detail"]


def test_delete_index_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试删除索引成功"""
    with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_analyzer.return_value = mock_instance

        response = client.delete(
            f"/api/v1/indexes/{test_connection.id}/indexes/users/idx_email"
        )

    assert response.status_code == 204


def test_delete_index_connection_not_found(client: TestClient):
    """测试删除索引 - 连接不存在"""
    response = client.delete("/api/v1/indexes/99999/indexes/users/idx_email")
    assert response.status_code == 404


def test_delete_primary_key_index(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试删除主键索引"""
    response = client.delete(
        f"/api/v1/indexes/{test_connection.id}/indexes/users/PRIMARY"
    )
    assert response.status_code == 400
    assert "不能删除主键索引" in response.json()["detail"]


def test_delete_index_service_error(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试删除索引 - 服务异常"""
    with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.drop_index.side_effect = Exception("数据库错误")
        mock_analyzer.return_value = mock_instance

        response = client.delete(
            f"/api/v1/indexes/{test_connection.id}/indexes/users/idx_email"
        )

    assert response.status_code == 500


def test_analyze_index_usage_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试分析索引使用率成功"""
    mock_connector = Mock()
    mock_connector.__enter__ = Mock(return_value=mock_connector)
    mock_connector.__exit__ = Mock(return_value=False)
    
    with patch("app.routers.index.MySQLConnector", return_value=mock_connector):
        with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
            mock_instance = Mock()
            mock_instance.analyze_index_usage.return_value = {
                "index_statistics": [
                    {"index": "idx_email", "table": "users", "selectivity": 90},
                    {"index": "idx_username", "table": "users", "selectivity": 10},
                ],
                "unused_indexes": [],
                "low_selectivity_indexes": [
                    {"index": "idx_username", "table": "users", "selectivity": 10},
                ],
            }
            mock_instance.get_index_usage_stats.return_value = []
            mock_analyzer.return_value = mock_instance

            response = client.post(f"/api/v1/indexes/{test_connection.id}/indexes/analyze")

    assert response.status_code == 200
    data = response.json()
    assert "total_indexes" in data
    assert "unused_indexes" in data






def test_analyze_index_usage_connection_not_found(client: TestClient):
    """测试分析索引使用率 - 连接不存在"""
    response = client.post("/api/v1/indexes/99999/indexes/analyze")
    assert response.status_code == 404


def test_analyze_index_usage_service_error(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试分析索引使用率 - 服务异常"""
    with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.analyze_index_usage.side_effect = Exception("分析失败")
        mock_analyzer.return_value = mock_instance

        response = client.post(f"/api/v1/indexes/{test_connection.id}/indexes/analyze")

    assert response.status_code == 500
    assert "分析索引使用率失败" in response.json()["detail"]


def test_detect_redundant_indexes_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试检测冗余索引成功"""
    with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance._find_duplicate_indexes.return_value = [
            {
                "index_name_1": "idx_email_username",
                "index_name_2": "idx_username_email",
                "table": "users",
                "redundancy_type": "subset",
                "reason": "存在前导列相同的索引",
            }
        ]
        mock_analyzer.return_value = mock_instance

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


def test_detect_redundant_indexes_service_error(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试检测冗余索引 - 服务异常"""
    with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance._find_duplicate_indexes.side_effect = Exception("检测失败")
        mock_analyzer.return_value = mock_instance

        response = client.post(
            f"/api/v1/indexes/{test_connection.id}/indexes/redundant"
        )

    assert response.status_code == 500
    assert "检测冗余索引失败" in response.json()["detail"]


def test_create_index_unique(client: TestClient, test_connection, mock_mysql_connector):
    """测试创建唯一索引"""
    with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_analyzer.return_value = mock_instance

        response = client.post(
            f"/api/v1/indexes/{test_connection.id}/indexes",
            json={
                "table_name": "users",
                "index_name": "idx_unique_email",
                "columns": ["email"],
                "unique": True,
            },
        )

    assert response.status_code == 200


def test_create_index_multi_column(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试创建多列索引"""
    with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_analyzer.return_value = mock_instance

        response = client.post(
            f"/api/v1/indexes/{test_connection.id}/indexes",
            json={
                "table_name": "users",
                "index_name": "idx_name_email",
                "columns": ["name", "email"],
                "unique": False,
            },
        )

    assert response.status_code == 200


def test_get_table_indexes_service_error(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取表索引列表 - 服务异常"""
    with patch("app.routers.index.IndexAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.get_table_indexes.side_effect = Exception("数据库错误")
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/indexes/{test_connection.id}/tables/users/indexes"
        )

    assert response.status_code == 500
    assert "获取索引列表失败" in response.json()["detail"]
