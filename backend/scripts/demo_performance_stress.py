"""
mysql_demo 性能监控场景脚本

产生QPS/TPS、Buffer Pool、连接数等指标变化
适配 mysql_demo 数据库结构
"""

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

import pymysql
from pymysql.cursors import DictCursor

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_db_config

DEMO_DB = "mysql_demo"


class DemoPerformanceStress:
    """mysql_demo 性能压测场景"""

    def __init__(self, db_name: str = DEMO_DB):
        self.db_name = db_name

    def _get_connection(self) -> pymysql.Connection:
        config = get_db_config(self.db_name)
        return pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            charset=config["charset"],
            cursorclass=DictCursor,
        )

    def generate_qps(self, queries_per_second: int = 100, duration: int = 60) -> Dict:
        """生成QPS负载 - 循环执行SELECT查询"""
        print(f"\n{'=' * 60}")
        print(f"开始生成QPS负载: {queries_per_second} QPS, 持续 {duration} 秒")
        print(f"{'=' * 60}")

        total_queries = 0
        start_time = time.time()
        interval = 1.0 / queries_per_second

        queries = [
            "SELECT COUNT(*) as cnt FROM users",
            "SELECT * FROM users WHERE id = %s",
            "SELECT * FROM products WHERE category = %s LIMIT 10",
            "SELECT COUNT(*) as cnt FROM orders WHERE status = %s",
            "SELECT * FROM users WHERE status = %s LIMIT 100",
        ]

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    while time.time() - start_time < duration:
                        loop_start = time.time()

                        query = random.choice(queries)
                        if "%s" in query:
                            if "id =" in query:
                                param = random.randint(1, 500)
                            elif "category" in query:
                                param = random.choice(
                                    ["电子产品", "服装", "食品", "家居"]
                                )
                            elif "status" in query:
                                param = random.choice(
                                    [
                                        "active",
                                        "inactive",
                                        "banned",
                                        "paid",
                                        "completed",
                                    ]
                                )
                            else:
                                param = None
                            cursor.execute(query, (param,))
                        else:
                            cursor.execute(query)

                        cursor.fetchall()
                        total_queries += 1

                        elapsed = time.time() - loop_start
                        sleep_time = max(0, interval - elapsed)
                        if sleep_time > 0:
                            time.sleep(sleep_time)

                        if total_queries % 1000 == 0:
                            print(f"  已执行 {total_queries:,} 次查询", end="\r")

        except KeyboardInterrupt:
            print("\n用户中断...")

        actual_duration = time.time() - start_time
        actual_qps = total_queries / actual_duration

        print(f"\n{'=' * 60}")
        print(f"QPS负载生成完成")
        print(f"  总查询数: {total_queries:,}")
        print(f"  实际QPS: {actual_qps:.2f}")
        print(f"  实际持续时间: {actual_duration:.2f}秒")
        print(f"{'=' * 60}")

        return {
            "total_queries": total_queries,
            "actual_qps": actual_qps,
            "duration": actual_duration,
        }

    def generate_tps(
        self, transactions_per_second: int = 50, duration: int = 60
    ) -> Dict:
        """生成TPS负载 - 循环执行INSERT/UPDATE/DELETE"""
        print(f"\n{'=' * 60}")
        print(f"开始生成TPS负载: {transactions_per_second} TPS, 持续 {duration} 秒")
        print(f"{'=' * 60}")

        total_inserts = 0
        total_updates = 0
        total_deletes = 0
        start_time = time.time()
        interval = 1.0 / transactions_per_second

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    while time.time() - start_time < duration:
                        loop_start = time.time()

                        operation = random.choices(
                            ["insert", "update", "delete"], weights=[0.5, 0.35, 0.15]
                        )[0]

                        if operation == "insert":
                            cursor.execute(
                                "INSERT INTO users (username, email, age, status, balance) VALUES (%s, %s, %s, %s, %s)",
                                (
                                    f"user_{int(time.time() * 1000)}",
                                    f"email_{random.randint(1, 1000000)}@test.com",
                                    random.randint(18, 70),
                                    "active",
                                    random.uniform(0, 10000),
                                ),
                            )
                            total_inserts += 1
                        elif operation == "update":
                            user_id = random.randint(1, 500)
                            cursor.execute(
                                "UPDATE users SET balance = balance + 1 WHERE id = %s",
                                (user_id,),
                            )
                            total_updates += 1
                        else:
                            cursor.execute(
                                "DELETE FROM users WHERE status = %s AND id > 500 LIMIT 1",
                                ("inactive",),
                            )
                            total_deletes += 1

                        conn.commit()

                        elapsed = time.time() - loop_start
                        sleep_time = max(0, interval - elapsed)
                        if sleep_time > 0:
                            time.sleep(sleep_time)

                        total = total_inserts + total_updates + total_deletes
                        if total % 500 == 0:
                            print(
                                f"  已执行 {total:,} 次事务 (I:{total_inserts} U:{total_updates} D:{total_deletes})",
                                end="\r",
                            )

        except KeyboardInterrupt:
            print("\n用户中断...")

        actual_duration = time.time() - start_time
        total_tx = total_inserts + total_updates + total_deletes
        actual_tps = total_tx / actual_duration

        print(f"\n{'=' * 60}")
        print(f"TPS负载生成完成")
        print(f"  总事务数: {total_tx:,}")
        print(f"    INSERT: {total_inserts:,}")
        print(f"    UPDATE: {total_updates:,}")
        print(f"    DELETE: {total_deletes:,}")
        print(f"  实际TPS: {actual_tps:.2f}")
        print(f"  实际持续时间: {actual_duration:.2f}秒")
        print(f"{'=' * 60}")

        return {
            "total_transactions": total_tx,
            "inserts": total_inserts,
            "updates": total_updates,
            "deletes": total_deletes,
            "actual_tps": actual_tps,
            "duration": actual_duration,
        }

    def generate_buffer_pool_miss(self, iterations: int = 10) -> Dict:
        """生成Buffer Pool未命中 - 大表扫描"""
        print(f"\n{'=' * 60}")
        print(f"开始生成Buffer Pool未命中: {iterations} 次大表扫描")
        print(f"{'=' * 60}")

        scan_times = []

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(iterations):
                    start = time.time()

                    cursor.execute(
                        """
                        SELECT SQL_NO_CACHE COUNT(*) as cnt 
                        FROM large_data 
                        WHERE data LIKE %s
                    """,
                        (f"%{random.randint(0, 9)}%",),
                    )

                    cursor.fetchall()

                    elapsed = time.time() - start
                    scan_times.append(elapsed)
                    print(f"  第 {i + 1}/{iterations} 次扫描完成, 耗时 {elapsed:.2f}秒")

                    time.sleep(0.5)

        avg_time = sum(scan_times) / len(scan_times)

        print(f"\n{'=' * 60}")
        print(f"Buffer Pool未命中生成完成")
        print(f"  扫描次数: {iterations}")
        print(f"  平均扫描时间: {avg_time:.2f}秒")
        print(f"  总耗时: {sum(scan_times):.2f}秒")
        print(f"  影响: Innodb_buffer_pool_reads 增加")
        print(f"{'=' * 60}")

        return {
            "iterations": iterations,
            "avg_scan_time": avg_time,
            "total_time": sum(scan_times),
        }

    def generate_concurrent_connections(
        self, num_threads: int = 10, duration: int = 30
    ) -> Dict:
        """生成并发连接 - 多个线程同时保持连接"""
        print(f"\n{'=' * 60}")
        print(f"开始生成并发连接: {num_threads} 个线程, 持续 {duration} 秒")
        print(f"{'=' * 60}")

        results = {"success": 0, "failed": 0}
        lock = threading.Lock()

        def worker(thread_id: int):
            try:
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    end_time = time.time() + duration
                    while time.time() < end_time:
                        cursor.execute("SELECT 1")
                        cursor.fetchall()
                        time.sleep(1)
                conn.close()
                with lock:
                    results["success"] += 1
            except Exception as e:
                with lock:
                    results["failed"] += 1
                print(f"  线程 {thread_id} 错误: {e}")

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, i) for i in range(num_threads)]

            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                print(
                    f"  运行中... {elapsed:.0f}/{duration}秒, 活跃连接: {num_threads}",
                    end="\r",
                )
                time.sleep(1)

            for _ in as_completed(futures):
                pass

        actual_duration = time.time() - start_time

        print(f"\n{'=' * 60}")
        print(f"并发连接生成完成")
        print(f"  线程数: {num_threads}")
        print(f"  成功: {results['success']}")
        print(f"  失败: {results['failed']}")
        print(f"  实际持续时间: {actual_duration:.2f}秒")
        print(f"  影响: Threads_connected 增加")
        print(f"{'=' * 60}")

        return results

    def generate_temp_tables(self, iterations: int = 20) -> Dict:
        """生成临时表使用 - 复杂GROUP BY和ORDER BY"""
        print(f"\n{'=' * 60}")
        print(f"开始生成临时表使用: {iterations} 次")
        print(f"{'=' * 60}")

        total_temp_tables = 0

        queries = [
            """
            SELECT SQL_NO_CACHE u.status, COUNT(*) as cnt, AVG(u.balance) as avg_balance
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.status
            ORDER BY cnt DESC
            """,
            """
            SELECT SQL_NO_CACHE category, COUNT(*) as cnt, SUM(total_amount) as total
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE u.status = 'active'
            GROUP BY category
            ORDER BY total DESC
            """,
            """
            SELECT SQL_NO_CACHE DATE(created_at) as date, status, COUNT(*) as cnt
            FROM orders
            GROUP BY DATE(created_at), status
            ORDER BY date DESC, cnt DESC
            LIMIT 100
            """,
        ]

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(iterations):
                    query = random.choice(queries)
                    cursor.execute(query)
                    cursor.fetchall()
                    total_temp_tables += 1
                    print(f"  第 {i + 1}/{iterations} 次查询完成", end="\r")
                    time.sleep(0.2)

        print(f"\n{'=' * 60}")
        print(f"临时表使用生成完成")
        print(f"  执行次数: {iterations}")
        print(f"  影响: Created_tmp_tables, Created_tmp_disk_tables 增加")
        print(f"{'=' * 60}")

        return {"iterations": iterations}

    def run_all_scenarios(
        self,
        qps: int = 100,
        tps: int = 50,
        duration: int = 30,
        threads: int = 10,
        buffer_iterations: int = 5,
        temp_iterations: int = 10,
    ) -> Dict:
        """运行所有性能场景"""
        print("\n" + "=" * 60)
        print("运行所有性能监控场景")
        print("=" * 60)

        results = {}

        results["qps"] = self.generate_qps(qps, duration)
        results["tps"] = self.generate_tps(tps, duration)
        results["buffer_pool"] = self.generate_buffer_pool_miss(buffer_iterations)
        results["concurrent"] = self.generate_concurrent_connections(threads, duration)
        results["temp_tables"] = self.generate_temp_tables(temp_iterations)

        print("\n" + "=" * 60)
        print("所有性能场景执行完成!")
        print("=" * 60)

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="mysql_demo 性能监控场景脚本")
    parser.add_argument("--qps", type=int, metavar="N", help="生成QPS负载 (每秒查询数)")
    parser.add_argument("--tps", type=int, metavar="N", help="生成TPS负载 (每秒事务数)")
    parser.add_argument(
        "--buffer-miss", type=int, metavar="N", help="生成Buffer Pool未命中 (扫描次数)"
    )
    parser.add_argument(
        "--concurrent", type=int, metavar="N", help="生成并发连接 (线程数)"
    )
    parser.add_argument(
        "--temp-tables", type=int, metavar="N", help="生成临时表使用 (查询次数)"
    )
    parser.add_argument(
        "--duration", type=int, default=30, help="持续时间（秒），默认30"
    )
    parser.add_argument("--all", action="store_true", help="运行所有场景")

    args = parser.parse_args()

    stress = DemoPerformanceStress()

    if args.all:
        stress.run_all_scenarios(
            qps=args.qps or 100,
            tps=args.tps or 50,
            duration=args.duration,
            threads=args.concurrent or 10,
        )
    elif args.qps:
        stress.generate_qps(args.qps, args.duration)
    elif args.tps:
        stress.generate_tps(args.tps, args.duration)
    elif args.buffer_miss:
        stress.generate_buffer_pool_miss(args.buffer_miss)
    elif args.concurrent:
        stress.generate_concurrent_connections(args.concurrent, args.duration)
    elif args.temp_tables:
        stress.generate_temp_tables(args.temp_tables)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
