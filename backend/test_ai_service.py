#!/usr/bin/env python3
"""
AI 诊断服务测试脚本

测试 GLM API 连接和基本功能
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ai.llm_adapter import ZhipuAdapter
from app.config import settings


async def test_glm_connection():
    """测试 GLM API 连接"""
    
    print("=" * 60)
    print("测试 GLM API 连接")
    print("=" * 60)
    
    print(f"\n配置信息:")
    print(f"  API Key: {settings.zhipu_api_key[:20]}...")
    print(f"  API Base: {settings.zhipu_api_base}")
    print(f"  Model: {settings.zhipu_model}")
    
    adapter = ZhipuAdapter(
        api_key=settings.zhipu_api_key,
        base_url=settings.zhipu_api_base,
        model=settings.zhipu_model,
    )
    
    # 测试 1: 简单对话
    print("\n" + "-" * 40)
    print("测试 1: 简单对话")
    print("-" * 40)
    
    try:
        response = await adapter.chat(
            messages=[{"role": "user", "content": "你好，请用一句话介绍 MySQL 的 InnoDB 存储引擎"}],
            system_prompt="你是一位 MySQL 数据库专家，请简洁回答问题。",
            temperature=0.3
        )
        print(f"响应: {response[:200]}...")
        print("✅ 测试通过")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    # 测试 2: 结构化分析
    print("\n" + "-" * 40)
    print("测试 2: 结构化分析")
    print("-" * 40)
    
    try:
        result = await adapter.analyze(
            prompt="""
分析以下 MySQL 配置并给出建议：

innodb_buffer_pool_size = 128M
max_connections = 100
slow_query_log = OFF

请以 JSON 格式返回：
{
    "issues": ["问题1", "问题2"],
    "suggestions": ["建议1", "建议2"]
}
""",
            data=None
        )
        print(f"分析结果: {result}")
        print("✅ 测试通过")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    # 测试 3: MySQL 诊断场景
    print("\n" + "-" * 40)
    print("测试 3: MySQL 诊断场景")
    print("-" * 40)
    
    try:
        response = await adapter.chat(
            messages=[{
                "role": "user", 
                "content": """
MySQL 实例状态：
- QPS: 1500
- Buffer Pool 命中率: 85%
- 慢查询数: 120/小时

请分析这个实例的性能状况并给出优化建议。
"""
            }],
            system_prompt="你是一位资深 MySQL DBA，请分析问题并给出可执行的优化建议。使用中文回答。",
            temperature=0.3
        )
        print(f"诊断结果:\n{response[:500]}...")
        print("✅ 测试通过")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("所有测试通过！AI 服务配置正确。")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_glm_connection())
    sys.exit(0 if success else 1)
