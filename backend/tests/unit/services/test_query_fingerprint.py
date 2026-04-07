"""
查询指纹服务测试
"""

import pytest
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.services.query_fingerprint import QueryFingerprintService
from app.models.slow_query import SlowQuery
from app.models.query_fingerprint import QueryFingerprint


class TestQueryFingerprintService:
    """测试查询指纹服务"""

    def test_normalize_sql_basic(self):
        """测试基本SQL规范化"""
        sql = "SELECT * FROM users WHERE id = 123"
        result = QueryFingerprintService.normalize_sql(sql)
        assert "select" in result.lower()
        assert "from" in result.lower()
        assert "where" in result.lower()

    def test_normalize_sql_with_comments(self):
        """测试带注释的SQL规范化"""
        sql = """SELECT * FROM users -- get users
                 WHERE id = 123"""
        result = QueryFingerprintService.normalize_sql(sql)
        assert "select" in result.lower()

    def test_normalize_sql_with_literals(self):
        """测试带字面量的SQL规范化"""
        sql = "SELECT * FROM users WHERE name = 'John' AND age = 25"
        result = QueryFingerprintService.normalize_sql(sql)
        # 字面量应该被替换
        assert "?" in result or "'john'" not in result.lower()

    def test_generate_fingerprint_consistency(self):
        """测试指纹生成一致性"""
        sql1 = "SELECT * FROM users WHERE id = 123"
        sql2 = "SELECT * FROM users WHERE id = 456"

        fingerprint1 = QueryFingerprintService.generate_fingerprint(sql1)
        fingerprint2 = QueryFingerprintService.generate_fingerprint(sql2)

        # 相似的SQL应该产生相同的指纹
        assert fingerprint1 == fingerprint2

    def test_generate_fingerprint_difference(self):
        """测试不同SQL产生不同指纹"""
        sql1 = "SELECT * FROM users WHERE id = 123"
        sql2 = "SELECT * FROM orders WHERE id = 123"

        fingerprint1 = QueryFingerprintService.generate_fingerprint(sql1)
        fingerprint2 = QueryFingerprintService.generate_fingerprint(sql2)

        # 不同的SQL应该产生不同的指纹
        assert fingerprint1 != fingerprint2

    def test_generate_fingerprint_length(self):
        """测试指纹长度"""
        sql = "SELECT * FROM users"
        fingerprint = QueryFingerprintService.generate_fingerprint(sql)

        # MD5哈希应该是32个字符
        assert len(fingerprint) == 32

    def test_identify_slow_query_pattern_empty(self):
        """测试空慢查询列表"""
        patterns = QueryFingerprintService.identify_slow_query_pattern([])
        assert patterns == {}

    def test_identify_slow_query_pattern_single(self):
        """测试单个慢查询"""
        slow_query = SlowQuery(
            connection_id=1,
            query_hash="abc123",
            full_sql="SELECT * FROM users WHERE id = 123",
            sql_digest="SELECT * FROM users",
            query_time=2.5,
            rows_examined=1000,
            rows_sent=500,
            timestamp=datetime.now(),
        )

        patterns = QueryFingerprintService.identify_slow_query_pattern([slow_query])

        assert len(patterns) == 1

    def test_identify_slow_query_pattern_multiple_same(self):
        """测试多个相同模式的慢查询"""
        now = datetime.now()
        slow_queries = [
            SlowQuery(
                connection_id=1,
                query_hash="abc123",
                full_sql=f"SELECT * FROM users WHERE id = {i}",
                sql_digest="SELECT * FROM users",
                query_time=float(i),
                rows_examined=1000,
                rows_sent=500,
                timestamp=now,
            )
            for i in range(1, 4)
        ]

        patterns = QueryFingerprintService.identify_slow_query_pattern(slow_queries)

        # 相同的查询模式应该被合并
        assert len(patterns) == 1

    def test_analyze_trends_empty(self):
        """测试空模式的趋势分析"""
        trends = QueryFingerprintService.analyze_trends({})
        assert trends == []

    def test_analyze_trends_with_data(self):
        """测试有数据的趋势分析"""
        patterns = {
            "hash1": {
                "normalized_sql": "select * from users",
                "count": 5,
                "avg_query_time": 2.0,
                "max_query_time": 5.0,
                "min_query_time": 1.0,
                "rows_examined": 5000,
                "first_seen": datetime.now() - timedelta(days=1),
                "last_seen": datetime.now(),
            }
        }

        trends = QueryFingerprintService.analyze_trends(patterns, days=7)

        assert len(trends) == 1
        assert trends[0]["fingerprint_hash"] == "hash1"
        assert trends[0]["count"] == 5
        assert trends[0]["trend"] == "stable"
        assert trends[0]["is_high_frequency"] == False
        assert trends[0]["is_slow"] == True  # avg_query_time > 1.0

    def test_analyze_trends_single_vs_stable(self):
        """测试单次查询vs稳定趋势"""
        now = datetime.now()
        patterns = {
            "hash1": {
                "normalized_sql": "select * from users",
                "count": 1,
                "avg_query_time": 1.0,
                "max_query_time": 1.0,
                "min_query_time": 1.0,
                "rows_examined": 100,
                "first_seen": now,
                "last_seen": now,
            },
            "hash2": {
                "normalized_sql": "select * from orders",
                "count": 15,
                "avg_query_time": 0.5,
                "max_query_time": 1.0,
                "min_query_time": 0.1,
                "rows_examined": 1000,
                "first_seen": now - timedelta(days=2),
                "last_seen": now,
            },
        }

        trends = QueryFingerprintService.analyze_trends(patterns, days=7)

        assert len(trends) == 2

        # 检查排序
        assert trends[0]["fingerprint_hash"] == "hash1"  # last_seen更晚

    def test_create_fingerprints_empty(self, db_session):
        """测试创建空指纹列表"""
        result = QueryFingerprintService.create_fingerprints(db_session, 1, {})
        assert result == []

    def test_create_fingerprints_with_data(self, db_session):
        """测试创建指纹记录"""
        patterns = {
            "hash1": {
                "normalized_sql": "select * from users",
                "count": 10,
                "avg_query_time": 2.0,
                "max_query_time": 5.0,
                "min_query_time": 1.0,
                "rows_examined": 1000,
                "first_seen": datetime.now(),
                "last_seen": datetime.now(),
            }
        }

        fingerprints = QueryFingerprintService.create_fingerprints(
            db_session, 1, patterns
        )

        assert len(fingerprints) == 1
        assert fingerprints[0].fingerprint_hash == "hash1"
        assert fingerprints[0].connection_id == 1
        assert fingerprints[0].execution_count == 10

    def test_extract_table_name_from_select(self):
        """测试从SELECT提取表名"""
        sql = "SELECT * FROM users WHERE id = 1"
        table_name = QueryFingerprintService._extract_table_name(sql)
        assert table_name == "users"

    def test_extract_table_name_from_update(self):
        """测试从UPDATE提取表名"""
        sql = "UPDATE users SET name = 'test' WHERE id = 1"
        table_name = QueryFingerprintService._extract_table_name(sql)
        assert table_name == "users"

    def test_extract_table_name_unknown(self):
        """测试无法识别的表名"""
        sql = "SELECT 1"
        table_name = QueryFingerprintService._extract_table_name(sql)
        assert table_name == "unknown"

    def test_update_fingerprint_id_for_slow_queries(self, db_session, test_connection):
        """测试更新慢查询的fingerprint_id"""
        # 创建慢查询
        slow_query = SlowQuery(
            connection_id=test_connection.id,
            query_hash="abc123",
            full_sql="SELECT * FROM users WHERE id = 1",
            query_time=2.5,
            timestamp=datetime.now(),
        )
        db_session.add(slow_query)
        db_session.commit()
        db_session.refresh(slow_query)

        # 创建指纹映射
        fingerprint_map = {
            QueryFingerprintService.generate_fingerprint(
                "SELECT * FROM users WHERE id = 1"
            ): 100
        }

        updated_count = QueryFingerprintService.update_fingerprint_id_for_slow_queries(
            db_session, test_connection.id, fingerprint_map
        )

        assert updated_count == 1
        db_session.refresh(slow_query)
        assert slow_query.fingerprint_id == 100

    def test_get_trends_empty(self, db_session, test_connection):
        """测试空趋势数据"""
        service = QueryFingerprintService()
        trends = service.get_trends(db_session, test_connection.id, days=7)

        assert trends == []

    def test_get_trends_with_data(self, db_session, test_connection):
        """测试获取趋势数据"""
        # 创建慢查询
        slow_query = SlowQuery(
            connection_id=test_connection.id,
            query_hash="abc123",
            full_sql="SELECT * FROM users WHERE id = 1",
            query_time=2.5,
            timestamp=datetime.now(),
        )
        db_session.add(slow_query)
        db_session.commit()

        service = QueryFingerprintService()
        trends = service.get_trends(db_session, test_connection.id, days=7)

        assert len(trends) == 1
        assert "fingerprint_hash" in trends[0]
        assert "normalized_sql" in trends[0]

    def test_generate_fingerprints_integration(self, db_session, test_connection):
        """测试完整的指纹生成流程"""
        # 创建多个慢查询
        slow_queries = [
            SlowQuery(
                connection_id=test_connection.id,
                query_hash=f"hash{i}",
                full_sql=f"SELECT * FROM users WHERE id = {i}",
                query_time=float(i),
                timestamp=datetime.now() - timedelta(hours=i),
            )
            for i in range(1, 4)
        ]
        for sq in slow_queries:
            db_session.add(sq)
        db_session.commit()

        service = QueryFingerprintService()
        fingerprints = service.generate_fingerprints(db_session, test_connection.id)

        # 所有相似查询应该生成一个指纹
        assert len(fingerprints) == 1

    def test_get_fingerprint_not_found(self, db_session):
        """测试获取不存在的指纹"""
        service = QueryFingerprintService()
        result = service.get_fingerprint(db_session, 99999)

        assert result is None

    def test_get_fingerprint_found(self, db_session, test_connection):
        """测试获取存在的指纹"""
        # 创建指纹
        fingerprint = QueryFingerprint(
            fingerprint_hash="test_hash",
            normalized_sql="select * from users",
            connection_id=test_connection.id,
            execution_count=10,
            avg_query_time=2.0,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        db_session.add(fingerprint)
        db_session.commit()
        db_session.refresh(fingerprint)

        service = QueryFingerprintService()
        result = service.get_fingerprint(db_session, fingerprint.id)

        assert result is not None
        assert result.fingerprint_hash == "test_hash"

    def test_list_fingerprints_empty(self, db_session, test_connection):
        """测试空指纹列表"""
        service = QueryFingerprintService()
        fingerprints = service.list_fingerprints(db_session, test_connection.id)

        assert fingerprints == []

    def test_list_fingerprints_with_data(self, db_session, test_connection):
        """测试有数据的指纹列表"""
        # 创建指纹
        fingerprint = QueryFingerprint(
            fingerprint_hash="test_hash",
            normalized_sql="select * from users",
            connection_id=test_connection.id,
            execution_count=10,
            avg_query_time=2.0,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
        )
        db_session.add(fingerprint)
        db_session.commit()

        service = QueryFingerprintService()
        fingerprints = service.list_fingerprints(db_session, test_connection.id)

        assert len(fingerprints) == 1

    def test_list_fingerprints_pagination(self, db_session, test_connection):
        """测试指纹列表分页"""
        # 创建多个指纹
        for i in range(5):
            fingerprint = QueryFingerprint(
                fingerprint_hash=f"hash{i}",
                normalized_sql=f"select * from table{i}",
                connection_id=test_connection.id,
                execution_count=i,
                avg_query_time=float(i),
                first_seen=datetime.now(),
                last_seen=datetime.now(),
            )
            db_session.add(fingerprint)
        db_session.commit()

        service = QueryFingerprintService()
        fingerprints = service.list_fingerprints(
            db_session, test_connection.id, limit=2, offset=0
        )

        assert len(fingerprints) == 2
