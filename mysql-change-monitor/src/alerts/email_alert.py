#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 变更监控 - 邮件告警模块
基于 Binary Log 监控的变更告警
"""

import smtplib
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Dict, List
from loguru import logger


class EmailAlert:
    """邮件告警器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.email_config = config.get('alerts', {}).get('email', {})
        self.enabled = self.email_config.get('enabled', False)
        
        if self.enabled:
            self.smtp_server = self.email_config.get('smtp_server')
            self.smtp_port = self.email_config.get('smtp_port', 587)
            self.use_tls = self.email_config.get('use_tls', True)
            self.username = self.email_config.get('username')
            self.password = self.email_config.get('password')
            self.recipients = self.email_config.get('recipients', [])
            self.subject_prefix = self.email_config.get('subject_prefix', '[MySQL变更]')
            
            logger.info(f"Email alert initialized for {len(self.recipients)} recipients")
    
    def send_change_alert(self, change_record: Dict):
        """发送变更告警邮件"""
        if not self.enabled:
            return
        
        try:
            subject = self._create_subject(change_record)
            content = self._create_content(change_record)
            
            self._send_email(subject, content)
            logger.info(f"Change alert email sent: {change_record['operation_type']} {change_record['table_name']}")
            
        except Exception as e:
            logger.error(f"Failed to send change alert email: {e}")
    
    def send_batch_alert(self, changes: List[Dict]):
        """发送批量变更告警"""
        if not self.enabled or not changes:
            return
        
        try:
            subject = f"{self.subject_prefix} 批量变更告警 ({len(changes)}条)"
            content = self._create_batch_content(changes)
            
            self._send_email(subject, content)
            logger.info(f"Batch alert email sent for {len(changes)} changes")
            
        except Exception as e:
            logger.error(f"Failed to send batch alert email: {e}")
    
    def send_summary_report(self, stats: Dict, period: str = "daily"):
        """发送汇总报告"""
        if not self.enabled:
            return
        
        try:
            subject = f"{self.subject_prefix} {period.title()} 变更汇总报告"
            content = self._create_summary_content(stats, period)
            
            self._send_email(subject, content)
            logger.info(f"{period.title()} summary report sent")
            
        except Exception as e:
            logger.error(f"Failed to send summary report: {e}")
    
    def _create_subject(self, change_record: Dict) -> str:
        """创建邮件主题"""
        operation = change_record['operation_type']
        database = change_record['database_name']
        table = change_record['table_name']
        
        if operation == 'DDL':
            return f"{self.subject_prefix} DDL变更告警 - {database}.{table}"
        elif operation == 'DELETE':
            return f"{self.subject_prefix} 删除操作告警 - {database}.{table}"
        else:
            return f"{self.subject_prefix} {operation}操作告警 - {database}.{table}"
    
    def _create_content(self, change_record: Dict) -> str:
        """创建邮件内容"""
        operation = change_record['operation_type']
        database = change_record['database_name']
        table = change_record['table_name']
        timestamp = change_record['timestamp']
        
        content = f"""
📊 MySQL 数据库变更告警
{'='*50}

🔍 变更详情:
  操作类型: {operation}
  数据库: {database}
  表名: {table}
  时间: {timestamp}
  来源: {change_record.get('source', 'binlog')}
"""
        
        if change_record.get('sql_statement'):
            content += f"  SQL语句: {change_record['sql_statement']}\n"
        
        if change_record.get('user_name'):
            content += f"  执行用户: {change_record['user_name']}\n"
        
        if change_record.get('rows_affected', 0) > 0:
            content += f"  影响行数: {change_record['rows_affected']}\n"
        
        if change_record.get('binlog_file') and change_record.get('binlog_pos'):
            content += f"  Binlog位置: {change_record['binlog_file']}:{change_record['binlog_pos']}\n"
        
        # 数据变更详情
        if operation in ['INSERT', 'UPDATE', 'DELETE']:
            content += "\n📝 数据变更详情:\n"
            
            if change_record.get('before_values'):
                content += f"  变更前: {self._format_values(change_record['before_values'])}\n"
            
            if change_record.get('after_values'):
                content += f"  变更后: {self._format_values(change_record['after_values'])}\n"
        
        # 告警原因
        content += f"\n⚠️  告警原因:\n"
        content += self._get_alert_reason(change_record)
        
        content += f"""

📋 处理建议:
  1. 立即检查变更是否为预期操作
  2. 如有异常，请立即联系相关负责人
  3. 确认数据完整性和业务影响
  4. 必要时启动应急响应流程

🔗 监控系统: http://localhost:8080

---
此邮件由 MySQL 变更监控系统自动发送
发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return content
    
    def _create_batch_content(self, changes: List[Dict]) -> str:
        """创建批量告警内容"""
        content = f"""
📊 MySQL 批量变更告警
{'='*50}

⚠️  检测到 {len(changes)} 条变更记录

📈 变更统计:
"""
        
        # 统计各类操作
        stats = {}
        for change in changes:
            operation = change['operation_type']
            stats[operation] = stats.get(operation, 0) + 1
        
        for operation, count in stats.items():
            content += f"  {operation}: {count} 条\n"
        
        content += "\n📝 变更详情:\n"
        
        # 列出前10条变更
        for i, change in enumerate(changes[:10], 1):
            content += f"  {i:2d}. {change['timestamp']} - {change['operation_type']} {change['database_name']}.{change['table_name']}\n"
        
        if len(changes) > 10:
            content += f"  ... 及其他 {len(changes) - 10} 条变更\n"
        
        content += f"""

🔗 查看完整详情: http://localhost:8080

---
发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return content
    
    def _create_summary_content(self, stats: Dict, period: str) -> str:
        """创建汇总报告内容"""
        content = f"""
📊 MySQL 变更汇总报告 ({period.title()})
{'='*50}

📈 变更统计:
  总变更数: {stats.get('total_changes', 0)}
  插入操作: {stats.get('inserts', 0)}
  更新操作: {stats.get('updates', 0)}
  删除操作: {stats.get('deletes', 0)}
  DDL操作: {stats.get('ddl_changes', 0)}

📋 活跃表统计:
"""
        
        table_stats = stats.get('table_stats', [])
        for i, table_stat in enumerate(table_stats[:10], 1):
            content += f"  {i:2d}. {table_stat['database_name']}.{table_stat['table_name']} - {table_stat['operation_type']}: {table_stat['count']} 次\n"
        
        content += f"""

🔗 详细报告: http://localhost:8080

---
报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return content
    
    def _format_values(self, values: Dict) -> str:
        """格式化数据值"""
        if not values:
            return "无"
        
        # 限制显示长度
        formatted = json.dumps(values, ensure_ascii=False, indent=2)
        if len(formatted) > 500:
            formatted = formatted[:500] + "... (内容过长，已截断)"
        
        return formatted
    
    def _get_alert_reason(self, change_record: Dict) -> str:
        """获取告警原因"""
        reasons = []
        
        operation = change_record['operation_type']
        table_name = change_record['table_name']
        
        # 检查关键表
        critical_tables = self.config.get('alerts', {}).get('critical_tables', [])
        if table_name in critical_tables:
            reasons.append(f"表 '{table_name}' 属于关键业务表")
        
        # 检查操作类型
        if operation == 'DELETE':
            reasons.append("检测到数据删除操作")
        elif operation == 'DDL':
            reasons.append("检测到数据库结构变更")
        
        # 检查批量操作
        rows_affected = change_record.get('rows_affected', 0)
        bulk_threshold = self.config.get('alerts', {}).get('bulk_threshold', 1000)
        if rows_affected >= bulk_threshold:
            reasons.append(f"批量操作，影响 {rows_affected} 行数据")
        
        if not reasons:
            reasons.append("匹配预设告警规则")
        
        return "  • " + "\n  • ".join(reasons)
    
    def _send_email(self, subject: str, content: str):
        """发送邮件"""
        if not self.recipients:
            logger.warning("No email recipients configured")
            return
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 添加邮件内容
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            # 连接SMTP服务器
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            server.login(self.username, self.password)
            
            # 发送邮件
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
    
    def test_connection(self) -> bool:
        """测试邮件连接"""
        if not self.enabled:
            logger.info("Email alert is disabled")
            return True
        
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            server.login(self.username, self.password)
            server.quit()
            
            logger.info("Email connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False