"""
健康巡检报告服务

提供 MySQL 数据库健康检查功能，从 8 个维度进行评估并生成综合报告。
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple, AsyncGenerator
from sqlalchemy.orm import Session

from app.services.ai.ai_diagnostic_service import AIDiagnosticService
from app.services.ai.llm_adapter import get_llm_adapter
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

# 评分提示词模板 — 含具体扣分标准，防止模型盲目给高分
SCORE_PROMPT_TEMPLATE = (
    '你是 MySQL DBA 专家评审。请根据以下诊断分析结果，对"{dimension_name}"维度严格评分（0-100）。\n'
    '\n'
    '评分标准（严格执行）：\n'
    '- 90-100：所有指标完全正常，无任何隐患\n'
    '- 70-89：整体良好，存在少量可优化项\n'
    '- 50-69：存在明显问题，需要关注和优化\n'
    '- 30-49：存在较严重问题，亟需处理\n'
    '- 0-29：存在严重故障或性能瓶颈\n'
    '\n'
    '扣分规则：\n'
    '- 发现每个"建议"级别的问题扣 3-5 分\n'
    '- 发现每个"警告"级别的问题扣 8-15 分\n'
    '- 发现每个"严重"级别的问题扣 20-30 分\n'
    '- 如分析中提到配置不合理、性能指标异常、资源利用率过高/过低等，必须扣分\n'
    '- 不要因为"系统还能正常运行"就给高分，要关注潜在风险\n'
    '\n'
    '请只返回一个整数评分，格式为：SCORE:数字\n'
    '例如：SCORE:72\n'
    '\n'
    '分析内容：\n'
    '{analysis_text}'
)

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

示例格式：
```json
[
  {{"severity": "warning", "category": "配置", "description": "innodb_buffer_pool_size 设置过小", "detail": "当前设置为 128MB，总内存 16GB，建议设为总内存的 60-80%", "suggestion": "SET GLOBAL innodb_buffer_pool_size = 10737418240;"}}
]
```

各维度分析结果：
{analysis_summary}
"""


class HealthReportService:
    """
    健康巡检报告服务

    从 8 个维度对 MySQL 数据库进行全面健康检查，
    生成综合评分和分析报告。
    """

    def __init__(self, ai_service: AIDiagnosticService):
        """初始化健康巡检服务"""
        self.diagnostic_service = ai_service
        self.llm = get_llm_adapter()

    async def generate_report_stream(
        self,
        db: Session,
        connection_id: int,
    ) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """
        流式生成健康巡检报告

        Yields:
            (event_type, data) 元组
        """
        logger.info(f"[健康巡检] 开始生成报告 connection_id={connection_id}")
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
                logger.info(f"[健康巡检] 正在分析维度 {idx}/{total}: {dim_name}")
                result = await self.diagnostic_service.diagnose(
                    db=db,
                    connection_id=connection_id,
                    question=dim["question"],
                    depth="standard",
                )

                analysis_text = result.get("answer", "")
                if not analysis_text:
                    analysis_text = result.get("analysis", result.get("content", ""))
                if isinstance(analysis_text, dict):
                    analysis_text = json.dumps(analysis_text, ensure_ascii=False)

                score = await self._score_dimension(dim_name, analysis_text)
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

        # 计算加权总分
        health_score = self._calculate_health_score(scores)
        logger.info(f"[健康巡检] 报告生成完成，综合评分: {health_score}")

        # 提取问题汇总列表
        yield "progress", {
            "current": total,
            "total": total,
            "dimension": "问题汇总",
            "status": "正在汇总问题...",
        }
        issues = await self._extract_issues(dimension_results)
        logger.info(f"[健康巡检] 提取到 {len(issues)} 个问题")

        # 构建报告内容
        report_content = {
            "health_score": health_score,
            "dimensions": dimension_results,
            "issues": issues,
            "generated_at": datetime.now().isoformat(),
            "connection_id": connection_id,
        }

        # 保存报告到数据库
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
            logger.info(f"[健康巡检] 报告已保存，report_id={report_id}")
        except Exception as e:
            logger.error(f"[健康巡检] 报告保存失败: {e}")

        # 发送最终结果事件
        yield "result", {
            "report_id": report_id,
            "health_score": health_score,
            "dimensions": dimension_results,
            "issues": issues,
            "content": report_content,
        }

    async def _extract_issues(self, dimension_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从各维度分析结果中提取问题汇总列表

        Returns:
            问题列表，每项包含 severity/category/description/detail/suggestion
        """
        # 构建各维度分析摘要
        summary_parts = []
        for dim in dimension_results:
            name = dim.get("name", "")
            score = dim.get("score", 0)
            analysis = dim.get("analysis", "")
            # 截断每个维度的分析文本，防止 token 过长
            truncated = analysis[:1500] if len(analysis) > 1500 else analysis
            summary_parts.append(f"### {name}（评分: {score}/100）\n{truncated}")

        analysis_summary = "\n\n".join(summary_parts)
        prompt = ISSUES_EXTRACT_PROMPT.format(analysis_summary=analysis_summary)

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=settings.ai_max_tokens,
            )

            logger.info(f"[健康巡检] 问题提取 AI 响应长度: {len(response)}")
            logger.debug(f"[健康巡检] 问题提取原始响应: {response[:500]}")

            # 提取 JSON 数组
            text = response.strip()
            # 尝试从 markdown 代码块中提取
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if json_match:
                text = json_match.group(1).strip()
                logger.info("[健康巡检] 从 markdown 代码块中提取到 JSON")
            else:
                # 尝试找到 [ 开头的 JSON
                bracket_start = text.find('[')
                if bracket_start >= 0:
                    bracket_end = text.rfind(']')
                    if bracket_end > bracket_start:
                        text = text[bracket_start:bracket_end + 1]
                        logger.info("[健康巡检] 从文本中定位到 JSON 数组")
                    else:
                        logger.warning(f"[健康巡检] 找到 '[' 但未找到匹配的 ']'，原始文本前200字: {text[:200]}")
                else:
                    logger.warning(f"[健康巡检] 响应中未找到 JSON 数组，原始文本前200字: {text[:200]}")

            issues = json.loads(text)
            if not isinstance(issues, list):
                logger.warning(f"[健康巡检] JSON 解析结果不是数组，类型: {type(issues)}")
                return []

            # 验证每个 issue 的字段完整性
            valid_issues = []
            for issue in issues:
                if not isinstance(issue, dict):
                    continue
                # 确保必填字段存在
                if not issue.get("description"):
                    continue
                # 规范化 severity
                severity = issue.get("severity", "info")
                if severity not in ("critical", "warning", "info"):
                    issue["severity"] = "info"
                valid_issues.append(issue)

            # 按严重等级排序：critical > warning > info
            severity_order = {"critical": 0, "warning": 1, "info": 2}
            valid_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 3))

            logger.info(f"[健康巡检] 成功提取 {len(valid_issues)} 个有效问题")
            return valid_issues

        except json.JSONDecodeError as e:
            logger.error(f"[健康巡检] 问题列表 JSON 解析失败: {e}, 文本前300字: {text[:300] if text else 'empty'}")
            return []
        except Exception as e:
            logger.error(f"[健康巡检] 提取问题列表失败: {type(e).__name__}: {e}")
            return []

    async def _score_dimension(self, dimension_name: str, analysis_text: str) -> int:
        """让 AI 对分析文本评分，返回 0-100"""
        prompt = SCORE_PROMPT_TEMPLATE.format(
            dimension_name=dimension_name,
            analysis_text=analysis_text[:2000],
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=512,
            )

            score_text = response.strip()
            logger.info(f"[健康巡检] 维度 {dimension_name} AI 评分原始响应: {score_text[:200]}")

            # 优先匹配 SCORE:XX 格式
            score_match = re.search(r'SCORE\s*[:：]\s*(\d{1,3})', score_text, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
                return max(0, min(100, score))

            # 回退：匹配独立的 1-3 位数字（带"分"或行尾的优先）
            score_with_unit = re.findall(r'(\d{1,3})\s*分', score_text)
            if score_with_unit:
                score = int(score_with_unit[-1])
                if 0 <= score <= 100:
                    return score

            # 再回退：匹配独立的 1-3 位数字
            standalone_numbers = re.findall(r'\b(\d{1,3})\b', score_text)
            # 过滤掉明显不是评分的数字（如端口号 3306、QPS 1200 等）
            valid_scores = [int(n) for n in standalone_numbers if 0 <= int(n) <= 100]
            if valid_scores:
                # 取最后一个有效评分（通常是最终结论）
                return valid_scores[-1]

            logger.warning(f"[健康巡检] 无法从 AI 响应中提取评分: {score_text[:200]}")
            return 50

        except Exception as e:
            logger.error(f"[健康巡检] 评分请求失败: {e}")
            return 50

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
            lines.append("| 序号 | 严重等级 | 问题类型 | 问题描述 | 优化建议 |")
            lines.append("|------|----------|----------|----------|----------|")
            for i, issue in enumerate(issues, 1):
                sev = severity_map.get(issue.get("severity", "info"), "建议")
                cat = issue.get("category", "-")
                desc = issue.get("description", "-")
                suggestion = issue.get("suggestion", "-")
                lines.append(f"| {i} | {sev} | {cat} | {desc} | {suggestion} |")
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
