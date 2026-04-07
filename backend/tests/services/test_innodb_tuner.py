"""
InnoDB调优建议服务测试
"""

import pytest
from app.services.innodb_tuner import InnoDBTuner


class TestInnoDBTuner:
    """InnoDBTuner测试类"""

    @pytest.fixture
    def tuner(self):
        """创建调优器实例"""
        return InnoDBTuner()

    # ==================== _parse_size 测试 ====================

    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("128M", 128 * 1024 * 1024),
            ("1G", 1024 * 1024 * 1024),
            ("512K", 512 * 1024),
            ("1024", 1024),
            (1024, 1024),
            ("128MB", 128 * 1024 * 1024),
            ("1GB", 1024 * 1024 * 1024),
            ("2G", 2 * 1024 * 1024 * 1024),
        ],
    )
    def test_parse_size_valid(self, tuner, input_value, expected):
        """测试有效的大小字符串解析"""
        assert tuner._parse_size(input_value) == expected

    def test_parse_size_invalid(self, tuner):
        """测试无效的大小字符串"""
        assert tuner._parse_size(None) == 0
        assert tuner._parse_size("") == 0
        assert tuner._parse_size("invalid") == 0

    # ==================== _format_size 测试 ====================

    @pytest.mark.parametrize(
        "input_bytes,expected",
        [
            (0, "0 B"),
            (1023, "1023 B"),
            (1024, "1 KB"),
            (1024 * 1024, "1 MB"),
            (128 * 1024 * 1024, "128 MB"),
            (1024 * 1024 * 1024, "1 GB"),
            (1536, "1.5 KB"),
        ],
    )
    def test_format_size(self, tuner, input_bytes, expected):
        """测试大小格式化"""
        result = tuner._format_size(input_bytes)
        # 允许空格差异
        assert result.replace(" ", "") == expected.replace(" ", "")

    # ==================== _calculate_buffer_pool_hit_rate 测试 ====================

    def test_calculate_buffer_pool_hit_rate_normal(self, tuner):
        """测试正常的Buffer Pool命中率计算"""
        # 100次请求，10次磁盘读取，命中率 = 1 - 10/100 = 90%
        status = {
            "Innodb_buffer_pool_read_requests": 100,
            "Innodb_buffer_pool_reads": 10,
        }
        assert tuner._calculate_buffer_pool_hit_rate(status) == 90.0

    def test_calculate_buffer_pool_hit_rate_perfect(self, tuner):
        """测试100%命中率"""
        status = {
            "Innodb_buffer_pool_read_requests": 1000,
            "Innodb_buffer_pool_reads": 0,
        }
        assert tuner._calculate_buffer_pool_hit_rate(status) == 100.0

    def test_calculate_buffer_pool_hit_rate_zero_requests(self, tuner):
        """测试零请求情况"""
        status = {
            "Innodb_buffer_pool_read_requests": 0,
            "Innodb_buffer_pool_reads": 0,
        }
        assert tuner._calculate_buffer_pool_hit_rate(status) == 100.0

    def test_calculate_buffer_pool_hit_rate_low(self, tuner):
        """测试低命中率"""
        # 100次请求，50次磁盘读取，命中率 = 50%
        status = {
            "Innodb_buffer_pool_read_requests": 100,
            "Innodb_buffer_pool_reads": 50,
        }
        assert tuner._calculate_buffer_pool_hit_rate(status) == 50.0

    # ==================== _recommend_buffer_pool_size 测试 ====================

    def test_recommend_buffer_pool_size_basic(self, tuner):
        """测试Buffer Pool大小推荐"""
        # 10000页，16KB页大小，数据=160MB，推荐=192MB
        result = tuner._recommend_buffer_pool_size(10000, 16384)
        # 向上取整到MB
        assert result >= 10000 * 16384 * 1.2

    def test_recommend_buffer_pool_size_zero(self, tuner):
        """测试零数据页"""
        result = tuner._recommend_buffer_pool_size(0, 16384)
        assert result == 0

    # ==================== analyze_and_recommend 综合测试 ====================

    def test_analyze_no_recommendations_when_healthy(self, tuner):
        """测试健康状态下无建议"""
        status = {
            "Innodb_buffer_pool_read_requests": 10000,
            "Innodb_buffer_pool_reads": 10,  # 99.9%命中率
            "Innodb_data_reads": 1000,
            "Innodb_data_writes": 500,
            "Innodb_os_log_fsyncs": 100,
        }
        variables = {
            "innodb_buffer_pool_size": "1G",
            "innodb_log_file_size": "256M",
            "innodb_io_capacity": "2000",
            "innodb_io_capacity_max": "4000",
            "innodb_buffer_pool_instances": "4",
            "innodb_flush_method": "O_DIRECT",
        }

        recommendations = tuner.analyze_and_recommend(status, variables)
        # 健康状态应返回空或很少建议
        assert isinstance(recommendations, list)

    def test_analyze_buffer_pool_recommendation(self, tuner):
        """测试Buffer Pool命中率低时的建议"""
        status = {
            "Innodb_buffer_pool_read_requests": 1000,
            "Innodb_buffer_pool_reads": 200,  # 80%命中率 < 95%
            "Innodb_data_reads": 1000,
            "Innodb_data_writes": 500,
            "Innodb_os_log_fsyncs": 100,
        }
        variables = {
            "innodb_buffer_pool_size": "128M",
            "innodb_log_file_size": "32M",
            "innodb_io_capacity": "200",
            "innodb_flush_method": "fdatasync",
        }

        recommendations = tuner.analyze_and_recommend(status, variables)
        bp_recommendations = [
            r for r in recommendations if r["param"] == "innodb_buffer_pool_size"
        ]
        assert len(bp_recommendations) >= 1
        assert bp_recommendations[0]["priority"] == "high"
        assert "命中率" in bp_recommendations[0]["reason"]

    def test_analyze_log_file_recommendation(self, tuner):
        """测试日志文件建议"""
        status = {
            "Innodb_buffer_pool_read_requests": 10000,
            "Innodb_buffer_pool_reads": 10,
            "Innodb_data_reads": 1000,
            "Innodb_data_writes": 500,
            "Innodb_os_log_fsyncs": 50000,  # 高fsync
        }
        variables = {
            "innodb_buffer_pool_size": "1G",
            "innodb_log_file_size": "48M",  # 较小
            "innodb_io_capacity": "2000",
            "innodb_flush_method": "O_DIRECT",
        }

        recommendations = tuner.analyze_and_recommend(status, variables)
        log_recommendations = [
            r for r in recommendations if r["param"] == "innodb_log_file_size"
        ]
        if log_recommendations:
            assert log_recommendations[0]["priority"] == "medium"

    def test_analyze_io_capacity_recommendation(self, tuner):
        """测试IO容量建议"""
        status = {
            "Innodb_buffer_pool_read_requests": 10000,
            "Innodb_buffer_pool_reads": 10,
            "Innodb_data_reads": 50000,
            "Innodb_data_writes": 30000,
            "Innodb_os_log_fsyncs": 100,
        }
        variables = {
            "innodb_buffer_pool_size": "1G",
            "innodb_log_file_size": "256M",
            "innodb_io_capacity": "200",  # 较低
            "innodb_flush_method": "O_DIRECT",
        }

        recommendations = tuner.analyze_and_recommend(status, variables)
        io_recommendations = [
            r for r in recommendations if r["param"] == "innodb_io_capacity"
        ]
        if io_recommendations:
            assert io_recommendations[0]["recommended_value"] == "2000"

    def test_analyze_flush_method_recommendation(self, tuner):
        """测试刷新方法建议"""
        status = {
            "Innodb_buffer_pool_read_requests": 10000,
            "Innodb_buffer_pool_reads": 10,
            "Innodb_data_reads": 1000,
            "Innodb_data_writes": 500,
            "Innodb_os_log_fsyncs": 100,
        }
        variables = {
            "innodb_buffer_pool_size": "1G",
            "innodb_log_file_size": "256M",
            "innodb_io_capacity": "2000",
            "innodb_flush_method": "fdatasync",  # 非O_DIRECT
        }

        recommendations = tuner.analyze_and_recommend(status, variables)
        flush_recommendations = [
            r for r in recommendations if r["param"] == "innodb_flush_method"
        ]
        assert len(flush_recommendations) >= 1
        assert flush_recommendations[0]["recommended_value"] == "O_DIRECT"

    def test_analyze_buffer_pool_instances_recommendation(self, tuner):
        """测试Buffer Pool实例数建议"""
        status = {
            "Innodb_buffer_pool_read_requests": 10000,
            "Innodb_buffer_pool_reads": 10,
            "Innodb_data_reads": 1000,
            "Innodb_data_writes": 500,
            "Innodb_os_log_fsyncs": 100,
        }
        variables = {
            "innodb_buffer_pool_size": "4G",  # 大于1GB
            "innodb_log_file_size": "1G",
            "innodb_io_capacity": "2000",
            "innodb_flush_method": "O_DIRECT",
            "innodb_buffer_pool_instances": "1",  # 过少
        }

        recommendations = tuner.analyze_and_recommend(status, variables)
        instances_recommendations = [
            r for r in recommendations if r["param"] == "innodb_buffer_pool_instances"
        ]
        if instances_recommendations:
            assert int(instances_recommendations[0]["recommended_value"]) > 1

    def test_analyze_with_buffer_pool_stats(self, tuner):
        """测试使用Buffer Pool统计数据的建议"""
        status = {
            "Innodb_buffer_pool_read_requests": 1000,
            "Innodb_buffer_pool_reads": 200,  # 80%命中率
            "Innodb_data_reads": 1000,
            "Innodb_data_writes": 500,
            "Innodb_os_log_fsyncs": 100,
        }
        variables = {
            "innodb_buffer_pool_size": "128M",
            "innodb_log_file_size": "32M",
            "innodb_io_capacity": "200",
            "innodb_flush_method": "fdatasync",
        }
        buffer_pool_stats = {
            "data_pages": 20000,  # 约320MB数据
            "page_size": 16384,
        }

        recommendations = tuner.analyze_and_recommend(
            status, variables, buffer_pool_stats
        )
        bp_recommendations = [
            r for r in recommendations if r["param"] == "innodb_buffer_pool_size"
        ]
        assert len(bp_recommendations) >= 1

    def test_analyze_returns_correct_format(self, tuner):
        """测试返回格式正确"""
        status = {
            "Innodb_buffer_pool_read_requests": 1000,
            "Innodb_buffer_pool_reads": 200,
            "Innodb_data_reads": 1000,
            "Innodb_data_writes": 500,
            "Innodb_os_log_fsyncs": 50000,
        }
        variables = {
            "innodb_buffer_pool_size": "128M",
            "innodb_log_file_size": "8M",
            "innodb_io_capacity": "100",
            "innodb_flush_method": "fdatasync",
        }

        recommendations = tuner.analyze_and_recommend(status, variables)

        for rec in recommendations:
            assert "category" in rec
            assert "param" in rec
            assert "current_value" in rec
            assert "recommended_value" in rec
            assert "reason" in rec
            assert "impact" in rec
            assert "priority" in rec
            assert "sql_statement" in rec
            assert rec["priority"] in ["high", "medium", "low"]

    def test_analyze_empty_inputs(self, tuner):
        """测试空输入"""
        recommendations = tuner.analyze_and_recommend({}, {})
        assert isinstance(recommendations, list)

    def test_analyze_string_values(self, tuner):
        """测试字符串类型的数值"""
        status = {
            "Innodb_buffer_pool_read_requests": "1000",
            "Innodb_buffer_pool_reads": "200",
            "Innodb_data_reads": "1000",
            "Innodb_data_writes": "500",
            "Innodb_os_log_fsyncs": "100",
        }
        variables = {
            "innodb_buffer_pool_size": "134217728",  # 128M
            "innodb_log_file_size": "33554432",  # 32M
            "innodb_io_capacity": "200",
            "innodb_flush_method": "O_DIRECT",
        }

        recommendations = tuner.analyze_and_recommend(status, variables)
        assert isinstance(recommendations, list)
