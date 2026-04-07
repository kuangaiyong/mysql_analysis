#!/usr/bin/env python3
"""
初始化测试数据脚本
创建测试表并插入测试数据
"""

import argparse
import random
import string
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

import pymysql

from config import add_db_args, create_connection, get_db_url


class SchemaManager:
    def __init__(self, conn: pymysql.Connection):
        self.conn = conn

    def drop_tables(self):
        tables = [
            "test_order_items",
            "test_orders",
            "test_logs",
            "test_products",
            "test_users",
            "test_large_table",
            "test_no_index_table",
        ]
        with self.conn.cursor() as cursor:
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
        self.conn.commit()

    def create_tables(self):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    status ENUM('active', 'inactive', 'pending') DEFAULT 'active',
                    score INT DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_email (email),
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    stock INT DEFAULT 0,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_category (category),
                    INDEX idx_price (price),
                    INDEX idx_stock (stock)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    status ENUM('pending', 'paid', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
                    amount DECIMAL(10, 2) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_status (status),
                    INDEX idx_created_at (created_at),
                    INDEX idx_user_status (user_id, status),
                    FOREIGN KEY (user_id) REFERENCES test_users(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_order_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    product_id INT NOT NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    INDEX idx_order_id (order_id),
                    INDEX idx_product_id (product_id),
                    INDEX idx_order_product (order_id, product_id),
                    FOREIGN KEY (order_id) REFERENCES test_orders(id),
                    FOREIGN KEY (product_id) REFERENCES test_products(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    action VARCHAR(50) NOT NULL,
                    description TEXT,
                    query_time DECIMAL(10, 6),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_user_id (user_id),
                    INDEX idx_action (action),
                    INDEX idx_created_at (created_at),
                    INDEX idx_query_time (query_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_large_table (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    value INT,
                    data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_no_index_table (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100),
                    value INT,
                    category VARCHAR(50),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

        self.conn.commit()

    def get_table_counts(self) -> Dict[str, int]:
        counts = {}
        tables = [
            "test_users",
            "test_products",
            "test_orders",
            "test_order_items",
            "test_logs",
            "test_large_table",
            "test_no_index_table",
        ]
        with self.conn.cursor() as cursor:
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                result = cursor.fetchone()
                counts[table] = result["cnt"] if result else 0
        return counts


class DataGenerator:
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
        "update_profile",
    ]
    USER_STATUSES = [
        "active",
        "active",
        "active",
        "active",
        "active",
        "active",
        "active",
        "inactive",
        "inactive",
        "pending",
    ]
    ORDER_STATUSES = [
        "pending",
        "paid",
        "paid",
        "shipped",
        "shipped",
        "delivered",
        "delivered",
        "delivered",
        "cancelled",
    ]

    def __init__(self, conn: pymysql.Connection, quick_mode: bool = False):
        self.conn = conn
        self.quick_mode = quick_mode

    def _random_string(self, length: int = 10) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _random_date(self, days_back: int = 365) -> datetime:
        delta = timedelta(
            days=random.randint(0, days_back),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        return datetime.now() - delta

    def _batch_insert(
        self,
        table: str,
        columns: List[str],
        rows: List[List[Any]],
        batch_size: int = 1000,
    ):
        if not rows:
            return
        placeholders = ", ".join(["%s"] * len(columns))
        columns_str = ", ".join(columns)
        sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

        with self.conn.cursor() as cursor:
            for i in range(0, len(rows), batch_size):
                batch = rows[i : i + batch_size]
                cursor.executemany(sql, batch)
                self.conn.commit()
                print(
                    f"  {table}: inserted {min(i + batch_size, len(rows))}/{len(rows)} rows",
                    end="\r",
                )
        print(f"  {table}: inserted {len(rows)} rows done.    ")

    def generate_users(self, count: int = 10000) -> List[int]:
        if self.quick_mode:
            count = min(count, 100)

        print(f"Generating {count} users...")
        rows = []
        user_ids = []

        for i in range(count):
            name = f"user_{self._random_string(8)}"
            email = f"{name}@example.com"
            status = random.choice(self.USER_STATUSES)
            score = random.randint(0, 1000)
            created_at = self._random_date(365)
            rows.append([name, email, status, score, created_at])
            user_ids.append(i + 1)

        self._batch_insert(
            "test_users", ["name", "email", "status", "score", "created_at"], rows
        )
        return user_ids

    def generate_products(self, count: int = 1000) -> List[int]:
        if self.quick_mode:
            count = min(count, 50)

        print(f"Generating {count} products...")
        rows = []
        product_ids = []

        for i in range(count):
            name = f"product_{self._random_string(10)}"
            category = random.choice(self.CATEGORIES)
            price = round(random.uniform(10, 10000), 2)
            stock = random.randint(0, 1000)
            description = f"Description for {name}" * random.randint(1, 5)
            rows.append([name, category, price, stock, description])
            product_ids.append(i + 1)

        self._batch_insert(
            "test_products", ["name", "category", "price", "stock", "description"], rows
        )
        return product_ids

    def generate_orders(self, user_count: int, count: int = 50000) -> List[int]:
        if self.quick_mode:
            count = min(count, 500)

        print(f"Generating {count} orders...")
        rows = []
        order_ids = []

        for i in range(count):
            user_id = random.randint(1, user_count)
            status = random.choice(self.ORDER_STATUSES)
            amount = round(random.uniform(50, 5000), 2)
            created_at = self._random_date(180)
            rows.append([user_id, status, amount, created_at])
            order_ids.append(i + 1)

        self._batch_insert(
            "test_orders", ["user_id", "status", "amount", "created_at"], rows
        )
        return order_ids

    def generate_order_items(
        self, order_count: int, product_count: int, count: int = 150000
    ):
        if self.quick_mode:
            count = min(count, 1500)

        print(f"Generating {count} order items...")
        rows = []

        for i in range(count):
            order_id = random.randint(1, order_count)
            product_id = random.randint(1, product_count)
            quantity = random.randint(1, 10)
            unit_price = round(random.uniform(10, 1000), 2)
            rows.append([order_id, product_id, quantity, unit_price])

        self._batch_insert(
            "test_order_items",
            ["order_id", "product_id", "quantity", "unit_price"],
            rows,
        )

    def generate_logs(self, user_count: int, count: int = 500000):
        if self.quick_mode:
            count = min(count, 5000)

        print(f"Generating {count} logs...")
        rows = []

        for i in range(count):
            user_id = random.randint(1, user_count) if random.random() > 0.1 else None
            action = random.choice(self.ACTIONS)
            description = f"{action} action detail: {self._random_string(50)}"
            query_time = round(random.uniform(0.001, 5.0), 6)
            created_at = self._random_date(30)
            rows.append([user_id, action, description, query_time, created_at])

        self._batch_insert(
            "test_logs",
            ["user_id", "action", "description", "query_time", "created_at"],
            rows,
        )

    def generate_large_table(self, count: int = 100000):
        if self.quick_mode:
            count = min(count, 5000)

        print(f"Generating {count} large table rows...")
        rows = []

        for i in range(count):
            name = f"item_{self._random_string(20)}"
            value = random.randint(1, 1000000)
            data = self._random_string(500)
            rows.append([name, value, data])

        self._batch_insert("test_large_table", ["name", "value", "data"], rows)

    def generate_no_index_table(self, count: int = 50000):
        if self.quick_mode:
            count = min(count, 2500)

        print(f"Generating {count} no_index table rows...")
        rows = []

        for i in range(count):
            name = f"entry_{self._random_string(15)}"
            value = random.randint(1, 100000)
            category = random.choice(self.CATEGORIES)
            rows.append([name, value, category])

        self._batch_insert("test_no_index_table", ["name", "value", "category"], rows)

    def generate_all(self, quick_mode: bool = False):
        print("\n=== Starting data generation ===\n")

        if quick_mode:
            user_count = 100
            product_count = 50
            order_count = 500
            order_item_count = 1500
            log_count = 5000
            large_table_count = 5000
            no_index_count = 2500
        else:
            user_count = 1000000
            product_count = 1000000
            order_count = 5000000
            order_item_count = 15000000
            log_count = 5000000
            large_table_count = 1000000
            no_index_count = 1000000

        self.generate_users(user_count)
        self.generate_products(product_count)
        self.generate_orders(user_count, order_count)
        self.generate_order_items(order_count, product_count, order_item_count)
        self.generate_logs(user_count, log_count)
        self.generate_large_table(large_table_count)
        self.generate_no_index_table(no_index_count)

        print("\n=== Data generation completed ===\n")


def main():
    parser = argparse.ArgumentParser(description="初始化测试数据")
    add_db_args(parser)
    parser.add_argument("--drop-existing", action="store_true", help="删除已存在的表")
    parser.add_argument(
        "--seed-only", action="store_true", help="只插入数据，假设表已存在"
    )
    parser.add_argument("--quick", action="store_true", help="快速模式，使用少量数据")
    parser.add_argument("--status", action="store_true", help="只显示当前表状态")

    args = parser.parse_args()

    print(f"连接到: {get_db_url(args)}")

    try:
        conn = create_connection(args)
        print("✓ 数据库连接成功!\n")

        schema_mgr = SchemaManager(conn)
        data_gen = DataGenerator(conn, quick_mode=args.quick)

        if args.status:
            counts = schema_mgr.get_table_counts()
            print("当前表数据量:")
            for table, count in counts.items():
                print(f"  {table}: {count:,} rows")
            conn.close()
            return

        if args.drop_existing and not args.seed_only:
            print("删除已存在的表...")
            schema_mgr.drop_tables()
            print("✓ 表删除完成\n")

        if not args.seed_only:
            print("创建表...")
            schema_mgr.create_tables()
            print("✓ 表创建完成\n")

        data_gen.generate_all(quick_mode=args.quick)

        counts = schema_mgr.get_table_counts()
        print("最终表数据量:")
        for table, count in counts.items():
            print(f"  {table}: {count:,} rows")

        conn.close()
        print("\n✓ 初始化完成!")

    except Exception as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
