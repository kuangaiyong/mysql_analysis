"""
AI 上下文构建器

从 MySQL 实例收集数据，构建 AI 诊断所需的上下文
"""

import json
import logging
import re
from enum import Enum
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
            connector = self._get_connector()
            
            # 获取基础状态指标
            status_query = "SHOW GLOBAL STATUS WHERE Variable_name IN ('Queries', 'Questions', 'Connections', 'Bytes_received', 'Bytes_sent', 'Innodb_buffer_pool_read_requests', 'Innodb_buffer_pool_reads')"
            status_result = connector.execute_query(status_query)
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
            connector = self._get_connector()

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
            variables = connector.execute_query(variables_query)

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
            connector = self._get_connector()
            
            # 检查 performance_schema 是否启用
            check_query = "SELECT COUNT(*) as count FROM performance_schema.setup_instruments WHERE ENABLED='YES'"
            result = connector.execute_query(check_query)
            
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
            
            slow_queries = connector.execute_query(query)
            
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
            connector = self._get_connector()
            
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
            
            events = connector.execute_query(query)
            
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
            connector = self._get_connector()
            
            # 执行 EXPLAIN
            explain_query = f"EXPLAIN FORMAT=JSON {sql}"
            result = connector.execute_query(explain_query)
            
            if result and len(result) > 0:
                # 解析 JSON 格式的 EXPLAIN 结果
                import json
                explain_json = result[0].get('EXPLAIN', '{}')
                if isinstance(explain_json, str):
                    return json.loads(explain_json)
                return explain_json
            
            # 回退到传统格式
            explain_query = f"EXPLAIN {sql}"
            return {"traditional": connector.execute_query(explain_query)}
        except Exception as e:
            logger.error(f"获取 EXPLAIN 失败: {e}")
            return {"error": str(e)}
    
    async def get_table_structure(self, table_name: str) -> Dict[str, Any]:
        """获取表结构"""
        try:
            connector = self._get_connector()

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
            columns = connector.execute_query(query, (table_name,))

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
            connector = self._get_connector()
            query = f"SHOW INDEX FROM `{table_name}`"
            rows = connector.execute_query(query)
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
            connector = self._get_connector()
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
            result = connector.execute_query(query, (table_name,))
            return result[0] if result else {}
        except Exception as e:
            logger.error(f"获取表统计失败: {e}")
            return {}
    
    async def get_innodb_status(self) -> Dict[str, Any]:
        """获取 InnoDB 引擎状态（解析 SHOW ENGINE INNODB STATUS）"""
        try:
            connector = self._get_connector()
            result = connector.execute_query("SHOW ENGINE INNODB STATUS")
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
            connector = self._get_connector()

            # 活跃会话（排除 Sleep，运行超过 1 秒）
            query = """
                SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE,
                       LEFT(INFO, 200) as INFO
                FROM information_schema.PROCESSLIST
                WHERE COMMAND != 'Sleep' AND TIME > 1
                ORDER BY TIME DESC
                LIMIT 20
            """
            active = connector.execute_query(query)

            # 总连接数统计
            count_query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN COMMAND = 'Sleep' THEN 1 ELSE 0 END) as sleeping,
                    SUM(CASE WHEN COMMAND != 'Sleep' THEN 1 ELSE 0 END) as active
                FROM information_schema.PROCESSLIST
            """
            counts = connector.execute_query(count_query)
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
            connector = self._get_connector()

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
            sizes = connector.execute_query(query)

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
            fragmented = connector.execute_query(frag_query)

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
            connector = self._get_connector()

            # 尝试 MySQL 8.0.22+ 语法
            try:
                result = connector.execute_query("SHOW REPLICA STATUS")
            except Exception:
                try:
                    result = connector.execute_query("SHOW SLAVE STATUS")
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
            connector = self._get_connector()

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
            result = connector.execute_query(query)

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
