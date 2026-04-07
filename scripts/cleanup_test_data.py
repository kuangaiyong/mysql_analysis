#!/usr/bin/env python3
"""
清理测试数据脚本
删除测试表或清空数据
"""

import argparse
import sys

import pymysql

from config import add_db_args, create_connection, get_db_url


class CleanupManager:
    TEST_TABLES = [
        "test_order_items",
        "test_orders",
        "test_logs",
        "test_products",
        "test_users",
        "test_large_table",
        "test_no_index_table",
    ]

    def __init__(self, conn: pymysql.Connection):
        self.conn = conn

    def show_status(self):
        print("\n当前测试表状态:\n")
        with self.conn.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'test_%'")
            tables = cursor.fetchall()

            if not tables:
                print("  没有找到 test_* 表")
                return {}

            counts = {}
            for row in tables:
                table_name = list(row.values())[0]
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
                count = cursor.fetchone()["cnt"]
                counts[table_name] = count
                print(f"  {table_name}: {count:,} rows")

            return counts

    def truncate_tables(self):
        print("\n清空测试表数据 (保留表结构)...\n")
        with self.conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in self.TEST_TABLES:
                try:
                    cursor.execute(f"TRUNCATE TABLE {table}")
                    print(f"  ✓ {table} 已清空")
                except pymysql.err.ProgrammingError:
                    print(f"  - {table} 不存在，跳过")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        self.conn.commit()
        print("\n✓ 清空完成")

    def drop_tables(self):
        print("\n删除测试表...\n")
        with self.conn.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in self.TEST_TABLES:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    print(f"  ✓ {table} 已删除")
                except pymysql.err.ProgrammingError as e:
                    print(f"  - {table} 删除失败: {e}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        self.conn.commit()
        print("\n✓ 删除完成")

    def drop_database(self, args):
        print("\n警告: 这将删除整个数据库!\n")
        params = {
            "host": args.host if hasattr(args, "host") else "localhost",
            "port": args.port if hasattr(args, "port") else 3306,
            "user": args.user if hasattr(args, "user") else "root",
            "password": args.password if hasattr(args, "password") else "",
        }

        self.conn.close()
        conn = pymysql.connect(**params, cursorclass=pymysql.cursors.DictCursor)

        with conn.cursor() as cursor:
            db_name = args.database if hasattr(args, "database") else "mysql_demo"
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
            print(f"  ✓ 数据库 {db_name} 已删除")

        conn.close()
        print("\n✓ 数据库删除完成")


def confirm(message: str = "确认执行?") -> bool:
    response = input(f"{message} [y/N]: ").strip().lower()
    return response == "y" or response == "yes"


def main():
    parser = argparse.ArgumentParser(description="清理测试数据")
    add_db_args(parser)
    parser.add_argument(
        "--truncate", action="store_true", help="清空表数据 (保留表结构)"
    )
    parser.add_argument("--drop-tables", action="store_true", help="删除所有测试表")
    parser.add_argument("--drop-database", action="store_true", help="删除整个数据库")
    parser.add_argument(
        "--status", action="store_true", help="只显示状态，不执行任何操作"
    )
    parser.add_argument("--force", action="store_true", help="跳过确认提示")

    args = parser.parse_args()

    if not (args.status or args.truncate or args.drop_tables or args.drop_database):
        args.status = True

    print(f"连接到: {get_db_url(args)}")

    try:
        conn = create_connection(args)
        print("✓ 数据库连接成功!")

        manager = CleanupManager(conn)

        if args.status:
            manager.show_status()
        elif args.truncate:
            if args.force or confirm("确认清空所有测试表数据?"):
                manager.truncate_tables()
            else:
                print("操作已取消")
        elif args.drop_tables:
            if args.force or confirm("确认删除所有测试表?"):
                manager.drop_tables()
            else:
                print("操作已取消")
        elif args.drop_database:
            if args.force or confirm("确认删除整个数据库? 此操作不可恢复!"):
                manager.drop_database(args)
            else:
                print("操作已取消")

        if not args.drop_database:
            conn.close()

        print("\n✓ 操作完成!")

    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
