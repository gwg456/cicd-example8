from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Text, JSON, ARRAY
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
    
    # One-to-many relationship with API clients
    api_clients = relationship("APIClient", back_populates="owner", cascade="all, delete-orphan")


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


class APIClient(Base):
    """API客户端表 - 用于外部客户端认证"""
    __tablename__ = "api_clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String, unique=True, index=True, nullable=False)
    client_secret_hash = Column(String, nullable=False)  # 加密存储的客户端密钥
    name = Column(String, nullable=False)  # 客户端名称
    description = Column(Text, nullable=True)  # 客户端描述
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # 权限和配置
    scopes = Column(ARRAY(String), nullable=True)  # 权限范围
    is_active = Column(Boolean, default=True)
    is_trusted = Column(Boolean, default=False)  # 是否为受信任客户端
    
    # 使用统计
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    request_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 客户端过期时间
    
    # 关系
    owner = relationship("User", back_populates="api_clients")
    api_keys = relationship("APIKey", back_populates="client", cascade="all, delete-orphan")


class APIKey(Base):
    """API密钥表"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String, unique=True, index=True, nullable=False)  # 公开的密钥ID
    key_hash = Column(String, nullable=False)  # 加密存储的密钥
    name = Column(String, nullable=False)  # 密钥名称
    client_id = Column(Integer, ForeignKey('api_clients.id'), nullable=False)
    
    # 权限和配置
    scopes = Column(ARRAY(String), nullable=True)  # 权限范围
    is_active = Column(Boolean, default=True)
    
    # 使用统计
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    request_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # 密钥过期时间
    
    # 关系
    client = relationship("APIClient", back_populates="api_keys")


class ClientAccessToken(Base):
    """客户端访问令牌表 - 用于跟踪活跃的客户端令牌"""
    __tablename__ = "client_access_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(String, unique=True, index=True, nullable=False)
    client_id = Column(String, ForeignKey('api_clients.client_id'), nullable=False)
    scopes = Column(ARRAY(String), nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)


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