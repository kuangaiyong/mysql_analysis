"""
Connection CRUD操作单元测试
"""

import pytest
from sqlalchemy.orm import Session

from app.crud import connection as connection_crud
from app.schemas.connection import ConnectionCreate, ConnectionUpdate
from app.models.connection import Connection


class TestConnectionCRUD:
    """Connection CRUD操作测试类"""

    def test_create_connection(self, db_session: Session):
        """测试创建连接"""
        connection_create = ConnectionCreate(
            name="测试连接",
            host="127.0.0.1",
            port=3306,
            username="root",
            password="test_password",
            database_name="test_db",
            connection_pool_size=10,
        )

        result = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        assert result is not None
        assert result.id is not None
        assert result.name == "测试连接"
        assert result.host == "127.0.0.1"
        assert result.port == 3306

    def test_get_connection(self, db_session: Session):
        """测试获取单个连接"""
        connection_create = ConnectionCreate(
            name="测试连接",
            host="127.0.0.1",
            port=3306,
            username="root",
            password="test_password",
            database_name="test_db",
        )
        created = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        result = connection_crud.get_connection(db=db_session, connection_id=created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == created.name

    def test_get_connection_not_found(self, db_session: Session):
        """测试获取不存在的连接"""
        result = connection_crud.get_connection(db=db_session, connection_id=999)

        assert result is None

    def test_get_connections(self, db_session: Session):
        """测试获取所有连接"""
        # 先创建一个连接
        connection_create = ConnectionCreate(
            name="测试连接",
            host="127.0.0.1",
            port=3306,
            username="root",
            password="test_password",
            database_name="test_db",
        )
        connection_crud.create_connection(db=db_session, connection=connection_create)

        results = connection_crud.get_connections(db=db_session, skip=0, limit=10)

        assert isinstance(results, list)
        assert len(results) >= 1

    def test_update_connection(self, db_session: Session):
        """测试更新连接"""
        connection_create = ConnectionCreate(
            name="测试连接",
            host="127.0.0.1",
            port=3306,
            username="root",
            password="test_password",
            database_name="test_db",
        )
        created = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        update_data = ConnectionUpdate(
            name="更新后的连接名称", port=3307, is_active=False
        )

        result = connection_crud.update_connection(
            db=db_session, connection_id=created.id, connection_update=update_data
        )

        assert result is not None
        assert result.name == "更新后的连接名称"
        assert result.port == 3307

    def test_update_connection_not_found(self, db_session: Session):
        """测试更新不存在的连接"""
        update_data = ConnectionUpdate(name="测试更新")

        result = connection_crud.update_connection(
            db=db_session, connection_id=999, connection_update=update_data
        )

        assert result is None

    def test_delete_connection(self, db_session: Session):
        """测试删除连接"""
        connection_create = ConnectionCreate(
            name="测试连接",
            host="127.0.0.1",
            port=3306,
            username="root",
            password="test_password",
            database_name="test_db",
        )
        created = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

        result = connection_crud.delete_connection(
            db=db_session, connection_id=created.id
        )

        assert result is True

        deleted = connection_crud.get_connection(
            db=db_session, connection_id=created.id
        )
        assert deleted is None

    def test_delete_connection_not_found(self, db_session: Session):
        """测试删除不存在的连接"""
        result = connection_crud.delete_connection(db=db_session, connection_id=999)

        assert result is False
