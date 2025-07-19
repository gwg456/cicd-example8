#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL注入检测分析器
用于检测和分析可疑的SQL注入攻击
"""

import re
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from ..utils.config import Config


class SQLInjectionDetector:
    """SQL注入检测器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.enabled = config.get('analyzers.sql_injection.enabled', True)
        self.sensitivity = config.get('analyzers.sql_injection.sensitivity', 'medium')
        
        # 检测规则
        self.injection_patterns = self._load_injection_patterns()
        self.suspicious_keywords = self._load_suspicious_keywords()
        
        # 统计信息
        self.detection_stats = {
            'total_analyzed': 0,
            'suspicious_detected': 0,
            'high_risk_detected': 0,
            'last_detection': None
        }
        
        # 缓存最近检测的查询哈希
        self.recent_queries = {}
        self.cache_duration = timedelta(minutes=30)
    
    def _load_injection_patterns(self) -> List[Dict]:
        """加载SQL注入检测模式"""
        return [
            {
                'name': 'Union Based Injection',
                'pattern': r'(?i)(union\s+(all\s+)?select|union\s+\(?\s*select)',
                'risk_level': 'high',
                'description': 'UNION based SQL injection attempt'
            },
            {
                'name': 'Boolean Based Injection',
                'pattern': r'(?i)(\s+(and|or)\s+\d+\s*=\s*\d+|\s+(and|or)\s+[\'"]?\w+[\'"]?\s*=\s*[\'"]?\w+[\'"]?)',
                'risk_level': 'medium',
                'description': 'Boolean based SQL injection attempt'
            },
            {
                'name': 'Time Based Injection',
                'pattern': r'(?i)(sleep\s*\(|benchmark\s*\(|waitfor\s+delay|pg_sleep\s*\()',
                'risk_level': 'high',
                'description': 'Time based SQL injection attempt'
            },
            {
                'name': 'Comment Injection',
                'pattern': r'(?i)(\/\*.*?\*\/|--\s*.*?(\r|\n|$)|#.*?(\r|\n|$))',
                'risk_level': 'medium',
                'description': 'SQL comment injection attempt'
            },
            {
                'name': 'Stacked Queries',
                'pattern': r'(?i)(;\s*(insert|update|delete|drop|create|alter|exec|execute))',
                'risk_level': 'high',
                'description': 'Stacked queries injection attempt'
            },
            {
                'name': 'Error Based Injection',
                'pattern': r'(?i)(extractvalue\s*\(|updatexml\s*\(|exp\s*\(~|floor\s*\(rand\s*\(\s*0\s*\)\s*\*\s*2\s*\))',
                'risk_level': 'high',
                'description': 'Error based SQL injection attempt'
            },
            {
                'name': 'Information Schema Access',
                'pattern': r'(?i)(information_schema\.(tables|columns|schemata|user_privileges))',
                'risk_level': 'medium',
                'description': 'Information schema enumeration attempt'
            },
            {
                'name': 'File Operations',
                'pattern': r'(?i)(load_file\s*\(|into\s+outfile|into\s+dumpfile)',
                'risk_level': 'high',
                'description': 'File operation injection attempt'
            },
            {
                'name': 'Blind Injection',
                'pattern': r'(?i)(substring\s*\(.*?,\s*\d+\s*,\s*1\s*\)|ascii\s*\(|length\s*\(.*?\)\s*=\s*\d+)',
                'risk_level': 'medium',
                'description': 'Blind SQL injection attempt'
            },
            {
                'name': 'XPath Injection',
                'pattern': r'(?i)(extractvalue\s*\(|updatexml\s*\().*xpath',
                'risk_level': 'medium',
                'description': 'XPath injection attempt'
            }
        ]
    
    def _load_suspicious_keywords(self) -> List[str]:
        """加载可疑关键词"""
        return [
            'script', 'alert', 'onload', 'onerror', 'javascript',
            'vbscript', 'expression', 'applet', 'meta', 'xml',
            'blink', 'style', 'embed', 'object', 'iframe',
            'frame', 'frameset', 'ilayer', 'layer', 'bgsound',
            'title', 'base', 'xss', 'injection', 'payload'
        ]
    
    def analyze_query(self, audit_record: Dict) -> Dict:
        """分析SQL查询是否存在注入风险"""
        if not self.enabled:
            return {'risk_level': 'none', 'analysis_performed': False}
        
        self.detection_stats['total_analyzed'] += 1
        
        sql_statement = audit_record.get('sql_statement', '')
        if not sql_statement:
            return {'risk_level': 'none', 'analysis_performed': True}
        
        # 检查是否为重复查询
        query_hash = self._get_query_hash(sql_statement)
        if self._is_recent_query(query_hash):
            return {'risk_level': 'none', 'analysis_performed': True, 'cached': True}
        
        # 执行检测
        detection_results = self._detect_injection_patterns(sql_statement)
        risk_assessment = self._assess_risk(detection_results, audit_record)
        
        # 更新统计信息
        if risk_assessment['risk_level'] in ['medium', 'high']:
            self.detection_stats['suspicious_detected'] += 1
            self.detection_stats['last_detection'] = datetime.now()
            
        if risk_assessment['risk_level'] == 'high':
            self.detection_stats['high_risk_detected'] += 1
        
        # 缓存查询
        self._cache_query(query_hash)
        
        return risk_assessment
    
    def _detect_injection_patterns(self, sql_statement: str) -> List[Dict]:
        """检测SQL注入模式"""
        detections = []
        
        for pattern_info in self.injection_patterns:
            pattern = pattern_info['pattern']
            matches = re.finditer(pattern, sql_statement)
            
            for match in matches:
                detection = {
                    'pattern_name': pattern_info['name'],
                    'risk_level': pattern_info['risk_level'],
                    'description': pattern_info['description'],
                    'matched_text': match.group(),
                    'position': match.span(),
                    'confidence': self._calculate_confidence(match.group(), pattern_info)
                }
                detections.append(detection)
        
        # 检测可疑关键词
        suspicious_words = self._detect_suspicious_keywords(sql_statement)
        if suspicious_words:
            detections.append({
                'pattern_name': 'Suspicious Keywords',
                'risk_level': 'low',
                'description': f'Contains suspicious keywords: {", ".join(suspicious_words)}',
                'matched_text': ', '.join(suspicious_words),
                'position': None,
                'confidence': 0.3
            })
        
        return detections
    
    def _detect_suspicious_keywords(self, sql_statement: str) -> List[str]:
        """检测可疑关键词"""
        found_keywords = []
        sql_lower = sql_statement.lower()
        
        for keyword in self.suspicious_keywords:
            if keyword in sql_lower:
                found_keywords.append(keyword)
        
        return found_keywords
    
    def _calculate_confidence(self, matched_text: str, pattern_info: Dict) -> float:
        """计算检测置信度"""
        base_confidence = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }.get(pattern_info['risk_level'], 0.5)
        
        # 根据匹配文本的特征调整置信度
        adjustments = 0.0
        
        # 长度调整
        if len(matched_text) > 50:
            adjustments += 0.1
        
        # 特殊字符密度
        special_chars = re.findall(r'[\'";()=<>-]', matched_text)
        if len(special_chars) > len(matched_text) * 0.2:
            adjustments += 0.1
        
        # 编码检测
        if self._contains_encoding(matched_text):
            adjustments += 0.2
        
        return min(1.0, base_confidence + adjustments)
    
    def _contains_encoding(self, text: str) -> bool:
        """检测是否包含编码内容"""
        encoding_patterns = [
            r'%[0-9a-fA-F]{2}',  # URL编码
            r'\\x[0-9a-fA-F]{2}',  # 十六进制编码
            r'&#\d+;',  # HTML实体编码
            r'\\u[0-9a-fA-F]{4}'  # Unicode编码
        ]
        
        for pattern in encoding_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _assess_risk(self, detections: List[Dict], audit_record: Dict) -> Dict:
        """综合评估风险等级"""
        if not detections:
            return {
                'risk_level': 'none',
                'confidence': 0.0,
                'detections': [],
                'analysis_performed': True
            }
        
        # 计算最高风险等级
        risk_levels = [d['risk_level'] for d in detections]
        max_risk = 'none'
        
        if 'high' in risk_levels:
            max_risk = 'high'
        elif 'medium' in risk_levels:
            max_risk = 'medium'
        elif 'low' in risk_levels:
            max_risk = 'low'
        
        # 计算综合置信度
        total_confidence = sum(d['confidence'] for d in detections)
        avg_confidence = total_confidence / len(detections)
        
        # 考虑上下文因素
        context_adjustments = self._analyze_context(audit_record)
        final_confidence = min(1.0, avg_confidence + context_adjustments)
        
        # 生成建议
        recommendations = self._generate_recommendations(detections, audit_record)
        
        return {
            'risk_level': max_risk,
            'confidence': final_confidence,
            'detections': detections,
            'context_factors': context_adjustments,
            'recommendations': recommendations,
            'analysis_performed': True
        }
    
    def _analyze_context(self, audit_record: Dict) -> float:
        """分析上下文因素"""
        adjustments = 0.0
        
        # 用户类型
        user_name = audit_record.get('user_name', '').lower()
        if user_name in ['root', 'admin', 'administrator']:
            adjustments -= 0.2  # 管理员用户降低风险
        elif user_name.startswith('web_') or user_name.startswith('app_'):
            adjustments += 0.1  # Web/应用用户增加风险
        
        # 连接来源
        host = audit_record.get('host', '')
        if '127.0.0.1' in host or 'localhost' in host:
            adjustments -= 0.1  # 本地连接降低风险
        elif self._is_external_ip(host):
            adjustments += 0.2  # 外部IP增加风险
        
        # 时间因素
        timestamp = audit_record.get('timestamp')
        if timestamp and self._is_non_business_hours(timestamp):
            adjustments += 0.1  # 非工作时间增加风险
        
        # 数据库类型
        database = audit_record.get('database_name', '')
        if database in ['mysql', 'information_schema', 'performance_schema']:
            adjustments += 0.1  # 系统数据库增加风险
        
        return adjustments
    
    def _is_external_ip(self, host: str) -> bool:
        """判断是否为外部IP"""
        if not host:
            return False
        
        # 提取IP地址
        ip_pattern = r'\d+\.\d+\.\d+\.\d+'
        match = re.search(ip_pattern, host)
        if not match:
            return True  # 域名视为外部
        
        ip = match.group()
        # 检查私有IP范围
        private_ranges = [
            (r'^10\.', True),
            (r'^172\.(1[6-9]|2[0-9]|3[01])\.', True),
            (r'^192\.168\.', True),
            (r'^127\.', False),  # 本地回环
        ]
        
        for pattern, is_private in private_ranges:
            if re.match(pattern, ip):
                return not is_private
        
        return True  # 其他情况视为外部
    
    def _is_non_business_hours(self, timestamp: datetime) -> bool:
        """判断是否为非工作时间"""
        if not timestamp:
            return False
        
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # 周末或晚上/早上
        return weekday >= 5 or hour < 8 or hour > 18
    
    def _generate_recommendations(self, detections: List[Dict], audit_record: Dict) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        if not detections:
            return recommendations
        
        # 基于检测类型的建议
        detection_types = set(d['pattern_name'] for d in detections)
        
        if 'Union Based Injection' in detection_types:
            recommendations.append("检查应用程序的输入验证和参数化查询")
            recommendations.append("考虑使用WAF过滤UNION查询")
        
        if 'Time Based Injection' in detection_types:
            recommendations.append("禁用或限制时间函数的使用")
            recommendations.append("监控查询执行时间异常")
        
        if 'File Operations' in detection_types:
            recommendations.append("限制文件操作权限")
            recommendations.append("审查LOAD_FILE和INTO OUTFILE的使用")
        
        if 'Information Schema Access' in detection_types:
            recommendations.append("限制对系统表的访问权限")
            recommendations.append("监控敏感系统信息的查询")
        
        # 通用建议
        recommendations.extend([
            "使用预编译语句(Prepared Statements)",
            "对用户输入进行严格验证和转义",
            "实施最小权限原则",
            "定期审查数据库用户权限"
        ])
        
        return list(set(recommendations))  # 去重
    
    def _get_query_hash(self, sql_statement: str) -> str:
        """获取查询的哈希值"""
        # 标准化SQL语句
        normalized = re.sub(r'\s+', ' ', sql_statement.strip().lower())
        # 移除参数值，只保留结构
        normalized = re.sub(r"'[^']*'", "'?'", normalized)
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _is_recent_query(self, query_hash: str) -> bool:
        """检查是否为最近的查询"""
        if query_hash in self.recent_queries:
            last_seen = self.recent_queries[query_hash]
            if datetime.now() - last_seen < self.cache_duration:
                return True
            else:
                # 清除过期缓存
                del self.recent_queries[query_hash]
        return False
    
    def _cache_query(self, query_hash: str):
        """缓存查询"""
        self.recent_queries[query_hash] = datetime.now()
        
        # 清理过期缓存
        current_time = datetime.now()
        expired_keys = [
            key for key, timestamp in self.recent_queries.items()
            if current_time - timestamp > self.cache_duration
        ]
        for key in expired_keys:
            del self.recent_queries[key]
    
    def get_detection_stats(self) -> Dict:
        """获取检测统计信息"""
        return {
            **self.detection_stats,
            'cache_size': len(self.recent_queries),
            'enabled': self.enabled,
            'sensitivity': self.sensitivity
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.detection_stats = {
            'total_analyzed': 0,
            'suspicious_detected': 0,
            'high_risk_detected': 0,
            'last_detection': None
        }
        self.recent_queries.clear()


def main():
    """测试入口"""
    from ..utils.config import Config
    
    config = Config()
    detector = SQLInjectionDetector(config)
    
    # 测试用例
    test_queries = [
        "SELECT * FROM users WHERE id = 1",
        "SELECT * FROM users WHERE id = 1 UNION SELECT username, password FROM admin",
        "SELECT * FROM users WHERE id = 1; DROP TABLE users;",
        "SELECT * FROM users WHERE id = 1 AND SLEEP(10)",
        "SELECT * FROM users WHERE username = 'admin'--' AND password = 'test'",
        "SELECT LOAD_FILE('/etc/passwd')",
        "SELECT * FROM information_schema.tables"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n测试 {i}: {query}")
        audit_record = {
            'sql_statement': query,
            'user_name': 'test_user',
            'host': '192.168.1.100',
            'database_name': 'testdb',
            'timestamp': datetime.now()
        }
        
        result = detector.analyze_query(audit_record)
        print(f"风险等级: {result['risk_level']}")
        print(f"置信度: {result['confidence']:.2f}")
        if result['detections']:
            print("检测到的威胁:")
            for detection in result['detections']:
                print(f"  - {detection['pattern_name']}: {detection['description']}")


if __name__ == '__main__':
    main()