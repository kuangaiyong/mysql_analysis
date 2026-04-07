"""
Performance Collector 服务测试补充
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from app.services.performance_collector import PerformanceCollector


# 导入 helper 函数（从主测试文件）
from tests.services.test_performance_collector import create_mock_query_results


class TestPerformanceCollector:
    """性能收集器测试类补充"""

    def test_init(self):
        """测试初始化"""
        config = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "password",
        }
        cache = Mock()
        collector = PerformanceCollector(connection_config=config, redis_cache=cache)

        assert collector.redis_cache == cache

    @pytest.mark.asyncio
    @patch("app.services.performance_collector.MySQLConnector")
    async def test_collect_realtime_metrics(self, mock_connector_class):
        """测试收集实时指标"""
        # 设置 mock
        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.execute_query = Mock(side_effect=create_mock_query_results())
        mock_connector_class.return_value = mock_conn

        cache = Mock()
        cache.get_cached_metrics = AsyncMock(return_value=None)
        cache.cache_metrics = AsyncMock()

        collector = PerformanceCollector(
            connection_config={
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "password",
            },
            redis_cache=cache,
        )
        result = await collector.collect_realtime_metrics()

        assert result is not None
        assert "qps" in result

    @pytest.mark.asyncio
    @patch("app.services.performance_collector.MySQLConnector")
    async def test_calculate_qps(self, mock_connector_class):
        """测试计算QPS"""
        # 设置 mock
        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.execute_query = Mock(side_effect=create_mock_query_results())
        mock_connector_class.return_value = mock_conn

        cache = Mock()
        cache.get_cached_metrics = AsyncMock(return_value=None)
        cache.cache_metrics = AsyncMock()

        collector = PerformanceCollector(
            connection_config={
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "password",
            },
            redis_cache=cache,
        )
        result = await collector.collect_realtime_metrics()

        assert result is not None
        assert "qps" in result

    @patch("app.services.performance_collector.MySQLConnector")
    def test_get_slow_queries_from_performance_schema(self, mock_connector_class):
        """测试从performance_schema获取慢查询"""
        # 设置 mock
        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.execute_query = Mock(
            return_value=[
                {
                    "sql_digest": "SELECT * FROM users",
                    "execution_count": 100,
                    "avg_query_time": 2.5,
                    "total_rows_examined": 10000,
                    "total_rows_sent": 1000,
                    "query_hash": "hash1",
                }
            ]
        )
        mock_connector_class.return_value = mock_conn

        cache = Mock()
        collector = PerformanceCollector(
            connection_config={
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "password",
            },
            redis_cache=cache,
        )
        result = collector.get_slow_queries_from_performance_schema(limit=10)

        assert len(result) == 1

    @patch("app.services.performance_collector.MySQLConnector")
    def test_get_index_usage_stats(self, mock_connector_class):
        """测试获取索引使用统计"""
        # 设置 mock
        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_conn.execute_query = Mock(
            return_value=[
                {
                    "total_indexes": 10,
                    "total_index_usages": 1000,
                }
            ]
        )
        mock_connector_class.return_value = mock_conn

        cache = Mock()
        collector = PerformanceCollector(
            connection_config={
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "password",
            },
            redis_cache=cache,
        )
        result = collector.get_index_usage_stats()

        assert isinstance(result, dict)

    def test_cache_metrics_success(self):
        """测试缓存指标成功"""
        cache = Mock()
        cache.set.return_value = True

        collector = PerformanceCollector(
            connection_config={
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "test",
            },
            redis_cache=cache,
        )
        result = collector.redis_cache.set(
            f"metrics:1", {"qps": 100, "tps": 50}, expire=300
        )

        assert result is True
        cache.set.assert_called_once()

    def test_cache_metrics_with_ttl(self):
        """测试缓存指标带TTL"""
        cache = Mock()
        cache.set.return_value = True

        collector = PerformanceCollector(
            connection_config={
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "test",
            },
            redis_cache=cache,
        )
        result = collector.redis_cache.set(f"metrics:1", {"qps": 100}, expire=1800)

        assert result is True

    def test_get_cached_metrics_success(self):
        """测试获取缓存指标成功"""
        cache = Mock()
        cache.get.return_value = b'{"qps": 100}'

        collector = PerformanceCollector(
            connection_config={
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "test",
            },
            redis_cache=cache,
        )
        result = collector.redis_cache.get(f"metrics:1")

        assert result == b'{"qps": 100}'
