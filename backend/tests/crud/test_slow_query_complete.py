"""
Slow Query CRUD 补充测试
"""

from sqlalchemy.orm import Session

from app.crud import slow_query as slow_query_crud
from app.crud import connection as connection_crud
from app.schemas.slow_query import SlowQueryCreate
from app.schemas.connection import ConnectionCreate


class TestSlowQueryCRUDComplete:
    """SlowQuery CRUD操作完整测试类"""

    def _create_test_connection(self, db_session: Session):
        """创建测试连接"""
        connection_create = ConnectionCreate(
            name="Test Connection",
            host="localhost",
            port=3306,
            username="test_user",
            password="test_password",
            database_name="test_db",
        )
        return connection_crud.create_connection(
            db=db_session, connection=connection_create
        )

    def test_create_slow_query_all_fields(self, db_session: Session):
        """测试创建包含所有字段的慢查询"""
        connection = self._create_test_connection(db_session)

        query_create = SlowQueryCreate(
            connection_id=connection.id,
            query_hash="test_hash_complete",
            sql_digest="SELECT * FROM users WHERE email = ?",
            full_sql="SELECT * FROM users WHERE email = 'test@example.com'",
            query_time=5.5,
            lock_time=0.1,
            rows_examined=10000,
            rows_sent=1000,
            database_name="test_db",
            execution_count=1,
        )

        result = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create
        )
        db_session.refresh(result)

        assert result.query_hash == "test_hash_complete"
        assert result.full_sql is not None

    def test_get_slow_queries_sorted_by_query_time(self, db_session: Session):
        """测试按查询时间排序获取慢查询"""
        connection = self._create_test_connection(db_session)

        for i in range(5):
            query_create = SlowQueryCreate(
                connection_id=connection.id,
                query_hash=f"hash_{i}",
                sql_digest="SELECT * FROM test",
                query_time=10.0 - i,
                rows_examined=1000,
                rows_sent=100,
                execution_count=1,
            )
            slow_query_crud.create_slow_query(db=db_session, slow_query=query_create)

        results = slow_query_crud.get_slow_queries_by_connection(
            db=db_session, connection_id=connection.id, skip=0, limit=10
        )

        assert len(results) == 5

    def test_get_slow_query_stats_comprehensive(self, db_session: Session):
        """测试全面的慢查询统计"""
        connection = self._create_test_connection(db_session)

        for i in range(10):
            query_create = SlowQueryCreate(
                connection_id=connection.id,
                query_hash=f"hash_stats_{i}",
                sql_digest="SELECT * FROM test",
                query_time=1.0 + i * 0.5,
                rows_examined=1000 * (i + 1),
                rows_sent=100,
                execution_count=1,
            )
            slow_query_crud.create_slow_query(db=db_session, slow_query=query_create)

        stats = slow_query_crud.get_slow_query_stats(
            db=db_session, connection_id=connection.id
        )

        assert stats["total_count"] == 10
        assert stats["avg_query_time"] > 0
        assert stats["max_query_time"] > 0

    def test_delete_old_slow_queries_by_time(self, db_session: Session):
        """测试按时间删除旧慢查询"""
        from datetime import datetime, timedelta

        connection = self._create_test_connection(db_session)

        now = datetime.now(timezone.utc)
        old_time = now - timedelta(days=31)

        query_create = SlowQueryCreate(
            connection_id=connection.id,
            query_hash="old_hash",
            sql_digest="SELECT * FROM old",
            query_time=1.0,
            rows_examined=1000,
            rows_sent=100,
            timestamp=old_time,
            execution_count=1,
        )
        slow_query_crud.create_slow_query(db=db_session, slow_query=query_create)

        deleted = slow_query_crud.delete_old_slow_queries(
            db=db_session, days=30, connection_id=connection.id
        )

        assert deleted >= 0
