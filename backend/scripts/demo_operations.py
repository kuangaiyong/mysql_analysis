"""
mysql_demo 数据库读写操作脚本

用于验证MySQL性能诊断系统的核心场景
执行基础的CRUD操作：创建表、插入数据、查询、更新、删除
"""

import random
import string
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

import pymysql
from pymysql.cursors import DictCursor

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_db_config, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD

# 目标数据库名称
DEMO_DB = "mysql_demo"

# Demo表定义
DEMO_TABLES = {
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL,
            age INT,
            status ENUM('active', 'inactive', 'banned') DEFAULT 'active',
            balance DECIMAL(10, 2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='用户表'
    """,
    "products": """
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            price DECIMAL(10, 2) NOT NULL,
            stock INT DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_category (category),
            INDEX idx_price (price)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='商品表'
    """,
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            total_amount DECIMAL(10, 2) NOT NULL,
            status ENUM('pending', 'paid', 'shipped', 'completed', 'cancelled') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_product_id (product_id),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='订单表'
    """,
    "logs": """
        CREATE TABLE IF NOT EXISTS logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR') DEFAULT 'INFO',
            message TEXT,
            source VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_level (level),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='日志表'
    """,
    "large_data": """
        CREATE TABLE IF NOT EXISTS large_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data VARCHAR(500) NOT NULL,
            value INT DEFAULT 0,
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_category (category)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='大数据表-全表扫描测试'
    """,
    "lock_test": """
        CREATE TABLE IF NOT EXISTS lock_test (
            id INT AUTO_INCREMENT PRIMARY KEY,
            value INT DEFAULT 0,
            name VARCHAR(100),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='锁测试表'
    """,
    "no_index_data": """
        CREATE TABLE IF NOT EXISTS no_index_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200),
            description TEXT,
            value INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COMMENT='无索引表-JOIN测试'
    """,
}


class DemoDatabase:
    """mysql_demo 数据库管理"""

    def __init__(self):
        self._connections = {}

    @contextmanager
    def get_connection(
        self, database: Optional[str] = None, autocommit: bool = True
    ) -> Generator[pymysql.Connection, None, None]:
        """获取数据库连接"""
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

    def test_connection(self) -> bool:
        """测试MySQL连接"""
        try:
            with self.get_connection(None) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            print(f"✓ MySQL连接成功 ({DB_HOST}:{DB_PORT})")
            return True
        except Exception as e:
            print(f"✗ MySQL连接失败: {e}")
            return False

    def create_database(self) -> bool:
        """创建demo数据库"""
        try:
            with self.get_connection(None) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"CREATE DATABASE IF NOT EXISTS `{DEMO_DB}` DEFAULT CHARSET utf8mb4"
                    )
            print(f"✓ 数据库 '{DEMO_DB}' 创建成功")
            return True
        except Exception as e:
            print(f"✗ 创建数据库失败: {e}")
            return False

    def drop_database(self) -> bool:
        """删除demo数据库"""
        try:
            with self.get_connection(None) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"DROP DATABASE IF EXISTS `{DEMO_DB}`")
            print(f"✓ 数据库 '{DEMO_DB}' 已删除")
            return True
        except Exception as e:
            print(f"✗ 删除数据库失败: {e}")
            return False

    def create_tables(self) -> bool:
        """创建所有表"""
        try:
            with self.get_connection(DEMO_DB) as conn:
                with conn.cursor() as cursor:
                    for table_name, create_sql in DEMO_TABLES.items():
                        cursor.execute(create_sql)
                        print(f"  ✓ 表 '{table_name}' 创建成功")
            print(f"✓ 所有表创建完成")
            return True
        except Exception as e:
            print(f"✗ 创建表失败: {e}")
            return False

    def init_database(self) -> bool:
        """初始化数据库（创建数据库和表）"""
        print(f"\n{'=' * 50}")
        print(f"初始化 mysql_demo 数据库")
        print(f"{'=' * 50}")

        if not self.test_connection():
            return False
        if not self.create_database():
            return False
        if not self.create_tables():
            return False

        print(f"\n✓ 初始化完成!")
        return True

    def get_table_counts(self) -> Dict[str, int]:
        """获取所有表的行数"""
        counts = {}
        with self.get_connection(DEMO_DB) as conn:
            with conn.cursor() as cursor:
                for table_name in DEMO_TABLES.keys():
                    cursor.execute(f"SELECT COUNT(*) as cnt FROM `{table_name}`")
                    counts[table_name] = cursor.fetchone()["cnt"]
        return counts


class DemoDataGenerator:
    """Demo数据生成器"""

    def __init__(self):
        self.db = DemoDatabase()

    def _random_string(self, length: int = 10) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _random_name(self) -> str:
        first_names = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
        last_names = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军"]
        return f"{random.choice(first_names)}{random.choice(last_names)}"

    def generate_users(self, count: int = 100) -> int:
        """生成用户数据"""
        print(f"\n生成 {count} 条用户数据...")

        with self.db.get_connection(DEMO_DB) as conn:
            with conn.cursor() as cursor:
                for i in range(count):
                    username = f"user_{self._random_string(8)}"
                    email = f"{self._random_string(6)}@example.com"
                    age = random.randint(18, 70)
                    status = random.choice(["active", "inactive", "banned"])
                    balance = round(random.uniform(0, 10000), 2)

                    cursor.execute(
                        """
                        INSERT INTO users (username, email, age, status, balance)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (username, email, age, status, balance),
                    )

                    if (i + 1) % 50 == 0:
                        print(f"  已插入 {i + 1}/{count} 条", end="\r")

        print(f"\n✓ 用户数据生成完成: {count} 条")
        return count

    def generate_products(self, count: int = 50) -> int:
        """生成商品数据"""
        print(f"\n生成 {count} 条商品数据...")

        categories = [
            "电子产品",
            "服装",
            "食品",
            "家居",
            "图书",
            "运动",
            "美妆",
            "汽车",
        ]

        with self.db.get_connection(DEMO_DB) as conn:
            with conn.cursor() as cursor:
                for i in range(count):
                    name = f"商品_{self._random_string(6)}"
                    category = random.choice(categories)
                    price = round(random.uniform(1, 9999), 2)
                    stock = random.randint(0, 1000)
                    description = f"这是{category}类商品描述: {self._random_string(50)}"

                    cursor.execute(
                        """
                        INSERT INTO products (name, category, price, stock, description)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (name, category, price, stock, description),
                    )

                    if (i + 1) % 20 == 0:
                        print(f"  已插入 {i + 1}/{count} 条", end="\r")

        print(f"\n✓ 商品数据生成完成: {count} 条")
        return count

    def generate_orders(self, count: int = 200) -> int:
        """生成订单数据"""
        print(f"\n生成 {count} 条订单数据...")

        with self.db.get_connection(DEMO_DB) as conn:
            with conn.cursor() as cursor:
                # 获取用户和商品ID范围
                cursor.execute("SELECT MIN(id), MAX(id) FROM users")
                user_range = cursor.fetchone()
                cursor.execute("SELECT MIN(id), MAX(id) FROM products")
                product_range = cursor.fetchone()

                user_min, user_max = (
                    user_range["MIN(id)"] or 1,
                    user_range["MAX(id)"] or 1,
                )
                product_min, product_max = (
                    product_range["MIN(id)"] or 1,
                    product_range["MAX(id)"] or 1,
                )

                for i in range(count):
                    user_id = random.randint(user_min, user_max)
                    product_id = random.randint(product_min, product_max)
                    quantity = random.randint(1, 5)
                    # 根据商品价格计算总金额（这里简化处理）
                    total_amount = round(random.uniform(10, 5000) * quantity, 2)
                    status = random.choice(
                        ["pending", "paid", "shipped", "completed", "cancelled"]
                    )

                    cursor.execute(
                        """
                        INSERT INTO orders (user_id, product_id, quantity, total_amount, status)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (user_id, product_id, quantity, total_amount, status),
                    )

                    if (i + 1) % 50 == 0:
                        print(f"  已插入 {i + 1}/{count} 条", end="\r")

        print(f"\n✓ 订单数据生成完成: {count} 条")
        return count

    def generate_logs(self, count: int = 100) -> int:
        """生成日志数据"""
        print(f"\n生成 {count} 条日志数据...")

        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        sources = ["api", "scheduler", "worker", "web", "batch"]
        messages = [
            "用户登录成功",
            "订单创建完成",
            "数据库查询超时",
            "缓存未命中",
            "支付回调处理中",
            "库存同步完成",
            "邮件发送成功",
            "定时任务执行",
        ]

        with self.db.get_connection(DEMO_DB) as conn:
            with conn.cursor() as cursor:
                for i in range(count):
                    level = random.choice(levels)
                    source = random.choice(sources)
                    message = f"[{source}] {random.choice(messages)} - {self._random_string(20)}"

                    cursor.execute(
                        """
                        INSERT INTO logs (level, message, source)
                        VALUES (%s, %s, %s)
                        """,
                        (level, message, source),
                    )

                    if (i + 1) % 50 == 0:
                        print(f"  已插入 {i + 1}/{count} 条", end="\r")

        print(f"\n✓ 日志数据生成完成: {count} 条")
        return count

    def generate_large_data(self, count: int = 10000, batch_size: int = 1000) -> int:
        """生成大数据表数据（用于全表扫描测试）"""
        print(f"\n生成 {count} 条大数据表数据...")
        total = 0
        categories = ["A", "B", "C", "D", "E"]

        with self.db.get_connection(DEMO_DB) as conn:
            with conn.cursor() as cursor:
                for i in range(0, count, batch_size):
                    batch_count = min(batch_size, count - i)
                    data_rows = []
                    for _ in range(batch_count):
                        data = self._random_string(random.randint(100, 500))
                        value = random.randint(1, 1000000)
                        category = random.choice(categories)
                        data_rows.append((data, value, category))

                    cursor.executemany(
                        "INSERT INTO large_data (data, value, category) VALUES (%s, %s, %s)",
                        data_rows,
                    )
                    total += batch_count
                    print(f"  已插入 {total}/{count} 条", end="\r")

        print(f"\n✓ 大数据表数据生成完成: {count} 条")
        return count

    def generate_lock_test_data(self, count: int = 100) -> int:
        """生成锁测试数据"""
        print(f"\n生成 {count} 条锁测试数据...")

        with self.db.get_connection(DEMO_DB) as conn:
            with conn.cursor() as cursor:
                data_rows = [(i, f"lock_test_{i}") for i in range(1, count + 1)]
                cursor.executemany(
                    "INSERT INTO lock_test (value, name) VALUES (%s, %s)", data_rows
                )

        print(f"✓ 锁测试数据生成完成: {count} 条")
        return count

    def generate_no_index_data(self, count: int = 10000, batch_size: int = 1000) -> int:
        """生成无索引表数据（用于慢查询测试）"""
        print(f"\n生成 {count} 条无索引表数据...")
        total = 0

        with self.db.get_connection(DEMO_DB) as conn:
            with conn.cursor() as cursor:
                for i in range(0, count, batch_size):
                    batch_count = min(batch_size, count - i)
                    data_rows = []
                    for _ in range(batch_count):
                        name = self._random_name()
                        description = self._random_string(random.randint(50, 200))
                        value = random.randint(1, 100000)
                        data_rows.append((name, description, value))

                    cursor.executemany(
                        "INSERT INTO no_index_data (name, description, value) VALUES (%s, %s, %s)",
                        data_rows,
                    )
                    total += batch_count
                    print(f"  已插入 {total}/{count} 条", end="\r")

        print(f"\n✓ 无索引表数据生成完成: {count} 条")
        return count

    def generate_all(
        self,
        users: int = 100,
        products: int = 50,
        orders: int = 200,
        logs: int = 100,
        large_data: int = 10000,
        lock_test: int = 100,
        no_index_data: int = 10000,
    ) -> Dict[str, int]:
        """生成所有测试数据"""
        print(f"\n{'=' * 50}")
        print(f"开始生成测试数据")
        print(f"{'=' * 50}")

        results = {}
        results["users"] = self.generate_users(users)
        results["products"] = self.generate_products(products)
        results["orders"] = self.generate_orders(orders)
        results["logs"] = self.generate_logs(logs)
        results["large_data"] = self.generate_large_data(large_data)
        results["lock_test"] = self.generate_lock_test_data(lock_test)
        results["no_index_data"] = self.generate_no_index_data(no_index_data)

        print(f"\n{'=' * 50}")
        print(f"测试数据生成完成!")
        print(f"{'=' * 50}")
        return results


class DemoOperations:
    """Demo读写操作"""

    def __init__(self):
        self.db = DemoDatabase()

    def read_operations(self) -> Dict[str, Any]:
        """执行各种读操作"""
        print(f"\n{'=' * 50}")
        print(f"执行读操作")
        print(f"{'=' * 50}")

        results = {}

        with self.db.get_connection(DEMO_DB) as conn:
            with conn.cursor() as cursor:
                # 1. 简单查询 - 统计各表数据量
                print("\n1. 统计各表数据量:")
                for table in DEMO_TABLES.keys():
                    cursor.execute(f"SELECT COUNT(*) as cnt FROM `{table}`")
                    count = cursor.fetchone()["cnt"]
                    print(f"   {table}: {count} 行")
                    results[f"{table}_count"] = count

                # 2. 条件查询 - 活跃用户
                print("\n2. 条件查询 - 活跃用户:")
                cursor.execute("SELECT * FROM users WHERE status = 'active' LIMIT 5")
                active_users = cursor.fetchall()
                for user in active_users:
                    print(
                        f"   ID={user['id']}, username={user['username']}, balance={user['balance']}"
                    )
                results["active_users"] = len(active_users)

                # 3. 排序查询 - 余额最高的用户
                print("\n3. 排序查询 - 余额最高的5个用户:")
                cursor.execute(
                    "SELECT id, username, balance FROM users ORDER BY balance DESC LIMIT 5"
                )
                top_users = cursor.fetchall()
                for user in top_users:
                    print(
                        f"   ID={user['id']}, username={user['username']}, balance={user['balance']}"
                    )
                results["top_users"] = len(top_users)

                # 4. 聚合查询 - 订单统计
                print("\n4. 聚合查询 - 订单状态分布:")
                cursor.execute("""
                    SELECT status, COUNT(*) as cnt, SUM(total_amount) as total
                    FROM orders GROUP BY status ORDER BY cnt DESC
                """)
                order_stats = cursor.fetchall()
                for stat in order_stats:
                    print(
                        f"   {stat['status']}: {stat['cnt']} 单, 总金额 {stat['total']}"
                    )
                results["order_stats"] = order_stats

                # 5. JOIN查询 - 用户订单详情
                print("\n5. JOIN查询 - 用户订单详情 (前5条):")
                cursor.execute("""
                    SELECT u.username, o.total_amount, o.status, o.created_at
                    FROM orders o
                    JOIN users u ON o.user_id = u.id
                    ORDER BY o.created_at DESC
                    LIMIT 5
                """)
                user_orders = cursor.fetchall()
                for order in user_orders:
                    print(
                        f"   用户: {order['username']}, 金额: {order['total_amount']}, 状态: {order['status']}"
                    )
                results["user_orders"] = len(user_orders)

                # 6. 分组统计 - 商品销量
                print("\n6. 分组统计 - 商品销量TOP5:")
                cursor.execute("""
                    SELECT p.name, p.category, SUM(o.quantity) as total_qty
                    FROM orders o
                    JOIN products p ON o.product_id = p.id
                    GROUP BY p.id
                    ORDER BY total_qty DESC
                    LIMIT 5
                """)
                product_sales = cursor.fetchall()
                for prod in product_sales:
                    print(
                        f"   {prod['name']} ({prod['category']}): 销量 {prod['total_qty']}"
                    )
                results["product_sales"] = len(product_sales)

                # 7. 日志级别统计
                print("\n7. 日志级别统计:")
                cursor.execute("""
                    SELECT level, COUNT(*) as cnt
                    FROM logs GROUP BY level ORDER BY cnt DESC
                """)
                log_stats = cursor.fetchall()
                for stat in log_stats:
                    print(f"   {stat['level']}: {stat['cnt']} 条")
                results["log_stats"] = log_stats

        print(f"\n✓ 读操作完成")
        return results

    def write_operations(self) -> Dict[str, Any]:
        """执行各种写操作"""
        print(f"\n{'=' * 50}")
        print(f"执行写操作")
        print(f"{'=' * 50}")

        results = {}

        with self.db.get_connection(DEMO_DB, autocommit=False) as conn:
            with conn.cursor() as cursor:
                # 1. INSERT - 新增用户
                print("\n1. INSERT - 新增用户:")
                cursor.execute(
                    "INSERT INTO users (username, email, age, status, balance) VALUES (%s, %s, %s, %s, %s)",
                    (
                        f"new_user_{int(time.time())}",
                        f"new_{int(time.time())}@test.com",
                        25,
                        "active",
                        100.00,
                    ),
                )
                new_user_id = cursor.lastrowid
                print(f"   新增用户ID: {new_user_id}")
                results["new_user_id"] = new_user_id

                # 2. UPDATE - 更新余额
                print("\n2. UPDATE - 更新用户余额:")
                cursor.execute(
                    "UPDATE users SET balance = balance + 50 WHERE id = %s",
                    (new_user_id,),
                )
                print(f"   用户 {new_user_id} 余额增加50")
                results["updated_rows"] = cursor.rowcount

                # 3. INSERT - 新增订单
                print("\n3. INSERT - 新增订单:")
                cursor.execute(
                    "INSERT INTO orders (user_id, product_id, quantity, total_amount, status) VALUES (%s, %s, %s, %s, %s)",
                    (new_user_id, 1, 2, 199.99, "pending"),
                )
                new_order_id = cursor.lastrowid
                print(f"   新增订单ID: {new_order_id}")
                results["new_order_id"] = new_order_id

                # 4. UPDATE - 更新订单状态
                print("\n4. UPDATE - 更新订单状态:")
                cursor.execute(
                    "UPDATE orders SET status = 'paid' WHERE id = %s", (new_order_id,)
                )
                print(f"   订单 {new_order_id} 状态更新为 paid")

                # 5. INSERT - 记录日志
                print("\n5. INSERT - 记录操作日志:")
                cursor.execute(
                    "INSERT INTO logs (level, message, source) VALUES (%s, %s, %s)",
                    ("INFO", f"用户 {new_user_id} 下单成功", "api"),
                )
                print(f"   操作日志已记录")

                # 6. 批量INSERT
                print("\n6. 批量INSERT - 插入多条日志:")
                logs_data = [
                    ("DEBUG", "批量插入测试1", "batch"),
                    ("DEBUG", "批量插入测试2", "batch"),
                    ("INFO", "批量插入测试3", "batch"),
                ]
                cursor.executemany(
                    "INSERT INTO logs (level, message, source) VALUES (%s, %s, %s)",
                    logs_data,
                )
                print(f"   批量插入 {len(logs_data)} 条日志")
                results["batch_insert"] = len(logs_data)

                # 7. DELETE - 删除测试数据
                print("\n7. DELETE - 删除测试日志:")
                cursor.execute("DELETE FROM logs WHERE source = 'batch'")
                print(f"   删除 {cursor.rowcount} 条测试日志")
                results["deleted_rows"] = cursor.rowcount

                # 提交事务
                conn.commit()
                print(f"\n✓ 所有写操作已提交")

        return results

    def transaction_demo(self) -> bool:
        """事务演示 - 模拟转账场景"""
        print(f"\n{'=' * 50}")
        print(f"事务演示 - 模拟转账")
        print(f"{'=' * 50}")

        with self.db.get_connection(DEMO_DB, autocommit=False) as conn:
            with conn.cursor() as cursor:
                try:
                    # 获取两个用户
                    cursor.execute(
                        "SELECT id, username, balance FROM users WHERE status = 'active' LIMIT 2"
                    )
                    users = cursor.fetchall()

                    if len(users) < 2:
                        print("   用户数量不足，跳过转账演示")
                        return False

                    from_user = users[0]
                    to_user = users[1]
                    amount = 100.00

                    print(
                        f"\n   转出用户: {from_user['username']} (余额: {from_user['balance']})"
                    )
                    print(
                        f"   转入用户: {to_user['username']} (余额: {to_user['balance']})"
                    )
                    print(f"   转账金额: {amount}")

                    # 扣减余额
                    cursor.execute(
                        "UPDATE users SET balance = balance - %s WHERE id = %s",
                        (amount, from_user["id"]),
                    )
                    print(f"   ✓ 扣减 {from_user['username']} 余额 {amount}")

                    # 增加余额
                    cursor.execute(
                        "UPDATE users SET balance = balance + %s WHERE id = %s",
                        (amount, to_user["id"]),
                    )
                    print(f"   ✓ 增加 {to_user['username']} 余额 {amount}")

                    # 记录日志
                    cursor.execute(
                        "INSERT INTO logs (level, message, source) VALUES (%s, %s, %s)",
                        (
                            "INFO",
                            f"转账: {from_user['username']} -> {to_user['username']} 金额: {amount}",
                            "transaction",
                        ),
                    )
                    print(f"   ✓ 记录转账日志")

                    # 提交事务
                    conn.commit()
                    print(f"\n✓ 转账成功，事务已提交")
                    return True

                except Exception as e:
                    conn.rollback()
                    print(f"\n✗ 转账失败，事务已回滚: {e}")
                    return False

    def run_all_operations(self) -> Dict[str, Any]:
        """执行所有读写操作"""
        print(f"\n{'=' * 60}")
        print(f"mysql_demo 数据库读写操作演示")
        print(f"{'=' * 60}")

        results = {}
        results["read"] = self.read_operations()
        results["write"] = self.write_operations()
        results["transaction"] = self.transaction_demo()

        print(f"\n{'=' * 60}")
        print(f"所有操作完成!")
        print(f"{'=' * 60}")

        return results


def print_status():
    """打印数据库状态"""
    print(f"\n{'=' * 50}")
    print(f"mysql_demo 数据库状态")
    print(f"{'=' * 50}")

    db = DemoDatabase()

    if not db.test_connection():
        return

    try:
        counts = db.get_table_counts()
        print(f"\n数据表统计:")
        for table, count in counts.items():
            print(f"  {table}: {count:,} 行")
    except Exception as e:
        print(f"  无法获取表统计: {e}")

    print(f"{'=' * 50}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="mysql_demo 数据库读写操作脚本")
    parser.add_argument(
        "--init", action="store_true", help="初始化数据库（创建数据库和表）"
    )
    parser.add_argument("--drop", action="store_true", help="删除数据库")
    parser.add_argument("--generate", action="store_true", help="生成测试数据")
    parser.add_argument("--users", type=int, default=100, help="用户数据数量")
    parser.add_argument("--products", type=int, default=50, help="商品数据数量")
    parser.add_argument("--orders", type=int, default=200, help="订单数据数量")
    parser.add_argument("--logs", type=int, default=100, help="日志数据数量")
    parser.add_argument(
        "--large-data", type=int, default=10000, help="大数据表数据数量"
    )
    parser.add_argument("--lock-test", type=int, default=100, help="锁测试数据数量")
    parser.add_argument("--no-index", type=int, default=10000, help="无索引表数据数量")
    parser.add_argument("--read", action="store_true", help="执行读操作")
    parser.add_argument("--write", action="store_true", help="执行写操作")
    parser.add_argument("--all", action="store_true", help="执行所有读写操作")
    parser.add_argument("--status", action="store_true", help="查看数据库状态")
    parser.add_argument(
        "--full", action="store_true", help="完整演示（初始化+生成数据+读写操作）"
    )

    args = parser.parse_args()

    if args.full:
        # 完整演示
        db = DemoDatabase()
        if db.init_database():
            generator = DemoDataGenerator()
            generator.generate_all(
                args.users,
                args.products,
                args.orders,
                args.logs,
                args.large_data,
                args.lock_test,
                args.no_index,
            )
            operations = DemoOperations()
            operations.run_all_operations()
            print_status()
    elif args.init:
        db = DemoDatabase()
        db.init_database()
    elif args.drop:
        db = DemoDatabase()
        db.drop_database()
    elif args.generate:
        generator = DemoDataGenerator()
        generator.generate_all(
            args.users,
            args.products,
            args.orders,
            args.logs,
            args.large_data,
            args.lock_test,
            args.no_index,
        )
    elif args.read:
        operations = DemoOperations()
        operations.read_operations()
    elif args.write:
        operations = DemoOperations()
        operations.write_operations()
    elif args.all:
        operations = DemoOperations()
        operations.run_all_operations()
    elif args.status:
        print_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
