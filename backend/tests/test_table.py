"""
表结构分析模块测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


def test_get_table_structure_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取表结构成功"""
    with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.get_table_structure.return_value = {
            "table_name": "users",
            "columns": [
                {
                    "column_name": "id",
                    "data_type": "int",
                    "is_nullable": False,
                    "column_key": "PRI",
                    "column_default": None,
                    "extra": "auto_increment",
                },
                {
                    "column_name": "username",
                    "data_type": "varchar",
                    "is_nullable": False,
                    "column_key": "",
                    "column_default": None,
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
                {
                    "index_name": "idx_username",
                    "column_name": "username",
                    "index_type": "BTREE",
                    "unique": False,
                    "primary": False,
                },
            ],
            "foreign_keys": [],
            "engine": "InnoDB",
            "charset": "utf8mb4",
            "collation": "utf8mb4_unicode_ci",
            "comment": "",
            "create_sql": "CREATE TABLE users (id INT PRIMARY KEY, username VARCHAR(100))",
            "table_info": {},
        }
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/users/structure"
        )

    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "create_sql" in data


def test_get_table_structure_connection_not_found(client: TestClient):
    """测试获取表结构 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/users/structure")
    assert response.status_code == 404


def test_get_table_structure_service_error(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取表结构 - 服务异常"""
    with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.get_table_structure.side_effect = Exception("数据库错误")
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/users/structure"
        )

    assert response.status_code == 500
    assert "获取表结构失败" in response.json()["detail"]


def test_get_table_ddl_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取表DDL成功"""
    with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.get_table_structure.return_value = {
            "table_name": "users",
            "create_sql": "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100))",
        }
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/users/ddl"
        )

    assert response.status_code == 200
    # The endpoint returns the DDL SQL string directly, not a dict
    assert "CREATE TABLE" in response.text


def test_get_table_ddl_connection_not_found(client: TestClient):
    """测试获取表DDL - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/users/ddl")
    assert response.status_code == 404


def test_analyze_table_size_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试分析表大小成功"""
    with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.analyze_table_size.return_value = {
            "table_name": "users",
            "engine": "InnoDB",
            "data_mb": 10.5,
            "index_mb": 2.3,
            "total_mb": 12.8,
            "data_free": 0,
            "index_ratio": 18.0,
        }
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/users/size"
        )

    assert response.status_code == 200
    data = response.json()
    assert "table_name" in data
    assert "data_mb" in data


def test_analyze_table_size_connection_not_found(client: TestClient):
    """测试分析表大小 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/users/size")
    assert response.status_code == 404


def test_analyze_table_size_service_error(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试分析表大小 - 服务异常"""
    with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.analyze_table_size.side_effect = Exception("分析失败")
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/users/size"
        )

    assert response.status_code == 500
    assert "分析表大小失败" in response.json()["detail"]


def test_get_foreign_keys_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取外键关系成功"""
    with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.analyze_foreign_keys.return_value = [
            {
                "constraint_name": "fk_user_role",
                "table_name": "users",
                "column_name": "role_id",
                "referenced_table": "roles",
                "referenced_column": "id",
                "on_delete": "CASCADE",
                "on_update": "CASCADE",
            }
        ]
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/users/foreign-keys"
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_foreign_keys_connection_not_found(client: TestClient):
    """测试获取外键关系 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/users/foreign-keys")
    assert response.status_code == 404


def test_get_table_stats_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取表统计信息成功"""
    with patch("app.routers.table.MySQLConnector") as mock_conn:
        mock_instance = Mock()
        mock_instance.execute_query.return_value = [
            {
                "TABLE_ROWS": 1000,
                "AVG_ROW_LENGTH": 50,
                "DATA_LENGTH": 50000,
                "INDEX_LENGTH": 10000,
                "DATA_FREE": 0,
                "AUTO_INCREMENT": 1001,
                "CREATE_TIME": "2024-01-01 10:00:00",
                "UPDATE_TIME": "2024-01-01 12:00:00",
                "MAX_DATA_LENGTH": 60000,
                "MAX_INDEX_LENGTH": 12000,
            }
        ]

        mock_instance.__enter__ = Mock(return_value=mock_instance)
        mock_instance.__exit__ = Mock(return_value=None)
        mock_conn.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/users/stats"
        )

    assert response.status_code == 200
    data = response.json()
    assert "table_name" in data
    assert "row_count" in data


def test_get_table_stats_connection_not_found(client: TestClient):
    """测试获取表统计信息 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/tables/users/stats")
    assert response.status_code == 404


def test_list_tables_success(client: TestClient, test_connection, mock_mysql_connector):
    """测试获取数据库表列表成功"""
    with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.analyze_database_tables.return_value = [
            {
                "table_name": "users",
                "row_count": 1000,
                "data_size_mb": 10.5,
            },
            {
                "table_name": "roles",
                "row_count": 10,
                "data_size_mb": 0.5,
            },
        ]
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/databases/test_db/tables"
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_tables_connection_not_found(client: TestClient):
    """测试获取数据库表列表 - 连接不存在"""
    response = client.get("/api/v1/table/connections/99999/databases/test_db/tables")
    assert response.status_code == 404


def test_list_tables_service_error(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取数据库表列表 - 服务异常"""
    with patch("app.routers.table.TableStructureAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.analyze_database_tables.side_effect = Exception("获取失败")
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/databases/test_db/tables"
        )

    assert response.status_code == 500
    assert "获取表列表失败" in response.json()["detail"]


def test_get_table_stats_empty_table(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试获取表统计信息 - 表不存在"""
    with patch("app.routers.table.MySQLConnector") as mock_conn:
        mock_instance = Mock()
        mock_instance.execute_query.return_value = []

        mock_instance.__enter__ = Mock(return_value=mock_instance)
        mock_instance.__exit__ = Mock(return_value=None)
        mock_conn.return_value = mock_instance

        response = client.get(
            f"/api/v1/table/connections/{test_connection.id}/tables/users/stats"
        )

    assert response.status_code == 404
    assert "表不存在" in response.json()["detail"]
