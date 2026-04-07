"""
健康评分算法单元测试
"""

import pytest
from app.services.health_score import HealthScoreCalculator


class TestHealthScoreCalculator:
    """测试HealthScoreCalculator类"""

    def setup_method(self):
        """每个测试前创建计算器实例"""
        self.calculator = HealthScoreCalculator()

    def test_perfect_score(self):
        """测试无问题时应该得100分"""
        violations = []
        status_metrics = {
            "Questions": 1000.0,
            "Connections": 100.0,
            "Aborted_connects": 0.0,
            "Threads_running": 10.0,
        }

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
            status_metrics=status_metrics,
        )

        assert result["health_score"] == 100
        assert result["base_score"] == 100
        assert len(result["deductions"]) == 0
        assert result["load_adjustment"]["factor"] == 1.0
        assert result["trend_adjustment"]["amount"] == 0

    def test_single_crit(self):
        """测试1个CRIT问题应该得80分"""
        violations = [
            {
                "param": "innodb_buffer_pool_size",
                "severity": "CRIT",
                "current_value": "1G",
                "recommended_value": "4G",
                "description": "InnoDB缓冲池过小",
            }
        ]

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
        )

        assert result["health_score"] == 80
        assert result["base_score"] == 100
        assert any(
            d["type"] == "violation" and d["severity"] == "CRIT"
            for d in result["deductions"]
        )

    def test_multiple_warnings(self):
        """测试2个WARN问题应该得80分"""
        violations = [
            {
                "param": "slow_query_log",
                "severity": "WARN",
                "current_value": "OFF",
                "description": "慢查询日志未启用",
            },
            {
                "param": "thread_cache_size",
                "severity": "WARN",
                "current_value": "0",
                "description": "线程缓存过小",
            },
        ]

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
        )

        assert result["health_score"] == 80
        assert result["deductions"][0]["amount"] == -10
        assert result["deductions"][1]["amount"] == -10

    def test_info_items(self):
        """测试1个INFO问题应该得95分"""
        violations = [
            {
                "param": "skip_name_resolve",
                "severity": "INFO",
                "current_value": "OFF",
                "description": "DNS解析跳过",
            }
        ]

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
        )

        assert result["health_score"] == 95
        assert result["deductions"][0]["amount"] == -5

    def test_load_aware_adjustment_high_qps(self):
        """测试高QPS环境下缓冲区问题权重加倍"""
        violations = [
            {
                "param": "tmp_table_size",
                "severity": "WARN",
                "current_value": "128M",
                "description": "临时表内存过大",
            }
        ]

        status_metrics = {
            "Questions": 20000.0,  # 高QPS
            "Connections": 100.0,
            "Aborted_connects": 0.0,
            "Threads_running": 10.0,
        }

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
            status_metrics=status_metrics,
        )

        # 高QPS + 缓冲区问题 = 1.5x权重
        assert result["health_score"] == 85
        assert result["load_adjustment"]["factor"] == 1.5
        assert result["deductions"][0]["amount"] == -15

    def test_historical_trend_increasing(self):
        """测试连续上升趋势应该加分"""
        historical_scores = [80, 85, 90, 92]  # 连续上升

        status_metrics = {
            "Questions": 1000.0,
            "Connections": 100.0,
            "Aborted_connects": 0.0,
            "Threads_running": 10.0,
        }

        result = self.calculator.calculate_score(
            violations=[],
            mysql_version="8.0.0",
            status_metrics=status_metrics,
            historical_scores=historical_scores,
        )

        # 明显上升，平均86.75，最新92
        # 趋势加5分，最多15分
        # 基础分数100 + 5 = 105，被限制到100
        assert result["health_score"] == 100
        assert result["trend_adjustment"]["amount"] == 5

    def test_historical_trend_decreasing(self):
        """测试连续下降趋势应该扣分"""
        historical_scores = [95, 90, 88, 85]  # 连续下降

        status_metrics = {
            "Questions": 1000.0,
            "Connections": 100.0,
            "Aborted_connects": 0.0,
            "Threads_running": 10.0,
        }

        result = self.calculator.calculate_score(
            violations=[],
            mysql_version="8.0.0",
            status_metrics=status_metrics,
            historical_scores=historical_scores,
        )

        # 明显下降，平均89.5，最新85
        # 趋势扣4分 (89.5-85)*0.95=4.275，取整4
        assert result["health_score"] == 96  # 100 - 4 = 96
        assert result["trend_adjustment"]["amount"] == -4

    def test_score_explanation(self):
        """测试评分解释生成"""
        violations = [
            {
                "param": "innodb_buffer_pool_size",
                "severity": "CRIT",
                "current_value": "1G",
                "recommended_value": "4G",
                "description": "InnoDB缓冲池过小",
            },
            {
                "param": "slow_query_log",
                "severity": "WARN",
                "current_value": "OFF",
                "description": "慢查询日志未启用",
            },
        ]

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
        )

        explanation = self.calculator.get_score_explanation(result)

        assert "健康评分: 70/100" in explanation
        assert "严重问题(CRIT)" in explanation
        assert "警告问题(WARN)" in explanation
        assert "基础分数: 100" in explanation
        assert "最终评分: 70/100" in explanation

    def test_high_connection_usage_with_connection_issues(self):
        """测试高连接使用率环境下连接问题权重加倍
        
        注意：由于代码逻辑中高连接使用率阈值(0.8)远大于高中断率阈值(0.05)，
        满足高连接使用率条件时一定也满足高中断率条件，
        所以这个分支实际上会被高中断率分支覆盖。
        这里测试的是当同时满足两个条件时，最终被高中断率分支处理的情况。
        """
        violations = [
            {
                "param": "max_connections",
                "severity": "WARN",
                "current_value": "100",
                "description": "最大连接数过小",
            }
        ]

        # 高连接使用率和高中断率同时满足
        # connection_usage = 90/101 ≈ 89% > 80%
        # aborted_ratio = 90/101 ≈ 89% > 5%
        status_metrics = {
            "Questions": 1000.0,
            "Connections": 100.0,
            "Aborted_connects": 90.0,
            "Threads_running": 10.0,
        }

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
            status_metrics=status_metrics,
        )

        # 由于高中断率条件也满足，会被高中断率分支覆盖，factor = 1.2
        assert result["load_adjustment"]["factor"] == 1.2
        assert "高中断率" in result["load_adjustment"]["description"]

    def test_high_aborted_rate_with_logging_issues(self):
        """测试高中断率环境下日志问题权重加倍"""
        violations = [
            {
                "param": "slow_query_log",
                "severity": "WARN",
                "current_value": "OFF",
                "description": "慢查询日志未启用",
            }
        ]

        # 高中断率：aborted_connects/connections > 0.05
        status_metrics = {
            "Questions": 1000.0,
            "Connections": 100.0,
            "Aborted_connects": 10.0,  # 10/100 = 10% > 5%
            "Threads_running": 10.0,
        }

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
            status_metrics=status_metrics,
        )

        # 高中断率 + 日志问题 = 1.4x权重
        assert result["load_adjustment"]["factor"] == 1.4
        assert "高中断率" in result["load_adjustment"]["description"]

    def test_high_aborted_rate_with_connection_issues(self):
        """测试高中断率环境下连接问题权重加倍（elif分支）"""
        violations = [
            {
                "param": "max_connections",
                "severity": "WARN",
                "current_value": "100",
                "description": "最大连接数过小",
            }
        ]

        # 高中断率：aborted_connects/connections > 0.05
        status_metrics = {
            "Questions": 1000.0,
            "Connections": 100.0,
            "Aborted_connects": 10.0,  # 10/100 = 10% > 5%
            "Threads_running": 10.0,
        }

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
            status_metrics=status_metrics,
        )

        # 高中断率 + 连接问题（无日志问题） = 1.2x权重
        assert result["load_adjustment"]["factor"] == 1.2
        assert "高中断率" in result["load_adjustment"]["description"]

    def test_high_thread_contention_with_buffer_issues(self):
        """测试高线程竞争环境下缓冲区问题权重加倍"""
        violations = [
            {
                "param": "innodb_buffer_pool_size",
                "severity": "WARN",
                "current_value": "128M",
                "description": "InnoDB缓冲池过小",
            }
        ]

        # 高线程竞争：threads_running/connections > 0.7
        status_metrics = {
            "Questions": 1000.0,
            "Connections": 100.0,
            "Aborted_connects": 0.0,
            "Threads_running": 80.0,  # 80/100 = 80% > 70%
        }

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
            status_metrics=status_metrics,
        )

        # 高线程竞争 + 缓冲区问题 = 1.3x权重
        assert result["load_adjustment"]["factor"] == 1.3
        assert "高线程竞争" in result["load_adjustment"]["description"]

    def test_high_thread_contention_with_connection_issues(self):
        """测试高线程竞争环境下连接问题权重加倍（elif分支）"""
        violations = [
            {
                "param": "max_connections",
                "severity": "WARN",
                "current_value": "100",
                "description": "最大连接数过小",
            }
        ]

        # 高线程竞争：threads_running/connections > 0.7
        status_metrics = {
            "Questions": 1000.0,
            "Connections": 100.0,
            "Aborted_connects": 0.0,
            "Threads_running": 80.0,  # 80/100 = 80% > 70%
        }

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
            status_metrics=status_metrics,
        )

        # 高线程竞争 + 连接问题（无缓冲区问题） = 1.15x权重
        assert result["load_adjustment"]["factor"] == 1.15
        assert "高线程竞争" in result["load_adjustment"]["description"]

    def test_historical_trend_insufficient_data_single(self):
        """测试历史数据不足（只有1条）无趋势调整"""
        historical_scores = [85]  # 只有1条

        result = self.calculator.calculate_score(
            violations=[],
            mysql_version="8.0.0",
            historical_scores=historical_scores,
        )

        # 只有1条数据时，calculate_score 不会调用 _calculate_trend_adjustment
        # 而是使用默认值 {"amount": 0, "description": "无趋势调整"}
        assert result["trend_adjustment"]["amount"] == 0
        assert result["trend_adjustment"]["description"] == "无趋势调整"

    def test_historical_trend_stable(self):
        """测试平稳趋势无调整"""
        # 构造一个不连续上升也不连续下降的趋势
        historical_scores = [85, 90, 85, 88]  # 波动，非单调

        result = self.calculator.calculate_score(
            violations=[],
            mysql_version="8.0.0",
            historical_scores=historical_scores,
        )

        # 平稳趋势，无调整
        assert result["trend_adjustment"]["amount"] == 0
        assert "平稳趋势" in result["trend_adjustment"]["description"]

    def test_score_explanation_with_load_adjustment(self):
        """测试评分解释中显示负载调整"""
        violations = [
            {
                "param": "innodb_buffer_pool_size",
                "severity": "WARN",
                "current_value": "128M",
                "description": "InnoDB缓冲池过小",
            }
        ]

        status_metrics = {
            "Questions": 20000.0,  # 高QPS
            "Connections": 100.0,
            "Aborted_connects": 0.0,
            "Threads_running": 10.0,
        }

        result = self.calculator.calculate_score(
            violations=violations,
            mysql_version="8.0.0",
            status_metrics=status_metrics,
        )

        explanation = self.calculator.get_score_explanation(result)

        # 负载调整因子不为1时应该显示
        assert "负载调整: 1.50x" in explanation
        assert "高QPS环境" in explanation

    def test_score_explanation_with_trend_adjustment(self):
        """测试评分解释中显示趋势调整"""
        historical_scores = [80, 85, 90, 92]  # 连续上升

        result = self.calculator.calculate_score(
            violations=[],
            mysql_version="8.0.0",
            historical_scores=historical_scores,
        )

        explanation = self.calculator.get_score_explanation(result)

        # 趋势调整不为0时应该显示
        assert "趋势调整: +5分" in explanation
        assert "连续上升趋势" in explanation

    def test_historical_trend_with_two_scores_increasing(self):
        """测试只有2个历史分数且上升的场景"""
        historical_scores = [80, 85]  # 连续上升，只有2个

        result = self.calculator.calculate_score(
            violations=[],
            mysql_version="8.0.0",
            historical_scores=historical_scores,
        )

        # 应该有趋势调整
        # 平均82.5，最新85，增加(85-82.5)*0.95=2.375，取整2
        assert result["trend_adjustment"]["amount"] == 2
        assert "连续上升趋势" in result["trend_adjustment"]["description"]

    def test_historical_trend_with_two_scores_decreasing(self):
        """测试只有2个历史分数且下降的场景"""
        historical_scores = [90, 85]  # 连续下降，只有2个

        result = self.calculator.calculate_score(
            violations=[],
            mysql_version="8.0.0",
            historical_scores=historical_scores,
        )

        # 应该有趋势调整
        # 平均87.5，最新85，减少(87.5-85)*0.95=2.375，取整2
        assert result["trend_adjustment"]["amount"] == -2
        assert "连续下降趋势" in result["trend_adjustment"]["description"]

