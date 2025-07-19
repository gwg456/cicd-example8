#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL General Log 收集器
用于实时监控和解析MySQL的General Log
"""

import os
import re
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Generator
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger
import pymysql
from ..utils.config import Config
from ..utils.parser import SQLParser
from ..storage.audit_storage import AuditStorage


class GeneralLogHandler(FileSystemEventHandler):
    """General Log文件变化监控处理器"""
    
    def __init__(self, collector):
        self.collector = collector
        
    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.collector.log_file_path:
            self.collector.process_new_lines()


class GeneralLogCollector:
    """MySQL General Log 收集器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.log_file_path = config.get('collectors.general_log.file_path', 
                                       '/var/log/mysql/general.log')
        self.poll_interval = config.get('collectors.general_log.poll_interval', 1)
        self.enabled = config.get('collectors.general_log.enabled', True)
        
        # 初始化组件
        self.sql_parser = SQLParser()
        self.storage = AuditStorage(config)
        
        # 状态管理
        self.file_position = 0
        self.running = False
        self.observer = None
        self.thread = None
        
        # 日志解析正则表达式
        self.log_pattern = re.compile(
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+'
            r'(?P<thread_id>\d+)\s+'
            r'(?P<command>\w+)\s+'
            r'(?P<argument>.*)'
        )
        
        # MySQL连接信息
        self.connection_pool = self._create_connection_pool()
        
    def _create_connection_pool(self) -> pymysql.Connection:
        """创建MySQL连接"""
        try:
            return pymysql.connect(
                host=self.config.get('mysql.host', 'localhost'),
                port=self.config.get('mysql.port', 3306),
                user=self.config.get('mysql.user'),
                password=self.config.get('mysql.password'),
                database=self.config.get('mysql.database', 'mysql'),
                charset='utf8mb4',
                autocommit=True
            )
        except Exception as e:
            logger.error(f"Failed to create MySQL connection: {e}")
            return None
    
    def start(self):
        """启动收集器"""
        if not self.enabled:
            logger.info("General Log collector is disabled")
            return
            
        if not os.path.exists(self.log_file_path):
            logger.error(f"General log file not found: {self.log_file_path}")
            return
            
        logger.info(f"Starting General Log collector for: {self.log_file_path}")
        
        # 设置文件监控
        self.observer = Observer()
        event_handler = GeneralLogHandler(self)
        log_dir = os.path.dirname(self.log_file_path)
        self.observer.schedule(event_handler, log_dir, recursive=False)
        
        # 启动监控
        self.running = True
        self.observer.start()
        
        # 启动处理线程
        self.thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.thread.start()
        
        # 处理已存在的日志
        self._initialize_file_position()
        self.process_new_lines()
        
        logger.info("General Log collector started successfully")
    
    def stop(self):
        """停止收集器"""
        logger.info("Stopping General Log collector...")
        
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            
        if self.thread:
            self.thread.join(timeout=5)
            
        if self.connection_pool:
            self.connection_pool.close()
            
        logger.info("General Log collector stopped")
    
    def _initialize_file_position(self):
        """初始化文件读取位置"""
        try:
            # 获取文件大小，从末尾开始读取新内容
            if os.path.exists(self.log_file_path):
                self.file_position = os.path.getsize(self.log_file_path)
                logger.info(f"Initialized file position to: {self.file_position}")
        except Exception as e:
            logger.error(f"Failed to initialize file position: {e}")
            self.file_position = 0
    
    def _collection_loop(self):
        """收集循环"""
        while self.running:
            try:
                time.sleep(self.poll_interval)
                # 定期检查文件变化
                self.process_new_lines()
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                time.sleep(5)  # 错误时等待更长时间
    
    def process_new_lines(self):
        """处理新的日志行"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 移动到上次读取位置
                f.seek(self.file_position)
                
                new_lines = []
                for line in f:
                    line = line.strip()
                    if line:
                        new_lines.append(line)
                
                # 更新文件位置
                self.file_position = f.tell()
                
                # 处理新行
                if new_lines:
                    self._process_log_lines(new_lines)
                    
        except FileNotFoundError:
            logger.warning(f"Log file not found: {self.log_file_path}")
        except Exception as e:
            logger.error(f"Error processing new lines: {e}")
    
    def _process_log_lines(self, lines: List[str]):
        """处理日志行"""
        for line in lines:
            try:
                parsed_log = self._parse_log_line(line)
                if parsed_log:
                    audit_record = self._create_audit_record(parsed_log)
                    if audit_record:
                        self.storage.store_audit_record(audit_record)
            except Exception as e:
                logger.error(f"Error processing log line: {line}, error: {e}")
    
    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """解析单行日志"""
        # 尝试匹配标准格式
        match = self.log_pattern.match(line)
        if match:
            return match.groupdict()
        
        # 处理特殊格式的日志
        return self._parse_special_format(line)
    
    def _parse_special_format(self, line: str) -> Optional[Dict]:
        """解析特殊格式的日志"""
        # 处理不同版本MySQL的日志格式差异
        patterns = [
            # MySQL 8.0格式
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(?P<thread_id>\d+)\s+(?P<command>\w+)\s+(?P<argument>.*)',
            # MySQL 5.7格式
            r'(?P<timestamp>\d{6}\s+\d{1,2}:\d{2}:\d{2})\s+(?P<thread_id>\d+)\s+(?P<command>\w+)\s+(?P<argument>.*)',
            # 简化格式
            r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(?P<thread_id>\d+)\s+(?P<command>\w+)\s+(?P<argument>.*)'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                return match.groupdict()
        
        return None
    
    def _create_audit_record(self, parsed_log: Dict) -> Optional[Dict]:
        """创建审计记录"""
        try:
            command = parsed_log.get('command', '').upper()
            argument = parsed_log.get('argument', '')
            
            # 过滤不需要审计的命令
            if self._should_skip_command(command, argument):
                return None
            
            # 解析SQL语句
            sql_info = self.sql_parser.parse(argument) if argument else {}
            
            # 获取连接信息
            thread_id = parsed_log.get('thread_id')
            connection_info = self._get_connection_info(thread_id)
            
            # 构建审计记录
            audit_record = {
                'timestamp': self._parse_timestamp(parsed_log.get('timestamp')),
                'thread_id': int(thread_id) if thread_id else None,
                'command': command,
                'sql_statement': argument,
                'sql_type': sql_info.get('type'),
                'database_name': sql_info.get('database'),
                'table_names': sql_info.get('tables', []),
                'user_name': connection_info.get('user'),
                'host': connection_info.get('host'),
                'connection_id': connection_info.get('connection_id'),
                'execution_time': sql_info.get('execution_time'),
                'rows_affected': sql_info.get('rows_affected'),
                'status': 'SUCCESS',  # General log通常只记录成功的操作
                'source': 'general_log'
            }
            
            return audit_record
            
        except Exception as e:
            logger.error(f"Error creating audit record: {e}")
            return None
    
    def _should_skip_command(self, command: str, argument: str) -> bool:
        """判断是否应该跳过某个命令"""
        # 跳过的命令类型
        skip_commands = {
            'PING', 'STATISTICS', 'PROCESSLIST', 'SHOW', 'DESC', 'DESCRIBE'
        }
        
        if command in skip_commands:
            return True
        
        # 跳过系统查询
        if argument:
            skip_patterns = [
                r'SELECT.*INFORMATION_SCHEMA',
                r'SELECT.*performance_schema',
                r'SELECT.*mysql\.',
                r'SHOW.*',
                r'DESC.*',
                r'EXPLAIN.*'
            ]
            
            for pattern in skip_patterns:
                if re.search(pattern, argument, re.IGNORECASE):
                    return True
        
        return False
    
    def _get_connection_info(self, thread_id: str) -> Dict:
        """获取连接信息"""
        if not self.connection_pool or not thread_id:
            return {}
        
        try:
            cursor = self.connection_pool.cursor()
            cursor.execute("""
                SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO
                FROM INFORMATION_SCHEMA.PROCESSLIST
                WHERE ID = %s
            """, (thread_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            if result:
                return {
                    'connection_id': result[0],
                    'user': result[1],
                    'host': result[2],
                    'database': result[3],
                    'command': result[4],
                    'time': result[5],
                    'state': result[6],
                    'info': result[7]
                }
        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
        
        return {}
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """解析时间戳"""
        if not timestamp_str:
            return datetime.now()
        
        # 支持多种时间格式
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d %H:%M:%S',
            '%y%m%d %H:%M:%S',
            '%Y%m%d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # 如果都解析失败，返回当前时间
        logger.warning(f"Failed to parse timestamp: {timestamp_str}")
        return datetime.now()
    
    def get_stats(self) -> Dict:
        """获取收集器统计信息"""
        return {
            'collector_type': 'general_log',
            'enabled': self.enabled,
            'running': self.running,
            'log_file_path': self.log_file_path,
            'file_position': self.file_position,
            'poll_interval': self.poll_interval,
            'file_exists': os.path.exists(self.log_file_path),
            'file_size': os.path.getsize(self.log_file_path) if os.path.exists(self.log_file_path) else 0
        }


def main():
    """测试入口"""
    from ..utils.config import Config
    
    config = Config()
    collector = GeneralLogCollector(config)
    
    try:
        collector.start()
        print("General Log collector started. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
            stats = collector.get_stats()
            print(f"Stats: {stats}")
    except KeyboardInterrupt:
        print("\nStopping collector...")
    finally:
        collector.stop()


if __name__ == '__main__':
    main()