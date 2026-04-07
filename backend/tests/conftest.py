"""
Pytest配置和共享fixtures - 更新版
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import hashlib

from app.database import Base, get_session
from app.main import app
from app.models.connection import Connection

# 条件导入 - 模型可能不存在
try:
    from app.models.alert import AlertRule, AlertHistory
except ImportError:
    AlertRule = None  # type: ignore
    AlertHistory = None  # type: ignore

try:
    from app.models.slow_query import SlowQuery
except ImportError:
    SlowQuery = None  # type: ignore

try:
    from app.models.metric import PerformanceMetric
except ImportError:
    PerformanceMetric = None  # type: ignore

try:
    from app.models.report import Report
except ImportError:
    Report = None  # type: ignore

try:
    from app.models.query_fingerprint import QueryFingerprint
except ImportError:
    QueryFingerprint = None  # type: ignore

try:
    from app.models.wait_event_cache import WaitEventCache
except ImportError:
    WaitEventCache = None  # type: ignore

try:
    from app.models.index_suggestion import IndexSuggestion
except ImportError:
    IndexSuggestion = None  # type: ignore

try:
    from app.models.config_analysis import ConfigAnalysisHistory
except ImportError:
    ConfigAnalysisHistory = None  # type: ignore


# SQLite自增ID计数器（用于BigInteger主键）
BIGINT_ID_COUNTER = {
    "alert_rule": 1,
    "alert_history": 1,
    "slow_query": 1,
    "metric": 1,
    "report": 1,
    "config_analysis": 1,
    "index_suggestion": 1,
}


def get_next_bigint_id(table_name: str) -> int:
    """获取下一个BigInteger ID（用于SQLite测试环境）"""
    return BIGINT_ID_COUNTER.get(table_name, 1)


def increment_bigint_id(table_name: str) -> None:
    """增加BigInteger ID计数器"""
    BIGINT_ID_COUNTER[table_name] = BIGINT_ID_COUNTER.get(table_name, 1) + 1


TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """创建测试用的数据库会话"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # 为SQLite测试环境添加事件监听器，自动生成BigInteger主键
    from sqlalchemy import event

    # 条件导入模型
    try:
        from app.models.alert import (
            AlertRule as _AlertRule,
            AlertHistory as _AlertHistory,
        )
    except ImportError:
        _AlertRule = None  # type: ignore
        _AlertHistory = None  # type: ignore

    try:
        from app.models.slow_query import SlowQuery as _SlowQuery
    except ImportError:
        _SlowQuery = None  # type: ignore

    try:
        from app.models.metric import PerformanceMetric as _PerformanceMetric
    except ImportError:
        _PerformanceMetric = None  # type: ignore

    try:
        from app.models.report import Report as _Report
    except ImportError:
        _Report = None  # type: ignore

    try:
        from app.models.config_analysis import (
            ConfigAnalysisHistory as _ConfigAnalysisHistory,
        )
    except ImportError:
        _ConfigAnalysisHistory = None  # type: ignore

    try:
        from app.models.index_suggestion import IndexSuggestion as _IndexSuggestion
    except ImportError:
        _IndexSuggestion = None  # type: ignore

    @event.listens_for(session, "before_flush")
    def generate_bigint_ids(session, context, instances):
        """在flush之前为BigInteger主键模型生成ID"""
        from tests.conftest import BIGINT_ID_COUNTER

        model_table_map = {}
        if _AlertRule is not None:
            model_table_map[_AlertRule] = "alert_rule"
        if _AlertHistory is not None:
            model_table_map[_AlertHistory] = "alert_history"
        if _SlowQuery is not None:
            model_table_map[_SlowQuery] = "slow_query"
        if _PerformanceMetric is not None:
            model_table_map[_PerformanceMetric] = "metric"
        if _Report is not None:
            model_table_map[_Report] = "report"
        if _ConfigAnalysisHistory is not None:
            model_table_map[_ConfigAnalysisHistory] = "config_analysis"
        if _IndexSuggestion is not None:
            model_table_map[_IndexSuggestion] = "index_suggestion"

        for instance in session.new:
            if instance.__class__ in model_table_map:
                table_name = model_table_map[instance.__class__]
                if instance.id is None:
                    instance.id = BIGINT_ID_COUNTER[table_name]
                    BIGINT_ID_COUNTER[table_name] += 1

    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session):
    """创建测试用的API客户端（带认证）"""
    from app.core.auth import create_access_token

    def override_get_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_session] = override_get_session

    # Create a test client with default auth headers
    token = create_access_token({"sub": "test_user", "user_id": 1})
    test_client = TestClient(app, headers={"Authorization": f"Bearer {token}"})

    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_connection_config():
    """模拟连接配置"""
    return {
        "host": "localhost",
        "port": 3306,
        "user": "test_user",
        "password": "test_password",
        "database": "test_db",
    }


@pytest.fixture(scope="function")
def sample_connection_data():
    """示例连接数据"""
    return {
        "name": "测试连接",
        "host": "127.0.0.1",
        "port": 3306,
        "username": "root",
        "password": "test_password",
        "database_name": "test_db",
        "connection_pool_size": 10,
        "is_active": True,
    }


@pytest.fixture(scope="function")
def sample_monitoring_data():
    """示例监控数据"""
    return {"interval": 5, "duration": 300}


@pytest.fixture(scope="function")
def sample_alert_rule_data():
    """示例告警规则数据"""
    return {
        "connection_id": 1,
        "rule_name": "测试告警",
        "metric_name": "cpu_usage",
        "condition_operator": ">",
        "threshold_value": 90.0,
        "time_window": 60,
        "severity": "critical",
        "notification_channels": {"system": True, "email": False},
        "is_enabled": True,
    }


@pytest.fixture(scope="function")
def sample_report_data():
    """示例报告数据"""
    from datetime import datetime

    return {
        "connection_id": 1,
        "report_type": "daily",
        "report_name": "测试日报",
        "description": "测试性能报告",
        "start_time": datetime(2024, 1, 1, 0, 0, 0),
        "end_time": datetime(2024, 1, 2, 0, 0, 0),
        "status": "completed",
    }


@pytest.fixture(scope="function")
def test_connection(db_session: Session):
    """创建测试连接"""
    connection = Connection(
        name="测试连接",
        host="localhost",
        port=3306,
        username="root",
        password_encrypted="encrypted_password",
        database_name="test_db",
        connection_pool_size=10,
        is_active=True,
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    return connection


@pytest.fixture(scope="function")
def test_alert_rule(db_session: Session, test_connection: Connection):
    """创建测试告警规则"""
    if AlertRule is None:
        pytest.skip("AlertRule 模型不存在")

    rule_id = BIGINT_ID_COUNTER["alert_rule"]
    BIGINT_ID_COUNTER["alert_rule"] += 1

    rule = AlertRule(
        id=rule_id,
        connection_id=test_connection.id,
        rule_name="测试告警规则",
        metric_name="cpu_usage",
        condition_operator=">",
        threshold_value=90.0,
        time_window=60,
        severity="critical",
        notification_channels={"system": True},
        is_enabled=True,
    )
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    return rule


@pytest.fixture(scope="function")
def test_slow_query(db_session: Session, test_connection: Connection):
    """创建测试慢查询"""
    if SlowQuery is None:
        pytest.skip("SlowQuery 模型不存在")

    slow_query_id = BIGINT_ID_COUNTER["slow_query"]
    BIGINT_ID_COUNTER["slow_query"] += 1

    query_hash = hashlib.md5("SELECT * FROM users".encode()).hexdigest()

    slow_query = SlowQuery(
        id=slow_query_id,
        connection_id=test_connection.id,
        query_hash=query_hash,
        sql_digest="SELECT * FROM users",
        full_sql="SELECT * FROM users WHERE status = 'active'",
        query_time=2.5,
        lock_time=0.1,
        rows_examined=1000,
        rows_sent=500,
        database_name="test_db",
        timestamp=datetime.now(),
        execution_count=10,
    )
    db_session.add(slow_query)
    db_session.commit()
    db_session.refresh(slow_query)
    return slow_query


@pytest.fixture(scope="function")
def test_performance_metric(db_session: Session, test_connection: Connection):
    """创建测试性能指标"""
    if PerformanceMetric is None:
        pytest.skip("PerformanceMetric 模型不存在")

    metric_id = BIGINT_ID_COUNTER["metric"]
    BIGINT_ID_COUNTER["metric"] += 1

    metric = PerformanceMetric(
        id=metric_id,
        connection_id=test_connection.id,
        metric_name="qps",
        metric_value=100.5,
        collected_at=datetime.now(),
    )
    db_session.add(metric)
    db_session.commit()
    db_session.refresh(metric)
    return metric


@pytest.fixture(scope="function")
def test_report(db_session: Session, test_connection: Connection):
    """创建测试报告"""
    if Report is None:
        pytest.skip("Report 模型不存在")

    from datetime import datetime

    report_id = BIGINT_ID_COUNTER["report"]
    BIGINT_ID_COUNTER["report"] += 1

    report = Report(
        id=report_id,
        connection_id=test_connection.id,
        report_type="daily",
        report_name="测试日报",
        description="测试性能报告",
        start_time=datetime(2024, 1, 1, 0, 0, 0),
        end_time=datetime(2024, 1, 2, 0, 0, 0),
        status="completed",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


@pytest.fixture(scope="function")
def mock_mysql_connector():
    routes_to_mock = [
        "app.routers.connections",
        "app.routers.slow_query",
        "app.routers.table",
        "app.routers.index",
        "app.routers.explain",
        "app.routers.monitoring",
        "app.routers.config",
    ]
    services_to_mock = [
        "app.services.index_analyzer",
        "app.services.table_analyzer",
        "app.services.slow_query_analyzer",
        "app.services.explain_analyzer",
        "app.services.performance_collector",
    ]

    patches = []
    mock_instances = []

    for route in routes_to_mock:
        try:
            p = patch(f"{route}.MySQLConnector")
            mock_connector = p.start()
            patches.append(p)

            mock_instance = Mock()
            mock_instance.test_connection.return_value = None
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance
            mock_instances.append(mock_instance)
        except Exception:
            pass

    for service in services_to_mock:
        try:
            p = patch(f"{service}.MySQLConnector")
            mock_connector = p.start()
            patches.append(p)

            mock_instance = Mock()
            mock_instance.test_connection.return_value = None
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_connector.return_value = mock_instance
            mock_instances.append(mock_instance)
        except Exception:
            pass

    yield mock_instances[0] if mock_instances else Mock()

    for p in patches:
        p.stop()


@pytest.fixture(scope="function")
def mock_performance_collector():
    """Mock性能采集器"""
    with patch("app.routers.monitoring.PerformanceCollector") as mock_collector:
        mock_instance = Mock()
        # 返回符合RealTimeMetrics结构的数据
        mock_instance.collect_realtime_metrics = AsyncMock(
            return_value={
                "qps": 100.5,
                "tps": 50.2,
                "connections": {"current": 10, "max": 100, "active": 8},
                "buffer_pool_hit_rate": 99.5,
                "queries": {"select": 100, "insert": 20, "update": 30, "delete": 10},
                "system": {"uptime": 3600, "thread_count": 8},
            }
        )
        # 注意：这是一个同步方法，不应该用AsyncMock
        mock_instance.get_slow_queries_from_performance_schema = Mock(
            return_value=[
                {
                    "sql_digest": "SELECT * FROM users",
                    "query_time": 2.5,
                    "rows_examined": 1000,
                    "query_hash": "abc123",
                }
            ]
        )
        mock_instance.stop_background_collection = AsyncMock(
            return_value={"status": "stopped"}
        )
        mock_collector.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_redis_cache():
    """Mock Redis缓存"""
    with patch("app.routers.monitoring.redis_cache") as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=None)
        yield mock_redis


@pytest.fixture(scope="function")
def auth_headers():
    """创建认证headers用于测试"""
    from app.core.auth import create_access_token

    token = create_access_token({"sub": "test_user", "user_id": 1})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_user(db_session: Session):
    """创建测试用户"""
    from app.models.user import User
    from app.core.auth import get_password_hash

    user = User(
        username="auth_test_user",
        password_hash=get_password_hash("password123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    yield user

    db_session.delete(user)
    db_session.commit()
