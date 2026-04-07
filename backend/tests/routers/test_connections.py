"""
Connection API路由测试
"""

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.crud import connection as connection_crud
from app.schemas.connection import ConnectionCreate, ConnectionUpdate
from app.models.connection import Connection


class TestConnectionRouter:
    """Connection路由测试类"""

    def test_create_connection_success(
        self, client, sample_connection_data: dict, mock_mysql_connector
    ):
        """测试成功创建连接"""
        response = client.post("/api/v1/connections/", json=sample_connection_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] is not None
        assert data["name"] == sample_connection_data["name"]

    def test_create_connection_duplicate_name(
        self,
        client,
        db_session: Session,
        sample_connection_data: dict,
        mock_mysql_connector,
    ):
        """测试创建重名连接"""
        connection_create = ConnectionCreate(**sample_connection_data)
        connection_crud.create_connection(db=db_session, connection=connection_create)

        response = client.post("/api/v1/connections/", json=sample_connection_data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_connection_missing_fields(self, client):
        """测试创建缺少字段的连接"""
        incomplete_data = {"name": "测试连接", "host": "127.0.0.1"}

        response = client.post("/api/v1/connections/", json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_connections(
        self, client, db_session: Session, sample_connection_data: dict
    ):
        """测试获取连接列表"""
        connection_create = ConnectionCreate(**sample_connection_data)
        connection_crud.create_connection(db=db_session, connection=connection_create)

        response = client.get("/api/v1/connections/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_connections_empty(self, client):
        """测试获取空连接列表"""
        response = client.get("/api/v1/connections/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_connection_by_id(
        self, client, db_session: Session, sample_connection_data: dict
    ):
        """测试通过ID获取连接"""
        connection_create = ConnectionCreate(**sample_connection_data)
        created = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        response = client.get(f"/api/v1/connections/{created.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == created.id
        assert data["name"] == created.name

    def test_get_connection_not_found(self, client):
        """测试获取不存在的连接"""
        response = client.get("/api/v1/connections/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_connection_success(
        self,
        client,
        db_session: Session,
        sample_connection_data: dict,
        mock_mysql_connector,
    ):
        """测试成功更新连接"""
        connection_create = ConnectionCreate(**sample_connection_data)
        created = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        update_data = ConnectionUpdate(name="更新后的名称", port=3307)

        response = client.put(
            f"/api/v1/connections/{created.id}", json=update_data.model_dump()
        )

        if response.status_code != status.HTTP_200_OK:
            print(f"ERROR: Update failed with status {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "更新后的名称"
        assert data["port"] == 3307

    def test_update_connection_not_found(self, client):
        """测试更新不存在的连接"""
        update_data = ConnectionUpdate(name="测试更新")

        response = client.put("/api/v1/connections/999", json=update_data.model_dump())

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_connection_success(
        self, client, db_session: Session, sample_connection_data: dict
    ):
        """测试成功删除连接"""
        connection_create = ConnectionCreate(**sample_connection_data)
        created = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        response = client.delete(f"/api/v1/connections/{created.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        verify_deleted = client.get(f"/api/v1/connections/{created.id}")
        assert verify_deleted.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_connection_not_found(self, client):
        """测试删除不存在的连接"""
        response = client.delete("/api/v1/connections/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_connections_with_pagination(
        self, client, db_session: Session, sample_connection_data: dict
    ):
        """测试分页获取连接列表"""
        for i in range(5):
            data = sample_connection_data.copy()
            data["name"] = f"连接{i}"
            connection_create = ConnectionCreate(**data)
            connection_crud.create_connection(
                db=db_session, connection=connection_create
            )

        response = client.get("/api/v1/connections/?skip=1&limit=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_connection_response_structure(
        self, client, db_session: Session, sample_connection_data: dict
    ):
        """测试连接响应结构"""
        connection_create = ConnectionCreate(**sample_connection_data)
        created = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        response = client.get(f"/api/v1/connections/{created.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        required_fields = [
            "id",
            "name",
            "host",
            "port",
            "username",
            "is_active",
            "created_at",
            "updated_at",
        ]
        for field in required_fields:
            assert field in data

    def test_connection_with_password_encryption(
        self,
        client,
        db_session: Session,
        sample_connection_data: dict,
        mock_mysql_connector,
    ):
        """测试密码加密存储"""
        connection_create = ConnectionCreate(**sample_connection_data)
        created = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        assert created.password_encrypted is not None
        assert created.password_encrypted == sample_connection_data["password"]

    def test_connection_default_values(self, client, db_session: Session):
        """测试连接字段默认值"""
        minimal_data = {
            "name": "最小连接",
            "host": "127.0.0.1",
            "port": 3306,
            "username": "root",
            "password": "password",
        }
        connection_create = ConnectionCreate(**minimal_data)
        created = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        response = client.get(f"/api/v1/connections/{created.id}")
        data = response.json()

        assert data["connection_pool_size"] == 10
        assert data["is_active"] is True
