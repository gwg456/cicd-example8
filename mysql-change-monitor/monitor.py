#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 数据库变更监控系统 - 主程序
专注于监控数据库的增删改操作
"""

import os
import sys
import signal
import time
import yaml
from datetime import datetime
from typing import Dict, List
from loguru import logger

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from collectors.binlog_collector import BinlogCollector
from storage.change_storage import ChangeStorage
from alerts.email_alert import EmailAlert
from web.app import create_app


class ChangeMonitor:
    """数据库变更监控系统主类"""
    
    def __init__(self, config_file: str = 'config/monitor.conf'):
        self.config_file = config_file
        self.config = self._load_config()
        
        # 初始化组件
        self.binlog_collector = None
        self.storage = None
        self.email_alert = None
        self.web_app = None
        
        # 运行状态
        self.running = False
        
        # 设置日志
        self._setup_logging()
        
        # 变更统计
        self.stats = {
            'start_time': None,
            'total_changes': 0,
            'insert_count': 0,
            'update_count': 0,
            'delete_count': 0,
            'ddl_count': 0,
            'alert_count': 0,
            'last_change_time': None
        }
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """设置日志"""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.config.get('logging', {}).get('file', 'logs/monitor.log')
        
        # 创建日志目录
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置loguru
        logger.remove()  # 移除默认handler
        
        # 添加文件日志
        logger.add(
            log_file,
            rotation="100 MB",
            retention="30 days",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
        )
        
        # 添加控制台日志
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}"
        )
    
    def _initialize_components(self):
        """初始化各个组件"""
        logger.info("Initializing components...")
        
        # 初始化存储
        self.storage = ChangeStorage(self.config)
        
        # 初始化告警
        if self.config.get('alerts', {}).get('email', {}).get('enabled', False):
            self.email_alert = EmailAlert(self.config)
        
        # 初始化Binlog收集器
        self.binlog_collector = BinlogCollector(self.config)
        self.binlog_collector.add_change_callback(self._handle_change)
        
        logger.info("Components initialized successfully")
    
    def _handle_change(self, change_record: Dict):
        """处理变更事件"""
        try:
            # 更新统计信息
            self._update_stats(change_record)
            
            # 存储变更记录
            if self.storage:
                self.storage.store_change(change_record)
            
            # 检查是否需要告警
            if self._should_alert(change_record):
                self._send_alert(change_record)
                self.stats['alert_count'] += 1
            
            # 记录变更信息
            self._log_change(change_record)
            
        except Exception as e:
            logger.error(f"Error handling change: {e}")
    
    def _update_stats(self, change_record: Dict):
        """更新统计信息"""
        self.stats['total_changes'] += 1
        self.stats['last_change_time'] = change_record['timestamp']
        
        operation = change_record['operation_type'].upper()
        if operation == 'INSERT':
            self.stats['insert_count'] += 1
        elif operation == 'UPDATE':
            self.stats['update_count'] += 1
        elif operation == 'DELETE':
            self.stats['delete_count'] += 1
        elif operation == 'DDL':
            self.stats['ddl_count'] += 1
    
    def _should_alert(self, change_record: Dict) -> bool:
        """判断是否需要告警"""
        # 检查关键表
        critical_tables = self.config.get('alerts', {}).get('critical_tables', [])
        table_name = change_record.get('table_name', '')
        
        if table_name in critical_tables:
            return True
        
        # 检查DDL操作
        if change_record['operation_type'] == 'DDL':
            return True
        
        # 检查大批量操作
        bulk_threshold = self.config.get('alerts', {}).get('bulk_threshold', 1000)
        rows_affected = change_record.get('rows_affected', 0)
        
        if rows_affected >= bulk_threshold:
            return True
        
        # 检查DELETE操作
        if change_record['operation_type'] == 'DELETE':
            return True
        
        return False
    
    def _send_alert(self, change_record: Dict):
        """发送告警"""
        if self.email_alert:
            try:
                self.email_alert.send_change_alert(change_record)
                logger.info(f"Alert sent for change: {change_record['operation_type']} {change_record['table_name']}")
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
    
    def _log_change(self, change_record: Dict):
        """记录变更信息"""
        operation = change_record['operation_type']
        database = change_record['database_name']
        table = change_record['table_name']
        timestamp = change_record['timestamp']
        
        if operation == 'DDL':
            logger.info(f"DDL变更: {database}.{table} - {change_record.get('sql_statement', '')}")
        else:
            before = change_record.get('before_values')
            after = change_record.get('after_values')
            
            if operation == 'INSERT':
                logger.info(f"数据插入: {database}.{table}")
            elif operation == 'UPDATE':
                logger.info(f"数据更新: {database}.{table}")
            elif operation == 'DELETE':
                logger.info(f"数据删除: {database}.{table}")
    
    def start(self):
        """启动监控系统"""
        if self.running:
            logger.warning("Monitor is already running")
            return
        
        logger.info("Starting MySQL Change Monitor...")
        
        try:
            # 初始化组件
            self._initialize_components()
            
            # 启动Binlog收集器
            self.binlog_collector.start()
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            logger.info("MySQL Change Monitor started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start monitor: {e}")
            raise
    
    def stop(self):
        """停止监控系统"""
        if not self.running:
            return
        
        logger.info("Stopping MySQL Change Monitor...")
        
        # 停止收集器
        if self.binlog_collector:
            self.binlog_collector.stop()
        
        # 关闭存储
        if self.storage:
            self.storage.close()
        
        self.running = False
        logger.info("MySQL Change Monitor stopped")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        current_stats = self.stats.copy()
        
        if current_stats['start_time']:
            uptime = datetime.now() - current_stats['start_time']
            current_stats['uptime_seconds'] = uptime.total_seconds()
        
        # 添加收集器统计信息
        if self.binlog_collector:
            collector_stats = self.binlog_collector.get_stats()
            current_stats.update(collector_stats)
        
        current_stats['running'] = self.running
        return current_stats
    
    def get_changes(self, start_time=None, end_time=None, table=None, limit=100) -> List[Dict]:
        """查询变更记录"""
        if not self.storage:
            return []
        
        return self.storage.get_changes(
            start_time=start_time,
            end_time=end_time,
            table=table,
            limit=limit
        )


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"Received signal {signum}, shutting down...")
    if 'monitor' in globals():
        monitor.stop()
    sys.exit(0)


def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建监控实例
    global monitor
    monitor = ChangeMonitor()
    
    try:
        # 启动监控
        monitor.start()
        
        # 显示启动信息
        print("=" * 60)
        print("🔍 MySQL 数据库变更监控系统")
        print("=" * 60)
        print("✅ 监控已启动，正在实时监控数据库变更...")
        print("📊 Web界面: http://localhost:8080")
        print("📋 API接口: http://localhost:8080/api/")
        print("🔄 按 Ctrl+C 停止监控")
        print("=" * 60)
        
        # 主循环 - 显示统计信息
        while True:
            time.sleep(30)  # 每30秒显示一次统计
            
            stats = monitor.get_stats()
            uptime = stats.get('uptime_seconds', 0)
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            
            print(f"\n📊 运行状态 (运行时间: {hours}小时{minutes}分钟)")
            print(f"   总变更: {stats['total_changes']}")
            print(f"   插入: {stats['insert_count']} | 更新: {stats['update_count']} | 删除: {stats['delete_count']} | DDL: {stats['ddl_count']}")
            print(f"   告警: {stats['alert_count']}")
            
            if stats.get('last_change_time'):
                print(f"   最后变更: {stats['last_change_time']}")
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        monitor.stop()


if __name__ == '__main__':
    main()