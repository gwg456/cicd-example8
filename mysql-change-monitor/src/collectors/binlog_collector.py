#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL Binary Log 变更收集器
专门监控数据库的INSERT、UPDATE、DELETE操作
"""

import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent
from pymysqlreplication.event import QueryEvent, XidEvent
from loguru import logger
import pymysql


class BinlogCollector:
    """Binary Log变更收集器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.mysql_settings = {
            'host': config.get('mysql.host', 'localhost'),
            'port': config.get('mysql.port', 3306),
            'user': config.get('mysql.user'),
            'passwd': config.get('mysql.password'),
            'charset': 'utf8mb4'
        }
        
        # 监控配置
        self.monitoring_mode = config.get('monitoring', {}).get('mode', 'whitelist')
        self.monitored_databases = config.get('monitoring', {}).get('databases', [])
        self.target_tables = config.get('monitoring', {}).get('target_tables', [])
        self.exclude_tables = config.get('monitoring', {}).get('exclude_tables', [])
        
        # 状态管理
        self.running = False
        self.stream = None
        self.thread = None
        
        # 变更事件回调
        self.change_callbacks = []
        
        # 统计信息
        self.stats = {
            'total_events': 0,
            'insert_events': 0,
            'update_events': 0,
            'delete_events': 0,
            'ddl_events': 0,
            'start_time': None,
            'last_event_time': None
        }
        
    def add_change_callback(self, callback: Callable):
        """添加变更事件回调函数"""
        self.change_callbacks.append(callback)
    
    def start(self):
        """启动Binary Log监控"""
        if self.running:
            logger.warning("Binlog collector is already running")
            return
        
        try:
            # 获取当前binlog位置
            log_file, log_pos = self._get_current_binlog_position()
            
            # 创建binlog流读取器
            self.stream = BinLogStreamReader(
                connection_settings=self.mysql_settings,
                server_id=self.config.get('collectors.binary_log.server_id', 1),
                log_file=log_file,
                log_pos=log_pos,
                only_events=[
                    DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent, QueryEvent
                ],
                resume_stream=True,
                blocking=True
            )
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            # 启动监控线程
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"Binlog collector started from {log_file}:{log_pos}")
            
        except Exception as e:
            logger.error(f"Failed to start binlog collector: {e}")
            raise
    
    def stop(self):
        """停止Binary Log监控"""
        if not self.running:
            return
        
        self.running = False
        
        if self.stream:
            self.stream.close()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Binlog collector stopped")
    
    def _get_current_binlog_position(self) -> tuple:
        """获取当前binlog位置"""
        try:
            connection = pymysql.connect(**self.mysql_settings)
            cursor = connection.cursor()
            
            cursor.execute("SHOW MASTER STATUS")
            result = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            if result:
                return result[0], result[1]  # (log_file, log_pos)
            else:
                raise Exception("Unable to get master status")
                
        except Exception as e:
            logger.error(f"Failed to get binlog position: {e}")
            raise
    
    def resume_from_position(self, log_file: str, log_pos: int):
        """从指定位置恢复监控"""
        try:
            if self.stream:
                self.stream.close()
            
            # 从指定位置创建新的流
            self.stream = BinLogStreamReader(
                connection_settings=self.mysql_settings,
                server_id=self.config.get('collectors.binary_log.server_id', 1),
                log_file=log_file,
                log_pos=log_pos,
                only_events=[
                    DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent, QueryEvent
                ],
                resume_stream=True,
                blocking=True
            )
            
            logger.info(f"Resumed binlog monitoring from {log_file}:{log_pos}")
            
        except Exception as e:
            logger.error(f"Failed to resume from position: {e}")
            raise
    
    def _monitor_loop(self):
        """监控循环"""
        logger.info("Starting binlog monitoring loop")
        
        try:
            for binlog_event in self.stream:
                if not self.running:
                    break
                
                self._process_binlog_event(binlog_event)
                self.stats['total_events'] += 1
                self.stats['last_event_time'] = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in binlog monitoring loop: {e}")
        finally:
            logger.info("Binlog monitoring loop ended")
    
    def _process_binlog_event(self, event):
        """处理binlog事件"""
        try:
            if isinstance(event, (WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent)):
                self._process_row_event(event)
            elif isinstance(event, QueryEvent):
                self._process_query_event(event)
                
        except Exception as e:
            logger.error(f"Error processing binlog event: {e}")
    
    def _process_row_event(self, event):
        """处理行变更事件"""
        schema = event.schema
        table = event.table
        
        # 检查是否需要监控此表
        if not self._should_monitor_table(schema, table):
            return
        
        # 确定操作类型
        if isinstance(event, WriteRowsEvent):
            operation = 'INSERT'
            self.stats['insert_events'] += 1
        elif isinstance(event, UpdateRowsEvent):
            operation = 'UPDATE'
            self.stats['update_events'] += 1
        elif isinstance(event, DeleteRowsEvent):
            operation = 'DELETE'
            self.stats['delete_events'] += 1
        else:
            return
        
        # 处理每一行变更
        for row in event.rows:
            change_record = self._create_change_record(
                event, operation, schema, table, row
            )
            
            # 调用回调函数
            self._notify_change_callbacks(change_record)
    
    def _process_query_event(self, event):
        """处理SQL查询事件（主要是DDL）"""
        if not event.query:
            return
        
        query = event.query.strip().upper()
        
        # 检查是否为DDL操作
        ddl_keywords = ['CREATE', 'ALTER', 'DROP', 'RENAME', 'TRUNCATE']
        if not any(query.startswith(keyword) for keyword in ddl_keywords):
            return
        
        self.stats['ddl_events'] += 1
        
        # 创建DDL变更记录
        change_record = {
            'timestamp': datetime.fromtimestamp(event.timestamp),
            'operation_type': 'DDL',
            'database_name': event.schema,
            'table_name': self._extract_table_name(event.query),
            'sql_statement': event.query,
            'user_name': None,  # DDL事件中通常没有用户信息
            'thread_id': event.packet.log_pos,
            'rows_affected': 0,
            'execution_time': 0,
            'before_values': None,
            'after_values': None,
            'source': 'binlog_ddl',
            'binlog_file': event.packet.log_file,
            'binlog_pos': event.packet.log_pos
        }
        
        # 调用回调函数
        self._notify_change_callbacks(change_record)
    
    def _create_change_record(self, event, operation: str, schema: str, table: str, row) -> Dict:
        """创建变更记录"""
        change_record = {
            'timestamp': datetime.fromtimestamp(event.timestamp),
            'operation_type': operation,
            'database_name': schema,
            'table_name': table,
            'sql_statement': None,
            'user_name': None,
            'thread_id': event.packet.log_pos,
            'rows_affected': 1,
            'execution_time': 0,
            'source': 'binlog_dml',
            'binlog_file': event.packet.log_file,
            'binlog_pos': event.packet.log_pos
        }
        
        # 根据操作类型设置前后值
        if operation == 'INSERT':
            change_record['before_values'] = None
            change_record['after_values'] = row['values']
        elif operation == 'UPDATE':
            change_record['before_values'] = row['before_values']
            change_record['after_values'] = row['after_values']
        elif operation == 'DELETE':
            change_record['before_values'] = row['values']
            change_record['after_values'] = None
        
        return change_record
    
    def _should_monitor_table(self, schema: str, table: str) -> bool:
        """判断是否应该监控此表"""
        # 检查数据库白名单
        if self.monitored_databases and schema not in self.monitored_databases:
            return False
        
        full_table_name = f"{schema}.{table}"
        table_only = table
        
        # 白名单模式：只监控指定的表
        if self.monitoring_mode == 'whitelist':
            if not self.target_tables:
                return False  # 没有指定表则不监控任何表
            
            # 检查是否在目标表列表中
            for target_table in self.target_tables:
                if self._match_table_pattern(full_table_name, table_only, target_table):
                    # 即使在白名单中，也要检查是否在排除列表中
                    for exclude_pattern in self.exclude_tables:
                        if self._match_pattern(full_table_name, exclude_pattern):
                            return False
                    return True
            return False
        
        # 黑名单模式：监控所有表除了排除的
        elif self.monitoring_mode == 'blacklist':
            # 检查表黑名单
            for exclude_pattern in self.exclude_tables:
                if self._match_pattern(full_table_name, exclude_pattern):
                    return False
            return True
        
        return False
    
    def _match_table_pattern(self, full_table_name: str, table_only: str, pattern: str) -> bool:
        """匹配表模式，支持 database.table 或 table 格式"""
        pattern = pattern.strip('"\'')  # 移除引号
        
        # 如果模式包含点，说明是 database.table 格式
        if '.' in pattern:
            return self._match_pattern(full_table_name.lower(), pattern.lower())
        else:
            # 只有表名，匹配表名部分
            return self._match_pattern(table_only.lower(), pattern.lower())
    
    def _match_pattern(self, name: str, pattern: str) -> bool:
        """匹配模式（支持通配符）"""
        import fnmatch
        return fnmatch.fnmatch(name.lower(), pattern.lower())
    
    def _extract_table_name(self, sql: str) -> Optional[str]:
        """从SQL语句中提取表名"""
        try:
            sql = sql.strip().upper()
            words = sql.split()
            
            # 查找表名的位置
            table_keywords = ['TABLE', 'INDEX', 'VIEW', 'PROCEDURE', 'FUNCTION']
            for i, word in enumerate(words):
                if word in table_keywords and i + 1 < len(words):
                    table_name = words[i + 1]
                    # 清理表名（去除反引号等）
                    table_name = table_name.strip('`"\'')
                    return table_name
            
            return None
        except:
            return None
    
    def _notify_change_callbacks(self, change_record: Dict):
        """通知所有变更回调函数"""
        for callback in self.change_callbacks:
            try:
                callback(change_record)
            except Exception as e:
                logger.error(f"Error in change callback: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        current_stats = self.stats.copy()
        
        if current_stats['start_time']:
            uptime = datetime.now() - current_stats['start_time']
            current_stats['uptime_seconds'] = uptime.total_seconds()
        
        current_stats['running'] = self.running
        return current_stats


def main():
    """测试入口"""
    import yaml
    
    # 测试配置
    config = {
        'mysql': {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'password'
        },
        'monitoring': {
            'databases': ['test'],
            'tables': ['users', 'orders'],
            'exclude_tables': ['logs']
        },
        'collectors': {
            'binary_log': {
                'server_id': 1
            }
        }
    }
    
    def change_handler(change_record):
        """变更处理函数"""
        print(f"变更检测: {change_record['operation_type']} "
              f"{change_record['database_name']}.{change_record['table_name']}")
        if change_record['before_values']:
            print(f"  变更前: {change_record['before_values']}")
        if change_record['after_values']:
            print(f"  变更后: {change_record['after_values']}")
    
    # 创建收集器
    collector = BinlogCollector(config)
    collector.add_change_callback(change_handler)
    
    try:
        # 启动监控
        collector.start()
        print("Binlog collector started. Press Ctrl+C to stop...")
        
        while True:
            time.sleep(5)
            stats = collector.get_stats()
            print(f"统计: 总事件={stats['total_events']}, "
                  f"插入={stats['insert_events']}, "
                  f"更新={stats['update_events']}, "
                  f"删除={stats['delete_events']}")
            
    except KeyboardInterrupt:
        print("\nStopping collector...")
    finally:
        collector.stop()


if __name__ == '__main__':
    main()