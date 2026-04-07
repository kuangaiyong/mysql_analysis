"""
性能监控测试
测试实时性能指标、慢查询和索引统计相关API端点
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


def test_get_metrics_success(
    client: TestClient, test_connection, mock_performance_collector
):
    """测试获取性能指标列表成功"""
    from unittest.mock import AsyncMock

    mock_performance_collector.collect_realtime_metrics = AsyncMock(
        return_value={
            "qps": 100.5,
            "tps": 50.2,
            "connections": {"current": 10, "max": 100, "active": 8},
            "buffer_pool_hit_rate": 99.5,
            "queries": {"select": 100, "insert": 20, "update": 30, "delete": 10},
            "system": {"uptime": 3600, "thread_count": 8},
        }
    )

    response = client.get(
        f"/api/v1/monitoring/connections/{test_connection.id}/metrics"
    )

    assert response.status_code == 200
    data = response.json()
    assert "qps" in data
    assert "tps" in data
    assert "connections" in data


def test_get_metrics_connection_not_found(client: TestClient):
    """测试获取性能指标 - 连接不存在"""
    response = client.get("/api/v1/monitoring/connections/99999/metrics")
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_get_metrics_with_pagination(
    client: TestClient, test_connection, mock_performance_collector
):
    """测试获取性能指标 - 分页"""
    from unittest.mock import AsyncMock

    mock_performance_collector.collect_realtime_metrics = AsyncMock(
        return_value={
            "qps": 100.0,
            "tps": 50.0,
            "connections": {"current": 10, "max": 100, "active": 8},
            "buffer_pool_hit_rate": 99.5,
            "queries": {"select": 100, "insert": 20, "update": 30, "delete": 10},
            "system": {"uptime": 3600, "thread_count": 8},
        }
    )

    response = client.get(
        f"/api/v1/monitoring/connections/{test_connection.id}/metrics?skip=0&limit=50"
    )

    response = client.get(
        f"/api/v1/monitoring/connections/{test_connection.id}/metrics?skip=0&limit=50"
    )

    response = client.get(
        f"/api/v1/monitoring/connections/{test_connection.id}/metrics?skip=0&limit=50"
    )

    response = client.get(
        f"/api/v1/monitoring/connections/{test_connection.id}/metrics?skip=0&limit=50"
    )

    assert response.status_code == 200


def test_get_metrics_history(client: TestClient, test_connection):
    """测试获取指标历史数据"""
    response = client.get(
        f"/api/v1/monitoring/connections/{test_connection.id}/metrics/history?start_time=2024-01-01&end_time=2024-01-02"
    )
    assert response.status_code == 200
    # Empty result is expected when no metrics in database
    assert isinstance(response.json(), list)


def test_get_realtime_metrics_success(
    client: TestClient, test_connection, mock_redis_cache
):
    """测试获取实时性能指标成功"""
    from unittest.mock import AsyncMock, Mock, patch

    mock_metrics = {
        "qps": 100.5,
        "tps": 50.2,
        "connections": {"current": 10, "max": 100, "active": 8},
        "buffer_pool_hit_rate": 99.5,
        "queries": {"select": 100, "insert": 20, "update": 30, "delete": 10},
        "system": {"uptime": 3600, "thread_count": 8},
    }

    with patch("app.routers.monitoring.redis_cache") as mock_redis:
        mock_redis.get = Mock(return_value=None)

        with patch(
            "app.routers.monitoring.PerformanceCollector"
        ) as mock_collector_class:
            mock_instance = Mock()
            mock_instance.collect_realtime_metrics = AsyncMock(
                return_value=mock_metrics
            )
            mock_collector_class.return_value = mock_instance

            response = client.get(
                f"/api/v1/monitoring/connections/{test_connection.id}/realtime-metrics"
            )

    assert response.status_code == 200
    data = response.json()
    assert data["qps"] == 100.5


def test_get_realtime_metrics_connection_not_found(client: TestClient):
    """测试获取实时指标 - 连接不存在"""
    response = client.get("/api/v1/monitoring/connections/99999/realtime-metrics")
    assert response.status_code == 404


def test_get_realtime_metrics_with_cache(client: TestClient, test_connection):
    """测试实时指标 - 使用缓存"""
    from unittest.mock import AsyncMock, Mock, patch

    cached_metrics = {
        "qps": 95.0,
        "tps": 50.0,
        "connections": {"current": 10, "max": 100, "active": 8},
        "buffer_pool_hit_rate": 99.5,
        "queries": {"select": 100, "insert": 20, "update": 30, "delete": 10},
        "system": {"uptime": 3600, "thread_count": 8},
    }

    mock_metrics = {
        "qps": 100.5,
        "tps": 50.2,
        "connections": {"current": 10, "max": 100, "active": 8},
        "buffer_pool_hit_rate": 99.5,
        "queries": {"select": 100, "insert": 20, "update": 30, "delete": 10},
        "system": {"uptime": 3600, "thread_count": 8},
    }

    with patch("app.routers.monitoring.redis_cache") as mock_redis:
        mock_redis.get = Mock(return_value=cached_metrics)

        with patch(
            "app.routers.monitoring.PerformanceCollector"
        ) as mock_collector_class:
            mock_instance = Mock()
            mock_instance.collect_realtime_metrics = AsyncMock(
                return_value=mock_metrics
            )
            mock_collector_class.return_value = mock_instance

            response = client.get(
                f"/api/v1/monitoring/connections/{test_connection.id}/realtime-metrics"
            )

    assert response.status_code == 200
    data = response.json()
    assert data["qps"] == 95.0


def test_start_monitoring_success(client: TestClient, test_connection):
    """测试启动自动指标采集成功"""
    response = client.post(
        f"/api/v1/monitoring/connections/{test_connection.id}/start-monitoring"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "已启动" in data["message"]


def test_start_monitoring_connection_not_found(client: TestClient):
    """测试启动指标采集 - 连接不存在"""
    response = client.post("/api/v1/monitoring/connections/99999/start-monitoring")
    assert response.status_code == 404


def test_stop_monitoring_success(client: TestClient, test_connection):
    """测试停止自动指标采集成功"""
    response = client.post(
        f"/api/v1/monitoring/connections/{test_connection.id}/stop-monitoring"
    )
    assert response.status_code == 200


def test_stop_monitoring_by_collection_id(client: TestClient, test_connection):
    """测试通过collection_id停止指标采集（兼容前端）"""
    response = client.post(f"/api/v1/monitoring/monitoring/{test_connection.id}/stop")
    assert response.status_code == 200


def test_stop_monitoring_connection_not_found(client: TestClient):
    """测试停止指标采集 - 连接不存在"""
    response = client.post("/api/v1/monitoring/connections/99999/stop-monitoring")
    assert response.status_code == 404


def test_test_connection_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试数据库连接成功"""
    mock_mysql_connector.test_connection.return_value = None

    response = client.post(f"/api/v1/monitoring/connections/{test_connection.id}/test")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_test_connection_connection_not_found(client: TestClient):
    """测试数据库连接 - 连接不存在"""
    response = client.post("/api/v1/monitoring/connections/99999/test")
    assert response.status_code == 404


def test_get_slow_queries_success(
    client: TestClient, test_connection, mock_performance_collector
):
    """测试获取慢查询列表成功"""
    mock_performance_collector.get_slow_queries_from_performance_schema.return_value = [
        {
            "sql_digest": "SELECT * FROM users",
            "query_time": 2.5,
            "rows_examined": 1000,
            "query_hash": "abc123",
        }
    ]

    response = client.get(
        f"/api/v1/monitoring/slow-queries?connection_id={test_connection.id}"
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_slow_queries_with_limit(
    client: TestClient, test_connection, mock_performance_collector
):
    """测试获取慢查询 - 带limit参数"""
    mock_performance_collector.get_slow_queries_from_performance_schema.return_value = []

    response = client.get(
        f"/api/v1/monitoring/slow-queries?connection_id={test_connection.id}&limit=50"
    )

    assert response.status_code == 200


def test_get_slow_query_by_hash_not_found(client: TestClient):
    """测试根据query_hash获取慢查询详情 - 不存在"""
    from unittest.mock import patch, Mock

    with patch("app.routers.monitoring.MySQLConnector") as mock_connector_class:
        mock_connector = Mock()
        mock_connector.execute_query.return_value = []  # 返回空列表表示未找到
        mock_connector_class.return_value = mock_connector

        response = client.get("/api/v1/monitoring/slow-queries/nonexistent123")
        assert response.status_code == 404
        assert "不存在" in response.json()["detail"]


def test_get_slow_query_by_hash_success(client: TestClient):
    """测试根据query_hash获取慢查询详情 - 成功"""
    from unittest.mock import patch, Mock

    mock_slow_query_result = [
        {
            "sql_digest": "SELECT * FROM users WHERE id = ?",
            "execution_count": 10,
            "total_query_time": 5.5,
            "avg_query_time": 0.55,
            "max_query_time": 1.2,
            "total_rows_examined": 10000,
            "total_rows_sent": 500,
            "database_name": "test_db",
            "query_hash": "abc123",
        }
    ]

    mock_analysis = {
        "explain_result": [{"id": 1, "select_type": "SIMPLE", "table": "users", "type": "ALL", "rows": 1000}],
        "suggestions": [{"type": "index", "priority": "high", "title": "全表扫描警告"}],
        "risk_level": "high",
        "performance_score": "D",
        "analysis_details": "访问类型: ALL (全表扫描)",
    }

    with patch("app.services.mysql_connector.MySQLConnector") as mock_connector_class:
        with patch("app.services.slow_query_analyzer.SlowQueryAnalyzer") as mock_analyzer_class:
            mock_connector = Mock()
            mock_connector.execute_query.return_value = mock_slow_query_result
            mock_connector_class.return_value = mock_connector

            mock_analyzer = Mock()
            mock_analyzer.analyze_slow_query.return_value = mock_analysis
            mock_analyzer_class.return_value = mock_analyzer

            response = client.get("/api/v1/monitoring/slow-queries/abc123")

            assert response.status_code == 200
            data = response.json()
            assert data["query_hash"] == "abc123"
            assert data["sql_text"] == "SELECT * FROM users WHERE id = ?"
            assert "explain_result" in data
            assert "suggestions" in data
            assert data["risk_level"] == "high"

def test_analyze_slow_query(client: TestClient):
    """测试分析慢查询并返回优化建议"""
    response = client.post(
        "/api/v1/monitoring/slow-queries/analyze",
        json={"sql": "SELECT * FROM users", "connection_id": 1},
    )
    assert response.status_code == 200


def test_analyze_slow_query_missing_sql(client: TestClient):
    """测试分析慢查询 - SQL为空"""
    response = client.post(
        "/api/v1/monitoring/slow-queries/analyze", json={"sql": "", "connection_id": 1}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False


def test_resolve_slow_query(client: TestClient, auth_headers):
    """测试标记慢查询为已解决"""
    response = client.post(
        "/api/v1/monitoring/slow-queries/abc123/resolve", json={"note": "已优化"}, headers=auth_headers
    )
    assert response.status_code == 404


def test_delete_slow_query(client: TestClient, auth_headers):
    """测试删除慢查询记录"""
    response = client.delete("/api/v1/monitoring/slow-queries/abc123", headers=auth_headers)
    assert response.status_code == 404


def test_batch_resolve_slow_queries(client: TestClient):
    """测试批量标记慢查询为已解决"""
    response = client.post(
        "/api/v1/monitoring/slow-queries/batch-resolve", json={"query_ids": [1, 2, 3]}
    )
    assert response.status_code == 200


def test_batch_resolve_slow_queries_empty(client: TestClient):
    """测试批量标记慢查询 - 空列表"""
    response = client.post(
        "/api/v1/monitoring/slow-queries/batch-resolve", json={"query_ids": []}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False


def test_batch_delete_slow_queries(client: TestClient):
    """测试批量删除慢查询"""
    response = client.request(
        "DELETE",
        "/api/v1/monitoring/slow-queries/batch-delete",
        json={"query_ids": [1, 2, 3]},
    )
    assert response.status_code == 200


def test_batch_delete_slow_queries_empty(client: TestClient):
    """测试批量删除慢查询 - 空列表"""
    response = client.request(
        "DELETE", "/api/v1/monitoring/slow-queries/batch-delete", json={"query_ids": []}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False


def test_list_slow_queries_without_pagination(client: TestClient, auth_headers):
    """测试获取所有慢查询（不分页）"""
    response = client.get("/api/v1/monitoring/slow-queries/", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "connection_id,expected_status",
    [
        (1, 200),
        (99999, 404),
    ],
)
def test_realtime_metrics_various_connections(
    client: TestClient,
    connection_id,
    expected_status,
    test_connection,
    mock_redis_cache,
):
    """测试不同连接ID的实时指标获取"""
    from unittest.mock import AsyncMock, Mock, patch

    mock_metrics = {
        "qps": 100.0,
        "tps": 50.0,
        "connections": {"current": 10, "max": 100, "active": 8},
        "buffer_pool_hit_rate": 99.5,
        "queries": {"select": 100, "insert": 20, "update": 30, "delete": 10},
        "system": {"uptime": 3600, "thread_count": 8},
    }

    if connection_id == 1:
        with patch("app.routers.monitoring.redis_cache") as mock_redis:
            mock_redis.get = Mock(return_value=None)

            with patch(
                "app.routers.monitoring.PerformanceCollector"
            ) as mock_collector_class:
                mock_instance = Mock()
                mock_instance.collect_realtime_metrics = AsyncMock(
                    return_value=mock_metrics
                )
                mock_collector_class.return_value = mock_instance

                response = client.get(
                    f"/api/v1/monitoring/connections/{connection_id}/realtime-metrics"
                )
    else:
        response = client.get(
            f"/api/v1/monitoring/connections/{connection_id}/realtime-metrics"
        )

    assert response.status_code == expected_status
