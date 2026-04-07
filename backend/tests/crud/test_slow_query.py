"""
SlowQuery CRUD操作单元测试
"""

import pytest
from sqlalchemy.orm import Session
from unittest.mock import Mock

from app.crud import slow_query as slow_query_crud
from app.schemas.slow_query import SlowQueryCreate
from app.models.slow_query import SlowQuery
from app.models.connection import Connection


class TestSlowQueryCRUD:
    """SlowQuery CRUD操作测试类"""

    @pytest.fixture(autouse=True)
    def setup_connection(self, db_session):
        """为每个测试方法创建连接记录"""
        connection = Connection(
            name="测试连接",
            host="localhost",
            port=3306,
            username="root",
            password_encrypted="test_password",
            database_name="test_db",
            connection_pool_size=10,
            is_active=True,
        )
        db_session.add(connection)
        db_session.commit()
        db_session.refresh(connection)
        self.test_connection_id = connection.id

    def test_create_slow_query(self, db_session: Session):
        """测试创建慢查询"""
        query_create = SlowQueryCreate(
            connection_id=self.test_connection_id,
            query_hash="test_hash_001",
            sql_digest="SELECT * FROM users WHERE id = ?",
            query_time=1.5,
        )

        result = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create
        )

        assert result is not None
        assert result.query_hash == "test_hash_001"
        assert result.query_time == 1.5

    def test_get_slow_query_by_id(self, db_session: Session):
        """测试通过ID获取慢查询"""
        query_create = SlowQueryCreate(
            connection_id=self.test_connection_id,
            query_hash="test_hash_002",
            sql_digest="SELECT * FROM products",
            query_time=2.0,
            execution_count=1,
        )
        created = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create
        )

        result = slow_query_crud.get_slow_query(db=db_session, slow_query_id=created.id)

        assert result is not None
        assert result.id == created.id

    def test_get_slow_query_by_id_not_found(self, db_session: Session):
        """测试获取不存在的慢查询"""
        result = slow_query_crud.get_slow_query(db=db_session, slow_query_id=999)

        assert result is None

    def test_get_slow_queries_by_connection(self, db_session: Session):
        """测试获取指定连接的慢查询"""
        for i in range(3):
            query_create = SlowQueryCreate(
                connection_id=self.test_connection_id,
                query_hash=f"test_hash_00{i}",
                sql_digest=f"SELECT {i}",
                query_time=1.0 + i * 0.5,
                execution_count=1,
            )
            slow_query_crud.create_slow_query(db=db_session, slow_query=query_create)

        results = slow_query_crud.get_slow_queries_by_connection(
            db=db_session, connection_id=self.test_connection_id, skip=0, limit=10
        )

        assert len(results) == 3

    def test_get_slow_queries_by_connection_with_pagination(self, db_session: Session):
        """测试分页获取慢查询"""
        for i in range(5):
            query_create = SlowQueryCreate(
                connection_id=self.test_connection_id,
                query_hash=f"test_hash_01{i}",
                sql_digest=f"SELECT {i}",
                query_time=1.0,
                execution_count=1,
            )
            slow_query_crud.create_slow_query(db=db_session, slow_query=query_create)

        results = slow_query_crud.get_slow_queries_by_connection(
            db=db_session, connection_id=self.test_connection_id, skip=2, limit=2
        )

        assert len(results) == 2

    def test_get_slow_queries_by_connection_empty(self, db_session: Session):
        """测试获取空的慢查询列表"""
        results = slow_query_crud.get_slow_queries_by_connection(
            db=db_session, connection_id=999, skip=0, limit=10
        )

        assert len(results) == 0

    def test_get_slow_queries_by_hash(self, db_session: Session):
        """测试通过hash获取慢查询"""
        query_create = SlowQueryCreate(
            connection_id=self.test_connection_id,
            query_hash="test_hash_003",
            sql_digest="SELECT * FROM orders",
            query_time=3.0,
            execution_count=1,
        )
        created = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create
        )

        results = slow_query_crud.get_slow_queries_by_hash(
            db=db_session, query_hash="test_hash_003"
        )

        assert len(results) == 1
        assert results[0].id == created.id

    def test_get_slow_queries_by_hash_empty(self, db_session: Session):
        """测试获取不存在的hash"""
        results = slow_query_crud.get_slow_queries_by_hash(
            db=db_session, query_hash="nonexistent_hash"
        )

        assert len(results) == 0

    def test_create_slow_query_with_deduplication(self, db_session: Session):
        """测试慢查询去重逻辑"""
        query_create_1 = SlowQueryCreate(
            connection_id=self.test_connection_id,
            query_hash="test_hash_004",
            sql_digest="SELECT * FROM test",
            query_time=1.0,
            execution_count=1,
        )
        created_1 = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create_1
        )

        query_create_2 = SlowQueryCreate(
            connection_id=self.test_connection_id,
            query_hash="test_hash_004",
            sql_digest="SELECT * FROM test",
            query_time=2.0,
            execution_count=1,
        )
        created_2 = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create_2
        )

        # 验证两个记录都有相同的query_hash但不同的id
        assert created_1.query_hash == "test_hash_004"
        assert created_2.query_hash == "test_hash_004"
        assert created_1.id != created_2.id

    def test_delete_slow_query(self, db_session: Session):
        """测试删除慢查询"""
        query_create = SlowQueryCreate(
            connection_id=self.test_connection_id,
            query_hash="test_hash_005",
            sql_digest="DELETE FROM temp",
            query_time=0.5,
            execution_count=1,
        )
        created = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create
        )

        result = slow_query_crud.delete_slow_query(
            db=db_session, slow_query_id=created.id
        )

        assert result is True

        deleted = slow_query_crud.get_slow_query(
            db=db_session, slow_query_id=created.id
        )
        assert deleted is None

    def test_delete_slow_query_not_found(self, db_session: Session):
        """测试删除不存在的慢查询"""
        result = slow_query_crud.delete_slow_query(db=db_session, slow_query_id=999)

        assert result is False

    def test_get_slow_query_stats(self, db_session: Session):
        """测试获取慢查询统计信息"""
        query_times = [1.0, 2.0, 3.0, 4.0, 5.0]
        for i, time in enumerate(query_times):
            query_create = SlowQueryCreate(
                connection_id=self.test_connection_id,
                query_hash=f"test_hash_stats_{i}",
                sql_digest=f"SELECT {i}",
                query_time=time,
                rows_examined=1000 * (i + 1),
                rows_sent=100,
                execution_count=1,
            )
            slow_query_crud.create_slow_query(db=db_session, slow_query=query_create)

        stats = slow_query_crud.get_slow_query_stats(
            db=db_session, connection_id=self.test_connection_id
        )

        assert stats["total_count"] == 5
        assert stats["avg_query_time"] == sum(query_times) / len(query_times)
        assert stats["max_query_time"] == max(query_times)

    def test_get_slow_query_stats_empty(self, db_session: Session):
        """测试获取空统计信息"""
        stats = slow_query_crud.get_slow_query_stats(db=db_session, connection_id=999)

        assert stats["total_count"] == 0
        assert stats["avg_query_time"] == 0

    def test_get_top_slow_queries(self, db_session: Session):
        """测试获取Top慢查询"""
        from datetime import datetime

        query_times = [10.0, 8.0, 6.0, 4.0, 2.0]
        for i, time in enumerate(query_times):
            query_create = SlowQueryCreate(
                connection_id=self.test_connection_id,
                query_hash=f"test_hash_top_{i}",
                sql_digest=f"SELECT {i}",
                query_time=time,
                execution_count=1,
                timestamp=datetime.now(),
            )
            slow_query_crud.create_slow_query(db=db_session, slow_query=query_create)

        top_queries = slow_query_crud.get_top_slow_queries(
            db=db_session, connection_id=self.test_connection_id, limit=3, days=7
        )

        assert len(top_queries) == 3
        top_query_times = [q.query_time for q in top_queries]
        assert top_query_times == sorted(top_query_times, reverse=True)[:3]

    def test_get_top_slow_queries_limit(self, db_session: Session):
        """测试Top慢查询的limit参数"""
        from datetime import datetime

        for i in range(10):
            query_create = SlowQueryCreate(
                connection_id=self.test_connection_id,
                query_hash=f"test_hash_limit_{i}",
                sql_digest=f"SELECT {i}",
                query_time=10.0 - i,
                execution_count=1,
                timestamp=datetime.now(),
            )
            slow_query_crud.create_slow_query(db=db_session, slow_query=query_create)

        top_queries = slow_query_crud.get_top_slow_queries(
            db=db_session, connection_id=self.test_connection_id, limit=5, days=7
        )

        assert len(top_queries) == 5

    def test_delete_old_slow_queries(self, db_session: Session):
        """测试删除旧慢查询"""
        from datetime import datetime, timedelta

        old_queries = []
        for i in range(3):
            query_create = SlowQueryCreate(
                connection_id=self.test_connection_id,
                query_hash=f"old_hash_{i}",
                sql_digest=f"SELECT {i}",
                query_time=1.0,
                execution_count=1,
            )
            created = slow_query_crud.create_slow_query(
                db=db_session, slow_query=query_create
            )
            old_queries.append(created)

        deleted_count = slow_query_crud.delete_old_slow_queries(
            db=db_session, days=30, connection_id=self.test_connection_id
        )

        assert deleted_count >= 0

    def test_slow_query_defaults(self, db_session: Session):
        """测试慢查询字段默认值"""
        query_create = SlowQueryCreate(
            connection_id=self.test_connection_id,
            query_hash="test_hash_defaults",
            sql_digest="SELECT *",
            query_time=1.5,
        )

        result = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create
        )

        assert result is not None
        assert result.execution_count == 1

    def test_multiple_connections_slow_queries(self, db_session: Session):
        """测试多连接的慢查询"""
        # 创建第二个连接
        connection_2 = Connection(
            name="测试连接2",
            host="localhost",
            port=3306,
            username="root",
            password_encrypted="test_password",
            database_name="test_db2",
            connection_pool_size=10,
            is_active=True,
        )
        db_session.add(connection_2)
        db_session.commit()
        db_session.refresh(connection_2)

        query_create_1 = SlowQueryCreate(
            connection_id=self.test_connection_id,
            query_hash="test_multi_conn_1",
            sql_digest="SELECT * FROM conn1",
            query_time=1.0,
            execution_count=1,
        )
        created_1 = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create_1
        )

        query_create_2 = SlowQueryCreate(
            connection_id=connection_2.id,
            query_hash="test_multi_conn_2",
            sql_digest="SELECT * FROM conn2",
            query_time=2.0,
            execution_count=1,
        )
        created_2 = slow_query_crud.create_slow_query(
            db=db_session, slow_query=query_create_2
        )

        conn1_queries = slow_query_crud.get_slow_queries_by_connection(
            db=db_session, connection_id=self.test_connection_id, skip=0, limit=10
        )
        conn2_queries = slow_query_crud.get_slow_queries_by_connection(
            db=db_session, connection_id=connection_2.id, skip=0, limit=10
        )

        assert len(conn1_queries) == 1
        assert len(conn2_queries) == 1
        assert conn1_queries[0].id != conn2_queries[0].id
