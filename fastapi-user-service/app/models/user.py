#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户数据模型
定义用户表结构和关系
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.database import Base

class User(Base):
    """用户数据模型"""
    
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    
    # 用户标识
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()), comment="用户UUID")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(254), unique=True, index=True, nullable=False, comment="邮箱地址")
    
    # 密码相关
    hashed_password = Column(String(255), nullable=False, comment="加密密码")
    password_changed_at = Column(DateTime(timezone=True), default=func.now(), comment="密码修改时间")
    
    # 基本信息
    full_name = Column(String(100), nullable=True, comment="全名")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    bio = Column(Text, nullable=True, comment="个人简介")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_verified = Column(Boolean, default=False, comment="是否已验证邮箱")
    is_superuser = Column(Boolean, default=False, comment="是否为超级用户")
    
    # 登录相关
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="最后登录时间")
    last_login_ip = Column(String(45), nullable=True, comment="最后登录IP")
    login_count = Column(Integer, default=0, comment="登录次数")
    failed_login_attempts = Column(Integer, default=0, comment="失败登录次数")
    locked_until = Column(DateTime(timezone=True), nullable=True, comment="锁定到期时间")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    deleted_at = Column(DateTime(timezone=True), nullable=True, comment="删除时间（软删除）")
    
    # 元数据
    metadata_json = Column(Text, nullable=True, comment="扩展元数据JSON")
    
    # 创建索引
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_username_active', 'username', 'is_active'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_last_login', 'last_login_at'),
        {'comment': '用户表'}
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def __str__(self):
        return f"User: {self.username} ({self.email})"
    
    @property
    def is_locked(self) -> bool:
        """检查用户是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def is_available(self) -> bool:
        """检查用户是否可用（激活且未锁定且未删除）"""
        return (
            self.is_active and 
            not self.is_locked and 
            self.deleted_at is None
        )
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """转换为字典格式"""
        data = {
            "id": self.id,
            "uuid": self.uuid,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_superuser": self.is_superuser,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "login_count": self.login_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data.update({
                "last_login_ip": self.last_login_ip,
                "failed_login_attempts": self.failed_login_attempts,
                "locked_until": self.locked_until.isoformat() if self.locked_until else None,
                "password_changed_at": self.password_changed_at.isoformat() if self.password_changed_at else None,
                "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            })
        
        return data
    
    def update_login_info(self, ip_address: str = None):
        """更新登录信息"""
        self.last_login_at = func.now()
        self.login_count += 1
        self.failed_login_attempts = 0  # 重置失败次数
        if ip_address:
            self.last_login_ip = ip_address
    
    def increment_failed_login(self, max_attempts: int = 5, lockout_minutes: int = 15):
        """增加失败登录次数，并检查是否需要锁定"""
        self.failed_login_attempts += 1
        
        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
    
    def unlock_account(self):
        """解锁账户"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def soft_delete(self):
        """软删除用户"""
        self.deleted_at = func.now()
        self.is_active = False
    
    def restore(self):
        """恢复已删除的用户"""
        self.deleted_at = None
        self.is_active = True

class UserSession(Base):
    """用户会话模型（可选）"""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, comment="用户ID")
    session_token = Column(String(255), unique=True, index=True, nullable=False, comment="会话Token")
    refresh_token = Column(String(255), unique=True, index=True, nullable=True, comment="刷新Token")
    
    # 会话信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    device_info = Column(Text, nullable=True, comment="设备信息")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="过期时间")
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), comment="最后使用时间")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    __table_args__ = (
        Index('idx_session_user_id', 'user_id'),
        Index('idx_session_token', 'session_token'),
        Index('idx_session_expires', 'expires_at'),
        {'comment': '用户会话表'}
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """检查会话是否有效"""
        return self.is_active and not self.is_expired
    
    def extend_session(self, hours: int = 24):
        """延长会话时间"""
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_used_at = func.now()
    
    def revoke(self):
        """撤销会话"""
        self.is_active = False

class UserLoginLog(Base):
    """用户登录日志模型（可选）"""
    
    __tablename__ = "user_login_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, comment="用户ID")
    username = Column(String(50), nullable=True, comment="用户名")
    
    # 登录信息
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(Text, nullable=True, comment="用户代理")
    login_method = Column(String(20), default="password", comment="登录方式")
    
    # 结果
    success = Column(Boolean, nullable=False, comment="是否成功")
    failure_reason = Column(String(100), nullable=True, comment="失败原因")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    __table_args__ = (
        Index('idx_login_log_user_id', 'user_id'),
        Index('idx_login_log_created_at', 'created_at'),
        Index('idx_login_log_ip', 'ip_address'),
        {'comment': '用户登录日志表'}
    )
    
    def __repr__(self):
        return f"<UserLoginLog(id={self.id}, user_id={self.user_id}, success={self.success})>"

# 创建数据库表的便捷函数
def create_user_tables():
    """创建用户相关的所有表"""
    from app.database import engine
    Base.metadata.create_all(bind=engine, tables=[
        User.__table__,
        UserSession.__table__,
        UserLoginLog.__table__
    ])

if __name__ == "__main__":
    # 测试模型
    from app.database import SessionLocal, engine
    from app.config import settings
    
    print(f"数据库URL: {settings.DATABASE_URL}")
    
    # 创建表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建成功")
    
    # 测试创建用户
    db = SessionLocal()
    try:
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User"
        )
        
        print(f"创建测试用户: {test_user}")
        print(f"用户UUID: {test_user.uuid}")
        print(f"用户可用性: {test_user.is_available}")
        print(f"用户字典: {test_user.to_dict()}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        db.close()