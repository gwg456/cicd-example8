"""
OIDC Authentication Routes
OIDC认证相关的API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from .. import crud, schemas, models
from ..database import get_db
from ..oidc_config import oidc_settings
from ..oidc_service import oidc_service
from ..auth import create_access_token
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/oidc", tags=["OIDC Authentication"])


@router.get("/providers")
def get_available_providers():
    """获取可用的OIDC提供商列表"""
    providers = []
    for provider_name in oidc_settings.get_available_providers():
        provider_config = oidc_settings.get_provider(provider_name)
        providers.append({
            "name": provider_name,
            "display_name": provider_config.name,
            "login_url": f"/auth/oidc/login/{provider_name}"
        })
    
    return {
        "providers": providers,
        "count": len(providers)
    }


@router.get("/login/{provider_name}")
def initiate_oidc_login(
    provider_name: str,
    request: Request,
    response: Response
):
    """启动OIDC登录流程"""
    if not oidc_settings.is_provider_enabled(provider_name):
        raise HTTPException(
            status_code=404,
            detail=f"Provider {provider_name} not found or not configured"
        )
    
    try:
        # 生成安全参数
        state = oidc_service.generate_state()
        nonce = oidc_service.generate_nonce()
        code_verifier = oidc_service.generate_code_verifier()
        
        # 存储在session中 (这里简化处理，实际应用中应使用secure session)
        session_data = {
            "oidc_state": state,
            "oidc_nonce": nonce,
            "oidc_code_verifier": code_verifier,
            "oidc_provider": provider_name
        }
        
        # 设置session cookie (简化版本)
        response.set_cookie(
            key="oidc_session",
            value=f"{state}:{nonce}:{code_verifier}:{provider_name}",
            max_age=settings.session_max_age,
            httponly=True,
            secure=not settings.debug,
            samesite="lax"
        )
        
        # 构建授权URL
        auth_url = oidc_service.build_authorization_url(
            provider_name=provider_name,
            state=state,
            nonce=nonce,
            code_verifier=code_verifier
        )
        
        return RedirectResponse(url=auth_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Failed to initiate OIDC login for {provider_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate login: {str(e)}"
        )


@router.get("/callback/{provider_name}")
def handle_oidc_callback(
    provider_name: str,
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """处理OIDC回调"""
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"OIDC error: {error} - {error_description or 'No description'}"
        )
    
    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing authorization code or state parameter"
        )
    
    # 获取session数据
    session_cookie = request.cookies.get("oidc_session")
    if not session_cookie:
        raise HTTPException(
            status_code=400,
            detail="Missing session data"
        )
    
    try:
        session_parts = session_cookie.split(":")
        if len(session_parts) != 4:
            raise ValueError("Invalid session data format")
        
        stored_state, stored_nonce, stored_code_verifier, stored_provider = session_parts
        
        # 验证state参数
        if state != stored_state:
            raise HTTPException(
                status_code=400,
                detail="Invalid state parameter"
            )
        
        # 验证provider
        if provider_name != stored_provider:
            raise HTTPException(
                status_code=400,
                detail="Provider mismatch"
            )
        
        # 用授权码换取tokens
        token_response = oidc_service.exchange_code_for_tokens(
            provider_name=provider_name,
            code=code,
            state=state,
            code_verifier=stored_code_verifier
        )
        
        access_token = token_response.get("access_token")
        id_token = token_response.get("id_token")
        
        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="No access token received"
            )
        
        # 获取用户信息
        user_info = oidc_service.get_userinfo(provider_name, access_token)
        
        # 如果有ID Token，验证它
        if id_token and "openid" in oidc_settings.get_provider(provider_name).scopes:
            try:
                id_claims = oidc_service.verify_id_token(provider_name, id_token, stored_nonce)
                # 可以将ID Token中的信息与userinfo合并
                user_info.update(id_claims)
            except Exception as e:
                logger.warning(f"ID token verification failed: {e}")
        
        # 标准化用户信息
        normalized_user_info = oidc_service.normalize_user_info(provider_name, user_info)
        
        # 查找或创建用户
        user = handle_user_from_oidc(db, normalized_user_info)
        
        # 创建内部JWT token
        internal_token = create_access_token(
            data={"sub": user.username, "provider": provider_name}
        )
        
        # 清除session cookie
        response.delete_cookie("oidc_session")
        
        # 返回成功响应
        return {
            "access_token": internal_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "provider": provider_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OIDC callback error for {provider_name}: {e}")
        response.delete_cookie("oidc_session")
        raise HTTPException(
            status_code=500,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/logout/{provider_name}")
def initiate_oidc_logout(
    provider_name: str,
    id_token_hint: Optional[str] = None
):
    """启动OIDC注销流程"""
    if not oidc_settings.is_provider_enabled(provider_name):
        raise HTTPException(
            status_code=404,
            detail=f"Provider {provider_name} not found"
        )
    
    logout_url = oidc_service.build_logout_url(provider_name, id_token_hint)
    
    if logout_url:
        return {"logout_url": logout_url}
    else:
        return {"message": "Logout completed (no provider logout URL available)"}


def handle_user_from_oidc(db: Session, user_info: Dict[str, Any]) -> models.User:
    """处理来自OIDC的用户信息，查找或创建用户"""
    provider = user_info["provider"]
    provider_user_id = user_info["provider_user_id"]
    email = user_info["email"]
    
    if not provider_user_id:
        raise ValueError("Provider user ID is required")
    
    # 首先尝试通过provider和provider_user_id查找用户
    user = crud.get_user_by_provider_id(db, provider, provider_user_id)
    
    if user:
        # 用户存在，更新信息（如果启用了更新功能）
        if settings.oidc_update_user_info:
            update_data = {}
            if user_info["name"] and user_info["name"] != user.full_name:
                update_data["full_name"] = user_info["name"]
            if user_info["email"] and user_info["email"] != user.email:
                update_data["email"] = user_info["email"]
            
            if update_data:
                user = crud.update_user(db, user.id, schemas.UserUpdate(**update_data))
        
        return user
    
    # 如果用户不存在，检查是否允许自动注册
    if not settings.oidc_auto_register:
        raise HTTPException(
            status_code=403,
            detail="Auto-registration is disabled. Please contact administrator."
        )
    
    # 检查邮箱是否已被其他用户使用
    if email:
        existing_user = crud.get_user_by_email(db, email)
        if existing_user:
            # 邮箱已存在，但可能是同一个用户的不同provider
            # 这里可以选择链接账户或报错
            raise HTTPException(
                status_code=409,
                detail="Email already registered with different provider"
            )
    
    # 创建新用户
    username = generate_username_from_oidc(user_info)
    
    # 确保用户名唯一
    base_username = username
    counter = 1
    while crud.get_user_by_username(db, username):
        username = f"{base_username}{counter}"
        counter += 1
    
    # 创建用户数据
    user_create = schemas.UserCreate(
        username=username,
        email=email or f"{username}@{provider}.local",
        password="",  # OIDC用户不需要密码
        full_name=user_info["name"] or username
    )
    
    # 创建用户
    user = crud.create_user(db, user_create, is_oidc_user=True)
    
    # 创建provider关联
    crud.create_user_provider_link(
        db=db,
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_data=user_info["raw_user_info"]
    )
    
    return user


def generate_username_from_oidc(user_info: Dict[str, Any]) -> str:
    """从OIDC用户信息生成用户名"""
    provider = user_info["provider"]
    
    # 优先使用邮箱前缀
    if user_info["email"]:
        email_prefix = user_info["email"].split("@")[0]
        if email_prefix and len(email_prefix) >= 3:
            return email_prefix.lower()
    
    # 使用名字
    if user_info["name"]:
        name = user_info["name"].lower().replace(" ", "").replace(".", "")
        if len(name) >= 3:
            return name
    
    # 使用given_name
    if user_info["given_name"]:
        given_name = user_info["given_name"].lower().replace(" ", "")
        if len(given_name) >= 3:
            return given_name
    
    # 最后使用provider + provider_user_id
    provider_user_id = str(user_info["provider_user_id"])[-8:]  # 取后8位
    return f"{provider}_{provider_user_id}"