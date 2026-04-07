#!/usr/bin/env python3
"""
数据库连接配置模块
为所有测试脚本提供统一的数据库连接参数和CLI参数解析
"""

import argparse
from typing import Dict, Any, Optional

import pymysql
from pymysql.cursors import DictCursor


# 默认数据库连接配置
DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "87j766h",
    "database": "mysql_demo",
    "charset": "utf8mb4",
}


def get_connection_params(args: Optional[argparse.Namespace] = None) -> Dict[str, Any]:
    """
    从CLI参数获取连接参数，使用默认值填充缺失项

    Args:
        args: argparse解析的命名空间对象

    Returns:
        连接参数字典
    """
    params = DEFAULT_CONFIG.copy()

    if args is not None:
        if hasattr(args, "host") and args.host:
            params["host"] = args.host
        if hasattr(args, "port") and args.port:
            params["port"] = args.port
        if hasattr(args, "user") and args.user:
            params["user"] = args.user
        if hasattr(args, "password") and args.password is not None:
            params["password"] = args.password
        if hasattr(args, "database") and args.database:
            params["database"] = args.database

    return params


def create_connection(args: Optional[argparse.Namespace] = None) -> pymysql.Connection:
    """
    创建数据库连接

    Args:
        args: argparse解析的命名空间对象

    Returns:
        pymysql连接对象
    """
    params = get_connection_params(args)
    return pymysql.connect(
        host=params["host"],
        port=params["port"],
        user=params["user"],
        password=params["password"],
        database=params["database"],
        charset=params["charset"],
        cursorclass=DictCursor,
    )


def add_db_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    为argparse解析器添加标准数据库连接参数

    Args:
        parser: argparse解析器

    Returns:
        添加了数据库参数的解析器
    """
    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_CONFIG["host"],
        help=f"数据库主机地址 (default: {DEFAULT_CONFIG['host']})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_CONFIG["port"],
        help=f"数据库端口 (default: {DEFAULT_CONFIG['port']})",
    )
    parser.add_argument(
        "--user",
        type=str,
        default=DEFAULT_CONFIG["user"],
        help=f"数据库用户名 (default: {DEFAULT_CONFIG['user']})",
    )
    parser.add_argument(
        "--password",
        type=str,
        default=DEFAULT_CONFIG["password"],
        help="数据库密码",
    )
    parser.add_argument(
        "--database",
        type=str,
        default=DEFAULT_CONFIG["database"],
        help=f"数据库名称 (default: {DEFAULT_CONFIG['database']})",
    )
    return parser


def get_db_url(args: Optional[argparse.Namespace] = None) -> str:
    """
    获取数据库连接URL（用于显示）

    Args:
        args: argparse解析的命名空间对象

    Returns:
        数据库URL字符串
    """
    params = get_connection_params(args)
    return f"mysql://{params['user']}@{params['host']}:{params['port']}/{params['database']}"


if __name__ == "__main__":
    # 测试配置模块
    parser = argparse.ArgumentParser(description="测试数据库连接配置")
    add_db_args(parser)
    args = parser.parse_args()

    print(f"连接参数: {get_connection_params(args)}")
    print(f"数据库URL: {get_db_url(args)}")

    try:
        conn = create_connection(args)
        print("✓ 数据库连接成功!")
        conn.close()
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
