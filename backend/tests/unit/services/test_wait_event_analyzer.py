"""
等待事件分析服务测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from app.services.wait_event_analyzer import WaitEventAnalyzer
from app.models.wait_event_cache import WaitEventCache
from app.models.slow_query import SlowQuery


class TestWaitEventAnalyzer:
    """测试等待事件分析器"""

    def test_identify_bottleneck_empty(self):
        """测试空事件列表"""
        result = WaitEventAnalyzer.identify_bottleneck([])
        assert result == "none"

    def test_identify_bottleneck_zero_wait(self):
        """测试零等待时间"""
        wait_events = [
            WaitEventCache(
                connection_id=1,
                event_name="wait/io/file/innodb/innodb_data_file",
                event_class="io",
                wait_time=0.0,
                wait_count=100,
            )
        ]
        result = WaitEventAnalyzer.identify_bottleneck(wait_events)
        assert result == "none"

    def test_identify_bottleneck_io_bound(self):
        """测试I/O密集型瓶颈"""
        wait_events = [
            WaitEventCache(
                connection_id=1,
                event_name="wait/io/file/innodb/innodb_data_file",
                event_class="io",
                wait_time=10.0,
                wait_count=100,
            ),
            WaitEventCache(
                connection_id=1,
                event_name="wait/io/file/innodb/innodb_log_file",
                event_class="io",
                wait_time=5.0,
                wait_count=50,
            ),
            WaitEventCache(
                connection_id=1,
                event_name="wait/synch/mutex/innodb/log_sys_mutex",
                event_class="mutex",
                wait_time=1.0,
                wait_count=20,
            ),
        ]
        result = WaitEventAnalyzer.identify_bottleneck(wait_events)
        assert result == "io-bound"

    def test_identify_bottleneck_lock_wait(self):
        """测试锁等待瓶颈"""
        wait_events = [
            WaitEventCache(
                connection_id=1,
                event_name="wait/lock/table/lock",
                event_class="lock",
                wait_time=10.0,
                wait_count=100,
            ),
            WaitEventCache(
                connection_id=1,
                event_name="wait/synch/rwlock/innodb/lock_sys",
                event_class="rwlock",
                wait_time=5.0,
                wait_count=50,
            ),
            WaitEventCache(
                connection_id=1,
                event_name="wait/io/file/innodb/innodb_data_file",
                event_class="io",
                wait_time=1.0,
                wait_count=20,
            ),
        ]
        result = WaitEventAnalyzer.identify_bottleneck(wait_events)
        assert result == "lock-wait"

    def test_identify_bottleneck_cpu_bound(self):
        """测试CPU密集型瓶颈"""
        wait_events = [
            WaitEventCache(
                connection_id=1,
                event_name="wait/synch/mutex/innodb/buf_pool_mutex",
                event_class="mutex",
                wait_time=10.0,
                wait_count=100,
            ),
            WaitEventCache(
                connection_id=1,
                event_name="wait/synch/rwlock/innodb/checkpoint_lock",
                event_class="rwlock",
                wait_time=2.0,
                wait_count=30,
            ),
            WaitEventCache(
                connection_id=1,
                event_name="wait/io/file/innodb/innodb_data_file",
                event_class="io",
                wait_time=1.0,
                wait_count=20,
            ),
        ]
        result = WaitEventAnalyzer.identify_bottleneck(wait_events)
        assert result == "cpu-bound"

    def test_get_wait_events_summary_empty(self, db_session, test_connection):
        """测试空等待事件汇总"""
        summary = WaitEventAnalyzer.get_wait_events_summary(
            db_session, test_connection.id, hours=24
        )

        assert summary["total_events"] == 0
        assert summary["total_wait_time"] == 0
        assert summary["bottleneck_type"] == "none"
        assert summary["top_events"] == []

    def test_get_wait_events_summary_with_data(self, db_session, test_connection):
        """测试有数据的等待事件汇总"""
        # 创建等待事件
        events = [
            WaitEventCache(
                id=i,
                connection_id=test_connection.id,
                event_name=f"wait/io/file/innodb/innodb_data_file_{i}",
                event_class="io",
                wait_time=float(i + 1),
                wait_count=(i + 1) * 10,
                timestamp=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]
        for event in events:
            db_session.add(event)
        db_session.commit()

        summary = WaitEventAnalyzer.get_wait_events_summary(
            db_session, test_connection.id, hours=24
        )

        assert summary["total_events"] == 5
        assert summary["total_wait_time"] == 15.0  # 1+2+3+4+5
        assert "bottleneck_type" in summary
        assert len(summary["top_events"]) <= 20

    def test_analyze_multi_dimensional(self, db_session, test_connection):
        """测试多维分析"""
        # 创建慢查询
        now = datetime.now(timezone.utc)
        slow_query = SlowQuery(
            id=1,
            connection_id=test_connection.id,
            query_hash="abc123",
            full_sql="SELECT * FROM users",
            query_time=2.5,
            timestamp=now,
        )
        db_session.add(slow_query)
        db_session.commit()

        # 创建关联的等待事件
        wait_event = WaitEventCache(
            id=1,
            connection_id=test_connection.id,
            event_name="wait/io/file/innodb/innodb_data_file",
            event_class="io",
            wait_time=5.0,
            wait_count=100,
            timestamp=now,
        )
        db_session.add(wait_event)
        db_session.commit()

        result = WaitEventAnalyzer.analyze_multi_dimensional(
            db_session, test_connection.id, slow_query.id
        )

        assert result["slow_query_id"] == slow_query.id
        assert "bottleneck_type" in result
        assert result["total_wait_events"] >= 0
        assert "top_events" in result

    def test_analyze_multi_dimensional_slow_query_not_found(
        self, db_session, test_connection
    ):
        """测试慢查询不存在的情况"""
        with pytest.raises(ValueError) as exc_info:
            WaitEventAnalyzer.analyze_multi_dimensional(
                db_session, test_connection.id, 99999
            )

        assert "not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_thresholds_and_alert(self, db_session, test_connection):
        """测试阈值检查和告警"""
        # 创建高等待时间的事件
        event = WaitEventCache(
            id=1,
            connection_id=test_connection.id,
            event_name="wait/io/file/innodb/innodb_data_file",
            event_class="io",
            wait_time=1.0,  # 超过0.5秒阈值
            wait_count=10,
            timestamp=datetime.now(timezone.utc),
        )
        db_session.add(event)
        db_session.commit()

        with patch("app.services.wait_event_analyzer.manager") as mock_manager:
            mock_manager.broadcast_to_connection = AsyncMock()

            alert_events = await WaitEventAnalyzer.check_thresholds_and_alert(
                db_session, test_connection.id, threshold_seconds=0.5
            )

            assert len(alert_events) == 1
            assert (
                alert_events[0]["event_name"] == "wait/io/file/innodb/innodb_data_file"
            )

    @pytest.mark.asyncio
    async def test_check_thresholds_no_alerts(self, db_session, test_connection):
        """测试无告警情况"""
        # 创建低等待时间的事件
        event = WaitEventCache(
            id=1,
            connection_id=test_connection.id,
            event_name="wait/io/file/innodb/innodb_data_file",
            event_class="io",
            wait_time=0.1,  # 低于0.5秒阈值
            wait_count=10,
            timestamp=datetime.now(timezone.utc),
        )
        db_session.add(event)
        db_session.commit()

        alert_events = await WaitEventAnalyzer.check_thresholds_and_alert(
            db_session, test_connection.id, threshold_seconds=0.5
        )

        assert len(alert_events) == 0

    def test_collect_wait_events_connection_not_found(self, db_session):
        """测试连接不存在时收集等待事件"""
        with pytest.raises(ValueError) as exc_info:
            WaitEventAnalyzer.collect_wait_events(db_session, 99999)

        assert "not found" in str(exc_info.value)
