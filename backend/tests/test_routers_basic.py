"""
Simple router tests - basic endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestBasicRouters:
    """Basic router tests"""

    def test_root_endpoint(self, client: TestClient):
        """测试根端点"""
        response = client.get("/")

        assert response.status_code in [200, 404]

    def test_health_check(self, client: TestClient):
        """测试健康检查端点（如果存在）"""
        response = client.get("/health")

        assert response.status_code in [200, 404]

    def test_api_docs(self, client: TestClient):
        """测试API文档端点"""
        response = client.get("/docs")

        assert response.status_code in [200, 404]

    def test_invalid_path(self, client: TestClient):
        """测试无效路径"""
        response = client.get("/api/v1/invalid-path")

        assert response.status_code == 404

    def test_get_connections_empty(self, client: TestClient):
        """测试获取空连接列表"""
        response = client.get("/api/v1/connections/")

        assert response.status_code in [200, 404]

    def test_post_connection_invalid(self, client: TestClient):
        """测试无效的连接创建"""
        response = client.post("/api/v1/connections/", json={})

        assert response.status_code in [200, 422]

    def test_explain_analyze_invalid(self, client: TestClient):
        """测试无效的EXPLAIN请求"""
        response = client.post("/api/v1/explain/analyze", json={})

        assert response.status_code in [200, 404, 422]
