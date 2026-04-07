#!/usr/bin/env python3
"""
初始化数据库并创建表
"""

import sys

sys.path.insert(0, ".")

from app.database import init_db
from app.config import settings


def main():
    print(f"正在初始化数据库: {settings.database_url}")
    try:
        init_db()
        print("✓ 数据库表创建成功！")
        print("\n创建的表:")
        print("  - connections (连接配置)")
        print("  - performance_metrics (性能指标)")
        print("  - slow_queries (慢查询)")
        print("  - alert_rules (告警规则)")
        print("  - alert_history (告警历史)")
        print("  - reports (性能报告)")
        return 0
    except Exception as e:
        print(f"✗ 数据库初始化失败: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
