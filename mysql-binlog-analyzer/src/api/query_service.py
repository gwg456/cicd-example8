#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询服务
提供MySQL binlog数据变更的查询接口
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from loguru import logger
import pymysql

from ..utils.mysql_helper import MySQLHelper


@dataclass
class QueryCriteria:
    """查询条件"""
    database: Optional[str] = None
    table: Optional[str] = None
    operations: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    primary_key: Optional[Dict] = None
    limit: int = 100
    offset: int = 0
    order_by: str = 'timestamp'
    order_desc: bool = True


@dataclass 
class ChangeRecord:
    """变更记录"""
    id: str
    timestamp: datetime
    database: str
    table: str
    operation: str
    primary_key: Dict
    old_data: Optional[Dict] = None
    new_data: Optional[Dict] = None
    changes: Optional[Dict] = None
    binlog_file: Optional[str] = None
    binlog_position: Optional[int] = None


class QueryService:
    """查询服务类"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.storage_config = config['mysql']['storage']
        self.mysql_helper = MySQLHelper(self.storage_config)
        
        # 表名配置
        self.tables = {
            'changes': 'binlog_changes',
            'statistics': 'binlog_statistics',
            'position': 'binlog_position'
        }
        
        logger.info("初始化查询服务")
    
    def get_table_changes(self, 
                         database: str, 
                         table: str,
                         operations: Optional[List[str]] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[ChangeRecord]:
        """获取指定表的变更记录"""
        criteria = QueryCriteria(
            database=database,
            table=table,
            operations=operations,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        
        return self.query_changes(criteria)
    
    def query_changes(self, criteria: QueryCriteria) -> List[ChangeRecord]:
        """根据条件查询变更记录"""
        try:
            sql, params = self._build_query_sql(criteria)
            
            with self.mysql_helper.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(sql, params)
                    results = cursor.fetchall()
            
            return [self._row_to_change_record(row) for row in results]
        
        except Exception as e:
            logger.error(f"查询变更记录失败: {e}")
            return []
    
    def _build_query_sql(self, criteria: QueryCriteria) -> tuple[str, list]:
        """构建查询SQL"""
        base_sql = f"""
        SELECT 
            id, timestamp, database_name, table_name, operation,
            primary_key, old_data, new_data, changes,
            binlog_file, binlog_position
        FROM {self.tables['changes']}
        WHERE 1=1
        """
        
        params = []
        conditions = []
        
        # 数据库条件
        if criteria.database:
            conditions.append("database_name = %s")
            params.append(criteria.database)
        
        # 表条件
        if criteria.table:
            conditions.append("table_name = %s")
            params.append(criteria.table)
        
        # 操作类型条件
        if criteria.operations:
            placeholders = ','.join(['%s'] * len(criteria.operations))
            conditions.append(f"operation IN ({placeholders})")
            params.extend(criteria.operations)
        
        # 时间范围条件
        if criteria.start_time:
            conditions.append("timestamp >= %s")
            params.append(criteria.start_time)
        
        if criteria.end_time:
            conditions.append("timestamp <= %s")
            params.append(criteria.end_time)
        
        # 主键条件
        if criteria.primary_key:
            conditions.append("JSON_CONTAINS(primary_key, %s)")
            params.append(json.dumps(criteria.primary_key))
        
        # 添加条件
        if conditions:
            base_sql += " AND " + " AND ".join(conditions)
        
        # 排序
        order_direction = "DESC" if criteria.order_desc else "ASC"
        base_sql += f" ORDER BY {criteria.order_by} {order_direction}"
        
        # 分页
        base_sql += " LIMIT %s OFFSET %s"
        params.extend([criteria.limit, criteria.offset])
        
        return base_sql, params
    
    def _row_to_change_record(self, row: Dict) -> ChangeRecord:
        """将数据库行转换为变更记录对象"""
        return ChangeRecord(
            id=row['id'],
            timestamp=row['timestamp'],
            database=row['database_name'],
            table=row['table_name'],
            operation=row['operation'],
            primary_key=json.loads(row['primary_key']) if row['primary_key'] else {},
            old_data=json.loads(row['old_data']) if row['old_data'] else None,
            new_data=json.loads(row['new_data']) if row['new_data'] else None,
            changes=json.loads(row['changes']) if row['changes'] else None,
            binlog_file=row['binlog_file'],
            binlog_position=row['binlog_position']
        )
    
    def get_operations(self,
                      database: str,
                      table: str,
                      operation: str,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      limit: int = 100) -> List[ChangeRecord]:
        """获取指定操作类型的记录"""
        return self.get_table_changes(
            database=database,
            table=table,
            operations=[operation],
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
    
    def get_inserts(self, database: str, table: str, **kwargs) -> List[ChangeRecord]:
        """获取INSERT操作记录"""
        return self.get_operations(database, table, 'INSERT', **kwargs)
    
    def get_updates(self, database: str, table: str, **kwargs) -> List[ChangeRecord]:
        """获取UPDATE操作记录"""
        return self.get_operations(database, table, 'UPDATE', **kwargs)
    
    def get_deletes(self, database: str, table: str, **kwargs) -> List[ChangeRecord]:
        """获取DELETE操作记录"""
        return self.get_operations(database, table, 'DELETE', **kwargs)
    
    def get_update_diffs(self,
                        database: str,
                        table: str,
                        primary_key_value: Any = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        limit: int = 100) -> List[Dict]:
        """获取UPDATE操作的变更对比"""
        criteria = QueryCriteria(
            database=database,
            table=table,
            operations=['UPDATE'],
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        if primary_key_value is not None:
            # 假设主键是'id'，实际使用时需要根据表配置确定
            criteria.primary_key = {'id': primary_key_value}
        
        changes = self.query_changes(criteria)
        
        # 格式化为对比格式
        diffs = []
        for change in changes:
            if change.changes:
                diff = {
                    'change_id': change.id,
                    'timestamp': change.timestamp.isoformat(),
                    'operation': change.operation,
                    'primary_key': change.primary_key,
                    'changes': change.changes
                }
                diffs.append(diff)
        
        return diffs
    
    def get_record_history(self,
                          database: str,
                          table: str,
                          primary_key: Dict,
                          limit: int = 50) -> List[ChangeRecord]:
        """获取特定记录的变更历史"""
        criteria = QueryCriteria(
            database=database,
            table=table,
            primary_key=primary_key,
            limit=limit,
            order_by='timestamp',
            order_desc=True
        )
        
        return self.query_changes(criteria)
    
    def get_table_stats(self,
                       database: str,
                       table: str,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> Dict:
        """获取表变更统计信息"""
        try:
            # 设置默认时间范围（最近7天）
            if not end_time:
                end_time = datetime.now()
            if not start_time:
                start_time = end_time - timedelta(days=7)
            
            sql = f"""
            SELECT 
                operation,
                COUNT(*) as count,
                DATE(timestamp) as date
            FROM {self.tables['changes']}
            WHERE database_name = %s 
                AND table_name = %s
                AND timestamp BETWEEN %s AND %s
            GROUP BY operation, DATE(timestamp)
            ORDER BY date, operation
            """
            
            with self.mysql_helper.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(sql, [database, table, start_time, end_time])
                    results = cursor.fetchall()
            
            # 统计总数
            total_sql = f"""
            SELECT 
                operation,
                COUNT(*) as count
            FROM {self.tables['changes']}
            WHERE database_name = %s 
                AND table_name = %s
                AND timestamp BETWEEN %s AND %s
            GROUP BY operation
            """
            
            with self.mysql_helper.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(total_sql, [database, table, start_time, end_time])
                    total_results = cursor.fetchall()
            
            # 整理统计数据
            stats = {
                'total_changes': sum(row['count'] for row in total_results),
                'operations': {row['operation']: row['count'] for row in total_results},
                'daily_stats': self._group_daily_stats(results),
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
            
            return stats
        
        except Exception as e:
            logger.error(f"获取表统计失败: {e}")
            return {}
    
    def _group_daily_stats(self, results: List[Dict]) -> Dict:
        """整理每日统计数据"""
        daily_stats = {}
        
        for row in results:
            date_str = row['date'].strftime('%Y-%m-%d')
            operation = row['operation']
            count = row['count']
            
            if date_str not in daily_stats:
                daily_stats[date_str] = {}
            
            daily_stats[date_str][operation] = count
        
        return daily_stats
    
    def search_changes(self,
                      keyword: str,
                      databases: Optional[List[str]] = None,
                      tables: Optional[List[str]] = None,
                      operations: Optional[List[str]] = None,
                      limit: int = 100) -> List[ChangeRecord]:
        """搜索包含关键字的变更记录"""
        try:
            # 构建搜索SQL
            base_sql = f"""
            SELECT 
                id, timestamp, database_name, table_name, operation,
                primary_key, old_data, new_data, changes,
                binlog_file, binlog_position
            FROM {self.tables['changes']}
            WHERE (
                old_data LIKE %s OR 
                new_data LIKE %s OR 
                changes LIKE %s
            )
            """
            
            params = [f'%{keyword}%', f'%{keyword}%', f'%{keyword}%']
            conditions = []
            
            # 数据库过滤
            if databases:
                placeholders = ','.join(['%s'] * len(databases))
                conditions.append(f"database_name IN ({placeholders})")
                params.extend(databases)
            
            # 表过滤
            if tables:
                placeholders = ','.join(['%s'] * len(tables))
                conditions.append(f"table_name IN ({placeholders})")
                params.extend(tables)
            
            # 操作类型过滤
            if operations:
                placeholders = ','.join(['%s'] * len(operations))
                conditions.append(f"operation IN ({placeholders})")
                params.extend(operations)
            
            if conditions:
                base_sql += " AND " + " AND ".join(conditions)
            
            base_sql += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            with self.mysql_helper.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(base_sql, params)
                    results = cursor.fetchall()
            
            return [self._row_to_change_record(row) for row in results]
        
        except Exception as e:
            logger.error(f"搜索变更记录失败: {e}")
            return []
    
    def get_database_tables(self, database: str) -> List[str]:
        """获取数据库中有变更记录的表列表"""
        try:
            sql = f"""
            SELECT DISTINCT table_name
            FROM {self.tables['changes']}
            WHERE database_name = %s
            ORDER BY table_name
            """
            
            with self.mysql_helper.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, [database])
                    results = cursor.fetchall()
            
            return [row[0] for row in results]
        
        except Exception as e:
            logger.error(f"获取数据库表列表失败: {e}")
            return []
    
    def get_all_databases(self) -> List[str]:
        """获取所有有变更记录的数据库列表"""
        try:
            sql = f"""
            SELECT DISTINCT database_name
            FROM {self.tables['changes']}
            ORDER BY database_name
            """
            
            with self.mysql_helper.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    results = cursor.fetchall()
            
            return [row[0] for row in results]
        
        except Exception as e:
            logger.error(f"获取数据库列表失败: {e}")
            return []
    
    def analyze_table_activity(self,
                              database: str,
                              table: str,
                              days: int = 7) -> Dict:
        """分析表的活动情况"""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            # 按小时统计
            hourly_sql = f"""
            SELECT 
                HOUR(timestamp) as hour,
                operation,
                COUNT(*) as count
            FROM {self.tables['changes']}
            WHERE database_name = %s 
                AND table_name = %s
                AND timestamp BETWEEN %s AND %s
            GROUP BY HOUR(timestamp), operation
            ORDER BY hour, operation
            """
            
            with self.mysql_helper.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(hourly_sql, [database, table, start_time, end_time])
                    hourly_results = cursor.fetchall()
            
            # 最频繁的操作
            frequent_sql = f"""
            SELECT 
                operation,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (
                    SELECT COUNT(*) 
                    FROM {self.tables['changes']} 
                    WHERE database_name = %s AND table_name = %s 
                    AND timestamp BETWEEN %s AND %s
                ), 2) as percentage
            FROM {self.tables['changes']}
            WHERE database_name = %s 
                AND table_name = %s
                AND timestamp BETWEEN %s AND %s
            GROUP BY operation
            ORDER BY count DESC
            """
            
            with self.mysql_helper.get_connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute(frequent_sql, [database, table, start_time, end_time, 
                                                database, table, start_time, end_time])
                    frequent_results = cursor.fetchall()
            
            # 整理结果
            analysis = {
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days
                },
                'hourly_distribution': self._group_hourly_stats(hourly_results),
                'operation_frequency': list(frequent_results),
                'peak_hours': self._find_peak_hours(hourly_results),
                'total_changes': sum(row['count'] for row in frequent_results)
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"分析表活动失败: {e}")
            return {}
    
    def _group_hourly_stats(self, results: List[Dict]) -> Dict:
        """整理小时级统计数据"""
        hourly_stats = {}
        
        for row in results:
            hour = row['hour']
            operation = row['operation']
            count = row['count']
            
            if hour not in hourly_stats:
                hourly_stats[hour] = {}
            
            hourly_stats[hour][operation] = count
        
        return hourly_stats
    
    def _find_peak_hours(self, results: List[Dict]) -> List[int]:
        """找出活动高峰时段"""
        hour_totals = {}
        
        for row in results:
            hour = row['hour']
            count = row['count']
            
            if hour not in hour_totals:
                hour_totals[hour] = 0
            hour_totals[hour] += count
        
        # 按活动量排序，返回前3个小时
        sorted_hours = sorted(hour_totals.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]
    
    def get_recent_changes(self,
                          hours: int = 1,
                          databases: Optional[List[str]] = None,
                          tables: Optional[List[str]] = None,
                          limit: int = 100) -> List[ChangeRecord]:
        """获取最近的变更记录"""
        start_time = datetime.now() - timedelta(hours=hours)
        
        criteria = QueryCriteria(
            start_time=start_time,
            limit=limit,
            order_by='timestamp',
            order_desc=True
        )
        
        # 添加数据库过滤
        if databases and len(databases) == 1:
            criteria.database = databases[0]
        
        # 添加表过滤
        if tables and len(tables) == 1:
            criteria.table = tables[0]
        
        changes = self.query_changes(criteria)
        
        # 如果有多个数据库或表的过滤，需要在这里进一步过滤
        if databases and len(databases) > 1:
            changes = [c for c in changes if c.database in databases]
        
        if tables and len(tables) > 1:
            changes = [c for c in changes if c.table in tables]
        
        return changes


def main():
    """测试函数"""
    # 测试配置
    config = {
        'mysql': {
            'storage': {
                'host': 'localhost',
                'port': 3306,
                'user': 'storage_user',
                'password': 'password',
                'database': 'binlog_analysis',
                'charset': 'utf8mb4'
            }
        }
    }
    
    # 创建查询服务
    query_service = QueryService(config)
    
    print("查询服务初始化完成")
    
    # 测试查询
    try:
        # 查询最近的变更
        recent_changes = query_service.get_recent_changes(hours=24, limit=10)
        print(f"最近24小时变更数量: {len(recent_changes)}")
        
        # 查询特定表的变更
        if recent_changes:
            first_change = recent_changes[0]
            table_changes = query_service.get_table_changes(
                database=first_change.database,
                table=first_change.table,
                limit=5
            )
            print(f"表 {first_change.database}.{first_change.table} 的变更数量: {len(table_changes)}")
            
            # 获取统计信息
            stats = query_service.get_table_stats(
                database=first_change.database,
                table=first_change.table
            )
            print(f"统计信息: {stats}")
    
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == '__main__':
    main()