"""
慢查询场景脚本

产生能被performance_schema记录的慢查询（>1秒）
验证系统慢查询分析功能
"""

import random
import time
from typing import Dict, List, Optional

import pymysql
from pymysql.cursors import DictCursor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEFAULT_TEST_DB, get_db_config, SLOW_QUERY_THRESHOLD
from base import ConnectionManager


class SlowQueryScenarios:
    """慢查询场景生成器"""

    def __init__(self, db_name: str = DEFAULT_TEST_DB):
        self.db_name = db_name
        self.conn_mgr = ConnectionManager()

    def _get_connection(self) -> pymysql.Connection:
        """获取新连接"""
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

    def generate_full_table_scan(self, iterations: int = 5) -> Dict[str, any]:
        """
        生成全表扫描慢查询
        
        EXPLAIN特征: type=ALL
        
        Args:
            iterations: 执行次数
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成全表扫描慢查询: {iterations} 次")
        print(f"{'='*60}")
        
        results = []
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(iterations):
                    start = time.time()
                    
                    cursor.execute("""
                        SELECT SQL_NO_CACHE * 
                        FROM test_large_table 
                        WHERE data LIKE CONCAT('%', %s, '%')
                        ORDER BY id
                        LIMIT 1000
                    """, (str(random.randint(0, 999)),))
                    
                    rows = cursor.fetchall()
                    elapsed = time.time() - start
                    results.append({
                        "iteration": i + 1,
                        "rows": len(rows),
                        "time": elapsed,
                    })
                    print(f"  第 {i+1}/{iterations} 次: 扫描完成, 返回 {len(rows)} 行, 耗时 {elapsed:.2f}秒")
                    
                    time.sleep(0.5)
        
        avg_time = sum(r["time"] for r in results) / len(results)
        
        print(f"\n{'='*60}")
        print(f"全表扫描慢查询生成完成")
        print(f"  执行次数: {iterations}")
        print(f"  平均耗时: {avg_time:.2f}秒")
        print(f"  EXPLAIN特征: type=ALL (全表扫描)")
        print(f"  监控指标: performance_schema.events_statements_summary_by_digest")
        print(f"{'='*60}")
        
        return {"iterations": iterations, "avg_time": avg_time, "results": results}

    def generate_filesort_query(self, iterations: int = 5) -> Dict[str, any]:
        """
        生成文件排序慢查询
        
        EXPLAIN特征: Using filesort
        
        Args:
            iterations: 执行次数
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成文件排序慢查询: {iterations} 次")
        print(f"{'='*60}")
        
        results = []
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(iterations):
                    start = time.time()
                    
                    cursor.execute("""
                        SELECT SQL_NO_CACHE * 
                        FROM test_users 
                        WHERE status = %s
                        ORDER BY score DESC, name ASC
                        LIMIT 1000
                    """, (random.choice(["active", "inactive", "pending"]),))
                    
                    rows = cursor.fetchall()
                    elapsed = time.time() - start
                    results.append({
                        "iteration": i + 1,
                        "rows": len(rows),
                        "time": elapsed,
                    })
                    print(f"  第 {i+1}/{iterations} 次: 排序完成, 返回 {len(rows)} 行, 耗时 {elapsed:.2f}秒")
                    
                    time.sleep(0.3)
        
        avg_time = sum(r["time"] for r in results) / len(results)
        
        print(f"\n{'='*60}")
        print(f"文件排序慢查询生成完成")
        print(f"  执行次数: {iterations}")
        print(f"  平均耗时: {avg_time:.2f}秒")
        print(f"  EXPLAIN特征: Using filesort (文件排序)")
        print(f"{'='*60}")
        
        return {"iterations": iterations, "avg_time": avg_time, "results": results}

    def generate_temp_table_query(self, iterations: int = 5) -> Dict[str, any]:
        """
        生成临时表慢查询
        
        EXPLAIN特征: Using temporary; Using filesort
        
        Args:
            iterations: 执行次数
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成临时表慢查询: {iterations} 次")
        print(f"{'='*60}")
        
        results = []
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(iterations):
                    start = time.time()
                    
                    cursor.execute("""
                        SELECT SQL_NO_CACHE 
                            u.status,
                            COUNT(*) as order_count,
                            SUM(o.amount) as total_amount,
                            AVG(o.amount) as avg_amount
                        FROM test_users u
                        LEFT JOIN test_orders o ON u.id = o.user_id
                        GROUP BY u.status
                        ORDER BY total_amount DESC
                    """)
                    
                    rows = cursor.fetchall()
                    elapsed = time.time() - start
                    results.append({
                        "iteration": i + 1,
                        "rows": len(rows),
                        "time": elapsed,
                    })
                    print(f"  第 {i+1}/{iterations} 次: 聚合完成, 返回 {len(rows)} 行, 耗时 {elapsed:.2f}秒")
                    
                    time.sleep(0.3)
        
        avg_time = sum(r["time"] for r in results) / len(results)
        
        print(f"\n{'='*60}")
        print(f"临时表慢查询生成完成")
        print(f"  执行次数: {iterations}")
        print(f"  平均耗时: {avg_time:.2f}秒")
        print(f"  EXPLAIN特征: Using temporary; Using filesort")
        print(f"{'='*60}")
        
        return {"iterations": iterations, "avg_time": avg_time, "results": results}

    def generate_subquery_scenarios(self, iterations: int = 5) -> Dict[str, any]:
        """
        生成子查询慢查询
        
        EXPLAIN特征: DEPENDENT SUBQUERY
        
        Args:
            iterations: 执行次数
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成子查询慢查询: {iterations} 次")
        print(f"{'='*60}")
        
        results = []
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(iterations):
                    start = time.time()
                    
                    cursor.execute("""
                        SELECT SQL_NO_CACHE * 
                        FROM test_users u
                        WHERE u.id IN (
                            SELECT o.user_id 
                            FROM test_orders o 
                            WHERE o.amount > %s
                            GROUP BY o.user_id
                            HAVING COUNT(*) > 1
                        )
                        AND u.status = %s
                        LIMIT 500
                    """, (random.randint(100, 5000), random.choice(["active", "inactive"])))
                    
                    rows = cursor.fetchall()
                    elapsed = time.time() - start
                    results.append({
                        "iteration": i + 1,
                        "rows": len(rows),
                        "time": elapsed,
                    })
                    print(f"  第 {i+1}/{iterations} 次: 子查询完成, 返回 {len(rows)} 行, 耗时 {elapsed:.2f}秒")
                    
                    time.sleep(0.3)
        
        avg_time = sum(r["time"] for r in results) / len(results)
        
        print(f"\n{'='*60}")
        print(f"子查询慢查询生成完成")
        print(f"  执行次数: {iterations}")
        print(f"  平均耗时: {avg_time:.2f}秒")
        print(f"  EXPLAIN特征: DEPENDENT SUBQUERY")
        print(f"{'='*60}")
        
        return {"iterations": iterations, "avg_time": avg_time, "results": results}

    def generate_like_pattern_scenarios(self, iterations: int = 5) -> Dict[str, any]:
        """
        生成LIKE前缀通配符慢查询
        
        EXPLAIN特征: type=ALL (无法使用索引)
        
        Args:
            iterations: 执行次数
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成LIKE通配符慢查询: {iterations} 次")
        print(f"{'='*60}")
        
        results = []
        patterns = ["%abc%", "%123%", "%xyz%", "%test%", "%demo%"]
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(iterations):
                    start = time.time()
                    
                    pattern = random.choice(patterns)
                    cursor.execute("""
                        SELECT SQL_NO_CACHE * 
                        FROM test_large_table 
                        WHERE data LIKE %s
                        LIMIT 100
                    """, (pattern,))
                    
                    rows = cursor.fetchall()
                    elapsed = time.time() - start
                    results.append({
                        "iteration": i + 1,
                        "pattern": pattern,
                        "rows": len(rows),
                        "time": elapsed,
                    })
                    print(f"  第 {i+1}/{iterations} 次: LIKE '{pattern}' 完成, 返回 {len(rows)} 行, 耗时 {elapsed:.2f}秒")
                    
                    time.sleep(0.3)
        
        avg_time = sum(r["time"] for r in results) / len(results)
        
        print(f"\n{'='*60}")
        print(f"LIKE通配符慢查询生成完成")
        print(f"  执行次数: {iterations}")
        print(f"  平均耗时: {avg_time:.2f}秒")
        print(f"  EXPLAIN特征: type=ALL (LIKE '%xxx%' 无法使用索引)")
        print(f"{'='*60}")
        
        return {"iterations": iterations, "avg_time": avg_time, "results": results}

    def generate_join_without_index(self, iterations: int = 5) -> Dict[str, any]:
        """
        生成无索引JOIN慢查询
        
        EXPLAIN特征: Using join buffer
        
        Args:
            iterations: 执行次数
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成无索引JOIN慢查询: {iterations} 次")
        print(f"{'='*60}")
        
        results = []
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(iterations):
                    start = time.time()
                    
                    cursor.execute("""
                        SELECT SQL_NO_CACHE 
                            u.name,
                            n.description,
                            n.value
                        FROM test_users u
                        JOIN test_no_index_table n ON u.name = n.name
                        WHERE u.status = %s
                        LIMIT 500
                    """, (random.choice(["active", "inactive", "pending"]),))
                    
                    rows = cursor.fetchall()
                    elapsed = time.time() - start
                    results.append({
                        "iteration": i + 1,
                        "rows": len(rows),
                        "time": elapsed,
                    })
                    print(f"  第 {i+1}/{iterations} 次: JOIN完成, 返回 {len(rows)} 行, 耗时 {elapsed:.2f}秒")
                    
                    time.sleep(0.3)
        
        avg_time = sum(r["time"] for r in results) / len(results)
        
        print(f"\n{'='*60}")
        print(f"无索引JOIN慢查询生成完成")
        print(f"  执行次数: {iterations}")
        print(f"  平均耗时: {avg_time:.2f}秒")
        print(f"  EXPLAIN特征: Using join buffer (无索引JOIN)")
        print(f"{'='*60}")
        
        return {"iterations": iterations, "avg_time": avg_time, "results": results}

    def generate_complex_query(self, iterations: int = 3) -> Dict[str, any]:
        """
        生成复杂组合慢查询
        
        包含多种慢查询特征: 全表扫描、文件排序、临时表、子查询
        
        Args:
            iterations: 执行次数
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成复杂组合慢查询: {iterations} 次")
        print(f"{'='*60}")
        
        results = []
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                for i in range(iterations):
                    start = time.time()
                    
                    cursor.execute("""
                        SELECT SQL_NO_CACHE 
                            u.status,
                            u.name,
                            COUNT(o.id) as order_count,
                            SUM(o.amount) as total_amount,
                            AVG(o.amount) as avg_amount
                        FROM test_users u
                        LEFT JOIN test_orders o ON u.id = o.user_id
                        WHERE u.id IN (
                            SELECT DISTINCT user_id 
                            FROM test_orders 
                            WHERE amount > %s
                        )
                        AND u.name LIKE %s
                        GROUP BY u.status, u.name
                        HAVING total_amount > %s
                        ORDER BY total_amount DESC, order_count DESC
                        LIMIT 100
                    """, (random.randint(100, 1000), f"%{random.randint(0,9)}%", random.randint(0, 500)))
                    
                    rows = cursor.fetchall()
                    elapsed = time.time() - start
                    results.append({
                        "iteration": i + 1,
                        "rows": len(rows),
                        "time": elapsed,
                    })
                    print(f"  第 {i+1}/{iterations} 次: 复杂查询完成, 返回 {len(rows)} 行, 耗时 {elapsed:.2f}秒")
                    
                    time.sleep(0.5)
        
        avg_time = sum(r["time"] for r in results) / len(results)
        
        print(f"\n{'='*60}")
        print(f"复杂组合慢查询生成完成")
        print(f"  执行次数: {iterations}")
        print(f"  平均耗时: {avg_time:.2f}秒")
        print(f"  EXPLAIN特征: type=ALL, Using filesort, Using temporary, DEPENDENT SUBQUERY")
        print(f"{'='*60}")
        
        return {"iterations": iterations, "avg_time": avg_time, "results": results}

    def run_all_scenarios(self, iterations: int = 5) -> Dict[str, any]:
        """运行所有慢查询场景"""
        print("\n" + "=" * 60)
        print("运行所有慢查询场景")
        print("=" * 60)
        
        results = {}
        
        results["full_table_scan"] = self.generate_full_table_scan(iterations)
        results["filesort"] = self.generate_filesort_query(iterations)
        results["temp_table"] = self.generate_temp_table_query(iterations)
        results["subquery"] = self.generate_subquery_scenarios(iterations)
        results["like_pattern"] = self.generate_like_pattern_scenarios(iterations)
        results["join_no_index"] = self.generate_join_without_index(iterations)
        results["complex"] = self.generate_complex_query(max(2, iterations // 2))
        
        print("\n" + "=" * 60)
        print("所有慢查询场景执行完成!")
        print("=" * 60)
        
        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MySQL慢查询场景脚本")
    parser.add_argument("--all", action="store_true", help="运行所有慢查询场景")
    parser.add_argument("--full-scan", type=int, metavar="N", help="生成全表扫描 (次数)")
    parser.add_argument("--filesort", type=int, metavar="N", help="生成文件排序 (次数)")
    parser.add_argument("--temp-table", type=int, metavar="N", help="生成临时表 (次数)")
    parser.add_argument("--subquery", type=int, metavar="N", help="生成子查询 (次数)")
    parser.add_argument("--like-pattern", type=int, metavar="N", help="生成LIKE通配符 (次数)")
    parser.add_argument("--join-no-index", type=int, metavar="N", help="生成无索引JOIN (次数)")
    parser.add_argument("--complex", type=int, metavar="N", help="生成复杂查询 (次数)")
    parser.add_argument("--iterations", type=int, default=5, help="默认执行次数")
    parser.add_argument("--db", type=str, default=DEFAULT_TEST_DB, help="数据库名")

    args = parser.parse_args()

    scenarios = SlowQueryScenarios(args.db)

    if args.all:
        scenarios.run_all_scenarios(args.iterations)
    elif args.full_scan:
        scenarios.generate_full_table_scan(args.full_scan)
    elif args.filesort:
        scenarios.generate_filesort_query(args.filesort)
    elif args.temp_table:
        scenarios.generate_temp_table_query(args.temp_table)
    elif args.subquery:
        scenarios.generate_subquery_scenarios(args.subquery)
    elif args.like_pattern:
        scenarios.generate_like_pattern_scenarios(args.like_pattern)
    elif args.join_no_index:
        scenarios.generate_join_without_index(args.join_no_index)
    elif args.complex:
        scenarios.generate_complex_query(args.complex)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
