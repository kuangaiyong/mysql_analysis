"""
AI 上下文构建器

从 MySQL 实例收集数据，构建 AI 诊断所需的上下文
"""

import asyncio
import json
import logging
import re
from enum import Enum
from functools import partial
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from decimal import Decimal

from app.services.mysql_connector import MySQLConnector
from app.models.connection import Connection
from app.services.ai.utils import DecimalEncoder

logger = logging.getLogger(__name__)


class CollectionDepth(str, Enum):
    """采集深度"""
    QUICK = "quick"        # 仅基础指标+配置
    STANDARD = "standard"  # 基础+慢查询+等待事件
    DEEP = "deep"          # 全部数据含 InnoDB STATUS、会话、复制等


class AIContextBuilder:
    """
    AI 上下文构建器
    
    负责从 MySQL 实例收集数据，构建 AI 诊断所需的上下文
    """
    
    def __init__(self, db: Session, connection_id: int):
        """
        初始化上下文构建器
        
        Args:
            db: 数据库会话
            connection_id: MySQL 连接 ID
        """
        self.db = db
        self.connection_id = connection_id
        self._connector: Optional[MySQLConnector] = None
        self._connection_info: Optional[Dict[str, Any]] = None
    
    def _get_connection(self) -> Connection:
        """获取连接配置"""
        from sqlalchemy import select
        
        connection = self.db.execute(
            select(Connection).where(Connection.id == self.connection_id)
        ).scalar_one_or_none()
        
        if not connection:
            raise ValueError(f"连接 {self.connection_id} 不存在")
        
        return connection
    
    def _get_connector(self) -> MySQLConnector:
        """获取 MySQL 连接器"""
        if self._connector is None:
            conn = self._get_connection()
            self._connector = MySQLConnector(
                host=conn.host,
                port=conn.port,
                user=conn.username,
                password=conn.password_encrypted,
                database=conn.database_name,
            )
        return self._connector
    
    async def _async_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        在线程池中执行同步 MySQL 查询，避免阻塞事件循环

        这是对 connector.execute_query 的异步包装。
        """
        connector = self._get_connector()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(connector.execute_query, query, params)
        )
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """获取连接基本信息"""
        if self._connection_info is None:
            conn = self._get_connection()
            self._connection_info = {
                "id": conn.id,
                "name": conn.name,
                "host": conn.host,
                "port": conn.port,
                "database": conn.database_name,
            }
        return self._connection_info
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标（简化版）"""
        try:
            
            # 获取基础状态指标
            status_query = "SHOW GLOBAL STATUS WHERE Variable_name IN ('Queries', 'Questions', 'Connections', 'Bytes_received', 'Bytes_sent', 'Innodb_buffer_pool_read_requests', 'Innodb_buffer_pool_reads')"
            status_result = await self._async_query(status_query)
            status = {row['Variable_name']: int(row['Value']) for row in status_result}
            
            # 计算简化的性能指标
            return {
                "queries": status.get('Queries', 0),
                "questions": status.get('Questions', 0),
                "connections": status.get('Connections', 0),
                "bytes_received": status.get('Bytes_received', 0),
                "bytes_sent": status.get('Bytes_sent', 0),
                "buffer_pool_read_requests": status.get('Innodb_buffer_pool_read_requests', 0),
                "buffer_pool_reads": status.get('Innodb_buffer_pool_reads', 0),
                "buffer_pool_hit_rate": self._calculate_hit_rate(
                    status.get('Innodb_buffer_pool_read_requests', 0),
                    status.get('Innodb_buffer_pool_reads', 0)
                ),
            }
        except Exception as e:
            logger.error(f"获取性能指标失败: {e}")
            return {"error": str(e)}
    
    def _calculate_hit_rate(self, requests: int, reads: int) -> float:
        """计算 Buffer Pool 命中率"""
        if requests == 0:
            return 0.0
        return round((1 - reads / requests) * 100, 2)
    
    async def get_config_issues(self) -> List[Dict[str, Any]]:
        """获取配置信息（扩展版，覆盖 45+ 关键参数）"""
        try:

            # 分类采集关键配置参数
            variables_list = [
                # InnoDB
                'innodb_buffer_pool_size', 'innodb_buffer_pool_instances',
                'innodb_log_file_size', 'innodb_log_buffer_size',
                'innodb_flush_log_at_trx_commit', 'innodb_flush_method',
                'innodb_io_capacity', 'innodb_io_capacity_max',
                'innodb_read_io_threads', 'innodb_write_io_threads',
                'innodb_file_per_table', 'innodb_doublewrite',
                'innodb_adaptive_hash_index', 'innodb_change_buffering',
                'innodb_thread_concurrency', 'innodb_lock_wait_timeout',
                # 连接
                'max_connections', 'max_connect_errors',
                'wait_timeout', 'interactive_timeout', 'connect_timeout',
                'thread_cache_size',
                # 日志
                'slow_query_log', 'long_query_time',
                'log_queries_not_using_indexes', 'general_log',
                'binlog_format', 'sync_binlog', 'expire_logs_days',
                # 查询缓存
                'query_cache_type', 'query_cache_size',
                # 复制
                'server_id', 'read_only', 'super_read_only',
                'gtid_mode', 'enforce_gtid_consistency',
                # 性能
                'sort_buffer_size', 'join_buffer_size',
                'tmp_table_size', 'max_heap_table_size',
                'table_open_cache', 'table_definition_cache',
                'open_files_limit', 'max_allowed_packet',
                'key_buffer_size', 'bulk_insert_buffer_size',
            ]
            placeholders = ', '.join(f"'{v}'" for v in variables_list)
            variables_query = f"SHOW VARIABLES WHERE Variable_name IN ({placeholders})"
            variables = await self._async_query(variables_query)

            config = [
                {
                    "name": row['Variable_name'],
                    "value": row['Value'],
                    "source": "runtime"
                }
                for row in variables
            ]

            return config
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return []
    
    async def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取慢查询（从 performance_schema）"""
        try:
            
            # 检查 performance_schema 是否启用
            check_query = "SELECT COUNT(*) as count FROM performance_schema.setup_instruments WHERE ENABLED='YES'"
            result = await self._async_query(check_query)
            
            if not result or result[0]['count'] == 0:
                return []
            
            # 查询慢查询
            query = f"""
                SELECT 
                    DIGEST as sql_digest,
                    DIGEST_TEXT as sql_text,
                    COUNT_STAR as execution_count,
                    AVG_TIMER_WAIT/1000000000 as avg_query_time_ms,
                    SUM_TIMER_WAIT/1000000000 as total_query_time_ms,
                    SUM_ROWS_EXAMINED as total_rows_examined,
                    SUM_ROWS_SENT as total_rows_sent
                FROM performance_schema.events_statements_summary_by_digest
                WHERE DIGEST IS NOT NULL
                ORDER BY SUM_TIMER_WAIT DESC
                LIMIT {limit}
            """
            
            slow_queries = await self._async_query(query)
            
            # 简化返回数据
            return [
                {
                    "sql_digest": sq.get("sql_digest", "")[:200],
                    "sql_text": sq.get("sql_text", "")[:200],
                    "execution_count": sq.get("execution_count", 0),
                    "avg_query_time_ms": round(sq.get("avg_query_time_ms", 0), 2),
                    "total_query_time_ms": round(sq.get("total_query_time_ms", 0), 2),
                    "total_rows_examined": sq.get("total_rows_examined", 0),
                }
                for sq in slow_queries
            ]
        except Exception as e:
            logger.error(f"获取慢查询失败: {e}")
            return []
    
    async def get_wait_events_summary(self) -> Dict[str, Any]:
        """获取等待事件摘要（简化版）"""
        try:
            
            # 查询等待事件
            query = """
                SELECT 
                    EVENT_NAME,
                    COUNT_STAR as event_count,
                    SUM_TIMER_WAIT/1000000000 as total_wait_time_ms
                FROM performance_schema.events_waits_summary_global_by_event_name
                WHERE COUNT_STAR > 0
                ORDER BY SUM_TIMER_WAIT DESC
                LIMIT 10
            """
            
            events = await self._async_query(query)
            
            return {
                "bottleneck_type": "待分析",
                "total_events": len(events),
                "top_events": [
                    {
                        "event_name": e.get("EVENT_NAME"),
                        "count": e.get("event_count", 0),
                        "wait_time_ms": round(e.get("total_wait_time_ms", 0), 2)
                    }
                    for e in events[:5]
                ],
            }
        except Exception as e:
            logger.error(f"获取等待事件失败: {e}")
            return {"error": str(e)}
    
    async def get_explain(self, sql: str) -> Dict[str, Any]:
        """获取 SQL 执行计划"""
        try:
            
            # 执行 EXPLAIN
            explain_query = f"EXPLAIN FORMAT=JSON {sql}"
            result = await self._async_query(explain_query)
            
            if result and len(result) > 0:
                # 解析 JSON 格式的 EXPLAIN 结果
                import json
                explain_json = result[0].get('EXPLAIN', '{}')
                if isinstance(explain_json, str):
                    return json.loads(explain_json)
                return explain_json
            
            # 回退到传统格式
            explain_query = f"EXPLAIN {sql}"
            return {"traditional": await self._async_query(explain_query)}
        except Exception as e:
            logger.error(f"获取 EXPLAIN 失败: {e}")
            return {"error": str(e)}
    
    async def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """获取表结构"""
        try:

            # 只查询关键字段，减少 token 消耗
            query = """
                SELECT
                    COLUMN_NAME,
                    COLUMN_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY,
                    EXTRA
                FROM information_schema.COLUMNS
                WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE()
                ORDER BY ORDINAL_POSITION
            """
            columns = await self._async_query(query, (table_name,))

            return {
                "table_name": table_name,
                "columns": columns
            }
        except Exception as e:
            logger.error(f"获取表结构失败: {e}")
            return {"error": str(e)}
    
    async def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表索引"""
        try:
            query = f"SHOW INDEX FROM `{table_name}`"
            rows = await self._async_query(query)
            # 只保留关键字段，减少 token 消耗
            return [
                {
                    "key_name": r.get("Key_name"),
                    "column_name": r.get("Column_name"),
                    "non_unique": r.get("Non_unique"),
                    "seq_in_index": r.get("Seq_in_index"),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"获取索引失败: {e}")
            return []
    
    async def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """获取表统计信息"""
        try:
            query = f"""
                SELECT 
                    TABLE_ROWS,
                    DATA_LENGTH,
                    INDEX_LENGTH,
                    AUTO_INCREMENT,
                    TABLE_COMMENT
                FROM information_schema.TABLES
                WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE()
            """
            result = await self._async_query(query, (table_name,))
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"获取表统计失败: {e}")
            return {}
    
    async def get_innodb_status(self) -> Dict[str, Any]:
        """获取 InnoDB 引擎状态（解析 SHOW ENGINE INNODB STATUS）"""
        try:
            result = await self._async_query("SHOW ENGINE INNODB STATUS")
            if not result:
                return {"error": "无法获取 InnoDB 状态"}

            status_text = result[0].get('Status', '')
            parsed = {}

            # 提取关键段落
            sections = {
                'semaphores': r'----------\nSEMAPHORES\n----------\n(.*?)(?=\n---)',
                'transactions': r'------------\nTRANSACTIONS\n------------\n(.*?)(?=\n---)',
                'file_io': r'--------\nFILE I/O\n--------\n(.*?)(?=\n---)',
                'buffer_pool': r'----------------------\nBUFFER POOL AND MEMORY\n----------------------\n(.*?)(?=\n---)',
                'row_operations': r'--------------\nROW OPERATIONS\n--------------\n(.*?)(?=\n===|$)',
            }

            for key, pattern in sections.items():
                match = re.search(pattern, status_text, re.DOTALL)
                if match:
                    text = match.group(1).strip()
                    # 截断每段最大 500 字符，防止 token 爆炸
                    parsed[key] = text[:500] if len(text) > 500 else text

            # 提取最近死锁
            deadlock_match = re.search(
                r'LATEST DETECTED DEADLOCK\n-+\n(.*?)(?=\n-{10,})',
                status_text, re.DOTALL
            )
            if deadlock_match:
                parsed['latest_deadlock'] = deadlock_match.group(1).strip()[:500]

            # 提取关键数值
            trx_match = re.search(r'Trx id counter (\d+)', status_text)
            if trx_match:
                parsed['trx_id_counter'] = trx_match.group(1)

            history_match = re.search(r'History list length (\d+)', status_text)
            if history_match:
                parsed['history_list_length'] = int(history_match.group(1))

            pending_reads = re.search(r'(\d+) OS file reads', status_text)
            pending_writes = re.search(r'(\d+) OS file writes', status_text)
            if pending_reads:
                parsed['os_file_reads'] = int(pending_reads.group(1))
            if pending_writes:
                parsed['os_file_writes'] = int(pending_writes.group(1))

            return parsed
        except Exception as e:
            logger.error(f"获取 InnoDB 状态失败: {e}")
            return {"error": str(e)}

    async def get_active_sessions(self) -> Dict[str, Any]:
        """获取活跃会话信息"""
        try:

            # 活跃会话（排除 Sleep，运行超过 1 秒）
            query = """
                SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE,
                       LEFT(INFO, 200) as INFO
                FROM information_schema.PROCESSLIST
                WHERE COMMAND != 'Sleep' AND TIME > 1
                ORDER BY TIME DESC
                LIMIT 20
            """
            active = await self._async_query(query)

            # 总连接数统计
            count_query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN COMMAND = 'Sleep' THEN 1 ELSE 0 END) as sleeping,
                    SUM(CASE WHEN COMMAND != 'Sleep' THEN 1 ELSE 0 END) as active
                FROM information_schema.PROCESSLIST
            """
            counts = await self._async_query(count_query)
            count_info = counts[0] if counts else {}

            return {
                "total_connections": count_info.get("total", 0),
                "sleeping_connections": count_info.get("sleeping", 0),
                "active_connections": count_info.get("active", 0),
                "long_running_queries": [
                    {
                        "id": s.get("ID"),
                        "user": s.get("USER"),
                        "host": str(s.get("HOST", ""))[:50],
                        "db": s.get("DB"),
                        "command": s.get("COMMAND"),
                        "time_seconds": s.get("TIME"),
                        "state": s.get("STATE"),
                        "info": s.get("INFO"),
                    }
                    for s in active
                ]
            }
        except Exception as e:
            logger.error(f"获取活跃会话失败: {e}")
            return {"error": str(e)}

    async def get_database_sizes(self) -> List[Dict[str, Any]]:
        """获取各数据库/表大小统计"""
        try:

            query = """
                SELECT
                    TABLE_SCHEMA as db_name,
                    COUNT(*) as table_count,
                    ROUND(SUM(DATA_LENGTH) / 1024 / 1024, 2) as data_size_mb,
                    ROUND(SUM(INDEX_LENGTH) / 1024 / 1024, 2) as index_size_mb,
                    ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as total_size_mb,
                    ROUND(SUM(DATA_FREE) / 1024 / 1024, 2) as fragmented_mb
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
                GROUP BY TABLE_SCHEMA
                ORDER BY SUM(DATA_LENGTH + INDEX_LENGTH) DESC
                LIMIT 20
            """
            sizes = await self._async_query(query)

            # 碎片率高的表
            frag_query = """
                SELECT
                    TABLE_SCHEMA, TABLE_NAME,
                    ROUND(DATA_LENGTH / 1024 / 1024, 2) as data_mb,
                    ROUND(DATA_FREE / 1024 / 1024, 2) as free_mb,
                    ROUND(DATA_FREE / NULLIF(DATA_LENGTH, 0) * 100, 1) as frag_pct
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA NOT IN ('information_schema', 'performance_schema', 'mysql', 'sys')
                  AND DATA_LENGTH > 0 AND DATA_FREE / DATA_LENGTH > 0.2
                ORDER BY DATA_FREE DESC
                LIMIT 10
            """
            fragmented = await self._async_query(frag_query)

            return {
                "databases": sizes,
                "fragmented_tables": fragmented
            }
        except Exception as e:
            logger.error(f"获取数据库大小失败: {e}")
            return {"error": str(e)}

    async def get_replication_status(self) -> Dict[str, Any]:
        """获取复制状态"""
        try:

            # 尝试 MySQL 8.0.22+ 语法
            try:
                result = await self._async_query("SHOW REPLICA STATUS")
            except Exception:
                try:
                    result = await self._async_query("SHOW SLAVE STATUS")
                except Exception:
                    return {"is_replica": False}

            if not result:
                return {"is_replica": False}

            row = result[0]
            return {
                "is_replica": True,
                "master_host": row.get("Master_Host") or row.get("Source_Host"),
                "master_port": row.get("Master_Port") or row.get("Source_Port"),
                "io_running": row.get("Slave_IO_Running") or row.get("Replica_IO_Running"),
                "sql_running": row.get("Slave_SQL_Running") or row.get("Replica_SQL_Running"),
                "seconds_behind": row.get("Seconds_Behind_Master") or row.get("Seconds_Behind_Source"),
                "last_error": row.get("Last_Error") or row.get("Last_SQL_Error"),
                "last_io_error": row.get("Last_IO_Error"),
                "gtid_executed": str(row.get("Executed_Gtid_Set", ""))[:200],
            }
        except Exception as e:
            logger.error(f"获取复制状态失败: {e}")
            return {"is_replica": False, "error": str(e)}

    async def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用分布（performance_schema）"""
        try:

            query = """
                SELECT
                    EVENT_NAME,
                    CURRENT_NUMBER_OF_BYTES_USED as current_bytes,
                    HIGH_NUMBER_OF_BYTES_USED as high_bytes
                FROM performance_schema.memory_summary_global_by_event_name
                WHERE CURRENT_NUMBER_OF_BYTES_USED > 0
                ORDER BY CURRENT_NUMBER_OF_BYTES_USED DESC
                LIMIT 10
            """
            result = await self._async_query(query)

            total_bytes = sum(r.get("current_bytes", 0) for r in result)
            return {
                "total_allocated_mb": round(total_bytes / 1024 / 1024, 2),
                "top_consumers": [
                    {
                        "event_name": r.get("EVENT_NAME"),
                        "current_mb": round(r.get("current_bytes", 0) / 1024 / 1024, 2),
                        "high_mb": round(r.get("high_bytes", 0) / 1024 / 1024, 2),
                    }
                    for r in result
                ]
            }
        except Exception as e:
            logger.error(f"获取内存使用失败: {e}")
            return {"error": str(e)}

    def build_full_context(self) -> Dict[str, Any]:
        """
        构建完整诊断上下文（同步版本）
        
        Returns:
            完整上下文字典
        """
        import asyncio
        
        loop = asyncio.new_event_loop()
        try:
            return {
                "connection_info": loop.run_until_complete(self.get_connection_info()),
                "performance_metrics": loop.run_until_complete(self.get_performance_metrics()),
                "config_issues": loop.run_until_complete(self.get_config_issues()),
                "slow_queries": loop.run_until_complete(self.get_slow_queries()),
                "wait_events": loop.run_until_complete(self.get_wait_events_summary()),
            }
        finally:
            loop.close()
    
    async def build_full_context_async(
        self, depth: CollectionDepth = CollectionDepth.STANDARD
    ) -> Dict[str, Any]:
        """
        构建完整诊断上下文（异步版本）

        Args:
            depth: 采集深度（quick/standard/deep）

        Returns:
            完整上下文字典
        """
        # quick: 仅基础指标+配置
        context = {
            "connection_info": await self.get_connection_info(),
            "performance_metrics": await self.get_performance_metrics(),
            "config_issues": await self.get_config_issues(),
        }

        if depth in (CollectionDepth.STANDARD, CollectionDepth.DEEP):
            context["slow_queries"] = await self.get_slow_queries()
            context["wait_events"] = await self.get_wait_events_summary()

        if depth == CollectionDepth.DEEP:
            context["innodb_status"] = await self.get_innodb_status()
            context["active_sessions"] = await self.get_active_sessions()
            context["database_sizes"] = await self.get_database_sizes()
            context["replication_status"] = await self.get_replication_status()
            context["memory_usage"] = await self.get_memory_usage()

        return context
    
    def _extract_table_names(self, sql: str) -> List[str]:
        """
        从 SQL 中提取所有表名（支持 FROM、JOIN、UPDATE、INTO）

        支持格式: table_name, `table_name`, db.table_name, `db`.`table_name`
        """
        # 匹配 FROM/JOIN/UPDATE/INTO 后面的表名
        pattern = r'(?:FROM|JOIN|UPDATE|INTO)\s+`?([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)`?'
        matches = re.findall(pattern, sql, re.IGNORECASE)
        # 去重并保持顺序，取 . 后面的部分（如果有 db.table 格式）
        seen = set()
        tables = []
        for m in matches:
            name = m.split('.')[-1]
            if name not in seen:
                seen.add(name)
                tables.append(name)
        return tables

    async def build_sql_optimization_context(self, sql: str) -> Dict[str, Any]:
        """
        构建 SQL 优化上下文

        Args:
            sql: SQL 语句

        Returns:
            SQL 优化上下文
        """
        table_names = self._extract_table_names(sql)

        context = {
            "sql": sql,
            "explain_result": await self.get_explain(sql),
        }

        if table_names:
            # 收集所有相关表的结构、索引和统计信息
            all_structures = {}
            all_indexes = {}
            all_stats = {}
            for table_name in table_names:
                all_structures[table_name] = await self.get_table_structure(table_name)
                all_indexes[table_name] = await self.get_table_indexes(table_name)
                all_stats[table_name] = await self.get_table_stats(table_name)
            context["table_structure"] = all_structures
            context["indexes"] = all_indexes
            context["table_stats"] = all_stats
        else:
            context["table_structure"] = {}
            context["indexes"] = {}
            context["table_stats"] = {}

        return context

    async def build_index_advisor_context(self) -> Dict[str, Any]:
        """构建索引顾问上下文"""
        context = {
            "connection_info": await self.get_connection_info(),
        }

        # 获取所有用户表的索引信息
        try:
            tables_query = """
                SELECT TABLE_NAME, TABLE_ROWS,
                       ROUND(DATA_LENGTH / 1024 / 1024, 2) as data_mb,
                       ROUND(INDEX_LENGTH / 1024 / 1024, 2) as index_mb
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY DATA_LENGTH DESC
                LIMIT 30
            """
            tables = await self._async_query(tables_query)
            context["table_stats"] = tables

            # 获取所有索引
            all_indexes = {}
            for t in tables[:20]:
                table_name = t.get("TABLE_NAME", "")
                if table_name:
                    all_indexes[table_name] = await self.get_table_indexes(table_name)
            context["table_indexes"] = all_indexes

            # 索引使用统计（如果 performance_schema 可用）
            try:
                usage_query = """
                    SELECT OBJECT_SCHEMA, OBJECT_NAME, INDEX_NAME,
                           COUNT_FETCH as fetch_count,
                           COUNT_INSERT as insert_count,
                           COUNT_UPDATE as update_count,
                           COUNT_DELETE as delete_count
                    FROM performance_schema.table_io_waits_summary_by_index_usage
                    WHERE OBJECT_SCHEMA = DATABASE()
                      AND INDEX_NAME IS NOT NULL
                    ORDER BY COUNT_FETCH DESC
                    LIMIT 100
                """
                context["index_usage_stats"] = await self._async_query(usage_query)
            except Exception:
                context["index_usage_stats"] = []

        except Exception as e:
            logger.error(f"构建索引顾问上下文失败: {e}")

        # 慢查询（可能缺索引的）
        context["slow_queries"] = await self.get_slow_queries(limit=15)

        return context

    async def build_lock_analysis_context(self) -> Dict[str, Any]:
        """构建锁分析上下文"""
        context = {
            "connection_info": await self.get_connection_info(),
        }

        # 当前锁等待
        try:
            # MySQL 8.0+
            lock_waits_query = """
                SELECT
                    r.trx_id AS waiting_trx_id,
                    r.trx_mysql_thread_id AS waiting_thread,
                    r.trx_query AS waiting_query,
                    r.trx_wait_started AS wait_started,
                    b.trx_id AS blocking_trx_id,
                    b.trx_mysql_thread_id AS blocking_thread,
                    b.trx_query AS blocking_query,
                    b.trx_started AS blocking_started
                FROM information_schema.innodb_lock_waits w
                JOIN information_schema.innodb_trx r ON w.requesting_trx_id = r.trx_id
                JOIN information_schema.innodb_trx b ON w.blocking_trx_id = b.trx_id
            """
            try:
                context["lock_waits"] = await self._async_query(lock_waits_query)
            except Exception:
                # MySQL 8.0.1+ performance_schema
                try:
                    ps_query = """
                        SELECT
                            r.ENGINE_TRANSACTION_ID as waiting_trx,
                            r.THREAD_ID as waiting_thread,
                            b.ENGINE_TRANSACTION_ID as blocking_trx,
                            b.THREAD_ID as blocking_thread,
                            w.REQUESTING_ENGINE_LOCK_ID,
                            w.BLOCKING_ENGINE_LOCK_ID
                        FROM performance_schema.data_lock_waits w
                        JOIN performance_schema.data_locks r ON w.REQUESTING_ENGINE_LOCK_ID = r.ENGINE_LOCK_ID
                        JOIN performance_schema.data_locks b ON w.BLOCKING_ENGINE_LOCK_ID = b.ENGINE_LOCK_ID
                        LIMIT 20
                    """
                    context["lock_waits"] = await self._async_query(ps_query)
                except Exception:
                    context["lock_waits"] = []
        except Exception:
            context["lock_waits"] = []

        # InnoDB 锁信息
        try:
            innodb_locks_query = """
                SELECT
                    ENGINE_TRANSACTION_ID as trx_id,
                    LOCK_TYPE, LOCK_MODE, LOCK_STATUS,
                    OBJECT_SCHEMA, OBJECT_NAME,
                    INDEX_NAME
                FROM performance_schema.data_locks
                LIMIT 50
            """
            context["innodb_locks"] = await self._async_query(innodb_locks_query)
        except Exception:
            try:
                context["innodb_locks"] = await self._async_query("SELECT * FROM information_schema.innodb_locks LIMIT 50")
            except Exception:
                context["innodb_locks"] = []

        # InnoDB 状态
        context["innodb_status"] = await self.get_innodb_status()

        # 活跃会话
        context["active_sessions"] = await self.get_active_sessions()

        # 锁等待统计
        try:
            lock_stats_query = """
                SELECT
                    EVENT_NAME,
                    COUNT_STAR as count,
                    SUM_TIMER_WAIT/1000000000 as total_wait_ms,
                    AVG_TIMER_WAIT/1000000000 as avg_wait_ms
                FROM performance_schema.events_waits_summary_global_by_event_name
                WHERE EVENT_NAME LIKE '%lock%' AND COUNT_STAR > 0
                ORDER BY SUM_TIMER_WAIT DESC
                LIMIT 20
            """
            context["lock_wait_stats"] = await self._async_query(lock_stats_query)
        except Exception:
            context["lock_wait_stats"] = []

        return context

    async def build_slow_query_patrol_context(self) -> Dict[str, Any]:
        """构建慢查询巡检上下文"""
        context = {
            "connection_info": await self.get_connection_info(),
        }

        # Top 慢查询（按总耗时）
        context["slow_queries_by_time"] = await self.get_slow_queries(limit=20)

        # Top 慢查询（按执行次数）
        try:
            by_count_query = """
                SELECT
                    DIGEST_TEXT as sql_text,
                    COUNT_STAR as execution_count,
                    AVG_TIMER_WAIT/1000000000 as avg_query_time_ms,
                    SUM_TIMER_WAIT/1000000000 as total_query_time_ms,
                    SUM_ROWS_EXAMINED as total_rows_examined,
                    SUM_ROWS_SENT as total_rows_sent,
                    SUM_NO_INDEX_USED as no_index_used,
                    SUM_NO_GOOD_INDEX_USED as no_good_index_used
                FROM performance_schema.events_statements_summary_by_digest
                WHERE DIGEST IS NOT NULL
                ORDER BY COUNT_STAR DESC
                LIMIT 20
            """
            context["slow_queries_by_count"] = await self._async_query(by_count_query)
        except Exception:
            context["slow_queries_by_count"] = []

        # 全表扫描查询
        try:
            full_scan_query = """
                SELECT
                    DIGEST_TEXT as sql_text,
                    COUNT_STAR as execution_count,
                    SUM_NO_INDEX_USED as no_index_count,
                    AVG_TIMER_WAIT/1000000000 as avg_time_ms,
                    SUM_ROWS_EXAMINED as rows_examined,
                    SUM_ROWS_SENT as rows_sent
                FROM performance_schema.events_statements_summary_by_digest
                WHERE SUM_NO_INDEX_USED > 0 AND DIGEST IS NOT NULL
                ORDER BY SUM_NO_INDEX_USED DESC
                LIMIT 15
            """
            context["full_scan_queries"] = await self._async_query(full_scan_query)
        except Exception:
            context["full_scan_queries"] = []

        # 慢查询配置
        context["slow_query_config"] = await self.get_config_issues()

        # 性能指标
        context["performance_metrics"] = await self.get_performance_metrics()

        return context

    async def build_config_tuning_context(self) -> Dict[str, Any]:
        """构建配置调优上下文"""
        context = {
            "connection_info": await self.get_connection_info(),
        }

        # 所有配置参数
        context["config_variables"] = await self.get_config_issues()

        # 运行时状态
        try:
            status_query = """
                SHOW GLOBAL STATUS WHERE Variable_name IN (
                    'Queries', 'Questions', 'Connections', 'Threads_connected',
                    'Threads_running', 'Threads_created', 'Threads_cached',
                    'Bytes_received', 'Bytes_sent',
                    'Innodb_buffer_pool_read_requests', 'Innodb_buffer_pool_reads',
                    'Innodb_buffer_pool_pages_total', 'Innodb_buffer_pool_pages_free',
                    'Innodb_buffer_pool_pages_dirty',
                    'Innodb_log_waits', 'Innodb_log_writes',
                    'Innodb_rows_read', 'Innodb_rows_inserted', 'Innodb_rows_updated', 'Innodb_rows_deleted',
                    'Created_tmp_tables', 'Created_tmp_disk_tables',
                    'Sort_merge_passes', 'Sort_rows',
                    'Table_locks_waited', 'Table_locks_immediate',
                    'Open_tables', 'Opened_tables',
                    'Max_used_connections', 'Aborted_connects', 'Aborted_clients',
                    'Select_full_join', 'Select_scan',
                    'Com_select', 'Com_insert', 'Com_update', 'Com_delete',
                    'Uptime'
                )
            """
            status_result = await self._async_query(status_query)
            context["status_variables"] = {row['Variable_name']: row['Value'] for row in status_result}
        except Exception:
            context["status_variables"] = {}

        # 性能指标
        context["performance_metrics"] = await self.get_performance_metrics()

        # 系统信息
        try:
            version_result = await self._async_query("SELECT VERSION() as version")
            context["system_info"] = {
                "mysql_version": version_result[0]["version"] if version_result else "unknown",
            }
        except Exception:
            context["system_info"] = {}

        return context

    async def build_capacity_prediction_context(self) -> Dict[str, Any]:
        """构建容量预测上下文"""
        context = {
            "connection_info": await self.get_connection_info(),
        }

        # 数据库/表大小
        context["database_sizes"] = await self.get_database_sizes()

        # 内存使用
        context["memory_usage"] = await self.get_memory_usage()

        # 连接使用情况
        context["active_sessions"] = await self.get_active_sessions()

        # 性能指标
        context["performance_metrics"] = await self.get_performance_metrics()

        # 配置参数
        context["config_variables"] = await self.get_config_issues()

        return context
    
    def _dump(self, data: Any, max_len: int = 3000) -> str:
        """JSON 序列化并截断，防止 token 爆炸"""
        text = json.dumps(data, ensure_ascii=False, indent=2, cls=DecimalEncoder)
        if len(text) > max_len:
            return text[:max_len] + "\n... (已截断)"
        return text

    def to_prompt_context(self, context: Dict[str, Any]) -> str:
        """
        将上下文转换为 Prompt 格式的字符串

        Args:
            context: 上下文字典

        Returns:
            格式化的上下文字符串
        """
        sections = [
            f"## 当前 MySQL 实例状态\n",
            f"### 连接信息\n{self._dump(context.get('connection_info', {}))}",
            f"### 性能指标\n{self._dump(context.get('performance_metrics', {}))}",
            f"### 配置信息\n{self._dump(context.get('config_issues', []))}",
        ]

        if 'slow_queries' in context:
            sections.append(f"### Top 慢查询\n{self._dump(context.get('slow_queries', []))}")
        if 'wait_events' in context:
            sections.append(f"### 等待事件\n{self._dump(context.get('wait_events', {}))}")

        # 深度采集数据
        if 'innodb_status' in context:
            sections.append(f"### InnoDB 引擎状态\n{self._dump(context.get('innodb_status', {}))}")
        if 'active_sessions' in context:
            sections.append(f"### 活跃会话\n{self._dump(context.get('active_sessions', {}))}")
        if 'database_sizes' in context:
            sections.append(f"### 数据库/表大小\n{self._dump(context.get('database_sizes', {}))}")
        if 'replication_status' in context:
            sections.append(f"### 复制状态\n{self._dump(context.get('replication_status', {}))}")
        if 'memory_usage' in context:
            sections.append(f"### 内存使用分布\n{self._dump(context.get('memory_usage', {}))}")

        return "\n\n".join(sections)
    
    def close(self):
        """关闭连接"""
        if self._connector:
            try:
                self._connector.close()
            except:
                pass
            self._connector = None


# ==================== 规则引擎预分析 ====================

class RuleEnginePreAnalyzer:
    """
    规则引擎预分析器

    在将采集数据发送给 LLM 之前，使用确定性规则对数据进行预检测，
    标记异常指标为 [!ANOMALY]，帮助 LLM 聚焦关键问题，减少遗漏。
    """

    @staticmethod
    def analyze_diagnostics(context: Dict[str, Any]) -> str:
        """
        对诊断上下文执行规则引擎预分析

        Args:
            context: build_full_context_async() 返回的完整上下文

        Returns:
            预分析结果文本（含 [!ANOMALY] 标记），可直接嵌入 prompt
        """
        findings: List[str] = []
        metrics = context.get("performance_metrics", {})
        config_list = context.get("config_issues", [])
        slow_queries = context.get("slow_queries", [])
        wait_events = context.get("wait_events", {})
        innodb = context.get("innodb_status", {})
        sessions = context.get("active_sessions", {})
        db_sizes = context.get("database_sizes", {})
        replication = context.get("replication_status", {})
        memory = context.get("memory_usage", {})

        # 将 config 列表转为字典方便查找
        config = {}
        for item in config_list:
            name = item.get("name", "")
            value = item.get("value", "")
            config[name] = value

        # ---------- 性能指标规则 ----------

        # R1: Buffer Pool 命中率
        hit_rate = metrics.get("buffer_pool_hit_rate", None)
        if hit_rate is not None and hit_rate < 99.0:
            level = "critical" if hit_rate < 95.0 else "warning"
            findings.append(
                f"[!ANOMALY][{level}] Buffer Pool 命中率偏低: {hit_rate}%"
                f"（建议 >= 99%，当前差 {round(99 - hit_rate, 2)} 个百分点）"
            )

        # ---------- 配置规则 ----------

        # R2: innodb_buffer_pool_size 过小
        bp_size_str = config.get("innodb_buffer_pool_size", "0")
        try:
            bp_size = int(bp_size_str)
            bp_size_mb = bp_size / 1024 / 1024
            if bp_size_mb < 256:
                findings.append(
                    f"[!ANOMALY][critical] innodb_buffer_pool_size = {bp_size_mb:.0f}MB，"
                    "严重偏小（建议为物理内存的 60-80%）"
                )
            elif bp_size_mb < 1024:
                findings.append(
                    f"[!ANOMALY][warning] innodb_buffer_pool_size = {bp_size_mb:.0f}MB，"
                    "偏小（建议为物理内存的 60-80%）"
                )
        except (ValueError, TypeError):
            pass

        # R3: innodb_flush_log_at_trx_commit
        flush_log = config.get("innodb_flush_log_at_trx_commit", "1")
        if flush_log == "0":
            findings.append(
                "[!ANOMALY][critical] innodb_flush_log_at_trx_commit = 0，"
                "存在数据丢失风险（崩溃可能丢失最近 1 秒的事务）"
            )
        elif flush_log == "2":
            findings.append(
                "[!ANOMALY][warning] innodb_flush_log_at_trx_commit = 2，"
                "OS 崩溃时可能丢失数据（适合非关键业务）"
            )

        # R4: sync_binlog
        sync_binlog = config.get("sync_binlog", "1")
        if sync_binlog == "0":
            findings.append(
                "[!ANOMALY][warning] sync_binlog = 0，"
                "binlog 未同步刷盘，主从切换时可能丢失事务"
            )

        # R5: max_connections
        max_conn_str = config.get("max_connections", "151")
        try:
            max_conn = int(max_conn_str)
            if max_conn > 1000:
                findings.append(
                    f"[!ANOMALY][warning] max_connections = {max_conn}，"
                    "过高可能导致内存不足（每个连接消耗约 1-10MB）"
                )
            elif max_conn < 50:
                findings.append(
                    f"[!ANOMALY][warning] max_connections = {max_conn}，"
                    "偏低，高并发时可能拒绝连接"
                )
        except (ValueError, TypeError):
            pass

        # R6: slow_query_log 未开启
        slow_log = config.get("slow_query_log", "OFF")
        if slow_log.upper() in ("OFF", "0"):
            findings.append(
                "[!ANOMALY][warning] slow_query_log 未开启，"
                "无法捕获慢查询，建议开启并设置合理的 long_query_time"
            )

        # R7: long_query_time 过大
        long_query_str = config.get("long_query_time", "10")
        try:
            long_query = float(long_query_str)
            if long_query > 5:
                findings.append(
                    f"[!ANOMALY][info] long_query_time = {long_query}s，"
                    "偏大，建议设为 1-2s 以捕获更多慢查询"
                )
        except (ValueError, TypeError):
            pass

        # R8: query_cache_type（MySQL 8.0 已移除，但低版本可能存在）
        qc_type = config.get("query_cache_type", "")
        if qc_type.upper() in ("ON", "1", "DEMAND"):
            findings.append(
                "[!ANOMALY][info] query_cache 已启用，"
                "在写密集场景下反而降低性能（MySQL 8.0 已移除该功能）"
            )

        # R9: innodb_file_per_table
        file_per_table = config.get("innodb_file_per_table", "ON")
        if file_per_table.upper() in ("OFF", "0"):
            findings.append(
                "[!ANOMALY][warning] innodb_file_per_table = OFF，"
                "所有表数据存储在共享表空间，空间回收困难"
            )

        # R10: innodb_log_file_size 过小
        log_size_str = config.get("innodb_log_file_size", "0")
        try:
            log_size = int(log_size_str)
            log_size_mb = log_size / 1024 / 1024
            if 0 < log_size_mb < 256:
                findings.append(
                    f"[!ANOMALY][warning] innodb_log_file_size = {log_size_mb:.0f}MB，"
                    "偏小（建议 512MB-2GB），可能导致频繁 checkpoint"
                )
        except (ValueError, TypeError):
            pass

        # R11: thread_cache_size
        thread_cache_str = config.get("thread_cache_size", "0")
        try:
            thread_cache = int(thread_cache_str)
            if thread_cache < 8:
                findings.append(
                    f"[!ANOMALY][info] thread_cache_size = {thread_cache}，"
                    "偏小，短连接场景下线程创建开销大"
                )
        except (ValueError, TypeError):
            pass

        # R12: tmp_table_size / max_heap_table_size 不一致
        tmp_size_str = config.get("tmp_table_size", "0")
        heap_size_str = config.get("max_heap_table_size", "0")
        try:
            tmp_size = int(tmp_size_str)
            heap_size = int(heap_size_str)
            if tmp_size > 0 and heap_size > 0 and tmp_size != heap_size:
                findings.append(
                    f"[!ANOMALY][info] tmp_table_size ({tmp_size//1024//1024}MB) != "
                    f"max_heap_table_size ({heap_size//1024//1024}MB)，"
                    "实际临时表大小取两者较小值，建议设为一致"
                )
        except (ValueError, TypeError):
            pass

        # ---------- 慢查询规则 ----------

        # R13: 存在高频慢查询
        for sq in slow_queries[:5]:
            avg_ms = sq.get("avg_query_time_ms", 0)
            exec_count = sq.get("execution_count", 0)
            total_ms = sq.get("total_query_time_ms", 0)
            sql_text = sq.get("sql_text", "")[:100]

            if avg_ms > 5000 and exec_count > 100:
                findings.append(
                    f"[!ANOMALY][critical] 高频慢查询: 平均 {avg_ms:.0f}ms × {exec_count} 次 = "
                    f"累计 {total_ms:.0f}ms | SQL: {sql_text}"
                )
            elif avg_ms > 1000 and exec_count > 50:
                findings.append(
                    f"[!ANOMALY][warning] 慢查询: 平均 {avg_ms:.0f}ms × {exec_count} 次 | SQL: {sql_text}"
                )

        # R14: 扫描行数远大于返回行数（可能缺索引）
        for sq in slow_queries[:5]:
            examined = sq.get("total_rows_examined", 0)
            sent = sq.get("total_rows_sent", 0)
            if examined > 0 and sent > 0 and examined / max(sent, 1) > 100:
                sql_text = sq.get("sql_text", "")[:80]
                findings.append(
                    f"[!ANOMALY][warning] 扫描/返回比过高: 扫描 {examined} 行，"
                    f"仅返回 {sent} 行（比值 {examined // max(sent, 1)}:1），"
                    f"可能缺少索引 | SQL: {sql_text}"
                )

        # ---------- 等待事件规则 ----------

        # R15: I/O 等待占比高
        top_events = wait_events.get("top_events", [])
        for evt in top_events[:3]:
            name = evt.get("event_name", "")
            wait_ms = evt.get("wait_time_ms", 0)
            if "io" in name.lower() and wait_ms > 10000:
                findings.append(
                    f"[!ANOMALY][warning] I/O 等待事件显著: {name}，"
                    f"累计等待 {wait_ms:.0f}ms"
                )
            elif "lock" in name.lower() and wait_ms > 5000:
                findings.append(
                    f"[!ANOMALY][warning] 锁等待事件显著: {name}，"
                    f"累计等待 {wait_ms:.0f}ms"
                )

        # ---------- InnoDB 状态规则 ----------

        # R16: History list length 过大（MVCC 回收滞后）
        hll = innodb.get("history_list_length", 0)
        if hll > 10000:
            level = "critical" if hll > 100000 else "warning"
            findings.append(
                f"[!ANOMALY][{level}] InnoDB History list length = {hll}，"
                "MVCC 旧版本回收滞后，可能存在长事务未提交"
            )

        # R17: 死锁
        if innodb.get("latest_deadlock"):
            findings.append(
                "[!ANOMALY][warning] 检测到最近的死锁记录，请检查事务并发模式"
            )

        # ---------- 会话规则 ----------

        # R18: 活跃连接比例
        total_conn = sessions.get("total_connections", 0)
        active_conn = sessions.get("active_connections", 0)
        if total_conn > 0:
            try:
                max_conn = int(config.get("max_connections", "151"))
                usage_pct = total_conn / max_conn * 100
                if usage_pct > 80:
                    findings.append(
                        f"[!ANOMALY][critical] 连接使用率 {usage_pct:.0f}%"
                        f"（{total_conn}/{max_conn}），即将耗尽"
                    )
                elif usage_pct > 60:
                    findings.append(
                        f"[!ANOMALY][warning] 连接使用率 {usage_pct:.0f}%"
                        f"（{total_conn}/{max_conn}），偏高"
                    )
            except (ValueError, TypeError):
                pass

        # R19: 长时间运行的查询
        long_running = sessions.get("long_running_queries", [])
        for q in long_running[:3]:
            time_sec = q.get("time_seconds", 0)
            if time_sec > 300:
                findings.append(
                    f"[!ANOMALY][critical] 长时间运行查询: {time_sec}s，"
                    f"用户={q.get('user','?')} 状态={q.get('state','?')} "
                    f"SQL: {str(q.get('info',''))[:80]}"
                )
            elif time_sec > 60:
                findings.append(
                    f"[!ANOMALY][warning] 运行中查询: {time_sec}s，"
                    f"用户={q.get('user','?')} SQL: {str(q.get('info',''))[:80]}"
                )

        # ---------- 复制规则 ----------

        # R20: 复制延迟
        if replication.get("is_replica"):
            lag = replication.get("seconds_behind", 0)
            io_running = replication.get("io_running", "")
            sql_running = replication.get("sql_running", "")

            if str(io_running).upper() != "YES":
                findings.append(
                    f"[!ANOMALY][critical] 复制 IO 线程未运行: {io_running}"
                )
            if str(sql_running).upper() != "YES":
                findings.append(
                    f"[!ANOMALY][critical] 复制 SQL 线程未运行: {sql_running}"
                )
            if lag is not None:
                try:
                    lag_val = int(lag)
                    if lag_val > 60:
                        findings.append(
                            f"[!ANOMALY][critical] 复制延迟 {lag_val}s，严重落后"
                        )
                    elif lag_val > 10:
                        findings.append(
                            f"[!ANOMALY][warning] 复制延迟 {lag_val}s"
                        )
                except (ValueError, TypeError):
                    pass

            last_error = replication.get("last_error", "")
            if last_error:
                findings.append(
                    f"[!ANOMALY][critical] 复制错误: {last_error[:200]}"
                )

        # ---------- 碎片规则 ----------

        # R21: 表碎片率高
        fragmented_tables = []
        if isinstance(db_sizes, dict):
            fragmented_tables = db_sizes.get("fragmented_tables", [])
        for ft in fragmented_tables[:3]:
            frag_pct = ft.get("frag_pct", 0)
            table_name = f"{ft.get('TABLE_SCHEMA','')}.{ft.get('TABLE_NAME','')}"
            free_mb = ft.get("free_mb", 0)
            if frag_pct and float(frag_pct) > 30 and free_mb and float(free_mb) > 100:
                findings.append(
                    f"[!ANOMALY][warning] 表碎片率高: {table_name}，"
                    f"碎片 {frag_pct}%（{free_mb}MB 可回收），"
                    "建议 OPTIMIZE TABLE 或 ALTER TABLE ... ENGINE=InnoDB"
                )

        # ---------- 汇总 ----------

        if not findings:
            return ""

        # 按严重程度排序
        severity_order = {"critical": 0, "warning": 1, "info": 2}

        def sort_key(line: str) -> int:
            for level, order in severity_order.items():
                if f"[{level}]" in line:
                    return order
            return 3

        findings.sort(key=sort_key)

        header = f"共检测到 {len(findings)} 个预警项（规则引擎自动检测）：\n"
        return header + "\n".join(f"- {f}" for f in findings)

    @staticmethod
    def analyze_sql_optimization(
        sql: str,
        explain_result: Dict[str, Any],
        table_stats: Dict[str, Any],
    ) -> str:
        """
        对 SQL 优化场景执行规则引擎预分析

        Args:
            sql: 原始 SQL
            explain_result: EXPLAIN JSON 结果
            table_stats: 各表统计信息

        Returns:
            预分析结果文本
        """
        findings: List[str] = []

        # 分析 EXPLAIN
        if isinstance(explain_result, dict):
            # JSON 格式 EXPLAIN
            query_block = explain_result.get("query_block", {})
            table_info = query_block.get("table", {})

            # 传统格式也可能在 "traditional" 键下
            traditional = explain_result.get("traditional", [])

            if table_info:
                access_type = table_info.get("access_type", "")
                rows = table_info.get("rows_examined_per_scan", 0)

                if access_type == "ALL":
                    findings.append(
                        f"[!ANOMALY][critical] 全表扫描（type=ALL），"
                        f"预估扫描 {rows} 行"
                    )
                elif access_type == "index":
                    findings.append(
                        f"[!ANOMALY][warning] 全索引扫描（type=index），"
                        f"预估扫描 {rows} 行"
                    )

                if table_info.get("using_filesort"):
                    findings.append(
                        "[!ANOMALY][warning] 使用了 filesort 排序，考虑添加覆盖排序的索引"
                    )
                if table_info.get("using_temporary_table"):
                    findings.append(
                        "[!ANOMALY][warning] 使用了临时表，检查 GROUP BY / DISTINCT / UNION 是否可优化"
                    )

            # 传统格式分析
            for row in traditional:
                row_type = row.get("type", "")
                extra = row.get("Extra", "")
                rows_val = row.get("rows", 0)

                if row_type == "ALL":
                    findings.append(
                        f"[!ANOMALY][critical] 表 {row.get('table','?')} 全表扫描，"
                        f"预估 {rows_val} 行"
                    )
                if "filesort" in extra.lower():
                    findings.append(
                        f"[!ANOMALY][warning] 表 {row.get('table','?')} 使用 filesort"
                    )
                if "temporary" in extra.lower():
                    findings.append(
                        f"[!ANOMALY][warning] 表 {row.get('table','?')} 使用临时表"
                    )

        # 分析表数据量
        if isinstance(table_stats, dict):
            for table_name, stats in table_stats.items():
                if isinstance(stats, dict):
                    row_count = stats.get("TABLE_ROWS", 0)
                    try:
                        row_count = int(row_count) if row_count else 0
                    except (ValueError, TypeError):
                        row_count = 0

                    if row_count > 10_000_000:
                        findings.append(
                            f"[!ANOMALY][warning] 表 {table_name} 行数约 {row_count:,}，"
                            "大表操作需注意锁和 I/O 影响"
                        )
                    elif row_count > 1_000_000:
                        findings.append(
                            f"[!ANOMALY][info] 表 {table_name} 行数约 {row_count:,}，"
                            "CREATE INDEX 可能需要较长时间"
                        )

        # SQL 模式检测
        sql_upper = sql.upper().strip()
        if "SELECT *" in sql_upper:
            findings.append(
                "[!ANOMALY][info] 使用了 SELECT *，建议明确指定所需列以减少 I/O"
            )
        if sql_upper.count("JOIN") > 3:
            findings.append(
                f"[!ANOMALY][warning] SQL 包含 {sql_upper.count('JOIN')} 个 JOIN，"
                "多表关联可能导致性能问题"
            )
        if "NOT IN" in sql_upper or "NOT EXISTS" in sql_upper:
            findings.append(
                "[!ANOMALY][info] 包含 NOT IN/NOT EXISTS，考虑改写为 LEFT JOIN ... IS NULL"
            )
        if "LIKE '%%" in sql_upper or "LIKE '%" in sql.upper():
            # 检查前导通配符
            import re as _re
            if _re.search(r"LIKE\s+'%", sql, _re.IGNORECASE):
                findings.append(
                    "[!ANOMALY][warning] LIKE 以 % 开头，无法使用索引前缀匹配"
                )
        if "ORDER BY" in sql_upper and "LIMIT" not in sql_upper:
            findings.append(
                "[!ANOMALY][info] 有 ORDER BY 但无 LIMIT，大结果集排序开销大"
            )

        if not findings:
            return ""

        return "规则引擎 SQL 预检结果：\n" + "\n".join(f"- {f}" for f in findings)
