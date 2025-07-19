#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里云短信服务接口模块
支持发送短信验证码和查询发送状态
"""

import json
import time
import secrets
from typing import Optional, Dict, Any
from alibabacloud_dysmsapi20170525.client import Client as DysmsapiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_models
from alibabacloud_tea_util import models as util_models
from loguru import logger

from .config import Config


class AliyunSMSClient:
    """阿里云短信客户端"""
    
    def __init__(self, config: Config):
        """
        初始化阿里云短信客户端
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.client = self._create_client()
        
    def _create_client(self) -> DysmsapiClient:
        """创建阿里云短信客户端"""
        try:
            config = open_api_models.Config(
                access_key_id=self.config.aliyun_access_key_id,
                access_key_secret=self.config.aliyun_access_key_secret,
                region_id=self.config.aliyun_region
            )
            config.endpoint = f'dysmsapi.{self.config.aliyun_region}.aliyuncs.com'
            
            return DysmsapiClient(config)
        except Exception as e:
            logger.error(f"创建阿里云短信客户端失败: {e}")
            raise
    
    def generate_verification_code(self, length: int = 6) -> str:
        """
        生成验证码
        
        Args:
            length: 验证码长度，默认6位
            
        Returns:
            str: 生成的验证码
        """
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    def send_verification_code(self, phone_number: str, code: str) -> Dict[str, Any]:
        """
        发送短信验证码
        
        Args:
            phone_number: 手机号码
            code: 验证码
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            # 验证手机号格式
            if not self._validate_phone_number(phone_number):
                return {
                    'success': False,
                    'error': 'Invalid phone number format'
                }
            
            # 构建短信参数
            template_param = json.dumps({
                'code': code
            })
            
            # 创建发送请求
            send_sms_request = dysmsapi_models.SendSmsRequest(
                phone_numbers=phone_number,
                sign_name=self.config.aliyun_sign_name,
                template_code=self.config.aliyun_template_code,
                template_param=template_param
            )
            
            # 发送短信
            runtime = util_models.RuntimeOptions()
            response = self.client.send_sms_with_options(send_sms_request, runtime)
            
            # 解析响应
            result = {
                'success': False,
                'biz_id': '',
                'request_id': '',
                'code': '',
                'message': '',
                'timestamp': int(time.time())
            }
            
            if response.body:
                result.update({
                    'success': response.body.code == 'OK',
                    'biz_id': response.body.biz_id,
                    'request_id': response.body.request_id,
                    'code': response.body.code,
                    'message': response.body.message
                })
            
            # 记录日志
            if result['success']:
                logger.info(f"短信发送成功: {phone_number}, BizId: {result['biz_id']}")
            else:
                logger.error(f"短信发送失败: {phone_number}, Error: {result['message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"发送短信异常: {phone_number}, Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': int(time.time())
            }
    
    def query_send_details(self, phone_number: str, biz_id: str, 
                          send_date: str) -> Dict[str, Any]:
        """
        查询短信发送详情
        
        Args:
            phone_number: 手机号码
            biz_id: 发送回执ID
            send_date: 发送日期，格式YYYYMMDD
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        try:
            query_request = dysmsapi_models.QuerySendDetailsRequest(
                phone_number=phone_number,
                biz_id=biz_id,
                send_date=send_date,
                page_size=10,
                current_page=1
            )
            
            runtime = util_models.RuntimeOptions()
            response = self.client.query_send_details_with_options(query_request, runtime)
            
            result = {
                'success': False,
                'total_count': 0,
                'sms_send_detail_dtos': [],
                'code': '',
                'message': ''
            }
            
            if response.body:
                result.update({
                    'success': response.body.code == 'OK',
                    'total_count': response.body.total_count,
                    'sms_send_detail_dtos': response.body.sms_send_detail_dtos,
                    'code': response.body.code,
                    'message': response.body.message
                })
            
            return result
            
        except Exception as e:
            logger.error(f"查询短信详情异常: {phone_number}, Error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """
        验证手机号格式
        
        Args:
            phone_number: 手机号码
            
        Returns:
            bool: 是否有效
        """
        import re
        
        # 移除可能的空格和特殊字符
        clean_number = re.sub(r'[\s\-\(\)]', '', phone_number)
        
        # 中国大陆手机号：1开头的11位数字
        china_mobile_pattern = r'^(\+86)?1[3-9]\d{9}$'
        
        # 国际手机号：+开头的格式
        international_pattern = r'^\+[1-9]\d{1,14}$'
        
        return (re.match(china_mobile_pattern, clean_number) or 
                re.match(international_pattern, clean_number))


class SMSCodeManager:
    """短信验证码管理器"""
    
    def __init__(self, config: Config, redis_client=None):
        """
        初始化验证码管理器
        
        Args:
            config: 配置对象
            redis_client: Redis客户端（可选）
        """
        self.config = config
        self.redis_client = redis_client
        self.sms_client = AliyunSMSClient(config)
        self._memory_cache = {}  # 内存缓存，当Redis不可用时使用
        
    def send_code(self, username: str, phone_number: str) -> Dict[str, Any]:
        """
        发送验证码
        
        Args:
            username: 用户名
            phone_number: 手机号码
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            # 检查发送频率限制
            if self._check_rate_limit(username, phone_number):
                return {
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'message': '发送过于频繁，请稍后再试'
                }
            
            # 生成验证码
            code = self.sms_client.generate_verification_code()
            
            # 发送短信
            result = self.sms_client.send_verification_code(phone_number, code)
            
            if result['success']:
                # 存储验证码
                self._store_verification_code(username, phone_number, code)
                
                # 记录发送记录
                self._record_send_attempt(username, phone_number)
                
                logger.info(f"验证码发送成功: {username} -> {phone_number}")
                
                return {
                    'success': True,
                    'message': '验证码发送成功',
                    'biz_id': result.get('biz_id'),
                    'expires_in': self.config.code_expire_time
                }
            else:
                logger.error(f"验证码发送失败: {username} -> {phone_number}, {result.get('message')}")
                return {
                    'success': False,
                    'error': result.get('error', 'SMS send failed'),
                    'message': '验证码发送失败，请稍后重试'
                }
                
        except Exception as e:
            logger.error(f"发送验证码异常: {username} -> {phone_number}, Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '验证码发送异常'
            }
    
    def verify_code(self, username: str, phone_number: str, code: str) -> Dict[str, Any]:
        """
        验证验证码
        
        Args:
            username: 用户名
            phone_number: 手机号码
            code: 验证码
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 获取存储的验证码
            stored_data = self._get_verification_code(username, phone_number)
            
            if not stored_data:
                logger.warning(f"验证码不存在或已过期: {username} -> {phone_number}")
                return {
                    'success': False,
                    'error': 'Code not found or expired',
                    'message': '验证码不存在或已过期'
                }
            
            stored_code = stored_data.get('code')
            created_time = stored_data.get('created_time', 0)
            
            # 检查验证码是否过期
            if time.time() - created_time > self.config.code_expire_time:
                self._remove_verification_code(username, phone_number)
                logger.warning(f"验证码已过期: {username} -> {phone_number}")
                return {
                    'success': False,
                    'error': 'Code expired',
                    'message': '验证码已过期'
                }
            
            # 验证验证码
            if stored_code == code:
                # 验证成功，删除验证码
                self._remove_verification_code(username, phone_number)
                logger.info(f"验证码验证成功: {username} -> {phone_number}")
                return {
                    'success': True,
                    'message': '验证码验证成功'
                }
            else:
                # 记录失败尝试
                self._record_verify_attempt(username, phone_number, False)
                logger.warning(f"验证码错误: {username} -> {phone_number}")
                return {
                    'success': False,
                    'error': 'Invalid code',
                    'message': '验证码错误'
                }
                
        except Exception as e:
            logger.error(f"验证验证码异常: {username} -> {phone_number}, Error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '验证码验证异常'
            }
    
    def _store_verification_code(self, username: str, phone_number: str, code: str):
        """存储验证码"""
        key = f"sms_code:{username}:{phone_number}"
        data = {
            'code': code,
            'created_time': time.time(),
            'phone_number': phone_number
        }
        
        try:
            if self.redis_client:
                # 使用Redis存储
                self.redis_client.setex(
                    key, 
                    self.config.code_expire_time, 
                    json.dumps(data)
                )
            else:
                # 使用内存缓存
                self._memory_cache[key] = data
        except Exception as e:
            logger.error(f"存储验证码失败: {e}")
            # 降级到内存缓存
            self._memory_cache[key] = data
    
    def _get_verification_code(self, username: str, phone_number: str) -> Optional[Dict]:
        """获取验证码"""
        key = f"sms_code:{username}:{phone_number}"
        
        try:
            if self.redis_client:
                # 从Redis获取
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # 从内存缓存获取
                data = self._memory_cache.get(key)
                if data:
                    # 检查过期时间
                    if time.time() - data['created_time'] <= self.config.code_expire_time:
                        return data
                    else:
                        # 已过期，删除
                        del self._memory_cache[key]
        except Exception as e:
            logger.error(f"获取验证码失败: {e}")
            
        return None
    
    def _remove_verification_code(self, username: str, phone_number: str):
        """删除验证码"""
        key = f"sms_code:{username}:{phone_number}"
        
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                self._memory_cache.pop(key, None)
        except Exception as e:
            logger.error(f"删除验证码失败: {e}")
    
    def _check_rate_limit(self, username: str, phone_number: str) -> bool:
        """检查发送频率限制"""
        rate_key = f"sms_rate:{username}:{phone_number}"
        
        try:
            if self.redis_client:
                current_count = self.redis_client.get(rate_key)
                if current_count and int(current_count) >= self.config.max_send_per_minute:
                    return True
            else:
                # 简单的内存限制检查
                rate_data = self._memory_cache.get(rate_key, {'count': 0, 'reset_time': 0})
                if time.time() < rate_data['reset_time'] and rate_data['count'] >= self.config.max_send_per_minute:
                    return True
                    
        except Exception as e:
            logger.error(f"检查发送频率限制失败: {e}")
            
        return False
    
    def _record_send_attempt(self, username: str, phone_number: str):
        """记录发送尝试"""
        rate_key = f"sms_rate:{username}:{phone_number}"
        
        try:
            if self.redis_client:
                pipe = self.redis_client.pipeline()
                pipe.incr(rate_key)
                pipe.expire(rate_key, 60)  # 1分钟过期
                pipe.execute()
            else:
                # 内存记录
                current_time = time.time()
                rate_data = self._memory_cache.get(rate_key, {'count': 0, 'reset_time': current_time + 60})
                if current_time >= rate_data['reset_time']:
                    rate_data = {'count': 1, 'reset_time': current_time + 60}
                else:
                    rate_data['count'] += 1
                self._memory_cache[rate_key] = rate_data
                
        except Exception as e:
            logger.error(f"记录发送尝试失败: {e}")
    
    def _record_verify_attempt(self, username: str, phone_number: str, success: bool):
        """记录验证尝试"""
        attempt_key = f"sms_verify:{username}:{phone_number}"
        
        try:
            if self.redis_client:
                attempts = self.redis_client.get(attempt_key) or 0
                attempts = int(attempts) + 1
                
                if not success and attempts >= self.config.max_verify_attempts:
                    # 达到最大尝试次数，删除验证码
                    self._remove_verification_code(username, phone_number)
                    logger.warning(f"验证尝试次数超限，删除验证码: {username} -> {phone_number}")
                
                self.redis_client.setex(attempt_key, 300, attempts)  # 5分钟过期
                
        except Exception as e:
            logger.error(f"记录验证尝试失败: {e}")


def test_sms_client():
    """测试短信客户端"""
    from .config import Config
    
    # 加载配置
    config = Config()
    
    # 创建短信客户端
    sms_client = AliyunSMSClient(config)
    
    # 生成验证码
    code = sms_client.generate_verification_code()
    print(f"生成的验证码: {code}")
    
    # 发送测试短信
    phone_number = "+8613812345678"  # 替换为实际手机号
    result = sms_client.send_verification_code(phone_number, code)
    print(f"发送结果: {result}")


if __name__ == "__main__":
    test_sms_client()