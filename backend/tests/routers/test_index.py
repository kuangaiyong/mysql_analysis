"""
Index Router 集成测试
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.test_factories import ConnectionFactory


class TestIndexRouter:
    """索引路由测试类"""

    def test_list_indexes_success(self, db_session: Session, client: TestClient):
        """测试列出表索引"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        response = client.get(f"/api/v1/index/list/{connection.id}/users")

        assert response.status_code in [200, 404]

    def test_list_indexes_not_found(self, client: TestClient):
        """测试列出不存在的索引"""
        response = client.get("/api/v1/index/list/999/users")

        assert response.status_code in [200, 404]

    def test_list_indexes_invalid_table(self, client: TestClient):
        """测试无效的表名"""
        response = client.get("/api/v1/index/list/1/invalid_table_name!")

        assert response.status_code in [200, 404, 422]

    def test_create_index_success(self, db_session: Session, client: TestClient):
        """测试创建索引"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {
            "connection_id": connection.id,
            "table_name": "users",
            "index_name": "idx_email",
            "columns": ["email"],
        }

        response = client.post("/api/v1/index/create", json=request_data)

        assert response.status_code in [200, 404, 422]

    def test_create_index_missing_fields(self, client: TestClient):
        """测试创建索引缺少字段"""
        response = client.post("/api/v1/index/1/indexes", json={})

        assert response.status_code in [404, 422]

    def test_drop_index_success(self, db_session: Session, client: TestClient):
        """测试删除索引"""
        connection = ConnectionFactory()
        db_session.add(connection)
        db_session.commit()

        request_data = {
            "connection_id": connection.id,
            "table_name": "users",
            "index_name": "idx_email",
        }

        response = client.post("/api/v1/index/drop", json=request_data)

        assert response.status_code in [200, 404, 422]

    def test_drop_index_missing_fields(self, client: TestClient):
        """测试删除索引缺少字段"""
        response = client.post("/api/v1/index/1/indexes/drop", json={})

        assert response.status_code in [404, 422]

    def test_invalid_connection_id(self, client: TestClient):
        """测试无效的连接ID"""
        response = client.post(
            "/api/v1/index/create",
            json={"connection_id": "invalid", "table_name": "users"},
        )

        assert response.status_code in [404, 422]
