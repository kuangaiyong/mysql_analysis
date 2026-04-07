"""
SQL Rewriter 服务单元测试
"""

from app.services.sql_rewriter import SQLRewriter


class TestSQLRewriter:
    """SQL改写建议器测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.rewriter = SQLRewriter()

    def test_suggest_rewrite_empty_sql(self):
        """测试空SQL返回空建议"""
        suggestions = self.rewriter.suggest_rewrite("")
        assert suggestions == []

    def test_suggest_rewrite_none_sql(self):
        """测试None SQL返回空建议"""
        suggestions = self.rewriter.suggest_rewrite(None)
        assert suggestions == []

    def test_suggest_rewrite_whitespace_only(self):
        """测试仅空白字符的SQL返回空建议"""
        suggestions = self.rewriter.suggest_rewrite("   ")
        assert suggestions == []

    def test_subquery_to_join_basic(self):
        """测试基本子查询改写为JOIN"""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        suggestions = self.rewriter.suggest_rewrite(sql)

        assert len(suggestions) > 0
        subquery_suggestion = next(
            (s for s in suggestions if s["type"] == "subquery_to_join"), None
        )
        assert subquery_suggestion is not None
        assert subquery_suggestion["priority"] == "high"
        assert "JOIN" in subquery_suggestion["sql_after"]
        assert subquery_suggestion["sql_before"] == sql

    def test_subquery_to_join_with_columns(self):
        """测试带列名的子查询改写"""
        sql = "SELECT name, email FROM users WHERE id IN (SELECT user_id FROM orders)"
        suggestions = self.rewriter.suggest_rewrite(sql)

        subquery_suggestion = next(
            (s for s in suggestions if s["type"] == "subquery_to_join"), None
        )
        assert subquery_suggestion is not None
        assert "INNER JOIN" in subquery_suggestion["sql_after"]

    def test_no_subquery_detection(self):
        """测试不含子查询的SQL不触发子查询建议"""
        sql = "SELECT * FROM users WHERE id = 1"
        suggestions = self.rewriter.suggest_rewrite(sql)

        subquery_suggestion = next(
            (s for s in suggestions if s["type"] == "subquery_to_join"), None
        )
        assert subquery_suggestion is None

    def test_or_to_union_basic(self):
        """测试基本OR条件改写为UNION ALL"""
        sql = "SELECT * FROM users WHERE status = 'active' OR status = 'pending'"
        suggestions = self.rewriter.suggest_rewrite(sql)

        or_suggestion = next(
            (s for s in suggestions if s["type"] == "or_to_union"), None
        )
        assert or_suggestion is not None
        assert or_suggestion["priority"] == "medium"
        assert "UNION ALL" in or_suggestion["sql_after"]
        assert or_suggestion["sql_before"] == sql

    def test_or_to_union_multiple_conditions(self):
        """测试多个OR条件改写"""
        sql = "SELECT id, name FROM products WHERE category = 'A' OR category = 'B' OR category = 'C'"
        suggestions = self.rewriter.suggest_rewrite(sql)

        or_suggestion = next(
            (s for s in suggestions if s["type"] == "or_to_union"), None
        )
        assert or_suggestion is not None
        assert or_suggestion["sql_after"].count("UNION ALL") == 2

    def test_no_or_detection(self):
        """测试不含OR的SQL不触发OR建议"""
        sql = "SELECT * FROM users WHERE status = 'active'"
        suggestions = self.rewriter.suggest_rewrite(sql)

        or_suggestion = next(
            (s for s in suggestions if s["type"] == "or_to_union"), None
        )
        assert or_suggestion is None

    def test_detect_select_star(self):
        """测试检测SELECT *"""
        sql = "SELECT * FROM users"
        suggestions = self.rewriter.suggest_rewrite(sql)

        star_suggestion = next(
            (s for s in suggestions if s["type"] == "select_star"), None
        )
        assert star_suggestion is not None
        assert star_suggestion["priority"] == "low"
        assert star_suggestion["sql_after"] is None  # 不自动改写

    def test_no_select_star_detection(self):
        """测试不含SELECT *的SQL不触发建议"""
        sql = "SELECT id, name FROM users"
        suggestions = self.rewriter.suggest_rewrite(sql)

        star_suggestion = next(
            (s for s in suggestions if s["type"] == "select_star"), None
        )
        assert star_suggestion is None

    def test_detect_like_prefix_wildcard(self):
        """测试检测LIKE前缀通配符"""
        sql = "SELECT * FROM users WHERE name LIKE '%john%'"
        suggestions = self.rewriter.suggest_rewrite(sql)

        like_suggestion = next(
            (s for s in suggestions if s["type"] == "like_prefix_wildcard"), None
        )
        assert like_suggestion is not None
        assert like_suggestion["priority"] == "medium"
        assert "全文索引" in like_suggestion["description"]

    def test_like_without_prefix_wildcard(self):
        """测试不含前缀通配符的LIKE不触发建议"""
        sql = "SELECT * FROM users WHERE name LIKE 'john%'"
        suggestions = self.rewriter.suggest_rewrite(sql)

        like_suggestion = next(
            (s for s in suggestions if s["type"] == "like_prefix_wildcard"), None
        )
        assert like_suggestion is None

    def test_multiple_suggestions(self):
        """测试同时返回多个建议"""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders) AND name LIKE '%test%'"
        suggestions = self.rewriter.suggest_rewrite(sql)

        types = [s["type"] for s in suggestions]
        assert "subquery_to_join" in types
        assert "like_prefix_wildcard" in types
        assert "select_star" in types

    def test_suggestion_structure(self):
        """测试建议结构完整性"""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        suggestions = self.rewriter.suggest_rewrite(sql)

        for suggestion in suggestions:
            assert "type" in suggestion
            assert "priority" in suggestion
            assert "title" in suggestion
            assert "description" in suggestion
            assert "sql_before" in suggestion
            assert "expected_improvement" in suggestion

    def test_rewrite_subquery_to_join_method(self):
        """测试_rewrite_subquery_to_join方法"""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        result = self.rewriter._rewrite_subquery_to_join(sql)

        assert result is not None
        assert "INNER JOIN" in result
        assert "users" in result
        assert "orders" in result

    def test_rewrite_subquery_to_join_no_match(self):
        """测试_rewrite_subquery_to_join方法无匹配"""
        sql = "SELECT * FROM users WHERE id = 1"
        result = self.rewriter._rewrite_subquery_to_join(sql)

        assert result is None

    def test_rewrite_or_to_union_method(self):
        """测试_rewrite_or_to_union方法"""
        sql = "SELECT * FROM users WHERE status = 'A' OR status = 'B'"
        result = self.rewriter._rewrite_or_to_union(sql)

        assert result is not None
        assert "UNION ALL" in result

    def test_rewrite_or_to_union_no_match(self):
        """测试_rewrite_or_to_union方法无匹配"""
        sql = "SELECT * FROM users WHERE status = 'A'"
        result = self.rewriter._rewrite_or_to_union(sql)

        assert result is None

    def test_detect_select_star_method(self):
        """测试_detect_select_star方法"""
        assert self.rewriter._detect_select_star("SELECT * FROM users") is True
        assert self.rewriter._detect_select_star("SELECT id, name FROM users") is False

    def test_detect_like_prefix_wildcard_method(self):
        """测试_detect_like_prefix_wildcard方法"""
        assert (
            self.rewriter._detect_like_prefix_wildcard(
                "SELECT * FROM t WHERE name LIKE '%test%'"
            )
            is True
        )
        assert (
            self.rewriter._detect_like_prefix_wildcard(
                "SELECT * FROM t WHERE name LIKE 'test%'"
            )
            is False
        )

    def test_split_or_conditions(self):
        """测试_split_or_conditions方法"""
        result = self.rewriter._split_or_conditions("a = 1 OR b = 2 OR c = 3")
        assert len(result) == 3
        assert "a = 1" in result
        assert "b = 2" in result
        assert "c = 3" in result

    def test_split_or_conditions_with_parentheses(self):
        """测试_split_or_conditions方法处理括号"""
        result = self.rewriter._split_or_conditions("(a = 1 OR b = 2) OR c = 3")
        assert len(result) == 2

    def test_complex_sql_with_subquery_and_select_star(self):
        """测试复杂SQL：包含子查询和SELECT *"""
        sql = "SELECT * FROM orders WHERE user_id IN (SELECT id FROM users WHERE status = 'active')"
        suggestions = self.rewriter.suggest_rewrite(sql)

        types = [s["type"] for s in suggestions]
        assert "subquery_to_join" in types
        assert "select_star" in types

    def test_expected_improvement_values(self):
        """测试预期提升描述包含关键信息"""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        suggestions = self.rewriter.suggest_rewrite(sql)

        for suggestion in suggestions:
            assert suggestion["expected_improvement"] is not None
            assert len(suggestion["expected_improvement"]) > 0
