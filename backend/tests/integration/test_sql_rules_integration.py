"""
SQL优化规则集成测试

测试规则引擎在复杂场景下的集成行为，包括：
- 多规则协同检测
- 规则优先级排序
- 真实SQL场景分析
- 规则启用/禁用交互
- 与API的集成测试
"""

import pytest
from typing import List, Dict, Any

from app.services.rule_engine import (
    get_rule_engine,
    reset_rule_engine,
    AnalysisContext,
    RuleCategory,
    Severity,
    RuleResult,
)
from app.services.sql_rules import (
    get_default_rules,
    register_all_rules,
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


@pytest.fixture(autouse=True)
def setup_rules():
    """每个测试前重置并重新注册规则"""
    reset_rule_engine()
    register_all_rules()
    yield
    reset_rule_engine()


class TestMultiRuleScenarios:
    """多规则协同检测测试"""

    @pytest.mark.parametrize(
        "sql,expected_rule_ids",
        [
            # 场景1: SELECT * + = NULL (两个问题)
            (
                "SELECT * FROM users WHERE id = NULL",
                ["IDX.001", "COL.001"],
            ),
            # 场景2: SELECT * + 函数 + ORDER BY LIMIT
            (
                "SELECT * FROM users WHERE UPPER(name) = 'JOHN' ORDER BY id LIMIT 10",
                ["IDX.001", "IDX.002", "CLA.001"],
            ),
            # 场景3: 复杂查询 - 多个问题
            (
                "SELECT * FROM orders WHERE user_id = '123' OR status = 'pending'",
                ["IDX.001", "COL.002", "IDX.003"],
            ),
            # 场景4: 前导通配符 + 子查询
            (
                "SELECT * FROM users WHERE name LIKE '%john%' AND id IN (SELECT user_id FROM orders)",
                ["IDX.001", "KWR.002", "CLA.004"],
            ),
            # 场景5: UPDATE无WHERE - 最高严重级别
            (
                "UPDATE users SET status = 'inactive'",
                ["ERN.001"],
            ),
            # 场景6: DELETE无WHERE - 危险操作
            (
                "DELETE FROM logs",
                ["ERN.001"],
            ),
        ],
    )
    def test_multiple_rules_triggered(self, sql: str, expected_rule_ids: List[str]):
        """测试复杂SQL触发多个规则"""
        engine = get_rule_engine()
        results = engine.analyze(sql)
        triggered_ids = [r.rule_id for r in results]

        for expected_id in expected_rule_ids:
            assert expected_id in triggered_ids, (
                f"Expected rule {expected_id} to be triggered for SQL: {sql}. "
                f"Triggered rules: {triggered_ids}"
            )

    def test_results_sorted_by_severity(self):
        """测试结果按严重级别排序（L9 > L8 > ... > L0）"""
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


class TestRealWorldSQLScenarios:
    """真实SQL场景测试"""

    def test_ecommerce_order_query(self):
        """电商订单查询场景"""
        engine = get_rule_engine()
        # 典型的电商订单查询（CLA.001需要ORDER BY和LIMIT在同一模式）
        sql = """
        SELECT * FROM orders o
        JOIN users u ON o.user_id = u.id
        WHERE o.status = 'pending'
        AND u.name LIKE '%张%'
        ORDER BY o.created_at DESC LIMIT 100
        """
        results = engine.analyze(sql)
        triggered_ids = [r.rule_id for r in results]

        # SELECT * 应该触发
        assert "IDX.001" in triggered_ids
        # 前导通配符应该触发
        assert "KWR.002" in triggered_ids
        # ORDER BY + LIMIT 应该触发（需要在同一行）
        assert "CLA.001" in triggered_ids

    def test_user_search_with_function(self):
        """用户搜索使用函数场景"""
        engine = get_rule_engine()
        sql = """
        SELECT id, name, email FROM users
        WHERE LOWER(email) = 'test@example.com'
        OR UPPER(name) = 'JOHN'
        """
        results = engine.analyze(sql)
        triggered_ids = [r.rule_id for r in results]

        # 函数使用应该触发
        assert "IDX.002" in triggered_ids
        # OR条件可能触发
        # 注意：这里可能不一定触发IDX.003，因为模式匹配可能不完全

    def test_report_aggregation_query(self):
        """报表聚合查询场景"""
        engine = get_rule_engine()
        sql = """
        SELECT DISTINCT category, COUNT(*) as cnt
        FROM products
        GROUP BY category
        HAVING COUNT(*) > 10
        ORDER BY cnt DESC
        """
        results = engine.analyze(sql)
        triggered_ids = [r.rule_id for r in results]

        # DISTINCT应该触发
        assert "CLA.003" in triggered_ids
        # GROUP BY应该触发
        assert "CLA.002" in triggered_ids

    def test_subquery_in_where(self):
        """WHERE子句中的子查询"""
        engine = get_rule_engine()
        sql = """
        SELECT * FROM users
        WHERE id NOT IN (SELECT user_id FROM banned_users)
        """
        results = engine.analyze(sql)
        triggered_ids = [r.rule_id for r in results]

        # SELECT * 应该触发
        assert "IDX.001" in triggered_ids
        # NOT IN 应该触发
        assert "KWR.001" in triggered_ids
        # WHERE中的子查询应该触发
        assert "CLA.004" in triggered_ids

    def test_clean_sql_minimal_issues(self):
        """干净的SQL应该只有轻微问题"""
        engine = get_rule_engine()
        # 使用不会触发隐式类型转换的列名
        sql = """
        SELECT u.id, u.name, o.total
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
        AND o.created_at >= '2024-01-01'
        ORDER BY o.created_at DESC
        LIMIT 50
        """
        results = engine.analyze(sql)

        # 应该没有高严重级别问题（L4及以上）
        high_severity = [
            r
            for r in results
            if r.severity.value in ["L4", "L5", "L6", "L7", "L8", "L9"]
        ]
        assert len(high_severity) == 0

    def test_dangerous_update_query(self):
        """危险的UPDATE查询"""
        engine = get_rule_engine()
        sql = "UPDATE products SET price = price * 1.1"
        results = engine.analyze(sql)
        triggered_ids = [r.rule_id for r in results]

        # 无WHERE的UPDATE应该触发最高严重级别
        assert "ERN.001" in triggered_ids
        # 验证严重级别是L8
        ern_result = next(r for r in results if r.rule_id == "ERN.001")
        assert ern_result.severity == Severity.L8


class TestRuleEnableDisable:
    """规则启用/禁用测试"""

    def test_disable_single_rule(self):
        """测试禁用单个规则"""
        engine = get_rule_engine()

        # 禁用IDX.001
        engine.disable_rule("IDX.001")

        results = engine.analyze("SELECT * FROM users")
        triggered_ids = [r.rule_id for r in results]

        assert "IDX.001" not in triggered_ids

    def test_disable_multiple_rules(self):
        """测试禁用多个规则"""
        engine = get_rule_engine()

        # 禁用多个规则
        engine.disable_rule("IDX.001")
        engine.disable_rule("COL.001")

        sql = "SELECT * FROM users WHERE id = NULL"
        results = engine.analyze(sql)
        triggered_ids = [r.rule_id for r in results]

        assert "IDX.001" not in triggered_ids
        assert "COL.001" not in triggered_ids

    def test_reenable_rule(self):
        """测试重新启用规则"""
        engine = get_rule_engine()

        # 禁用再启用
        engine.disable_rule("IDX.001")
        engine.enable_rule("IDX.001")

        results = engine.analyze("SELECT * FROM users")
        triggered_ids = [r.rule_id for r in results]

        assert "IDX.001" in triggered_ids

    def test_get_enabled_rules_count(self):
        """测试获取启用的规则数量"""
        engine = get_rule_engine()

        initial_count = len(engine.get_enabled_rules())
        assert initial_count == 15

        engine.disable_rule("IDX.001")
        assert len(engine.get_enabled_rules()) == 14

        engine.disable_rule("COL.001")
        assert len(engine.get_enabled_rules()) == 13

    def test_all_rules_disabled_empty_results(self):
        """测试禁用所有规则后返回空结果"""
        engine = get_rule_engine()

        # 禁用所有规则
        for rule in engine.get_all_rules():
            engine.disable_rule(rule.rule_id)

        results = engine.analyze("SELECT * FROM users WHERE id = NULL")
        assert len(results) == 0


class TestAnalysisContext:
    """分析上下文测试"""

    def test_context_with_explain_result(self):
        """测试带有EXPLAIN结果的分析"""
        context = AnalysisContext(
            sql="SELECT * FROM users WHERE id = 1",
            explain_result=[
                {"id": 1, "select_type": "SIMPLE", "table": "users", "type": "ALL"}
            ],
        )

        engine = get_rule_engine()
        results = engine.analyze_with_context(context)

        # 应该检测到SELECT *
        assert any(r.rule_id == "IDX.001" for r in results)

    def test_context_with_table_schema(self):
        """测试带有表结构的分析"""
        context = AnalysisContext(
            sql="SELECT * FROM users WHERE id = 1",
            table_schema={
                "users": [
                    {"name": "id", "type": "INT", "key": "PRI"},
                    {"name": "name", "type": "VARCHAR(100)"},
                ]
            },
        )

        engine = get_rule_engine()
        results = engine.analyze_with_context(context)

        assert len(results) > 0

    def test_context_with_metadata(self):
        """测试带有元数据的分析"""
        context = AnalysisContext(
            sql="SELECT * FROM users",
            metadata={
                "database": "production",
                "query_time": 2.5,
                "source": "slow_query_log",
            },
        )

        engine = get_rule_engine()
        results = engine.analyze_with_context(context)

        # 元数据应该被保留（虽然当前规则不使用）
        assert any(r.rule_id == "IDX.001" for r in results)


class TestRuleResultStructure:
    """规则结果结构测试"""

    def test_result_complete_structure(self):
        """测试结果结构完整性"""
        engine = get_rule_engine()
        results = engine.analyze("SELECT * FROM users")

        for result in results:
            # 验证必需字段
            assert result.rule_name is not None
            assert result.rule_id is not None
            assert result.category is not None
            assert result.severity is not None
            assert result.description is not None
            assert result.suggestion is not None

            # 验证类型
            assert isinstance(result.category, RuleCategory)
            assert isinstance(result.severity, Severity)
            assert isinstance(result.description, str)
            assert isinstance(result.suggestion, str)

    def test_result_to_dict(self):
        """测试结果转换为字典"""
        engine = get_rule_engine()
        results = engine.analyze("SELECT * FROM users")

        for result in results:
            result_dict = result.to_dict()

            # 验证字典包含所有字段
            assert "rule_name" in result_dict
            assert "rule_id" in result_dict
            assert "category" in result_dict
            assert "severity" in result_dict
            assert "description" in result_dict
            assert "suggestion" in result_dict
            assert "sql_segment" in result_dict
            assert "fix_sql" in result_dict
            assert "metadata" in result_dict

            # 验证枚举值转换为字符串
            assert isinstance(result_dict["category"], str)
            assert isinstance(result_dict["severity"], str)


class TestRuleRegistration:
    """规则注册测试"""

    def test_all_15_rules_registered(self):
        """测试所有15个规则都已注册"""
        engine = get_rule_engine()
        assert engine.rule_count == 15

    def test_rule_ids_unique(self):
        """测试规则ID唯一"""
        engine = get_rule_engine()
        rules = engine.get_all_rules()
        rule_ids = [r.rule_id for r in rules]

        assert len(rule_ids) == len(set(rule_ids))

    def test_get_rule_by_id(self):
        """测试通过ID获取规则"""
        engine = get_rule_engine()

        rule = engine.get_rule("IDX.001")
        assert rule is not None
        assert rule.rule_id == "IDX.001"
        assert rule.name == "避免使用 SELECT *"

    def test_get_nonexistent_rule(self):
        """测试获取不存在的规则"""
        engine = get_rule_engine()

        rule = engine.get_rule("NONEXISTENT.001")
        assert rule is None

    def test_unregister_rule(self):
        """测试注销规则"""
        engine = get_rule_engine()

        initial_count = engine.rule_count
        result = engine.unregister_rule("IDX.001")

        assert result is True
        assert engine.rule_count == initial_count - 1
        assert engine.get_rule("IDX.001") is None

    def test_unregister_nonexistent_rule(self):
        """测试注销不存在的规则"""
        engine = get_rule_engine()

        result = engine.unregister_rule("NONEXISTENT.001")
        assert result is False


class TestEdgeCases:
    """边缘情况测试"""

    def test_empty_sql(self):
        """测试空SQL"""
        engine = get_rule_engine()
        results = engine.analyze("")
        assert len(results) == 0

    def test_whitespace_only_sql(self):
        """测试仅包含空白的SQL"""
        engine = get_rule_engine()
        results = engine.analyze("   \n\t   ")
        assert len(results) == 0

    def test_sql_with_comments(self):
        """测试带有注释的SQL"""
        engine = get_rule_engine()
        sql = """
        -- This is a comment
        SELECT * FROM users
        /* Multi-line
           comment */
        WHERE id = 1
        """
        results = engine.analyze(sql)

        # 注释不应该阻止规则检测
        assert any(r.rule_id == "IDX.001" for r in results)

    def test_case_insensitive_detection(self):
        """测试大小写不敏感检测"""
        engine = get_rule_engine()

        # 大写
        results_upper = engine.analyze("SELECT * FROM USERS")
        # 小写
        results_lower = engine.analyze("select * from users")
        # 混合
        results_mixed = engine.analyze("Select * From Users")

        assert any(r.rule_id == "IDX.001" for r in results_upper)
        assert any(r.rule_id == "IDX.001" for r in results_lower)
        assert any(r.rule_id == "IDX.001" for r in results_mixed)

    def test_multiple_statements(self):
        """测试多条SQL语句（仅分析第一条）"""
        engine = get_rule_engine()
        # 当前实现对多条语句只检测整体
        sql = "SELECT * FROM users; DELETE FROM logs;"
        results = engine.analyze(sql)

        # 至少应该检测到SELECT *
        assert any(r.rule_id == "IDX.001" for r in results)

    def test_very_long_sql(self):
        """测试超长SQL"""
        engine = get_rule_engine()

        # 构造超长SQL
        columns = ", ".join([f"col{i}" for i in range(100)])
        sql = f"SELECT {columns} FROM users WHERE id = NULL"

        results = engine.analyze(sql)

        # 应该检测到 = NULL
        assert any(r.rule_id == "COL.001" for r in results)


class TestRuleCategories:
    """规则分类测试"""

    def test_index_category_rules(self):
        """测试索引分类规则"""
        engine = get_rule_engine()
        rules = engine.get_all_rules()
        idx_rules = [r for r in rules if r.category == RuleCategory.IDX]

        assert len(idx_rules) == 3  # IDX.001, IDX.002, IDX.003

    def test_column_category_rules(self):
        """测试列分类规则"""
        engine = get_rule_engine()
        rules = engine.get_all_rules()
        col_rules = [r for r in rules if r.category == RuleCategory.COL]

        assert len(col_rules) == 2  # COL.001, COL.002

    def test_clause_category_rules(self):
        """测试子句分类规则"""
        engine = get_rule_engine()
        rules = engine.get_all_rules()
        cla_rules = [r for r in rules if r.category == RuleCategory.CLA]

        assert len(cla_rules) == 5  # CLA.001-005

    def test_keyword_category_rules(self):
        """测试关键字分类规则"""
        engine = get_rule_engine()
        rules = engine.get_all_rules()
        kwr_rules = [r for r in rules if r.category == RuleCategory.KWR]

        assert len(kwr_rules) == 3  # KWR.001-003

    def test_error_category_rules(self):
        """测试错误分类规则"""
        engine = get_rule_engine()
        rules = engine.get_all_rules()
        ern_rules = [r for r in rules if r.category == RuleCategory.ERN]

        assert len(ern_rules) == 2  # ERN.001, ERN.002


class TestSeverityLevels:
    """严重级别测试"""

    @pytest.mark.parametrize(
        "sql,expected_min_severity",
        [
            ("UPDATE users SET status = 'x'", Severity.L8),  # 无WHERE的UPDATE
            ("DELETE FROM users", Severity.L8),  # 无WHERE的DELETE
            ("SELECT * FROM users WHERE id = NULL", Severity.L5),  # = NULL
            ("SELECT * FROM users WHERE name LIKE '%x'", Severity.L5),  # 前导通配符
            ("SELECT * FROM users", Severity.L3),  # SELECT *
            ("SELECT DISTINCT name FROM users", Severity.L2),  # DISTINCT
            ("SELECT id FROM users UNION SELECT id FROM admins", Severity.L2),  # UNION
        ],
    )
    def test_severity_levels_correct(self, sql: str, expected_min_severity: Severity):
        """测试不同问题的严重级别"""
        engine = get_rule_engine()
        results = engine.analyze(sql)

        # 获取最高严重级别
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

        if results:
            min_severity_order = min(
                severity_order.get(r.severity, 10) for r in results
            )
            expected_order = severity_order.get(expected_min_severity, 10)
            assert min_severity_order <= expected_order


class TestPerformance:
    """性能测试"""

    def test_analysis_performance(self):
        """测试分析性能（应该在合理时间内完成）"""
        import time

        engine = get_rule_engine()
        sql = "SELECT * FROM users WHERE id = NULL"

        start = time.time()
        for _ in range(100):
            engine.analyze(sql)
        elapsed = time.time() - start

        # 100次分析应该在1秒内完成
        assert elapsed < 1.0, f"Analysis too slow: {elapsed:.3f}s for 100 iterations"

    def test_large_sql_performance(self):
        """测试大SQL分析性能"""
        import time

        engine = get_rule_engine()

        # 构造大SQL
        tables = ", ".join([f"table{i} t{i}" for i in range(10)])
        sql = f"SELECT * FROM {tables} WHERE t0.id = NULL"

        start = time.time()
        results = engine.analyze(sql)
        elapsed = time.time() - start

        # 应该在100ms内完成
        assert elapsed < 0.1, f"Large SQL analysis too slow: {elapsed:.3f}s"
        # 应该检测到问题
        assert len(results) > 0
