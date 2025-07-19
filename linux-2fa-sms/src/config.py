#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
处理系统配置文件的加载和验证
"""

import os
import configparser
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from loguru import logger


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: str = "/etc/sms-2fa/2fa.conf"):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._encryption_key = None
        
        # 默认配置值
        self._defaults = {
            # 阿里云短信配置
            'aliyun_access_key_id': '',
            'aliyun_access_key_secret': '',
            'aliyun_region': 'cn-hangzhou',
            'aliyun_sign_name': '',
            'aliyun_template_code': '',
            
            # 验证码配置
            'code_expire_time': 300,  # 5分钟
            'code_length': 6,
            'max_send_per_minute': 3,
            'max_verify_attempts': 5,
            
            # 系统配置
            'log_level': 'INFO',
            'log_file': '/var/log/sms-2fa/sms-2fa.log',
            'enable_redis': False,
            'redis_host': 'localhost',
            'redis_port': 6379,
            'redis_db': 0,
            'redis_password': '',
            
            # 安全配置
            'enable_encryption': True,
            'fail_delay': 3,  # 失败后延迟秒数
            'max_login_attempts': 5,
            'lockout_duration': 1800,  # 30分钟
            
            # PAM配置
            'pam_service_name': 'sms-2fa',
            'enable_bypass_users': True,
            'bypass_users': 'root',  # 逗号分隔的用户列表
            
            # 审计配置
            'enable_audit_log': True,
            'audit_log_file': '/var/log/sms-2fa/audit.log',
            'audit_log_level': 'INFO'
        }
        
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                logger.warning(f"配置文件不存在，使用默认配置: {self.config_file}")
                self._create_default_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            raise
    
    def _create_default_config(self):
        """创建默认配置文件"""
        try:
            # 创建配置目录
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, mode=0o755, exist_ok=True)
            
            # 创建默认配置
            self.config['aliyun'] = {
                'access_key_id': 'YOUR_ACCESS_KEY_ID',
                'access_key_secret': 'YOUR_ACCESS_KEY_SECRET',
                'region': 'cn-hangzhou',
                'sign_name': '您的签名',
                'template_code': 'SMS_123456789'
            }
            
            self.config['sms'] = {
                'code_expire_time': '300',
                'code_length': '6',
                'max_send_per_minute': '3',
                'max_verify_attempts': '5'
            }
            
            self.config['system'] = {
                'log_level': 'INFO',
                'log_file': '/var/log/sms-2fa/sms-2fa.log',
                'enable_redis': 'false',
                'redis_host': 'localhost',
                'redis_port': '6379',
                'redis_db': '0',
                'redis_password': ''
            }
            
            self.config['security'] = {
                'enable_encryption': 'true',
                'fail_delay': '3',
                'max_login_attempts': '5',
                'lockout_duration': '1800'
            }
            
            self.config['pam'] = {
                'service_name': 'sms-2fa',
                'enable_bypass_users': 'true',
                'bypass_users': 'root'
            }
            
            self.config['audit'] = {
                'enable_audit_log': 'true',
                'audit_log_file': '/var/log/sms-2fa/audit.log',
                'audit_log_level': 'INFO'
            }
            
            # 保存配置文件
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            
            # 设置文件权限
            os.chmod(self.config_file, 0o600)
            
            logger.info(f"默认配置文件创建成功: {self.config_file}")
            
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
            raise
    
    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            section: 配置节
            key: 配置键
            fallback: 默认值
            
        Returns:
            配置值
        """
        try:
            if self.config.has_option(section, key):
                value = self.config.get(section, key)
                
                # 解密敏感配置
                if self._is_sensitive_key(key) and self.enable_encryption:
                    value = self._decrypt_value(value)
                
                return value
            else:
                # 使用默认值
                default_key = f"{section}_{key}" if section else key
                return self._defaults.get(default_key, fallback)
        except Exception as e:
            logger.error(f"获取配置失败: {section}.{key}, Error: {e}")
            return fallback
    
    def set(self, section: str, key: str, value: Any):
        """
        设置配置值
        
        Args:
            section: 配置节
            key: 配置键
            value: 配置值
        """
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            # 加密敏感配置
            if self._is_sensitive_key(key) and self.enable_encryption:
                value = self._encrypt_value(str(value))
            
            self.config.set(section, key, str(value))
            
        except Exception as e:
            logger.error(f"设置配置失败: {section}.{key}, Error: {e}")
            raise
    
    def save(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            
            # 设置文件权限
            os.chmod(self.config_file, 0o600)
            
            logger.info(f"配置文件保存成功: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise
    
    def _is_sensitive_key(self, key: str) -> bool:
        """判断是否为敏感配置项"""
        sensitive_keys = [
            'access_key_secret',
            'password',
            'secret',
            'token',
            'key'
        ]
        return any(sensitive in key.lower() for sensitive in sensitive_keys)
    
    def _get_encryption_key(self) -> bytes:
        """获取加密密钥"""
        if self._encryption_key is None:
            key_file = "/etc/sms-2fa/.encryption_key"
            
            try:
                if os.path.exists(key_file):
                    with open(key_file, 'rb') as f:
                        self._encryption_key = f.read()
                else:
                    # 生成新密钥
                    self._encryption_key = Fernet.generate_key()
                    
                    # 创建目录并保存密钥
                    os.makedirs(os.path.dirname(key_file), mode=0o700, exist_ok=True)
                    with open(key_file, 'wb') as f:
                        f.write(self._encryption_key)
                    
                    # 设置文件权限
                    os.chmod(key_file, 0o600)
                    
            except Exception as e:
                logger.error(f"获取加密密钥失败: {e}")
                # 使用默认密钥
                self._encryption_key = Fernet.generate_key()
        
        return self._encryption_key
    
    def _encrypt_value(self, value: str) -> str:
        """加密配置值"""
        try:
            f = Fernet(self._get_encryption_key())
            encrypted = f.encrypt(value.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"加密配置值失败: {e}")
            return value
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """解密配置值"""
        try:
            f = Fernet(self._get_encryption_key())
            decrypted = f.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"解密配置值失败: {e}")
            return encrypted_value
    
    # 属性访问器
    @property
    def aliyun_access_key_id(self) -> str:
        """阿里云AccessKey ID"""
        return self.get('aliyun', 'access_key_id', self._defaults['aliyun_access_key_id'])
    
    @property
    def aliyun_access_key_secret(self) -> str:
        """阿里云AccessKey Secret"""
        return self.get('aliyun', 'access_key_secret', self._defaults['aliyun_access_key_secret'])
    
    @property
    def aliyun_region(self) -> str:
        """阿里云地域"""
        return self.get('aliyun', 'region', self._defaults['aliyun_region'])
    
    @property
    def aliyun_sign_name(self) -> str:
        """阿里云短信签名"""
        return self.get('aliyun', 'sign_name', self._defaults['aliyun_sign_name'])
    
    @property
    def aliyun_template_code(self) -> str:
        """阿里云短信模板代码"""
        return self.get('aliyun', 'template_code', self._defaults['aliyun_template_code'])
    
    @property
    def code_expire_time(self) -> int:
        """验证码过期时间（秒）"""
        return int(self.get('sms', 'code_expire_time', self._defaults['code_expire_time']))
    
    @property
    def code_length(self) -> int:
        """验证码长度"""
        return int(self.get('sms', 'code_length', self._defaults['code_length']))
    
    @property
    def max_send_per_minute(self) -> int:
        """每分钟最大发送次数"""
        return int(self.get('sms', 'max_send_per_minute', self._defaults['max_send_per_minute']))
    
    @property
    def max_verify_attempts(self) -> int:
        """最大验证尝试次数"""
        return int(self.get('sms', 'max_verify_attempts', self._defaults['max_verify_attempts']))
    
    @property
    def log_level(self) -> str:
        """日志级别"""
        return self.get('system', 'log_level', self._defaults['log_level'])
    
    @property
    def log_file(self) -> str:
        """日志文件路径"""
        return self.get('system', 'log_file', self._defaults['log_file'])
    
    @property
    def enable_redis(self) -> bool:
        """是否启用Redis"""
        return self.get('system', 'enable_redis', 'false').lower() == 'true'
    
    @property
    def redis_host(self) -> str:
        """Redis主机"""
        return self.get('system', 'redis_host', self._defaults['redis_host'])
    
    @property
    def redis_port(self) -> int:
        """Redis端口"""
        return int(self.get('system', 'redis_port', self._defaults['redis_port']))
    
    @property
    def redis_db(self) -> int:
        """Redis数据库"""
        return int(self.get('system', 'redis_db', self._defaults['redis_db']))
    
    @property
    def redis_password(self) -> str:
        """Redis密码"""
        return self.get('system', 'redis_password', self._defaults['redis_password'])
    
    @property
    def enable_encryption(self) -> bool:
        """是否启用加密"""
        return self.get('security', 'enable_encryption', 'true').lower() == 'true'
    
    @property
    def fail_delay(self) -> int:
        """失败延迟时间（秒）"""
        return int(self.get('security', 'fail_delay', self._defaults['fail_delay']))
    
    @property
    def max_login_attempts(self) -> int:
        """最大登录尝试次数"""
        return int(self.get('security', 'max_login_attempts', self._defaults['max_login_attempts']))
    
    @property
    def lockout_duration(self) -> int:
        """锁定持续时间（秒）"""
        return int(self.get('security', 'lockout_duration', self._defaults['lockout_duration']))
    
    @property
    def pam_service_name(self) -> str:
        """PAM服务名称"""
        return self.get('pam', 'service_name', self._defaults['pam_service_name'])
    
    @property
    def enable_bypass_users(self) -> bool:
        """是否启用绕过用户"""
        return self.get('pam', 'enable_bypass_users', 'true').lower() == 'true'
    
    @property
    def bypass_users(self) -> list:
        """绕过用户列表"""
        users_str = self.get('pam', 'bypass_users', self._defaults['bypass_users'])
        return [user.strip() for user in users_str.split(',') if user.strip()]
    
    @property
    def enable_audit_log(self) -> bool:
        """是否启用审计日志"""
        return self.get('audit', 'enable_audit_log', 'true').lower() == 'true'
    
    @property
    def audit_log_file(self) -> str:
        """审计日志文件路径"""
        return self.get('audit', 'audit_log_file', self._defaults['audit_log_file'])
    
    @property
    def audit_log_level(self) -> str:
        """审计日志级别"""
        return self.get('audit', 'audit_log_level', self._defaults['audit_log_level'])
    
    def validate(self) -> Dict[str, list]:
        """
        验证配置
        
        Returns:
            Dict[str, list]: 验证结果，包含errors和warnings
        """
        errors = []
        warnings = []
        
        # 验证阿里云配置
        if not self.aliyun_access_key_id:
            errors.append("阿里云AccessKey ID未配置")
        
        if not self.aliyun_access_key_secret:
            errors.append("阿里云AccessKey Secret未配置")
        
        if not self.aliyun_sign_name:
            errors.append("阿里云短信签名未配置")
        
        if not self.aliyun_template_code:
            errors.append("阿里云短信模板代码未配置")
        
        # 验证验证码配置
        if self.code_expire_time < 60:
            warnings.append("验证码过期时间过短，建议设置为60秒以上")
        
        if self.code_expire_time > 1800:
            warnings.append("验证码过期时间过长，建议设置为30分钟以内")
        
        if self.code_length < 4:
            warnings.append("验证码长度过短，建议设置为4位以上")
        
        if self.max_send_per_minute > 10:
            warnings.append("每分钟发送次数过多，建议控制在10次以内")
        
        # 验证Redis配置
        if self.enable_redis:
            if not self.redis_host:
                errors.append("Redis主机地址未配置")
            
            if self.redis_port < 1 or self.redis_port > 65535:
                errors.append("Redis端口配置无效")
        
        # 验证文件路径
        log_dir = os.path.dirname(self.log_file)
        if not os.path.exists(log_dir):
            warnings.append(f"日志目录不存在: {log_dir}")
        
        audit_log_dir = os.path.dirname(self.audit_log_file)
        if not os.path.exists(audit_log_dir):
            warnings.append(f"审计日志目录不存在: {audit_log_dir}")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            Dict[str, Any]: 配置摘要
        """
        return {
            'config_file': self.config_file,
            'aliyun_region': self.aliyun_region,
            'code_expire_time': self.code_expire_time,
            'code_length': self.code_length,
            'enable_redis': self.enable_redis,
            'enable_encryption': self.enable_encryption,
            'enable_audit_log': self.enable_audit_log,
            'bypass_users_count': len(self.bypass_users),
            'log_level': self.log_level
        }


class UserConfig:
    """用户配置管理类"""
    
    def __init__(self, config_file: str = "/etc/sms-2fa/users.conf"):
        """
        初始化用户配置
        
        Args:
            config_file: 用户配置文件路径
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _load_config(self):
        """加载用户配置文件"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                logger.info(f"用户配置文件加载成功: {self.config_file}")
            else:
                logger.warning(f"用户配置文件不存在，创建默认配置: {self.config_file}")
                self._create_default_config()
        except Exception as e:
            logger.error(f"加载用户配置文件失败: {e}")
            raise
    
    def _create_default_config(self):
        """创建默认用户配置文件"""
        try:
            # 创建配置目录
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, mode=0o755, exist_ok=True)
            
            # 创建默认用户配置
            self.config['users'] = {
                '# 格式: username = phone_number': '',
                '# 示例: admin = +8613812345678': ''
            }
            
            # 保存配置文件
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            
            # 设置文件权限
            os.chmod(self.config_file, 0o600)
            
            logger.info(f"默认用户配置文件创建成功: {self.config_file}")
            
        except Exception as e:
            logger.error(f"创建默认用户配置文件失败: {e}")
            raise
    
    def get_user_phone(self, username: str) -> Optional[str]:
        """
        获取用户手机号
        
        Args:
            username: 用户名
            
        Returns:
            Optional[str]: 手机号，如果用户不存在则返回None
        """
        try:
            if self.config.has_option('users', username):
                return self.config.get('users', username)
        except Exception as e:
            logger.error(f"获取用户手机号失败: {username}, Error: {e}")
        
        return None
    
    def set_user_phone(self, username: str, phone_number: str):
        """
        设置用户手机号
        
        Args:
            username: 用户名
            phone_number: 手机号
        """
        try:
            if not self.config.has_section('users'):
                self.config.add_section('users')
            
            self.config.set('users', username, phone_number)
            
        except Exception as e:
            logger.error(f"设置用户手机号失败: {username}, Error: {e}")
            raise
    
    def remove_user(self, username: str) -> bool:
        """
        删除用户
        
        Args:
            username: 用户名
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if self.config.has_option('users', username):
                self.config.remove_option('users', username)
                return True
        except Exception as e:
            logger.error(f"删除用户失败: {username}, Error: {e}")
        
        return False
    
    def list_users(self) -> Dict[str, str]:
        """
        列出所有用户
        
        Returns:
            Dict[str, str]: 用户名到手机号的映射
        """
        try:
            if self.config.has_section('users'):
                users = {}
                for username, phone in self.config.items('users'):
                    # 跳过注释行
                    if not username.startswith('#'):
                        users[username] = phone
                return users
        except Exception as e:
            logger.error(f"列出用户失败: {e}")
        
        return {}
    
    def save(self):
        """保存用户配置到文件"""
        try:
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            
            # 设置文件权限
            os.chmod(self.config_file, 0o600)
            
            logger.info(f"用户配置文件保存成功: {self.config_file}")
            
        except Exception as e:
            logger.error(f"保存用户配置文件失败: {e}")
            raise


if __name__ == "__main__":
    # 测试配置管理
    config = Config("/tmp/test_2fa.conf")
    print("配置摘要:", config.get_summary())
    
    validation = config.validate()
    if validation['errors']:
        print("配置错误:", validation['errors'])
    if validation['warnings']:
        print("配置警告:", validation['warnings'])
    
    # 测试用户配置
    user_config = UserConfig("/tmp/test_users.conf")
    user_config.set_user_phone("testuser", "+8613812345678")
    user_config.save()
    
    print("用户手机号:", user_config.get_user_phone("testuser"))
    print("所有用户:", user_config.list_users())