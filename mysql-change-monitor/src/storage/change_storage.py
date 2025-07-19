#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 变更存储模块
基于 Binary Log 的变更数据存储和查询
"""

import sqlite3
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger
import pymysql


class ChangeStorage:
    """变更数据存储器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.storage_type = config.get('storage', {}).get('type', 'sqlite')
        self.lock = threading.Lock()
        
        # 初始化存储
        if self.storage_type == 'sqlite':
            self._init_sqlite()
        elif self.storage_type == 'mysql':
            self._init_mysql()
        
        # 数据保留策略
        self.retention_days = config.get('storage', {}).get('retention', {}).get('days', 30)
        
    def _init_sqlite(self):
        """初始化SQLite存储"""
        db_file = self.config.get('storage', {}).get('sqlite', {}).get('database_file', 'data/changes.db')
        
        # 创建目录
        import os
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        
        self.sqlite_conn = sqlite3.connect(db_file, check_same_thread=False)
        self.sqlite_conn.row_factory = sqlite3.Row
        
        # 创建表结构
        self._create_sqlite_tables()
        logger.info(f"SQLite storage initialized: {db_file}")
    
    def _init_mysql(self):
        """初始化MySQL存储"""
        mysql_config = self.config.get('storage', {}).get('mysql', {})
        self.mysql_settings = {
            'host': mysql_config.get('host', 'localhost'),
            'port': mysql_config.get('port', 3306),
            'user': mysql_config.get('user'),
            'password': mysql_config.get('password'),
            'database': mysql_config.get('database'),
            'charset': 'utf8mb4'
        }
        
        # 测试连接并创建表
        self._create_mysql_tables()
        logger.info("MySQL storage initialized")
    
    def _create_sqlite_tables(self):
        """创建SQLite表结构"""
        cursor = self.sqlite_conn.cursor()
        
        # 变更记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                operation_type VARCHAR(10) NOT NULL,
                database_name VARCHAR(100) NOT NULL,
                table_name VARCHAR(100) NOT NULL,
                sql_statement TEXT,
                user_name VARCHAR(100),
                thread_id BIGINT,
                rows_affected INTEGER DEFAULT 0,
                execution_time INTEGER DEFAULT 0,
                before_values TEXT,
                after_values TEXT,
                source VARCHAR(20) DEFAULT 'binlog',
                binlog_file VARCHAR(100),
                binlog_pos BIGINT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS change_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                database_name VARCHAR(100) NOT NULL,
                table_name VARCHAR(100) NOT NULL,
                operation_type VARCHAR(10) NOT NULL,
                count INTEGER DEFAULT 0,
                UNIQUE(date, database_name, table_name, operation_type)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_timestamp ON changes(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_table ON changes(database_name, table_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_operation ON changes(operation_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_changes_binlog ON changes(binlog_file, binlog_pos)')
        
        self.sqlite_conn.commit()
        logger.info("SQLite tables created successfully")
    
    def _create_mysql_tables(self):
        """创建MySQL表结构"""
        try:
            connection = pymysql.connect(**self.mysql_settings)
            cursor = connection.cursor()
            
            # 变更记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS changes (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    operation_type VARCHAR(10) NOT NULL,
                    database_name VARCHAR(100) NOT NULL,
                    table_name VARCHAR(100) NOT NULL,
                    sql_statement TEXT,
                    user_name VARCHAR(100),
                    thread_id BIGINT,
                    rows_affected INT DEFAULT 0,
                    execution_time INT DEFAULT 0,
                    before_values JSON,
                    after_values JSON,
                    source VARCHAR(20) DEFAULT 'binlog',
                    binlog_file VARCHAR(100),
                    binlog_pos BIGINT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_table (database_name, table_name),
                    INDEX idx_operation (operation_type),
                    INDEX idx_binlog (binlog_file, binlog_pos)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # 统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS change_stats (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    database_name VARCHAR(100) NOT NULL,
                    table_name VARCHAR(100) NOT NULL,
                    operation_type VARCHAR(10) NOT NULL,
                    count INT DEFAULT 0,
                    UNIQUE KEY unique_stat (date, database_name, table_name, operation_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            connection.commit()
            cursor.close()
            connection.close()
            
            logger.info("MySQL tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create MySQL tables: {e}")
            raise
    
    def store_change(self, change_record: Dict):
        """存储变更记录"""
        with self.lock:
            try:
                if self.storage_type == 'sqlite':
                    self._store_change_sqlite(change_record)
                elif self.storage_type == 'mysql':
                    self._store_change_mysql(change_record)
                
                # 更新统计
                self._update_stats(change_record)
                
            except Exception as e:
                logger.error(f"Failed to store change record: {e}")
    
    def _store_change_sqlite(self, change_record: Dict):
        """存储到SQLite"""
        cursor = self.sqlite_conn.cursor()
        
        cursor.execute('''
            INSERT INTO changes (
                timestamp, operation_type, database_name, table_name,
                sql_statement, user_name, thread_id, rows_affected,
                execution_time, before_values, after_values, source,
                binlog_file, binlog_pos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            change_record['timestamp'],
            change_record['operation_type'],
            change_record['database_name'],
            change_record['table_name'],
            change_record.get('sql_statement'),
            change_record.get('user_name'),
            change_record.get('thread_id'),
            change_record.get('rows_affected', 0),
            change_record.get('execution_time', 0),
            json.dumps(change_record.get('before_values')) if change_record.get('before_values') else None,
            json.dumps(change_record.get('after_values')) if change_record.get('after_values') else None,
            change_record.get('source', 'binlog'),
            change_record.get('binlog_file'),
            change_record.get('binlog_pos')
        ))
        
        self.sqlite_conn.commit()
    
    def _store_change_mysql(self, change_record: Dict):
        """存储到MySQL"""
        connection = pymysql.connect(**self.mysql_settings)
        try:
            cursor = connection.cursor()
            
            cursor.execute('''
                INSERT INTO changes (
                    timestamp, operation_type, database_name, table_name,
                    sql_statement, user_name, thread_id, rows_affected,
                    execution_time, before_values, after_values, source,
                    binlog_file, binlog_pos
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                change_record['timestamp'],
                change_record['operation_type'],
                change_record['database_name'],
                change_record['table_name'],
                change_record.get('sql_statement'),
                change_record.get('user_name'),
                change_record.get('thread_id'),
                change_record.get('rows_affected', 0),
                change_record.get('execution_time', 0),
                json.dumps(change_record.get('before_values')) if change_record.get('before_values') else None,
                json.dumps(change_record.get('after_values')) if change_record.get('after_values') else None,
                change_record.get('source', 'binlog'),
                change_record.get('binlog_file'),
                change_record.get('binlog_pos')
            ))
            
            connection.commit()
        finally:
            connection.close()
    
    def _update_stats(self, change_record: Dict):
        """更新统计信息"""
        date = change_record['timestamp'].date()
        database_name = change_record['database_name']
        table_name = change_record['table_name']
        operation_type = change_record['operation_type']
        
        if self.storage_type == 'sqlite':
            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO change_stats 
                (date, database_name, table_name, operation_type, count)
                VALUES (?, ?, ?, ?, COALESCE(
                    (SELECT count FROM change_stats 
                     WHERE date=? AND database_name=? AND table_name=? AND operation_type=?), 0
                ) + 1)
            ''', (date, database_name, table_name, operation_type,
                  date, database_name, table_name, operation_type))
            self.sqlite_conn.commit()
    
    def get_changes(self, start_time=None, end_time=None, database=None, 
                   table=None, operation=None, limit=100) -> List[Dict]:
        """查询变更记录"""
        where_conditions = []
        params = []
        
        if start_time:
            where_conditions.append("timestamp >= ?")
            params.append(start_time)
        
        if end_time:
            where_conditions.append("timestamp <= ?")
            params.append(end_time)
        
        if database:
            where_conditions.append("database_name = ?")
            params.append(database)
        
        if table:
            where_conditions.append("table_name = ?")
            params.append(table)
        
        if operation:
            where_conditions.append("operation_type = ?")
            params.append(operation)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        if self.storage_type == 'sqlite':
            cursor = self.sqlite_conn.cursor()
            cursor.execute(f'''
                SELECT * FROM changes 
                WHERE {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', params + [limit])
            
            results = []
            for row in cursor.fetchall():
                record = dict(row)
                # 解析JSON字段
                if record['before_values']:
                    record['before_values'] = json.loads(record['before_values'])
                if record['after_values']:
                    record['after_values'] = json.loads(record['after_values'])
                results.append(record)
            
            return results
        
        return []
    
    def get_stats(self, days=7) -> Dict:
        """获取统计信息"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        if self.storage_type == 'sqlite':
            cursor = self.sqlite_conn.cursor()
            
            # 总变更数
            cursor.execute('''
                SELECT COUNT(*) as total_changes,
                       SUM(CASE WHEN operation_type='INSERT' THEN 1 ELSE 0 END) as inserts,
                       SUM(CASE WHEN operation_type='UPDATE' THEN 1 ELSE 0 END) as updates,
                       SUM(CASE WHEN operation_type='DELETE' THEN 1 ELSE 0 END) as deletes,
                       SUM(CASE WHEN operation_type='DDL' THEN 1 ELSE 0 END) as ddl_changes
                FROM changes 
                WHERE DATE(timestamp) >= ? AND DATE(timestamp) <= ?
            ''', (start_date, end_date))
            
            stats = dict(cursor.fetchone())
            
            # 按表统计
            cursor.execute('''
                SELECT database_name, table_name, operation_type, COUNT(*) as count
                FROM changes 
                WHERE DATE(timestamp) >= ? AND DATE(timestamp) <= ?
                GROUP BY database_name, table_name, operation_type
                ORDER BY count DESC
                LIMIT 20
            ''', (start_date, end_date))
            
            table_stats = [dict(row) for row in cursor.fetchall()]
            stats['table_stats'] = table_stats
            
            return stats
        
        return {}
    
    def cleanup_old_data(self):
        """清理过期数据"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        with self.lock:
            if self.storage_type == 'sqlite':
                cursor = self.sqlite_conn.cursor()
                cursor.execute('DELETE FROM changes WHERE timestamp < ?', (cutoff_date,))
                cursor.execute('DELETE FROM change_stats WHERE date < ?', (cutoff_date.date(),))
                self.sqlite_conn.commit()
                
                deleted_count = cursor.rowcount
                logger.info(f"Cleaned up {deleted_count} old change records")
    
    def get_binlog_position(self) -> Optional[tuple]:
        """获取最后处理的binlog位置"""
        if self.storage_type == 'sqlite':
            cursor = self.sqlite_conn.cursor()
            cursor.execute('''
                SELECT binlog_file, binlog_pos 
                FROM changes 
                WHERE binlog_file IS NOT NULL AND binlog_pos IS NOT NULL
                ORDER BY timestamp DESC 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            if result:
                return (result[0], result[1])
        
        return None
    
    def close(self):
        """关闭存储连接"""
        if self.storage_type == 'sqlite' and hasattr(self, 'sqlite_conn'):
            self.sqlite_conn.close()
            logger.info("SQLite connection closed")