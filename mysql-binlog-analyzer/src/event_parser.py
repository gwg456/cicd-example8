#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binlog 事件解析器
解析MySQL binlog事件，提取数据变更信息
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pymysqlreplication.row_event import (
    DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent
)
from loguru import logger


class BinlogEventParser:
    """Binlog 事件解析器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.target_tables = self._load_target_tables()
        
        # 数据类型处理器
        self.type_handlers = {
            'datetime': self._handle_datetime,
            'date': self._handle_date,
            'time': self._handle_time,
            'timestamp': self._handle_timestamp,
            'decimal': self._handle_decimal,
            'json': self._handle_json,
            'binary': self._handle_binary
        }
        
        logger.info(f"初始化事件解析器，监控 {len(self.target_tables)} 个表")
    
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
                    'primary_key': table_config.get('primary_key', 'id'),
                    'sensitive_columns': table_config.get('sensitive_columns', [])
                }
        
        return target_tables
    
    def parse_row_event(self, binlog_event) -> Optional[Dict]:
        """解析行事件"""
        try:
            # 获取表配置
            table_key = f"{binlog_event.schema}.{binlog_event.table}"
            table_config = self.target_tables.get(table_key)
            
            if not table_config:
                return None
            
            # 确定操作类型
            if isinstance(binlog_event, WriteRowsEvent):
                operation = 'INSERT'
            elif isinstance(binlog_event, UpdateRowsEvent):
                operation = 'UPDATE'
            elif isinstance(binlog_event, DeleteRowsEvent):
                operation = 'DELETE'
            else:
                return None
            
            # 检查是否需要监控此操作
            if operation not in table_config['operations']:
                return None
            
            # 解析行数据
            events = []
            for row in binlog_event.rows:
                event = self._parse_single_row(binlog_event, row, operation, table_config)
                if event:
                    events.append(event)
            
            return events if len(events) > 1 else (events[0] if events else None)
        
        except Exception as e:
            logger.error(f"解析行事件失败: {e}")
            return None
    
    def _parse_single_row(self, binlog_event, row, operation: str, table_config: Dict) -> Optional[Dict]:
        """解析单行数据"""
        try:
            # 基础事件信息
            event = {
                'id': str(uuid.uuid4()),
                'timestamp': datetime.now(),
                'database': binlog_event.schema,
                'table': binlog_event.table,
                'operation': operation,
                'binlog_file': getattr(binlog_event.packet, 'log_file', ''),
                'binlog_position': getattr(binlog_event.packet, 'log_pos', 0),
                'server_id': getattr(binlog_event, 'server_id', 0)
            }
            
            # 根据操作类型处理数据
            if operation == 'INSERT':
                event.update(self._parse_insert_row(row, table_config))
            elif operation == 'UPDATE':
                event.update(self._parse_update_row(row, table_config))
            elif operation == 'DELETE':
                event.update(self._parse_delete_row(row, table_config))
            
            return event
        
        except Exception as e:
            logger.error(f"解析单行数据失败: {e}")
            return None
    
    def _parse_insert_row(self, row, table_config: Dict) -> Dict:
        """解析INSERT行"""
        after_values = row['values']
        
        # 过滤需要跟踪的列
        filtered_data = self._filter_columns(after_values, table_config)
        
        # 脱敏敏感数据
        filtered_data = self._mask_sensitive_data(filtered_data, table_config)
        
        return {
            'new_data': filtered_data,
            'primary_key': self._extract_primary_key(after_values, table_config),
            'affected_columns': list(filtered_data.keys())
        }
    
    def _parse_update_row(self, row, table_config: Dict) -> Dict:
        """解析UPDATE行"""
        before_values = row['before_values']
        after_values = row['after_values']
        
        # 过滤需要跟踪的列
        old_data = self._filter_columns(before_values, table_config)
        new_data = self._filter_columns(after_values, table_config)
        
        # 找出变更的列
        changes = self._detect_changes(old_data, new_data)
        
        # 脱敏敏感数据
        old_data = self._mask_sensitive_data(old_data, table_config)
        new_data = self._mask_sensitive_data(new_data, table_config)
        
        return {
            'old_data': old_data,
            'new_data': new_data,
            'changes': changes,
            'primary_key': self._extract_primary_key(after_values, table_config),
            'affected_columns': list(changes.keys())
        }
    
    def _parse_delete_row(self, row, table_config: Dict) -> Dict:
        """解析DELETE行"""
        before_values = row['values']
        
        # 过滤需要跟踪的列
        filtered_data = self._filter_columns(before_values, table_config)
        
        # 脱敏敏感数据
        filtered_data = self._mask_sensitive_data(filtered_data, table_config)
        
        return {
            'old_data': filtered_data,
            'primary_key': self._extract_primary_key(before_values, table_config),
            'affected_columns': list(filtered_data.keys())
        }
    
    def _filter_columns(self, data: Dict, table_config: Dict) -> Dict:
        """过滤需要跟踪的列"""
        track_columns = table_config.get('track_columns', [])
        
        if not track_columns:
            # 如果没有指定列，返回所有列
            return self._convert_data_types(data)
        
        # 只返回指定的列
        filtered = {}
        for column in track_columns:
            if column in data:
                filtered[column] = data[column]
        
        return self._convert_data_types(filtered)
    
    def _convert_data_types(self, data: Dict) -> Dict:
        """转换数据类型为JSON可序列化的格式"""
        converted = {}
        
        for key, value in data.items():
            converted[key] = self._convert_single_value(value)
        
        return converted
    
    def _convert_single_value(self, value: Any) -> Any:
        """转换单个值的数据类型"""
        if value is None:
            return None
        
        # datetime类型
        if isinstance(value, datetime):
            return self._handle_datetime(value)
        
        # date类型
        if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
            return self._handle_date(value)
        
        # time类型
        if hasattr(value, 'hour') and hasattr(value, 'minute') and hasattr(value, 'second'):
            return self._handle_time(value)
        
        # decimal类型
        if hasattr(value, 'to_eng_string'):
            return self._handle_decimal(value)
        
        # bytes类型
        if isinstance(value, bytes):
            return self._handle_binary(value)
        
        # 其他类型直接返回
        return value
    
    def _handle_datetime(self, value) -> str:
        """处理datetime类型"""
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
    
    def _handle_date(self, value) -> str:
        """处理date类型"""
        return str(value)
    
    def _handle_time(self, value) -> str:
        """处理time类型"""
        return str(value)
    
    def _handle_timestamp(self, value) -> str:
        """处理timestamp类型"""
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
    
    def _handle_decimal(self, value) -> float:
        """处理decimal类型"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return str(value)
    
    def _handle_json(self, value) -> Dict:
        """处理JSON类型"""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {"raw": value}
        return value
    
    def _handle_binary(self, value: bytes) -> str:
        """处理binary类型"""
        try:
            # 尝试解码为UTF-8
            return value.decode('utf-8')
        except UnicodeDecodeError:
            # 如果无法解码，返回hex字符串
            return value.hex()
    
    def _detect_changes(self, old_data: Dict, new_data: Dict) -> Dict:
        """检测数据变更"""
        changes = {}
        
        # 检查所有新数据的字段
        for column, new_value in new_data.items():
            old_value = old_data.get(column)
            
            # 如果值发生变化
            if old_value != new_value:
                changes[column] = {
                    'old': old_value,
                    'new': new_value
                }
        
        # 检查被删除的字段
        for column, old_value in old_data.items():
            if column not in new_data:
                changes[column] = {
                    'old': old_value,
                    'new': None
                }
        
        return changes
    
    def _extract_primary_key(self, data: Dict, table_config: Dict) -> Dict:
        """提取主键值"""
        primary_key_column = table_config.get('primary_key', 'id')
        
        if isinstance(primary_key_column, str):
            # 单列主键
            return {primary_key_column: data.get(primary_key_column)}
        elif isinstance(primary_key_column, list):
            # 复合主键
            return {col: data.get(col) for col in primary_key_column}
        else:
            # 默认使用id列
            return {'id': data.get('id')}
    
    def _mask_sensitive_data(self, data: Dict, table_config: Dict) -> Dict:
        """脱敏敏感数据"""
        sensitive_columns = table_config.get('sensitive_columns', [])
        
        if not sensitive_columns:
            return data
        
        masked_data = data.copy()
        
        for column in sensitive_columns:
            if column in masked_data and masked_data[column] is not None:
                masked_data[column] = self._mask_value(masked_data[column], column)
        
        return masked_data
    
    def _mask_value(self, value: Any, column: str) -> str:
        """脱敏单个值"""
        if value is None:
            return None
        
        value_str = str(value)
        
        # 根据列名判断脱敏方式
        if 'password' in column.lower():
            return '***'
        elif 'phone' in column.lower():
            return self._mask_phone(value_str)
        elif 'email' in column.lower():
            return self._mask_email(value_str)
        elif 'card' in column.lower() or 'account' in column.lower():
            return self._mask_card(value_str)
        else:
            # 默认脱敏方式
            return self._mask_default(value_str)
    
    def _mask_phone(self, phone: str) -> str:
        """脱敏手机号"""
        if len(phone) >= 7:
            return phone[:3] + '****' + phone[-4:]
        return '***'
    
    def _mask_email(self, email: str) -> str:
        """脱敏邮箱"""
        if '@' in email:
            local, domain = email.split('@', 1)
            if len(local) > 2:
                return local[:2] + '***@' + domain
            return '***@' + domain
        return '***'
    
    def _mask_card(self, card: str) -> str:
        """脱敏卡号"""
        if len(card) > 8:
            return card[:4] + '****' + card[-4:]
        return '****'
    
    def _mask_default(self, value: str) -> str:
        """默认脱敏方式"""
        if len(value) > 6:
            return value[:2] + '***' + value[-2:]
        return '***'
    
    def get_table_schema(self, database: str, table: str) -> Optional[Dict]:
        """获取表结构信息"""
        # 这里可以实现获取表结构的逻辑
        # 可以从INFORMATION_SCHEMA获取列信息
        pass
    
    def validate_event(self, event: Dict) -> bool:
        """验证事件数据"""
        required_fields = ['id', 'timestamp', 'database', 'table', 'operation']
        
        for field in required_fields:
            if field not in event:
                logger.warning(f"事件缺少必需字段: {field}")
                return False
        
        return True
    
    def enrich_event(self, event: Dict) -> Dict:
        """丰富事件信息"""
        # 添加额外的元数据
        event['parser_version'] = '1.0.0'
        event['processed_at'] = datetime.now().isoformat()
        
        # 计算影响的行数
        if 'affected_columns' in event:
            event['affected_column_count'] = len(event['affected_columns'])
        
        # 添加操作类型标签
        event['operation_type'] = self._get_operation_type(event['operation'])
        
        return event
    
    def _get_operation_type(self, operation: str) -> str:
        """获取操作类型标签"""
        if operation in ['INSERT']:
            return 'CREATE'
        elif operation in ['UPDATE']:
            return 'MODIFY'
        elif operation in ['DELETE']:
            return 'REMOVE'
        else:
            return 'UNKNOWN'
    
    def batch_parse_events(self, binlog_events: List) -> List[Dict]:
        """批量解析事件"""
        parsed_events = []
        
        for binlog_event in binlog_events:
            parsed = self.parse_row_event(binlog_event)
            if parsed:
                if isinstance(parsed, list):
                    parsed_events.extend(parsed)
                else:
                    parsed_events.append(parsed)
        
        return parsed_events
    
    def filter_events_by_criteria(self, events: List[Dict], criteria: Dict) -> List[Dict]:
        """根据条件过滤事件"""
        filtered = []
        
        for event in events:
            if self._match_criteria(event, criteria):
                filtered.append(event)
        
        return filtered
    
    def _match_criteria(self, event: Dict, criteria: Dict) -> bool:
        """检查事件是否匹配条件"""
        # 检查数据库
        if 'databases' in criteria:
            if event['database'] not in criteria['databases']:
                return False
        
        # 检查表
        if 'tables' in criteria:
            table_key = f"{event['database']}.{event['table']}"
            if table_key not in criteria['tables']:
                return False
        
        # 检查操作类型
        if 'operations' in criteria:
            if event['operation'] not in criteria['operations']:
                return False
        
        # 检查时间范围
        if 'start_time' in criteria:
            if event['timestamp'] < criteria['start_time']:
                return False
        
        if 'end_time' in criteria:
            if event['timestamp'] > criteria['end_time']:
                return False
        
        return True


def main():
    """测试函数"""
    # 测试配置
    config = {
        'tables': {
            'target_tables': [
                {
                    'database': 'test',
                    'table': 'users',
                    'operations': ['INSERT', 'UPDATE', 'DELETE'],
                    'track_columns': ['id', 'username', 'email', 'phone'],
                    'primary_key': 'id',
                    'sensitive_columns': ['phone', 'email']
                }
            ]
        }
    }
    
    # 创建解析器
    parser = BinlogEventParser(config)
    
    # 模拟事件数据进行测试
    print("事件解析器初始化完成")
    print(f"监控表数量: {len(parser.target_tables)}")
    
    # 测试数据转换
    test_data = {
        'id': 123,
        'username': 'testuser',
        'email': 'test@example.com',
        'phone': '13800138000',
        'created_at': datetime.now()
    }
    
    converted = parser._convert_data_types(test_data)
    print(f"数据转换结果: {converted}")
    
    # 测试脱敏
    table_config = parser.target_tables['test.users']
    masked = parser._mask_sensitive_data(converted, table_config)
    print(f"脱敏结果: {masked}")


if __name__ == '__main__':
    main()