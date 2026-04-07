"""
慢查询模块测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import hashlib


def test_list_slow_queries_success(
    client: TestClient, test_connection, test_slow_query
):
    """测试获取慢查询列表成功"""
    response = client.get(
        f"/api/v1/slow-queries/list/{test_connection.id}?skip=0&limit=10"
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data


def test_list_slow_queries_connection_not_found(client: TestClient):
    """测试获取慢查询列表 - 连接不存在"""
    response = client.get("/api/v1/slow-queries/list/99999")
    assert response.status_code == 404


def test_list_slow_queries_with_ordering(client: TestClient, test_connection):
    """测试获取慢查询列表 - 带排序"""
    response = client.get(
        f"/api/v1/slow-queries/list/{test_connection.id}?order_by=query_time&order_desc=true"
    )
    assert response.status_code == 200


def test_analyze_slow_query_success(
    client: TestClient, test_connection, test_slow_query, mock_mysql_connector
):
    """测试分析慢查询成功"""
    with patch("app.routers.slow_query.SlowQueryAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.analyze_slow_query.return_value = {
            "query_hash": test_slow_query.query_hash,
            "sql_digest": "SELECT * FROM users",
            "suggestions": [
                {
                    "type": "index",
                    "priority": "high",
                    "title": "添加索引",
                    "description": "为WHERE条件添加索引",
                }
            ],
            "risk_level": "medium",
            "analysis_details": "查询执行时间较长",
        }
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/slow-queries/analysis/{test_connection.id}/{test_slow_query.query_hash}"
        )

    assert response.status_code == 200
    data = response.json()
    assert "query_hash" in data
    assert "suggestions" in data


def test_analyze_slow_query_connection_not_found(client: TestClient):
    """测试分析慢查询 - 连接不存在"""
    response = client.get("/api/v1/slow-queries/analysis/99999/abc123")
    assert response.status_code == 404


def test_analyze_slow_query_query_not_found(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试分析慢查询 - 查询不存在"""
    with patch("app.routers.slow_query.SlowQueryAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/slow-queries/analysis/{test_connection.id}/nonexistent"
        )

    assert response.status_code == 404


def test_collect_slow_queries_success(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试采集慢查询成功"""
    with patch("app.routers.slow_query.SlowQueryAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.collect_slow_queries_from_performance_schema.return_value = []
        mock_instance.get_full_sql_from_digest.return_value = "SELECT * FROM users"
        mock_instance.analyze_slow_query.return_value = {
            "query_hash": "abc123",
            "suggestions": [],
            "performance_score": 80,
        }
        mock_analyzer.return_value = mock_instance

        response = client.post(
            f"/api/v1/slow-queries/collect/{test_connection.id}",
            json={"threshold": 1.0, "limit": 10},
        )

    assert response.status_code == 200
    data = response.json()
    assert "collected" in data
    assert "saved" in data


def test_collect_slow_queries_connection_not_found(client: TestClient):
    """测试采集慢查询 - 连接不存在"""
    response = client.post("/api/v1/slow-queries/collect/99999")
    assert response.status_code == 404


def test_collect_slow_queries_invalid_threshold(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试采集慢查询 - 无效阈值"""
    response = client.post(
        f"/api/v1/slow-queries/collect/{test_connection.id}",
        json={"threshold": -1.0, "limit": 10},
    )
    assert response.status_code in [400, 500]


def test_get_slow_query_stats_success(client: TestClient, test_connection):
    """测试获取慢查询统计成功"""
    response = client.get(f"/api/v1/slow-queries/stats/{test_connection.id}")
    assert response.status_code == 200
    data = response.json()
    assert "total_count" in data or "total_queries" in data


def test_get_slow_query_stats_connection_not_found(client: TestClient):
    """测试获取慢查询统计 - 连接不存在"""
    response = client.get("/api/v1/slow-queries/stats/99999")
    assert response.status_code == 404


def test_get_slow_query_stats_with_date_range(client: TestClient, test_connection):
    """测试获取慢查询统计 - 带日期范围"""
    from datetime import datetime, timedelta

    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    response = client.get(
        f"/api/v1/slow-queries/stats/{test_connection.id}?start_time={start_time.isoformat()}&end_time={end_time.isoformat()}"
    )
    assert response.status_code == 200


def test_get_top_slow_queries_success(client: TestClient, test_connection):
    """测试获取Top慢查询成功"""
    response = client.get(
        f"/api/v1/slow-queries/top/{test_connection.id}?limit=10&days=7"
    )
    assert response.status_code == 200
    data = response.json()
    assert "top_queries" in data


def test_get_top_slow_queries_connection_not_found(client: TestClient):
    """测试获取Top慢查询 - 连接不存在"""
    response = client.get("/api/v1/slow-queries/top/99999")
    assert response.status_code == 404


def test_get_top_slow_queries_custom_limit(client: TestClient, test_connection):
    """测试获取Top慢查询 - 自定义limit"""
    response = client.get(
        f"/api/v1/slow-queries/top/{test_connection.id}?limit=5&days=30"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["top_queries"]) <= 5


def test_delete_slow_query_success(client: TestClient, test_slow_query):
    """测试删除慢查询成功"""
    response = client.delete(f"/api/v1/slow-queries/{test_slow_query.id}")
    assert response.status_code == 204


def test_delete_slow_query_not_found(client: TestClient):
    """测试删除慢查询 - 查询不存在"""
    response = client.delete("/api/v1/slow-queries/99999")
    assert response.status_code == 404


def test_list_slow_queries_empty_response(client: TestClient, test_connection):
    """测试获取慢查询列表 - 空响应"""
    response = client.get(
        f"/api/v1/slow-queries/list/{test_connection.id}?skip=0&limit=10"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0


def test_collect_slow_queries_service_error(
    client: TestClient, test_connection, mock_mysql_connector
):
    """测试采集慢查询 - 服务异常"""
    with patch("app.routers.slow_query.SlowQueryAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.collect_slow_queries_from_performance_schema.side_effect = (
            Exception("数据库错误")
        )
        mock_analyzer.return_value = mock_instance

        response = client.post(
            f"/api/v1/slow-queries/collect/{test_connection.id}",
            json={"threshold": 1.0, "limit": 10},
        )

    assert response.status_code == 500
    assert "采集慢查询失败" in response.json()["detail"]


def test_analyze_slow_query_service_error(
    client: TestClient, test_connection, test_slow_query, mock_mysql_connector
):
    """测试分析慢查询 - 服务异常"""
    with patch("app.routers.slow_query.SlowQueryAnalyzer") as mock_analyzer:
        mock_instance = Mock()
        mock_instance.analyze_slow_query.side_effect = Exception("分析失败")
        mock_instance.get_full_sql_from_digest.return_value = "SELECT * FROM users"
        mock_analyzer.return_value = mock_instance

        response = client.get(
            f"/api/v1/slow-queries/analysis/{test_connection.id}/{test_slow_query.query_hash}"
        )

    assert response.status_code == 500


def test_get_slow_query_stats_service_error(client: TestClient, test_connection):
    """测试获取慢查询统计 - 服务异常"""
    with patch("app.crud.slow_query.get_slow_query_stats") as mock_crud:
        mock_crud.side_effect = Exception("数据库错误")

        response = client.get(f"/api/v1/slow-queries/stats/{test_connection.id}")

    assert response.status_code == 500


def test_get_top_slow_queries_service_error(client: TestClient, test_connection):
    """测试获取Top慢查询 - 服务异常"""
    with patch("app.crud.slow_query.get_top_slow_queries") as mock_crud:
        mock_crud.side_effect = Exception("数据库错误")

        response = client.get(
            f"/api/v1/slow-queries/top/{test_connection.id}?limit=10&days=7"
        )

    assert response.status_code == 500
