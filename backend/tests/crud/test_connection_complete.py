"""
Connection CRUD 补充测试
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.crud import connection as connection_crud
from app.models.connection import Connection
from app.schemas.connection import ConnectionCreate, ConnectionUpdate


class TestConnectionCRUDComplete:
    """Connection CRUD操作完整测试类"""

    def test_get_connections_pagination(self, db_session: Session):
        """测试分页获取连接"""
        for i in range(15):
            conn = Connection(
                name=f"Test Connection {i}",
                host="localhost",
                port=3306,
                username="test_user",
                password_encrypted="encrypted",
                database_name="test_db",
            )
            db_session.add(conn)
        db_session.commit()

        results = connection_crud.get_connections(db=db_session, skip=0, limit=10)
        assert len(results) == 10

    def test_get_connections_all(self, db_session: Session):
        """测试获取所有连接"""
        for i in range(3):
            conn = Connection(
                name=f"Test Connection {i}",
                host="localhost",
                port=3306,
                username="test_user",
                password_encrypted="encrypted",
                database_name="test_db",
            )
            db_session.add(conn)
        db_session.commit()

        results = connection_crud.get_connections(db=db_session, skip=0, limit=100)
        assert len(results) == 3

    def test_create_connection_all_fields(self, db_session: Session):
        """测试创建包含所有字段的连接"""
        connection_create = ConnectionCreate(
            name="Complete Connection",
            host="127.0.0.1",
            port=3307,
            username="admin",
            password="secret_password",
            database_name="mydb",
            connection_pool_size=20,
        )

        result = connection_crud.create_connection(
            db=db_session, connection=connection_create
        )
        db_session.refresh(result)

        assert result.name == "Complete Connection"
        assert result.port == 3307
        assert result.connection_pool_size == 20
        assert result.is_active is True

    def test_update_connection_all_fields(self, db_session: Session):
        """测试更新所有字段"""
        conn = Connection(
            name="Original",
            host="localhost",
            port=3306,
            username="test_user",
            password_encrypted="encrypted",
            database_name="test_db",
        )
        db_session.add(conn)
        db_session.commit()

        connection_update = ConnectionUpdate(
            name="Updated",
            host="newhost",
            port=3307,
            username="newuser",
            password="new_password",
            database_name="newdb",
            connection_pool_size=20,
        )

        result = connection_crud.update_connection(
            db=db_session, connection_id=conn.id, connection_update=connection_update
        )
        db_session.refresh(result)

        assert result.name == "Updated"

    def test_get_active_connections_only(self, db_session: Session):
        """测试只获取活跃连接"""
        active_conn = Connection(
            name="Active",
            host="localhost",
            port=3306,
            username="test_user",
            password_encrypted="encrypted",
            database_name="test_db",
            is_active=True,
        )
        inactive_conn = Connection(
            name="Inactive",
            host="localhost",
            port=3306,
            username="test_user",
            password_encrypted="encrypted",
            database_name="test_db",
            is_active=False,
        )
        db_session.add_all([active_conn, inactive_conn])
        db_session.commit()

        results = connection_crud.get_active_connections(db=db_session)
        assert len(results) == 1
        assert results[0].name == "Active"

    def test_get_active_connections_empty(self, db_session: Session):
        """测试没有活跃连接时"""
        results = connection_crud.get_active_connections(db=db_session)
        assert len(results) == 0
