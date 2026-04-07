"""
mysql_demo 综合测试脚本

统一入口：初始化、数据生成、所有场景测试
"""

import argparse
import sys
import time

sys.path.insert(0, sys.path[0])

from demo_operations import (
    DemoDatabase,
    DemoDataGenerator,
    DemoOperations,
    print_status,
)
from demo_slow_query_scenarios import DemoSlowQueryScenarios
from demo_lock_scenarios import DemoLockScenarios
from demo_performance_stress import DemoPerformanceStress


class DemoTestRunner:
    """mysql_demo 综合测试运行器"""

    def __init__(self):
        self.db = DemoDatabase()
        self.generator = DemoDataGenerator()
        self.operations = DemoOperations()
        self.slow_query = DemoSlowQueryScenarios()
        self.lock = DemoLockScenarios()
        self.stress = DemoPerformanceStress()

    def run_init(self) -> bool:
        """初始化数据库"""
        return self.db.init_database()

    def run_generate(
        self,
        users: int = 100,
        products: int = 50,
        orders: int = 200,
        logs: int = 100,
        large_data: int = 10000,
        lock_test: int = 100,
        no_index_data: int = 10000,
    ):
        """生成测试数据"""
        return self.generator.generate_all(
            users, products, orders, logs, large_data, lock_test, no_index_data
        )

    def run_read_operations(self):
        """运行读操作"""
        return self.operations.read_operations()

    def run_write_operations(self):
        """运行写操作"""
        return self.operations.write_operations()

    def run_slow_query_scenarios(self, iterations: int = 5):
        """运行慢查询场景"""
        return self.slow_query.run_all_scenarios(iterations)

    def run_lock_scenarios(self, duration: int = 20):
        """运行锁场景"""
        return self.lock.run_all_scenarios(duration)

    def run_performance_scenarios(
        self, qps: int = 100, tps: int = 50, duration: int = 30, threads: int = 10
    ):
        """运行性能场景"""
        return self.stress.run_all_scenarios(qps, tps, duration, threads)

    def run_all_tests(
        self,
        slow_query_iterations: int = 3,
        lock_duration: int = 15,
        stress_duration: int = 20,
        qps: int = 100,
        tps: int = 50,
        threads: int = 5,
    ):
        """运行所有测试场景"""
        print("\n" + "=" * 70)
        print(" " * 20 + "mysql_demo 综合测试")
        print("=" * 70)

        start_time = time.time()
        results = {}

        print("\n[1/5] 执行读操作测试...")
        results["read"] = self.run_read_operations()

        print("\n[2/5] 执行写操作测试...")
        results["write"] = self.run_write_operations()

        print("\n[3/5] 执行慢查询场景测试...")
        results["slow_query"] = self.run_slow_query_scenarios(slow_query_iterations)

        print("\n[4/5] 执行锁场景测试...")
        results["lock"] = self.run_lock_scenarios(lock_duration)

        print("\n[5/5] 执行性能压力测试...")
        results["performance"] = self.run_performance_scenarios(
            qps, tps, stress_duration, threads
        )

        total_time = time.time() - start_time

        print("\n" + "=" * 70)
        print(" " * 20 + "测试完成汇总")
        print("=" * 70)
        print(f"  总耗时: {total_time:.2f} 秒")
        print(f"  读操作: ✓ 完成")
        print(f"  写操作: ✓ 完成")
        print(f"  慢查询场景: ✓ 完成")
        print(f"  锁场景: ✓ 完成")
        print(f"  性能压力: ✓ 完成")
        print("=" * 70)

        return results

    def run_full_demo(self, data_config: dict = None):
        """完整演示流程"""
        print("\n" + "=" * 70)
        print(" " * 15 + "mysql_demo 完整演示流程")
        print("=" * 70)

        if data_config is None:
            data_config = {
                "users": 100,
                "products": 50,
                "orders": 200,
                "logs": 100,
                "large_data": 5000,
                "lock_test": 100,
                "no_index_data": 5000,
            }

        start_time = time.time()

        print("\n[阶段1/4] 初始化数据库...")
        if not self.run_init():
            print("初始化失败，退出")
            return False

        print("\n[阶段2/4] 生成测试数据...")
        self.run_generate(**data_config)

        print("\n[阶段3/4] 查看数据库状态...")
        print_status()

        print("\n[阶段4/4] 运行所有测试...")
        results = self.run_all_tests(
            slow_query_iterations=3,
            lock_duration=15,
            stress_duration=15,
            qps=50,
            tps=30,
            threads=5,
        )

        total_time = time.time() - start_time

        print("\n" + "=" * 70)
        print(" " * 15 + "完整演示流程结束")
        print("=" * 70)
        print(f"  总耗时: {total_time:.2f} 秒")
        print("=" * 70)

        return results


def main():
    parser = argparse.ArgumentParser(
        description="mysql_demo 综合测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 完整演示（初始化+数据生成+所有测试）
  python demo_test_runner.py --full

  # 仅初始化数据库
  python demo_test_runner.py --init

  # 生成测试数据
  python demo_test_runner.py --generate --users 200 --large-data 10000

  # 运行所有测试（需要先初始化和生成数据）
  python demo_test_runner.py --all-tests

  # 单独运行某类测试
  python demo_test_runner.py --read
  python demo_test_runner.py --slow-query --iterations 5
  python demo_test_runner.py --lock --duration 30
  python demo_test_runner.py --stress --duration 60
        """,
    )

    # 主要操作
    parser.add_argument("--full", action="store_true", help="运行完整演示流程")
    parser.add_argument("--init", action="store_true", help="初始化数据库")
    parser.add_argument("--generate", action="store_true", help="生成测试数据")
    parser.add_argument(
        "--all-tests", action="store_true", help="运行所有测试（不含初始化和数据生成）"
    )

    # 单独测试
    parser.add_argument("--read", action="store_true", help="运行读操作")
    parser.add_argument("--write", action="store_true", help="运行写操作")
    parser.add_argument("--slow-query", action="store_true", help="运行慢查询场景")
    parser.add_argument("--lock", action="store_true", help="运行锁场景")
    parser.add_argument("--stress", action="store_true", help="运行性能压力测试")
    parser.add_argument("--status", action="store_true", help="查看数据库状态")

    # 参数配置
    parser.add_argument("--users", type=int, default=100, help="用户数据数量")
    parser.add_argument("--products", type=int, default=50, help="商品数据数量")
    parser.add_argument("--orders", type=int, default=200, help="订单数据数量")
    parser.add_argument("--logs", type=int, default=100, help="日志数据数量")
    parser.add_argument(
        "--large-data", type=int, default=10000, help="大数据表数据数量"
    )
    parser.add_argument("--lock-test", type=int, default=100, help="锁测试数据数量")
    parser.add_argument("--no-index", type=int, default=10000, help="无索引表数据数量")

    parser.add_argument("--iterations", type=int, default=3, help="慢查询迭代次数")
    parser.add_argument(
        "--duration", type=int, default=20, help="锁/压力测试持续时间（秒）"
    )
    parser.add_argument("--qps", type=int, default=100, help="QPS目标值")
    parser.add_argument("--tps", type=int, default=50, help="TPS目标值")
    parser.add_argument("--threads", type=int, default=10, help="并发线程数")

    args = parser.parse_args()

    runner = DemoTestRunner()

    if args.full:
        data_config = {
            "users": args.users,
            "products": args.products,
            "orders": args.orders,
            "logs": args.logs,
            "large_data": args.large_data,
            "lock_test": args.lock_test,
            "no_index_data": args.no_index,
        }
        runner.run_full_demo(data_config)
    elif args.init:
        runner.run_init()
    elif args.generate:
        runner.run_generate(
            args.users,
            args.products,
            args.orders,
            args.logs,
            args.large_data,
            args.lock_test,
            args.no_index,
        )
    elif args.all_tests:
        runner.run_all_tests(
            slow_query_iterations=args.iterations,
            lock_duration=args.duration,
            stress_duration=args.duration,
            qps=args.qps,
            tps=args.tps,
            threads=args.threads,
        )
    elif args.read:
        runner.run_read_operations()
    elif args.write:
        runner.run_write_operations()
    elif args.slow_query:
        runner.run_slow_query_scenarios(args.iterations)
    elif args.lock:
        runner.run_lock_scenarios(args.duration)
    elif args.stress:
        runner.run_performance_scenarios(
            args.qps, args.tps, args.duration, args.threads
        )
    elif args.status:
        print_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
