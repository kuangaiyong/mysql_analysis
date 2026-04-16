"""
健康巡检报告服务

提供 MySQL 数据库健康检查功能，从 8 个维度进行评估并生成综合报告。
v2.0 — 合并分析+评分为单次 LLM 调用（16→8 次），使用规则引擎预分析上下文
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, AsyncGenerator
from sqlalchemy.orm import Session

from app.services.ai.llm_adapter import get_llm_adapter
from app.services.ai.context_builder import AIContextBuilder, CollectionDepth, RuleEnginePreAnalyzer
from app.services.ai.prompts import build_health_dimension_prompt, HEALTH_DIMENSION_PROMPT
from app.crud import diagnosis as diagnosis_crud
from app.config import settings
from app.models.diagnosis import DiagnosisReport

logger = logging.getLogger(__name__)

# 8 个诊断维度及其权重
DIMENSIONS = [
    {"name": "整体性能", "weight": 0.20, "question": "请全面分析当前 MySQL 数据库的整体性能状况，包括 QPS、TPS、响应时间等关键指标。"},
    {"name": "配置", "weight": 0.15, "question": "请分析当前 MySQL 的配置是否合理，包括关键参数设置、内存分配、线程配置等。"},
    {"name": "慢查询", "weight": 0.15, "question": "请分析当前 MySQL 的慢查询情况，包括慢查询数量、频率、典型慢查询模式等。"},
    {"name": "索引", "weight": 0.15, "question": "请分析当前 MySQL 的索引使用情况，包括索引命中率、冗余索引、缺失索引等。"},
    {"name": "BufferPool", "weight": 0.10, "question": "请分析 InnoDB Buffer Pool 的使用情况，包括命中率、脏页比例、内存利用率等。"},
    {"name": "锁", "weight": 0.10, "question": "请分析当前 MySQL 的锁等待和死锁情况，包括锁争用、等待时间、死锁频率等。"},
    {"name": "连接", "weight": 0.10, "question": "请分析当前 MySQL 的连接使用情况，包括连接数、连接池利用率、异常连接等。"},
    {"name": "I/O", "weight": 0.05, "question": "请分析当前 MySQL 的磁盘 I/O 情况，包括读写吞吐量、IOPS、I/O 等待时间等。"},
]

# 问题提取提示词模板
ISSUES_EXTRACT_PROMPT = """你是 MySQL DBA 专家。请从以下健康巡检的各维度分析结果中，提取所有需要优化的问题。

要求：
1. 仔细阅读每个维度的分析文本，任何提到的异常、不合理配置、性能隐患都应提取为问题
2. 评分低于 80 的维度，至少应有 1 个问题
3. 严格按以下 JSON 数组格式返回，用 ```json 代码块包裹

每个问题的字段：
- severity: "critical"（严重）/ "warning"（警告）/ "info"（建议）
- category: 问题类型（性能/配置/索引/慢查询/BufferPool/锁/连接/I/O）
- description: 问题描述（一句话概括）
- detail: 问题详情（引用具体数据和现象）
- suggestion: 优化建议（给出具体操作命令或步骤）
- fix_command: 可直接执行的修复命令（SQL/配置），如无则为空字符串
- fix_risk: "low"/"medium"/"high"，表示执行风险等级

示例格式：
```json
[
  {{"severity": "warning", "category": "配置", "description": "innodb_buffer_pool_size 设置过小", "detail": "当前设置为 128MB，总内存 16GB，建议设为总内存的 60-80%", "suggestion": "SET GLOBAL innodb_buffer_pool_size = 10737418240;", "fix_command": "SET GLOBAL innodb_buffer_pool_size = 10737418240;", "fix_risk": "medium"}}
]
```

各维度分析结果：
{analysis_summary}
"""


class HealthReportService:
    """
    健康巡检报告服务

    v2.0 改进：
    - 每个维度只需 1 次 LLM 调用（分析+评分合并），总计 8+1=9 次（含问题提取）
    - 使用规则引擎预分析上下文，提高诊断质量
    - 问题提取增加 fix_command 和 fix_risk 字段
    """

    def __init__(self):
        self.llm = get_llm_adapter()

    async def generate_report_stream(
        self,
        db: Session,
        connection_id: int,
    ) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """
        流式生成健康巡检报告
        """
        logger.info(f"[健康巡检] 开始生成报告 connection_id={connection_id}")

        # 1. 预先采集完整上下文（只采集一次，所有维度共享）
        yield "progress", {
            "current": 0,
            "total": len(DIMENSIONS),
            "dimension": "数据采集",
            "status": "正在采集 MySQL 实例数据...",
        }

        context_builder = AIContextBuilder(db, connection_id)
        try:
            context = await context_builder.build_full_context_async(depth=CollectionDepth.DEEP)
        except Exception as e:
            logger.error(f"[健康巡检] 数据采集失败: {e}")
            yield "error", {"message": f"数据采集失败: {e}"}
            return
        finally:
            context_builder.close()

        # 2. 规则引擎预分析
        pre_analysis = RuleEnginePreAnalyzer.analyze_diagnostics(context)

        # 格式化上下文数据用于 prompt
        ctx_builder_for_format = AIContextBuilder(db, connection_id)
        context_text = ctx_builder_for_format.to_prompt_context(context)
        if pre_analysis:
            context_text = f"### 规则引擎预检结果\n{pre_analysis}\n\n{context_text}"

        # 3. 逐维度分析（每个维度 1 次 LLM 调用 = 分析+评分）
        total = len(DIMENSIONS)
        dimension_results: List[Dict[str, Any]] = []
        scores: Dict[str, float] = {}

        for idx, dim in enumerate(DIMENSIONS, start=1):
            dim_name = dim["name"]

            yield "progress", {
                "current": idx,
                "total": total,
                "dimension": dim_name,
                "status": "分析中...",
            }

            try:
                logger.info(f"[健康巡检] 分析维度 {idx}/{total}: {dim_name}")

                prompt = build_health_dimension_prompt(
                    dimension_name=dim_name,
                    question=dim["question"],
                    context_data=context_text,
                )

                response = await self.llm.chat_with_retry(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=settings.ai_max_tokens,
                )

                # 从响应中提取评分
                analysis_text, score = self._parse_dimension_response(dim_name, response)
                scores[dim_name] = score

                dim_result = {
                    "name": dim_name,
                    "score": score,
                    "weight": dim["weight"],
                    "analysis": analysis_text,
                }
                dimension_results.append(dim_result)

                yield "dimension", {
                    "name": dim_name,
                    "score": score,
                    "analysis": analysis_text,
                }

                logger.info(f"[健康巡检] 维度 {dim_name} 完成，评分: {score}")

            except Exception as e:
                logger.error(f"[健康巡检] 维度 {dim_name} 分析失败: {e}")
                dim_result = {
                    "name": dim_name,
                    "score": 0,
                    "weight": dim["weight"],
                    "analysis": f"分析失败: {str(e)}",
                }
                dimension_results.append(dim_result)
                scores[dim_name] = 0

                yield "dimension", {
                    "name": dim_name,
                    "score": 0,
                    "analysis": f"分析失败: {str(e)}",
                }

        # 4. 计算加权总分
        health_score = self._calculate_health_score(scores)
        logger.info(f"[健康巡检] 综合评分: {health_score}")

        # 5. 提取问题汇总
        yield "progress", {
            "current": total,
            "total": total,
            "dimension": "问题汇总",
            "status": "正在汇总问题...",
        }
        issues = await self._extract_issues(dimension_results)
        logger.info(f"[健康巡检] 提取到 {len(issues)} 个问题")

        # 6. 构建报告
        report_content = {
            "health_score": health_score,
            "dimensions": dimension_results,
            "issues": issues,
            "pre_analysis": pre_analysis,
            "generated_at": datetime.now().isoformat(),
            "connection_id": connection_id,
        }

        # 保存到数据库
        report_id = None
        try:
            report = diagnosis_crud.create_report(
                db=db,
                connection_id=connection_id,
                health_score=health_score,
                content_json=json.dumps(report_content, ensure_ascii=False),
                dimensions_json=json.dumps(dimension_results, ensure_ascii=False),
            )
            report_id = report.id
            logger.info(f"[健康巡检] 报告已保存 report_id={report_id}")
        except Exception as e:
            logger.error(f"[健康巡检] 报告保存失败: {e}")

        yield "result", {
            "report_id": report_id,
            "health_score": health_score,
            "dimensions": dimension_results,
            "issues": issues,
            "content": report_content,
        }

    def _parse_dimension_response(self, dimension_name: str, response: str) -> Tuple[str, int]:
        """
        从合并的 LLM 响应中提取分析文本和评分

        Returns:
            (analysis_text, score) 元组
        """
        score = 50  # 默认分数

        # 提取 DIMENSION_SCORE:{...} 格式
        score_match = re.search(
            r'DIMENSION_SCORE\s*:\s*(\{[^}]+\})',
            response, re.IGNORECASE
        )
        if score_match:
            try:
                score_data = json.loads(score_match.group(1))
                score = max(0, min(100, int(score_data.get("score", 50))))
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning(f"[健康巡检] 维度 {dimension_name} DIMENSION_SCORE JSON 解析失败: {e}")

            # 分析文本 = 移除 DIMENSION_SCORE 行后的内容
            analysis_text = response[:score_match.start()].strip()
        else:
            # Fallback: 尝试 SCORE:XX 格式
            legacy_match = re.search(r'SCORE\s*[:：]\s*(\d{1,3})', response, re.IGNORECASE)
            if legacy_match:
                score = max(0, min(100, int(legacy_match.group(1))))

            analysis_text = response.strip()
            logger.warning(f"[健康巡检] 维度 {dimension_name} 未找到 DIMENSION_SCORE 标记，使用 fallback")

        return analysis_text, score

    async def _extract_issues(self, dimension_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从各维度分析结果中提取问题汇总列表"""
        summary_parts = []
        for dim in dimension_results:
            name = dim.get("name", "")
            score = dim.get("score", 0)
            analysis = dim.get("analysis", "")
            truncated = analysis[:1500] if len(analysis) > 1500 else analysis
            summary_parts.append(f"### {name}（评分: {score}/100）\n{truncated}")

        analysis_summary = "\n\n".join(summary_parts)
        prompt = ISSUES_EXTRACT_PROMPT.format(analysis_summary=analysis_summary)

        try:
            response = await self.llm.chat_with_retry(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=settings.ai_max_tokens,
            )

            # 提取 JSON 数组
            text = response.strip()
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if json_match:
                text = json_match.group(1).strip()
            else:
                bracket_start = text.find('[')
                if bracket_start >= 0:
                    bracket_end = text.rfind(']')
                    if bracket_end > bracket_start:
                        text = text[bracket_start:bracket_end + 1]

            issues = json.loads(text)
            if not isinstance(issues, list):
                return []

            # 验证和排序
            valid_issues = []
            for issue in issues:
                if not isinstance(issue, dict) or not issue.get("description"):
                    continue
                severity = issue.get("severity", "info")
                if severity not in ("critical", "warning", "info"):
                    issue["severity"] = "info"
                # 确保新字段存在
                issue.setdefault("fix_command", "")
                issue.setdefault("fix_risk", "medium")
                valid_issues.append(issue)

            severity_order = {"critical": 0, "warning": 1, "info": 2}
            valid_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 3))

            logger.info(f"[健康巡检] 成功提取 {len(valid_issues)} 个有效问题")
            return valid_issues

        except json.JSONDecodeError as e:
            logger.error(f"[健康巡检] 问题列表 JSON 解析失败: {e}")
            return []
        except Exception as e:
            logger.error(f"[健康巡检] 提取问题列表失败: {type(e).__name__}: {e}")
            return []

    def _calculate_health_score(self, scores: Dict[str, float]) -> int:
        """根据权重加权求和计算综合健康评分"""
        total_score = 0.0
        total_weight = 0.0

        for dim in DIMENSIONS:
            dim_name = dim["name"]
            weight = dim["weight"]
            score = scores.get(dim_name, 0)
            total_score += score * weight
            total_weight += weight

        if total_weight > 0:
            health_score = total_score / total_weight
        else:
            health_score = 0

        return round(health_score)

    @staticmethod
    def export_to_markdown(report: DiagnosisReport) -> str:
        """将报告对象转换为 Markdown 文本"""
        content = json.loads(report.content_json) if report.content_json else {}
        dimensions = json.loads(report.dimensions_json) if report.dimensions_json else []
        issues = content.get("issues", [])
        generated_at = content.get("generated_at", report.created_at.isoformat() if report.created_at else "")
        health_score = report.health_score

        if health_score >= 90:
            level = "优秀"
        elif health_score >= 75:
            level = "良好"
        elif health_score >= 60:
            level = "一般"
        else:
            level = "较差"

        lines = [
            "# MySQL 健康巡检报告",
            "",
            f"**生成时间**: {generated_at}",
            "",
            f"## 综合评分: {health_score} 分（{level}）",
            "",
            "---",
            "",
        ]

        # 问题汇总
        if issues:
            severity_map = {"critical": "严重", "warning": "警告", "info": "建议"}
            lines.append("## 问题汇总")
            lines.append("")
            lines.append("| 序号 | 严重等级 | 问题类型 | 问题描述 | 优化建议 | 修复命令 | 风险 |")
            lines.append("|------|----------|----------|----------|----------|----------|------|")
            for i, issue in enumerate(issues, 1):
                sev = severity_map.get(issue.get("severity", "info"), "建议")
                cat = issue.get("category", "-")
                desc = issue.get("description", "-")
                suggestion = issue.get("suggestion", "-")
                fix_cmd = issue.get("fix_command", "-") or "-"
                fix_risk = issue.get("fix_risk", "-") or "-"
                lines.append(f"| {i} | {sev} | {cat} | {desc} | {suggestion} | `{fix_cmd}` | {fix_risk} |")
            lines.append("")
            lines.append("---")
            lines.append("")

        # 各维度评估
        lines.append("## 各维度评估")
        lines.append("")

        for dim in dimensions:
            name = dim.get("name", "未知")
            score = dim.get("score", 0)
            weight = dim.get("weight", 0)
            analysis = dim.get("analysis", "无分析结果")

            lines.append(f"### {name}（权重 {weight:.0%}）")
            lines.append("")
            lines.append(f"**评分**: {score} 分")
            lines.append("")
            lines.append("**分析**:")
            lines.append("")
            lines.append(analysis)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)
