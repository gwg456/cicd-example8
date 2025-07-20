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


# OIDC Schemas
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


# Update forward references
User.model_rebuild()
UserWithRoles.model_rebuild()
Role.model_rebuild()
RoleWithUsers.model_rebuild()