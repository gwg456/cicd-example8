#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMS 2FA 用户管理工具
提供用户添加、删除、列表和测试功能
"""

import sys
import os
import argparse
import json
from typing import Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from src.sms_2fa import SMS2FAManager
    from src.config import Config, UserConfig
    from src.aliyun_sms import AliyunSMSClient
except ImportError:
    # 如果在安装环境中运行
    import sys
    sys.path.insert(0, '/opt/sms-2fa/src')
    from sms_2fa import SMS2FAManager
    from config import Config, UserConfig
    from aliyun_sms import AliyunSMSClient


class UserManagerCLI:
    """用户管理命令行工具"""
    
    def __init__(self, config_file: str = "/etc/sms-2fa/2fa.conf"):
        """
        初始化用户管理工具
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.manager = SMS2FAManager(config_file)
        self.config = Config(config_file)
        self.user_config = UserConfig()
    
    def add_user(self, username: str, phone_number: str, test_sms: bool = False) -> int:
        """
        添加用户
        
        Args:
            username: 用户名
            phone_number: 手机号
            test_sms: 是否测试短信发送
            
        Returns:
            int: 退出码
        """
        try:
            print(f"📱 添加用户: {username} -> {phone_number}")
            
            result = self.manager.add_user(username, phone_number)
            
            if result['success']:
                print(f"✅ {result['message']}")
                
                # 测试短信发送
                if test_sms:
                    print("\n📤 测试短信发送...")
                    test_result = self.manager.test_user_sms(username)
                    
                    if test_result['success']:
                        print("✅ 短信发送测试成功")
                    else:
                        print(f"❌ 短信发送测试失败: {test_result.get('message')}")
                        return 1
                
                return 0
            else:
                print(f"❌ {result['message']}")
                return 1
                
        except Exception as e:
            print(f"❌ 添加用户失败: {e}")
            return 1
    
    def remove_user(self, username: str, confirm: bool = False) -> int:
        """
        删除用户
        
        Args:
            username: 用户名
            confirm: 是否已确认删除
            
        Returns:
            int: 退出码
        """
        try:
            # 获取用户信息
            phone = self.user_config.get_user_phone(username)
            if not phone:
                print(f"❌ 用户 {username} 不存在")
                return 1
            
            # 确认删除
            if not confirm:
                print(f"⚠️  即将删除用户: {username} ({phone})")
                response = input("确认删除？ (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("取消删除")
                    return 0
            
            print(f"🗑️  删除用户: {username}")
            
            result = self.manager.remove_user(username)
            
            if result['success']:
                print(f"✅ {result['message']}")
                return 0
            else:
                print(f"❌ {result['message']}")
                return 1
                
        except Exception as e:
            print(f"❌ 删除用户失败: {e}")
            return 1
    
    def list_users(self, output_format: str = "table") -> int:
        """
        列出所有用户
        
        Args:
            output_format: 输出格式 (table, json, csv)
            
        Returns:
            int: 退出码
        """
        try:
            result = self.manager.list_users()
            
            if not result['success']:
                print(f"❌ 获取用户列表失败: {result.get('message')}")
                return 1
            
            users = result['users']
            
            if not users:
                print("📭 没有配置的用户")
                return 0
            
            if output_format == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            elif output_format == "csv":
                print("用户名,手机号,掩码手机号,绕过状态")
                for user in users:
                    bypass_status = "是" if user.get('bypass_enabled') else "否"
                    print(f"{user['username']},{user['phone_number']},{user.get('phone_masked', '')},{bypass_status}")
            else:  # table format
                print(f"\n📋 用户列表 (共 {len(users)} 个用户):")
                print("-" * 70)
                print(f"{'用户名':<15} {'手机号':<15} {'掩码显示':<12} {'绕过2FA':<8}")
                print("-" * 70)
                
                for user in users:
                    bypass_status = "✅" if user.get('bypass_enabled') else "❌"
                    print(f"{user['username']:<15} {user['phone_number']:<15} {user.get('phone_masked', ''):<12} {bypass_status:<8}")
                
                print("-" * 70)
            
            return 0
            
        except Exception as e:
            print(f"❌ 列出用户失败: {e}")
            return 1
    
    def test_user(self, username: str) -> int:
        """
        测试用户短信发送
        
        Args:
            username: 用户名
            
        Returns:
            int: 退出码
        """
        try:
            phone = self.user_config.get_user_phone(username)
            if not phone:
                print(f"❌ 用户 {username} 不存在")
                return 1
            
            print(f"📤 测试用户 {username} 短信发送...")
            print(f"📱 手机号: {phone}")
            
            result = self.manager.test_user_sms(username)
            
            if result['success']:
                print("✅ 短信发送成功")
                print(f"📊 BizId: {result.get('biz_id', 'N/A')}")
                print(f"⏰ 过期时间: {result.get('expires_in', 300)} 秒")
                return 0
            else:
                print(f"❌ 短信发送失败: {result.get('message')}")
                return 1
                
        except Exception as e:
            print(f"❌ 测试用户失败: {e}")
            return 1
    
    def show_user_status(self, username: str) -> int:
        """
        显示用户状态
        
        Args:
            username: 用户名
            
        Returns:
            int: 退出码
        """
        try:
            status = self.manager.authenticator.get_user_status(username)
            
            if 'error' in status:
                print(f"❌ 获取用户状态失败: {status['error']}")
                return 1
            
            print(f"\n👤 用户状态: {username}")
            print("-" * 40)
            print(f"手机号配置: {'✅ 已配置' if status['phone_configured'] else '❌ 未配置'}")
            
            if status['phone_configured']:
                print(f"手机号显示: {status['phone_masked']}")
            
            print(f"绕过2FA: {'✅ 是' if status['bypass_enabled'] else '❌ 否'}")
            print(f"需要2FA: {'✅ 是' if status['2fa_required'] else '❌ 否'}")
            
            return 0
            
        except Exception as e:
            print(f"❌ 获取用户状态失败: {e}")
            return 1
    
    def update_user(self, username: str, phone_number: str) -> int:
        """
        更新用户手机号
        
        Args:
            username: 用户名
            phone_number: 新手机号
            
        Returns:
            int: 退出码
        """
        try:
            old_phone = self.user_config.get_user_phone(username)
            if not old_phone:
                print(f"❌ 用户 {username} 不存在")
                return 1
            
            print(f"📝 更新用户 {username} 手机号:")
            print(f"   旧手机号: {old_phone}")
            print(f"   新手机号: {phone_number}")
            
            # 验证新手机号格式
            sms_client = AliyunSMSClient(self.config)
            if not sms_client._validate_phone_number(phone_number):
                print("❌ 新手机号格式无效")
                return 1
            
            # 更新手机号
            self.user_config.set_user_phone(username, phone_number)
            self.user_config.save()
            
            print("✅ 用户手机号更新成功")
            return 0
            
        except Exception as e:
            print(f"❌ 更新用户失败: {e}")
            return 1
    
    def validate_config(self) -> int:
        """
        验证配置
        
        Returns:
            int: 退出码
        """
        try:
            print("🔍 验证配置文件...")
            
            validation = self.config.validate()
            
            if validation['errors']:
                print("\n❌ 配置错误:")
                for error in validation['errors']:
                    print(f"   - {error}")
            
            if validation['warnings']:
                print("\n⚠️  配置警告:")
                for warning in validation['warnings']:
                    print(f"   - {warning}")
            
            if not validation['errors'] and not validation['warnings']:
                print("✅ 配置验证通过")
            
            print(f"\n📊 配置摘要:")
            summary = self.config.get_summary()
            for key, value in summary.items():
                print(f"   {key}: {value}")
            
            return 0 if not validation['errors'] else 1
            
        except Exception as e:
            print(f"❌ 验证配置失败: {e}")
            return 1
    
    def test_connection(self) -> int:
        """
        测试阿里云连接
        
        Returns:
            int: 退出码
        """
        try:
            print("🔗 测试阿里云短信服务连接...")
            
            # 创建短信客户端
            sms_client = AliyunSMSClient(self.config)
            
            # 尝试生成验证码（不发送）
            code = sms_client.generate_verification_code()
            print(f"✅ 验证码生成成功: {code}")
            
            # 验证配置
            if not self.config.aliyun_access_key_id:
                print("❌ 阿里云AccessKey ID未配置")
                return 1
            
            if not self.config.aliyun_access_key_secret:
                print("❌ 阿里云AccessKey Secret未配置")
                return 1
            
            if not self.config.aliyun_sign_name:
                print("❌ 阿里云短信签名未配置")
                return 1
            
            if not self.config.aliyun_template_code:
                print("❌ 阿里云短信模板代码未配置")
                return 1
            
            print("✅ 阿里云配置验证通过")
            
            # 测试Redis连接（如果启用）
            if self.config.enable_redis:
                try:
                    import redis
                    redis_client = redis.Redis(
                        host=self.config.redis_host,
                        port=self.config.redis_port,
                        db=self.config.redis_db,
                        password=self.config.redis_password if self.config.redis_password else None
                    )
                    redis_client.ping()
                    print("✅ Redis连接测试成功")
                except Exception as e:
                    print(f"❌ Redis连接测试失败: {e}")
                    return 1
            
            return 0
            
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SMS 2FA 用户管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s add alice +8613812345678    # 添加用户
  %(prog)s add bob +8618888888888 -t   # 添加用户并测试短信
  %(prog)s remove alice               # 删除用户
  %(prog)s list                       # 列出所有用户
  %(prog)s list --format json        # JSON格式输出
  %(prog)s test alice                 # 测试用户短信发送
  %(prog)s status alice               # 查看用户状态
  %(prog)s update alice +8613999999999 # 更新用户手机号
  %(prog)s validate                   # 验证配置
  %(prog)s check                      # 测试连接
"""
    )
    
    parser.add_argument(
        "--config", 
        default="/etc/sms-2fa/2fa.conf",
        help="配置文件路径 (默认: /etc/sms-2fa/2fa.conf)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 添加用户
    add_parser = subparsers.add_parser("add", help="添加用户")
    add_parser.add_argument("username", help="用户名")
    add_parser.add_argument("phone_number", help="手机号 (格式: +8613812345678)")
    add_parser.add_argument("-t", "--test", action="store_true", help="添加后测试短信发送")
    
    # 删除用户
    remove_parser = subparsers.add_parser("remove", help="删除用户")
    remove_parser.add_argument("username", help="用户名")
    remove_parser.add_argument("-y", "--yes", action="store_true", help="不询问确认直接删除")
    
    # 列出用户
    list_parser = subparsers.add_parser("list", help="列出所有用户")
    list_parser.add_argument(
        "--format", 
        choices=["table", "json", "csv"], 
        default="table",
        help="输出格式 (默认: table)"
    )
    
    # 测试用户
    test_parser = subparsers.add_parser("test", help="测试用户短信发送")
    test_parser.add_argument("username", help="用户名")
    
    # 用户状态
    status_parser = subparsers.add_parser("status", help="查看用户状态")
    status_parser.add_argument("username", help="用户名")
    
    # 更新用户
    update_parser = subparsers.add_parser("update", help="更新用户手机号")
    update_parser.add_argument("username", help="用户名")
    update_parser.add_argument("phone_number", help="新手机号")
    
    # 验证配置
    subparsers.add_parser("validate", help="验证配置文件")
    
    # 测试连接
    subparsers.add_parser("check", help="测试阿里云连接")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # 创建用户管理工具
        cli = UserManagerCLI(args.config)
        
        # 执行命令
        if args.command == "add":
            return cli.add_user(args.username, args.phone_number, args.test)
        elif args.command == "remove":
            return cli.remove_user(args.username, args.yes)
        elif args.command == "list":
            return cli.list_users(args.format)
        elif args.command == "test":
            return cli.test_user(args.username)
        elif args.command == "status":
            return cli.show_user_status(args.username)
        elif args.command == "update":
            return cli.update_user(args.username, args.phone_number)
        elif args.command == "validate":
            return cli.validate_config()
        elif args.command == "check":
            return cli.test_connection()
        else:
            print(f"❌ 未知命令: {args.command}")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⏹️  操作已取消")
        return 1
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        return 1


if __name__ == "__main__":
    exit(main())