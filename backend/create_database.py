#!/usr/bin/env python3
"""
创建MySQL数据库脚本
从环境变量读取数据库连接信息
"""

import os
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库配置
db_host = os.getenv("TARGET_MYSQL_HOST", "localhost")
db_port = int(os.getenv("TARGET_MYSQL_PORT", "3306"))
db_user = os.getenv("TARGET_MYSQL_USER", "root")
db_password = os.getenv("TARGET_MYSQL_PASSWORD", "")
db_name = os.getenv("TARGET_MYSQL_DATABASE", "mysql_analysis")


def create_database():
    """创建mysql_analysis数据库"""

    # 检查必需的环境变量
    if not db_password:
        print("✗ 错误: TARGET_MYSQL_PASSWORD 环境变量未设置")
        print("  请在 .env 文件中设置该变量，或者创建 .env 文件从 .env.example 复制")
        return 1

    # 连接到MySQL服务器（不指定数据库）
    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            charset="utf8mb4",
        )
    except Exception as e:
        print(f"✗ 连接MySQL服务器失败: {str(e)}")
        print(f"  检查配置: host={db_host}, port={db_port}, user={db_user}")
        return 1

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            print(f"✓ 数据库 '{db_name}' 创建成功！")
        return 0
    except Exception as e:
        print(f"✗ 创建数据库失败: {str(e)}")
        return 1
    finally:
        connection.close()


if __name__ == "__main__":
    exit(create_database())
