"""
PerformanceMetric CRUD 单元测试
测试性能指标的CRUD操作
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.crud.metric import (
    get_metric,
    get_metrics,
    get_latest_metric,
    create_metric,
    create_metrics_bulk,
    delete_old_metrics,
    get_metric_aggregations,
)
from app.models.metric import PerformanceMetric
from app.schemas.metric import PerformanceMetricCreate
from tests.conftest import BIGINT_ID_COUNTER, increment_bigint_id


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    return Mock(spec=Session)


@pytest.fixture
def test_metric(db_session):
    """测试性能指标"""
    metric_id = BIGINT_ID_COUNTER["metric"]
    BIGINT_ID_COUNTER["metric"] += 1

    metric = PerformanceMetric(
        id=metric_id,
        connection_id=1,
        metric_name="qps",
        metric_value=100.5,
        collected_at=datetime.now(timezone.utc),
    )

    db_session.execute.return_value = Mock(scalar_one_or_none=metric)
    db_session.commit.return_value = None

    result = get_metric(db=db_session, metric_id=metric_id)
    assert result is not None
    assert result.id == metric_id
    assert result.metric_name == "qps"


def test_get_metric_not_found(db_session):
    """测试获取不存在的指标"""
    # 正确配置Mock链式调用
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    db_session.execute.return_value = mock_result

    result = get_metric(db=db_session, metric_id=999)
    assert result is None


class TestGetMetrics:
    """获取指标列表测试"""

    def test_get_metrics_basic(self, db_session):
        """测试基本指标列表"""
        metrics = [
            PerformanceMetric(
                id=i,
                connection_id=1,
                metric_name="qps",
                metric_value=float(i * 10),
                collected_at=datetime.now(timezone.utc),
            )
            for i in range(1, 4)
        ]

        # 正确配置Mock链式调用
        mock_scalars = Mock()
        mock_scalars.all.return_value = metrics
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result

        result = get_metrics(db=db_session, connection_id=1)
        assert len(result) == 3

    def test_get_metrics_with_metric_name_filter(self, db_session):
        """测试按指标名称筛选"""
        all_metrics = [
            PerformanceMetric(
                id=i,
                connection_id=1,
                metric_name="qps" if i < 3 else "tps",
                metric_value=float(i * 10),
                collected_at=datetime.now(timezone.utc),
            )
            for i in range(1, 6)
        ]

        # 正确配置Mock链式调用
        mock_scalars = Mock()
        mock_scalars.all.return_value = all_metrics
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result

        result = get_metrics(db=db_session, connection_id=1, metric_name="qps")
        assert len(result) == 5

    def test_get_metrics_with_time_range(self, db_session):
        """测试按时间范围筛选"""
        metrics = [
            PerformanceMetric(
                id=i,
                connection_id=1,
                metric_name="qps",
                metric_value=float(i * 10),
                collected_at=datetime.now(timezone.utc) - timedelta(hours=i),
            )
            for i in range(1, 4)
        ]

        # 正确配置Mock链式调用
        mock_scalars = Mock()
        mock_scalars.all.return_value = metrics
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result

        start_time = datetime.now(timezone.utc) - timedelta(hours=2)
        end_time = datetime.now(timezone.utc) - timedelta(hours=1)

        result = get_metrics(
            db=db_session,
            connection_id=1,
            start_time=start_time,
            end_time=end_time,
        )
        assert len(result) == 3

    def test_get_metrics_with_pagination(self, db_session):
        """测试分页"""
        metrics = [
            PerformanceMetric(
                id=i,
                connection_id=1,
                metric_name="qps",
                metric_value=float(i * 10),
                collected_at=datetime.now(timezone.utc),
            )
            for i in range(1, 12)
        ]

        # 正确配置Mock链式调用
        mock_scalars = Mock()
        mock_scalars.all.return_value = metrics
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result

        result = get_metrics(db=db_session, connection_id=1, skip=5, limit=5)
        assert len(result) == 11

    def test_get_metrics_empty(self, db_session):
        """测试空指标列表"""
        # 正确配置Mock链式调用
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result

        result = get_metrics(db=db_session, connection_id=1)
        assert result == []


class TestGetLatestMetric:
    """获取最新指标测试"""

    def test_get_latest_metric_success(self, db_session):
        """测试获取最新指标成功"""
        metric_id = BIGINT_ID_COUNTER["metric"]
        BIGINT_ID_COUNTER["metric"] += 1

        metric = PerformanceMetric(
            id=metric_id,
            connection_id=1,
            metric_name="qps",
            metric_value=100.5,
            collected_at=datetime.now(timezone.utc),
        )

        # 正确配置Mock链式调用
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = metric
        db_session.execute.return_value = mock_result

        result = get_latest_metric(db=db_session, connection_id=1, metric_name="qps")
        assert result is not None
        assert result.metric_value == 100.5

    def test_get_latest_metric_not_found(self, db_session):
        """测试获取不存在的最新指标"""
        # 正确配置Mock链式调用
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        db_session.execute.return_value = mock_result

        result = get_latest_metric(db=db_session, connection_id=1, metric_name="qps")
        assert result is None

    def test_get_latest_metric_without_metric_name(self, db_session):
        """测试不指定指标名称获取最新"""
        metric_id = BIGINT_ID_COUNTER["metric"]
        BIGINT_ID_COUNTER["metric"] += 1

        metric = PerformanceMetric(
            id=metric_id,
            connection_id=1,
            metric_name="tps",
            metric_value=50.0,
            collected_at=datetime.now(timezone.utc),
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = metric
        db_session.execute.return_value = mock_result

        result = get_latest_metric(db=db_session, connection_id=1, metric_name=None)
        assert result is not None
        assert result.metric_name == "tps"


class TestCreateMetric:
    """创建指标测试"""

    def test_create_metric_basic(self, db_session):
        """测试基本指标创建"""
        metric_data = PerformanceMetricCreate(
            connection_id=1,
            metric_name="qps",
            metric_value=100.5,
        )

        db_session.add.return_value = None
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        result = create_metric(db=db_session, metric=metric_data)
        assert result.metric_value == 100.5
        assert result.metric_name == "qps"

    def test_create_metric_all_fields(self, db_session):
        """测试创建包含所有字段的指标"""
        metric_data = PerformanceMetricCreate(
            connection_id=1,
            metric_name="qps",
            metric_value=100.5,
        )

        db_session.add.return_value = None
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        result = create_metric(db=db_session, metric=metric_data)
        assert result.metric_value == 100.5


class TestCreateMetricsBulk:
    """批量创建指标测试"""

    def test_create_metrics_bulk_empty(self, db_session):
        """测试空列表"""
        result = create_metrics_bulk(db=db_session, metrics=[])
        assert result == []

    def test_create_metrics_bulk_single(self, db_session):
        """测试单个指标批量创建"""
        metric_data = PerformanceMetricCreate(
            connection_id=1,
            metric_name="qps",
            metric_value=100.5,
        )

        db_session.add_all.return_value = None
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        result = create_metrics_bulk(db=db_session, metrics=[metric_data])
        assert len(result) == 1

    def test_create_metrics_bulk_multiple(self, db_session):
        """测试多个指标批量创建"""
        metrics_data = [
            PerformanceMetricCreate(
                connection_id=1,
                metric_name="qps",
                metric_value=float(i * 10),
            )
            for i in range(1, 4)
        ]

        db_session.add_all.return_value = None
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        result = create_metrics_bulk(db=db_session, metrics=metrics_data)
        assert len(result) == 3


class TestDeleteOldMetrics:
    """删除旧指标测试"""

    def test_delete_old_metrics_some(self, db_session):
        """测试删除部分旧指标"""
        old_metrics = [
            PerformanceMetric(
                id=i,
                connection_id=1,
                metric_name="qps",
                metric_value=float(i * 10),
                collected_at=datetime.now(timezone.utc) - timedelta(days=i),
            )
            for i in range(1, 3)
        ]

        mock_scalars = Mock()
        mock_scalars.all.return_value = old_metrics
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result
        db_session.delete.return_value = None
        db_session.commit.return_value = None

        result = delete_old_metrics(db=db_session, connection_id=1, days_to_keep=30)
        assert result == 2

    def test_delete_old_metrics_none(self, db_session):
        """测试没有旧指标"""
        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result
        db_session.delete.return_value = None
        db_session.commit.return_value = None

        result = delete_old_metrics(db=db_session, connection_id=1, days_to_keep=30)
        assert result == 0

    def test_delete_old_metrics_custom_days(self, db_session):
        """测试自定义保留天数"""
        old_metrics = [
            PerformanceMetric(
                id=i,
                connection_id=1,
                metric_name="qps",
                metric_value=float(i * 10),
                collected_at=datetime.now(timezone.utc) - timedelta(days=i),
            )
            for i in range(1, 3)
        ]

        mock_scalars = Mock()
        mock_scalars.all.return_value = old_metrics
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result
        db_session.delete.return_value = None
        db_session.commit.return_value = None

        result = delete_old_metrics(db=db_session, connection_id=1, days_to_keep=60)
        assert result == 2

    def test_delete_old_metrics_all(self, db_session):
        """测试删除所有旧指标"""
        old_metrics = [
            PerformanceMetric(
                id=i,
                connection_id=1,
                metric_name="qps",
                metric_value=float(i * 10),
                collected_at=datetime.now(timezone.utc) - timedelta(days=i),
            )
            for i in range(1, 4)
        ]

        mock_scalars = Mock()
        mock_scalars.all.return_value = old_metrics
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        db_session.execute.return_value = mock_result
        db_session.delete.return_value = None
        db_session.commit.return_value = None

        result = delete_old_metrics(db=db_session, connection_id=1, days_to_keep=0)
        assert result == 3


class TestGetMetricAggregations:
    """指标聚合统计测试"""

    def test_get_metric_aggregations_basic(self, db_session):
        """测试基本聚合"""
        mock_result = Mock()
        mock_result.first.return_value = (4, 25.0, 10.0, 40.0)
        db_session.execute.return_value = mock_result

        result = get_metric_aggregations(
            db=db_session, connection_id=1, metric_name="qps"
        )
        assert result["count"] == 4
        assert result["avg"] == 25.0
        assert result["min"] == 10.0
        assert result["max"] == 40.0

    def test_get_metric_aggregations_with_time_range(self, db_session):
        """测试带时间范围的聚合"""
        mock_result = Mock()
        mock_result.first.return_value = (0, None, None, None)
        db_session.execute.return_value = mock_result

        result = get_metric_aggregations(
            db=db_session,
            connection_id=1,
            metric_name="qps",
            start_time=datetime.now(timezone.utc) - timedelta(hours=2),
            end_time=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        assert result["count"] == 0

    def test_get_metric_aggregations_no_data(self, db_session):
        """测试无数据的聚合"""
        mock_result = Mock()
        mock_result.first.return_value = None
        db_session.execute.return_value = mock_result

        result = get_metric_aggregations(
            db=db_session, connection_id=1, metric_name="qps"
        )
        assert result["count"] == 0
        assert result["avg"] is None
        assert result["min"] is None
        assert result["max"] is None

    def test_get_metric_aggregations_boundary_values(self, db_session):
        """测试边界值"""
        mock_result = Mock()
        mock_result.first.return_value = (3, 2.0, 1.0, 3.0)
        db_session.execute.return_value = mock_result

        result = get_metric_aggregations(
            db=db_session, connection_id=1, metric_name="qps"
        )
        assert result["count"] == 3
        assert result["min"] == 1.0
        assert result["max"] == 3.0

    def test_get_metric_aggregations_negative_values(self, db_session):
        """测试负值"""
        mock_result = Mock()
        mock_result.first.return_value = (3, -2.0, -3.0, -1.0)
        db_session.execute.return_value = mock_result

        result = get_metric_aggregations(
            db=db_session, connection_id=1, metric_name="qps"
        )
        assert result["count"] == 3
        assert result["min"] == -3.0
        assert result["max"] == -1.0
