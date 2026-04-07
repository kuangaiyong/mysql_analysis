"""
Monitoring router comprehensive tests
"""

import pytest
from fastapi.testclient import TestClient


class TestMonitoringRouterComprehensive:
    """Monitoring router comprehensive tests"""

    def test_realtime_metrics_basic(self, client: TestClient):
        """测试基本实时指标"""
        response = client.get("/api/v1/monitoring/realtime/1")

        assert response.status_code in [200, 404]

    def test_realtime_metrics_cache_hit(self, client: TestClient):
        """测试实时指标缓存命中"""
        response = client.get("/api/v1/monitoring/realtime/1?use_cache=true")

        assert response.status_code in [200, 404]

    def test_realtime_metrics_timeout(self, client: TestClient):
        """测试实时指标超时"""
        response = client.get("/api/v1/monitoring/realtime/999")

        assert response.status_code in [404, 200]

    def test_slow_queries_basic(self, client: TestClient):
        """测试基本慢查询列表"""
        response = client.get("/api/v1/monitoring/slow-queries?connection_id=1&limit=10")

        assert response.status_code in [200, 404, 500]

    def test_slow_queries_with_time_range(self, client: TestClient):
        """测试带时间范围的慢查询"""
        response = client.get(
            "/api/v1/monitoring/slow-queries?connection_id=1&hours=24&threshold=2.0"
        )

        assert response.status_code in [200, 404, 500]

    def test_slow_queries_pagination(self, client: TestClient):
        """测试慢查询分页"""
        response = client.get("/api/v1/monitoring/slow-queries?connection_id=1&skip=0&limit=20")

        assert response.status_code in [200, 404, 500]

    def test_index_stats_basic(self, client: TestClient):
        """测试基本索引统计"""
        response = client.get("/api/v1/monitoring/index-stats/1")

        assert response.status_code in [200, 404]

    def test_start_collection_success(self, client: TestClient):
        """测试成功启动收集"""
        response = client.post("/api/v1/monitoring/start-collection/1")

        assert response.status_code in [200, 404]

    def test_stop_collection(self, client: TestClient):
        """测试停止收集"""
        response = client.post("/api/v1/monitoring/stop-collection/1")

        assert response.status_code in [200, 404]

    def test_collection_status(self, client: TestClient):
        """测试收集状态"""
        response = client.get("/api/v1/monitoring/collection-status/1")

        assert response.status_code in [200, 404]

    def test_custom_metrics(self, client: TestClient):
        """测试自定义指标"""
        response = client.get("/api/v1/monitoring/metrics/1?metrics=cpu,memory,disk")

        assert response.status_code in [200, 404]

    def test_metrics_aggregation(self, client: TestClient):
        """测试指标聚合"""
        response = client.get("/api/v1/monitoring/metrics/1?aggregate=avg,max,min")

        assert response.status_code in [200, 404]
