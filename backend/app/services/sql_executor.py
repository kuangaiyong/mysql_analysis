"""
SQL 执行服务 — 安全分类 + 执行 + 回滚命令生成

安全等级:
  - low:       SET GLOBAL / FLUSH 等运行时参数调整
  - medium:    CREATE INDEX / ALTER TABLE ADD INDEX（在线DDL）
  - high:      ALTER TABLE（结构变更）、大表操作
  - forbidden: DROP TABLE / TRUNCATE / DELETE 无 WHERE 等破坏性操作
"""

import re
import asyncio
import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from functools import partial

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FORBIDDEN = "forbidden"


RISK_LABELS = {
    RiskLevel.LOW: "低风险",
    RiskLevel.MEDIUM: "中风险",
    RiskLevel.HIGH: "高风险",
    RiskLevel.FORBIDDEN: "禁止执行",
}

RISK_COLORS = {
    RiskLevel.LOW: "#67C23A",
    RiskLevel.MEDIUM: "#E6A23C",
    RiskLevel.HIGH: "#F56C6C",
    RiskLevel.FORBIDDEN: "#909399",
}


@dataclass
class SQLClassification:
    """SQL 分类结果"""
    risk_level: RiskLevel
    risk_label: str
    risk_color: str
    description: str
    rollback_sql: Optional[str] = None
    impact: Optional[str] = None
    requires_confirmation: bool = True


# ==================== 禁止模式 ====================

_FORBIDDEN_PATTERNS = [
    (r"^\s*DROP\s+TABLE", "DROP TABLE 会导致数据永久丢失"),
    (r"^\s*DROP\s+DATABASE", "DROP DATABASE 会导致整个数据库丢失"),
    (r"^\s*TRUNCATE\s+", "TRUNCATE 会清空表中所有数据"),
    (r"^\s*DELETE\s+FROM\s+\S+\s*$", "DELETE 无 WHERE 条件会删除所有数据"),
    (r"^\s*DELETE\s+FROM\s+\S+\s*;?\s*$", "DELETE 无 WHERE 条件会删除所有数据"),
    (r"^\s*UPDATE\s+\S+\s+SET\s+.*(?<!WHERE\s.*)$", None),  # 单独处理
    (r"^\s*GRANT\s+", "GRANT 会修改用户权限"),
    (r"^\s*REVOKE\s+", "REVOKE 会修改用户权限"),
    (r"^\s*CREATE\s+USER", "CREATE USER 涉及权限管理"),
    (r"^\s*DROP\s+USER", "DROP USER 涉及权限管理"),
    (r"^\s*ALTER\s+USER", "ALTER USER 涉及权限管理"),
]


def classify_sql(sql: str) -> SQLClassification:
    """
    对 SQL 进行安全分类

    Args:
        sql: 待分类的 SQL 语句

    Returns:
        SQLClassification 分类结果
    """
    sql_stripped = sql.strip().rstrip(";").strip()
    sql_upper = sql_stripped.upper()

    # 1) 禁止类
    for pattern, reason in _FORBIDDEN_PATTERNS:
        if re.match(pattern, sql_stripped, re.IGNORECASE | re.DOTALL):
            if reason is None:
                continue
            return SQLClassification(
                risk_level=RiskLevel.FORBIDDEN,
                risk_label=RISK_LABELS[RiskLevel.FORBIDDEN],
                risk_color=RISK_COLORS[RiskLevel.FORBIDDEN],
                description=reason,
                requires_confirmation=False,
            )

    # UPDATE 无 WHERE
    if re.match(r"^\s*UPDATE\s+", sql_stripped, re.IGNORECASE):
        if "WHERE" not in sql_upper:
            return SQLClassification(
                risk_level=RiskLevel.FORBIDDEN,
                risk_label=RISK_LABELS[RiskLevel.FORBIDDEN],
                risk_color=RISK_COLORS[RiskLevel.FORBIDDEN],
                description="UPDATE 无 WHERE 条件会修改所有行",
                requires_confirmation=False,
            )

    # 2) 低风险: SET GLOBAL / FLUSH / ANALYZE TABLE
    if re.match(r"^\s*SET\s+(GLOBAL\s+|SESSION\s+)?", sql_stripped, re.IGNORECASE):
        var_match = re.match(
            r"^\s*SET\s+(?:GLOBAL\s+)?(\w+)\s*=\s*(.+)$", sql_stripped, re.IGNORECASE
        )
        rollback = None
        if var_match:
            var_name = var_match.group(1)
            rollback = f"-- 需要手动查询当前值后回滚:\n-- SHOW GLOBAL VARIABLES LIKE '{var_name}';"
        return SQLClassification(
            risk_level=RiskLevel.LOW,
            risk_label=RISK_LABELS[RiskLevel.LOW],
            risk_color=RISK_COLORS[RiskLevel.LOW],
            description="运行时参数调整，重启后失效",
            rollback_sql=rollback,
            impact="仅影响运行时配置，重启 MySQL 后恢复默认值",
            requires_confirmation=True,
        )

    if re.match(r"^\s*FLUSH\s+", sql_stripped, re.IGNORECASE):
        return SQLClassification(
            risk_level=RiskLevel.LOW,
            risk_label=RISK_LABELS[RiskLevel.LOW],
            risk_color=RISK_COLORS[RiskLevel.LOW],
            description="刷新操作，通常安全",
            impact="可能短暂影响性能",
            requires_confirmation=True,
        )

    if re.match(r"^\s*ANALYZE\s+TABLE\s+", sql_stripped, re.IGNORECASE):
        return SQLClassification(
            risk_level=RiskLevel.LOW,
            risk_label=RISK_LABELS[RiskLevel.LOW],
            risk_color=RISK_COLORS[RiskLevel.LOW],
            description="更新表统计信息，不影响数据",
            impact="短暂加读锁，对生产影响很小",
            requires_confirmation=True,
        )

    # 3) 中风险: CREATE INDEX / ALTER TABLE ADD INDEX
    if re.match(r"^\s*CREATE\s+(UNIQUE\s+)?INDEX\s+", sql_stripped, re.IGNORECASE):
        idx_match = re.match(
            r"^\s*CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\S+)\s+ON\s+(\S+)",
            sql_stripped,
            re.IGNORECASE,
        )
        rollback = None
        table = ""
        if idx_match:
            idx_name = idx_match.group(1).strip("`")
            table = idx_match.group(2).strip("`").rstrip("(")
            rollback = f"DROP INDEX `{idx_name}` ON `{table}`;"
        return SQLClassification(
            risk_level=RiskLevel.MEDIUM,
            risk_label=RISK_LABELS[RiskLevel.MEDIUM],
            risk_color=RISK_COLORS[RiskLevel.MEDIUM],
            description="创建索引（InnoDB 在线 DDL）",
            rollback_sql=rollback,
            impact=f"在表 {table} 上创建索引，期间写入性能可能下降",
            requires_confirmation=True,
        )

    if re.match(r"^\s*ALTER\s+TABLE\s+\S+\s+ADD\s+(UNIQUE\s+)?(INDEX|KEY)\s+", sql_stripped, re.IGNORECASE):
        alter_match = re.match(
            r"^\s*ALTER\s+TABLE\s+(\S+)\s+ADD\s+(?:UNIQUE\s+)?(?:INDEX|KEY)\s+(\S+)",
            sql_stripped,
            re.IGNORECASE,
        )
        rollback = None
        table = ""
        if alter_match:
            table = alter_match.group(1).strip("`")
            idx_name = alter_match.group(2).strip("`").rstrip("(")
            rollback = f"ALTER TABLE `{table}` DROP INDEX `{idx_name}`;"
        return SQLClassification(
            risk_level=RiskLevel.MEDIUM,
            risk_label=RISK_LABELS[RiskLevel.MEDIUM],
            risk_color=RISK_COLORS[RiskLevel.MEDIUM],
            description="添加索引（InnoDB 在线 DDL）",
            rollback_sql=rollback,
            impact=f"在表 {table} 上添加索引，期间写入性能可能下降",
            requires_confirmation=True,
        )

    # 4) 高风险: 其他 ALTER TABLE
    if re.match(r"^\s*ALTER\s+TABLE\s+", sql_stripped, re.IGNORECASE):
        table_match = re.match(r"^\s*ALTER\s+TABLE\s+(\S+)", sql_stripped, re.IGNORECASE)
        table = table_match.group(1).strip("`") if table_match else "unknown"
        return SQLClassification(
            risk_level=RiskLevel.HIGH,
            risk_label=RISK_LABELS[RiskLevel.HIGH],
            risk_color=RISK_COLORS[RiskLevel.HIGH],
            description="表结构变更，可能锁表",
            impact=f"修改表 {table} 结构，大表可能耗时较长并导致锁等待",
            requires_confirmation=True,
        )

    # 5) 只读查询 — 不需要确认
    if re.match(r"^\s*(SELECT|SHOW|EXPLAIN|DESCRIBE|DESC)\s+", sql_stripped, re.IGNORECASE):
        return SQLClassification(
            risk_level=RiskLevel.LOW,
            risk_label="只读",
            risk_color="#409EFF",
            description="只读查询",
            requires_confirmation=False,
        )

    # 6) 默认: 高风险
    return SQLClassification(
        risk_level=RiskLevel.HIGH,
        risk_label=RISK_LABELS[RiskLevel.HIGH],
        risk_color=RISK_COLORS[RiskLevel.HIGH],
        description="未识别的 SQL 类型，建议谨慎执行",
        requires_confirmation=True,
    )


def _execute_sql_on_connection_sync(
    connection_id: int,
    sql: str,
    db_session: Any,
) -> Dict[str, Any]:
    """
    在指定连接上执行 SQL（同步内部实现）

    Args:
        connection_id: 数据库连接 ID
        sql: 要执行的 SQL
        db_session: SQLAlchemy session（用于读取连接信息）

    Returns:
        执行结果字典
    """
    from app.crud.connection import get_connection
    from app.services.mysql_connector import MySQLConnector

    conn_config = get_connection(db_session, connection_id)
    if not conn_config:
        return {"success": False, "error": "连接不存在"}

    connector = MySQLConnector(
        host=conn_config.host,
        port=conn_config.port,
        user=conn_config.username,
        password=conn_config.password_encrypted or "",
        database=conn_config.database_name,
    )

    try:
        connector.connect()
        sql_upper = sql.strip().upper()

        # 判断是否有结果集
        is_query = sql_upper.startswith(("SELECT", "SHOW", "EXPLAIN", "DESCRIBE", "DESC"))

        if is_query:
            rows = connector.execute_query(sql)
            return {
                "success": True,
                "rows_affected": len(rows),
                "data": rows,
                "message": f"查询返回 {len(rows)} 行",
            }
        else:
            # DML / DDL — 需要 commit
            with connector.connection.cursor() as cursor:
                cursor.execute(sql)
            connector.connection.commit()
            # 获取 affected rows
            with connector.connection.cursor() as cursor:
                cursor.execute("SELECT ROW_COUNT() as cnt")
                row_count_result = cursor.fetchone()
                affected_rows = row_count_result.get("cnt", 0) if row_count_result else 0
            return {
                "success": True,
                "rows_affected": affected_rows,
                "message": f"执行成功，影响 {affected_rows} 行",
            }
    except Exception as e:
        logger.error(f"SQL 执行失败: {e}")
        return {"success": False, "error": str(e)}
    finally:
        connector.close()


async def execute_sql_on_connection(
    connection_id: int,
    sql: str,
    db_session: Any,
) -> Dict[str, Any]:
    """
    在指定连接上执行 SQL（异步包装，不阻塞事件循环）

    内部通过 run_in_executor 将同步 MySQLConnector 调用
    放到线程池中执行，避免阻塞 FastAPI 的异步事件循环。
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        partial(_execute_sql_on_connection_sync, connection_id, sql, db_session),
    )
