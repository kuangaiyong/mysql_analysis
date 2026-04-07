#!/usr/bin/env python3
"""
读取负载生成脚本
生成各种SELECT查询模式，包括慢查询
"""

import argparse
import random
import sys
import time
from datetime import datetime, timedelta

import pymysql

from config import add_db_args, create_connection, get_db_url


class ReadWorkload:
    def __init__(self, conn: pymysql.Connection):
        self.conn = conn
        self._user_count = self._get_count("test_users")
        self._product_count = self._get_count("test_products")
        self._order_count = self._get_count("test_orders")
        self._log_count = self._get_count("test_logs")

    def _get_count(self, table: str) -> int:
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            return cursor.fetchone()["cnt"]

    def _execute_with_timing(
        self, query: str, params: tuple = None, show_explain: bool = False
    ) -> dict:
        if show_explain:
            with self.conn.cursor() as cursor:
                cursor.execute(f"EXPLAIN {query}")
                explain = cursor.fetchall()
                print(f"  EXPLAIN: {explain[0] if explain else 'N/A'}")

        start_time = time.time()
        with self.conn.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
        elapsed = time.time() - start_time
        return {"rows": len(result), "time": elapsed}

    def simple_selects(self, count: int = 1000, show_explain: bool = False):
        print(f"执行简单SELECT {count}次...")
        total_time = 0

        for i in range(count):
            query_type = i % 3
            if query_type == 0:
                user_id = (
                    random.randint(1, self._user_count) if self._user_count > 0 else 1
                )
                result = self._execute_with_timing(
                    "SELECT * FROM test_users WHERE id = %s",
                    (user_id,),
                    show_explain and i == 0,
                )
            elif query_type == 1:
                category = random.choice(
                    ["Electronics", "Clothing", "Food", "Home", "Books"]
                )
                result = self._execute_with_timing(
                    "SELECT * FROM test_products WHERE category = %s LIMIT 100",
                    (category,),
                    show_explain and i == 0,
                )
            else:
                result = self._execute_with_timing(
                    "SELECT * FROM test_users WHERE status = 'active' LIMIT 100",
                    show_explain=show_explain and i == 0,
                )
            total_time += result["time"]

        print(
            f"  完成: {count} 次查询, 总耗时: {total_time:.2f}s, 平均: {total_time / count * 1000:.2f}ms, QPS: {count / total_time:.2f}"
        )
        return total_time

    def range_queries(self, count: int = 500, show_explain: bool = False):
        print(f"执行范围查询 {count}次...")
        total_time = 0

        for i in range(count):
            query_type = i % 2
            if query_type == 0:
                days_ago = random.randint(1, 90)
                result = self._execute_with_timing(
                    "SELECT * FROM test_orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY) LIMIT 100",
                    (days_ago,),
                    show_explain and i == 0,
                )
            else:
                min_price = random.uniform(100, 500)
                max_price = min_price + random.uniform(200, 500)
                result = self._execute_with_timing(
                    "SELECT * FROM test_products WHERE price BETWEEN %s AND %s",
                    (min_price, max_price),
                    show_explain and i == 0,
                )
            total_time += result["time"]

        print(
            f"  完成: {count} 次查询, 总耗时: {total_time:.2f}s, QPS: {count / total_time:.2f}"
        )
        return total_time

    def join_queries(self, count: int = 500, show_explain: bool = False):
        print(f"执行JOIN查询 {count}次...")
        total_time = 0

        for i in range(count):
            query_type = i % 3
            if query_type == 0:
                result = self._execute_with_timing(
                    """
                    SELECT u.name, u.email, o.id as order_id, o.amount, o.status
                    FROM test_users u
                    INNER JOIN test_orders o ON u.id = o.user_id
                    WHERE u.status = 'active'
                    LIMIT 100
                """,
                    show_explain=show_explain and i == 0,
                )
            elif query_type == 1:
                result = self._execute_with_timing(
                    """
                    SELECT o.id, u.name, COUNT(oi.id) as item_count, SUM(oi.quantity * oi.unit_price) as total
                    FROM test_orders o
                    INNER JOIN test_users u ON o.user_id = u.id
                    LEFT JOIN test_order_items oi ON o.id = oi.order_id
                    GROUP BY o.id, u.name
                    LIMIT 100
                """,
                    show_explain=show_explain and i == 0,
                )
            else:
                result = self._execute_with_timing(
                    """
                    SELECT p.name, p.category, COUNT(oi.id) as order_count, SUM(oi.quantity) as total_qty
                    FROM test_products p
                    LEFT JOIN test_order_items oi ON p.id = oi.product_id
                    GROUP BY p.id, p.name, p.category
                    ORDER BY order_count DESC
                    LIMIT 50
                """,
                    show_explain=show_explain and i == 0,
                )
            total_time += result["time"]

        print(
            f"  完成: {count} 次查询, 总耗时: {total_time:.2f}s, QPS: {count / total_time:.2f}"
        )
        return total_time

    def aggregation_queries(self, count: int = 300, show_explain: bool = False):
        print(f"执行聚合查询 {count}次...")
        total_time = 0

        for i in range(count):
            query_type = i % 4
            if query_type == 0:
                result = self._execute_with_timing(
                    """
                    SELECT status, COUNT(*) as cnt, SUM(amount) as total_amount, AVG(amount) as avg_amount
                    FROM test_orders
                    GROUP BY status
                """,
                    show_explain=show_explain and i == 0,
                )
            elif query_type == 1:
                result = self._execute_with_timing(
                    """
                    SELECT user_id, COUNT(*) as order_count
                    FROM test_orders
                    GROUP BY user_id
                    HAVING order_count > 3
                    ORDER BY order_count DESC
                    LIMIT 100
                """,
                    show_explain=show_explain and i == 0,
                )
            elif query_type == 2:
                result = self._execute_with_timing(
                    """
                    SELECT DATE(created_at) as order_date, COUNT(*) as cnt, SUM(amount) as daily_total
                    FROM test_orders
                    WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    GROUP BY DATE(created_at)
                    ORDER BY order_date DESC
                """,
                    show_explain=show_explain and i == 0,
                )
            else:
                result = self._execute_with_timing(
                    """
                    SELECT category, COUNT(*) as product_count, AVG(price) as avg_price, MIN(price) as min_price, MAX(price) as max_price
                    FROM test_products
                    GROUP BY category
                    ORDER BY product_count DESC
                """,
                    show_explain=show_explain and i == 0,
                )
            total_time += result["time"]

        print(
            f"  完成: {count} 次查询, 总耗时: {total_time:.2f}s, QPS: {count / total_time:.2f}"
        )
        return total_time

    def subquery_patterns(self, count: int = 200, show_explain: bool = False):
        print(f"执行子查询 {count}次...")
        total_time = 0

        for i in range(count):
            query_type = i % 3
            if query_type == 0:
                result = self._execute_with_timing(
                    """
                    SELECT * FROM test_users
                    WHERE id IN (SELECT user_id FROM test_orders WHERE amount > 1000)
                    LIMIT 100
                """,
                    show_explain=show_explain and i == 0,
                )
            elif query_type == 1:
                result = self._execute_with_timing(
                    """
                    SELECT * FROM test_products p
                    WHERE EXISTS (
                        SELECT 1 FROM test_order_items oi
                        WHERE oi.product_id = p.id AND oi.quantity > 5
                    )
                    LIMIT 100
                """,
                    show_explain=show_explain and i == 0,
                )
            else:
                result = self._execute_with_timing(
                    """
                    SELECT u.*,
                           (SELECT COUNT(*) FROM test_orders WHERE user_id = u.id) as order_count,
                           (SELECT SUM(amount) FROM test_orders WHERE user_id = u.id) as total_spent
                    FROM test_users u
                    WHERE u.status = 'active'
                    LIMIT 100
                """,
                    show_explain=show_explain and i == 0,
                )
            total_time += result["time"]

        print(
            f"  完成: {count} 次查询, 总耗时: {total_time:.2f}s, QPS: {count / total_time:.2f}"
        )
        return total_time

    def full_table_scans(self, count: int = 50, show_explain: bool = False):
        print(f"执行全表扫描 (慢查询) {count}次...")
        total_time = 0

        for i in range(count):
            query_type = i % 4
            if query_type == 0:
                result = self._execute_with_timing(
                    """
                    SELECT SQL_NO_CACHE * FROM test_large_table
                    WHERE data LIKE '%abc%'
                    LIMIT 100
                """,
                    show_explain=show_explain and i == 0,
                )
            elif query_type == 1:
                result = self._execute_with_timing(
                    """
                    SELECT SQL_NO_CACHE * FROM test_no_index_table
                    WHERE category = 'Electronics' AND value > 50000
                    ORDER BY name
                    LIMIT 100
                """,
                    show_explain=show_explain and i == 0,
                )
            elif query_type == 2:
                result = self._execute_with_timing(
                    """
                    SELECT SQL_NO_CACHE * FROM test_large_table
                    WHERE name LIKE '%test%' AND value > 500000
                    ORDER BY created_at DESC
                    LIMIT 100
                """,
                    show_explain=show_explain and i == 0,
                )
            else:
                result = self._execute_with_timing(
                    """
                    SELECT SQL_NO_CACHE * FROM test_logs
                    WHERE description LIKE '%detail%'
                    ORDER BY created_at DESC
                    LIMIT 500
                """,
                    show_explain=show_explain and i == 0,
                )
            total_time += result["time"]

        print(
            f"  完成: {count} 次查询, 总耗时: {total_time:.2f}s, 平均: {total_time / count * 1000:.2f}ms"
        )
        return total_time

    def like_patterns(self, count: int = 200, show_explain: bool = False):
        print(f"执行LIKE查询 {count}次...")
        total_time = 0

        for i in range(count):
            query_type = i % 3
            if query_type == 0:
                result = self._execute_with_timing(
                    "SELECT * FROM test_users WHERE email LIKE '%@gmail.com' LIMIT 100",
                    show_explain=show_explain and i == 0,
                )
            elif query_type == 1:
                suffix = self._random_suffix()
                result = self._execute_with_timing(
                    f"SELECT * FROM test_users WHERE name LIKE '%{suffix}' LIMIT 100",
                    show_explain=show_explain and i == 0,
                )
            else:
                result = self._execute_with_timing(
                    "SELECT * FROM test_logs WHERE description LIKE '%action%' LIMIT 200",
                    show_explain=show_explain and i == 0,
                )
            total_time += result["time"]

        print(
            f"  完成: {count} 次查询, 总耗时: {total_time:.2f}s, QPS: {count / total_time:.2f}"
        )
        return total_time

    def order_by_limit(self, count: int = 300, show_explain: bool = False):
        print(f"执行ORDER BY + LIMIT分页查询 {count}次...")
        total_time = 0

        for i in range(count):
            offset = random.choice([0, 100, 500, 1000, 5000, 10000])
            result = self._execute_with_timing(
                f"SELECT * FROM test_orders ORDER BY created_at DESC LIMIT {offset}, 20",
                show_explain=show_explain and i == 0,
            )
            total_time += result["time"]

        print(
            f"  完成: {count} 次查询, 总耗时: {total_time:.2f}s, QPS: {count / total_time:.2f}"
        )
        return total_time

    def _random_suffix(self) -> str:
        import string

        return "".join(random.choices(string.ascii_lowercase, k=4))

    def run_all(self, show_explain: bool = False, slow_only: bool = False):
        print("\n=== 执行全部读取负载 ===\n")

        if slow_only:
            self.full_table_scans(100, show_explain)
            self.like_patterns(300, show_explain)
            self.subquery_patterns(200, show_explain)
        else:
            self.simple_selects(1000, show_explain)
            self.range_queries(500, show_explain)
            self.join_queries(500, show_explain)
            self.aggregation_queries(300, show_explain)
            self.subquery_patterns(200, show_explain)
            self.full_table_scans(50, show_explain)
            self.like_patterns(200, show_explain)
            self.order_by_limit(300, show_explain)

        print("\n=== 读取负载完成 ===\n")


def main():
    parser = argparse.ArgumentParser(description="生成读取负载")
    add_db_args(parser)
    parser.add_argument("--simple", type=int, help="简单SELECT数量")
    parser.add_argument("--joins", type=int, help="JOIN查询数量")
    parser.add_argument("--aggregations", type=int, help="聚合查询数量")
    parser.add_argument("--subqueries", type=int, help="子查询数量")
    parser.add_argument("--full-scan", type=int, help="全表扫描数量")
    parser.add_argument("--all", action="store_true", help="执行所有读取模式")
    parser.add_argument("--slow-only", action="store_true", help="只执行慢查询模式")
    parser.add_argument("--explain", action="store_true", help="显示EXPLAIN信息")

    args = parser.parse_args()

    print(f"连接到: {get_db_url(args)}")

    try:
        conn = create_connection(args)
        print("✓ 数据库连接成功!\n")

        workload = ReadWorkload(conn)

        if args.all or args.slow_only:
            workload.run_all(show_explain=args.explain, slow_only=args.slow_only)
        else:
            if args.simple:
                workload.simple_selects(args.simple, args.explain)
            if args.joins:
                workload.join_queries(args.joins, args.explain)
            if args.aggregations:
                workload.aggregation_queries(args.aggregations, args.explain)
            if args.subqueries:
                workload.subquery_patterns(args.subqueries, args.explain)
            if args.full_scan:
                workload.full_table_scans(args.full_scan, args.explain)

        conn.close()
        print("\n✓ 读取负载完成!")

    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
