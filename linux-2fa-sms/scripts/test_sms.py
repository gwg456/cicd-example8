#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMS 2FA 短信测试工具
用于测试短信发送功能和验证验证码
"""

import sys
import os
import argparse
import time
import getpass
from typing import Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from src.config import Config
    from src.aliyun_sms import AliyunSMSClient, SMSCodeManager
except ImportError:
    # 如果在安装环境中运行
    sys.path.insert(0, '/opt/sms-2fa/src')
    from config import Config
    from aliyun_sms import AliyunSMSClient, SMSCodeManager


class SMSTestTool:
    """短信测试工具类"""
    
    def __init__(self, config_file: str = "/etc/sms-2fa/2fa.conf"):
        """
        初始化短信测试工具
        
        Args:
            config_file: 配置文件路径
        """
        self.config = Config(config_file)
        self.sms_client = AliyunSMSClient(self.config)
        self.sms_manager = SMSCodeManager(self.config)
    
    def test_config(self) -> int:
        """
        测试配置
        
        Returns:
            int: 退出码
        """
        try:
            print("🔍 测试短信服务配置...")
            
            # 验证基本配置
            errors = []
            
            if not self.config.aliyun_access_key_id:
                errors.append("阿里云AccessKey ID未配置")
            
            if not self.config.aliyun_access_key_secret:
                errors.append("阿里云AccessKey Secret未配置")
            
            if not self.config.aliyun_sign_name:
                errors.append("阿里云短信签名未配置")
            
            if not self.config.aliyun_template_code:
                errors.append("阿里云短信模板代码未配置")
            
            if errors:
                print("❌ 配置错误:")
                for error in errors:
                    print(f"   - {error}")
                return 1
            
            print("✅ 基础配置验证通过")
            
            # 显示配置信息
            print(f"\n📊 配置信息:")
            print(f"   AccessKey ID: {self.config.aliyun_access_key_id[:8]}...")
            print(f"   地域: {self.config.aliyun_region}")
            print(f"   签名: {self.config.aliyun_sign_name}")
            print(f"   模板代码: {self.config.aliyun_template_code}")
            print(f"   验证码长度: {self.config.code_length}")
            print(f"   过期时间: {self.config.code_expire_time} 秒")
            
            return 0
            
        except Exception as e:
            print(f"❌ 配置测试失败: {e}")
            return 1
    
    def generate_code(self, length: int = None) -> int:
        """
        生成验证码
        
        Args:
            length: 验证码长度
            
        Returns:
            int: 退出码
        """
        try:
            if length is None:
                length = self.config.code_length
            
            print(f"🔢 生成 {length} 位验证码...")
            
            code = self.sms_client.generate_verification_code(length)
            
            print(f"✅ 验证码: {code}")
            
            return 0
            
        except Exception as e:
            print(f"❌ 生成验证码失败: {e}")
            return 1
    
    def send_test_sms(self, phone_number: str, custom_code: str = None) -> int:
        """
        发送测试短信
        
        Args:
            phone_number: 手机号
            custom_code: 自定义验证码
            
        Returns:
            int: 退出码
        """
        try:
            print(f"📱 发送测试短信到: {phone_number}")
            
            # 生成或使用自定义验证码
            if custom_code:
                code = custom_code
                print(f"🔢 使用自定义验证码: {code}")
            else:
                code = self.sms_client.generate_verification_code()
                print(f"🔢 生成验证码: {code}")
            
            # 发送短信
            result = self.sms_client.send_verification_code(phone_number, code)
            
            if result['success']:
                print("✅ 短信发送成功")
                print(f"📊 详细信息:")
                print(f"   BizId: {result.get('biz_id')}")
                print(f"   RequestId: {result.get('request_id')}")
                print(f"   响应码: {result.get('code')}")
                print(f"   响应消息: {result.get('message')}")
                print(f"   发送时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.get('timestamp', time.time())))}")
                
                return 0
            else:
                print("❌ 短信发送失败")
                print(f"错误信息: {result.get('message', result.get('error', '未知错误'))}")
                return 1
                
        except Exception as e:
            print(f"❌ 发送短信异常: {e}")
            return 1
    
    def interactive_test(self, phone_number: str) -> int:
        """
        交互式测试
        
        Args:
            phone_number: 手机号
            
        Returns:
            int: 退出码
        """
        try:
            print(f"🧪 开始交互式短信测试: {phone_number}")
            print("=" * 50)
            
            # 发送验证码
            test_username = "test_user"
            
            print("📤 第一步: 发送验证码")
            result = self.sms_manager.send_code(test_username, phone_number)
            
            if not result['success']:
                print(f"❌ 验证码发送失败: {result.get('message')}")
                return 1
            
            print("✅ 验证码发送成功")
            print(f"⏰ 有效期: {result.get('expires_in', 300)} 秒")
            print()
            
            # 等待用户输入验证码
            print("📥 第二步: 验证验证码")
            try:
                verification_code = input("请输入收到的验证码: ").strip()
                
                if not verification_code:
                    print("❌ 验证码不能为空")
                    return 1
                
                # 验证验证码
                verify_result = self.sms_manager.verify_code(test_username, phone_number, verification_code)
                
                if verify_result['success']:
                    print("✅ 验证码验证成功")
                    print("🎉 交互式测试通过")
                    return 0
                else:
                    print(f"❌ 验证码验证失败: {verify_result.get('message')}")
                    return 1
                    
            except KeyboardInterrupt:
                print("\n⏹️  测试已取消")
                return 1
                
        except Exception as e:
            print(f"❌ 交互式测试异常: {e}")
            return 1
    
    def validate_phone(self, phone_number: str) -> int:
        """
        验证手机号格式
        
        Args:
            phone_number: 手机号
            
        Returns:
            int: 退出码
        """
        try:
            print(f"📞 验证手机号格式: {phone_number}")
            
            is_valid = self.sms_client._validate_phone_number(phone_number)
            
            if is_valid:
                print("✅ 手机号格式正确")
                
                # 显示格式化信息
                import re
                clean_number = re.sub(r'[\s\-\(\)]', '', phone_number)
                
                if clean_number.startswith('+86') or (clean_number.startswith('1') and len(clean_number) == 11):
                    print("📱 识别为中国大陆手机号")
                elif clean_number.startswith('+'):
                    print("🌍 识别为国际手机号")
                
                return 0
            else:
                print("❌ 手机号格式错误")
                print("💡 正确格式示例:")
                print("   - 中国大陆: +8613812345678 或 13812345678")
                print("   - 国际格式: +1234567890")
                return 1
                
        except Exception as e:
            print(f"❌ 验证手机号异常: {e}")
            return 1
    
    def query_send_details(self, phone_number: str, biz_id: str, send_date: str = None) -> int:
        """
        查询短信发送详情
        
        Args:
            phone_number: 手机号
            biz_id: 发送回执ID
            send_date: 发送日期 (YYYYMMDD)
            
        Returns:
            int: 退出码
        """
        try:
            if send_date is None:
                send_date = time.strftime('%Y%m%d')
            
            print(f"🔍 查询短信发送详情:")
            print(f"   手机号: {phone_number}")
            print(f"   BizId: {biz_id}")
            print(f"   日期: {send_date}")
            
            result = self.sms_client.query_send_details(phone_number, biz_id, send_date)
            
            if result['success']:
                print("✅ 查询成功")
                print(f"📊 详情:")
                print(f"   总数量: {result.get('total_count', 0)}")
                
                details = result.get('sms_send_detail_dtos', [])
                if details:
                    for i, detail in enumerate(details, 1):
                        print(f"   记录 {i}:")
                        print(f"     状态: {getattr(detail, 'send_status', 'N/A')}")
                        print(f"     发送时间: {getattr(detail, 'send_date', 'N/A')}")
                        print(f"     内容: {getattr(detail, 'content', 'N/A')}")
                        print(f"     错误码: {getattr(detail, 'err_code', 'N/A')}")
                else:
                    print("   无发送记录")
                
                return 0
            else:
                print(f"❌ 查询失败: {result.get('message', result.get('error', '未知错误'))}")
                return 1
                
        except Exception as e:
            print(f"❌ 查询发送详情异常: {e}")
            return 1
    
    def performance_test(self, phone_number: str, count: int = 5, interval: int = 60) -> int:
        """
        性能测试
        
        Args:
            phone_number: 手机号
            count: 测试次数
            interval: 间隔时间（秒）
            
        Returns:
            int: 退出码
        """
        try:
            print(f"⚡ 开始性能测试:")
            print(f"   手机号: {phone_number}")
            print(f"   测试次数: {count}")
            print(f"   间隔时间: {interval} 秒")
            print()
            
            success_count = 0
            fail_count = 0
            total_time = 0
            
            for i in range(count):
                print(f"📤 第 {i+1}/{count} 次测试...")
                
                start_time = time.time()
                
                # 发送短信
                code = self.sms_client.generate_verification_code()
                result = self.sms_client.send_verification_code(phone_number, code)
                
                end_time = time.time()
                duration = end_time - start_time
                total_time += duration
                
                if result['success']:
                    success_count += 1
                    print(f"✅ 成功 - 耗时: {duration:.2f}s - BizId: {result.get('biz_id')}")
                else:
                    fail_count += 1
                    print(f"❌ 失败 - 耗时: {duration:.2f}s - 错误: {result.get('message')}")
                
                # 等待间隔时间（除了最后一次）
                if i < count - 1:
                    print(f"⏰ 等待 {interval} 秒...")
                    time.sleep(interval)
                
                print()
            
            # 显示统计结果
            print("📊 测试结果统计:")
            print(f"   总次数: {count}")
            print(f"   成功次数: {success_count}")
            print(f"   失败次数: {fail_count}")
            print(f"   成功率: {success_count/count*100:.1f}%")
            print(f"   平均耗时: {total_time/count:.2f}s")
            print(f"   总耗时: {total_time:.2f}s")
            
            return 0 if success_count > 0 else 1
            
        except KeyboardInterrupt:
            print("\n⏹️  性能测试已取消")
            return 1
        except Exception as e:
            print(f"❌ 性能测试异常: {e}")
            return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SMS 2FA 短信测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s config                           # 测试配置
  %(prog)s generate                         # 生成验证码
  %(prog)s generate --length 8              # 生成8位验证码
  %(prog)s send +8613812345678              # 发送测试短信
  %(prog)s send +8613812345678 --code 123456 # 发送自定义验证码
  %(prog)s test +8613812345678              # 交互式测试
  %(prog)s validate +8613812345678          # 验证手机号格式
  %(prog)s query +8613812345678 SMS123456   # 查询发送详情
  %(prog)s perf +8613812345678 --count 3    # 性能测试
"""
    )
    
    parser.add_argument(
        "--config",
        default="/etc/sms-2fa/2fa.conf",
        help="配置文件路径 (默认: /etc/sms-2fa/2fa.conf)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 测试配置
    subparsers.add_parser("config", help="测试配置")
    
    # 生成验证码
    generate_parser = subparsers.add_parser("generate", help="生成验证码")
    generate_parser.add_argument("--length", type=int, help="验证码长度")
    
    # 发送短信
    send_parser = subparsers.add_parser("send", help="发送测试短信")
    send_parser.add_argument("phone_number", help="手机号")
    send_parser.add_argument("--code", help="自定义验证码")
    
    # 交互式测试
    test_parser = subparsers.add_parser("test", help="交互式测试")
    test_parser.add_argument("phone_number", help="手机号")
    
    # 验证手机号
    validate_parser = subparsers.add_parser("validate", help="验证手机号格式")
    validate_parser.add_argument("phone_number", help="手机号")
    
    # 查询详情
    query_parser = subparsers.add_parser("query", help="查询发送详情")
    query_parser.add_argument("phone_number", help="手机号")
    query_parser.add_argument("biz_id", help="发送回执ID")
    query_parser.add_argument("--date", help="发送日期 (YYYYMMDD)")
    
    # 性能测试
    perf_parser = subparsers.add_parser("perf", help="性能测试")
    perf_parser.add_argument("phone_number", help="手机号")
    perf_parser.add_argument("--count", type=int, default=5, help="测试次数 (默认: 5)")
    perf_parser.add_argument("--interval", type=int, default=60, help="间隔时间 (默认: 60秒)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # 创建测试工具
        tool = SMSTestTool(args.config)
        
        # 执行命令
        if args.command == "config":
            return tool.test_config()
        elif args.command == "generate":
            return tool.generate_code(args.length)
        elif args.command == "send":
            return tool.send_test_sms(args.phone_number, args.code)
        elif args.command == "test":
            return tool.interactive_test(args.phone_number)
        elif args.command == "validate":
            return tool.validate_phone(args.phone_number)
        elif args.command == "query":
            return tool.query_send_details(args.phone_number, args.biz_id, args.date)
        elif args.command == "perf":
            return tool.performance_test(args.phone_number, args.count, args.interval)
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