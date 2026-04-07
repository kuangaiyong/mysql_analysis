"""
数据库连接配置

支持从环境变量或 .env 文件加载配置
"""

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

if HAS_DOTENV:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

DB_HOST: str = os.getenv("MYSQL_HOST", "localhost")
DB_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER: str = os.getenv("MYSQL_USER", "root")
DB_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
DB_NAME: str = os.getenv("MYSQL_DATABASE", "mysql_test")

LONG_TRANSACTION_THRESHOLD: int = 60
CRITICAL_TRANSACTION_THRESHOLD: int = 300
SLOW_QUERY_THRESHOLD: float = 1.0
HISTORY_LIST_LENGTH_WARNING: int = 100000
HISTORY_LIST_LENGTH_CRITICAL: int = 1000000

DEFAULT_TEST_DB: str = "mysql_test"

TEST_TABLES = {
    "test_users": """
        CREATE TABLE IF NOT EXISTS test_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            status ENUM('active', 'inactive', 'pending') DEFAULT 'active',
            score INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "test_orders": """
        CREATE TABLE IF NOT EXISTS test_orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            order_no VARCHAR(50) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            status ENUM('pending', 'paid', 'shipped', 'completed', 'cancelled') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_order_no (order_no),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "test_products": """
        CREATE TABLE IF NOT EXISTS test_products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            category VARCHAR(100),
            description TEXT,
            stock INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_category (category),
            INDEX idx_price (price)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "test_large_table": """
        CREATE TABLE IF NOT EXISTS test_large_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            data VARCHAR(500) NOT NULL,
            value INT DEFAULT 0,
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "test_lock_table": """
        CREATE TABLE IF NOT EXISTS test_lock_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            value INT DEFAULT 0,
            name VARCHAR(100),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
    "test_no_index_table": """
        CREATE TABLE IF NOT EXISTS test_no_index_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200),
            description TEXT,
            value INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """,
}


def get_db_config(override_db: Optional[str] = None) -> dict:
    """获取数据库连接配置"""
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": override_db or DB_NAME,
        "charset": "utf8mb4",
    }


def print_config():
    """打印当前配置"""
    print("=" * 50)
    print("数据库配置:")
    print(f"  Host: {DB_HOST}:{DB_PORT}")
    print(f"  User: {DB_USER}")
    print(f"  Database: {DB_NAME}")
    print(f"  测试库: {DEFAULT_TEST_DB}")
    print("=" * 50)


if __name__ == "__main__":
    print_config()
