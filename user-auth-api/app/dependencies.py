"""
Dependency injection functions for authentication
认证相关的依赖注入函数
"""

from fastapi import Depends, HTTPException, status, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from jose import jwt, JWTError

from .database import get_db
from .config import settings
from .client_auth import client_auth_service
from . import crud, models

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> models.User:
    """获取当前认证用户（JWT令牌）"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_superuser(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, 
            detail="Not enough permissions"
        )
    return current_user


def get_current_client(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> models.APIClient:
    """获取当前认证客户端（客户端凭据流）"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate client credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = client_auth_service.verify_client_token(token)
        
        if not payload:
            raise credentials_exception
        
        client_id = payload.get("client_id")
        if not client_id:
            raise credentials_exception
            
    except Exception:
        raise credentials_exception
    
    client = crud.get_api_client_by_id(db, client_id)
    if not client or not client.is_active:
        raise credentials_exception
    
    return client


def get_current_client_with_scopes(required_scopes: List[str]):
    """获取具有特定权限范围的当前客户端"""
    
    def _get_client_with_scopes(
        credentials: HTTPAuthorizationCredentials = Security(security),
        db: Session = Depends(get_db)
    ) -> models.APIClient:
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate client credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            token = credentials.credentials
            payload = client_auth_service.verify_client_token(token)
            
            if not payload:
                raise credentials_exception
            
            client_id = payload.get("client_id")
            token_scopes = payload.get("scopes", [])
            
            if not client_id:
                raise credentials_exception
            
            # 检查权限范围
            if not all(scope in token_scopes for scope in required_scopes):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
                
        except HTTPException:
            raise
        except Exception:
            raise credentials_exception
        
        client = crud.get_api_client_by_id(db, client_id)
        if not client or not client.is_active:
            raise credentials_exception
        
        return client
    
    return _get_client_with_scopes


def get_api_key_auth(
    x_api_key: Optional[str] = Header(None),
    x_api_signature: Optional[str] = Header(None),
    x_api_timestamp: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[models.APIKey]:
    """API密钥认证（通过Headers）"""
    
    if not x_api_key:
        return None
    
    # 如果提供了签名，验证签名认证
    if x_api_signature and x_api_timestamp:
        # 解析API Key ID
        try:
            key_parts = x_api_key.split('_')
            if len(key_parts) < 2:
                raise ValueError("Invalid API key format")
            
            key_id = f"{key_parts[0]}_{key_parts[1]}"
            api_key = crud.get_api_key_by_id(db, key_id)
            
            if not api_key or not api_key.is_active:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )
            
            # 获取客户端密钥用于验证签名
            client = crud.get_api_client_by_id(db, api_key.client.client_id)
            if not client:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid client"
                )
            
            # 验证签名
            if not client_auth_service.verify_api_key_signature(
                x_api_key, x_api_timestamp, x_api_signature, client.client_secret
            ):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key signature"
                )
            
            return api_key
            
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"API key authentication failed: {str(e)}"
            )
    
    else:
        # 简单API密钥认证（不推荐用于生产环境）
        api_key = crud.authenticate_api_key(db, x_api_key, x_api_key)
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        return api_key


def get_user_or_client(
    # 尝试用户认证
    user_credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False),
    # 尝试API密钥认证
    x_api_key: Optional[str] = Header(None),
    x_api_signature: Optional[str] = Header(None),
    x_api_timestamp: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """支持用户JWT令牌或客户端认证的灵活认证"""
    
    # 首先尝试API密钥认证
    if x_api_key:
        try:
            api_key = get_api_key_auth(x_api_key, x_api_signature, x_api_timestamp, db)
            if api_key:
                return {"type": "api_key", "auth": api_key}
        except HTTPException:
            pass
    
    # 然后尝试用户JWT认证
    if user_credentials:
        try:
            user = get_current_user(user_credentials, db)
            return {"type": "user", "auth": user}
        except HTTPException:
            pass
    
    # 最后尝试客户端凭据认证
    if user_credentials:
        try:
            client = get_current_client(user_credentials, db)
            return {"type": "client", "auth": client}
        except HTTPException:
            pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )