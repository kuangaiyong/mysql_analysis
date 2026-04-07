"""
SQL优化规则单元测试

测试15个核心SQL优化规则的检测功能。
"""

import pytest
from app.services.rule_engine import (
    get_rule_engine,
    reset_rule_engine,
    AnalysisContext,
    RuleCategory,
    Severity,
)
from app.services.sql_rules import (
    get_default_rules,
    IDX001_SelectStarRule,
    IDX002_WhereFunctionRule,
    IDX003_OrConditionRule,
    COL001_NullComparisonRule,
    COL002_ImplicitTypeConversionRule,
    CLA001_OrderByLimitRule,
    CLA002_GroupByNoIndexRule,
    CLA003_DistinctRule,
    CLA004_SubqueryInWhereRule,
    CLA005_UnionRule,
    KWR001_NotInRule,
    KWR002_LikeLeadingWildcardRule,
    KWR003_HavingNoGroupByRule,
    ERN001_NoWhereInUpdateDeleteRule,
    ERN002_AmbiguousColumnRule,
)


def register_all_rules():
    """注册所有规则到全局规则引擎"""
    engine = get_rule_engine()
    for rule in get_default_rules():
        engine.register_rule(rule)


@pytest.fixture(autouse=True)
def setup_rules():
    """每个测试前重置并重新注册规则"""
    reset_rule_engine()
    register_all_rules()
    yield
    reset_rule_engine()


class TestRuleEngineBasics:
    """规则引擎基础测试"""

    def test_register_all_rules(self):
        """测试注册所有规则"""
        engine = get_rule_engine()
        assert engine.rule_count == 15

    def test_get_all_rules(self):
        """测试获取所有规则"""
        engine = get_rule_engine()
        rules = engine.get_all_rules()
        rule_ids = [r.rule_id for r in rules]

        expected_ids = [
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
        ]
        for expected_id in expected_ids:
            assert expected_id in rule_ids


class TestIDX001SelectStar:
    """IDX.001: 避免使用 SELECT *"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users",
            "SELECT * FROM users WHERE id = 1",
            "select * from users",
        ],
    )
    def test_triggers_on_select_star(self, sql):
        """测试触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "IDX.001" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT id, name FROM users",
            "SELECT id, name FROM users WHERE id = 1",
        ],
    )
    def test_not_triggers_on_explicit_columns(self, sql):
        """测试不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "IDX.001" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = IDX001_SelectStarRule()
        assert rule.rule_id == "IDX.001"
        assert rule.severity == Severity.L3
        assert rule.category == RuleCategory.IDX


class TestIDX002WhereFunction:
    """IDX.002: WHERE子句避免对列使用函数"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE UPPER(name) = 'JOHN'",
            "SELECT * FROM users WHERE LOWER(email) = 'test@example.com'",
            "SELECT * FROM users WHERE DATE(created_at) = '2024-01-01'",
            "SELECT * FROM users WHERE YEAR(created_at) = 2024",
        ],
    )
    def test_triggers_on_function_usage(self, sql):
        """测试函数使用触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "IDX.002" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE name = 'john'",
            "SELECT * FROM users WHERE created_at = '2024-01-01'",
        ],
    )
    def test_not_triggers_without_function(self, sql):
        """测试无函数不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "IDX.002" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = IDX002_WhereFunctionRule()
        assert rule.rule_id == "IDX.002"
        assert rule.severity == Severity.L4
        assert rule.category == RuleCategory.IDX


class TestIDX003OrCondition:
    """IDX.003: 注意OR条件可能导致索引失效"""

    def test_triggers_on_or_different_columns(self):
        """测试OR连接不同列触发规则"""
        engine = get_rule_engine()
        sql = "SELECT * FROM users WHERE name = 'test' OR age = 20"
        results = engine.analyze(sql)
        assert any(r.rule_id == "IDX.003" for r in results)

    def test_not_triggers_on_or_same_column(self):
        """测试OR连接同一列不触发规则"""
        engine = get_rule_engine()
        sql = "SELECT * FROM users WHERE status = 'A' OR status = 'B'"
        results = engine.analyze(sql)
        assert not any(r.rule_id == "IDX.003" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = IDX003_OrConditionRule()
        assert rule.rule_id == "IDX.003"
        assert rule.severity == Severity.L3
        assert rule.category == RuleCategory.IDX


class TestCOL001NullComparison:
    """COL.001: 正确使用NULL比较"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE name = NULL",
            "SELECT * FROM users WHERE id = NULL",
        ],
    )
    def test_triggers_on_null_equality(self, sql):
        """测试 = NULL 触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "COL.001" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE name IS NULL",
            "SELECT * FROM users WHERE name IS NOT NULL",
        ],
    )
    def test_not_triggers_on_is_null(self, sql):
        """测试 IS NULL 不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "COL.001" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = COL001_NullComparisonRule()
        assert rule.rule_id == "COL.001"
        assert rule.severity == Severity.L5
        assert rule.category == RuleCategory.COL


class TestCOL002ImplicitTypeConversion:
    """COL.002: 避免隐式类型转换"""

    def test_triggers_on_numeric_col_with_string(self):
        """测试数值列与字符串比较触发规则"""
        engine = get_rule_engine()
        sql = "SELECT * FROM users WHERE id = '123'"
        results = engine.analyze(sql)
        assert any(r.rule_id == "COL.002" for r in results)

    def test_not_triggers_on_string_col_with_string(self):
        """测试字符串列与字符串比较不触发规则"""
        engine = get_rule_engine()
        sql = "SELECT * FROM users WHERE name = 'john'"
        results = engine.analyze(sql)
        assert not any(r.rule_id == "COL.002" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = COL002_ImplicitTypeConversionRule()
        assert rule.rule_id == "COL.002"
        assert rule.severity == Severity.L3
        assert rule.category == RuleCategory.COL


class TestCLA001OrderByLimit:
    """CLA.001: 注意ORDER BY与LIMIT的组合"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users ORDER BY id LIMIT 10",
            "SELECT * FROM users ORDER BY created_at DESC LIMIT 5",
        ],
    )
    def test_triggers_on_order_by_limit(self, sql):
        """测试 ORDER BY + LIMIT 触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "CLA.001" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users ORDER BY id",
            "SELECT * FROM users LIMIT 10",
        ],
    )
    def test_not_triggers_on_partial(self, sql):
        """测试仅 ORDER BY 或仅 LIMIT 不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "CLA.001" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = CLA001_OrderByLimitRule()
        assert rule.rule_id == "CLA.001"
        assert rule.severity == Severity.L3
        assert rule.category == RuleCategory.CLA


class TestCLA002GroupByNoIndex:
    """CLA.002: GROUP BY列建议有索引"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT status, COUNT(*) FROM users GROUP BY status",
            "SELECT category, SUM(amount) FROM orders GROUP BY category",
        ],
    )
    def test_triggers_on_group_by(self, sql):
        """测试 GROUP BY 触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "CLA.002" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT status, COUNT(*) FROM users",
            "SELECT * FROM users",
        ],
    )
    def test_not_triggers_without_group_by(self, sql):
        """测试无 GROUP BY 不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "CLA.002" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = CLA002_GroupByNoIndexRule()
        assert rule.rule_id == "CLA.002"
        assert rule.severity == Severity.L3
        assert rule.category == RuleCategory.CLA


class TestCLA003Distinct:
    """CLA.003: 检查DISTINCT是否必要"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT DISTINCT name FROM users",
            "SELECT DISTINCT category FROM products",
        ],
    )
    def test_triggers_on_distinct(self, sql):
        """测试 DISTINCT 触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "CLA.003" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT name FROM users",
            "SELECT name FROM users GROUP BY name",
        ],
    )
    def test_not_triggers_without_distinct(self, sql):
        """测试无 DISTINCT 不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "CLA.003" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = CLA003_DistinctRule()
        assert rule.rule_id == "CLA.003"
        assert rule.severity == Severity.L2
        assert rule.category == RuleCategory.CLA


class TestCLA004SubqueryInWhere:
    """CLA.004: 避免WHERE子句中的子查询"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)",
            "SELECT * FROM users WHERE EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id)",
        ],
    )
    def test_triggers_on_subquery_in_where(self, sql):
        """测试 WHERE 子查询触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "CLA.004" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE id = 1",
            "SELECT * FROM users u JOIN orders o ON u.id = o.user_id",
        ],
    )
    def test_not_triggers_without_subquery(self, sql):
        """测试无子查询不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "CLA.004" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = CLA004_SubqueryInWhereRule()
        assert rule.rule_id == "CLA.004"
        assert rule.severity == Severity.L4
        assert rule.category == RuleCategory.CLA


class TestCLA005Union:
    """CLA.005: 考虑使用UNION ALL替代UNION"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT id FROM users UNION SELECT id FROM admins",
            "SELECT name FROM table1 UNION SELECT name FROM table2",
        ],
    )
    def test_triggers_on_union(self, sql):
        """测试 UNION 触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "CLA.005" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT id FROM users UNION ALL SELECT id FROM admins",
            "SELECT id FROM users",
        ],
    )
    def test_not_triggers_on_union_all(self, sql):
        """测试 UNION ALL 不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "CLA.005" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = CLA005_UnionRule()
        assert rule.rule_id == "CLA.005"
        assert rule.severity == Severity.L2
        assert rule.category == RuleCategory.CLA


class TestKWR001NotIn:
    """KWR.001: 避免使用NOT IN"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE status NOT IN ('deleted', 'banned')",
            "SELECT * FROM orders WHERE id NOT IN (SELECT order_id FROM returns)",
        ],
    )
    def test_triggers_on_not_in(self, sql):
        """测试 NOT IN 触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "KWR.001" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE status IN ('active', 'pending')",
            "SELECT * FROM users WHERE status != 'deleted'",
        ],
    )
    def test_not_triggers_on_in(self, sql):
        """测试 IN 不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "KWR.001" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = KWR001_NotInRule()
        assert rule.rule_id == "KWR.001"
        assert rule.severity == Severity.L4
        assert rule.category == RuleCategory.KWR


class TestKWR002LikeLeadingWildcard:
    """KWR.002: 避免LIKE以通配符开头"""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE name LIKE '%john'",
            "SELECT * FROM users WHERE name LIKE '%john%'",
            "SELECT * FROM users WHERE name LIKE '_john'",
        ],
    )
    def test_triggers_on_leading_wildcard(self, sql):
        """测试前导通配符触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "KWR.002" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM users WHERE name LIKE 'john%'",
            "SELECT * FROM users WHERE name = 'john'",
        ],
    )
    def test_not_triggers_on_trailing_wildcard(self, sql):
        """测试后置通配符不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "KWR.002" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = KWR002_LikeLeadingWildcardRule()
        assert rule.rule_id == "KWR.002"
        assert rule.severity == Severity.L5
        assert rule.category == RuleCategory.KWR


class TestKWR003HavingNoGroupBy:
    """KWR.003: HAVING应与GROUP BY配合使用"""

    def test_triggers_on_having_without_group_by(self):
        """测试 HAVING 无 GROUP BY 触发规则"""
        engine = get_rule_engine()
        sql = "SELECT * FROM users HAVING COUNT(*) > 1"
        results = engine.analyze(sql)
        assert any(r.rule_id == "KWR.003" for r in results)

    def test_not_triggers_on_having_with_group_by(self):
        """测试 HAVING 有 GROUP BY 不触发规则"""
        engine = get_rule_engine()
        sql = "SELECT status, COUNT(*) FROM users GROUP BY status HAVING COUNT(*) > 1"
        results = engine.analyze(sql)
        assert not any(r.rule_id == "KWR.003" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = KWR003_HavingNoGroupByRule()
        assert rule.rule_id == "KWR.003"
        assert rule.severity == Severity.L3
        assert rule.category == RuleCategory.KWR


class TestERN001NoWhereInUpdateDelete:
    """ERN.001: UPDATE/DELETE必须有WHERE条件"""

    @pytest.mark.parametrize(
        "sql",
        [
            "UPDATE users SET status = 'inactive'",
            "DELETE FROM users",
        ],
    )
    def test_triggers_on_update_delete_without_where(self, sql):
        """测试无 WHERE 的 UPDATE/DELETE 触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert any(r.rule_id == "ERN.001" for r in results)

    @pytest.mark.parametrize(
        "sql",
        [
            "UPDATE users SET status = 'inactive' WHERE id = 1",
            "DELETE FROM users WHERE id = 1",
        ],
    )
    def test_not_triggers_with_where(self, sql):
        """测试有 WHERE 不触发规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        assert not any(r.rule_id == "ERN.001" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = ERN001_NoWhereInUpdateDeleteRule()
        assert rule.rule_id == "ERN.001"
        assert rule.severity == Severity.L8
        assert rule.category == RuleCategory.ERN


class TestERN002AmbiguousColumn:
    """ERN.002: 避免歧义列引用"""

    def test_triggers_on_ambiguous_column_in_join(self):
        """测试 JOIN 中歧义列触发规则"""
        engine = get_rule_engine()
        sql = "SELECT id, name FROM users JOIN orders ON users.id = orders.user_id"
        results = engine.analyze(sql)
        # id 和 name 可能是歧义列
        assert any(r.rule_id == "ERN.002" for r in results)

    def test_not_triggers_on_single_table(self):
        """测试单表查询不触发规则"""
        engine = get_rule_engine()
        sql = "SELECT id, name FROM users"
        results = engine.analyze(sql)
        assert not any(r.rule_id == "ERN.002" for r in results)

    def test_rule_properties(self):
        """测试规则属性"""
        rule = ERN002_AmbiguousColumnRule()
        assert rule.rule_id == "ERN.002"
        assert rule.severity == Severity.L6
        assert rule.category == RuleCategory.ERN


class TestRuleResults:
    """规则结果测试"""

    def test_result_structure(self):
        """测试结果结构完整性"""
        engine = get_rule_engine()
        results = engine.analyze("SELECT * FROM users")

        for result in results:
            assert result.rule_name is not None
            assert result.rule_id is not None
            assert result.category is not None
            assert result.severity is not None
            assert result.description is not None
            assert result.suggestion is not None

    def test_result_to_dict(self):
        """测试结果转换为字典"""
        engine = get_rule_engine()
        results = engine.analyze("SELECT * FROM users")

        for result in results:
            result_dict = result.to_dict()
            assert "rule_name" in result_dict
            assert "rule_id" in result_dict
            assert "category" in result_dict
            assert "severity" in result_dict
            assert "description" in result_dict
            assert "suggestion" in result_dict

    def test_results_sorted_by_severity(self):
        """测试结果按严重级别排序"""
        engine = get_rule_engine()
        # 使用会触发多个规则的SQL
        sql = "SELECT * FROM users WHERE id = NULL"
        results = engine.analyze(sql)

        if len(results) > 1:
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
                assert severity_order.get(
                    results[i].severity, 10
                ) <= severity_order.get(results[i + 1].severity, 10)


class TestMultipleRules:
    """多规则触发测试"""

    def test_multiple_issues_detected(self):
        """测试同时检测多个问题"""
        engine = get_rule_engine()
        # 这个SQL有多个问题：SELECT *, = NULL
        sql = "SELECT * FROM users WHERE id = NULL"
        results = engine.analyze(sql)

        rule_ids = [r.rule_id for r in results]
        assert "IDX.001" in rule_ids  # SELECT *
        assert "COL.001" in rule_ids  # = NULL

    def test_clean_sql_no_critical_issues(self):
        """测试干净的SQL不触发高级别规则"""
        engine = get_rule_engine()
        # 使用不会触发隐式类型转换规则的列名（避免status, type, code等）
        sql = "SELECT id, name FROM users WHERE email = 'test@example.com'"
        results = engine.analyze(sql)

        # 过滤掉L2及以下级别的提示
        critical_results = [
            r
            for r in results
            if r.severity.value in ["L3", "L4", "L5", "L6", "L7", "L8"]
        ]
        assert len(critical_results) == 0


class TestRuleEnableDisable:
    """规则启用/禁用测试"""

    def test_disable_rule(self):
        """测试禁用规则"""
        engine = get_rule_engine()
        engine.disable_rule("IDX.001")

        results = engine.analyze("SELECT * FROM users")
        assert not any(r.rule_id == "IDX.001" for r in results)

    def test_enable_rule(self):
        """测试启用规则"""
        engine = get_rule_engine()
        engine.disable_rule("IDX.001")
        engine.enable_rule("IDX.001")

        results = engine.analyze("SELECT * FROM users")
        assert any(r.rule_id == "IDX.001" for r in results)


class TestAnalysisContext:
    """分析上下文测试"""

    def test_context_with_all_fields(self):
        """测试完整上下文"""
        context = AnalysisContext(
            sql="SELECT * FROM users",
            explain_result=[{"table": "users", "type": "ALL"}],
            table_schema={"users": [{"name": "id", "type": "INT"}]},
            indexes={"users": [{"name": "PRIMARY", "columns": ["id"]}]},
            metadata={"database": "test_db"},
        )

        engine = get_rule_engine()
        results = engine.analyze_with_context(context)
        assert len(results) > 0


class TestGetDefaultRules:
    """get_default_rules 函数测试"""

    def test_returns_15_rules(self):
        """测试返回15个规则"""
        rules = get_default_rules()
        assert len(rules) == 15

    def test_all_rules_have_required_attributes(self):
        """测试所有规则都有必需属性"""
        rules = get_default_rules()
        for rule in rules:
            assert rule.rule_id is not None
            assert rule.name is not None
            assert rule.description is not None
            assert rule.severity is not None
            assert rule.category is not None
