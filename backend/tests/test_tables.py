"""
表结构分析测试
测试表结构、DDL、大小、外键等API端点
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime


def test_get_table_structure(client: TestClient, test_connection):
    """测试获取表结构"""
    with patch("app.routers.table.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.get_table_structure.return_value = {
                "table_name": "users",
                "columns": [
                    {
                        "column_name": "id",
                        "data_type": "int",
                        "is_nullable": False,
                        "column_default": None,
                        "column_key": "PRI",
                        "extra": "auto_increment",
                    },
                    {
                        "column_name": "username",
                        "data_type": "varchar",
                        "is_nullable": False,
                        "column_default": None,
                        "column_key": "",
                        "extra": "",
                    },
                ],
                "indexes": [
                    {
                        "index_name": "PRIMARY",
                        "column_name": "id",
                        "index_type": "BTREE",
                        "unique": True,
                        "primary": True,
                    },
                ],
                "foreign_keys": [],
                "engine": "InnoDB",
                "charset": "utf8mb4",
                "collation": "utf8mb4_unicode_ci",
                "comment": "",
                "table_info": {
                    "table_name": "users",
                    "engine": "InnoDB",
                    "charset": "utf8mb4",
                },
                "create_sql": "CREATE TABLE users (id INT PRIMARY KEY, username VARCHAR(255))",
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/table/connections/{test_connection.id}/tables/users/structure"
            )

    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "table_info" in data
    assert "create_sql" in data
    assert isinstance(data["columns"], list)


def test_get_table_structure_connection_not_found(client: TestClient):
    """测试获取表结构 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/users/structure")
    assert response.status_code == 404


def test_get_table_structure_exception(client: TestClient, test_connection):
    """测试获取表结构 - 服务异常"""
    with patch("app.routers.table.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.get_table_structure.side_effect = Exception(
                "数据库错误"
            )
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/table/connections/{test_connection.id}/tables/users/structure"
            )

    assert response.status_code == 500


def test_get_table_ddl(client: TestClient, test_connection):
    """测试获取表DDL"""
    with patch("app.routers.table.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.get_table_structure.return_value = {
                "create_sql": "CREATE TABLE users (\n  id INT PRIMARY KEY,\n  username VARCHAR(255) NOT NULL\n) ENGINE=InnoDB"
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/table/connections/{test_connection.id}/tables/users/ddl"
            )

    assert response.status_code == 200
    assert "CREATE TABLE" in response.text


def test_get_table_ddl_connection_not_found(client: TestClient):
    """测试获取DDL - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/users/ddl")
    assert response.status_code == 404


def test_analyze_table_size(client: TestClient, test_connection):
    """测试分析表大小"""
    with patch("app.routers.table.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_table_size.return_value = {
                "table_name": "users",
                "engine": "InnoDB",
                "data_mb": 8.0,
                "index_mb": 2.5,
                "total_mb": 10.5,
                "data_free": 0,
                "index_ratio": 23.8,
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/table/connections/{test_connection.id}/tables/users/size"
            )

    assert response.status_code == 200
    data = response.json()
    assert "total_mb" in data
    assert "data_mb" in data
    assert "index_mb" in data


def test_analyze_table_size_connection_not_found(client: TestClient):
    """测试分析表大小 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/users/size")
    assert response.status_code == 404


def test_get_foreign_keys(client: TestClient, test_connection):
    """测试获取外键关系"""
    with patch("app.routers.table.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_foreign_keys.return_value = [
                {
                    "constraint_name": "fk_user_id",
                    "column_name": "user_id",
                    "referenced_table": "users",
                    "referenced_column": "id",
                }
            ]
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/table/connections/{test_connection.id}/tables/orders/foreign-keys"
            )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_foreign_keys_connection_not_found(client: TestClient):
    """测试获取外键 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/orders/foreign-keys")
    assert response.status_code == 404


def test_get_table_stats(client: TestClient, test_connection):
    """测试获取表统计信息"""
    with patch("app.routers.table.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        mock_conn_instance.execute_query.return_value = [
            {
                "TABLE_ROWS": 10000,
                "AVG_ROW_LENGTH": 800,
                "DATA_LENGTH": 8000000,
                "INDEX_LENGTH": 2000000,
                "DATA_FREE": 0,
                "AUTO_INCREMENT": 10001,
                "CREATE_TIME": datetime.now(),
                "UPDATE_TIME": datetime.now(),
                "MAX_DATA_LENGTH": 0,
                "MAX_INDEX_LENGTH": 0,
            }
        ]

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/users/stats"
        )

    assert response.status_code == 200
    data = response.json()
    assert "table_name" in data
    assert "row_count" in data
    assert "data_length" in data
    assert "index_length" in data


def test_get_table_stats_not_found(client: TestClient, test_connection):
    """测试获取表统计 - 表不存在"""
    with patch("app.routers.table.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        mock_conn_instance.execute_query.return_value = []

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/nonexistent/stats"
        )

    assert response.status_code == 404


def test_get_table_stats_connection_not_found(client: TestClient):
    """测试获取表统计 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/users/stats")
    assert response.status_code == 404


def test_list_tables(client: TestClient, test_connection):
    """测试获取数据库表列表"""
    with patch("app.routers.table.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_database_tables.return_value = [
                {
                    "table_name": "users",
                    "table_type": "BASE TABLE",
                    "engine": "InnoDB",
                    "row_count": 10000,
                },
                {
                    "table_name": "orders",
                    "table_type": "BASE TABLE",
                    "engine": "InnoDB",
                    "row_count": 50000,
                },
            ]
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/table/connections/{test_connection.id}/databases/test_db/tables"
            )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_tables_connection_not_found(client: TestClient):
    """测试获取表列表 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/databases/test_db/tables")
    assert response.status_code == 404


@pytest.mark.parametrize("table_name", ["users", "products", "orders", "customers"])
def test_get_structure_various_tables(client: TestClient, test_connection, table_name):
    """测试获取不同表的结构"""
    with patch("app.routers.table.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.get_table_structure.return_value = {
                "table_name": table_name,
                "columns": [],
                "indexes": [],
                "foreign_keys": [],
                "engine": "InnoDB",
                "charset": "utf8mb4",
                "collation": "utf8mb4_unicode_ci",
                "comment": "",
                "table_info": {},
                "create_sql": "",
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/table/connections/{test_connection.id}/tables/{table_name}/structure"
            )

    assert response.status_code == 200
