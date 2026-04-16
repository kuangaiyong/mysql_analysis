"""
AI 诊断服务

核心 AI 诊断功能实现
v2.0 — 规则引擎预分析 + 3 层结构化输出解析
"""

import json
import logging
import re
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
from app.services.ai.context_builder import AIContextBuilder, CollectionDepth, RuleEnginePreAnalyzer
from app.services.ai.cache import get_cache
from app.services.ai.utils import DecimalEncoder

logger = logging.getLogger(__name__)


# ==================== 结构化输出解析器 ====================

def parse_structured_response(raw_response: str) -> Dict[str, Any]:
    """
    解析 LLM 返回的 3 层结构化响应

    从 raw_response 中提取：
    - summary: 执行摘要
    - issues: 结构化问题 JSON 数组
    - detail: 深度分析 Markdown

    如果响应不含结构化标记，则 fallback 为纯文本模式（兼容旧版）
    """
    result = {
        "summary": "",
        "issues": [],
        "detail": "",
        "raw": raw_response,
    }

    # 提取执行摘要
    summary_match = re.search(
        r'<!-- SUMMARY_START -->(.*?)<!-- SUMMARY_END -->',
        raw_response, re.DOTALL
    )
    if summary_match:
        result["summary"] = summary_match.group(1).strip()

    # 提取结构化问题 JSON
    issues_match = re.search(
        r'<!-- ISSUES_JSON_START -->(.*?)<!-- ISSUES_JSON_END -->',
        raw_response, re.DOTALL
    )
    if issues_match:
        json_text = issues_match.group(1).strip()
        # 去除可能的 markdown 代码块包裹
        json_code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_text)
        if json_code_match:
            json_text = json_code_match.group(1).strip()
        try:
            issues = json.loads(json_text)
            if isinstance(issues, list):
                result["issues"] = issues
        except json.JSONDecodeError as e:
            logger.warning(f"结构化问题 JSON 解析失败: {e}")

    # 提取深度分析
    detail_match = re.search(
        r'<!-- DETAIL_START -->(.*?)<!-- DETAIL_END -->',
        raw_response, re.DOTALL
    )
    if detail_match:
        result["detail"] = detail_match.group(1).strip()

    # Fallback: 如果没有任何结构化标记，整体作为 detail
    if not result["summary"] and not result["issues"] and not result["detail"]:
        result["detail"] = raw_response
        # 尝试从纯文本中提取第一段作为 summary
        lines = raw_response.strip().split('\n')
        non_empty = [l.strip() for l in lines if l.strip() and not l.strip().startswith('#')]
        if non_empty:
            result["summary"] = non_empty[0][:200]

    return result


class AIDiagnosticService:
    """
    AI 诊断服务

    提供智能诊断对话、SQL 优化、EXPLAIN 解读等功能
    """

    def __init__(self, llm_adapter: Optional[LLMAdapter] = None):
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

        Returns:
            包含 structured 字段（summary/issues/detail）的诊断结果
        """
        context_builder = None
        try:
            logger.info(f"[AI诊断] 开始诊断 connection_id={connection_id} depth={depth} question={question[:50]}...")

            if progress_callback:
                progress_callback("status", {"message": "开始诊断", "step": "init"})

            # 1. 构建上下文
            logger.info("步骤 1: 构建上下文...")
            collection_depth = CollectionDepth(depth) if depth in [d.value for d in CollectionDepth] else CollectionDepth.STANDARD
            context_builder = AIContextBuilder(db, connection_id)
            context = await context_builder.build_full_context_async(depth=collection_depth)
            logger.info(f"[AI诊断] 上下文构建完成 depth={depth}")

            if progress_callback:
                progress_callback("context", {
                    "message": "数据收集完成",
                    "metrics_available": "error" not in context.get("performance_metrics", {}),
                    "slow_queries_count": len(context.get("slow_queries", []))
                })

            # 2. 规则引擎预分析
            logger.info("步骤 2: 规则引擎预分析...")
            pre_analysis = RuleEnginePreAnalyzer.analyze_diagnostics(context)
            if pre_analysis:
                logger.info(f"[AI诊断] 规则引擎发现预警项")
            else:
                logger.info("[AI诊断] 规则引擎未发现预警项")

            # 3. 构建提示
            logger.info("步骤 3: 构建提示...")
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
                extra_context=extra_context if extra_context else None,
                pre_analysis=pre_analysis if pre_analysis else None,
            )
            logger.info(f"[AI诊断] 提示构建完成 prompt_len={len(prompt)}")

            # 4. 构建消息列表
            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})

            # 5. 调用 LLM
            if progress_callback:
                progress_callback("analysis", {"message": "正在分析..."})

            response = await self.llm.chat_with_retry(
                messages=messages,
                system_prompt=DIAGNOSIS_SYSTEM_PROMPT,
                temperature=0.3
            )

            # 6. 解析结构化输出
            structured = parse_structured_response(response)

            # 7. 返回结果
            logger.info(f"[AI诊断] 诊断完成 connection_id={connection_id} answer_len={len(response)} issues={len(structured['issues'])}")

            result = {
                "success": True,
                "answer": response,
                "structured": structured,
                "pre_analysis": pre_analysis,
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

            json_str = json.dumps(result, cls=DecimalEncoder)

            if progress_callback:
                progress_callback("result", {"message": "分析完成", "success": True})

            return json.loads(json_str)

        except Exception as e:
            import sys
            import traceback as tb

            exc_type, exc_value, exc_traceback = sys.exc_info()
            stack_trace = ''.join(tb.format_exception(exc_type, exc_value, exc_traceback))
            logger.error(f"[AI诊断] 失败: {type(e).__name__}: {e}\n{stack_trace}")

            if progress_callback:
                progress_callback("error", {"message": f"诊断失败：{str(e)}", "success": False, "error": str(e)})

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
        """
        context_builder = None
        try:
            logger.info(f"开始 AI 诊断（流式），连接 ID: {connection_id}, depth={depth}")

            yield ("status", {"message": "开始诊断", "step": "init"})

            # 1. 构建上下文
            collection_depth = CollectionDepth(depth) if depth in [d.value for d in CollectionDepth] else CollectionDepth.STANDARD
            context_builder = AIContextBuilder(db, connection_id)
            context = await context_builder.build_full_context_async(depth=collection_depth)

            yield ("context", {
                "message": "数据收集完成",
                "metrics_available": "error" not in context.get("performance_metrics", {}),
                "slow_queries_count": len(context.get("slow_queries", []))
            })

            # 2. 规则引擎预分析
            pre_analysis = RuleEnginePreAnalyzer.analyze_diagnostics(context)

            # 3. 构建提示
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
                extra_context=extra_context if extra_context else None,
                pre_analysis=pre_analysis if pre_analysis else None,
            )

            messages = history.copy() if history else []
            messages.append({"role": "user", "content": prompt})

            yield ("analysis", {"message": "正在分析..."})

            # 4. 调用 LLM（真流式）
            response_chunks = []
            async for chunk in self.llm.chat_stream(
                messages=messages,
                system_prompt=DIAGNOSIS_SYSTEM_PROMPT,
                temperature=0.3,
            ):
                response_chunks.append(chunk)
                yield ("chunk", {"text": chunk})

            response = "".join(response_chunks)

            # 5. 解析结构化输出
            structured = parse_structured_response(response)

            result = {
                "success": True,
                "answer": response,
                "structured": structured,
                "pre_analysis": pre_analysis,
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

            json_str = json.dumps(result, cls=DecimalEncoder)
            result = json.loads(json_str)

            yield ("result", result)

        except Exception as e:
            import sys
            import traceback as tb
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stack_trace = ''.join(tb.format_exception(exc_type, exc_value, exc_traceback))
            logger.error(f"[AI诊断-流式] 失败: {type(e).__name__}: {e}\n{stack_trace}")
            yield ("error", {"message": f"诊断失败：{str(e)}", "success": False, "error": str(e)})
        finally:
            if context_builder:
                context_builder.close()

    async def optimize_sql(
        self,
        db: Session,
        connection_id: int,
        sql: str
    ) -> Dict[str, Any]:
        """SQL 优化建议（含规则引擎预分析）"""
        context_builder = None
        try:
            logger.info(f"[SQL优化] 开始优化 connection_id={connection_id} sql_len={len(sql)}")

            # 1. 构建上下文
            context_builder = AIContextBuilder(db, connection_id)
            context = await context_builder.build_sql_optimization_context(sql)
            explain_result = context.get("explain_result", {})

            # 2. 规则引擎预分析
            pre_analysis = RuleEnginePreAnalyzer.analyze_sql_optimization(
                sql=sql,
                explain_result=explain_result,
                table_stats=context.get("table_stats", {}),
            )

            # 3. 构建提示
            prompt = build_sql_optimization_prompt(
                sql=sql,
                explain_result=explain_result,
                table_structure=context.get("table_structure", {}),
                indexes=context.get("indexes", []),
                table_stats=context.get("table_stats", {}),
                pre_analysis=pre_analysis if pre_analysis else None,
            )

            # 4. 调用 LLM
            from app.config import settings
            response_text = await self.llm.chat_with_retry(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=SQL_OPTIMIZATION_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=settings.ai_max_tokens
            )

            # 5. 解析 JSON 响应
            response = extract_json_from_markdown(response_text)

            # 6. 对优化后的 SQL 执行 EXPLAIN
            explain_after = None
            optimized_sql = response.get("optimized_sql", "").strip()
            if optimized_sql and optimized_sql.lower() != sql.strip().lower():
                try:
                    explain_after = await context_builder.get_explain(optimized_sql)
                except Exception as e:
                    logger.warning(f"[SQL优化] 优化后 EXPLAIN 执行失败: {e}")

            return {
                "success": True,
                "original_sql": sql,
                "optimization": response,
                "explain_before": explain_result,
                "explain_after": explain_after,
                "pre_analysis": pre_analysis,
                "provider": self.llm.get_provider_name(),
            }

        except Exception as e:
            logger.error(f"SQL 优化分析失败: {e}")
            return {"success": False, "error": str(e), "original_sql": sql}
        finally:
            if context_builder:
                context_builder.close()

    async def optimize_sql_stream(
        self,
        db: Session,
        connection_id: int,
        sql: str
    ) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """SQL 优化建议 - 流式版本（含规则引擎预分析）"""
        context_builder = None
        try:
            yield ("status", {"message": "开始分析 SQL", "step": "init"})

            # 1. 构建上下文
            context_builder = AIContextBuilder(db, connection_id)
            yield ("status", {"message": "正在连接数据库并执行 EXPLAIN...", "step": "explain"})
            context = await context_builder.build_sql_optimization_context(sql)
            explain_result = context.get("explain_result", {})

            yield ("context", {
                "message": "EXPLAIN 执行完成，正在收集表结构信息...",
                "tables_found": list(context.get("table_structure", {}).keys()) if isinstance(context.get("table_structure"), dict) else [],
            })

            # 2. 规则引擎预分析
            pre_analysis = RuleEnginePreAnalyzer.analyze_sql_optimization(
                sql=sql,
                explain_result=explain_result,
                table_stats=context.get("table_stats", {}),
            )

            # 3. 构建提示
            prompt = build_sql_optimization_prompt(
                sql=sql,
                explain_result=explain_result,
                table_structure=context.get("table_structure", {}),
                indexes=context.get("indexes", {}),
                table_stats=context.get("table_stats", {}),
                pre_analysis=pre_analysis if pre_analysis else None,
            )

            yield ("analysis", {"message": "正在进行 AI 分析..."})

            # 4. 调用 LLM（流式收集）
            from app.config import settings
            response_parts = []
            async for chunk in self.llm.chat_stream(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=SQL_OPTIMIZATION_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=settings.ai_max_tokens,
            ):
                response_parts.append(chunk)
                yield ("chunk", {"text": chunk})

            response_text = "".join(response_parts)

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

            yield ("result", {
                "success": True,
                "original_sql": sql,
                "optimization": response,
                "explain_before": explain_result,
                "explain_after": explain_after,
                "pre_analysis": pre_analysis,
                "provider": self.llm.get_provider_name(),
            })

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
        """EXPLAIN 结果解读"""
        try:
            prompt = build_explain_prompt(sql, explain_result)
            response = await self.llm.chat_with_retry(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=EXPLAIN_SYSTEM_PROMPT,
                temperature=0.3
            )
            return {
                "success": True,
                "sql": sql,
                "interpretation": response,
                "original_explain": explain_result,
                "provider": self.llm.get_provider_name(),
            }
        except Exception as e:
            logger.error(f"EXPLAIN 解读失败: {e}")
            return {"success": False, "error": str(e), "sql": sql}

    async def quick_diagnosis(
        self,
        db: Session,
        connection_id: int,
        question_type: str
    ) -> Dict[str, Any]:
        """快速诊断（预设问题）"""
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

        json_str = json.dumps(result, cls=DecimalEncoder)
        return json.loads(json_str)

    async def get_index_suggestions(
        self,
        db: Session,
        connection_id: int,
        table_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取索引建议"""
        if table_name:
            question = f"分析表 {table_name} 的索引使用情况，给出优化建议。"
        else:
            question = "分析当前数据库所有表的索引使用情况，给出优化建议。重点关注缺失索引、冗余索引和未使用的索引。"
        return await self.diagnose(db=db, connection_id=connection_id, question=question)

    async def analyze_bottleneck(
        self,
        db: Session,
        connection_id: int
    ) -> Dict[str, Any]:
        """分析性能瓶颈"""
        return await self.diagnose(
            db=db,
            connection_id=connection_id,
            question="分析当前数据库的性能瓶颈，包括 I/O、CPU、内存、锁等方面，并给出优化建议。"
        )


# 服务实例
def get_ai_service() -> AIDiagnosticService:
    """获取 AI 诊断服务实例（每次创建新实例确保代码更新即时生效）"""
    return AIDiagnosticService()
