"""
级联删除服务模块

提供程序级级联删除功能，替代数据库外键约束
支持事务回滚和批量删除优化
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update
from app.models.connection import Connection

# 条件导入可选模型
try:
    from app.models.alert import AlertRule, AlertHistory
except ImportError:
    AlertRule = None
    AlertHistory = None

try:
    from app.models.slow_query import SlowQuery
except ImportError:
    SlowQuery = None

try:
    from app.models.query_fingerprint import QueryFingerprint
except ImportError:
    QueryFingerprint = None

try:
    from app.models.metric import PerformanceMetric
except ImportError:
    PerformanceMetric = None

try:
    from app.models.report import Report
except ImportError:
    Report = None

try:
    from app.models.wait_event_cache import WaitEventCache
except ImportError:
    WaitEventCache = None

try:
    from app.models.index_suggestion import IndexSuggestion
except ImportError:
    IndexSuggestion = None

try:
    from app.models.config_analysis import ConfigAnalysisHistory
except ImportError:
    ConfigAnalysisHistory = None


def validate_connection_exists(db: Session, connection_id: int) -> bool:
    """验证连接是否存在

    Args:
        db: 数据库会话
        connection_id: 连接ID

    Returns:
        True如果连接存在，False otherwise
    """
    connection = db.execute(
        select(Connection).where(Connection.id == connection_id)
    ).scalar_one_or_none()
    return connection is not None


def cascade_delete_connection(db: Session, connection_id: int) -> bool:
    """级联删除连接及其所有关联数据

    删除顺序（避免外键冲突，虽然我们移除了外键，但保持顺序是好习惯）：
    1. AlertHistory（依赖AlertRule）
    2. AlertRule（依赖Connection）
    3. PerformanceMetric（依赖Connection）
    4. SlowQuery（依赖Connection）
    5. Report（依赖Connection）
    6. QueryFingerprint（依赖Connection）
    7. WaitEventCache（依赖Connection）
    8. IndexSuggestion（依赖Connection）
    9. ConfigAnalysisHistory（依赖Connection）
    10. Connection（最后删除）

    Args:
        db: 数据库会话
        connection_id: 连接ID

    Returns:
        True如果删除成功，False otherwise

    Raises:
        会回滚所有更改
    """
    # 先验证连接是否存在
    if not validate_connection_exists(db, connection_id):
        return False

    try:
        # 1. 删除AlertHistory (如果模型存在)
        if AlertHistory is not None:
            db.execute(
                delete(AlertHistory).where(AlertHistory.connection_id == connection_id)
            )

        # 2. 删除AlertRule (如果模型存在)
        if AlertRule is not None:
            db.execute(delete(AlertRule).where(AlertRule.connection_id == connection_id))

        # 3. 删除PerformanceMetric (如果模型存在)
        if PerformanceMetric is not None:
            db.execute(
                delete(PerformanceMetric).where(
                    PerformanceMetric.connection_id == connection_id
                )
            )

        # 4. 删除SlowQuery (如果模型存在)
        if SlowQuery is not None:
            db.execute(delete(SlowQuery).where(SlowQuery.connection_id == connection_id))

        # 5. 删除Report (如果模型存在)
        if Report is not None:
            db.execute(delete(Report).where(Report.connection_id == connection_id))

        # 6. 删除QueryFingerprint (如果模型存在)
        if QueryFingerprint is not None:
            db.execute(
                delete(QueryFingerprint).where(
                    QueryFingerprint.connection_id == connection_id
                )
            )

        # 7. 删除WaitEventCache (如果模型存在)
        if WaitEventCache is not None:
            db.execute(
                delete(WaitEventCache).where(WaitEventCache.connection_id == connection_id)
            )

        # 8. 删除IndexSuggestion (如果模型存在)
        if IndexSuggestion is not None:
            db.execute(
                delete(IndexSuggestion).where(
                    IndexSuggestion.connection_id == connection_id
                )
            )

        # 9. 删除ConfigAnalysisHistory (如果模型存在)
        if ConfigAnalysisHistory is not None:
            db.execute(
                delete(ConfigAnalysisHistory).where(
                    ConfigAnalysisHistory.connection_id == connection_id
                )
            )

        # 10. 删除Connection
        db.execute(delete(Connection).where(Connection.id == connection_id))

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise e


def delete_alert_rule_with_history(db: Session, rule_id: int) -> bool:
    """删除告警规则及其告警历史

    Args:
        db: 数据库会话
        rule_id: 告警规则ID

    Returns:
        True如果删除成功，False otherwise

    Raises:
        会回滚所有更改
    """
    try:
        # 1. 删除AlertHistory
        db.execute(delete(AlertHistory).where(AlertHistory.alert_rule_id == rule_id))

        # 2. 删除AlertRule
        db.execute(delete(AlertRule).where(AlertRule.id == rule_id))

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise e


def delete_fingerprint_with_slow_queries(db: Session, fingerprint_id: int) -> bool:
    """删除查询指纹，并将慢查询的fingerprint_id设为NULL

    注意：保留SlowQuery.fingerprint_id的SET NULL行为

    Args:
        db: 数据库会话
        fingerprint_id: 查询指纹ID

    Returns:
        True如果删除成功，False otherwise

    Raises:
        会回滚所有更改
    """
    try:
        # 1. 先将SlowQuery.fingerprint_id设为NULL（SET NULL行为）
        db.execute(
            update(SlowQuery)
            .where(SlowQuery.fingerprint_id == fingerprint_id)
            .values(fingerprint_id=None)
        )

        # 2. 删除QueryFingerprint
        db.execute(
            delete(QueryFingerprint).where(QueryFingerprint.id == fingerprint_id)
        )

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        raise e
