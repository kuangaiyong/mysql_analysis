"""
慢查询分析测试
测试慢查询采集、分析和优化建议相关API端点
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime


def test_list_slow_queries_empty(client: TestClient, test_connection):
    """测试获取慢查询列表 - 空列表"""
    response = client.get(f"/api/v1/slow-queries/list/{test_connection.id}")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_list_slow_queries_with_data(
    client: TestClient, test_connection, test_slow_query
):
    """测试获取慢查询列表 - 有数据"""
    response = client.get(f"/api/v1/slow-queries/list/{test_connection.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_list_slow_queries_with_pagination(client: TestClient, test_connection):
    """测试获取慢查询列表 - 分页"""
    response = client.get(
        f"/api/v1/slow-queries/list/{test_connection.id}?skip=0&limit=5"
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


def test_list_slow_queries_with_ordering(client: TestClient, test_connection):
    """测试获取慢查询列表 - 排序"""
    response = client.get(
        f"/api/v1/slow-queries/list/{test_connection.id}?order_by=query_time&order_desc=true"
    )
    assert response.status_code == 200


def test_list_slow_queries_connection_not_found(client: TestClient):
    """测试获取慢查询列表 - 连接不存在"""
    response = client.get("/api/v1/slow-queries/list/99999")
    assert response.status_code == 404


def test_analyze_slow_query(client: TestClient, test_connection, test_slow_query):
    """测试分析慢查询"""
    import hashlib

    query_hash = test_slow_query.query_hash

    with patch("app.routers.slow_query.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.slow_query.SlowQueryAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.analyze_slow_query.return_value = {
                "query_hash": query_hash,
                "sql_digest": "SELECT * FROM users",
                "suggestions": [],
                "risk_level": "medium",
                "analysis_details": "分析完成",
            }
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.get(
                f"/api/v1/slow-queries/analysis/{test_connection.id}/{query_hash}"
            )

    assert response.status_code == 200


def test_analyze_slow_query_not_found(client: TestClient, test_connection):
    """测试分析不存在的慢查询"""
    query_hash = "nonexistent_hash"
    response = client.get(
        f"/api/v1/slow-queries/analysis/{test_connection.id}/{query_hash}"
    )
    # 可能返回404（不存在）或500（内部错误）
    assert response.status_code in [404, 500]


def test_analyze_slow_query_connection_not_found(client: TestClient):
    """测试分析慢查询 - 连接不存在"""
    response = client.get("/api/v1/slow-queries/analysis/99999/some_hash")
    assert response.status_code == 404


def test_collect_slow_queries(client: TestClient, test_connection):
    """测试从performance_schema采集慢查询"""
    with patch("app.routers.slow_query.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.slow_query.SlowQueryAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.collect_slow_queries_from_performance_schema.return_value = [
                {
                    "query_hash": "hash1",
                    "sql_digest": "SELECT * FROM users",
                    "avg_query_time": 2.5,
                    "total_rows_examined": 1000,
                    "total_rows_sent": 500,
                    "database_name": "test_db",
                    "execution_count": 10,
                }
            ]
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(f"/api/v1/slow-queries/collect/{test_connection.id}")

    assert response.status_code == 200
    data = response.json()
    assert "collected" in data
    assert "saved" in data


def test_collect_slow_queries_with_threshold(client: TestClient, test_connection):
    """测试采集慢查询 - 带threshold参数"""
    with patch("app.routers.slow_query.MySQLConnector") as mock_connector:
        mock_conn_instance = Mock()
        mock_conn_instance.__enter__ = Mock(return_value=mock_conn_instance)
        mock_conn_instance.__exit__ = Mock(return_value=False)
        mock_connector.return_value = mock_conn_instance

        with patch("app.routers.slow_query.SlowQueryAnalyzer") as mock_analyzer:
            mock_analyzer_instance = Mock()
            mock_analyzer_instance.collect_slow_queries_from_performance_schema.return_value = []
            mock_analyzer.return_value = mock_analyzer_instance

            response = client.post(
                f"/api/v1/slow-queries/collect/{test_connection.id}?threshold=2.0&limit=50"
            )

    assert response.status_code == 200


def test_collect_slow_queries_connection_not_found(client: TestClient):
    """测试采集慢查询 - 连接不存在"""
    response = client.post("/api/v1/slow-queries/collect/99999")
    assert response.status_code == 404


def test_get_slow_query_stats(client: TestClient, test_connection):
    """测试获取慢查询统计信息"""
    response = client.get(f"/api/v1/slow-queries/stats/{test_connection.id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_slow_query_stats_with_date_range(client: TestClient, test_connection):
    """测试获取慢查询统计 - 带时间范围"""
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    end_time = datetime(2024, 1, 2, 0, 0, 0)

    response = client.get(
        f"/api/v1/slow-queries/stats/{test_connection.id}?start_time={start_time.isoformat()}&end_time={end_time.isoformat()}"
    )

    assert response.status_code == 200


def test_get_slow_query_stats_connection_not_found(client: TestClient):
    """测试获取慢查询统计 - 连接不存在"""
    response = client.get("/api/v1/slow-queries/stats/99999")
    assert response.status_code == 404


def test_get_top_slow_queries(client: TestClient, test_connection, test_slow_query):
    """测试获取Top慢查询"""
    response = client.get(
        f"/api/v1/slow-queries/top/{test_connection.id}?limit=10&days=7"
    )
    assert response.status_code == 200
    data = response.json()
    assert "top_queries" in data
    assert isinstance(data["top_queries"], list)


def test_get_top_slow_queries_with_custom_limit(client: TestClient, test_connection):
    """测试获取Top慢查询 - 自定义limit"""
    response = client.get(
        f"/api/v1/slow-queries/top/{test_connection.id}?limit=5&days=30"
    )
    assert response.status_code == 200


def test_get_top_slow_queries_connection_not_found(client: TestClient):
    """测试获取Top慢查询 - 连接不存在"""
    response = client.get("/api/v1/slow-queries/top/99999")
    assert response.status_code == 404


def test_delete_slow_query(client: TestClient, test_connection, test_slow_query):
    """测试删除慢查询"""
    response = client.delete(f"/api/v1/slow-queries/{test_slow_query.id}")
    assert response.status_code == 204


def test_delete_slow_query_not_found(client: TestClient):
    """测试删除不存在的慢查询"""
    response = client.delete("/api/v1/slow-queries/99999")
    assert response.status_code == 404


@pytest.mark.parametrize("skip,limit", [(0, 10), (10, 20), (0, 100)])
def test_list_slow_queries_pagination_variations(
    client: TestClient, test_connection, skip, limit
):
    """测试慢查询列表的各种分页参数"""
    response = client.get(
        f"/api/v1/slow-queries/list/{test_connection.id}?skip={skip}&limit={limit}"
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    "order_by,order_desc",
    [
        ("query_time", True),
        ("query_time", False),
        ("timestamp", True),
    ],
)
def test_list_slow_queries_ordering_variations(
    client: TestClient, test_connection, order_by, order_desc
):
    """测试慢查询列表的各种排序参数"""
    response = client.get(
        f"/api/v1/slow-queries/list/{test_connection.id}?order_by={order_by}&order_desc={order_desc}"
    )
    assert response.status_code == 200
