"""
测试 SQL 注入防护功能
"""

import pytest
from app.routers.slow_query import validate_sql_for_explain


class TestSQLInjectionProtection:
    """SQL 注入防护测试"""

    def test_safe_select_query(self):
        """测试安全的 SELECT 查询"""
        safe_queries = [
            "SELECT * FROM users",
            "SELECT id, name FROM users WHERE id = 1",
            "SELECT COUNT(*) FROM orders",
            "  SELECT * FROM products  ",  # 带空格
        ]
        for sql in safe_queries:
            assert validate_sql_for_explain(sql) is True, f"应该通过: {sql}"

    def test_unsafe_insert_query(self):
        """测试危险的 INSERT 查询"""
        unsafe_queries = [
            "INSERT INTO users VALUES (1, 'hacker')",
            "INSERT INTO users SELECT * FROM other_table",
        ]
        for sql in unsafe_queries:
            assert validate_sql_for_explain(sql) is False, f"应该拒绝: {sql}"

    def test_unsafe_update_query(self):
        """测试危险的 UPDATE 查询"""
        unsafe_queries = [
            "UPDATE users SET password = 'hacked'",
            "UPDATE accounts SET balance = 0",
        ]
        for sql in unsafe_queries:
            assert validate_sql_for_explain(sql) is False, f"应该拒绝: {sql}"

    def test_unsafe_delete_query(self):
        """测试危险的 DELETE 查询"""
        unsafe_queries = [
            "DELETE FROM users",
            "DELETE FROM accounts WHERE 1=1",
        ]
        for sql in unsafe_queries:
            assert validate_sql_for_explain(sql) is False, f"应该拒绝: {sql}"

    def test_unsafe_drop_query(self):
        """测试危险的 DROP 查询"""
        unsafe_queries = [
            "DROP TABLE users",
            "DROP DATABASE mysql",
        ]
        for sql in unsafe_queries:
            assert validate_sql_for_explain(sql) is False, f"应该拒绝: {sql}"

    def test_sql_with_dangerous_keywords_in_strings(self):
        """测试字符串中包含危险关键词的安全查询"""
        # 字符串中的关键词不应触发警告
        safe_queries = [
            "SELECT * FROM logs WHERE message = 'DELETE operation recorded'",
            "SELECT * FROM audit WHERE action = 'DROP COLUMN attempted'",
        ]
        for sql in safe_queries:
            assert validate_sql_for_explain(sql) is True, f"应该通过: {sql}"

    def test_empty_sql(self):
        """测试空 SQL"""
        assert validate_sql_for_explain("") is False
        assert validate_sql_for_explain("   ") is False
        assert validate_sql_for_explain(None) is False

    def test_non_select_statements(self):
        """测试非 SELECT 语句"""
        non_select_queries = [
            "EXPLAIN SELECT * FROM users",  # 以 EXPLAIN 开头不是 SELECT
            "SHOW TABLES",
            "DESCRIBE users",
            "SET @var = 1",
        ]
        for sql in non_select_queries:
            assert validate_sql_for_explain(sql) is False, f"应该拒绝: {sql}"

    def test_complex_safe_query(self):
        """测试复杂但安全的查询"""
        safe_queries = [
            """
            SELECT u.id, u.name, COUNT(o.id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.created_at > '2024-01-01'
            GROUP BY u.id, u.name
            HAVING COUNT(o.id) > 0
            ORDER BY order_count DESC
            LIMIT 10
            """,
            "SELECT * FROM (SELECT id FROM users) AS subquery",
        ]
        for sql in safe_queries:
            assert validate_sql_for_explain(sql) is True, f"应该通过: {sql}"
