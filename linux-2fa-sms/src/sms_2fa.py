#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMS 2FA 主要认证模块
提供双重因子认证的核心功能
"""

import os
import time
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from .config import Config, UserConfig
from .aliyun_sms import SMSCodeManager


class SMS2FAAuthenticator:
    """SMS双重因子认证器"""
    
    def __init__(self, config_file: str = "/etc/sms-2fa/2fa.conf"):
        """
        初始化认证器
        
        Args:
            config_file: 配置文件路径
        """
        self.config = Config(config_file)
        self.user_config = UserConfig()
        self.sms_manager = self._create_sms_manager()
        self._login_attempts = {}  # 内存中的登录尝试记录
        
        # 配置日志
        self._setup_logging()
        
        logger.info("SMS 2FA 认证器初始化完成")
    
    def _create_sms_manager(self) -> SMSCodeManager:
        """创建SMS管理器"""
        redis_client = None
        
        if self.config.enable_redis:
            try:
                import redis
                redis_client = redis.Redis(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    db=self.config.redis_db,
                    password=self.config.redis_password if self.config.redis_password else None,
                    decode_responses=True
                )
                # 测试连接
                redis_client.ping()
                logger.info("Redis连接成功")
            except Exception as e:
                logger.warning(f"Redis连接失败，使用内存存储: {e}")
                redis_client = None
        
        return SMSCodeManager(self.config, redis_client)
    
    def _setup_logging(self):
        """设置日志配置"""
        try:
            # 创建日志目录
            log_dir = os.path.dirname(self.config.log_file)
            os.makedirs(log_dir, mode=0o755, exist_ok=True)
            
            # 配置loguru
            logger.add(
                self.config.log_file,
                level=self.config.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
                rotation="10 MB",
                retention="30 days",
                compression="gz"
            )
            
            # 审计日志
            if self.config.enable_audit_log:
                audit_log_dir = os.path.dirname(self.config.audit_log_file)
                os.makedirs(audit_log_dir, mode=0o755, exist_ok=True)
                
                logger.add(
                    self.config.audit_log_file,
                    level=self.config.audit_log_level,
                    format="{time:YYYY-MM-DD HH:mm:ss} | AUDIT | {message}",
                    filter=lambda record: record["extra"].get("audit", False),
                    rotation="10 MB",
                    retention="90 days"
                )
            
        except Exception as e:
            print(f"设置日志失败: {e}")
    
    def authenticate(self, username: str, remote_ip: str = "unknown") -> Dict[str, Any]:
        """
        执行双重因子认证
        
        Args:
            username: 用户名
            remote_ip: 远程IP地址
            
        Returns:
            Dict[str, Any]: 认证结果
        """
        auth_session_id = self._generate_session_id(username, remote_ip)
        
        try:
            # 记录认证开始
            self._log_audit(
                f"2FA认证开始: 用户={username}, IP={remote_ip}, 会话={auth_session_id}"
            )
            
            # 检查用户是否需要绕过2FA
            if self._should_bypass_user(username):
                self._log_audit(
                    f"用户绕过2FA: 用户={username}, IP={remote_ip}",
                    level="WARNING"
                )
                return {
                    'success': True,
                    'bypassed': True,
                    'message': '用户已绕过双重认证',
                    'session_id': auth_session_id
                }
            
            # 检查登录尝试限制
            if self._is_user_locked(username, remote_ip):
                self._log_audit(
                    f"用户被锁定: 用户={username}, IP={remote_ip}",
                    level="WARNING"
                )
                return {
                    'success': False,
                    'error': 'User locked',
                    'message': f'用户已被锁定，请{self.config.lockout_duration//60}分钟后再试',
                    'session_id': auth_session_id
                }
            
            # 获取用户手机号
            phone_number = self.user_config.get_user_phone(username)
            if not phone_number:
                self._log_audit(
                    f"用户手机号未配置: 用户={username}, IP={remote_ip}",
                    level="ERROR"
                )
                return {
                    'success': False,
                    'error': 'Phone number not configured',
                    'message': '用户手机号未配置，请联系管理员',
                    'session_id': auth_session_id
                }
            
            # 发送验证码
            result = self.sms_manager.send_code(username, phone_number)
            
            if result['success']:
                self._log_audit(
                    f"验证码发送成功: 用户={username}, 手机={self._mask_phone(phone_number)}, IP={remote_ip}"
                )
                
                return {
                    'success': True,
                    'message': f'验证码已发送到 {self._mask_phone(phone_number)}',
                    'session_id': auth_session_id,
                    'expires_in': result.get('expires_in', self.config.code_expire_time),
                    'phone_masked': self._mask_phone(phone_number)
                }
            else:
                self._log_audit(
                    f"验证码发送失败: 用户={username}, 手机={self._mask_phone(phone_number)}, 错误={result.get('error')}, IP={remote_ip}",
                    level="ERROR"
                )
                
                return {
                    'success': False,
                    'error': result.get('error', 'SMS send failed'),
                    'message': result.get('message', '验证码发送失败'),
                    'session_id': auth_session_id
                }
                
        except Exception as e:
            logger.error(f"2FA认证异常: {username}, Error: {e}")
            self._log_audit(
                f"2FA认证异常: 用户={username}, 错误={str(e)}, IP={remote_ip}",
                level="ERROR"
            )
            
            return {
                'success': False,
                'error': 'Authentication error',
                'message': '认证过程发生异常',
                'session_id': auth_session_id
            }
    
    def verify_code(self, username: str, verification_code: str, 
                   remote_ip: str = "unknown", session_id: str = None) -> Dict[str, Any]:
        """
        验证短信验证码
        
        Args:
            username: 用户名
            verification_code: 验证码
            remote_ip: 远程IP地址
            session_id: 认证会话ID
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 记录验证开始
            self._log_audit(
                f"验证码验证开始: 用户={username}, IP={remote_ip}, 会话={session_id}"
            )
            
            # 检查用户是否被锁定
            if self._is_user_locked(username, remote_ip):
                self._log_audit(
                    f"验证时用户被锁定: 用户={username}, IP={remote_ip}",
                    level="WARNING"
                )
                return {
                    'success': False,
                    'error': 'User locked',
                    'message': f'用户已被锁定，请{self.config.lockout_duration//60}分钟后再试'
                }
            
            # 获取用户手机号
            phone_number = self.user_config.get_user_phone(username)
            if not phone_number:
                return {
                    'success': False,
                    'error': 'Phone number not configured',
                    'message': '用户手机号未配置'
                }
            
            # 验证验证码
            result = self.sms_manager.verify_code(username, phone_number, verification_code)
            
            if result['success']:
                # 验证成功，重置登录尝试
                self._reset_login_attempts(username, remote_ip)
                
                self._log_audit(
                    f"2FA认证成功: 用户={username}, IP={remote_ip}, 会话={session_id}"
                )
                
                return {
                    'success': True,
                    'message': '双重认证成功',
                    'authenticated_at': datetime.now().isoformat()
                }
            else:
                # 验证失败，记录尝试
                self._record_login_attempt(username, remote_ip, False)
                
                # 添加失败延迟
                time.sleep(self.config.fail_delay)
                
                self._log_audit(
                    f"验证码验证失败: 用户={username}, 错误={result.get('error')}, IP={remote_ip}",
                    level="WARNING"
                )
                
                return {
                    'success': False,
                    'error': result.get('error', 'Verification failed'),
                    'message': result.get('message', '验证码验证失败'),
                    'remaining_attempts': self._get_remaining_attempts(username, remote_ip)
                }
                
        except Exception as e:
            logger.error(f"验证码验证异常: {username}, Error: {e}")
            self._log_audit(
                f"验证码验证异常: 用户={username}, 错误={str(e)}, IP={remote_ip}",
                level="ERROR"
            )
            
            return {
                'success': False,
                'error': 'Verification error',
                'message': '验证过程发生异常'
            }
    
    def resend_code(self, username: str, remote_ip: str = "unknown") -> Dict[str, Any]:
        """
        重新发送验证码
        
        Args:
            username: 用户名
            remote_ip: 远程IP地址
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            self._log_audit(
                f"重发验证码请求: 用户={username}, IP={remote_ip}"
            )
            
            # 检查用户是否被锁定
            if self._is_user_locked(username, remote_ip):
                return {
                    'success': False,
                    'error': 'User locked',
                    'message': f'用户已被锁定，请{self.config.lockout_duration//60}分钟后再试'
                }
            
            # 获取用户手机号
            phone_number = self.user_config.get_user_phone(username)
            if not phone_number:
                return {
                    'success': False,
                    'error': 'Phone number not configured',
                    'message': '用户手机号未配置'
                }
            
            # 重新发送验证码
            result = self.sms_manager.send_code(username, phone_number)
            
            if result['success']:
                self._log_audit(
                    f"验证码重发成功: 用户={username}, 手机={self._mask_phone(phone_number)}, IP={remote_ip}"
                )
            else:
                self._log_audit(
                    f"验证码重发失败: 用户={username}, 错误={result.get('error')}, IP={remote_ip}",
                    level="WARNING"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"重发验证码异常: {username}, Error: {e}")
            return {
                'success': False,
                'error': 'Resend error',
                'message': '重发验证码失败'
            }
    
    def _should_bypass_user(self, username: str) -> bool:
        """检查用户是否应该绕过2FA"""
        if not self.config.enable_bypass_users:
            return False
        
        return username in self.config.bypass_users
    
    def _is_user_locked(self, username: str, remote_ip: str) -> bool:
        """检查用户是否被锁定"""
        key = f"{username}:{remote_ip}"
        
        if key in self._login_attempts:
            attempts_data = self._login_attempts[key]
            
            # 检查是否超过最大尝试次数
            if attempts_data['count'] >= self.config.max_login_attempts:
                # 检查锁定是否已过期
                if time.time() - attempts_data['first_attempt'] < self.config.lockout_duration:
                    return True
                else:
                    # 锁定已过期，重置
                    del self._login_attempts[key]
        
        return False
    
    def _record_login_attempt(self, username: str, remote_ip: str, success: bool):
        """记录登录尝试"""
        key = f"{username}:{remote_ip}"
        current_time = time.time()
        
        if success:
            # 成功登录，重置尝试记录
            self._login_attempts.pop(key, None)
        else:
            # 失败登录，记录尝试
            if key not in self._login_attempts:
                self._login_attempts[key] = {
                    'count': 1,
                    'first_attempt': current_time,
                    'last_attempt': current_time
                }
            else:
                self._login_attempts[key]['count'] += 1
                self._login_attempts[key]['last_attempt'] = current_time
    
    def _reset_login_attempts(self, username: str, remote_ip: str):
        """重置登录尝试"""
        key = f"{username}:{remote_ip}"
        self._login_attempts.pop(key, None)
    
    def _get_remaining_attempts(self, username: str, remote_ip: str) -> int:
        """获取剩余尝试次数"""
        key = f"{username}:{remote_ip}"
        
        if key in self._login_attempts:
            used_attempts = self._login_attempts[key]['count']
            return max(0, self.config.max_login_attempts - used_attempts)
        
        return self.config.max_login_attempts
    
    def _mask_phone(self, phone_number: str) -> str:
        """掩码手机号"""
        if not phone_number:
            return ""
        
        if len(phone_number) <= 4:
            return phone_number
        
        # 保留前3位和后2位，中间用*替换
        return phone_number[:3] + "*" * (len(phone_number) - 5) + phone_number[-2:]
    
    def _generate_session_id(self, username: str, remote_ip: str) -> str:
        """生成认证会话ID"""
        data = f"{username}:{remote_ip}:{time.time()}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _log_audit(self, message: str, level: str = "INFO"):
        """记录审计日志"""
        if self.config.enable_audit_log:
            logger.bind(audit=True).log(level, message)
    
    def get_user_status(self, username: str) -> Dict[str, Any]:
        """
        获取用户状态
        
        Args:
            username: 用户名
            
        Returns:
            Dict[str, Any]: 用户状态信息
        """
        try:
            phone_number = self.user_config.get_user_phone(username)
            
            return {
                'username': username,
                'phone_configured': bool(phone_number),
                'phone_masked': self._mask_phone(phone_number) if phone_number else None,
                'bypass_enabled': self._should_bypass_user(username),
                '2fa_required': bool(phone_number) and not self._should_bypass_user(username)
            }
            
        except Exception as e:
            logger.error(f"获取用户状态失败: {username}, Error: {e}")
            return {
                'username': username,
                'error': str(e)
            }
    
    def cleanup_expired_sessions(self):
        """清理过期的会话和尝试记录"""
        try:
            current_time = time.time()
            expired_keys = []
            
            # 清理过期的登录尝试记录
            for key, data in self._login_attempts.items():
                if current_time - data['first_attempt'] > self.config.lockout_duration:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._login_attempts[key]
            
            if expired_keys:
                logger.info(f"清理了 {len(expired_keys)} 个过期的登录尝试记录")
                
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")


class SMS2FAManager:
    """SMS 2FA 管理器"""
    
    def __init__(self, config_file: str = "/etc/sms-2fa/2fa.conf"):
        """
        初始化管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.authenticator = SMS2FAAuthenticator(config_file)
        self.user_config = UserConfig()
    
    def add_user(self, username: str, phone_number: str) -> Dict[str, Any]:
        """
        添加用户
        
        Args:
            username: 用户名
            phone_number: 手机号
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 验证手机号格式
            from .aliyun_sms import AliyunSMSClient
            sms_client = AliyunSMSClient(self.authenticator.config)
            
            if not sms_client._validate_phone_number(phone_number):
                return {
                    'success': False,
                    'error': 'Invalid phone number format',
                    'message': '手机号格式无效'
                }
            
            # 设置用户手机号
            self.user_config.set_user_phone(username, phone_number)
            self.user_config.save()
            
            logger.info(f"用户添加成功: {username} -> {phone_number}")
            
            return {
                'success': True,
                'message': f'用户 {username} 添加成功'
            }
            
        except Exception as e:
            logger.error(f"添加用户失败: {username}, Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '添加用户失败'
            }
    
    def remove_user(self, username: str) -> Dict[str, Any]:
        """
        删除用户
        
        Args:
            username: 用户名
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if self.user_config.remove_user(username):
                self.user_config.save()
                logger.info(f"用户删除成功: {username}")
                
                return {
                    'success': True,
                    'message': f'用户 {username} 删除成功'
                }
            else:
                return {
                    'success': False,
                    'error': 'User not found',
                    'message': f'用户 {username} 不存在'
                }
                
        except Exception as e:
            logger.error(f"删除用户失败: {username}, Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '删除用户失败'
            }
    
    def list_users(self) -> Dict[str, Any]:
        """
        列出所有用户
        
        Returns:
            Dict[str, Any]: 用户列表
        """
        try:
            users = self.user_config.list_users()
            
            # 为每个用户添加状态信息
            user_list = []
            for username, phone in users.items():
                status = self.authenticator.get_user_status(username)
                user_list.append({
                    'username': username,
                    'phone_number': phone,
                    'phone_masked': status.get('phone_masked'),
                    'bypass_enabled': status.get('bypass_enabled', False)
                })
            
            return {
                'success': True,
                'users': user_list,
                'total_count': len(user_list)
            }
            
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取用户列表失败'
            }
    
    def test_user_sms(self, username: str) -> Dict[str, Any]:
        """
        测试用户短信发送
        
        Args:
            username: 用户名
            
        Returns:
            Dict[str, Any]: 测试结果
        """
        try:
            phone_number = self.user_config.get_user_phone(username)
            if not phone_number:
                return {
                    'success': False,
                    'error': 'Phone number not configured',
                    'message': f'用户 {username} 手机号未配置'
                }
            
            # 发送测试验证码
            result = self.authenticator.sms_manager.send_code(username, phone_number)
            
            if result['success']:
                logger.info(f"用户短信测试成功: {username} -> {phone_number}")
            else:
                logger.warning(f"用户短信测试失败: {username} -> {phone_number}, {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"测试用户短信失败: {username}, Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '短信测试失败'
            }


def main():
    """主函数，用于命令行测试"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python sms_2fa.py <command> [args...]")
        print("命令:")
        print("  auth <username> - 发起认证")
        print("  verify <username> <code> - 验证验证码")
        print("  status <username> - 查看用户状态")
        return
    
    command = sys.argv[1]
    authenticator = SMS2FAAuthenticator()
    
    if command == "auth" and len(sys.argv) >= 3:
        username = sys.argv[2]
        result = authenticator.authenticate(username)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif command == "verify" and len(sys.argv) >= 4:
        username = sys.argv[2]
        code = sys.argv[3]
        result = authenticator.verify_code(username, code)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    elif command == "status" and len(sys.argv) >= 3:
        username = sys.argv[2]
        result = authenticator.get_user_status(username)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    else:
        print("无效的命令或参数")


if __name__ == "__main__":
    main()