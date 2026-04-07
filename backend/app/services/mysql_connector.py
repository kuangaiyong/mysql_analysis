"""
MySQL 连接器服务
"""

import pymysql
from typing import List, Dict, Any, Optional
from decimal import Decimal


def _convert_decimals(obj: Any) -> Any:
    """
    递归转换 Decimal 类型为 float
    
    Args:
        obj: 待转换的对象
    
    Returns:
        转换后的对象
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: _convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_decimals(item) for item in obj]
    return obj


class MySQLConnector:
    """MySQL数据库连接器"""

    def __init__(
        self,
        host: str,
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        """建立数据库连接"""
        self.connection = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            cursorclass=pymysql.cursors.DictCursor,
            charset="utf8mb4",
        )
        return self.connection

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """执行查询并返回结果"""
        if not self.connection:
            self.connect()

        with self.connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
        
        # 转换所有 Decimal 类型为 float
        return _convert_decimals(result)

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                connect_timeout=5,
            )
            conn.close()
            return True
        except Exception as e:
            raise Exception(f"连接测试失败: {str(e)}")

    def get_global_status(self) -> Dict[str, str]:
        """获取MySQL全局状态变量"""
        query = "SHOW GLOBAL STATUS"
        result = self.execute_query(query)
        return {row["Variable_name"]: row["Value"] for row in result}

    def get_global_variables(self) -> Dict[str, str]:
        """获取MySQL全局变量"""
        query = "SHOW GLOBAL VARIABLES"
        result = self.execute_query(query)
        return {row["Variable_name"]: row["Value"] for row in result}

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
