"""
锁等待与死锁场景脚本

产生行锁等待、死锁、阻塞链等场景
验证系统锁监控和死锁检测功能
"""

import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

import pymysql
from pymysql.cursors import DictCursor

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEFAULT_TEST_DB, get_db_config
from base import ConnectionManager


class LockScenarios:
    """锁场景生成器"""

    def __init__(self, db_name: str = DEFAULT_TEST_DB):
        self.db_name = db_name
        self.conn_mgr = ConnectionManager()

    def _get_connection(self, autocommit: bool = False) -> pymysql.Connection:
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
            autocommit=autocommit,
        )

    def generate_row_lock_wait(self, duration: int = 30) -> Dict[str, any]:
        """
        生成行锁等待
        
        影响: Innodb_row_lock_waits 增加
        
        Args:
            duration: 锁持有时间（秒）
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成行锁等待: 持有锁 {duration} 秒")
        print(f"{'='*60}")
        
        results = {"lock_holder": False, "lock_waiter": False, "deadlock": False}
        lock_id = random.randint(1, 100)
        
        holder_ready = threading.Event()
        holder_done = threading.Event()
        waiter_started = threading.Event()
        exception_holder = []
        exception_waiter = []

        def lock_holder():
            """锁持有者"""
            try:
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("BEGIN")
                    cursor.execute(
                        "UPDATE test_lock_table SET value = value + 1 WHERE id = %s",
                        (lock_id,)
                    )
                    print(f"  [持有者] 获取行锁 id={lock_id}")
                    holder_ready.set()
                    
                    time.sleep(duration)
                    
                    cursor.execute("COMMIT")
                    print(f"  [持有者] 释放行锁")
                conn.close()
                results["lock_holder"] = True
            except Exception as e:
                exception_holder.append(str(e))
                holder_ready.set()

        def lock_waiter():
            """锁等待者"""
            try:
                holder_ready.wait()
                time.sleep(0.5)
                waiter_started.set()
                
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    print(f"  [等待者] 尝试获取同一行锁 id={lock_id}...")
                    start_time = time.time()
                    
                    cursor.execute(
                        "UPDATE test_lock_table SET value = value + 1 WHERE id = %s",
                        (lock_id,)
                    )
                    
                    wait_time = time.time() - start_time
                    print(f"  [等待者] 获取锁成功，等待了 {wait_time:.2f} 秒")
                    
                    cursor.execute("COMMIT")
                conn.close()
                results["lock_waiter"] = True
            except Exception as e:
                exception_waiter.append(str(e))

        holder_thread = threading.Thread(target=lock_holder)
        waiter_thread = threading.Thread(target=lock_waiter)
        
        holder_thread.start()
        waiter_thread.start()
        
        holder_thread.join()
        waiter_thread.join()
        
        print(f"\n{'='*60}")
        print(f"行锁等待场景完成")
        print(f"  锁持有者: {'成功' if results['lock_holder'] else '失败'}")
        print(f"  锁等待者: {'成功' if results['lock_waiter'] else '失败'}")
        print(f"  影响: Innodb_row_lock_waits 增加")
        if exception_holder:
            print(f"  持有者异常: {exception_holder}")
        if exception_waiter:
            print(f"  等待者异常: {exception_waiter}")
        print(f"{'='*60}")
        
        return results

    def generate_deadlock_scenario(self) -> Dict[str, any]:
        """
        生成死锁场景
        
        影响: Innodb_deadlocks 增加，SHOW ENGINE INNODB STATUS 记录
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成死锁场景")
        print(f"{'='*60}")
        
        results = {"thread1_victim": False, "thread2_success": False, "deadlock_detected": False}
        
        lock_id_1 = random.randint(1, 50)
        lock_id_2 = random.randint(51, 100)
        
        thread1_step1 = threading.Event()
        thread2_step1 = threading.Event()
        exception_t1 = []
        exception_t2 = []

        def thread1():
            """线程1: 先锁id_1，再锁id_2"""
            try:
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("BEGIN")
                    
                    cursor.execute(
                        "UPDATE test_lock_table SET value = value + 1 WHERE id = %s",
                        (lock_id_1,)
                    )
                    print(f"  [T1] 锁定 id={lock_id_1}")
                    thread1_step1.set()
                    
                    thread2_step1.wait(timeout=5)
                    time.sleep(0.5)
                    
                    print(f"  [T1] 尝试锁定 id={lock_id_2} (将导致死锁)...")
                    cursor.execute(
                        "UPDATE test_lock_table SET value = value + 1 WHERE id = %s",
                        (lock_id_2,)
                    )
                    
                    cursor.execute("COMMIT")
                    results["thread1_victim"] = True
                conn.close()
            except Exception as e:
                error_msg = str(e)
                if "Deadlock" in error_msg or "deadlock" in error_msg.lower() or "1213" in error_msg:
                    print(f"  [T1] 被选为死锁牺牲者")
                    results["deadlock_detected"] = True
                exception_t1.append(error_msg)

        def thread2():
            """线程2: 先锁id_2，再锁id_1"""
            try:
                thread1_step1.wait(timeout=5)
                
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("BEGIN")
                    
                    cursor.execute(
                        "UPDATE test_lock_table SET value = value + 1 WHERE id = %s",
                        (lock_id_2,)
                    )
                    print(f"  [T2] 锁定 id={lock_id_2}")
                    thread2_step1.set()
                    
                    time.sleep(0.5)
                    
                    print(f"  [T2] 尝试锁定 id={lock_id_1}...")
                    cursor.execute(
                        "UPDATE test_lock_table SET value = value + 1 WHERE id = %s",
                        (lock_id_1,)
                    )
                    
                    cursor.execute("COMMIT")
                    print(f"  [T2] 成功完成")
                    results["thread2_success"] = True
                conn.close()
            except Exception as e:
                exception_t2.append(str(e))

        t1 = threading.Thread(target=thread1)
        t2 = threading.Thread(target=thread2)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        print(f"\n{'='*60}")
        print(f"死锁场景完成")
        print(f"  死锁检测: {'是' if results['deadlock_detected'] else '否'}")
        print(f"  线程1(牺牲者): {'成功' if results['thread1_victim'] else '被回滚'}")
        print(f"  线程2(赢家): {'成功' if results['thread2_success'] else '失败'}")
        print(f"  影响: Innodb_deadlocks 增加")
        print(f"  可通过 SHOW ENGINE INNODB STATUS 查看死锁记录")
        print(f"{'='*60}")
        
        return results

    def generate_blocking_chain(self, chain_length: int = 3, duration: int = 30) -> Dict[str, any]:
        """
        生成阻塞链
        
        T1 -> T2 -> T3 (T1阻塞T2, T2阻塞T3)
        
        Args:
            chain_length: 阻塞链长度
            duration: 持续时间（秒）
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成阻塞链: 长度 {chain_length}, 持续 {duration} 秒")
        print(f"{'='*60}")
        
        results = {"threads": []}
        lock_ids = [random.randint(1, 100) for _ in range(chain_length)]
        exceptions = [[] for _ in range(chain_length)]
        events = [threading.Event() for _ in range(chain_length)]

        def chain_thread(index: int):
            """阻塞链中的线程"""
            try:
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("BEGIN")
                    
                    my_lock_id = lock_ids[index]
                    cursor.execute(
                        "UPDATE test_lock_table SET value = value + 1 WHERE id = %s",
                        (my_lock_id,)
                    )
                    print(f"  [T{index+1}] 获取锁 id={my_lock_id}")
                    events[index].set()
                    
                    if index > 0:
                        prev_lock_id = lock_ids[index - 1]
                        events[index - 1].wait(timeout=5)
                        time.sleep(0.3)
                        print(f"  [T{index+1}] 尝试获取 T{index} 的锁 id={prev_lock_id}...")
                        cursor.execute(
                            "UPDATE test_lock_table SET value = value + 1 WHERE id = %s",
                            (prev_lock_id,)
                        )
                        print(f"  [T{index+1}] 获取锁成功")
                    
                    if index == 0:
                        time.sleep(duration)
                    
                    cursor.execute("COMMIT")
                    print(f"  [T{index+1}] 完成")
                    results["threads"].append(index + 1)
                conn.close()
            except Exception as e:
                exceptions[index].append(str(e))
                print(f"  [T{index+1}] 异常: {e}")

        threads = []
        for i in range(chain_length):
            t = threading.Thread(target=chain_thread, args=(i,))
            threads.append(t)
            t.start()
            time.sleep(0.2)
        
        for t in threads:
            t.join()
        
        print(f"\n{'='*60}")
        print(f"阻塞链场景完成")
        print(f"  完成的线程: {results['threads']}")
        print(f"  阻塞链长度: {chain_length}")
        print(f"  影响: information_schema.innodb_lock_waits, performance_schema.data_locks")
        print(f"{'='*60}")
        
        return results

    def generate_table_lock_scenario(self, duration: int = 10) -> Dict[str, any]:
        """
        生成表锁场景
        
        使用 LOCK TABLES 显式加锁
        
        Args:
            duration: 锁持有时间（秒）
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成表锁场景: 持续 {duration} 秒")
        print(f"{'='*60}")
        
        results = {"lock_acquired": False, "waiter_blocked": False}
        holder_ready = threading.Event()
        exception_holder = []
        exception_waiter = []

        def table_lock_holder():
            """表锁持有者"""
            try:
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("LOCK TABLES test_lock_table WRITE")
                    print(f"  [持有者] 获取表锁 WRITE")
                    results["lock_acquired"] = True
                    holder_ready.set()
                    
                    time.sleep(duration)
                    
                    cursor.execute("UNLOCK TABLES")
                    print(f"  [持有者] 释放表锁")
                conn.close()
            except Exception as e:
                exception_holder.append(str(e))
                holder_ready.set()

        def table_lock_waiter():
            """表锁等待者"""
            try:
                holder_ready.wait()
                time.sleep(0.5)
                
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    print(f"  [等待者] 尝试读取表...")
                    start_time = time.time()
                    
                    cursor.execute("SELECT * FROM test_lock_table LIMIT 1")
                    cursor.fetchall()
                    
                    wait_time = time.time() - start_time
                    print(f"  [等待者] 读取成功，等待了 {wait_time:.2f} 秒")
                    results["waiter_blocked"] = True
                conn.close()
            except Exception as e:
                exception_waiter.append(str(e))

        t1 = threading.Thread(target=table_lock_holder)
        t2 = threading.Thread(target=table_lock_waiter)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        print(f"\n{'='*60}")
        print(f"表锁场景完成")
        print(f"  锁获取: {'成功' if results['lock_acquired'] else '失败'}")
        print(f"  等待者阻塞: {'是' if results['waiter_blocked'] else '否'}")
        print(f"  影响: Table_locks_waited 增加")
        print(f"{'='*60}")
        
        return results

    def generate_multiple_deadlocks(self, count: int = 3, interval: float = 2.0) -> Dict[str, any]:
        """
        生成多次死锁
        
        Args:
            count: 死锁次数
            interval: 每次间隔（秒）
        
        Returns:
            执行统计
        """
        print(f"\n{'='*60}")
        print(f"开始生成多次死锁: {count} 次")
        print(f"{'='*60}")
        
        results = []
        for i in range(count):
            print(f"\n--- 第 {i+1}/{count} 次死锁 ---")
            result = self.generate_deadlock_scenario()
            results.append(result)
            
            if i < count - 1:
                print(f"  等待 {interval} 秒...")
                time.sleep(interval)
        
        success_count = sum(1 for r in results if r.get("deadlock_detected"))
        
        print(f"\n{'='*60}")
        print(f"多次死锁场景完成")
        print(f"  总次数: {count}")
        print(f"  成功检测: {success_count}")
        print(f"  影响: Innodb_deadlocks 增加 {success_count}")
        print(f"{'='*60}")
        
        return {"total": count, "detected": success_count, "results": results}

    def get_lock_status(self) -> Dict[str, any]:
        """获取当前锁状态"""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW GLOBAL STATUS LIKE 'Innodb_row_lock%'")
                row_locks = {row["Variable_name"]: row["Value"] for row in cursor.fetchall()}
                
                cursor.execute("SHOW GLOBAL STATUS LIKE 'Innodb_deadlocks'")
                deadlocks = cursor.fetchone()
                
                cursor.execute("SHOW GLOBAL STATUS LIKE 'Table_locks%'")
                table_locks = {row["Variable_name"]: row["Value"] for row in cursor.fetchall()}
        
        return {
            "row_locks": row_locks,
            "deadlocks": deadlocks["Value"] if deadlocks else 0,
            "table_locks": table_locks,
        }

    def run_all_scenarios(self, duration: int = 20) -> Dict[str, any]:
        """运行所有锁场景"""
        print("\n" + "=" * 60)
        print("运行所有锁场景")
        print("=" * 60)
        
        results = {}
        
        print("\n--- 获取初始锁状态 ---")
        initial_status = self.get_lock_status()
        print(f"  初始 Innodb_row_lock_waits: {initial_status['row_locks'].get('Innodb_row_lock_waits', 0)}")
        print(f"  初始 Innodb_deadlocks: {initial_status['deadlocks']}")
        
        results["row_lock"] = self.generate_row_lock_wait(duration)
        results["deadlock"] = self.generate_deadlock_scenario()
        results["blocking_chain"] = self.generate_blocking_chain(chain_length=3, duration=duration)
        
        print("\n--- 获取最终锁状态 ---")
        final_status = self.get_lock_status()
        print(f"  最终 Innodb_row_lock_waits: {final_status['row_locks'].get('Innodb_row_lock_waits', 0)}")
        print(f"  最终 Innodb_deadlocks: {final_status['deadlocks']}")
        
        print("\n" + "=" * 60)
        print("所有锁场景执行完成!")
        print("=" * 60)
        
        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MySQL锁场景脚本")
    parser.add_argument("--row-lock", action="store_true", help="生成行锁等待")
    parser.add_argument("--deadlock", action="store_true", help="生成死锁")
    parser.add_argument("--multiple-deadlocks", type=int, metavar="N", help="生成N次死锁")
    parser.add_argument("--blocking-chain", type=int, metavar="N", help="生成长度为N的阻塞链")
    parser.add_argument("--table-lock", action="store_true", help="生成表锁")
    parser.add_argument("--status", action="store_true", help="查看锁状态")
    parser.add_argument("--all", action="store_true", help="运行所有场景")
    parser.add_argument("--duration", type=int, default=20, help="持续时间（秒）")
    parser.add_argument("--db", type=str, default=DEFAULT_TEST_DB, help="数据库名")

    args = parser.parse_args()

    lock = LockScenarios(args.db)

    if args.status:
        status = lock.get_lock_status()
        print("\n锁状态:")
        print(f"  Innodb_row_lock_waits: {status['row_locks'].get('Innodb_row_lock_waits', 0)}")
        print(f"  Innodb_row_lock_time: {status['row_locks'].get('Innodb_row_lock_time', 0)}")
        print(f"  Innodb_deadlocks: {status['deadlocks']}")
        print(f"  Table_locks_waited: {status['table_locks'].get('Table_locks_waited', 0)}")
    elif args.all:
        lock.run_all_scenarios(args.duration)
    elif args.row_lock:
        lock.generate_row_lock_wait(args.duration)
    elif args.deadlock:
        lock.generate_deadlock_scenario()
    elif args.multiple_deadlocks:
        lock.generate_multiple_deadlocks(args.multiple_deadlocks)
    elif args.blocking_chain:
        lock.generate_blocking_chain(args.blocking_chain, args.duration)
    elif args.table_lock:
        lock.generate_table_lock_scenario(args.duration)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
