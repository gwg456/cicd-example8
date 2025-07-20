from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)  # 对于OIDC用户可能为空
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_oidc_user = Column(Boolean, default=False)  # 标识是否为OIDC用户
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Many-to-many relationship with roles
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    # One-to-many relationship with OIDC provider links
    oidc_links = relationship("UserOIDCLink", back_populates="user", cascade="all, delete-orphan")


class UserOIDCLink(Base):
    """用户OIDC提供商关联表"""
    __tablename__ = "user_oidc_links"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    provider = Column(String, nullable=False)  # 提供商名称，如 'google', 'azure'
    provider_user_id = Column(String, nullable=False)  # 提供商中的用户ID
    provider_data = Column(JSON, nullable=True)  # 原始提供商数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="oidc_links")
    
    # 创建复合唯一索引
    __table_args__ = (
        {'extend_existing': True}
    )


class Role(Base):
    """Role model"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Many-to-many relationship with users
    users = relationship("User", secondary=user_roles, back_populates="roles")


class Permission(Base):
    """Permission model"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    resource = Column(String, nullable=False)  # e.g., 'users', 'posts'
    action = Column(String, nullable=False)    # e.g., 'read', 'write', 'delete'
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class OIDCSession(Base):
    """OIDC会话表，用于存储临时认证状态"""
    __tablename__ = "oidc_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    state = Column(String, nullable=False)
    nonce = Column(String, nullable=False)
    code_verifier = Column(String, nullable=True)  # PKCE
    provider = Column(String, nullable=False)
    redirect_uri = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())