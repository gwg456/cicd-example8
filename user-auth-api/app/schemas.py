from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema"""
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """User update schema"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserInDB(UserBase):
    """User schema for database operations"""
    id: int
    is_superuser: bool
    is_oidc_user: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class User(UserInDB):
    """User response schema"""
    pass


class UserWithRoles(User):
    """User with roles schema"""
    roles: List["Role"] = []


# API Client schemas
class APIClientBase(BaseModel):
    """Base API client schema"""
    name: str
    description: Optional[str] = None
    scopes: Optional[List[str]] = ["read"]
    is_trusted: bool = False


class APIClientCreate(APIClientBase):
    """API client creation schema"""
    expires_days: Optional[int] = None
    
    @validator('scopes')
    def validate_scopes(cls, v):
        valid_scopes = ["read", "write", "admin", "delete"]
        if v:
            for scope in v:
                if scope not in valid_scopes:
                    raise ValueError(f"Invalid scope: {scope}. Valid scopes: {valid_scopes}")
        return v


class APIClientUpdate(BaseModel):
    """API client update schema"""
    name: Optional[str] = None
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_trusted: Optional[bool] = None


class APIClientInDB(APIClientBase):
    """API client schema for database operations"""
    id: int
    client_id: str
    owner_id: int
    is_active: bool
    request_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class APIClient(APIClientInDB):
    """API client response schema"""
    pass


class APIClientWithSecret(APIClient):
    """API client with secret (only returned on creation)"""
    client_secret: str


class APIClientWithKeys(APIClient):
    """API client with API keys"""
    api_keys: List["APIKey"] = []


# API Key schemas
class APIKeyBase(BaseModel):
    """Base API key schema"""
    name: str
    scopes: Optional[List[str]] = ["read"]


class APIKeyCreate(APIKeyBase):
    """API key creation schema"""
    expires_days: Optional[int] = 365
    
    @validator('scopes')
    def validate_scopes(cls, v):
        valid_scopes = ["read", "write", "admin", "delete"]
        if v:
            for scope in v:
                if scope not in valid_scopes:
                    raise ValueError(f"Invalid scope: {scope}. Valid scopes: {valid_scopes}")
        return v


class APIKeyInDB(APIKeyBase):
    """API key schema for database operations"""
    id: int
    key_id: str
    client_id: int
    is_active: bool
    request_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class APIKey(APIKeyInDB):
    """API key response schema"""
    pass


class APIKeyWithValue(APIKey):
    """API key with value (only returned on creation)"""
    key_value: str


# Client Authentication schemas
class ClientCredentialsRequest(BaseModel):
    """Client credentials grant request"""
    grant_type: str = "client_credentials"
    client_id: str
    client_secret: str
    scope: Optional[str] = "read"


class ClientAccessTokenResponse(BaseModel):
    """Client access token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


class APIKeyAuthRequest(BaseModel):
    """API key authentication request"""
    api_key: str
    timestamp: str
    signature: str


# OIDC Schemas (保留现有OIDC相关schemas)
class OIDCProvider(BaseModel):
    """OIDC Provider information"""
    name: str
    display_name: str
    login_url: str


class OIDCProvidersResponse(BaseModel):
    """OIDC Providers list response"""
    providers: List[OIDCProvider]
    count: int


class UserOIDCLink(BaseModel):
    """User OIDC Provider Link"""
    id: int
    provider: str
    provider_user_id: str
    provider_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserWithOIDCLinks(User):
    """User with OIDC provider links"""
    oidc_links: List[UserOIDCLink] = []


class OIDCAuthResponse(BaseModel):
    """OIDC Authentication response"""
    access_token: str
    token_type: str
    user: User


class OIDCLogoutResponse(BaseModel):
    """OIDC Logout response"""
    logout_url: Optional[str] = None
    message: Optional[str] = None


# Role schemas
class RoleBase(BaseModel):
    """Base role schema"""
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Role creation schema"""
    pass


class RoleUpdate(BaseModel):
    """Role update schema"""
    name: Optional[str] = None
    description: Optional[str] = None


class RoleInDB(RoleBase):
    """Role schema for database operations"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Role(RoleInDB):
    """Role response schema"""
    pass


class RoleWithUsers(Role):
    """Role with users schema"""
    users: List[User] = []


# Authentication schemas
class Token(BaseModel):
    """Token schema"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = None


class UserLogin(BaseModel):
    """User login schema"""
    username: str
    password: str


class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        return v


class UserSearch(BaseModel):
    """User search parameters"""
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_oidc_user: Optional[bool] = None
    skip: int = 0
    limit: int = 100


# API Documentation schemas
class APIInfo(BaseModel):
    """API information"""
    name: str
    version: str
    description: str
    authentication_methods: List[str]


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Update forward references
User.model_rebuild()
UserWithRoles.model_rebuild()
Role.model_rebuild()
RoleWithUsers.model_rebuild()
APIClient.model_rebuild()
APIClientWithKeys.model_rebuild()
APIKey.model_rebuild()