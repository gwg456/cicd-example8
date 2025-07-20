"""
Client Authentication Routes
客户端认证相关的API路由 - 支持外部客户端的API访问
"""

from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from .. import crud, schemas, models
from ..database import get_db
from ..client_auth import client_auth_service
from ..dependencies import get_current_user, get_current_client
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/client", tags=["Client Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=schemas.APIClientWithSecret)
def register_client(
    client: schemas.APIClientCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """注册新的API客户端"""
    
    # 检查用户是否已达到客户端数量限制
    user_clients = crud.get_user_api_clients(db, current_user.id)
    if len(user_clients) >= settings.max_clients_per_user:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum number of clients ({settings.max_clients_per_user}) reached"
        )
    
    # 创建客户端
    db_client = crud.create_api_client(db, client, current_user.id)
    
    logger.info(f"Created new API client {db_client.client_id} for user {current_user.username}")
    
    return db_client


@router.get("/", response_model=List[schemas.APIClient])
def list_clients(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有API客户端"""
    return crud.get_user_api_clients(db, current_user.id)


@router.get("/{client_id}", response_model=schemas.APIClientWithKeys)
def get_client(
    client_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取特定客户端详情（包含API密钥列表）"""
    client = crud.get_api_client_by_id(db, client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 检查权限
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 加载API密钥
    client.api_keys = crud.get_client_api_keys(db, client.id)
    
    return client


@router.put("/{client_id}", response_model=schemas.APIClient)
def update_client(
    client_id: str,
    client_update: schemas.APIClientUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新API客户端"""
    client = crud.get_api_client_by_id(db, client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 检查权限
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_client = crud.update_api_client(db, client_id, client_update)
    
    logger.info(f"Updated API client {client_id} by user {current_user.username}")
    
    return updated_client


@router.delete("/{client_id}")
def delete_client(
    client_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除API客户端"""
    client = crud.get_api_client_by_id(db, client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 检查权限
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = crud.delete_api_client(db, client_id)
    
    if success:
        logger.info(f"Deleted API client {client_id} by user {current_user.username}")
        return {"message": "Client deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete client")


@router.post("/token", response_model=schemas.ClientAccessTokenResponse)
def get_client_token(
    request: schemas.ClientCredentialsRequest,
    db: Session = Depends(get_db)
):
    """客户端凭据流 - 获取访问令牌"""
    
    if request.grant_type != "client_credentials":
        raise HTTPException(
            status_code=400,
            detail="Unsupported grant type"
        )
    
    # 验证客户端凭据
    client = crud.authenticate_client(db, request.client_id, request.client_secret)
    
    if not client:
        raise HTTPException(
            status_code=401,
            detail="Invalid client credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 解析请求的权限范围
    requested_scopes = request.scope.split() if request.scope else ["read"]
    
    # 检查客户端是否有请求的权限
    if not client_auth_service.check_client_permissions(client.client_id, requested_scopes, db):
        raise HTTPException(
            status_code=403,
            detail="Insufficient client permissions"
        )
    
    # 创建访问令牌
    access_token = client_auth_service.create_client_access_token(
        client_id=client.client_id,
        scopes=requested_scopes
    )
    
    logger.info(f"Issued access token for client {client.client_id}")
    
    return schemas.ClientAccessTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.client_token_expire_minutes * 60,
        scope=" ".join(requested_scopes)
    )


@router.post("/{client_id}/keys", response_model=schemas.APIKeyWithValue)
def create_api_key(
    client_id: str,
    api_key: schemas.APIKeyCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """为客户端创建API密钥"""
    client = crud.get_api_client_by_id(db, client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 检查权限
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 创建API密钥
    db_key = crud.create_api_key(db, api_key, client.id)
    
    logger.info(f"Created API key {db_key.key_id} for client {client_id}")
    
    return db_key


@router.get("/{client_id}/keys", response_model=List[schemas.APIKey])
def list_api_keys(
    client_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取客户端的所有API密钥"""
    client = crud.get_api_client_by_id(db, client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 检查权限
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return crud.get_client_api_keys(db, client.id)


@router.delete("/{client_id}/keys/{key_id}")
def revoke_api_key(
    client_id: str,
    key_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """撤销API密钥"""
    client = crud.get_api_client_by_id(db, client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # 检查权限
    if client.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 验证密钥属于该客户端
    api_key = crud.get_api_key_by_id(db, key_id)
    if not api_key or api_key.client_id != client.id:
        raise HTTPException(status_code=404, detail="API key not found")
    
    success = crud.revoke_api_key(db, key_id)
    
    if success:
        logger.info(f"Revoked API key {key_id} for client {client_id}")
        return {"message": "API key revoked successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to revoke API key")


@router.get("/auth/verify")
def verify_client_auth(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """验证客户端令牌（用于测试）"""
    
    token = credentials.credentials
    
    # 验证令牌
    payload = client_auth_service.verify_client_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # 检查客户端状态
    client = crud.get_api_client_by_id(db, payload["client_id"])
    if not client or not client.is_active:
        raise HTTPException(
            status_code=401,
            detail="Client not found or inactive"
        )
    
    return {
        "authenticated": True,
        "client_id": payload["client_id"],
        "scopes": payload["scopes"],
        "token_type": payload["token_type"],
        "expires_at": payload["exp"]
    }