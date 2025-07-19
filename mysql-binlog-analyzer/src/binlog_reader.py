#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL Binlog 读取器
实时读取和解析 MySQL binlog 事件
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Generator, Callable
from queue import Queue, Empty
import pymysql
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent
)
from pymysqlreplication.event import RotateEvent, FormatDescriptionEvent
from loguru import logger

from .event_parser import BinlogEventParser
from .utils.mysql_helper import MySQLHelper


class BinlogPosition:
    """Binlog位置信息"""
    
    def __init__(self, log_file: str = "", log_pos: int = 4):
        self.log_file = log_file
        self.log_pos = log_pos
        self.timestamp = datetime.now()
    
    def __str__(self):
        return f"{self.log_file}:{self.log_pos}"
    
    def to_dict(self):
        return {
            'log_file': self.log_file,
            'log_pos': self.log_pos,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        pos = cls(data['log_file'], data['log_pos'])
        if 'timestamp' in data:
            pos.timestamp = datetime.fromisoformat(data['timestamp'])
        return pos


class BinlogReader:
    """MySQL Binlog 读取器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.mysql_config = config['mysql']['source']
        self.binlog_config = self.mysql_config.get('binlog', {})
        
        # 初始化组件
        self.mysql_helper = MySQLHelper(self.mysql_config)
        self.event_parser = BinlogEventParser(config)
        
        # 状态管理
        self.running = False
        self.reader_thread = None
        self.stream = None
        
        # 事件队列
        self.event_queue = Queue(maxsize=config.get('processing', {}).get('queue_size', 10000))
        
        # 位置管理
        self.current_position = None
        self.checkpoint_interval = config.get('processing', {}).get('checkpoint_interval', 60)
        self.last_checkpoint_time = time.time()
        
        # 监控表配置
        self.target_tables = self._load_target_tables()
        
        # 事件回调
        self.event_callbacks = []
        
        # 统计信息
        self.stats = {
            'events_processed': 0,
            'events_filtered': 0,
            'bytes_processed': 0,
            'start_time': None,
            'last_event_time': None,
            'errors': 0
        }
        
        logger.info(f"初始化 BinlogReader，监控 {len(self.target_tables)} 个表")
    
    def _load_target_tables(self) -> Dict[str, Dict]:
        """加载目标表配置"""
        target_tables = {}
        tables_config = self.config.get('tables', {}).get('target_tables', [])
        
        for table_config in tables_config:
            database = table_config.get('database')
            table = table_config.get('table')
            
            if database and table:
                key = f"{database}.{table}"
                target_tables[key] = {
                    'database': database,
                    'table': table,
                    'operations': set(table_config.get('operations', ['INSERT', 'UPDATE', 'DELETE'])),
                    'track_columns': table_config.get('track_columns', []),
                    'primary_key': table_config.get('primary_key', 'id')
                }
        
        return target_tables
    
    def add_event_callback(self, callback: Callable):
        """添加事件回调函数"""
        self.event_callbacks.append(callback)
    
    def get_current_position(self) -> Optional[BinlogPosition]:
        """获取当前binlog位置"""
        return self.current_position
    
    def set_start_position(self, position: BinlogPosition):
        """设置起始位置"""
        self.current_position = position
        logger.info(f"设置起始位置: {position}")
    
    def get_latest_position(self) -> BinlogPosition:
        """获取最新的binlog位置"""
        try:
            with self.mysql_helper.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SHOW MASTER STATUS")
                    result = cursor.fetchone()
                    if result:
                        return BinlogPosition(result[0], result[1])
                    else:
                        raise Exception("无法获取master status")
        except Exception as e:
            logger.error(f"获取最新位置失败: {e}")
            raise
    
    def start_reading(self, start_position: Optional[BinlogPosition] = None):
        """开始读取binlog"""
        if self.running:
            logger.warning("BinlogReader 已经在运行")
            return
        
        # 设置起始位置
        if start_position:
            self.set_start_position(start_position)
        elif not self.current_position:
            # 使用配置中的位置或最新位置
            if self.binlog_config.get('log_file'):
                self.current_position = BinlogPosition(
                    self.binlog_config['log_file'],
                    self.binlog_config.get('log_pos', 4)
                )
            else:
                self.current_position = self.get_latest_position()
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # 启动读取线程
        self.reader_thread = threading.Thread(target=self._read_binlog, daemon=True)
        self.reader_thread.start()
        
        logger.info(f"开始读取 binlog，起始位置: {self.current_position}")
    
    def stop_reading(self):
        """停止读取binlog"""
        if not self.running:
            return
        
        logger.info("停止读取 binlog...")
        self.running = False
        
        # 关闭stream
        if self.stream:
            self.stream.close()
        
        # 等待线程结束
        if self.reader_thread:
            self.reader_thread.join(timeout=5)
        
        logger.info("Binlog 读取已停止")
    
    def _read_binlog(self):
        """读取binlog的主循环"""
        try:
            # 创建binlog stream
            self._create_stream()
            
            logger.info("开始处理 binlog 事件...")
            
            for binlog_event in self.stream:
                if not self.running:
                    break
                
                try:
                    self._process_binlog_event(binlog_event)
                except Exception as e:
                    logger.error(f"处理 binlog 事件失败: {e}")
                    self.stats['errors'] += 1
                    continue
                
                # 定期检查点
                if self._should_checkpoint():
                    self._save_checkpoint()
        
        except Exception as e:
            logger.error(f"读取 binlog 失败: {e}")
            self.stats['errors'] += 1
        finally:
            if self.stream:
                self.stream.close()
    
    def _create_stream(self):
        """创建binlog stream"""
        stream_settings = {
            'connection_settings': {
                'host': self.mysql_config['host'],
                'port': self.mysql_config['port'],
                'user': self.mysql_config['user'],
                'passwd': self.mysql_config['password'],
                'charset': self.mysql_config.get('charset', 'utf8mb4')
            },
            'server_id': self.binlog_config.get('server_id', 1001),
            'blocking': True,
            'resume_stream': True,
            'log_file': self.current_position.log_file if self.current_position.log_file else None,
            'log_pos': self.current_position.log_pos if self.current_position.log_file else None,
            'auto_position': self.binlog_config.get('auto_position', False),
            'only_events': [DeleteRowsEvent, WriteRowsEvent, UpdateRowsEvent, RotateEvent],
            'only_tables': list(self.target_tables.keys()) if self.target_tables else None,
            'ignored_tables': self._get_ignored_tables(),
            'freeze_schema': True
        }
        
        # 如果没有指定文件，从最新位置开始
        if not self.current_position.log_file:
            latest_pos = self.get_latest_position()
            stream_settings['log_file'] = latest_pos.log_file
            stream_settings['log_pos'] = latest_pos.log_pos
            self.current_position = latest_pos
        
        self.stream = BinLogStreamReader(**stream_settings)
        logger.info(f"创建 binlog stream，起始位置: {self.current_position}")
    
    def _get_ignored_tables(self) -> List[str]:
        """获取需要忽略的表"""
        ignored = []
        
        # 系统表
        ignored.extend([
            'mysql.*',
            'information_schema.*',
            'performance_schema.*',
            'sys.*'
        ])
        
        # 配置中的忽略表
        config_ignored = self.config.get('tables', {}).get('ignored_tables', [])
        ignored.extend(config_ignored)
        
        return ignored
    
    def _process_binlog_event(self, binlog_event):
        """处理单个binlog事件"""
        self.stats['events_processed'] += 1
        self.stats['last_event_time'] = datetime.now()
        
        # 更新当前位置
        if hasattr(binlog_event, 'packet') and hasattr(binlog_event.packet, 'log_pos'):
            self.current_position.log_pos = binlog_event.packet.log_pos
        
        # 处理rotate事件
        if isinstance(binlog_event, RotateEvent):
            self.current_position.log_file = binlog_event.next_binlog
            self.current_position.log_pos = binlog_event.position
            logger.info(f"切换到新的 binlog 文件: {self.current_position}")
            return
        
        # 跳过格式描述事件
        if isinstance(binlog_event, FormatDescriptionEvent):
            return
        
        # 处理行事件
        if self._is_target_table_event(binlog_event):
            parsed_event = self.event_parser.parse_row_event(binlog_event)
            if parsed_event:
                # 添加到队列
                try:
                    self.event_queue.put(parsed_event, timeout=1)
                    
                    # 调用回调函数
                    for callback in self.event_callbacks:
                        try:
                            callback(parsed_event)
                        except Exception as e:
                            logger.error(f"事件回调失败: {e}")
                
                except Exception as e:
                    logger.warning(f"事件队列已满，丢弃事件: {e}")
        else:
            self.stats['events_filtered'] += 1
    
    def _is_target_table_event(self, binlog_event) -> bool:
        """判断是否为目标表事件"""
        if not hasattr(binlog_event, 'table') or not hasattr(binlog_event, 'schema'):
            return False
        
        table_key = f"{binlog_event.schema}.{binlog_event.table}"
        return table_key in self.target_tables
    
    def _should_checkpoint(self) -> bool:
        """判断是否需要保存检查点"""
        return time.time() - self.last_checkpoint_time > self.checkpoint_interval
    
    def _save_checkpoint(self):
        """保存检查点"""
        try:
            # 这里可以将位置信息保存到数据库或文件
            logger.debug(f"保存检查点: {self.current_position}")
            self.last_checkpoint_time = time.time()
        except Exception as e:
            logger.error(f"保存检查点失败: {e}")
    
    def get_events(self, timeout: float = 1.0) -> Generator[Dict, None, None]:
        """获取解析后的事件"""
        while self.running or not self.event_queue.empty():
            try:
                event = self.event_queue.get(timeout=timeout)
                yield event
                self.event_queue.task_done()
            except Empty:
                if not self.running:
                    break
                continue
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = self.stats.copy()
        stats['running'] = self.running
        stats['queue_size'] = self.event_queue.qsize()
        stats['current_position'] = self.current_position.to_dict() if self.current_position else None
        
        if stats['start_time']:
            uptime = datetime.now() - stats['start_time']
            stats['uptime_seconds'] = uptime.total_seconds()
            
            if stats['uptime_seconds'] > 0:
                stats['events_per_second'] = stats['events_processed'] / stats['uptime_seconds']
        
        return stats
    
    def wait_for_events(self, count: int, timeout: float = 30.0) -> List[Dict]:
        """等待指定数量的事件"""
        events = []
        start_time = time.time()
        
        while len(events) < count and time.time() - start_time < timeout:
            try:
                event = self.event_queue.get(timeout=1.0)
                events.append(event)
                self.event_queue.task_done()
            except Empty:
                continue
        
        return events
    
    def skip_to_latest(self):
        """跳转到最新位置"""
        latest_pos = self.get_latest_position()
        self.set_start_position(latest_pos)
        logger.info(f"跳转到最新位置: {latest_pos}")
    
    def replay_from_position(self, position: BinlogPosition, target_tables: List[str] = None):
        """从指定位置重放事件"""
        logger.info(f"从位置 {position} 开始重放事件")
        
        original_tables = self.target_tables.copy()
        
        # 如果指定了表，临时更新监控表
        if target_tables:
            self.target_tables = {table: original_tables.get(table, {}) 
                                for table in target_tables 
                                if table in original_tables}
        
        try:
            self.set_start_position(position)
            if not self.running:
                self.start_reading()
        finally:
            # 恢复原来的监控表配置
            self.target_tables = original_tables


def main():
    """测试函数"""
    import yaml
    
    # 测试配置
    config = {
        'mysql': {
            'source': {
                'host': 'localhost',
                'port': 3306,
                'user': 'binlog_reader',
                'password': 'password',
                'charset': 'utf8mb4',
                'binlog': {
                    'server_id': 1001,
                    'auto_position': True
                }
            }
        },
        'tables': {
            'target_tables': [
                {
                    'database': 'test',
                    'table': 'users',
                    'operations': ['INSERT', 'UPDATE', 'DELETE'],
                    'track_columns': ['id', 'username', 'email']
                }
            ]
        },
        'processing': {
            'queue_size': 1000,
            'checkpoint_interval': 60
        }
    }
    
    # 创建读取器
    reader = BinlogReader(config)
    
    # 添加事件处理回调
    def handle_event(event):
        print(f"收到事件: {event['operation']} {event['database']}.{event['table']}")
        if event['operation'] == 'UPDATE':
            print(f"  变更: {event.get('changes', {})}")
    
    reader.add_event_callback(handle_event)
    
    try:
        # 开始读取
        reader.start_reading()
        
        # 处理事件
        print("开始监听事件，按 Ctrl+C 停止...")
        for event in reader.get_events():
            print(f"处理事件: {event}")
    
    except KeyboardInterrupt:
        print("\n停止监听...")
    finally:
        reader.stop_reading()
        
        # 显示统计信息
        stats = reader.get_stats()
        print("\n统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == '__main__':
    main()