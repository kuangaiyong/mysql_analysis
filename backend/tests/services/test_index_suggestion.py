"""
IndexSuggestionEngine服务单元测试 - 基于EXPLAIN的建议方法
"""

import pytest
from unittest.mock import Mock, patch

from app.services.index_suggestion import IndexSuggestionEngine


class TestIndexSuggestionEngineExplain:
    """IndexSuggestionEngine基于EXPLAIN的建议方法测试"""

    def setup_method(self):
        self.engine = IndexSuggestionEngine()

    def test_extract_where_columns_simple(self):
        sql = "SELECT * FROM users WHERE name = 'test'"
        columns = self.engine._extract_where_columns(sql)
        assert "name" in columns

    def test_extract_where_columns_multiple(self):
        sql = "SELECT * FROM users WHERE name = 'test' AND age > 18"
        columns = self.engine._extract_where_columns(sql)
        assert "name" in columns
        assert "age" in columns

    def test_extract_where_columns_with_table_prefix(self):
        sql = "SELECT * FROM users u WHERE u.name = 'test'"
        columns = self.engine._extract_where_columns(sql, "u")
        assert "name" in columns

    def test_extract_where_columns_no_where(self):
        sql = "SELECT * FROM users"
        columns = self.engine._extract_where_columns(sql)
        assert columns == []

    def test_extract_order_by_columns_simple(self):
        sql = "SELECT * FROM users ORDER BY created_at DESC"
        columns = self.engine._extract_order_by_columns(sql)
        assert "created_at" in columns

    def test_extract_order_by_columns_multiple(self):
        sql = "SELECT * FROM users ORDER BY created_at DESC, name ASC"
        columns = self.engine._extract_order_by_columns(sql)
        assert "created_at" in columns
        assert "name" in columns

    def test_extract_order_by_columns_no_order(self):
        sql = "SELECT * FROM users"
        columns = self.engine._extract_order_by_columns(sql)
        assert columns == []

    def test_extract_group_by_columns_simple(self):
        sql = "SELECT category, COUNT(*) FROM products GROUP BY category"
        columns = self.engine._extract_group_by_columns(sql)
        assert "category" in columns

    def test_extract_group_by_columns_multiple(self):
        sql = (
            "SELECT category, status, COUNT(*) FROM products GROUP BY category, status"
        )
        columns = self.engine._extract_group_by_columns(sql)
        assert "category" in columns
        assert "status" in columns

    def test_extract_group_by_columns_no_group(self):
        sql = "SELECT * FROM users"
        columns = self.engine._extract_group_by_columns(sql)
        assert columns == []

    def test_extract_table_name(self):
        sql = "SELECT * FROM users WHERE id = 1"
        table = self.engine._extract_table_name(sql)
        assert table == "users"

    def test_extract_table_name_with_alias(self):
        sql = "SELECT * FROM orders o WHERE o.id = 1"
        table = self.engine._extract_table_name(sql)
        assert table == "orders"

    def test_generate_composite_index_suggestion(self):
        suggestion = self.engine._generate_composite_index_suggestion(
            "users", ["name", "age"]
        )
        assert suggestion is not None
        assert suggestion["type"] == "composite_index"
        assert suggestion["table"] == "users"
        assert "name" in suggestion["columns"]
        assert "age" in suggestion["columns"]
        assert "CREATE INDEX" in suggestion["sql"]

    def test_generate_composite_index_suggestion_single_column(self):
        suggestion = self.engine._generate_composite_index_suggestion("users", ["name"])
        assert suggestion is None

    def test_generate_index_recommendations_with_explain_full_scan(self):
        mock_connector = Mock()
        mock_connector.execute_query.return_value = [
            {
                "table": "users",
                "type": "ALL",
                "possible_keys": None,
                "key": None,
                "Extra": "",
                "rows": 10000,
            }
        ]

        sql = "SELECT * FROM users WHERE name = 'test'"
        recommendations = self.engine.generate_index_recommendations_with_explain(
            sql, mock_connector
        )

        assert len(recommendations) >= 1
        assert any(r["type"] == "missing_index" for r in recommendations)
        assert any("全表扫描" in r["reason"] for r in recommendations)
        assert any("CREATE INDEX" in r["sql"] for r in recommendations)

    def test_generate_index_recommendations_with_filesort(self):
        mock_connector = Mock()
        mock_connector.execute_query.return_value = [
            {
                "table": "users",
                "type": "range",
                "possible_keys": "idx_name",
                "key": "idx_name",
                "Extra": "Using where; Using filesort",
                "rows": 100,
            }
        ]

        sql = "SELECT * FROM users WHERE name = 'test' ORDER BY created_at"
        recommendations = self.engine.generate_index_recommendations_with_explain(
            sql, mock_connector
        )

        assert any(
            "filesort" in r["reason"].lower() or "排序" in r["reason"]
            for r in recommendations
        )

    def test_generate_index_recommendations_with_temporary(self):
        mock_connector = Mock()
        mock_connector.execute_query.return_value = [
            {
                "table": "orders",
                "type": "ALL",
                "possible_keys": None,
                "key": None,
                "Extra": "Using temporary; Using filesort",
                "rows": 5000,
            }
        ]

        sql = "SELECT status, COUNT(*) FROM orders GROUP BY status"
        recommendations = self.engine.generate_index_recommendations_with_explain(
            sql, mock_connector
        )

        assert any("临时表" in r["reason"] for r in recommendations)

    def test_generate_index_recommendations_unused_index(self):
        mock_connector = Mock()
        mock_connector.execute_query.return_value = [
            {
                "table": "users",
                "type": "ALL",
                "possible_keys": "idx_name,idx_email",
                "key": None,
                "Extra": "",
                "rows": 10000,
            }
        ]

        sql = "SELECT * FROM users WHERE name = 'test'"
        recommendations = self.engine.generate_index_recommendations_with_explain(
            sql, mock_connector
        )

        assert any(r["type"] == "unused_index" for r in recommendations)

    def test_generate_index_recommendations_error_handling(self):
        mock_connector = Mock()
        mock_connector.execute_query.side_effect = Exception("Connection error")

        sql = "SELECT * FROM users WHERE name = 'test'"
        recommendations = self.engine.generate_index_recommendations_with_explain(
            sql, mock_connector
        )

        assert len(recommendations) == 1
        assert recommendations[0]["type"] == "error"

    def test_generate_index_recommendations_simple_query(self):
        mock_connector = Mock()
        mock_connector.execute_query.return_value = [
            {
                "table": "users",
                "type": "ALL",
                "possible_keys": None,
                "key": None,
                "Extra": "",
                "rows": 1000,
            }
        ]

        sql = "SELECT * FROM users WHERE name = 'test'"
        recommendations = self.engine.generate_index_recommendations_with_explain(
            sql, mock_connector
        )

        assert len(recommendations) >= 1
        rec = recommendations[0]
        assert rec["type"] == "missing_index"
        assert rec["table"] == "users"
        assert rec["priority"] == "high"
        assert "CREATE INDEX" in rec["sql"]

    def test_generate_index_recommendations_composite(self):
        mock_connector = Mock()
        mock_connector.execute_query.return_value = [
            {
                "table": "users",
                "type": "ALL",
                "possible_keys": None,
                "key": None,
                "Extra": "",
                "rows": 1000,
            }
        ]

        sql = "SELECT * FROM users WHERE name = 'test' AND age > 18"
        recommendations = self.engine.generate_index_recommendations_with_explain(
            sql, mock_connector
        )

        composite_recs = [r for r in recommendations if r["type"] == "composite_index"]
        assert len(composite_recs) >= 1


class TestIndexSuggestionEngineHelpers:
    """辅助方法测试"""

    def setup_method(self):
        self.engine = IndexSuggestionEngine()

    def test_extract_where_columns_with_in_clause(self):
        sql = "SELECT * FROM users WHERE id IN (1, 2, 3)"
        columns = self.engine._extract_where_columns(sql)
        assert "id" in columns

    def test_extract_where_columns_with_like(self):
        sql = "SELECT * FROM users WHERE name LIKE '%test%'"
        columns = self.engine._extract_where_columns(sql)
        assert "name" in columns

    def test_extract_where_columns_with_between(self):
        sql = "SELECT * FROM users WHERE age BETWEEN 18 AND 30"
        columns = self.engine._extract_where_columns(sql)
        assert "age" in columns

    def test_extract_order_by_with_table_prefix(self):
        sql = "SELECT * FROM users u ORDER BY u.created_at"
        columns = self.engine._extract_order_by_columns(sql)
        assert "created_at" in columns

    def test_extract_group_by_with_table_prefix(self):
        sql = "SELECT u.status, COUNT(*) FROM users u GROUP BY u.status"
        columns = self.engine._extract_group_by_columns(sql)
        assert "status" in columns

    def test_generate_create_index_sql_single(self):
        sql = self.engine.generate_create_index_sql(
            table_name="users",
            index_name="idx_name",
            column_names=["name"],
        )
        assert "CREATE INDEX" in sql
        assert "idx_name" in sql
        assert "users" in sql
        assert "name" in sql

    def test_generate_create_index_sql_composite(self):
        sql = self.engine.generate_create_index_sql(
            table_name="users",
            index_name="idx_composite",
            column_names=["name", "age"],
        )
        assert "CREATE INDEX" in sql
        assert "name" in sql
        assert "age" in sql

    def test_generate_create_index_sql_unique(self):
        sql = self.engine.generate_create_index_sql(
            table_name="users",
            index_name="idx_email",
            column_names=["email"],
            unique=True,
        )
        assert "CREATE UNIQUE INDEX" in sql


class TestIndexSuggestionEngineNewMethods:
    """新增方法测试"""

    def setup_method(self):
        self.engine = IndexSuggestionEngine()

    def test_analyze_covering_index_basic(self):
        mock_connector = Mock()
        mock_connector.execute_query.return_value = []

        sql = "SELECT id, name FROM users WHERE status = 1"
        result = self.engine.analyze_covering_index(sql, mock_connector)

        assert result["covering_possible"] is True
        assert "status" in result["columns"]
        assert "CREATE INDEX" in result["suggested_index"]

    def test_analyze_covering_index_no_table(self):
        mock_connector = Mock()

        sql = "SELECT 1"
        result = self.engine.analyze_covering_index(sql, mock_connector)

        assert result["covering_possible"] is False

    def test_analyze_covering_index_with_star(self):
        mock_connector = Mock()
        mock_connector.execute_query.return_value = []

        sql = "SELECT * FROM users WHERE status = 1"
        result = self.engine.analyze_covering_index(sql, mock_connector)

        assert result["covering_possible"] is True
        assert "status" in result["columns"]

    def test_analyze_selectivity_high(self):
        mock_connector = Mock()
        mock_connector.execute_query.side_effect = [
            [{"total": 1000}],
            [{"Cardinality": 800, "Column_name": "id"}],
        ]

        selectivity = self.engine.analyze_selectivity("users", "id", mock_connector)

        assert 0.0 <= selectivity <= 1.0
        assert selectivity == 0.8

    def test_analyze_selectivity_empty_table(self):
        mock_connector = Mock()
        mock_connector.execute_query.return_value = [{"total": 0}]

        selectivity = self.engine.analyze_selectivity("users", "id", mock_connector)

        assert selectivity == 0.0

    def test_analyze_selectivity_no_index(self):
        mock_connector = Mock()
        mock_connector.execute_query.side_effect = [
            [{"total": 1000}],
            [],
            [{"distinct_count": 500}],
        ]

        selectivity = self.engine.analyze_selectivity("users", "name", mock_connector)

        assert selectivity == 0.5

    def test_suggest_prefix_index_varchar_long(self):
        result = self.engine._suggest_prefix_index("description", "varchar(500)")

        assert result["suggested"] is True
        assert result["prefix_length"] > 0
        assert "VARCHAR" in result["reason"]

    def test_suggest_prefix_index_varchar_short(self):
        result = self.engine._suggest_prefix_index("code", "varchar(20)")

        assert result["suggested"] is False

    def test_suggest_prefix_index_text(self):
        result = self.engine._suggest_prefix_index("content", "text")

        assert result["suggested"] is True
        assert result["prefix_length"] == 30
        assert "必须使用前缀索引" in result["reason"]

    def test_suggest_prefix_index_int(self):
        result = self.engine._suggest_prefix_index("id", "int")

        assert result["suggested"] is False

    def test_extract_select_columns_basic(self):
        sql = "SELECT id, name, email FROM users"
        columns = self.engine._extract_select_columns(sql)

        assert "id" in columns
        assert "name" in columns
        assert "email" in columns

    def test_extract_select_columns_with_star(self):
        sql = "SELECT * FROM users"
        columns = self.engine._extract_select_columns(sql)

        assert columns == []

    def test_extract_join_columns_basic(self):
        sql = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        columns = self.engine._extract_join_columns(sql)

        assert "id" in columns or "user_id" in columns

    def test_get_table_structure_with_connector(self):
        mock_connector = Mock()
        mock_connector.execute_query.side_effect = [
            [
                {
                    "TABLE_NAME": "users",
                    "TABLE_ROWS": 1000,
                    "DATA_LENGTH": 1024,
                    "INDEX_LENGTH": 512,
                    "TABLE_COMMENT": "",
                }
            ],
            [
                {
                    "TABLE_NAME": "users",
                    "COLUMN_NAME": "id",
                    "COLUMN_TYPE": "int",
                    "IS_NULLABLE": "NO",
                    "COLUMN_KEY": "PRI",
                    "COLUMN_DEFAULT": None,
                    "COLUMN_COMMENT": "",
                }
            ],
        ]

        result = self.engine._get_table_structure(None, 1, mock_connector)

        assert "tables" in result
        assert "columns_by_table" in result

    def test_get_table_structure_without_connector(self):
        result = self.engine._get_table_structure(None, 1, None)

        assert result == {}
