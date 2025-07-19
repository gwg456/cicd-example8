#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 变更监控 - 表管理脚本
方便添加、删除和管理要监控的表
"""

import os
import sys
import yaml
import argparse
from typing import List, Dict


class TableManager:
    """表管理器"""
    
    def __init__(self, config_file: str = 'config/monitor.conf'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {self.config_file}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ 配置文件格式错误: {e}")
            sys.exit(1)
    
    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            print(f"✅ 配置已保存到: {self.config_file}")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
    
    def list_tables(self):
        """列出当前监控的表"""
        monitoring = self.config.get('monitoring', {})
        mode = monitoring.get('mode', 'whitelist')
        databases = monitoring.get('databases', [])
        target_tables = monitoring.get('target_tables', [])
        exclude_tables = monitoring.get('exclude_tables', [])
        
        print("📊 当前监控配置")
        print("=" * 50)
        print(f"监控模式: {mode}")
        print(f"监控数据库: {', '.join(databases)}")
        print()
        
        if mode == 'whitelist':
            print("🎯 监控表列表 (白名单):")
            if target_tables:
                for i, table in enumerate(target_tables, 1):
                    print(f"  {i:2d}. {table}")
            else:
                print("  (无)")
        
        print()
        print("🚫 排除表列表:")
        if exclude_tables:
            for i, table in enumerate(exclude_tables, 1):
                print(f"  {i:2d}. {table}")
        else:
            print("  (无)")
    
    def add_table(self, table_name: str):
        """添加监控表"""
        monitoring = self.config.setdefault('monitoring', {})
        target_tables = monitoring.setdefault('target_tables', [])
        
        if table_name in target_tables:
            print(f"⚠️  表 '{table_name}' 已在监控列表中")
            return
        
        target_tables.append(table_name)
        self._save_config()
        print(f"✅ 已添加监控表: {table_name}")
    
    def remove_table(self, table_name: str):
        """移除监控表"""
        monitoring = self.config.get('monitoring', {})
        target_tables = monitoring.get('target_tables', [])
        
        if table_name not in target_tables:
            print(f"⚠️  表 '{table_name}' 不在监控列表中")
            return
        
        target_tables.remove(table_name)
        self._save_config()
        print(f"✅ 已移除监控表: {table_name}")
    
    def add_exclude(self, table_name: str):
        """添加排除表"""
        monitoring = self.config.setdefault('monitoring', {})
        exclude_tables = monitoring.setdefault('exclude_tables', [])
        
        if table_name in exclude_tables:
            print(f"⚠️  表 '{table_name}' 已在排除列表中")
            return
        
        exclude_tables.append(table_name)
        self._save_config()
        print(f"✅ 已添加排除表: {table_name}")
    
    def remove_exclude(self, table_name: str):
        """移除排除表"""
        monitoring = self.config.get('monitoring', {})
        exclude_tables = monitoring.get('exclude_tables', [])
        
        if table_name not in exclude_tables:
            print(f"⚠️  表 '{table_name}' 不在排除列表中")
            return
        
        exclude_tables.remove(table_name)
        self._save_config()
        print(f"✅ 已移除排除表: {table_name}")
    
    def set_mode(self, mode: str):
        """设置监控模式"""
        if mode not in ['whitelist', 'blacklist']:
            print("❌ 监控模式必须是 'whitelist' 或 'blacklist'")
            return
        
        monitoring = self.config.setdefault('monitoring', {})
        monitoring['mode'] = mode
        self._save_config()
        print(f"✅ 监控模式已设置为: {mode}")
    
    def add_database(self, database_name: str):
        """添加监控数据库"""
        monitoring = self.config.setdefault('monitoring', {})
        databases = monitoring.setdefault('databases', [])
        
        if database_name in databases:
            print(f"⚠️  数据库 '{database_name}' 已在监控列表中")
            return
        
        databases.append(database_name)
        self._save_config()
        print(f"✅ 已添加监控数据库: {database_name}")
    
    def remove_database(self, database_name: str):
        """移除监控数据库"""
        monitoring = self.config.get('monitoring', {})
        databases = monitoring.get('databases', [])
        
        if database_name not in databases:
            print(f"⚠️  数据库 '{database_name}' 不在监控列表中")
            return
        
        databases.remove(database_name)
        self._save_config()
        print(f"✅ 已移除监控数据库: {database_name}")
    
    def batch_add_tables(self, table_file: str):
        """批量添加表"""
        try:
            with open(table_file, 'r', encoding='utf-8') as f:
                tables = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            monitoring = self.config.setdefault('monitoring', {})
            target_tables = monitoring.setdefault('target_tables', [])
            
            added_count = 0
            for table in tables:
                if table not in target_tables:
                    target_tables.append(table)
                    added_count += 1
                    print(f"✅ 添加: {table}")
                else:
                    print(f"⚠️  跳过: {table} (已存在)")
            
            if added_count > 0:
                self._save_config()
                print(f"\n✅ 批量添加完成，共添加 {added_count} 个表")
            else:
                print("\n⚠️  没有新表需要添加")
                
        except FileNotFoundError:
            print(f"❌ 文件不存在: {table_file}")
        except Exception as e:
            print(f"❌ 批量添加失败: {e}")
    
    def generate_template(self, template_type: str = 'basic'):
        """生成配置模板"""
        templates = {
            'basic': {
                'mode': 'whitelist',
                'databases': ['your_database_name'],
                'target_tables': [
                    'your_database_name.users',
                    'your_database_name.orders',
                    'your_database_name.products'
                ]
            },
            'ecommerce': {
                'mode': 'whitelist',
                'databases': ['ecommerce_db'],
                'target_tables': [
                    'ecommerce_db.users',
                    'ecommerce_db.user_profiles',
                    'ecommerce_db.products',
                    'ecommerce_db.orders',
                    'ecommerce_db.order_items',
                    'ecommerce_db.payments',
                    'ecommerce_db.inventory'
                ]
            },
            'finance': {
                'mode': 'whitelist',
                'databases': ['finance_db'],
                'target_tables': [
                    'finance_db.accounts',
                    'finance_db.transactions',
                    'finance_db.payments',
                    'finance_db.balances',
                    'finance_db.risk_events'
                ]
            }
        }
        
        if template_type not in templates:
            print(f"❌ 未知模板类型: {template_type}")
            print(f"可用模板: {', '.join(templates.keys())}")
            return
        
        template = templates[template_type]
        self.config['monitoring'] = template
        self._save_config()
        print(f"✅ 已应用 {template_type} 模板")


def main():
    parser = argparse.ArgumentParser(description='MySQL 变更监控表管理工具')
    parser.add_argument('--config', '-c', default='config/monitor.conf', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 列出表
    subparsers.add_parser('list', help='列出当前监控配置')
    
    # 添加表
    add_parser = subparsers.add_parser('add', help='添加监控表')
    add_parser.add_argument('table', help='表名 (格式: database.table 或 table)')
    
    # 移除表
    remove_parser = subparsers.add_parser('remove', help='移除监控表')
    remove_parser.add_argument('table', help='表名')
    
    # 添加排除表
    exclude_add_parser = subparsers.add_parser('exclude-add', help='添加排除表')
    exclude_add_parser.add_argument('table', help='表名')
    
    # 移除排除表
    exclude_remove_parser = subparsers.add_parser('exclude-remove', help='移除排除表')
    exclude_remove_parser.add_argument('table', help='表名')
    
    # 设置模式
    mode_parser = subparsers.add_parser('mode', help='设置监控模式')
    mode_parser.add_argument('mode', choices=['whitelist', 'blacklist'], help='监控模式')
    
    # 添加数据库
    db_add_parser = subparsers.add_parser('add-db', help='添加监控数据库')
    db_add_parser.add_argument('database', help='数据库名')
    
    # 移除数据库
    db_remove_parser = subparsers.add_parser('remove-db', help='移除监控数据库')
    db_remove_parser.add_argument('database', help='数据库名')
    
    # 批量添加
    batch_parser = subparsers.add_parser('batch-add', help='从文件批量添加表')
    batch_parser.add_argument('file', help='包含表名的文件，每行一个表名')
    
    # 生成模板
    template_parser = subparsers.add_parser('template', help='应用配置模板')
    template_parser.add_argument('type', choices=['basic', 'ecommerce', 'finance'], 
                                help='模板类型')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = TableManager(args.config)
    
    if args.command == 'list':
        manager.list_tables()
    elif args.command == 'add':
        manager.add_table(args.table)
    elif args.command == 'remove':
        manager.remove_table(args.table)
    elif args.command == 'exclude-add':
        manager.add_exclude(args.table)
    elif args.command == 'exclude-remove':
        manager.remove_exclude(args.table)
    elif args.command == 'mode':
        manager.set_mode(args.mode)
    elif args.command == 'add-db':
        manager.add_database(args.database)
    elif args.command == 'remove-db':
        manager.remove_database(args.database)
    elif args.command == 'batch-add':
        manager.batch_add_tables(args.file)
    elif args.command == 'template':
        manager.generate_template(args.type)


if __name__ == '__main__':
    main()