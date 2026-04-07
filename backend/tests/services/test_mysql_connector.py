"""
MySQL Connector 服务单元测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pymysql
from app.services.mysql_connector import MySQLConnector


class TestMySQLConnector:
    """MySQL 连接器测试类"""

    def test_init(self):
        """测试初始化"""
        connector = MySQLConnector(
            host="localhost",
            port=3306,
            user="root",
            password="password",
            database="test_db",
        )

        assert connector.host == "localhost"
        assert connector.port == 3306
        assert connector.user == "root"
        assert connector.password == "password"
        assert connector.database == "test_db"
        assert connector.connection is None

    def test_init_defaults(self):
        """测试初始化默认值"""
        connector = MySQLConnector(host="localhost", user="root", password="password")

        assert connector.port == 3306
        assert connector.database is None

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_connect(self, mock_connect):
        """测试建立连接"""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        connector = MySQLConnector(host="localhost", user="root", password="password")

        result = connector.connect()

        assert result == mock_connection
        assert connector.connection == mock_connection
        mock_connect.assert_called_once_with(
            host="localhost",
            port=3306,
            user="root",
            password="password",
            database=None,
            cursorclass=pymysql.cursors.DictCursor,
            charset="utf8mb4",
        )

    def test_close(self):
        """测试关闭连接"""
        connector = MySQLConnector(host="localhost", user="root", password="password")
        connector.connection = MagicMock()

        connector.close()

        connector.connection.close.assert_called_once()

    def test_close_without_connection(self):
        """测试关闭未建立的连接"""
        connector = MySQLConnector(host="localhost", user="root", password="password")
        connector.connection = None

        connector.close()

        assert True

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_execute_query_with_existing_connection(self, mock_connect):
        """测试使用现有连接执行查询"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]

        connector = MySQLConnector(host="localhost", user="root", password="password")
        connector.connection = mock_connection

        result = connector.execute_query("SELECT * FROM test")

        assert result == [{"id": 1, "name": "test"}]
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test")
        mock_cursor.fetchall.assert_called_once()
        mock_connect.assert_not_called()

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_execute_query_auto_connect(self, mock_connect):
        """测试自动建立连接执行查询"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        mock_cursor.fetchall.return_value = [{"id": 1}]

        connector = MySQLConnector(host="localhost", user="root", password="password")

        result = connector.execute_query("SELECT 1")

        assert result == [{"id": 1}]
        mock_connect.assert_called_once()

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_execute_query_with_params(self, mock_connect):
        """测试带参数执行查询"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        mock_cursor.fetchall.return_value = []

        connector = MySQLConnector(host="localhost", user="root", password="password")

        result = connector.execute_query(
            "SELECT * FROM users WHERE id = %s", params=(1,)
        )

        assert result == []
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM users WHERE id = %s", (1,)
        )

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_execute_query_empty_params(self, mock_connect):
        """测试空参数执行查询"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        mock_cursor.fetchall.return_value = []

        connector = MySQLConnector(host="localhost", user="root", password="password")

        result = connector.execute_query("SELECT 1")

        assert result == []
        mock_cursor.execute.assert_called_once_with("SELECT 1")

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_connection_success(self, mock_connect):
        """测试连接成功"""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        connector = MySQLConnector(
            host="localhost", user="root", password="password", database="test_db"
        )

        result = connector.test_connection()

        assert result is True
        mock_connect.assert_called_once_with(
            host="localhost",
            port=3306,
            user="root",
            password="password",
            database="test_db",
            connect_timeout=5,
        )
        mock_connection.close.assert_called_once()

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_connection_failure(self, mock_connect):
        """测试连接失败"""
        mock_connect.side_effect = Exception("Access denied")

        connector = MySQLConnector(
            host="localhost", user="root", password="wrong_password"
        )

        with pytest.raises(Exception) as exc_info:
            connector.test_connection()

        assert "连接测试失败" in str(exc_info.value)
        assert "Access denied" in str(exc_info.value)

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_get_global_status(self, mock_connect):
        """测试获取全局状态"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        mock_cursor.fetchall.return_value = [
            {"Variable_name": "Queries", "Value": "1000"},
            {"Variable_name": "Uptime", "Value": "3600"},
        ]

        connector = MySQLConnector(host="localhost", user="root", password="password")
        connector.connection = mock_connection

        result = connector.get_global_status()

        assert result == {"Queries": "1000", "Uptime": "3600"}
        mock_cursor.execute.assert_called_once_with("SHOW GLOBAL STATUS")

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_get_global_variables(self, mock_connect):
        """测试获取全局变量"""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        mock_cursor.fetchall.return_value = [
            {"Variable_name": "max_connections", "Value": "151"},
            {"Variable_name": "innodb_buffer_pool_size", "Value": "134217728"},
        ]

        connector = MySQLConnector(host="localhost", user="root", password="password")
        connector.connection = mock_connection

        result = connector.get_global_variables()

        assert result == {
            "max_connections": "151",
            "innodb_buffer_pool_size": "134217728",
        }
        mock_cursor.execute.assert_called_once_with("SHOW GLOBAL VARIABLES")

    @patch("app.services.mysql_connector.pymysql.connect")
    def test_context_manager(self, mock_connect):
        """测试上下文管理器"""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        with MySQLConnector(
            host="localhost", user="root", password="password"
        ) as connector:
            assert connector.connection == mock_connection

        mock_connection.close.assert_called_once()
