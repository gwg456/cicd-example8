#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 审计监控主程序
基于 MariaDB Audit Plugin 实现指定表的精确审计
"""

import os
import re
import time
import yaml
import json
import threading
from datetime import datetime
from typing import Dict, List, Set, Optional
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from loguru import logger

from log_parser import AuditLogParser
from rule_engine import AuditRuleEngine
from alert_manager import AlertManager


class AuditFileHandler(FileSystemEventHandler):
    """审计日志文件监控处理器"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.last_position = 0
        
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.src_path == self.monitor.audit_log_file:
            self.monitor.process_new_log_entries()


class MySQLAuditMonitor:
    """MySQL 审计监控主类"""
    
    def __init__(self, config_file: str = 'config/audit_tables.conf'):
        self.config_file = config_file
        self.config = self._load_config()
        
        # 初始化组件
        self.log_parser = AuditLogParser()
        self.rule_engine = AuditRuleEngine(self.config)
        self.alert_manager = AlertManager(self.config)
        
        # 监控状态
        self.running = False
        self.observer = None
        self.file_handler = None
        
        # 审计配置
        self.target_tables = self._load_target_tables()
        self.audit_log_file = self.config.get('mysql', {}).get('audit_log_file', '/var/log/mysql/audit.log')
        self.last_position = 0
        
        # 统计信息
        self.stats = {
            'start_time': None,
            'total_events': 0,
            'matched_events': 0,
            'alerts_sent': 0,
            'last_event_time': None,
            'table_stats': {}
        }
        
        # 设置日志
        self._setup_logging()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {self.config_file}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise
    
    def _setup_logging(self):
        """设置日志配置"""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.config.get('logging', {}).get('file', '/var/log/mysql-audit/monitor.log')
        
        # 创建日志目录
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 配置loguru
        logger.remove()
        
        # 文件日志
        logger.add(
            log_file,
            rotation="100 MB",
            retention="30 days",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
        )
        
        # 控制台日志
        logger.add(
            lambda msg: print(msg, end=''),
            level=log_level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
        )
    
    def _load_target_tables(self) -> Dict[str, Dict]:
        """加载目标表配置"""
        target_tables = {}
        audit_config = self.config.get('audit_config', {})
        
        for table_config in audit_config.get('target_tables', []):
            database = table_config.get('database')
            table = table_config.get('table')
            
            if database and table:
                key = f"{database}.{table}"
                target_tables[key] = {
                    'database': database,
                    'table': table,
                    'operations': set(table_config.get('operations', ['INSERT', 'UPDATE', 'DELETE'])),
                    'sensitive_fields': table_config.get('sensitive_fields', []),
                    'alert_on_delete': table_config.get('alert_on_delete', False),
                    'alert_threshold': table_config.get('alert_threshold', 1000),
                    'high_priority': table_config.get('high_priority', False)
                }
        
        logger.info(f"加载了 {len(target_tables)} 个目标表配置")
        return target_tables
    
    def start(self):
        """启动审计监控"""
        if self.running:
            logger.warning("审计监控已经在运行")
            return
        
        logger.info("启动 MySQL 审计监控...")
        
        try:
            # 检查审计日志文件
            if not os.path.exists(self.audit_log_file):
                logger.error(f"审计日志文件不存在: {self.audit_log_file}")
                raise FileNotFoundError(f"审计日志文件不存在: {self.audit_log_file}")
            
            # 获取文件当前位置
            self.last_position = os.path.getsize(self.audit_log_file)
            
            # 设置文件监控
            self.file_handler = AuditFileHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                self.file_handler,
                path=os.path.dirname(self.audit_log_file),
                recursive=False
            )
            
            # 启动文件监控
            self.observer.start()
            
            # 处理现有日志（如果需要）
            if self.config.get('processing', {}).get('process_existing', False):
                self._process_existing_logs()
            
            self.running = True
            self.stats['start_time'] = datetime.now()
            
            logger.info("MySQL 审计监控启动成功")
            
        except Exception as e:
            logger.error(f"启动审计监控失败: {e}")
            raise
    
    def stop(self):
        """停止审计监控"""
        if not self.running:
            return
        
        logger.info("停止 MySQL 审计监控...")
        
        self.running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        logger.info("MySQL 审计监控已停止")
    
    def process_new_log_entries(self):
        """处理新的日志条目"""
        try:
            with open(self.audit_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # 移动到上次读取的位置
                f.seek(self.last_position)
                
                # 读取新内容
                new_content = f.read()
                if not new_content:
                    return
                
                # 更新文件位置
                self.last_position = f.tell()
                
                # 按行处理新日志
                lines = new_content.strip().split('\n')
                for line in lines:
                    if line.strip():
                        self._process_log_line(line)
                        
        except Exception as e:
            logger.error(f"处理新日志条目失败: {e}")
    
    def _process_existing_logs(self):
        """处理现有的日志文件"""
        logger.info("处理现有审计日志...")
        
        try:
            with open(self.audit_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_no, line in enumerate(f, 1):
                    if line.strip():
                        self._process_log_line(line.strip())
                    
                    # 每处理1000行显示进度
                    if line_no % 1000 == 0:
                        logger.info(f"已处理 {line_no} 行日志")
                
                self.last_position = f.tell()
                
        except Exception as e:
            logger.error(f"处理现有日志失败: {e}")
    
    def _process_log_line(self, line: str):
        """处理单行日志"""
        try:
            # 解析日志行
            log_entry = self.log_parser.parse_line(line)
            if not log_entry:
                return
            
            self.stats['total_events'] += 1
            self.stats['last_event_time'] = datetime.now()
            
            # 检查是否匹配目标表
            if self._should_audit_event(log_entry):
                self.stats['matched_events'] += 1
                
                # 更新表统计
                table_key = f"{log_entry.get('database')}.{log_entry.get('table')}"
                if table_key not in self.stats['table_stats']:
                    self.stats['table_stats'][table_key] = {
                        'total': 0, 'insert': 0, 'update': 0, 'delete': 0, 'ddl': 0
                    }
                
                self.stats['table_stats'][table_key]['total'] += 1
                operation = log_entry.get('operation', '').lower()
                if operation in self.stats['table_stats'][table_key]:
                    self.stats['table_stats'][table_key][operation] += 1
                
                # 应用规则引擎
                rule_results = self.rule_engine.evaluate(log_entry)
                
                # 处理告警
                if rule_results.get('should_alert', False):
                    self._send_alert(log_entry, rule_results)
                
                # 记录详细信息
                self._log_audit_event(log_entry, rule_results)
                
        except Exception as e:
            logger.error(f"处理日志行失败: {e}, 日志行: {line[:200]}...")
    
    def _should_audit_event(self, log_entry: Dict) -> bool:
        """判断是否应该审计此事件"""
        database = log_entry.get('database')
        table = log_entry.get('table')
        operation = log_entry.get('operation', '').upper()
        user = log_entry.get('user')
        
        if not database or not table:
            return False
        
        # 检查排除的表
        exclude_tables = self.config.get('audit_config', {}).get('exclude_tables', [])
        for exclude_pattern in exclude_tables:
            if self._match_pattern(f"{database}.{table}", exclude_pattern):
                return False
        
        # 检查用户过滤
        audit_users = self.config.get('audit_config', {}).get('audit_users', {})
        include_users = audit_users.get('include', [])
        exclude_users = audit_users.get('exclude', [])
        
        if include_users and user not in include_users:
            return False
        
        if exclude_users and user in exclude_users:
            return False
        
        # 检查目标表
        table_key = f"{database}.{table}"
        if table_key in self.target_tables:
            table_config = self.target_tables[table_key]
            return operation in table_config['operations']
        
        # 检查操作类型过滤
        operations_config = self.config.get('audit_config', {}).get('operations', {})
        if operation in ['CREATE', 'ALTER', 'DROP'] and operations_config.get('ddl', True):
            return True
        elif operation in ['INSERT', 'UPDATE', 'DELETE'] and operations_config.get('dml', True):
            return True
        
        return False
    
    def _match_pattern(self, name: str, pattern: str) -> bool:
        """匹配模式（支持通配符）"""
        import fnmatch
        return fnmatch.fnmatch(name.lower(), pattern.lower())
    
    def _send_alert(self, log_entry: Dict, rule_results: Dict):
        """发送告警"""
        try:
            self.alert_manager.send_alert(log_entry, rule_results)
            self.stats['alerts_sent'] += 1
            
            logger.warning(
                f"发送告警: {log_entry.get('operation')} "
                f"{log_entry.get('database')}.{log_entry.get('table')} "
                f"by {log_entry.get('user')}"
            )
            
        except Exception as e:
            logger.error(f"发送告警失败: {e}")
    
    def _log_audit_event(self, log_entry: Dict, rule_results: Dict):
        """记录审计事件"""
        event_info = {
            'timestamp': log_entry.get('timestamp'),
            'database': log_entry.get('database'),
            'table': log_entry.get('table'),
            'operation': log_entry.get('operation'),
            'user': log_entry.get('user'),
            'sql': log_entry.get('sql', '')[:200],  # 截断长SQL
            'rule_matched': rule_results.get('matched_rules', []),
            'alert_sent': rule_results.get('should_alert', False)
        }
        
        logger.info(f"审计事件: {json.dumps(event_info, ensure_ascii=False)}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        current_stats = self.stats.copy()
        
        if current_stats['start_time']:
            uptime = datetime.now() - current_stats['start_time']
            current_stats['uptime_seconds'] = uptime.total_seconds()
        
        current_stats['running'] = self.running
        current_stats['target_tables_count'] = len(self.target_tables)
        
        return current_stats
    
    def reload_config(self):
        """重新加载配置"""
        logger.info("重新加载配置...")
        
        try:
            old_config = self.config
            self.config = self._load_config()
            self.target_tables = self._load_target_tables()
            
            # 重新初始化规则引擎和告警管理器
            self.rule_engine = AuditRuleEngine(self.config)
            self.alert_manager = AlertManager(self.config)
            
            logger.info("配置重新加载成功")
            
        except Exception as e:
            logger.error(f"重新加载配置失败: {e}")
            self.config = old_config  # 恢复旧配置
            raise
    
    def get_target_tables(self) -> Dict:
        """获取目标表配置"""
        return self.target_tables.copy()
    
    def add_target_table(self, database: str, table: str, operations: List[str], **kwargs):
        """添加目标表"""
        key = f"{database}.{table}"
        self.target_tables[key] = {
            'database': database,
            'table': table,
            'operations': set(operations),
            'sensitive_fields': kwargs.get('sensitive_fields', []),
            'alert_on_delete': kwargs.get('alert_on_delete', False),
            'alert_threshold': kwargs.get('alert_threshold', 1000),
            'high_priority': kwargs.get('high_priority', False)
        }
        
        logger.info(f"添加目标表: {key}")
    
    def remove_target_table(self, database: str, table: str):
        """移除目标表"""
        key = f"{database}.{table}"
        if key in self.target_tables:
            del self.target_tables[key]
            logger.info(f"移除目标表: {key}")
        else:
            logger.warning(f"目标表不存在: {key}")


def main():
    """主函数"""
    import signal
    import sys
    
    def signal_handler(signum, frame):
        logger.info(f"接收到信号 {signum}，正在关闭...")
        if 'monitor' in globals():
            monitor.stop()
        sys.exit(0)
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建监控实例
    try:
        monitor = MySQLAuditMonitor()
        
        # 启动监控
        monitor.start()
        
        # 显示启动信息
        print("=" * 60)
        print("🔍 MySQL 指定表审计监控系统")
        print("=" * 60)
        print("✅ 监控已启动，正在实时监控指定表变更...")
        print(f"📊 监控表数量: {len(monitor.target_tables)}")
        print(f"📁 审计日志: {monitor.audit_log_file}")
        print("🔄 按 Ctrl+C 停止监控")
        print("=" * 60)
        
        # 主循环 - 显示统计信息
        while True:
            time.sleep(60)  # 每分钟显示一次统计
            
            stats = monitor.get_stats()
            uptime = stats.get('uptime_seconds', 0)
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            
            print(f"\n📊 运行状态 (运行时间: {hours}小时{minutes}分钟)")
            print(f"   总事件: {stats['total_events']}")
            print(f"   匹配事件: {stats['matched_events']}")
            print(f"   告警数: {stats['alerts_sent']}")
            
            if stats.get('last_event_time'):
                print(f"   最后事件: {stats['last_event_time']}")
            
            # 显示表统计
            if stats['table_stats']:
                print("   表统计:")
                for table, table_stats in stats['table_stats'].items():
                    print(f"     {table}: 总计={table_stats['total']}")
    
    except KeyboardInterrupt:
        logger.info("接收到键盘中断")
    except Exception as e:
        logger.error(f"监控程序错误: {e}")
    finally:
        if 'monitor' in locals():
            monitor.stop()


if __name__ == '__main__':
    main()