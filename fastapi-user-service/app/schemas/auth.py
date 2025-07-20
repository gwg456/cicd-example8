#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认证相关的Pydantic模型
用于JWT认证和登录相关的数据验证
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Token(BaseModel):
    """JWT Token模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class TokenData(BaseModel):
    """Token数据模型"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    scopes: List[str] = []

class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名或邮箱")
    password: str = Field(..., min_length=1, max_length=50, description="密码")
    remember_me: bool = Field(False, description="记住我")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名或邮箱"""
        v = v.strip()
        if not v:
            raise ValueError('用户名或邮箱不能为空')
        return v

class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: dict
    
class RefreshTokenRequest(BaseModel):
    """刷新Token请求模型"""
    refresh_token: str = Field(..., min_length=1, description="刷新Token")

class RefreshTokenResponse(BaseModel):
    """刷新Token响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LogoutRequest(BaseModel):
    """登出请求模型"""
    refresh_token: Optional[str] = Field(None, description="刷新Token（可选）")
    logout_all_devices: bool = Field(False, description="是否登出所有设备")

class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    current_password: str = Field(..., min_length=1, description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=50, description="新密码")
    new_password_confirm: str = Field(..., min_length=8, max_length=50, description="确认新密码")
    
    @validator('new_password_confirm')
    def validate_password_confirm(cls, v, values):
        """验证确认密码"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的新密码不一致')
        return v

class ForgotPasswordRequest(BaseModel):
    """忘记密码请求模型"""
    email: EmailStr = Field(..., description="注册邮箱")

class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    token: str = Field(..., min_length=1, description="重置Token")
    new_password: str = Field(..., min_length=8, max_length=50, description="新密码")
    new_password_confirm: str = Field(..., min_length=8, max_length=50, description="确认新密码")
    
    @validator('new_password_confirm')
    def validate_password_confirm(cls, v, values):
        """验证确认密码"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的新密码不一致')
        return v

class VerifyEmailRequest(BaseModel):
    """邮箱验证请求模型"""
    token: str = Field(..., min_length=1, description="验证Token")

class ResendVerificationRequest(BaseModel):
    """重新发送验证邮件请求模型"""
    email: EmailStr = Field(..., description="邮箱地址")

# OAuth相关模型
class OAuthProviderInfo(BaseModel):
    """OAuth提供商信息"""
    provider: str
    client_id: str
    authorization_url: str
    scope: List[str]

class OAuthCallbackRequest(BaseModel):
    """OAuth回调请求模型"""
    provider: str = Field(..., description="OAuth提供商")
    code: str = Field(..., description="授权码")
    state: Optional[str] = Field(None, description="状态参数")

class OAuthLoginResponse(BaseModel):
    """OAuth登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: dict
    is_new_user: bool = Field(False, description="是否为新用户")

# 会话管理模型
class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str
    user_id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[str]
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    is_current: bool = False

class SessionListResponse(BaseModel):
    """会话列表响应模型"""
    sessions: List[SessionInfo]
    total: int

class RevokeSessionRequest(BaseModel):
    """撤销会话请求模型"""
    session_id: str = Field(..., description="会话ID")

# 两步验证模型
class TwoFactorSetupRequest(BaseModel):
    """两步验证设置请求模型"""
    password: str = Field(..., description="当前密码")

class TwoFactorSetupResponse(BaseModel):
    """两步验证设置响应模型"""
    secret: str
    qr_code: str
    backup_codes: List[str]

class TwoFactorVerifyRequest(BaseModel):
    """两步验证验证请求模型"""
    code: str = Field(..., min_length=6, max_length=6, description="验证码")

class TwoFactorLoginRequest(BaseModel):
    """两步验证登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    totp_code: str = Field(..., min_length=6, max_length=6, description="TOTP验证码")
    remember_me: bool = Field(False, description="记住我")

class TwoFactorDisableRequest(BaseModel):
    """禁用两步验证请求模型"""
    password: str = Field(..., description="当前密码")
    backup_code: Optional[str] = Field(None, description="备用验证码")

# API密钥管理模型
class ApiKeyCreateRequest(BaseModel):
    """API密钥创建请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="密钥名称")
    description: Optional[str] = Field(None, max_length=500, description="密钥描述")
    scopes: List[str] = Field(default=[], description="权限范围")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class ApiKeyResponse(BaseModel):
    """API密钥响应模型"""
    id: int
    name: str
    description: Optional[str]
    key: str  # 只在创建时返回完整密钥
    key_preview: str  # 其他时候只返回预览
    scopes: List[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool

class ApiKeyListResponse(BaseModel):
    """API密钥列表响应模型"""
    keys: List[ApiKeyResponse]
    total: int

class ApiKeyUpdateRequest(BaseModel):
    """API密钥更新请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="密钥名称")
    description: Optional[str] = Field(None, max_length=500, description="密钥描述")
    scopes: Optional[List[str]] = Field(None, description="权限范围")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: Optional[bool] = Field(None, description="是否激活")

# 登录历史模型
class LoginHistoryItem(BaseModel):
    """登录历史项目模型"""
    id: int
    ip_address: Optional[str]
    user_agent: Optional[str]
    login_method: str
    success: bool
    failure_reason: Optional[str]
    created_at: datetime

class LoginHistoryResponse(BaseModel):
    """登录历史响应模型"""
    history: List[LoginHistoryItem]
    total: int
    page: int
    size: int

# 安全事件模型
class SecurityEvent(BaseModel):
    """安全事件模型"""
    event_type: str
    description: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

class SecurityEventListResponse(BaseModel):
    """安全事件列表响应模型"""
    events: List[SecurityEvent]
    total: int
    page: int
    size: int

# 权限和角色模型
class Permission(BaseModel):
    """权限模型"""
    name: str
    description: str
    resource: str
    action: str

class Role(BaseModel):
    """角色模型"""
    name: str
    description: str
    permissions: List[Permission]

class UserPermissions(BaseModel):
    """用户权限模型"""
    user_id: int
    roles: List[Role]
    permissions: List[Permission]

# 账户锁定模型
class AccountLockInfo(BaseModel):
    """账户锁定信息模型"""
    is_locked: bool
    locked_until: Optional[datetime]
    failed_attempts: int
    max_attempts: int
    lockout_duration: int  # 分钟

class UnlockAccountRequest(BaseModel):
    """解锁账户请求模型"""
    user_id: int = Field(..., description="用户ID")
    reason: str = Field(..., min_length=1, max_length=500, description="解锁原因")

# 认证响应模型
class AuthResponse(BaseModel):
    """通用认证响应模型"""
    success: bool
    message: str
    data: Optional[dict] = None

class LoginAttemptResponse(BaseModel):
    """登录尝试响应模型"""
    success: bool
    message: str
    requires_2fa: bool = False
    requires_email_verification: bool = False
    account_locked: bool = False
    locked_until: Optional[datetime] = None
    data: Optional[dict] = None

# 设备管理模型
class DeviceInfo(BaseModel):
    """设备信息模型"""
    device_id: str
    device_name: str
    device_type: str  # mobile, desktop, tablet
    os: Optional[str]
    browser: Optional[str]
    ip_address: Optional[str]
    last_seen: datetime
    is_trusted: bool = False

class TrustedDeviceRequest(BaseModel):
    """信任设备请求模型"""
    device_id: str = Field(..., description="设备ID")
    trust: bool = Field(..., description="是否信任")

if __name__ == "__main__":
    # 测试认证模型
    from datetime import timedelta
    
    print("=== 测试认证模型验证 ===")
    
    # 测试登录请求
    try:
        login_data = {
            "username": "testuser",
            "password": "testpassword",
            "remember_me": True
        }
        
        login_request = LoginRequest(**login_data)
        print(f"✅ 登录请求模型验证通过: {login_request.username}")
        
    except Exception as e:
        print(f"❌ 登录请求模型验证失败: {e}")
    
    # 测试Token模型
    try:
        token_data = {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "bearer",
            "expires_in": 3600,
            "refresh_token": "refresh_token_here"
        }
        
        token = Token(**token_data)
        print(f"✅ Token模型验证通过: {token.token_type}")
        
    except Exception as e:
        print(f"❌ Token模型验证失败: {e}")
    
    # 测试密码修改请求
    try:
        change_pwd_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "new_password_confirm": "newpassword123"
        }
        
        change_pwd = ChangePasswordRequest(**change_pwd_data)
        print(f"✅ 密码修改请求模型验证通过")
        
    except Exception as e:
        print(f"❌ 密码修改请求模型验证失败: {e}")
    
    # 测试密码不匹配的情况
    try:
        invalid_pwd_data = {
            "current_password": "oldpassword",
            "new_password": "newpassword123",
            "new_password_confirm": "differentpassword"
        }
        
        ChangePasswordRequest(**invalid_pwd_data)
        print("❌ 密码不匹配验证应该失败")
        
    except Exception as e:
        print(f"✅ 密码不匹配验证正确失败: {e}")
    
    print("=== 认证模型验证测试完成 ===")