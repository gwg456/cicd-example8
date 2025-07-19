from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from .database import get_db
from .auth import verify_token
from . import models, schemas

# Security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = verify_token(credentials.credentials)
    if username is None:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user: models.User = Depends(get_current_active_user)
) -> models.User:
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def require_roles(required_roles: List[str]):
    """Dependency factory for role-based access control"""
    def role_checker(
        current_user: models.User = Depends(get_current_active_user)
    ) -> models.User:
        user_roles = [role.name for role in current_user.roles]
        
        # Superuser has all permissions
        if current_user.is_superuser:
            return current_user
        
        # Check if user has any of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker


def require_permission(resource: str, action: str):
    """Dependency factory for permission-based access control"""
    def permission_checker(
        current_user: models.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> models.User:
        # Superuser has all permissions
        if current_user.is_superuser:
            return current_user
        
        # Check if user has the required permission through roles
        for role in current_user.roles:
            # In a full implementation, you would check role.permissions
            # For now, we'll use a simple role-based check
            pass
        
        # For demonstration, let's allow users to read their own data
        if resource == "users" and action == "read":
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required permission: {action} on {resource}"
        )
    
    return permission_checker