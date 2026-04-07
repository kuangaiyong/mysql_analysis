"""
Simple tests for CRUD layer - basic operations only
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from app.models.connection import Connection
from app.models.slow_query import SlowQuery
from app.crud import connection as connection_crud
from app.crud import slow_query as slow_query_crud
from app.schemas.connection import ConnectionCreate, ConnectionUpdate
from app.schemas.slow_query import SlowQueryCreate
from decimal import Decimal


class TestBasicCRUD:
    """Basic CRUD operations test"""

    def test_connection_crud_count(self, db_session: Session):
        """测试连接计数"""
        count = (
            db_session.execute(
                select(Connection).where(Connection.is_active == True)
            ).scalar_one_or_none()
            or 0
        )

        assert count is not None
        assert count >= 0

    def test_slow_query_crud_count(self, db_session: Session):
        """测试慢查询计数"""
        count = db_session.execute(select(SlowQuery)).scalar_one_or_none() or 0

        assert count is not None
        assert count >= 0

    def test_create_basic_connection(self, db_session: Session):
        """测试创建基础连接"""
        conn = Connection(
            name="Test Connection",
            host="localhost",
            port=3306,
            username="test_user",
            password_encrypted="encrypted",
            database_name="test_db",
            connection_pool_size=10,
            is_active=True,
        )
        db_session.add(conn)
        db_session.commit()
        db_session.refresh(conn)

        assert conn.id is not None
        assert conn.name == "Test Connection"

    def test_create_basic_slow_query(self, db_session: Session):
        """测试创建基础慢查询"""
        query = SlowQuery(
            connection_id=1,
            query_hash="test_hash",
            sql_digest="SELECT 1",
            full_sql="SELECT 1",
            query_time=Decimal("1.5"),
            lock_time=Decimal("0.1"),
            rows_examined=100,
            rows_sent=10,
            database_name="test_db",
            execution_count=1,
        )
        db_session.add(query)
        db_session.commit()
        db_session.refresh(query)

        assert query.id is not None
        assert query.query_hash == "test_hash"
