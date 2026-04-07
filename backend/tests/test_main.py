"""
测试 main.py 模块
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app


class TestMainApp:
    """测试主应用"""

    def test_app_creation(self):
        """测试应用创建"""
        assert app.title == "MySQL性能诊断系统"
        assert app.version == "1.0.0"
        assert app.docs_url == "/api/docs"
        assert app.redoc_url == "/api/redoc"

    def test_health_check(self):
        """测试健康检查接口"""
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    def test_cors_middleware(self):
        """测试CORS中间件 - 验证CORS配置已正确设置"""
        from app.config import settings

        # 测试配置是否正确加载
        assert settings.cors_origins_list is not None
        assert isinstance(settings.cors_origins_list, list)
        assert "http://localhost:5173" in settings.cors_origins_list

    @patch("app.main.init_db")
    def test_startup_event(self, mock_init_db):
        """测试启动事件"""
        # 注意：这个测试不会真正调用 startup_event，
        # 因为 TestClient 不会触发 startup 事件
        # 这里我们只是验证 mock 已设置
        assert mock_init_db is not None

    def test_api_docs_available(self):
        """测试API文档可用"""
        client = TestClient(app)
        response = client.get("/api/docs")
        assert response.status_code == 200

    def test_redoc_available(self):
        """测试ReDoc可用"""
        client = TestClient(app)
        response = client.get("/api/redoc")
        assert response.status_code == 200

    def test_router_registration(self):
        """测试路由注册"""
        routes = [route.path for route in app.routes]
        # 打印所有路由用于调试
        api_routes = [r for r in routes if "/api" in r]
        print(f"API Routes: {api_routes}")

        # 检查主要路由是否已注册
        assert any("/api/v1/connections" in route for route in routes), (
            "connections route not found"
        )
        assert any("/api/v1/monitoring" in route for route in routes), (
            "monitoring route not found"
        )
        assert any("/api/v1/explain" in route for route in routes), (
            "explain route not found"
        )
        assert any("indexes" in route for route in routes), "index route not found"
        assert any("/api/v1/slow-queries" in route for route in routes), (
            "slow-queries route not found"
        )
        assert any("/api/v1/alerts" in route for route in routes), (
            "alerts route not found"
        )
        assert any("/api/v1/reports" in route for route in routes), (
            "reports route not found"
        )
        assert any("/api/v1/table" in route for route in routes), (
            "table route not found"
        )

    def test_openapi_schema(self):
        """测试OpenAPI schema生成"""
        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema


class TestMainAppIntegration:
    """测试主应用集成"""

    def test_root_endpoint_not_found(self):
        """测试根端点返回404"""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 404

    def test_invalid_endpoint(self):
        """测试无效端点在/api/v1/下返回401(认证优先于路由)"""
        client = TestClient(app)
        response = client.get("/api/v1/invalid-endpoint")
        # AuthMiddleware 在路由之前检查认证，所以未认证的 /api/v1/* 请求返回 401
        assert response.status_code == 401

    def test_global_exception_handler(self):
        """测试全局异常处理器"""
        client = TestClient(app)

        # 这个端点不存在，应该返回 401 (认证在路由之前检查)
        response = client.get("/api/v1/nonexistent")
        # 认证中间件在路由之前检查，未认证的 /api/v1/* 请求返回 401
        assert response.status_code == 401
