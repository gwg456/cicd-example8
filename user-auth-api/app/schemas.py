from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
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
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class User(UserInDB):
    """Public user schema"""
    roles: List["Role"] = []


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


class Role(RoleBase):
    """Role schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Permission schemas
class PermissionBase(BaseModel):
    """Base permission schema"""
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    """Permission creation schema"""
    pass


class Permission(PermissionBase):
    """Permission schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


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


# Update forward references
User.model_rebuild()