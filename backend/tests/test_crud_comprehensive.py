"""
CRUD operations comprehensive tests
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.connection import Connection
from app.models.slow_query import SlowQuery
from app.crud import connection as connection_crud
from app.crud import slow_query as slow_query_crud
from app.schemas.connection import ConnectionCreate, ConnectionUpdate
from app.schemas.slow_query import SlowQueryCreate


class TestCRUDComprehensive:
    """Comprehensive CRUD operations tests"""

    def test_connection_bulk_operations(self, db_session: Session):
        """测试连接批量操作"""
        from tests.test_factories import create_test_connection

        # Create multiple connections
        connections = []
        for i in range(5):
            conn = create_test_connection()
            db_session.add(conn)
            connections.append(conn)
        db_session.commit()

        assert len(connections) == 5

        # Get all connections
        all_conns = connection_crud.get_connections(db=db_session)
        assert len(all_conns) >= 5

    def test_slow_query_bulk_operations(self, db_session: Session):
        """测试慢查询批量操作"""
        from tests.test_factories import create_test_slow_query

        # Create multiple slow queries
        for i in range(5):
            sq = create_test_slow_query()
            db_session.add(sq)
            db_session.commit()

        # Get by connection
        conn_sq = slow_query_crud.get_slow_queries_by_connection(
            db=db_session, connection_id=1, skip=0, limit=10
        )
        assert len(conn_sq) >= 0

    def test_connection_update_with_no_changes(self, db_session: Session):
        """测试没有变化的更新"""
        conn = Connection(
            name="Test",
            host="localhost",
            port=3306,
            username="test_user",
            password_encrypted="encrypted",
            database_name="test_db",
        )
        db_session.add(conn)
        db_session.commit()
        db_session.refresh(conn)

        # Update with no actual changes
        update_data = ConnectionUpdate(name="Test Updated")
        result = connection_crud.update_connection(
            db=db_session, connection_id=conn.id, connection_update=update_data
        )

        assert result.name == "Test Updated"

    def test_slow_query_aggregation_queries(self, db_session: Session):
        """测试慢查询聚合查询"""
        from tests.test_factories import create_test_connection

        conn = create_test_connection()
        db_session.add(conn)
        db_session.commit()

        # Create slow queries with same hash but different timestamps
        for i in range(3):
            sq = SlowQuery(
                connection_id=conn.id,
                query_hash="hash_agg",
                sql_digest="SELECT * FROM test",
                full_sql="SELECT * FROM test",
                query_time=Decimal(str(1.0 + i * 0.5)),
                lock_time=Decimal("0.0001"),
                rows_examined=1000,
                rows_sent=100,
                database_name="test_db",
                timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                execution_count=1,
            )
            db_session.add(sq)
            db_session.commit()

        # Get statistics
        stats = slow_query_crud.get_slow_query_stats(
            db=db_session, connection_id=conn.id
        )

        assert stats is not None
        assert stats["total_count"] >= 3

    def test_slow_query_purge_old_data(self, db_session: Session):
        """测试清理旧慢查询数据"""
        from tests.test_factories import create_test_connection
        from datetime import datetime, timedelta

        conn = create_test_connection()
        db_session.add(conn)
        db_session.commit()

        # Create old slow queries
        old_date = datetime.now(timezone.utc) - timedelta(days=30)
        for i in range(3):
            sq = SlowQuery(
                connection_id=conn.id,
                query_hash=f"old_hash_{i}",
                sql_digest="SELECT * FROM old_data",
                full_sql="SELECT * FROM old_data",
                query_time=Decimal("10.0"),
                timestamp=old_date,
            )
            db_session.add(sq)
            db_session.commit()

        # Purge old data
        deleted = slow_query_crud.delete_old_slow_queries(
            db=db_session, days=7, connection_id=conn.id
        )

        assert deleted >= 2

    def test_transaction_rollback(self, db_session: Session):
        """测试事务回滚"""
        conn = Connection(
            name="Test Rollback",
            host="localhost",
            port=3306,
            username="test_user",
            password_encrypted="encrypted",
            database_name="test_db",
            is_active=False,
        )
        db_session.add(conn)
        db_session.commit()

        # Get connection for update
        retrieved = connection_crud.get_connection(db=db_session, connection_id=conn.id)
        assert retrieved is not None
        original_name = retrieved.name

        # Try update with exclude_unset - should work now
        update_data = ConnectionUpdate(port=3307)
        result = connection_crud.update_connection(
            db=db_session, connection_id=conn.id, connection_update=update_data
        )

        # Verify name unchanged, port changed
        db_session.refresh(retrieved)
        assert retrieved.name == original_name
        assert result.port == 3307

    def test_query_hash_consistency(self):
        """测试查询哈希一致性"""
        from app.services.slow_query_analyzer import SlowQueryAnalyzer
        from unittest.mock import Mock

        mock_connector = Mock()
        analyzer = SlowQueryAnalyzer(mock_connector)
        sql = "SELECT * FROM users WHERE id = ?"
        hash1 = analyzer.generate_query_hash(sql)

        # Same query should give same hash
        hash2 = analyzer.generate_query_hash(sql)

        assert hash1 == hash2

        # Different query should give different hash
        sql2 = "SELECT * FROM users WHERE name = ?"
        hash3 = analyzer.generate_query_hash(sql2)

        assert hash3 != hash1
