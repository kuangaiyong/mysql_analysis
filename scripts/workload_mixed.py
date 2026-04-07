#!/usr/bin/env python3
"""
混合负载生成脚本
模拟真实应用的并发读写操作
"""

import argparse
import random
import string
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Any

import pymysql

from config import add_db_args, get_connection_params, get_db_url


class MixedWorkload:
    CATEGORIES = [
        "Electronics",
        "Clothing",
        "Food",
        "Home",
        "Books",
        "Sports",
        "Beauty",
        "Auto",
    ]
    ACTIONS = [
        "login",
        "logout",
        "view_product",
        "add_to_cart",
        "checkout",
        "payment",
        "search",
    ]
    USER_STATUSES = ["active", "active", "active", "inactive", "pending"]
    ORDER_STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled"]

    def __init__(self, read_ratio: float = 0.7):
        self.read_ratio = read_ratio
        self._lock = threading.Lock()
        self._stats = {
            "reads": 0,
            "writes": 0,
            "errors": 0,
            "read_time": 0.0,
            "write_time": 0.0,
        }

    def _get_connection(self, args) -> pymysql.Connection:
        params = get_connection_params(args)
        return pymysql.connect(
            host=params["host"],
            port=params["port"],
            user=params["user"],
            password=params["password"],
            database=params["database"],
            charset=params["charset"],
            cursorclass=pymysql.cursors.DictCursor,
        )

    def _random_string(self, length: int = 10) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _update_stats(self, op_type: str, elapsed: float, is_error: bool = False):
        with self._lock:
            if is_error:
                self._stats["errors"] += 1
            elif op_type == "read":
                self._stats["reads"] += 1
                self._stats["read_time"] += elapsed
            else:
                self._stats["writes"] += 1
                self._stats["write_time"] += elapsed

    def _execute_read(self, conn: pymysql.Connection, args) -> float:
        start_time = time.time()
        try:
            with conn.cursor() as cursor:
                query_type = random.randint(0, 5)
                if query_type == 0:
                    cursor.execute(
                        "SELECT * FROM test_users WHERE status = %s LIMIT 50",
                        (random.choice(self.USER_STATUSES),),
                    )
                elif query_type == 1:
                    cursor.execute(
                        "SELECT * FROM test_products WHERE category = %s LIMIT 50",
                        (random.choice(self.CATEGORIES),),
                    )
                elif query_type == 2:
                    cursor.execute("""
                        SELECT u.name, o.id, o.amount
                        FROM test_users u
                        JOIN test_orders o ON u.id = o.user_id
                        LIMIT 50
                    """)
                elif query_type == 3:
                    cursor.execute("""
                        SELECT status, COUNT(*) as cnt, SUM(amount) as total
                        FROM test_orders
                        GROUP BY status
                    """)
                elif query_type == 4:
                    cursor.execute(
                        "SELECT * FROM test_logs WHERE action = %s LIMIT 100",
                        (random.choice(self.ACTIONS),),
                    )
                else:
                    cursor.execute(
                        "SELECT * FROM test_orders ORDER BY created_at DESC LIMIT 20"
                    )
                cursor.fetchall()
            elapsed = time.time() - start_time
            self._update_stats("read", elapsed)
            return elapsed
        except Exception as e:
            self._update_stats("read", 0, is_error=True)
            raise

    def _execute_write(self, conn: pymysql.Connection, args) -> float:
        start_time = time.time()
        try:
            with conn.cursor() as cursor:
                write_type = random.randint(0, 3)
                if write_type == 0:
                    cursor.execute(
                        "INSERT INTO test_logs (user_id, action, description, query_time) VALUES (%s, %s, %s, %s)",
                        (
                            random.randint(1, 10000),
                            random.choice(self.ACTIONS),
                            f"detail: {self._random_string(30)}",
                            random.uniform(0.001, 2.0),
                        ),
                    )
                elif write_type == 1:
                    cursor.execute(
                        "UPDATE test_users SET score = score + 1 WHERE id = %s",
                        (random.randint(1, 10000),),
                    )
                elif write_type == 2:
                    cursor.execute(
                        "UPDATE test_products SET stock = stock - 1 WHERE id = %s AND stock > 0",
                        (random.randint(1, 1000),),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM test_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY) LIMIT 10"
                    )
                conn.commit()
            elapsed = time.time() - start_time
            self._update_stats("write", elapsed)
            return elapsed
        except Exception as e:
            self._update_stats("write", 0, is_error=True)
            raise

    def _worker(self, args, operations: int, worker_id: int) -> Dict[str, Any]:
        local_stats = {"reads": 0, "writes": 0, "errors": 0, "time": 0.0}
        conn = None
        try:
            conn = self._get_connection(args)
            for _ in range(operations):
                is_read = random.random() < self.read_ratio
                try:
                    if is_read:
                        elapsed = self._execute_read(conn, args)
                        local_stats["reads"] += 1
                    else:
                        elapsed = self._execute_write(conn, args)
                        local_stats["writes"] += 1
                    local_stats["time"] += elapsed
                except Exception:
                    local_stats["errors"] += 1
        finally:
            if conn:
                conn.close()
        return local_stats

    def run_fixed_operations(self, args, total_ops: int = 10000, num_threads: int = 10):
        print(
            f"\n=== 执行混合负载 (总操作: {total_ops}, 线程数: {num_threads}, 读比例: {self.read_ratio * 100:.0f}%) ===\n"
        )

        ops_per_thread = total_ops // num_threads
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(self._worker, args, ops_per_thread, i)
                for i in range(num_threads)
            ]

            completed = 0
            for future in as_completed(futures):
                result = future.result()
                completed += 1
                print(f"  线程完成: {completed}/{num_threads}", end="\r")

        elapsed = time.time() - start_time
        self._print_stats(elapsed, total_ops)

    def run_duration(self, args, duration_seconds: int = 60, num_threads: int = 10):
        print(
            f"\n=== 执行混合负载 (持续时间: {duration_seconds}s, 线程数: {num_threads}, 读比例: {self.read_ratio * 100:.0f}%) ===\n"
        )

        start_time = time.time()
        end_time = start_time + duration_seconds

        def duration_worker(args, worker_id):
            local_stats = {"reads": 0, "writes": 0, "errors": 0, "time": 0.0}
            conn = None
            try:
                conn = self._get_connection(args)
                while time.time() < end_time:
                    is_read = random.random() < self.read_ratio
                    try:
                        if is_read:
                            elapsed = self._execute_read(conn, args)
                            local_stats["reads"] += 1
                        else:
                            elapsed = self._execute_write(conn, args)
                            local_stats["writes"] += 1
                        local_stats["time"] += elapsed
                    except Exception:
                        local_stats["errors"] += 1
            finally:
                if conn:
                    conn.close()
            return local_stats

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(duration_worker, args, i) for i in range(num_threads)
            ]

            last_print = start_time
            while time.time() < end_time:
                time.sleep(1)
                remaining = int(end_time - time.time())
                if time.time() - last_print >= 5:
                    print(f"  剩余时间: {remaining}s...", end="\r")
                    last_print = time.time()

            for future in as_completed(futures):
                future.result()

        elapsed = time.time() - start_time
        total_ops = self._stats["reads"] + self._stats["writes"]
        self._print_stats(elapsed, total_ops)

    def _print_stats(self, elapsed: float, total_ops: int):
        print(f"\n\n=== 负载测试结果 ===\n")
        print(f"总耗时: {elapsed:.2f}s")
        print(f"总操作数: {total_ops}")
        print(f"总体QPS: {total_ops / elapsed:.2f}")
        print(f"\n操作分布:")
        print(
            f"  读操作: {self._stats['reads']} ({self._stats['reads'] / total_ops * 100:.1f}%)"
        )
        print(
            f"  写操作: {self._stats['writes']} ({self._stats['writes'] / total_ops * 100:.1f}%)"
        )
        print(f"  错误: {self._stats['errors']}")

        if self._stats["reads"] > 0:
            print(
                f"\n读操作平均延迟: {self._stats['read_time'] / self._stats['reads'] * 1000:.2f}ms"
            )
        if self._stats["writes"] > 0:
            print(
                f"写操作平均延迟: {self._stats['write_time'] / self._stats['writes'] * 1000:.2f}ms"
            )

    def profile_read_heavy(
        self, args, duration_seconds: int = 60, num_threads: int = 10
    ):
        self.read_ratio = 0.8
        print("配置: 读密集型 (80% 读, 20% 写)")
        self.run_duration(args, duration_seconds, num_threads)

    def profile_balanced(self, args, duration_seconds: int = 60, num_threads: int = 10):
        self.read_ratio = 0.5
        print("配置: 平衡型 (50% 读, 50% 写)")
        self.run_duration(args, duration_seconds, num_threads)

    def profile_write_heavy(
        self, args, duration_seconds: int = 60, num_threads: int = 10
    ):
        self.read_ratio = 0.3
        print("配置: 写密集型 (30% 读, 70% 写)")
        self.run_duration(args, duration_seconds, num_threads)

    def profile_oltp(self, args, duration_seconds: int = 60, num_threads: int = 10):
        self.read_ratio = 0.85
        print("配置: OLTP模式 (85% 读, 15% 写, 短事务)")
        self.run_duration(args, duration_seconds, num_threads)


def main():
    parser = argparse.ArgumentParser(description="生成混合读写负载")
    add_db_args(parser)
    parser.add_argument("--threads", type=int, default=10, help="并发线程数")
    parser.add_argument("--duration", type=int, help="持续运行时间(秒)")
    parser.add_argument("--ops", type=int, help="总操作数(替代duration)")
    parser.add_argument(
        "--profile",
        choices=["read_heavy", "balanced", "write_heavy", "oltp"],
        help="预定义负载模式",
    )
    parser.add_argument("--read-ratio", type=float, help="读操作比例(0.0-1.0)")

    args = parser.parse_args()

    print(f"连接到: {get_db_url(args)}")

    try:
        params = get_connection_params(args)
        test_conn = pymysql.connect(
            host=params["host"],
            port=params["port"],
            user=params["user"],
            password=params["password"],
            database=params["database"],
            charset=params["charset"],
        )
        print("✓ 数据库连接成功!\n")
        test_conn.close()

        read_ratio = args.read_ratio if args.read_ratio is not None else 0.7
        workload = MixedWorkload(read_ratio=read_ratio)

        if args.profile:
            profile_method = getattr(workload, f"profile_{args.profile}")
            profile_method(args, args.duration or 60, args.threads)
        elif args.ops:
            workload.run_fixed_operations(args, args.ops, args.threads)
        elif args.duration:
            workload.run_duration(args, args.duration, args.threads)
        else:
            workload.run_duration(args, 60, args.threads)

        print("\n✓ 混合负载完成!")

    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
