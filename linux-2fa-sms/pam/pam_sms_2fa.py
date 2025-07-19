#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PAM SMS 2FA 模块
与Linux PAM系统集成的双重因子认证模块
"""

import sys
import os
import getpass
import time
from typing import Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from src.sms_2fa import SMS2FAAuthenticator
    from src.config import Config
except ImportError:
    # 如果直接执行此文件，使用相对路径
    from sms_2fa import SMS2FAAuthenticator
    from config import Config


def pam_sm_authenticate(pamh, flags, argv):
    """
    PAM认证模块入口点
    
    Args:
        pamh: PAM句柄
        flags: PAM标志
        argv: 参数列表
        
    Returns:
        int: PAM认证结果
    """
    try:
        # PAM返回码
        PAM_SUCCESS = 0
        PAM_AUTH_ERR = 7
        PAM_USER_UNKNOWN = 10
        PAM_CRED_INSUFFICIENT = 8
        PAM_MAXTRIES = 25
        
        # 获取用户名
        try:
            username = pamh.get_user()
        except Exception:
            return PAM_USER_UNKNOWN
        
        if not username:
            return PAM_USER_UNKNOWN
        
        # 获取远程IP
        remote_ip = pamh.rhost if hasattr(pamh, 'rhost') and pamh.rhost else "unknown"
        
        # 初始化认证器
        config_file = "/etc/sms-2fa/2fa.conf"
        for arg in argv:
            if arg.startswith("config="):
                config_file = arg.split("=", 1)[1]
        
        authenticator = SMS2FAAuthenticator(config_file)
        
        # 检查用户是否需要绕过2FA
        config = Config(config_file)
        if config.enable_bypass_users and username in config.bypass_users:
            return PAM_SUCCESS
        
        # 获取用户手机号
        phone_number = authenticator.user_config.get_user_phone(username)
        if not phone_number:
            pamh.conversation(pamh.Message(pamh.PAM_ERROR_MSG, 
                                         "SMS 2FA: 用户手机号未配置，请联系管理员"))
            return PAM_CRED_INSUFFICIENT
        
        # 发送验证码
        auth_result = authenticator.authenticate(username, remote_ip)
        
        if not auth_result['success']:
            if 'locked' in auth_result.get('error', '').lower():
                pamh.conversation(pamh.Message(pamh.PAM_ERROR_MSG, 
                                             auth_result.get('message', '用户已被锁定')))
                return PAM_MAXTRIES
            else:
                pamh.conversation(pamh.Message(pamh.PAM_ERROR_MSG, 
                                             auth_result.get('message', '验证码发送失败')))
                return PAM_AUTH_ERR
        
        # 如果用户被绕过
        if auth_result.get('bypassed'):
            return PAM_SUCCESS
        
        # 提示用户输入验证码
        session_id = auth_result.get('session_id')
        max_attempts = config.max_verify_attempts
        
        for attempt in range(max_attempts):
            try:
                # 提示输入验证码
                prompt = f"SMS验证码已发送到 {auth_result.get('phone_masked', 'your phone')}"
                if attempt > 0:
                    prompt += f" (剩余尝试: {max_attempts - attempt})"
                prompt += ": "
                
                resp = pamh.conversation(pamh.Message(pamh.PAM_PROMPT_ECHO_OFF, prompt))
                verification_code = resp.resp
                
                if not verification_code:
                    continue
                
                # 验证验证码
                verify_result = authenticator.verify_code(
                    username, verification_code, remote_ip, session_id
                )
                
                if verify_result['success']:
                    pamh.conversation(pamh.Message(pamh.PAM_TEXT_INFO, 
                                                 "SMS 2FA 认证成功"))
                    return PAM_SUCCESS
                else:
                    error_msg = verify_result.get('message', '验证码错误')
                    if attempt < max_attempts - 1:
                        pamh.conversation(pamh.Message(pamh.PAM_ERROR_MSG, 
                                                     f"{error_msg}，请重试"))
                    else:
                        pamh.conversation(pamh.Message(pamh.PAM_ERROR_MSG, 
                                                     f"{error_msg}，认证失败"))
                
            except Exception as e:
                pamh.conversation(pamh.Message(pamh.PAM_ERROR_MSG, 
                                             f"验证过程发生错误: {str(e)}"))
                return PAM_AUTH_ERR
        
        return PAM_AUTH_ERR
        
    except Exception as e:
        try:
            pamh.conversation(pamh.Message(pamh.PAM_ERROR_MSG, 
                                         f"SMS 2FA 认证模块错误: {str(e)}"))
        except:
            pass
        return PAM_AUTH_ERR


def pam_sm_setcred(pamh, flags, argv):
    """
    PAM设置凭据模块
    
    Args:
        pamh: PAM句柄
        flags: PAM标志
        argv: 参数列表
        
    Returns:
        int: PAM结果
    """
    return 0  # PAM_SUCCESS


def pam_sm_acct_mgmt(pamh, flags, argv):
    """
    PAM账户管理模块
    
    Args:
        pamh: PAM句柄
        flags: PAM标志
        argv: 参数列表
        
    Returns:
        int: PAM结果
    """
    return 0  # PAM_SUCCESS


def pam_sm_open_session(pamh, flags, argv):
    """
    PAM打开会话模块
    
    Args:
        pamh: PAM句柄
        flags: PAM标志
        argv: 参数列表
        
    Returns:
        int: PAM结果
    """
    return 0  # PAM_SUCCESS


def pam_sm_close_session(pamh, flags, argv):
    """
    PAM关闭会话模块
    
    Args:
        pamh: PAM句柄
        flags: PAM标志
        argv: 参数列表
        
    Returns:
        int: PAM结果
    """
    return 0  # PAM_SUCCESS


def pam_sm_chauthtok(pamh, flags, argv):
    """
    PAM更改认证令牌模块
    
    Args:
        pamh: PAM句柄
        flags: PAM标志
        argv: 参数列表
        
    Returns:
        int: PAM结果
    """
    return 0  # PAM_SUCCESS


class InteractiveSMS2FA:
    """交互式SMS 2FA认证类，用于命令行测试"""
    
    def __init__(self, config_file: str = "/etc/sms-2fa/2fa.conf"):
        """
        初始化交互式认证
        
        Args:
            config_file: 配置文件路径
        """
        self.authenticator = SMS2FAAuthenticator(config_file)
    
    def authenticate_user(self, username: str, remote_ip: str = "127.0.0.1") -> bool:
        """
        交互式用户认证
        
        Args:
            username: 用户名
            remote_ip: 远程IP地址
            
        Returns:
            bool: 认证是否成功
        """
        try:
            print(f"开始为用户 {username} 进行SMS双重因子认证...")
            
            # 发送验证码
            auth_result = self.authenticator.authenticate(username, remote_ip)
            
            if not auth_result['success']:
                print(f"错误: {auth_result.get('message', '认证失败')}")
                return False
            
            # 如果用户被绕过
            if auth_result.get('bypassed'):
                print("用户已绕过双重认证")
                return True
            
            print(auth_result.get('message', '验证码已发送'))
            
            # 输入验证码
            session_id = auth_result.get('session_id')
            max_attempts = self.authenticator.config.max_verify_attempts
            
            for attempt in range(max_attempts):
                try:
                    prompt = "请输入收到的验证码"
                    if attempt > 0:
                        prompt += f" (剩余尝试: {max_attempts - attempt})"
                    prompt += ": "
                    
                    verification_code = getpass.getpass(prompt)
                    
                    if not verification_code.strip():
                        print("验证码不能为空，请重试")
                        continue
                    
                    # 验证验证码
                    verify_result = self.authenticator.verify_code(
                        username, verification_code.strip(), remote_ip, session_id
                    )
                    
                    if verify_result['success']:
                        print("✅ SMS双重因子认证成功！")
                        return True
                    else:
                        error_msg = verify_result.get('message', '验证码错误')
                        if attempt < max_attempts - 1:
                            print(f"❌ {error_msg}，请重试")
                        else:
                            print(f"❌ {error_msg}，认证失败")
                
                except KeyboardInterrupt:
                    print("\n认证已取消")
                    return False
                except Exception as e:
                    print(f"验证过程发生错误: {e}")
                    return False
            
            return False
            
        except Exception as e:
            print(f"认证过程发生异常: {e}")
            return False
    
    def test_sms_send(self, username: str) -> bool:
        """
        测试短信发送
        
        Args:
            username: 用户名
            
        Returns:
            bool: 测试是否成功
        """
        try:
            phone_number = self.authenticator.user_config.get_user_phone(username)
            if not phone_number:
                print(f"错误: 用户 {username} 手机号未配置")
                return False
            
            print(f"测试向用户 {username} ({self.authenticator._mask_phone(phone_number)}) 发送短信...")
            
            result = self.authenticator.sms_manager.send_code(username, phone_number)
            
            if result['success']:
                print("✅ 短信发送成功！")
                return True
            else:
                print(f"❌ 短信发送失败: {result.get('message')}")
                return False
                
        except Exception as e:
            print(f"测试短信发送异常: {e}")
            return False


def main():
    """主函数，用于命令行测试PAM模块"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SMS 2FA PAM模块测试工具")
    parser.add_argument("command", choices=["test", "auth", "send"], 
                       help="命令: test(测试配置), auth(认证用户), send(测试短信)")
    parser.add_argument("username", nargs="?", help="用户名")
    parser.add_argument("--config", default="/etc/sms-2fa/2fa.conf", 
                       help="配置文件路径")
    parser.add_argument("--ip", default="127.0.0.1", help="远程IP地址")
    
    args = parser.parse_args()
    
    if args.command == "test":
        # 测试配置
        try:
            config = Config(args.config)
            validation = config.validate()
            
            print("📋 配置验证结果:")
            if validation['errors']:
                print("❌ 错误:")
                for error in validation['errors']:
                    print(f"   - {error}")
            
            if validation['warnings']:
                print("⚠️  警告:")
                for warning in validation['warnings']:
                    print(f"   - {warning}")
            
            if not validation['errors'] and not validation['warnings']:
                print("✅ 配置验证通过")
            
            print("\n📊 配置摘要:")
            summary = config.get_summary()
            for key, value in summary.items():
                print(f"   {key}: {value}")
                
        except Exception as e:
            print(f"❌ 配置测试失败: {e}")
            return 1
    
    elif args.command == "auth":
        if not args.username:
            print("错误: 认证命令需要指定用户名")
            return 1
        
        # 交互式认证
        try:
            auth = InteractiveSMS2FA(args.config)
            success = auth.authenticate_user(args.username, args.ip)
            return 0 if success else 1
            
        except Exception as e:
            print(f"❌ 认证失败: {e}")
            return 1
    
    elif args.command == "send":
        if not args.username:
            print("错误: 发送命令需要指定用户名")
            return 1
        
        # 测试短信发送
        try:
            auth = InteractiveSMS2FA(args.config)
            success = auth.test_sms_send(args.username)
            return 0 if success else 1
            
        except Exception as e:
            print(f"❌ 短信发送测试失败: {e}")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(main())