#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用户路由模块
提供用户注册、登录、信息管理等API接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.schemas.user import (
    UserCreate, UserResponse, UserUpdate, UserPasswordChange,
    UserListResponse, UserSearchParams, UserApiResponse
)
from app.schemas.auth import LoginRequest, LoginResponse, Token
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user, get_current_active_user
from app.utils.security import get_client_ip, get_user_agent
from app.config import settings

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

# OAuth2方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

# 依赖注入服务
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """获取用户服务实例"""
    return UserService(db)

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)

@router.post(
    "/register",
    response_model=UserApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户",
    tags=["用户管理"]
)
async def register_user(
    user_data: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """
    用户注册接口
    
    - **username**: 用户名（3-20个字符，只能包含字母、数字、下划线、连字符）
    - **email**: 邮箱地址
    - **password**: 密码（8-50个字符，需要包含大小写字母和数字）
    - **password_confirm**: 确认密码
    - **full_name**: 全名（可选）
    - **bio**: 个人简介（可选）
    """
    
    # 检查是否允许注册
    if not settings.ENABLE_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户注册功能已禁用"
        )
    
    try:
        # 获取客户端信息
        client_ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        logger.info(f"用户注册请求: {user_data.username} ({user_data.email}) from {client_ip}")
        
        # 创建用户
        user = await user_service.create_user(
            user_data=user_data,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        # 如果需要邮箱验证，发送验证邮件
        if settings.REQUIRE_EMAIL_VERIFICATION:
            background_tasks.add_task(
                user_service.send_verification_email,
                user.email,
                user.username
            )
        
        logger.info(f"用户注册成功: {user.username} (ID: {user.id})")
        
        return UserApiResponse(
            success=True,
            message="注册成功",
            data=UserResponse.from_orm(user)
        )
        
    except ValueError as e:
        logger.warning(f"用户注册验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录",
    description="用户登录获取JWT Token",
    tags=["认证授权"]
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录接口
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    
    返回JWT Token用于后续API调用认证
    """
    
    try:
        # 获取客户端信息
        client_ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        logger.info(f"用户登录请求: {form_data.username} from {client_ip}")
        
        # 用户登录验证
        login_result = await auth_service.authenticate_user(
            username=form_data.username,
            password=form_data.password,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        if not login_result.success:
            logger.warning(f"用户登录失败: {form_data.username} - {login_result.message}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=login_result.message,
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 生成JWT Token
        token_data = await auth_service.create_access_token(
            user_id=login_result.user.id,
            username=login_result.user.username
        )
        
        logger.info(f"用户登录成功: {login_result.user.username} (ID: {login_result.user.id})")
        
        return LoginResponse(
            access_token=token_data.access_token,
            token_type=token_data.token_type,
            expires_in=token_data.expires_in,
            refresh_token=token_data.refresh_token,
            user=UserResponse.from_orm(login_result.user).dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )

@router.get(
    "/profile",
    response_model=UserApiResponse,
    summary="获取用户信息",
    description="获取当前登录用户的详细信息",
    tags=["用户管理"]
)
async def get_user_profile(
    current_user=Depends(get_current_active_user)
):
    """
    获取用户信息接口（需要认证）
    
    返回当前登录用户的详细信息
    """
    
    try:
        logger.info(f"获取用户信息: {current_user.username} (ID: {current_user.id})")
        
        return UserApiResponse(
            success=True,
            message="获取用户信息成功",
            data=UserResponse.from_orm(current_user)
        )
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

@router.put(
    "/profile",
    response_model=UserApiResponse,
    summary="更新用户信息",
    description="更新当前登录用户的信息",
    tags=["用户管理"]
)
async def update_user_profile(
    user_update: UserUpdate,
    current_user=Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    更新用户信息接口（需要认证）
    
    - **full_name**: 全名
    - **bio**: 个人简介
    - **avatar_url**: 头像URL
    """
    
    try:
        logger.info(f"更新用户信息: {current_user.username} (ID: {current_user.id})")
        
        # 更新用户信息
        updated_user = await user_service.update_user(
            user_id=current_user.id,
            user_update=user_update
        )
        
        logger.info(f"用户信息更新成功: {updated_user.username}")
        
        return UserApiResponse(
            success=True,
            message="用户信息更新成功",
            data=UserResponse.from_orm(updated_user)
        )
        
    except ValueError as e:
        logger.warning(f"用户信息更新验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"用户信息更新失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户信息失败"
        )

@router.post(
    "/change-password",
    response_model=UserApiResponse,
    summary="修改密码",
    description="修改当前登录用户的密码",
    tags=["用户管理"]
)
async def change_password(
    password_data: UserPasswordChange,
    request: Request,
    current_user=Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    修改密码接口（需要认证）
    
    - **current_password**: 当前密码
    - **new_password**: 新密码
    - **new_password_confirm**: 确认新密码
    """
    
    try:
        client_ip = get_client_ip(request)
        logger.info(f"用户修改密码: {current_user.username} from {client_ip}")
        
        # 修改密码
        await user_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
            client_ip=client_ip
        )
        
        logger.info(f"用户密码修改成功: {current_user.username}")
        
        return UserApiResponse(
            success=True,
            message="密码修改成功",
            data=None
        )
        
    except ValueError as e:
        logger.warning(f"密码修改验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"密码修改失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )

@router.get(
    "/list",
    response_model=UserListResponse,
    summary="获取用户列表",
    description="获取用户列表（管理员功能）",
    tags=["用户管理"]
)
async def get_users_list(
    search_params: UserSearchParams = Depends(),
    current_user=Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    获取用户列表接口（需要管理员权限）
    
    支持搜索、过滤、分页和排序
    """
    
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        logger.info(f"管理员获取用户列表: {current_user.username}")
        
        # 获取用户列表
        users_result = await user_service.get_users_list(search_params)
        
        return UserListResponse(
            users=[UserResponse.from_orm(user) for user in users_result.users],
            total=users_result.total,
            page=search_params.page,
            size=search_params.size,
            pages=(users_result.total + search_params.size - 1) // search_params.size
        )
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )

@router.get(
    "/{user_id}",
    response_model=UserApiResponse,
    summary="获取指定用户信息",
    description="根据用户ID获取用户信息（管理员功能）",
    tags=["用户管理"]
)
async def get_user_by_id(
    user_id: int,
    current_user=Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    获取指定用户信息接口（需要管理员权限或本人）
    """
    
    # 检查权限：管理员或本人
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    try:
        logger.info(f"获取用户信息: ID {user_id} by {current_user.username}")
        
        # 获取用户信息
        user = await user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserApiResponse(
            success=True,
            message="获取用户信息成功",
            data=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )

@router.delete(
    "/{user_id}",
    response_model=UserApiResponse,
    summary="删除用户",
    description="删除指定用户（管理员功能）",
    tags=["用户管理"]
)
async def delete_user(
    user_id: int,
    current_user=Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    删除用户接口（需要管理员权限）
    
    执行软删除，用户数据会被保留但标记为已删除
    """
    
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    # 不能删除自己
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    try:
        logger.info(f"管理员删除用户: ID {user_id} by {current_user.username}")
        
        # 删除用户
        result = await user_service.delete_user(user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        logger.info(f"用户删除成功: ID {user_id}")
        
        return UserApiResponse(
            success=True,
            message="用户删除成功",
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )

@router.post(
    "/{user_id}/activate",
    response_model=UserApiResponse,
    summary="激活用户",
    description="激活指定用户账户（管理员功能）",
    tags=["用户管理"]
)
async def activate_user(
    user_id: int,
    current_user=Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    激活用户接口（需要管理员权限）
    """
    
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        logger.info(f"管理员激活用户: ID {user_id} by {current_user.username}")
        
        # 激活用户
        user = await user_service.activate_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        logger.info(f"用户激活成功: ID {user_id}")
        
        return UserApiResponse(
            success=True,
            message="用户激活成功",
            data=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"激活用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="激活用户失败"
        )

@router.post(
    "/{user_id}/deactivate",
    response_model=UserApiResponse,
    summary="禁用用户",
    description="禁用指定用户账户（管理员功能）",
    tags=["用户管理"]
)
async def deactivate_user(
    user_id: int,
    current_user=Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    禁用用户接口（需要管理员权限）
    """
    
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    # 不能禁用自己
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己的账户"
        )
    
    try:
        logger.info(f"管理员禁用用户: ID {user_id} by {current_user.username}")
        
        # 禁用用户
        user = await user_service.deactivate_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        logger.info(f"用户禁用成功: ID {user_id}")
        
        return UserApiResponse(
            success=True,
            message="用户禁用成功",
            data=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"禁用用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="禁用用户失败"
        )

# 用户统计接口（管理员功能）
@router.get(
    "/stats/overview",
    summary="用户统计概览",
    description="获取用户统计信息（管理员功能）",
    tags=["用户管理"]
)
async def get_user_stats(
    current_user=Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    获取用户统计信息接口（需要管理员权限）
    """
    
    # 检查管理员权限
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要管理员权限"
        )
    
    try:
        logger.info(f"管理员获取用户统计: {current_user.username}")
        
        # 获取统计信息
        stats = await user_service.get_user_stats()
        
        return {
            "success": True,
            "message": "获取统计信息成功",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取用户统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        )