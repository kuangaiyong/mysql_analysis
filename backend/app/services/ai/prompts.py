"""
AI Prompt 模板

包含诊断、SQL 优化、EXPLAIN 解读等场景的提示词模板
"""

import json
from typing import Dict, Any, List, Optional
from decimal import Decimal
from app.services.ai.utils import DecimalEncoder


# ==================== 系统提示 ====================

DIAGNOSIS_SYSTEM_PROMPT = """你是一位资深 MySQL 数据库专家（10+ 年经验），专注于性能诊断和调优。

## 你的能力
- 分析 MySQL 性能指标（QPS/TPS/Buffer Pool 命中率/锁等待等）
- 识别配置问题并给出修复建议
- 诊断慢查询根因
- 提供 EXPLAIN 执行计划解读
- 给出索引优化建议
- 分析等待事件和瓶颈
- 解读 InnoDB 引擎状态（事务、死锁、Buffer Pool、I/O）
- 分析活跃会话和阻塞链
- 评估复制延迟和主从健康
- 分析内存分配和表空间碎片

## 回答规范
1. **结构化回答**：使用标题、列表、表格组织内容
2. **数据支撑**：引用具体指标数据
3. **可执行建议**：给出具体的 SQL 或配置修改命令
4. **优先级排序**：高优先级问题优先处理
5. **风险提示**：涉及数据安全的操作必须警告
6. **中文回答**：使用中文回答，技术术语可保留英文

## 输出格式示例
### 🔍 问题诊断
[描述发现的问题]

### 📊 数据分析
[引用相关指标]

### 💡 优化建议
1. [建议1] - 优先级：高/中/低
   - 操作：[具体命令]
   - 预期效果：[量化效果]

### ⚠️ 注意事项
[风险提示]
"""

SQL_OPTIMIZATION_SYSTEM_PROMPT = """你是一位 SQL 优化专家，专注于 MySQL 查询性能优化。

## 你的能力
- 分析 SQL 执行计划
- 识别性能瓶颈（全表扫描、filesort、临时表等）
- 重写 SQL 提升性能
- 设计最优索引方案
- 评估优化效果

## 回答规范
1. **问题定位**：准确指出性能瓶颈
2. **原理说明**：解释为什么慢
3. **优化方案**：提供可执行的 SQL 重写和索引建议
4. **效果预估**：量化预期性能提升

## 输出格式
请严格以 JSON 格式返回结果：
{
    "problem_analysis": "问题分析（支持 Markdown 格式）",
    "optimized_sql": "优化后的完整 SQL 语句",
    "optimization_points": [
        {
            "type": "rewrite 或 index 或 config",
            "description": "具体优化描述",
            "impact": "high 或 medium 或 low"
        }
    ],
    "index_suggestions": [
        {
            "table": "表名",
            "index_name": "idx_表名_列名",
            "columns": ["列1", "列2"],
            "type": "BTREE",
            "create_statement": "CREATE INDEX idx_表名_列名 ON 表名 (列1, 列2);",
            "drop_statement": "DROP INDEX idx_表名_列名 ON 表名;",
            "reason": "原因说明",
            "impact": "high 或 medium 或 low",
            "estimated_improvement": "预计提升效果描述"
        }
    ],
    "expected_improvement": "整体预期效果说明"
}

注意：
- index_suggestions 中的 create_statement 和 drop_statement 必须是完整可执行的 DDL 语句
- index_name 使用 idx_表名_列名 的命名规范
- 如果原 SQL 已经最优，optimized_sql 返回原 SQL 即可
"""

EXPLAIN_SYSTEM_PROMPT = """你是一位 MySQL 执行计划解读专家。

## 你的任务
将 EXPLAIN 结果转换为易于理解的自然语言解释。

## 需要解释的内容
1. **访问类型**：type 字段的含义和性能影响
2. **扫描行数**：rows 字段的影响
3. **额外操作**：Extra 字段的含义（filesort、temporary 等）
4. **索引使用**：是否使用了索引，使用了哪个索引
5. **性能评估**：整体性能评分（A-E 五级）
6. **优化建议**：如果需要优化，给出建议

## 输出格式
请以清晰的结构化格式返回，使用中文。
"""


# ==================== 用户提示模板 ====================

DIAGNOSIS_PROMPT_TEMPLATE = """## 当前 MySQL 实例状态

### 连接信息
- 连接 ID: {connection_id}
- 数据库: {database_name}

### 性能指标
{performance_metrics}

### 配置信息
{config_issues}

### Top 慢查询
{slow_queries}

### 等待事件分析
{wait_events}
{extra_context}
---

## 用户问题
{question}

---

请基于以上数据分析问题并给出诊断建议。回答请使用中文。
"""

SQL_OPTIMIZATION_PROMPT_TEMPLATE = """请分析以下 SQL 并提供优化建议：

## 原始 SQL
```sql
{sql}
```

## EXPLAIN 结果
{explain_result}

## 表结构（仅关键字段）
{table_structure}

## 现有索引
{indexes}

## 表统计信息
{table_stats}

---

请分析问题并给出优化建议，以 JSON 格式返回。
"""

EXPLAIN_PROMPT_TEMPLATE = """请解读以下 EXPLAIN 结果：

## SQL
```sql
{sql}
```

## EXPLAIN 结果
{explain_result}

---

请用中文解释这个执行计划，包括：
1. 访问类型说明
2. 索引使用情况
3. 性能瓶颈识别
4. 优化建议
5. 性能评分（A-E）
"""


# ==================== 快速问题模板 ====================

QUICK_QUESTIONS = {
    "slow_database": {
        "question": "为什么数据库最近变慢了？",
        "context_type": "full"
    },
    "config_issues": {
        "question": "分析当前 MySQL 配置问题",
        "context_type": "config"
    },
    "slow_queries": {
        "question": "Top 5 慢查询是什么？如何优化？",
        "context_type": "slow_queries"
    },
    "index_suggestions": {
        "question": "当前系统需要添加哪些索引？",
        "context_type": "indexes"
    },
    "buffer_pool": {
        "question": "Buffer Pool 命中率正常吗？需要调整吗？",
        "context_type": "buffer_pool"
    },
    "lock_analysis": {
        "question": "当前有锁等待问题吗？",
        "context_type": "locks"
    },
    "connection_health": {
        "question": "连接池配置合理吗？",
        "context_type": "connections"
    },
    "io_bottleneck": {
        "question": "是否存在 I/O 瓶颈？",
        "context_type": "io"
    }
}


# ==================== 辅助函数 ====================

def _dump_context(data: Any, max_len: int = 3000) -> str:
    """JSON 序列化并截断"""
    text = json.dumps(data, ensure_ascii=False, indent=2, cls=DecimalEncoder)
    if len(text) > max_len:
        return text[:max_len] + "\n... (已截断)"
    return text


def build_diagnosis_prompt(
    connection_id: int,
    database_name: str,
    performance_metrics: Dict[str, Any],
    config_issues: List[Dict[str, Any]],
    slow_queries: List[Dict[str, Any]],
    wait_events: Dict[str, Any],
    question: str,
    extra_context: Optional[Dict[str, Any]] = None
) -> str:
    """构建诊断提示"""

    import json

    # 构建深度采集的额外上下文段落
    extra_sections = ""
    if extra_context:
        if extra_context.get("innodb_status"):
            extra_sections += f"\n### InnoDB 引擎状态\n{_dump_context(extra_context['innodb_status'])}\n"
        if extra_context.get("active_sessions"):
            extra_sections += f"\n### 活跃会话\n{_dump_context(extra_context['active_sessions'])}\n"
        if extra_context.get("database_sizes"):
            extra_sections += f"\n### 数据库/表大小\n{_dump_context(extra_context['database_sizes'])}\n"
        if extra_context.get("replication_status"):
            extra_sections += f"\n### 复制状态\n{_dump_context(extra_context['replication_status'])}\n"
        if extra_context.get("memory_usage"):
            extra_sections += f"\n### 内存使用分布\n{_dump_context(extra_context['memory_usage'])}\n"

    return DIAGNOSIS_PROMPT_TEMPLATE.format(
        connection_id=connection_id,
        database_name=database_name or "未知",
        performance_metrics=_dump_context(performance_metrics),
        config_issues=_dump_context(config_issues),
        slow_queries=_dump_context(slow_queries[:10]),
        wait_events=_dump_context(wait_events),
        extra_context=extra_sections,
        question=question
    )


def build_sql_optimization_prompt(
    sql: str,
    explain_result: Any,
    table_structure: Dict[str, Any],
    indexes: List[Dict[str, Any]],
    table_stats: Dict[str, Any]
) -> str:
    """构建 SQL 优化提示"""

    import json

    return SQL_OPTIMIZATION_PROMPT_TEMPLATE.format(
        sql=sql,
        explain_result=json.dumps(explain_result, ensure_ascii=False, indent=2, cls=DecimalEncoder) if explain_result else "无",
        table_structure=json.dumps(table_structure, ensure_ascii=False, indent=2, cls=DecimalEncoder) if table_structure else "无",
        indexes=json.dumps(indexes, ensure_ascii=False, indent=2, cls=DecimalEncoder) if indexes else "无",
        table_stats=json.dumps(table_stats, ensure_ascii=False, indent=2, cls=DecimalEncoder) if table_stats else "无",
    )


def build_explain_prompt(sql: str, explain_result: Any) -> str:
    """构建 EXPLAIN 解读提示"""
    
    import json
    
    return EXPLAIN_PROMPT_TEMPLATE.format(
        sql=sql,
        explain_result=json.dumps(explain_result, ensure_ascii=False, indent=2, cls=DecimalEncoder)
    )
