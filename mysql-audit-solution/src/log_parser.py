#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 审计日志解析器
解析 MariaDB Audit Plugin 生成的审计日志
"""

import re
import json
import csv
from datetime import datetime
from typing import Dict, Optional, List
from loguru import logger


class AuditLogParser:
    """审计日志解析器"""
    
    def __init__(self):
        # MariaDB Audit Plugin 日志格式正则
        self.csv_pattern = re.compile(
            r'(\d{8}\s\d{2}:\d{2}:\d{2}),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),(.*)$'
        )
        
        # SQL语句解析正则
        self.sql_patterns = {
            'select': re.compile(r'SELECT.*?FROM\s+`?(\w+)`?\.`?(\w+)`?', re.IGNORECASE | re.DOTALL),
            'insert': re.compile(r'INSERT\s+INTO\s+`?(\w+)`?\.`?(\w+)`?', re.IGNORECASE),
            'update': re.compile(r'UPDATE\s+`?(\w+)`?\.`?(\w+)`?', re.IGNORECASE),
            'delete': re.compile(r'DELETE\s+FROM\s+`?(\w+)`?\.`?(\w+)`?', re.IGNORECASE),
            'create': re.compile(r'CREATE\s+TABLE\s+`?(\w+)`?\.`?(\w+)`?', re.IGNORECASE),
            'alter': re.compile(r'ALTER\s+TABLE\s+`?(\w+)`?\.`?(\w+)`?', re.IGNORECASE),
            'drop': re.compile(r'DROP\s+TABLE\s+`?(\w+)`?\.`?(\w+)`?', re.IGNORECASE),
        }
        
        # 操作类型映射
        self.operation_mapping = {
            'QUERY': 'QUERY',
            'CONNECT': 'CONNECT',
            'DISCONNECT': 'DISCONNECT',
            'TABLE': 'TABLE',
            'CREATE': 'CREATE',
            'ALTER': 'ALTER',
            'DROP': 'DROP',
            'INSERT': 'INSERT',
            'UPDATE': 'UPDATE',
            'DELETE': 'DELETE',
            'SELECT': 'SELECT'
        }
    
    def parse_line(self, line: str) -> Optional[Dict]:
        """解析单行日志"""
        try:
            # 尝试解析CSV格式
            log_entry = self._parse_csv_format(line)
            if log_entry:
                return log_entry
            
            # 尝试解析JSON格式
            log_entry = self._parse_json_format(line)
            if log_entry:
                return log_entry
            
            return None
            
        except Exception as e:
            logger.debug(f"解析日志行失败: {e}, 行内容: {line[:100]}...")
            return None
    
    def _parse_csv_format(self, line: str) -> Optional[Dict]:
        """解析CSV格式的审计日志"""
        try:
            # MariaDB Audit Plugin CSV格式:
            # timestamp,serverhost,username,host,connectionid,queryid,operation,database,object,retcode
            
            # 使用CSV模块解析，处理引号和逗号
            reader = csv.reader([line])
            fields = next(reader)
            
            if len(fields) < 9:
                return None
            
            timestamp_str = fields[0]
            server_host = fields[1]
            username = fields[2]
            host = fields[3]
            connection_id = fields[4]
            query_id = fields[5]
            operation = fields[6]
            database = fields[7]
            object_name = fields[8]
            retcode = fields[9] if len(fields) > 9 else '0'
            
            # 解析时间戳
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d %H:%M:%S')
            except ValueError:
                timestamp = datetime.now()
            
            # 创建基础日志条目
            log_entry = {
                'timestamp': timestamp,
                'server_host': server_host,
                'user': username,
                'host': host,
                'connection_id': connection_id,
                'query_id': query_id,
                'operation': operation.upper(),
                'database': database,
                'object': object_name,
                'return_code': retcode,
                'source': 'mariadb_audit'
            }
            
            # 如果是QUERY操作，解析SQL语句
            if operation.upper() == 'QUERY' and len(fields) > 10:
                sql_statement = fields[10]
                log_entry['sql'] = sql_statement
                
                # 解析SQL获取真实操作类型和表信息
                parsed_sql = self._parse_sql_statement(sql_statement)
                if parsed_sql:
                    log_entry.update(parsed_sql)
            
            # 如果是TABLE操作，直接使用对象名作为表名
            elif operation.upper() == 'TABLE':
                log_entry['table'] = object_name
            
            return log_entry
            
        except Exception as e:
            logger.debug(f"CSV格式解析失败: {e}")
            return None
    
    def _parse_json_format(self, line: str) -> Optional[Dict]:
        """解析JSON格式的审计日志"""
        try:
            data = json.loads(line)
            
            # 标准化字段名
            log_entry = {
                'timestamp': self._parse_timestamp(data.get('timestamp')),
                'server_host': data.get('server_host', ''),
                'user': data.get('user', data.get('username', '')),
                'host': data.get('host', ''),
                'connection_id': data.get('connection_id', ''),
                'query_id': data.get('query_id', ''),
                'operation': data.get('operation', '').upper(),
                'database': data.get('database', ''),
                'object': data.get('object', ''),
                'return_code': data.get('retcode', '0'),
                'source': 'json_audit'
            }
            
            # 处理SQL语句
            if 'sql' in data or 'query' in data:
                sql_statement = data.get('sql', data.get('query', ''))
                log_entry['sql'] = sql_statement
                
                # 解析SQL
                parsed_sql = self._parse_sql_statement(sql_statement)
                if parsed_sql:
                    log_entry.update(parsed_sql)
            
            return log_entry
            
        except json.JSONDecodeError:
            return None
        except Exception as e:
            logger.debug(f"JSON格式解析失败: {e}")
            return None
    
    def _parse_sql_statement(self, sql: str) -> Optional[Dict]:
        """解析SQL语句，提取操作类型、数据库和表名"""
        if not sql or not sql.strip():
            return None
        
        sql = sql.strip()
        result = {}
        
        # 检测操作类型并提取表信息
        for operation, pattern in self.sql_patterns.items():
            match = pattern.search(sql)
            if match:
                result['operation'] = operation.upper()
                
                if len(match.groups()) >= 2:
                    # 数据库.表名格式
                    database = match.group(1)
                    table = match.group(2)
                    result['database'] = database
                    result['table'] = table
                elif len(match.groups()) >= 1:
                    # 只有表名
                    result['table'] = match.group(1)
                
                break
        
        # 特殊处理一些SQL类型
        sql_upper = sql.upper()
        
        # 检测USE语句
        use_match = re.search(r'USE\s+`?(\w+)`?', sql_upper)
        if use_match:
            result['operation'] = 'USE'
            result['database'] = use_match.group(1)
        
        # 检测SHOW语句
        elif sql_upper.startswith('SHOW'):
            result['operation'] = 'SHOW'
        
        # 检测DESCRIBE/DESC语句
        elif sql_upper.startswith(('DESCRIBE', 'DESC')):
            result['operation'] = 'DESCRIBE'
            desc_match = re.search(r'DESC(?:RIBE)?\s+`?(\w+)`?(?:\.`?(\w+)`?)?', sql_upper)
            if desc_match:
                if desc_match.group(2):  # database.table
                    result['database'] = desc_match.group(1)
                    result['table'] = desc_match.group(2)
                else:  # 只有表名
                    result['table'] = desc_match.group(1)
        
        # 检测GRANT/REVOKE语句
        elif sql_upper.startswith(('GRANT', 'REVOKE')):
            result['operation'] = 'GRANT' if sql_upper.startswith('GRANT') else 'REVOKE'
        
        return result if result else None
    
    def _parse_timestamp(self, timestamp_str) -> datetime:
        """解析时间戳"""
        if not timestamp_str:
            return datetime.now()
        
        # 尝试多种时间格式
        formats = [
            '%Y%m%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S.%f'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # 如果都失败，返回当前时间
        logger.warning(f"无法解析时间戳: {timestamp_str}")
        return datetime.now()
    
    def parse_batch(self, lines: List[str]) -> List[Dict]:
        """批量解析日志行"""
        results = []
        
        for line in lines:
            parsed = self.parse_line(line)
            if parsed:
                results.append(parsed)
        
        return results
    
    def extract_table_operations(self, log_entries: List[Dict]) -> Dict[str, List[Dict]]:
        """按表分组提取操作"""
        table_operations = {}
        
        for entry in log_entries:
            database = entry.get('database', '')
            table = entry.get('table', '')
            
            if database and table:
                key = f"{database}.{table}"
                if key not in table_operations:
                    table_operations[key] = []
                table_operations[key].append(entry)
        
        return table_operations
    
    def filter_operations(self, log_entries: List[Dict], 
                         databases: List[str] = None,
                         tables: List[str] = None,
                         operations: List[str] = None,
                         users: List[str] = None) -> List[Dict]:
        """根据条件过滤日志条目"""
        filtered = []
        
        for entry in log_entries:
            # 数据库过滤
            if databases and entry.get('database') not in databases:
                continue
            
            # 表过滤
            if tables:
                table_key = f"{entry.get('database', '')}.{entry.get('table', '')}"
                if table_key not in tables and entry.get('table') not in tables:
                    continue
            
            # 操作类型过滤
            if operations and entry.get('operation') not in operations:
                continue
            
            # 用户过滤
            if users and entry.get('user') not in users:
                continue
            
            filtered.append(entry)
        
        return filtered


def main():
    """测试函数"""
    parser = AuditLogParser()
    
    # 测试CSV格式日志
    csv_log = '20241201 10:30:15,localhost,testuser,127.0.0.1,123,456,QUERY,testdb,,"0","SELECT * FROM users WHERE id=1"'
    
    result = parser.parse_line(csv_log)
    if result:
        print("CSV解析结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    
    # 测试JSON格式日志
    json_log = '{"timestamp": "2024-12-01 10:30:15", "user": "testuser", "operation": "QUERY", "database": "testdb", "sql": "INSERT INTO orders (id, amount) VALUES (1, 100)"}'
    
    result = parser.parse_line(json_log)
    if result:
        print("\nJSON解析结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")


if __name__ == '__main__':
    main()