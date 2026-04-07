"""
SQL优化规则单元测试

为每个规则编写测试用例，验证规则能正确检测SQL反模式和正常SQL。
"""

import pytest

from app.services.rule_engine import (
    get_rule_engine,
    reset_rule_engine,
    AnalysisContext,
    RuleCategory,
    Severity,
)
from app.services.sql_rules import get_default_rules


@pytest.fixture(autouse=True)
def setup_rules():
    """每个测试前重置并重新注册规则"""
    reset_rule_engine()
    engine = get_rule_engine()
    for rule in get_default_rules():
        engine.register_rule(rule)
    yield
    reset_rule_engine()


def get_triggered_rule_ids(sql: str) -> list:
    """辅助函数：获取SQL触发的规则ID列表"""
    engine = get_rule_engine()
    results = engine.analyze(sql)
    return [r.rule_id for r in results]


# ==============================================================================
# IDX Rules - 索引相关规则测试
# ==============================================================================


class TestIDX001SelectStar:
    """测试 IDX.001: 避免 SELECT *"""

    def test_detects_select_star(self):
        """检测 SELECT * 模式"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users")
        assert "IDX.001" in rule_ids

    def test_detects_select_star_with_where(self):
        """检测带WHERE的 SELECT *"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE id = 1")
        assert "IDX.001" in rule_ids

    def test_passes_specific_columns(self):
        """指定列名时通过"""
        rule_ids = get_triggered_rule_ids("SELECT id, name FROM users")
        assert "IDX.001" not in rule_ids

    def test_passes_select_count(self):
        """SELECT COUNT(*) 不触发"""
        rule_ids = get_triggered_rule_ids("SELECT COUNT(*) FROM users")
        assert "IDX.001" not in rule_ids

    def test_case_insensitive(self):
        """大小写不敏感"""
        rule_ids = get_triggered_rule_ids("select * from users")
        assert "IDX.001" in rule_ids


class TestIDX002WhereFunction:
    """测试 IDX.002: WHERE子句避免对列使用函数"""

    def test_detects_upper_function(self):
        """检测 UPPER 函数"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE UPPER(name) = 'JOHN'"
        )
        assert "IDX.002" in rule_ids

    def test_detects_date_function(self):
        """检测 DATE 函数"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM orders WHERE DATE(created_at) = '2024-01-01'"
        )
        assert "IDX.002" in rule_ids

    def test_detects_lower_function(self):
        """检测 LOWER 函数"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE LOWER(email) = 'test@example.com'"
        )
        assert "IDX.002" in rule_ids

    def test_passes_function_on_value(self):
        """函数应用于值而非列时通过"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE name = UPPER('john')"
        )
        assert "IDX.002" not in rule_ids

    def test_passes_no_function(self):
        """无函数时通过"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name = 'JOHN'")
        assert "IDX.002" not in rule_ids


class TestIDX003OrCondition:
    """测试 IDX.003: 注意OR条件可能导致索引失效"""

    def test_detects_or_different_columns(self):
        """检测不同列的OR条件"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE name = 'John' OR email = 'john@example.com'"
        )
        assert "IDX.003" in rule_ids

    def test_passes_or_same_column(self):
        """同一列的OR条件不触发"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE status = 1 OR status = 2"
        )
        assert "IDX.003" not in rule_ids

    def test_passes_no_or(self):
        """无OR条件时通过"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE name = 'John' AND status = 1"
        )
        assert "IDX.003" not in rule_ids


# ==============================================================================
# COL Rules - 列相关规则测试
# ==============================================================================


class TestCOL001NullComparison:
    """测试 COL.001: 正确使用NULL比较"""

    def test_detects_equals_null(self):
        """检测 = NULL 错误比较"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name = NULL")
        assert "COL.001" in rule_ids

    def test_detects_equals_null_with_space(self):
        """检测带空格的 = NULL"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name =  NULL")
        assert "COL.001" in rule_ids

    def test_passes_is_null(self):
        """使用 IS NULL 时通过"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name IS NULL")
        assert "COL.001" not in rule_ids

    def test_passes_is_not_null(self):
        """使用 IS NOT NULL 时通过"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name IS NOT NULL")
        assert "COL.001" not in rule_ids

    def test_passes_string_comparison(self):
        """字符串比较不触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name = 'NULL'")
        assert "COL.001" not in rule_ids


class TestCOL002ImplicitTypeConversion:
    """测试 COL.002: 避免隐式类型转换"""

    def test_detects_id_string_comparison(self):
        """检测 id 列与字符串比较"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE id = '123'")
        assert "COL.002" in rule_ids

    def test_detects_amount_string_comparison(self):
        """检测 amount 列与字符串比较"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM orders WHERE amount = '100.00'"
        )
        assert "COL.002" in rule_ids

    def test_detects_price_string_comparison(self):
        """检测 price 列与字符串比较"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM products WHERE price = '99.99'"
        )
        assert "COL.002" in rule_ids

    def test_passes_numeric_comparison(self):
        """数值比较不触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE id = 123")
        assert "COL.002" not in rule_ids

    def test_passes_string_column_string_value(self):
        """字符串列与字符串值比较不触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name = 'John'")
        assert "COL.002" not in rule_ids


# ==============================================================================
# CLA Rules - 子句相关规则测试
# ==============================================================================


class TestCLA001OrderByLimit:
    """测试 CLA.001: 注意ORDER BY与LIMIT的组合"""

    def test_detects_order_by_limit(self):
        """检测 ORDER BY + LIMIT 组合"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT 10"
        )
        assert "CLA.001" in rule_ids

    def test_detects_order_by_limit_with_offset(self):
        """检测带 OFFSET 的 ORDER BY + LIMIT"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users ORDER BY id LIMIT 10 OFFSET 20"
        )
        assert "CLA.001" in rule_ids

    def test_passes_order_by_only(self):
        """只有 ORDER BY 不触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users ORDER BY created_at")
        assert "CLA.001" not in rule_ids

    def test_passes_limit_only(self):
        """只有 LIMIT 不触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users LIMIT 10")
        assert "CLA.001" not in rule_ids


class TestCLA002GroupBy:
    """测试 CLA.002: GROUP BY列建议有索引"""

    def test_detects_group_by(self):
        """检测 GROUP BY"""
        rule_ids = get_triggered_rule_ids(
            "SELECT status, COUNT(*) FROM users GROUP BY status"
        )
        assert "CLA.002" in rule_ids

    def test_detects_group_by_multiple_columns(self):
        """检测多列 GROUP BY"""
        rule_ids = get_triggered_rule_ids(
            "SELECT status, role, COUNT(*) FROM users GROUP BY status, role"
        )
        assert "CLA.002" in rule_ids

    def test_passes_no_group_by(self):
        """无 GROUP BY 时不触发"""
        rule_ids = get_triggered_rule_ids("SELECT status, COUNT(*) FROM users")
        assert "CLA.002" not in rule_ids


class TestCLA003Distinct:
    """测试 CLA.003: 检查DISTINCT是否必要"""

    def test_detects_distinct(self):
        """检测 SELECT DISTINCT"""
        rule_ids = get_triggered_rule_ids("SELECT DISTINCT name FROM users")
        assert "CLA.003" in rule_ids

    def test_detects_distinct_multiple_columns(self):
        """检测多列 DISTINCT"""
        rule_ids = get_triggered_rule_ids("SELECT DISTINCT name, email FROM users")
        assert "CLA.003" in rule_ids

    def test_passes_no_distinct(self):
        """无 DISTINCT 时不触发"""
        rule_ids = get_triggered_rule_ids("SELECT name FROM users")
        assert "CLA.003" not in rule_ids


class TestCLA004SubqueryInWhere:
    """测试 CLA.004: 避免WHERE子句中的子查询"""

    def test_detects_subquery_in_where(self):
        """检测 WHERE 子句中的子查询"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        )
        assert "CLA.004" in rule_ids

    def test_detects_subquery_with_comparison(self):
        """检测带比较的子查询"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE salary > (SELECT AVG(salary) FROM users)"
        )
        assert "CLA.004" in rule_ids

    def test_passes_no_subquery(self):
        """无子查询时不触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE status = 1")
        assert "CLA.004" not in rule_ids

    def test_passes_join_instead_of_subquery(self):
        """使用 JOIN 替代子查询时不触发"""
        rule_ids = get_triggered_rule_ids(
            "SELECT u.* FROM users u JOIN orders o ON u.id = o.user_id"
        )
        assert "CLA.004" not in rule_ids


class TestCLA005Union:
    """测试 CLA.005: 考虑使用UNION ALL替代UNION"""

    def test_detects_union(self):
        """检测 UNION（不带 ALL）"""
        rule_ids = get_triggered_rule_ids(
            "SELECT id FROM users UNION SELECT id FROM admins"
        )
        assert "CLA.005" in rule_ids

    def test_passes_union_all(self):
        """UNION ALL 不触发"""
        rule_ids = get_triggered_rule_ids(
            "SELECT id FROM users UNION ALL SELECT id FROM admins"
        )
        assert "CLA.005" not in rule_ids

    def test_passes_no_union(self):
        """无 UNION 时不触发"""
        rule_ids = get_triggered_rule_ids("SELECT id FROM users")
        assert "CLA.005" not in rule_ids


# ==============================================================================
# KWR Rules - 关键字相关规则测试
# ==============================================================================


class TestKWR001NotIn:
    """测试 KWR.001: 避免使用NOT IN"""

    def test_detects_not_in(self):
        """检测 NOT IN"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE status NOT IN (1, 2, 3)"
        )
        assert "KWR.001" in rule_ids

    def test_detects_not_in_subquery(self):
        """检测带子查询的 NOT IN"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM orders)"
        )
        assert "KWR.001" in rule_ids

    def test_passes_in_clause(self):
        """IN 子句不触发"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE status IN (1, 2, 3)"
        )
        assert "KWR.001" not in rule_ids

    def test_passes_not_exists(self):
        """NOT EXISTS 不触发"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE NOT EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id)"
        )
        assert "KWR.001" not in rule_ids


class TestKWR002LikeLeadingWildcard:
    """测试 KWR.002: 避免LIKE以通配符开头"""

    def test_detects_leading_percent(self):
        """检测 LIKE '%xxx' 模式"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name LIKE '%John'")
        assert "KWR.002" in rule_ids

    def test_detects_leading_underscore(self):
        """检测 LIKE '_xxx' 模式"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name LIKE '_ohn'")
        assert "KWR.002" in rule_ids

    def test_detects_both_wildcards(self):
        """检测 LIKE '%xxx%' 模式"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE name LIKE '%John%'"
        )
        assert "KWR.002" in rule_ids

    def test_passes_trailing_wildcard(self):
        """LIKE 'xxx%' 不触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name LIKE 'John%'")
        assert "KWR.002" not in rule_ids

    def test_passes_no_wildcard(self):
        """无通配符时不触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name LIKE 'John'")
        assert "KWR.002" not in rule_ids


class TestKWR003HavingNoGroupBy:
    """测试 KWR.003: HAVING应与GROUP BY配合使用"""

    def test_detects_having_without_group_by(self):
        """检测没有 GROUP BY 的 HAVING"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users HAVING status = 1")
        assert "KWR.003" in rule_ids

    def test_passes_having_with_group_by(self):
        """有 GROUP BY 的 HAVING 不触发"""
        rule_ids = get_triggered_rule_ids(
            "SELECT status, COUNT(*) FROM users GROUP BY status HAVING COUNT(*) > 10"
        )
        assert "KWR.003" not in rule_ids

    def test_passes_no_having(self):
        """无 HAVING 时不触发"""
        rule_ids = get_triggered_rule_ids(
            "SELECT status, COUNT(*) FROM users GROUP BY status"
        )
        assert "KWR.003" not in rule_ids


# ==============================================================================
# ERN Rules - 错误相关规则测试
# ==============================================================================


class TestERN001NoWhereInUpdateDelete:
    """测试 ERN.001: UPDATE/DELETE必须有WHERE条件"""

    def test_detects_update_without_where(self):
        """检测无 WHERE 的 UPDATE"""
        rule_ids = get_triggered_rule_ids("UPDATE users SET status = 1")
        assert "ERN.001" in rule_ids

    def test_detects_delete_without_where(self):
        """检测无 WHERE 的 DELETE"""
        rule_ids = get_triggered_rule_ids("DELETE FROM users")
        assert "ERN.001" in rule_ids

    def test_passes_update_with_where(self):
        """有 WHERE 的 UPDATE 不触发"""
        rule_ids = get_triggered_rule_ids("UPDATE users SET status = 1 WHERE id = 1")
        assert "ERN.001" not in rule_ids

    def test_passes_delete_with_where(self):
        """有 WHERE 的 DELETE 不触发"""
        rule_ids = get_triggered_rule_ids("DELETE FROM users WHERE id = 1")
        assert "ERN.001" not in rule_ids

    def test_passes_select_statement(self):
        """SELECT 语句不触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users")
        assert "ERN.001" not in rule_ids


class TestERN002AmbiguousColumn:
    """测试 ERN.002: 避免歧义列引用"""

    def test_detects_ambiguous_column_in_join(self):
        """检测 JOIN 中的歧义列引用"""
        # 使用逗号连接的多表查询
        rule_ids = get_triggered_rule_ids(
            "SELECT id, name FROM users, orders WHERE users.id = orders.user_id"
        )
        assert "ERN.002" in rule_ids

    def test_passes_qualified_columns_in_join(self):
        """使用表名限定的列不触发"""
        rule_ids = get_triggered_rule_ids(
            "SELECT users.id, users.name FROM users JOIN orders ON users.id = orders.user_id"
        )
        assert "ERN.002" not in rule_ids

    def test_passes_single_table(self):
        """单表查询不触发"""
        rule_ids = get_triggered_rule_ids("SELECT id, name FROM users")
        assert "ERN.002" not in rule_ids

    def test_passes_select_star_in_join(self):
        """SELECT * 在 JOIN 中不触发歧义检查"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        )
        assert "ERN.002" not in rule_ids


# ==============================================================================
# 综合测试
# ==============================================================================


class TestMultipleRules:
    """测试多个规则同时触发的情况"""

    def test_select_star_with_null_comparison(self):
        """SELECT * 和 = NULL 同时触发"""
        rule_ids = get_triggered_rule_ids("SELECT * FROM users WHERE name = NULL")
        assert "IDX.001" in rule_ids
        assert "COL.001" in rule_ids

    def test_update_without_where_with_function(self):
        """UPDATE 无 WHERE 和其他问题"""
        rule_ids = get_triggered_rule_ids("UPDATE users SET name = UPPER(name)")
        assert "ERN.001" in rule_ids

    def test_complex_bad_query(self):
        """复杂问题SQL触发多个规则"""
        rule_ids = get_triggered_rule_ids(
            "SELECT * FROM users WHERE UPPER(name) LIKE '%John%' AND id = '123' AND status NOT IN (1, 2)"
        )
        # 应该触发 SELECT *、函数使用、类型转换、LIKE通配符、NOT IN
        assert "IDX.001" in rule_ids
        assert "IDX.002" in rule_ids
        assert "COL.002" in rule_ids
        assert "KWR.001" in rule_ids
        assert "KWR.002" in rule_ids


class TestRuleRegistration:
    """测试规则注册"""

    def test_all_rules_registered(self):
        """验证所有15个规则都已注册"""
        engine = get_rule_engine()
        rules = engine.get_all_rules()
        rule_ids = {r.rule_id for r in rules}

        expected_ids = {
            "IDX.001",
            "IDX.002",
            "IDX.003",
            "COL.001",
            "COL.002",
            "CLA.001",
            "CLA.002",
            "CLA.003",
            "CLA.004",
            "CLA.005",
            "KWR.001",
            "KWR.002",
            "KWR.003",
            "ERN.001",
            "ERN.002",
        }

        assert rule_ids == expected_ids

    def test_rule_count(self):
        """验证规则数量"""
        engine = get_rule_engine()
        assert engine.rule_count == 15


class TestRuleCategories:
    """测试规则分类"""

    def test_idx_category_count(self):
        """验证 IDX 分类规则数量"""
        engine = get_rule_engine()
        idx_rules = [
            r for r in engine.get_all_rules() if r.category == RuleCategory.IDX
        ]
        assert len(idx_rules) == 3

    def test_col_category_count(self):
        """验证 COL 分类规则数量"""
        engine = get_rule_engine()
        col_rules = [
            r for r in engine.get_all_rules() if r.category == RuleCategory.COL
        ]
        assert len(col_rules) == 2

    def test_cla_category_count(self):
        """验证 CLA 分类规则数量"""
        engine = get_rule_engine()
        cla_rules = [
            r for r in engine.get_all_rules() if r.category == RuleCategory.CLA
        ]
        assert len(cla_rules) == 5

    def test_kwr_category_count(self):
        """验证 KWR 分类规则数量"""
        engine = get_rule_engine()
        kwr_rules = [
            r for r in engine.get_all_rules() if r.category == RuleCategory.KWR
        ]
        assert len(kwr_rules) == 3

    def test_ern_category_count(self):
        """验证 ERN 分类规则数量"""
        engine = get_rule_engine()
        ern_rules = [
            r for r in engine.get_all_rules() if r.category == RuleCategory.ERN
        ]
        assert len(ern_rules) == 2


class TestRuleResultStructure:
    """测试规则结果结构"""

    def test_result_has_required_fields(self):
        """验证结果包含必要字段"""
        engine = get_rule_engine()
        results = engine.analyze("SELECT * FROM users")
        assert len(results) > 0

        result = results[0]
        assert result.rule_name is not None
        assert result.rule_id is not None
        assert result.category is not None
        assert result.severity is not None
        assert result.description is not None
        assert result.suggestion is not None

    def test_result_to_dict(self):
        """验证结果可序列化为字典"""
        engine = get_rule_engine()
        results = engine.analyze("SELECT * FROM users")
        result = results[0]

        result_dict = result.to_dict()
        assert "rule_name" in result_dict
        assert "rule_id" in result_dict
        assert "category" in result_dict
        assert "severity" in result_dict
        assert "description" in result_dict
        assert "suggestion" in result_dict

    def test_results_sorted_by_severity(self):
        """验证结果按严重级别排序"""
        engine = get_rule_engine()
        # 这个SQL会触发多个规则
        results = engine.analyze(
            "SELECT * FROM users WHERE id = NULL AND name LIKE '%test'"
        )

        if len(results) > 1:
            # L5 (COL.001) > L3 (IDX.001) > L5 (KWR.002)
            # 验证排序（严重级别高的在前）
            severity_order = {
                Severity.L9: 0,
                Severity.L8: 1,
                Severity.L7: 2,
                Severity.L6: 3,
                Severity.L5: 4,
                Severity.L4: 5,
                Severity.L3: 6,
                Severity.L2: 7,
                Severity.L1: 8,
                Severity.L0: 9,
            }
            for i in range(len(results) - 1):
                current_order = severity_order.get(results[i].severity, 10)
                next_order = severity_order.get(results[i + 1].severity, 10)
                assert current_order <= next_order
