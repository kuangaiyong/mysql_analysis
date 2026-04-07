"""
Simple service layer tests
"""

import pytest
from unittest.mock import Mock, patch
from decimal import Decimal


class TestSimpleServices:
    """Simple service layer tests"""

    @patch("app.services.slow_query_analyzer.MySQLConnector")
    def test_query_hash_generation(self, mock_connector):
        """测试查询哈希生成"""
        from app.services.slow_query_analyzer import SlowQueryAnalyzer

        mock_instance = Mock()
        mock_connector.return_value = mock_instance

        analyzer = SlowQueryAnalyzer(connector=mock_instance)
        sql1 = "SELECT * FROM users WHERE id = 1"
        sql2 = "SELECT * FROM users WHERE id = 2"

        hash1 = analyzer.generate_query_hash(sql1)
        hash2 = analyzer.generate_query_hash(sql2)

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64

    @patch("app.services.slow_query_analyzer.MySQLConnector")
    def test_different_queries_different_hashes(self, mock_connector):
        """测试不同查询生成不同哈希"""
        from app.services.slow_query_analyzer import SlowQueryAnalyzer

        mock_instance = Mock()
        mock_connector.return_value = mock_instance

        analyzer = SlowQueryAnalyzer(connector=mock_instance)
        sql1 = "SELECT * FROM users"
        sql2 = "SELECT * FROM orders"

        hash1 = analyzer.generate_query_hash(sql1)
        hash2 = analyzer.generate_query_hash(sql2)

        assert hash1 != hash2

    @patch("app.services.mysql_connector.pymysql")
    def test_mysql_connector_init(self, mock_pymysql):
        """测试 MySQL 连接器初始化"""
        from app.services.mysql_connector import MySQLConnector

        connector = MySQLConnector(
            host="localhost", port=3306, user="test_user", password="test_pass"
        )

        assert connector.host == "localhost"
        assert connector.port == 3306
        assert connector.user == "test_user"
        assert connector.password == "test_pass"
        assert connector.database is None
        assert connector.connection is None

    @patch("app.services.mysql_connector.pymysql")
    def test_mysql_connector_with_database(self, mock_pymysql):
        """测试带数据库的 MySQL 连接器初始化"""
        from app.services.mysql_connector import MySQLConnector

        connector = MySQLConnector(
            host="localhost",
            port=3307,
            user="root",
            password="password",
            database="test_db",
        )

        assert connector.database == "test_db"

    def test_cache_class_init(self):
        """测试缓存类初始化"""
        from app.services.cache import RedisCache

        cache = RedisCache(host="localhost", port=6379, db=0)

        assert cache.host == "localhost"
        assert cache.port == 6379
        assert cache.db == 0
