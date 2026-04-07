"""
可视化EXPLAIN解析器测试
"""

import pytest
from app.services.visual_explain import VisualExplainParser


class TestVisualExplainParser:
    """测试可视化EXPLAIN解析器"""

    def test_parse_explain_result_empty(self):
        """测试解析空结果"""
        result = VisualExplainParser.parse_explain_result([])
        assert result == []

    def test_parse_explain_result_basic(self):
        """测试基本EXPLAIN结果解析"""
        explain_rows = [
            {
                "id": 1,
                "select_type": "SIMPLE",
                "table": "users",
                "type": "ALL",
                "possible_keys": None,
                "key": None,
                "key_len": None,
                "ref": None,
                "rows": 1000,
                "filtered": 100.0,
                "Extra": None,
            }
        ]

        nodes = VisualExplainParser.parse_explain_result(explain_rows)

        assert len(nodes) == 1
        assert nodes[0]["id"] == 1
        assert nodes[0]["table"] == "users"
        assert nodes[0]["type"] == "ALL"

    def test_parse_explain_result_multiple_rows(self):
        """测试多行EXPLAIN结果解析"""
        explain_rows = [
            {
                "id": 1,
                "select_type": "SIMPLE",
                "table": "orders",
                "type": "ALL",
                "rows": 5000,
            },
            {
                "id": 1,
                "select_type": "SIMPLE",
                "table": "users",
                "type": "eq_ref",
                "key": "PRIMARY",
                "rows": 1,
            },
        ]

        nodes = VisualExplainParser.parse_explain_result(explain_rows)

        assert len(nodes) == 2
        assert nodes[0]["table"] == "orders"
        assert nodes[1]["table"] == "users"

    def test_parse_explain_result_with_possible_keys(self):
        """测试带可能索引的解析"""
        explain_rows = [
            {
                "id": 1,
                "select_type": "SIMPLE",
                "table": "users",
                "type": "ALL",
                "possible_keys": "idx_name,idx_email",
                "key": None,
            }
        ]

        nodes = VisualExplainParser.parse_explain_result(explain_rows)

        assert len(nodes[0]["possible_keys"]) == 2
        assert "idx_name" in nodes[0]["possible_keys"]
        assert "idx_email" in nodes[0]["possible_keys"]

    def test_parse_list_field_none(self):
        """测试解析None列表字段"""
        result = VisualExplainParser._parse_list_field(None)
        assert result == []

    def test_parse_list_field_string(self):
        """测试解析字符串列表字段"""
        result = VisualExplainParser._parse_list_field("a,b,c")
        assert result == ["a", "b", "c"]

    def test_parse_list_field_list(self):
        """测试解析列表字段"""
        result = VisualExplainParser._parse_list_field(["a", "b", "c"])
        assert result == ["a", "b", "c"]

    def test_safe_int_valid(self):
        """测试安全转换整数"""
        assert VisualExplainParser._safe_int(100) == 100
        assert VisualExplainParser._safe_int("100") == 100

    def test_safe_int_invalid(self):
        """测试无效值转整数"""
        assert VisualExplainParser._safe_int(None) == 0
        assert VisualExplainParser._safe_int("invalid") == 0
        assert VisualExplainParser._safe_int([]) == 0

    def test_has_warning_all_type(self):
        """测试全表扫描警告"""
        node = {
            "type": "ALL",
            "key": None,
            "rows": 100,
            "Extra": None,
        }
        assert VisualExplainParser._has_warning(node) is True

    def test_has_warning_no_key(self):
        """测试无索引警告"""
        node = {
            "type": "ref",
            "key": None,
            "rows": 100,
            "Extra": None,
        }
        assert VisualExplainParser._has_warning(node) is True

    def test_has_warning_large_rows(self):
        """测试大量行警告"""
        node = {
            "type": "index",
            "key": "idx_test",
            "rows": 200000,
            "Extra": None,
        }
        assert VisualExplainParser._has_warning(node) is True

    def test_has_warning_filesort(self):
        """测试filesort警告"""
        node = {
            "type": "index",
            "key": "idx_test",
            "rows": 100,
            "Extra": "Using filesort",
        }
        assert VisualExplainParser._has_warning(node) is True

    def test_has_warning_temporary(self):
        """测试temporary警告"""
        node = {
            "type": "index",
            "key": "idx_test",
            "rows": 100,
            "Extra": "Using temporary",
        }
        assert VisualExplainParser._has_warning(node) is True

    def test_has_warning_good(self):
        """测试无警告情况"""
        node = {
            "type": "eq_ref",
            "key": "PRIMARY",
            "rows": 1,
            "Extra": None,
        }
        assert VisualExplainParser._has_warning(node) is False

    def test_get_node_color_warning(self):
        """测试警告节点颜色"""
        node = {
            "type": "ALL",
            "key": None,
            "rows": 100,
            "Extra": None,
        }
        assert VisualExplainParser._get_node_color(node) == "#f56c6c"

    def test_get_node_color_good_types(self):
        """测试良好类型颜色"""
        good_nodes = [
            {"type": "eq_ref", "key": "idx", "rows": 1, "Extra": None},
            {"type": "ref", "key": "idx", "rows": 10, "Extra": None},
            {"type": "const", "key": "idx", "rows": 1, "Extra": None},
            {"type": "system", "key": "idx", "rows": 1, "Extra": None},
        ]

        for node in good_nodes:
            color = VisualExplainParser._get_node_color(node)
            assert color == "#67c23a" or color == "#909399"

    def test_get_node_color_default(self):
        """测试默认颜色"""
        node = {
            "type": "unique_subquery",
            "key": "idx",
            "rows": 1,
            "Extra": None,
        }
        assert VisualExplainParser._get_node_color(node) == "#409eff"

    def test_extract_graph_data(self):
        """测试提取图表数据"""
        nodes = [
            {
                "id": 1,
                "table": "users",
                "type": "ALL",
                "rows": 1000,
                "key": None,
                "filtered": 100,
                "Extra": None,
                "parent_id": None,
            },
            {
                "id": 2,
                "table": "orders",
                "type": "ref",
                "rows": 10,
                "key": "idx_user_id",
                "filtered": 100,
                "Extra": None,
                "parent_id": 1,
            },
        ]

        graph_nodes, links = VisualExplainParser.extract_graph_data(nodes)

        assert len(graph_nodes) == 2
        assert len(links) == 1
        assert links[0]["source"] == 1
        assert links[0]["target"] == 2

    def test_generate_node_positions(self):
        """测试生成节点位置"""
        nodes = [
            {"id": 1, "parent_id": None, "depth": 0},
            {"id": 2, "parent_id": 1, "depth": 1},
            {"id": 3, "parent_id": 1, "depth": 1},
        ]

        positions = VisualExplainParser.generate_node_positions(nodes, 1000, 800)

        assert 1 in positions
        assert 2 in positions
        assert 3 in positions

        # 根节点应该在最上面 (y值较大)
        root_y = positions[1][1]
        child1_y = positions[2][1]
        assert root_y > child1_y
