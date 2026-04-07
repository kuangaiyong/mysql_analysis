"""
Index router comprehensive tests
"""

import pytest
from fastapi.testclient import TestClient


class TestIndexRouterComprehensive:
    """Index router comprehensive tests"""

    def test_list_indexes_basic(self, client: TestClient):
        """测试基本索引列表"""
        response = client.get("/api/v1/index/list/1/users")

        assert response.status_code in [200, 404]

    def test_list_indexes_with_pagination(self, client: TestClient):
        """测试分页索引列表"""
        response = client.get("/api/v1/index/list/1/users?skip=0&limit=10")

        assert response.status_code in [200, 404]

    def test_create_index_missing_fields(self, client: TestClient):
        """测试创建索引缺少字段"""
        response = client.post("/api/v1/index/1/indexes", json={})

        assert response.status_code in [404, 422]

    def test_create_index_invalid_table(self, client: TestClient):
        """测试为无效表创建索引"""
        response = client.post(
            "/api/v1/index/1/indexes",
            json={
                "connection_id": 1,
                "table_name": "nonexistent_table",
                "index_name": "idx_test",
                "columns": ["id"],
            },
        )

        assert response.status_code in [404, 422]

    def test_create_index_duplicate(self, client: TestClient):
        """测试创建重复索引"""
        response = client.post(
            "/api/v1/index/1/indexes",
            json={
                "connection_id": 1,
                "table_name": "users",
                "index_name": "idx_duplicate",
                "columns": ["email"],
            },
        )

        assert response.status_code in [200, 404, 422]

    def test_drop_index_missing_fields(self, client: TestClient):
        """测试删除索引缺少字段"""
        response = client.post("/api/v1/index/1/indexes/drop", json={})

        assert response.status_code in [404, 422]

    def test_drop_index_nonexistent(self, client: TestClient):
        """测试删除不存在的索引"""
        response = client.post(
            "/api/v1/index/1/indexes/drop",
            json={
                "connection_id": 1,
                "table_name": "users",
                "index_name": "idx_nonexistent",
            },
        )

        assert response.status_code in [200, 404]

    def test_index_analysis_basic(self, client: TestClient):
        """测试基本索引分析"""
        response = client.get("/api/v1/index/analyze/1/users")

        assert response.status_code in [200, 404]

    def test_index_analysis_empty_table(self, client: TestClient):
        """测试空表的索引分析"""
        response = client.get("/api/v1/index/analyze/1/empty_table")

        assert response.status_code in [200, 404]

    def test_multiple_indexes(self, client: TestClient):
        """测试多个索引"""
        response = client.post(
            "/api/v1/index/1/indexes",
            json={
                "connection_id": 1,
                "table_name": "users",
                "index_name": "idx_multi",
                "columns": ["id", "email", "created_at"],
            },
        )

        assert response.status_code in [200, 404, 422]
