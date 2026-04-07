#!/usr/bin/env python3
"""
写入负载生成脚本
生成INSERT、UPDATE、DELETE操作
"""

import argparse
import random
import string
import sys
import time
from datetime import datetime, timedelta

import pymysql

from config import add_db_args, create_connection, get_db_url


class WriteWorkload:
    def __init__(self, conn: pymysql.Connection):
        self.conn = conn
        self._user_count = self._get_count("test_users")
        self._product_count = self._get_count("test_products")
        self._order_count = self._get_count("test_orders")

    def _get_count(self, table: str) -> int:
        with self.conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            return cursor.fetchone()["cnt"]

    def _random_string(self, length: int = 10) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _random_date(self, days_back: int = 30) -> datetime:
        delta = timedelta(
            days=random.randint(0, days_back),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        return datetime.now() - delta

    def single_inserts(self, count: int = 1000):
        print(f"执行单条INSERT {count}次...")
        start_time = time.time()
        actions = ["login", "logout", "view_product", "add_to_cart", "checkout"]

        with self.conn.cursor() as cursor:
            for i in range(count):
                user_id = (
                    random.randint(1, self._user_count)
                    if self._user_count > 0
                    else None
                )
                action = random.choice(actions)
                description = f"{action} detail: {self._random_string(30)}"
                query_time = round(random.uniform(0.001, 2.0), 6)
                created_at = self._random_date(7)

                cursor.execute(
                    "INSERT INTO test_logs (user_id, action, description, query_time, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, action, description, query_time, created_at),
                )
                if i % 100 == 0:
                    self.conn.commit()

            self.conn.commit()

        elapsed = time.time() - start_time
        print(
            f"  完成: {count} 条插入, 耗时: {elapsed:.2f}s, QPS: {count / elapsed:.2f}"
        )
        return elapsed

    def batch_inserts(self, count: int = 10000, batch_size: int = 1000):
        print(f"执行批量INSERT {count}条 (batch_size={batch_size})...")
        start_time = time.time()
        actions = ["login", "logout", "view_product", "add_to_cart", "checkout"]

        with self.conn.cursor() as cursor:
            for batch_start in range(0, count, batch_size):
                batch_count = min(batch_size, count - batch_start)
                values = []
                for _ in range(batch_count):
                    user_id = (
                        random.randint(1, self._user_count)
                        if self._user_count > 0
                        else None
                    )
                    action = random.choice(actions)
                    description = f"{action} detail: {self._random_string(30)}"
                    query_time = round(random.uniform(0.001, 2.0), 6)
                    created_at = self._random_date(7)
                    values.append(
                        (user_id, action, description, query_time, created_at)
                    )

                cursor.executemany(
                    "INSERT INTO test_logs (user_id, action, description, query_time, created_at) VALUES (%s, %s, %s, %s, %s)",
                    values,
                )
                self.conn.commit()

        elapsed = time.time() - start_time
        print(
            f"  完成: {count} 条插入, 耗时: {elapsed:.2f}s, QPS: {count / elapsed:.2f}"
        )
        return elapsed

    def simple_updates(self, count: int = 5000):
        print(f"执行简单UPDATE {count}次...")
        start_time = time.time()

        with self.conn.cursor() as cursor:
            for i in range(count):
                user_id = (
                    random.randint(1, self._user_count) if self._user_count > 0 else 1
                )
                score_delta = random.randint(-10, 10)
                cursor.execute(
                    "UPDATE test_users SET score = score + %s WHERE id = %s",
                    (score_delta, user_id),
                )
                if i % 500 == 0:
                    self.conn.commit()

            self.conn.commit()

        elapsed = time.time() - start_time
        print(
            f"  完成: {count} 次更新, 耗时: {elapsed:.2f}s, QPS: {count / elapsed:.2f}"
        )
        return elapsed

    def complex_updates(self, count: int = 1000):
        print(f"执行复杂UPDATE (子查询) {count}次...")
        start_time = time.time()

        with self.conn.cursor() as cursor:
            for i in range(count):
                cursor.execute("""
                    UPDATE test_orders o
                    SET status = 'cancelled'
                    WHERE user_id IN (
                        SELECT id FROM test_users WHERE status = 'inactive'
                    )
                    AND status = 'pending'
                    LIMIT 10
                """)
                self.conn.commit()

        elapsed = time.time() - start_time
        print(
            f"  完成: {count} 次复杂更新, 耗时: {elapsed:.2f}s, QPS: {count / elapsed:.2f}"
        )
        return elapsed

    def range_updates(self, count: int = 500):
        print(f"执行范围UPDATE {count}次...")
        start_time = time.time()

        with self.conn.cursor() as cursor:
            for i in range(count):
                min_price = random.uniform(10, 1000)
                max_price = min_price + random.uniform(100, 500)
                cursor.execute(
                    "UPDATE test_products SET stock = stock + 1 WHERE price BETWEEN %s AND %s",
                    (min_price, max_price),
                )
                if i % 100 == 0:
                    self.conn.commit()

            self.conn.commit()

        elapsed = time.time() - start_time
        print(
            f"  完成: {count} 次范围更新, 耗时: {elapsed:.2f}s, QPS: {count / elapsed:.2f}"
        )
        return elapsed

    def single_deletes(self, count: int = 1000):
        print(f"执行单条DELETE {count}次...")
        start_time = time.time()

        with self.conn.cursor() as cursor:
            for i in range(count):
                cursor.execute("""
                    DELETE FROM test_logs
                    WHERE created_at < DATE_SUB(NOW(), INTERVAL 60 DAY)
                    LIMIT 10
                """)
                self.conn.commit()

        elapsed = time.time() - start_time
        print(
            f"  完成: {count} 次删除, 耗时: {elapsed:.2f}s, QPS: {count / elapsed:.2f}"
        )
        return elapsed

    def bulk_deletes(self, count: int = 100):
        print(f"执行批量DELETE {count}次...")
        start_time = time.time()

        with self.conn.cursor() as cursor:
            for i in range(count):
                order_ids = [random.randint(1, self._order_count) for _ in range(5)]
                placeholders = ", ".join(["%s"] * len(order_ids))
                cursor.execute(
                    f"DELETE FROM test_order_items WHERE order_id IN ({placeholders})",
                    order_ids,
                )
                self.conn.commit()

        elapsed = time.time() - start_time
        print(
            f"  完成: {count} 次批量删除, 耗时: {elapsed:.2f}s, QPS: {count / elapsed:.2f}"
        )
        return elapsed

    def run_all(self, duration_seconds: int = None):
        if duration_seconds:
            print(f"\n=== 执行写入负载 (持续{duration_seconds}秒) ===\n")
            end_time = time.time() + duration_seconds
            ops = 0
            while time.time() < end_time:
                op = random.choice([self.single_inserts, self.simple_updates])
                op(count=100)
                ops += 100
            print(f"\n总计执行 {ops} 次操作")
        else:
            print("\n=== 执行全部写入负载 ===\n")
            self.single_inserts(1000)
            self.batch_inserts(10000)
            self.simple_updates(5000)
            self.complex_updates(1000)
            self.range_updates(500)
            self.single_deletes(1000)
            self.bulk_deletes(100)
            print("\n=== 写入负载完成 ===\n")


def main():
    parser = argparse.ArgumentParser(description="生成写入负载")
    add_db_args(parser)
    parser.add_argument("--inserts", type=int, default=1000, help="INSERT操作数量")
    parser.add_argument("--updates", type=int, default=5000, help="UPDATE操作数量")
    parser.add_argument("--deletes", type=int, default=1000, help="DELETE操作数量")
    parser.add_argument("--duration", type=int, help="持续运行时间(秒)")
    parser.add_argument("--batch-size", type=int, default=1000, help="批量操作大小")
    parser.add_argument("--all", action="store_true", help="执行所有写入模式")

    args = parser.parse_args()

    print(f"连接到: {get_db_url(args)}")

    try:
        conn = create_connection(args)
        print("✓ 数据库连接成功!\n")

        workload = WriteWorkload(conn)

        if args.all or args.duration:
            workload.run_all(duration_seconds=args.duration)
        else:
            print(f"执行INSERT {args.inserts}次...")
            workload.single_inserts(args.inserts)
            workload.batch_inserts(args.inserts * 10, args.batch_size)

            print(f"\n执行UPDATE {args.updates}次...")
            workload.simple_updates(args.updates)
            workload.complex_updates(args.updates // 5)
            workload.range_updates(args.updates // 10)

            print(f"\n执行DELETE {args.deletes}次...")
            workload.single_deletes(args.deletes)
            workload.bulk_deletes(args.deletes // 10)

        conn.close()
        print("\n✓ 写入负载完成!")

    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
