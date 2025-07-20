#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户相关的Pydantic模型
用于API请求和响应的数据验证
"""

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
import re

from app.config import settings

class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH)
    email: EmailStr = Field(..., max_length=settings.EMAIL_MAX_LENGTH)
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if not re.match(settings.USERNAME_PATTERN, v):
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        
        # 禁用的用户名列表
        forbidden_usernames = [
            'admin', 'root', 'administrator', 'user', 'test', 'guest',
            'null', 'undefined', 'api', 'www', 'mail', 'ftp', 'system'
        ]
        
        if v.lower() in forbidden_usernames:
            raise ValueError('此用户名不可用')
        
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """验证全名"""
        if v and len(v.strip()) < 2:
            raise ValueError('全名长度至少2个字符')
        return v.strip() if v else v

class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=settings.PWD_MIN_LENGTH, max_length=settings.PWD_MAX_LENGTH)
    password_confirm: str = Field(..., min_length=settings.PWD_MIN_LENGTH, max_length=settings.PWD_MAX_LENGTH)
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        requirements = settings.get_password_requirements()
        
        if len(v) < requirements['min_length']:
            raise ValueError(f'密码长度至少{requirements["min_length"]}个字符')
        
        if len(v) > requirements['max_length']:
            raise ValueError(f'密码长度不能超过{requirements["max_length"]}个字符')
        
        # 检查密码复杂度
        if requirements['require_uppercase'] and not re.search(r'[A-Z]', v):
            raise ValueError('密码必须包含至少一个大写字母')
        
        if requirements['require_lowercase'] and not re.search(r'[a-z]', v):
            raise ValueError('密码必须包含至少一个小写字母')
        
        if requirements['require_numbers'] and not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        
        if requirements['require_special'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密码必须包含至少一个特殊字符')
        
        # 检查常见弱密码
        weak_passwords = [
            'password', '123456', 'qwerty', 'abc123', 'password123',
            '12345678', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if v.lower() in weak_passwords:
            raise ValueError('密码过于简单，请选择更强的密码')
        
        return v
    
    @validator('password_confirm')
    def validate_password_confirm(cls, v, values):
        """验证确认密码"""
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v

class UserUpdate(BaseModel):
    """用户更新模型"""
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """验证全名"""
        if v and len(v.strip()) < 2:
            raise ValueError('全名长度至少2个字符')
        return v.strip() if v else v
    
    @validator('avatar_url')
    def validate_avatar_url(cls, v):
        """验证头像URL"""
        if v and not re.match(r'^https?://.+', v):
            raise ValueError('头像URL格式不正确')
        return v

class UserPasswordChange(BaseModel):
    """用户密码修改模型"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=settings.PWD_MIN_LENGTH, max_length=settings.PWD_MAX_LENGTH)
    new_password_confirm: str = Field(..., min_length=settings.PWD_MIN_LENGTH, max_length=settings.PWD_MAX_LENGTH)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码"""
        # 复用创建用户时的密码验证逻辑
        return UserCreate.validate_password(v)
    
    @validator('new_password_confirm')
    def validate_new_password_confirm(cls, v, values):
        """验证确认新密码"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的新密码不一致')
        return v

class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    uuid: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login_at: Optional[datetime]
    login_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        
    @validator('last_login_at', 'created_at', 'updated_at', pre=True)
    def parse_datetime(cls, v):
        """解析日期时间"""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

class UserDetailResponse(UserResponse):
    """用户详细信息响应模型（包含敏感信息，仅管理员可见）"""
    last_login_ip: Optional[str]
    failed_login_attempts: int
    locked_until: Optional[datetime]
    password_changed_at: Optional[datetime]
    deleted_at: Optional[datetime]

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int

class UserSearchParams(BaseModel):
    """用户搜索参数"""
    keyword: Optional[str] = Field(None, max_length=100, description="搜索关键词（用户名、邮箱、全名）")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_verified: Optional[bool] = Field(None, description="是否已验证")
    is_superuser: Optional[bool] = Field(None, description="是否为超级用户")
    created_after: Optional[datetime] = Field(None, description="创建时间起始")
    created_before: Optional[datetime] = Field(None, description="创建时间结束")
    
    # 分页参数
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    
    # 排序参数
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="排序方向")
    
    @validator('keyword')
    def validate_keyword(cls, v):
        """验证搜索关键词"""
        if v and len(v.strip()) < 2:
            raise ValueError('搜索关键词长度至少2个字符')
        return v.strip() if v else v

class UserStatus(BaseModel):
    """用户状态模型"""
    is_active: bool
    is_verified: bool
    is_superuser: bool

class UserStats(BaseModel):
    """用户统计信息"""
    total_users: int
    active_users: int
    verified_users: int
    superusers: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int

# 邮箱验证相关模型
class EmailVerificationRequest(BaseModel):
    """邮箱验证请求"""
    email: EmailStr

class EmailVerificationConfirm(BaseModel):
    """邮箱验证确认"""
    token: str = Field(..., min_length=1)

# 密码重置相关模型
class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """密码重置确认"""
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=settings.PWD_MIN_LENGTH, max_length=settings.PWD_MAX_LENGTH)
    new_password_confirm: str = Field(..., min_length=settings.PWD_MIN_LENGTH, max_length=settings.PWD_MAX_LENGTH)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """验证新密码"""
        return UserCreate.validate_password(v)
    
    @validator('new_password_confirm')
    def validate_new_password_confirm(cls, v, values):
        """验证确认新密码"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的新密码不一致')
        return v

# 用户导入导出模型
class UserImport(BaseModel):
    """用户导入模型"""
    users: List[UserCreate]
    
    @validator('users')
    def validate_users_list(cls, v):
        """验证用户列表"""
        if len(v) > 1000:
            raise ValueError('单次导入用户数量不能超过1000个')
        
        # 检查重复的用户名和邮箱
        usernames = [user.username for user in v]
        emails = [user.email for user in v]
        
        if len(set(usernames)) != len(usernames):
            raise ValueError('导入列表中存在重复的用户名')
        
        if len(set(emails)) != len(emails):
            raise ValueError('导入列表中存在重复的邮箱')
        
        return v

class UserExportParams(BaseModel):
    """用户导出参数"""
    format: str = Field("csv", regex="^(csv|json|xlsx)$", description="导出格式")
    include_sensitive: bool = Field(False, description="是否包含敏感信息")
    filters: Optional[UserSearchParams] = Field(None, description="过滤条件")

# API响应模型
class ApiResponse(BaseModel):
    """通用API响应模型"""
    success: bool
    message: str
    data: Optional[dict] = None
    errors: Optional[List[str]] = None

class UserApiResponse(ApiResponse):
    """用户API响应模型"""
    data: Optional[UserResponse] = None

class UserListApiResponse(ApiResponse):
    """用户列表API响应模型"""
    data: Optional[UserListResponse] = None

if __name__ == "__main__":
    # 测试模型验证
    import json
    
    print("=== 测试用户模型验证 ===")
    
    # 测试用户创建
    try:
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecurePass123",
            "password_confirm": "SecurePass123",
            "full_name": "Test User"
        }
        
        user_create = UserCreate(**user_data)
        print(f"✅ 用户创建模型验证通过: {user_create.username}")
        
    except Exception as e:
        print(f"❌ 用户创建模型验证失败: {e}")
    
    # 测试密码验证
    try:
        weak_user_data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "123456",  # 弱密码
            "password_confirm": "123456",
            "full_name": "Test User 2"
        }
        
        UserCreate(**weak_user_data)
        print("❌ 弱密码验证应该失败")
        
    except Exception as e:
        print(f"✅ 弱密码验证正确失败: {e}")
    
    # 测试搜索参数
    try:
        search_params = UserSearchParams(
            keyword="test",
            page=1,
            size=20,
            sort_by="username",
            sort_order="asc"
        )
        print(f"✅ 搜索参数验证通过: {search_params.dict()}")
        
    except Exception as e:
        print(f"❌ 搜索参数验证失败: {e}")
    
    print("=== 模型验证测试完成 ===")