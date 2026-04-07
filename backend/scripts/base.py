"""
基础工具类

提供数据库连接管理、测试数据生成等功能
"""

import random
import string
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional

import pymysql
from pymysql.cursors import DictCursor

from config import (
    DEFAULT_TEST_DB,
    TEST_TABLES,
    get_db_config,
    print_config,
)


class ConnectionManager:
    """数据库连接管理器"""

    _instance: Optional["ConnectionManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections = {}
        return cls._instance

    @contextmanager
    def get_connection(
        self, database: Optional[str] = None, autocommit: bool = True
    ) -> Generator[pymysql.Connection, None, None]:
        """获取数据库连接（上下文管理器）"""
        config = get_db_config(database)
        conn = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            charset=config["charset"],
            cursorclass=DictCursor,
            autocommit=autocommit,
        )
        try:
            yield conn
        finally:
            conn.close()

    def test_connection(self, database: Optional[str] = None) -> bool:
        """测试数据库连接"""
        try:
            with self.get_connection(database) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False

    def execute(
        self,
        sql: str,
        params: Optional[tuple] = None,
        database: Optional[str] = None,
        fetch: bool = True,
    ) -> Optional[List[Dict[str, Any]]]:
        """执行SQL语句"""
        with self.get_connection(database) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                if fetch:
                    return cursor.fetchall()
                return None

    def execute_many(
        self,
        sql: str,
        params_list: List[tuple],
        database: Optional[str] = None,
    ) -> int:
        """批量执行SQL语句"""
        with self.get_connection(database) as conn:
            with conn.cursor() as cursor:
                affected = cursor.executemany(sql, params_list)
                return affected


class TestDatabase:
    """测试数据库管理"""

    def __init__(self):
        self.conn_mgr = ConnectionManager()

    def create_test_database(self, db_name: str = DEFAULT_TEST_DB) -> bool:
        """创建测试数据库"""
        try:
            with self.conn_mgr.get_connection(None) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARSET utf8mb4")
                    cursor.execute(f"USE `{db_name}`")
            print(f"✓ 测试数据库 '{db_name}' 创建成功")
            return True
        except Exception as e:
            print(f"✗ 创建测试数据库失败: {e}")
            return False

    def drop_test_database(self, db_name: str = DEFAULT_TEST_DB) -> bool:
        """删除测试数据库"""
        try:
            with self.conn_mgr.get_connection(None) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
            print(f"✓ 测试数据库 '{db_name}' 已删除")
            return True
        except Exception as e:
            print(f"✗ 删除测试数据库失败: {e}")
            return False

    def create_test_tables(self, db_name: str = DEFAULT_TEST_DB) -> bool:
        """创建测试表"""
        try:
            with self.conn_mgr.get_connection(db_name) as conn:
                with conn.cursor() as cursor:
                    for table_name, create_sql in TEST_TABLES.items():
                        cursor.execute(create_sql)
                        print(f"  ✓ 表 '{table_name}' 创建成功")
            print(f"✓ 所有测试表创建完成")
            return True
        except Exception as e:
            print(f"✗ 创建测试表失败: {e}")
            return False

    def cleanup_test_data(self, db_name: str = DEFAULT_TEST_DB) -> bool:
        """清理测试数据"""
        try:
            with self.conn_mgr.get_connection(db_name) as conn:
                with conn.cursor() as cursor:
                    for table_name in TEST_TABLES.keys():
                        cursor.execute(f"TRUNCATE TABLE `{table_name}`")
                        print(f"  ✓ 表 '{table_name}' 数据已清理")
            print(f"✓ 所有测试数据清理完成")
            return True
        except Exception as e:
            print(f"✗ 清理测试数据失败: {e}")
            return False

    def init_test_environment(self, db_name: str = DEFAULT_TEST_DB) -> bool:
        """初始化测试环境（创建数据库和表）"""
        print(f"\n初始化测试环境...")
        if not self.create_test_database(db_name):
            return False
        if not self.create_test_tables(db_name):
            return False
        print(f"✓ 测试环境初始化完成\n")
        return True

    def destroy_test_environment(self, db_name: str = DEFAULT_TEST_DB) -> bool:
        """销毁测试环境（删除整个数据库）"""
        print(f"\n销毁测试环境...")
        return self.drop_test_database(db_name)


class DataGenerator:
    """测试数据生成器"""

    def __init__(self, db_name: str = DEFAULT_TEST_DB):
        self.conn_mgr = ConnectionManager()
        self.db_name = db_name

    def _random_string(self, length: int = 10) -> str:
        """生成随机字符串"""
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _random_email(self) -> str:
        """生成随机邮箱"""
        domains = ["gmail.com", "yahoo.com", "outlook.com", "qq.com", "163.com"]
        return f"{self._random_string(8).lower()}@{random.choice(domains)}"

    def _random_name(self) -> str:
        """生成随机姓名"""
        first_names = [
            "张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴",
            "John", "Jane", "Mike", "Emily", "David", "Sarah", "Tom", "Lisa"
        ]
        last_names = [
            "伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军",
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis"
        ]
        return f"{random.choice(first_names)}{random.choice(last_names)}"

    def generate_users(self, count: int = 10000, batch_size: int = 1000) -> int:
        """生成用户数据"""
        print(f"生成 {count} 条用户数据...")
        total = 0
        statuses = ["active", "inactive", "pending"]

        for i in range(0, count, batch_size):
            batch_count = min(batch_size, count - i)
            users = []
            for _ in range(batch_count):
                users.append(
                    (
                        self._random_name(),
                        self._random_email(),
                        random.choice(statuses),
                        random.randint(0, 1000),
                    )
                )

            sql = """
                INSERT INTO test_users (name, email, status, score)
                VALUES (%s, %s, %s, %s)
            """
            affected = self.conn_mgr.execute_many(sql, users, self.db_name)
            total += affected
            print(f"  已插入 {total}/{count} 条用户数据", end="\r")

        print(f"\n✓ 用户数据生成完成: {total} 条")
        return total

    def generate_orders(self, count: int = 50000, batch_size: int = 1000, max_user_id: int = 10000) -> int:
        """生成订单数据"""
        print(f"生成 {count} 条订单数据...")
        total = 0
        statuses = ["pending", "paid", "shipped", "completed", "cancelled"]

        for i in range(0, count, batch_size):
            batch_count = min(batch_size, count - i)
            orders = []
            base_time = datetime.now() - timedelta(days=random.randint(0, 365))

            for j in range(batch_count):
                user_id = random.randint(1, max_user_id)
                order_no = f"ORD{int(time.time() * 1000)}{random.randint(1000, 9999)}"
                amount = round(random.uniform(10, 10000), 2)
                status = random.choice(statuses)
                orders.append((user_id, order_no, amount, status))

            sql = """
                INSERT INTO test_orders (user_id, order_no, amount, status)
                VALUES (%s, %s, %s, %s)
            """
            affected = self.conn_mgr.execute_many(sql, orders, self.db_name)
            total += affected
            print(f"  已插入 {total}/{count} 条订单数据", end="\r")

        print(f"\n✓ 订单数据生成完成: {total} 条")
        return total

    def generate_products(self, count: int = 1000, batch_size: int = 500) -> int:
        """生成产品数据"""
        print(f"生成 {count} 条产品数据...")
        total = 0
        categories = ["电子产品", "服装", "食品", "家居", "图书", "运动", "美妆", "汽车"]

        for i in range(0, count, batch_size):
            batch_count = min(batch_size, count - i)
            products = []
            for _ in range(batch_count):
                name = f"产品_{self._random_string(8)}"
                price = round(random.uniform(1, 9999), 2)
                category = random.choice(categories)
                description = self._random_string(200)
                stock = random.randint(0, 10000)
                products.append((name, price, category, description, stock))

            sql = """
                INSERT INTO test_products (name, price, category, description, stock)
                VALUES (%s, %s, %s, %s, %s)
            """
            affected = self.conn_mgr.execute_many(sql, products, self.db_name)
            total += affected
            print(f"  已插入 {total}/{count} 条产品数据", end="\r")

        print(f"\n✓ 产品数据生成完成: {total} 条")
        return total

    def generate_large_table(self, rows: int = 100000, batch_size: int = 5000) -> int:
        """生成大表数据（用于全表扫描测试）"""
        print(f"生成 {rows} 条大表数据...")
        total = 0
        categories = ["A", "B", "C", "D", "E"]

        for i in range(0, rows, batch_size):
            batch_count = min(batch_size, rows - i)
            data_rows = []
            for _ in range(batch_count):
                data = self._random_string(random.randint(100, 500))
                value = random.randint(1, 1000000)
                category = random.choice(categories)
                data_rows.append((data, value, category))

            sql = """
                INSERT INTO test_large_table (data, value, category)
                VALUES (%s, %s, %s)
            """
            affected = self.conn_mgr.execute_many(sql, data_rows, self.db_name)
            total += affected
            print(f"  已插入 {total}/{rows} 条大表数据", end="\r")

        print(f"\n✓ 大表数据生成完成: {total} 条")
        return total

    def generate_lock_test_data(self, rows: int = 100) -> int:
        """生成锁测试数据"""
        print(f"生成 {rows} 条锁测试数据...")
        data_rows = [(i, f"lock_test_{i}") for i in range(1, rows + 1)]
        sql = """
            INSERT INTO test_lock_table (value, name)
            VALUES (%s, %s)
        """
        affected = self.conn_mgr.execute_many(sql, data_rows, self.db_name)
        print(f"✓ 锁测试数据生成完成: {affected} 条")
        return affected

    def generate_no_index_data(self, rows: int = 50000, batch_size: int = 5000) -> int:
        """生成无索引表数据（用于慢查询测试）"""
        print(f"生成 {rows} 条无索引表数据...")
        total = 0

        for i in range(0, rows, batch_size):
            batch_count = min(batch_size, rows - i)
            data_rows = []
            for _ in range(batch_count):
                name = self._random_name()
                description = self._random_string(random.randint(50, 200))
                value = random.randint(1, 100000)
                data_rows.append((name, description, value))

            sql = """
                INSERT INTO test_no_index_table (name, description, value)
                VALUES (%s, %s, %s)
            """
            affected = self.conn_mgr.execute_many(sql, data_rows, self.db_name)
            total += affected
            print(f"  已插入 {total}/{rows} 条无索引表数据", end="\r")

        print(f"\n✓ 无索引表数据生成完成: {total} 条")
        return total

    def generate_all_test_data(
        self,
        users: int = 10000,
        orders: int = 50000,
        products: int = 1000,
        large_table: int = 100000,
        lock_data: int = 100,
        no_index_data: int = 50000,
    ) -> Dict[str, int]:
        """生成所有测试数据"""
        print("\n" + "=" * 50)
        print("开始生成测试数据...")
        print("=" * 50)

        results = {}
        results["users"] = self.generate_users(users)
        results["orders"] = self.generate_orders(orders, max_user_id=users)
        results["products"] = self.generate_products(products)
        results["large_table"] = self.generate_large_table(large_table)
        results["lock_data"] = self.generate_lock_test_data(lock_data)
        results["no_index_data"] = self.generate_no_index_data(no_index_data)

        print("\n" + "=" * 50)
        print("测试数据生成完成!")
        print("=" * 50)
        return results


def get_table_row_count(table_name: str, db_name: str = DEFAULT_TEST_DB) -> int:
    """获取表行数"""
    conn_mgr = ConnectionManager()
    result = conn_mgr.execute(f"SELECT COUNT(*) as cnt FROM `{table_name}`", database=db_name)
    if result:
        return result[0]["cnt"]
    return 0


def get_all_table_counts(db_name: str = DEFAULT_TEST_DB) -> Dict[str, int]:
    """获取所有测试表的行数"""
    counts = {}
    for table_name in TEST_TABLES.keys():
        counts[table_name] = get_table_row_count(table_name, db_name)
    return counts


def print_status(db_name: str = DEFAULT_TEST_DB):
    """打印测试环境状态"""
    print("\n" + "=" * 60)
    print("测试环境状态")
    print("=" * 60)

    conn_mgr = ConnectionManager()
    if not conn_mgr.test_connection(db_name):
        print(f"数据库 '{db_name}' 不存在或无法连接")
        return

    print(f"数据库: {db_name}")
    print("-" * 60)

    counts = get_all_table_counts(db_name)
    for table_name, count in counts.items():
        print(f"  {table_name}: {count:,} 行")

    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MySQL测试基础工具")
    parser.add_argument("--init", action="store_true", help="初始化测试环境")
    parser.add_argument("--destroy", action="store_true", help="销毁测试环境")
    parser.add_argument("--generate-data", action="store_true", help="生成测试数据")
    parser.add_argument("--cleanup", action="store_true", help="清理测试数据")
    parser.add_argument("--status", action="store_true", help="查看测试环境状态")
    parser.add_argument("--config", action="store_true", help="显示配置信息")

    args = parser.parse_args()

    if args.config:
        print_config()
    elif args.init:
        db = TestDatabase()
        db.init_test_environment()
    elif args.destroy:
        db = TestDatabase()
        db.destroy_test_environment()
    elif args.generate_data:
        generator = DataGenerator()
        generator.generate_all_test_data()
    elif args.cleanup:
        db = TestDatabase()
        db.cleanup_test_data()
    elif args.status:
        print_status()
    else:
        parser.print_help()
