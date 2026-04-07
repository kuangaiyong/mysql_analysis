"""
AI 诊断服务

核心 AI 诊断功能实现
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from collections.abc import AsyncGenerator
from sqlalchemy.orm import Session

from app.services.ai.llm_adapter import LLMAdapter, get_llm_adapter, extract_json_from_markdown
from app.services.ai.prompts import (
    DIAGNOSIS_SYSTEM_PROMPT,
    SQL_OPTIMIZATION_SYSTEM_PROMPT,
    EXPLAIN_SYSTEM_PROMPT,
    build_diagnosis_prompt,
    build_sql_optimization_prompt,
    build_explain_prompt,
    QUICK_QUESTIONS,
)
from app.services.ai.context_builder import AIContextBuilder, CollectionDepth
from app.services.ai.cache import get_cache
from app.services.ai.utils import DecimalEncoder

logger = logging.getLogger(__name__)


class AIDiagnosticService:
    """
    AI 诊断服务
    
    提供智能诊断对话、SQL 优化、EXPLAIN 解读等功能
    """
    
    def __init__(self, llm_adapter: Optional[LLMAdapter] = None):
        """
        初始化 AI 诊断服务
        
        Args:
            llm_adapter: LLM 适配器实例（可选，默认使用配置的提供商）
        """
        self.llm = llm_adapter or get_llm_adapter()
    
    async def diagnose(
        self,
        db: Session,
        connection_id: int,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        智能诊断对话

        Args:
            db: 数据库会话
            connection_id: MySQL 连接 ID
            question: 用户问题
            history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            depth: 采集深度 (quick/standard/deep)

        Returns:
            诊断结果
        """
        context_builder = None
        try:
            logger.info(f"[AI诊断] 开始诊断 connection_id={connection_id} depth={depth} question={question[:50]}...")

            # 开始时回调
            if progress_callback:
                progress_callback("status", {"message": "开始诊断", "step": "init"})

            # 1. 构建上下文
            logger.info("步骤 1: 构建上下文...")
            collection_depth = CollectionDepth(depth) if depth in [d.value for d in CollectionDepth] else CollectionDepth.STANDARD
            context_builder = AIContextBuilder(db, connection_id)
            context = await context_builder.build_full_context_async(depth=collection_depth)
            logger.info(f"[AI诊断] 上下文构建完成 depth={depth} metrics_available={'error' not in context.get('performance_metrics', {})} slow_queries={len(context.get('slow_queries', []))} config_issues={len(context.get('config_issues', []))}")

            # 上下文构建完成后回调
            if progress_callback:
                progress_callback("context", {
                    "message": "数据收集完成",
                    "metrics_available": "error" not in context.get("performance_metrics", {}),
                    "slow_queries_count": len(context.get("slow_queries", []))
                })

            # 2. 构建提示（包含深度采集的额外数据）
            logger.info("步骤 2: 构建提示...")
            extra_context = {}
            for key in ("innodb_status", "active_sessions", "database_sizes", "replication_status", "memory_usage"):
                if key in context:
                    extra_context[key] = context[key]

            prompt = build_diagnosis_prompt(
                connection_id=connection_id,
                database_name=context.get("connection_info", {}).get("database", ""),
                performance_metrics=context.get("performance_metrics", {}),
                config_issues=context.get("config_issues", []),
                slow_queries=context.get("slow_queries", []),
                wait_events=context.get("wait_events", {}),
                question=question,
                extra_context=extra_context if extra_context else None
            )
            logger.info(f"[AI诊断] 提示构建完成 prompt_len={len(prompt)}")
            
            # 3. 构建消息列表
            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})
            
            # 4. 调用 LLM
            # LLM 调用开始时回调
            if progress_callback:
                progress_callback("analysis", {"message": "正在分析..."})
            
            response = await self.llm.chat(
                messages=messages,
                system_prompt=DIAGNOSIS_SYSTEM_PROMPT,
                temperature=0.3
            )
            
            # 5. 返回结果
            logger.info(f"[AI诊断] 诊断完成 connection_id={connection_id} answer_len={len(response)}")
            
            # 在返回前进行序列化，确保所有 Decimal 都被转换
            import json

            result = {
                "success": True,
                "answer": response,
                "context_summary": {
                    "connection_id": connection_id,
                    "database": context.get("connection_info", {}).get("database"),
                    "metrics_available": "error" not in context.get("performance_metrics", {}),
                    "config_issues_count": len(context.get("config_issues", [])),
                    "slow_queries_count": len(context.get("slow_queries", [])),
                    "bottleneck_type": context.get("wait_events", {}).get("bottleneck_type", "none"),
                },
                "provider": self.llm.get_provider_name(),
            }
            
            logger.info("序列化结果...")
            json_str = json.dumps(result, cls=DecimalEncoder)
            logger.info(f"✅ 序列化成功，长度: {len(json_str)}")
            
            # 完成时回调
            if progress_callback:
                progress_callback("result", {"message": "分析完成", "success": True})
            
            return json.loads(json_str)
            
        except Exception as e:
            import sys
            import traceback as tb
            from datetime import datetime
            
            # 详细的错误信息
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            error_type = type(e).__name__
            error_value = str(e)
            
            # 完整堆栈
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stack_trace = ''.join(tb.format_exception(exc_type, exc_value, exc_traceback))
            
            # 记录详细错误
            logger.error(f"\n{'='*80}")
            logger.error(f"[ERROR DETAILS] {error_time}")
            logger.error(f"Location: {__file__}")
            logger.error(f"Function: diagnose")
            logger.error(f"Exception Type: {error_type}")
            logger.error(f"Exception Value: {error_value}")
            logger.error(f"\n[STACK TRACE]")
            logger.error(stack_trace)
            logger.error(f"{'='*80}\n")
            
            # 同时打印到控制台
            print(f"\n{'='*80}", file=sys.stderr)
            print(f"[ERROR] AI 诊断失败", file=sys.stderr)
            print(f"Type: {error_type}", file=sys.stderr)
            print(f"Value: {error_value}", file=sys.stderr)
            print(f"\nStack Trace:\n{stack_trace}", file=sys.stderr)
            print(f"\n{'='*80}\n", file=sys.stderr)
            
            # 异常时回调
            if progress_callback:
                progress_callback("error", {
                    "message": f"诊断失败：{str(e)}",
                    "success": False,
                    "error": str(e)
                })
            
            return {
                "success": False,
                "error": str(e),
                "answer": f"诊断过程中发生错误：{str(e)}",
            }
        finally:
            if context_builder:
                context_builder.close()
    
    async def diagnose_stream(
        self,
        db: Session,
        connection_id: int,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        depth: str = "standard"
    ) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """
        智能诊断对话 - 流式版本

        Args:
            db: 数据库会话
            connection_id: MySQL 连接 ID
            question: 用户问题
            history: 对话历史
            depth: 采集深度 (quick/standard/deep)

        Yields:
            (event_type, data) 元组
        """
        context_builder = None
        try:
            logger.info(f"开始 AI 诊断（流式），连接 ID: {connection_id}, depth={depth}, 问题: {question}")

            # 发送开始状态
            yield ("status", {"message": "开始诊断", "step": "init"})

            # 1. 构建上下文
            logger.info("步骤 1: 构建上下文...")
            collection_depth = CollectionDepth(depth) if depth in [d.value for d in CollectionDepth] else CollectionDepth.STANDARD
            context_builder = AIContextBuilder(db, connection_id)
            context = await context_builder.build_full_context_async(depth=collection_depth)
            logger.info("✅ 上下文构建成功")

            # 发送上下文收集完成状态
            yield ("context", {
                "message": "数据收集完成",
                "metrics_available": "error" not in context.get("performance_metrics", {}),
                "slow_queries_count": len(context.get("slow_queries", []))
            })

            # 2. 构建提示
            logger.info("步骤 2: 构建提示...")
            extra_context = {}
            for key in ("innodb_status", "active_sessions", "database_sizes", "replication_status", "memory_usage"):
                if key in context:
                    extra_context[key] = context[key]

            prompt = build_diagnosis_prompt(
                connection_id=connection_id,
                database_name=context.get("connection_info", {}).get("database", ""),
                performance_metrics=context.get("performance_metrics", {}),
                config_issues=context.get("config_issues", []),
                slow_queries=context.get("slow_queries", []),
                wait_events=context.get("wait_events", {}),
                question=question,
                extra_context=extra_context if extra_context else None
            )
            logger.info(f"✅ 提示构建成功，长度: {len(prompt)}")
            
            # 3. 构建消息列表
            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})
            
            # 发送分析状态
            yield ("analysis", {"message": "正在分析..."})
            
            # 4. 调用 LLM
            response = await self.llm.chat(
                messages=messages,
                system_prompt=DIAGNOSIS_SYSTEM_PROMPT,
                temperature=0.3
            )
            
            # 5. 构建结果
            result = {
                "success": True,
                "answer": response,
                "context_summary": {
                    "connection_id": connection_id,
                    "database": context.get("connection_info", {}).get("database"),
                    "metrics_available": "error" not in context.get("performance_metrics", {}),
                    "config_issues_count": len(context.get("config_issues", [])),
                    "slow_queries_count": len(context.get("slow_queries", [])),
                    "bottleneck_type": context.get("wait_events", {}).get("bottleneck_type", "none"),
                },
                "provider": self.llm.get_provider_name(),
            }
            
            # 序列化结果
            json_str = json.dumps(result, cls=DecimalEncoder)
            result = json.loads(json_str)
            
            # 发送最终结果
            yield ("result", result)
            
        except Exception as e:
            import sys
            import traceback as tb
            from datetime import datetime
            
            # 详细的错误信息
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            error_type = type(e).__name__
            error_value = str(e)
            
            # 完整堆栈
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stack_trace = ''.join(tb.format_exception(exc_type, exc_value, exc_traceback))
            
            # 记录详细错误
            logger.error(f"\n{'='*80}")
            logger.error(f"[ERROR DETAILS] {error_time}")
            logger.error(f"Location: {__file__}")
            logger.error(f"Function: diagnose_stream")
            logger.error(f"Exception Type: {error_type}")
            logger.error(f"Exception Value: {error_value}")
            logger.error(f"\n[STACK TRACE]")
            logger.error(stack_trace)
            logger.error(f"{'='*80}\n")
            
            # 发送错误事件
            yield ("error", {
                "message": f"诊断失败：{str(e)}",
                "success": False,
                "error": str(e)
            })
            
        finally:
            if context_builder:
                context_builder.close()

    async def optimize_sql(
        self,
        db: Session,
        connection_id: int,
        sql: str
    ) -> Dict[str, Any]:
        """
        SQL 优化建议

        Args:
            db: 数据库会话
            connection_id: MySQL 连接 ID
            sql: 待优化的 SQL 语句

        Returns:
            优化建议
        """
        context_builder = None
        try:
            logger.info(f"[SQL优化] 开始优化 connection_id={connection_id} sql_len={len(sql)}")
            # 1. 构建上下文
            context_builder = AIContextBuilder(db, connection_id)
            context = await context_builder.build_sql_optimization_context(sql)
            explain_result = context.get("explain_result", {})
            logger.info(f"[SQL优化] EXPLAIN 完成 type={explain_result.get('type', 'N/A')} rows={explain_result.get('rows', 'N/A')}")
            # 2. 构建提示
            prompt = build_sql_optimization_prompt(
                sql=sql,
                explain_result=explain_result,
                table_structure=context.get("table_structure", {}),
                indexes=context.get("indexes", []),
                table_stats=context.get("table_stats", {})
            )

            # 3. 调用 LLM
            from app.config import settings
            response_text = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=SQL_OPTIMIZATION_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=settings.ai_max_tokens
            )

            # 4. 解析 JSON 响应
            response = extract_json_from_markdown(response_text)

            # 5. 对优化后的 SQL 执行 EXPLAIN（如果有）
            explain_after = None
            optimized_sql = response.get("optimized_sql", "").strip()
            if optimized_sql and optimized_sql.lower() != sql.strip().lower():
                try:
                    explain_after = await context_builder.get_explain(optimized_sql)
                    logger.info("[SQL优化] 优化后 EXPLAIN 执行成功")
                except Exception as e:
                    logger.warning(f"[SQL优化] 优化后 EXPLAIN 执行失败: {e}")

            # 6. 返回结果
            logger.info(f"[SQL优化] 优化完成 has_suggestions={bool(response.get('index_suggestions'))}")
            return {
                "success": True,
                "original_sql": sql,
                "optimization": response,
                "explain_before": context.get("explain_result", {}),
                "explain_after": explain_after,
                "provider": self.llm.get_provider_name(),
            }

        except Exception as e:
            logger.error(f"SQL 优化分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_sql": sql,
            }
        finally:
            if context_builder:
                context_builder.close()

    async def optimize_sql_stream(
        self,
        db: Session,
        connection_id: int,
        sql: str
    ) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """
        SQL 优化建议 - 流式版本

        Yields:
            (event_type, data) 元组
        """
        context_builder = None
        try:
            logger.info(f"[SQL优化-流式] 开始优化 connection_id={connection_id}")

            yield ("status", {"message": "开始分析 SQL", "step": "init"})

            # 1. 构建上下文 + EXPLAIN
            context_builder = AIContextBuilder(db, connection_id)
            yield ("status", {"message": "正在连接数据库并执行 EXPLAIN...", "step": "explain"})
            context = await context_builder.build_sql_optimization_context(sql)
            explain_result = context.get("explain_result", {})

            yield ("context", {
                "message": "EXPLAIN 执行完成，正在收集表结构信息...",
                "tables_found": list(context.get("table_structure", {}).keys()) if isinstance(context.get("table_structure"), dict) else [],
            })

            # 2. 构建提示
            prompt = build_sql_optimization_prompt(
                sql=sql,
                explain_result=explain_result,
                table_structure=context.get("table_structure", {}),
                indexes=context.get("indexes", {}),
                table_stats=context.get("table_stats", {})
            )

            yield ("analysis", {"message": "正在进行 AI 分析..."})

            # 3. 调用 LLM
            from app.config import settings
            response_text = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=SQL_OPTIMIZATION_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=settings.ai_max_tokens
            )

            # 4. 解析响应
            if not response_text or not response_text.strip():
                raise Exception("LLM 返回了空响应，请检查模型配置或稍后重试")
            response = extract_json_from_markdown(response_text)

            # 5. 对优化后的 SQL 执行 EXPLAIN 对比
            explain_after = None
            optimized_sql = response.get("optimized_sql", "").strip()
            if optimized_sql and optimized_sql.lower() != sql.strip().lower():
                try:
                    yield ("comparison", {"message": "正在对比优化前后执行计划..."})
                    explain_after = await context_builder.get_explain(optimized_sql)
                except Exception as e:
                    logger.warning(f"[SQL优化-流式] 优化后 EXPLAIN 失败: {e}")

            result = {
                "success": True,
                "original_sql": sql,
                "optimization": response,
                "explain_before": explain_result,
                "explain_after": explain_after,
                "provider": self.llm.get_provider_name(),
            }

            yield ("result", result)

        except Exception as e:
            logger.error(f"SQL 优化流式分析失败: {e}")
            yield ("error", {"message": f"SQL 优化失败：{str(e)}", "success": False})
        finally:
            if context_builder:
                context_builder.close()
    
    async def explain_interpret(
        self,
        sql: str,
        explain_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        EXPLAIN 结果解读
        
        Args:
            sql: SQL 语句
            explain_result: EXPLAIN 执行结果
        
        Returns:
            自然语言解释
        """
        try:
            logger.info(f"[EXPLAIN解读] 开始解读 sql_len={len(sql)}")
            # 构建提示
            prompt = build_explain_prompt(sql, explain_result)
            
            # 调用 LLM
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=EXPLAIN_SYSTEM_PROMPT,
                temperature=0.3
            )
            
            logger.info(f"[EXPLAIN解读] 解读完成 interpretation_len={len(response)}")
            return {
                "success": True,
                "sql": sql,
                "interpretation": response,
                "original_explain": explain_result,
                "provider": self.llm.get_provider_name(),
            }
            
        except Exception as e:
            logger.error(f"EXPLAIN 解读失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "sql": sql,
            }
    
    async def quick_diagnosis(
        self,
        db: Session,
        connection_id: int,
        question_type: str
    ) -> Dict[str, Any]:
        """
        快速诊断（预设问题）
        
        Args:
            db: 数据库会话
            connection_id: MySQL 连接 ID
            question_type: 问题类型 (slow_database/config_issues/slow_queries 等)
        
        Returns:
            诊断结果
        """
        if question_type not in QUICK_QUESTIONS:
            return {
                "success": False,
                "error": f"未知的问题类型: {question_type}",
                "available_types": list(QUICK_QUESTIONS.keys()),
            }
        
        question_config = QUICK_QUESTIONS[question_type]
        result = await self.diagnose(
            db=db,
            connection_id=connection_id,
            question=question_config["question"]
        )
        
        # 序列化并反序列化，确保所有 Decimal 都被转换为 float
        import json

        json_str = json.dumps(result, cls=DecimalEncoder)
        return json.loads(json_str)
    
    async def get_index_suggestions(
        self,
        db: Session,
        connection_id: int,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取索引建议
        
        Args:
            db: 数据库会话
            connection_id: MySQL 连接 ID
            table_name: 表名（可选，不指定则分析所有表）
        
        Returns:
            索引建议
        """
        if table_name:
            question = f"分析表 {table_name} 的索引使用情况，给出优化建议。"
        else:
            question = "分析当前数据库所有表的索引使用情况，给出优化建议。重点关注缺失索引、冗余索引和未使用的索引。"
        
        return await self.diagnose(
            db=db,
            connection_id=connection_id,
            question=question
        )
    
    async def analyze_bottleneck(
        self,
        db: Session,
        connection_id: int
    ) -> Dict[str, Any]:
        """
        分析性能瓶颈
        
        Args:
            db: 数据库会话
            connection_id: MySQL 连接 ID
        
        Returns:
            瓶颈分析结果
        """
        return await self.diagnose(
            db=db,
            connection_id=connection_id,
            question="分析当前数据库的性能瓶颈，包括 I/O、CPU、内存、锁等方面，并给出优化建议。"
        )


# 服务实例缓存
_service_instance: Optional[AIDiagnosticService] = None


def get_ai_service() -> AIDiagnosticService:
    """
    获取 AI 诊断服务实例
    
    注意：不再使用单例模式，每次都创建新实例
    这确保代码更新后能立即生效
    """
    return AIDiagnosticService()
