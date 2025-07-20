#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI用户服务主应用
提供用户注册、登录和JWT认证功能
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
import time
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_tables
from app.routers import user, auth

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动FastAPI用户服务...")
    
    # 创建数据库表
    try:
        create_tables()
        logger.info("✅ 数据库表创建成功")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise
    
    yield
    
    # 关闭时执行
    logger.info("🛑 FastAPI用户服务关闭")

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description="基于FastAPI的现代化用户管理服务，提供JWT认证功能",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 添加可信主机中间件（生产环境安全）
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # 记录请求日志
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.3f}s")
    
    return response

# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """数据验证异常处理"""
    logger.warning(f"数据验证错误: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "数据验证失败",
            "details": exc.errors(),
            "status_code": 422,
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "服务器内部错误",
            "status_code": 500,
            "path": str(request.url)
        }
    )

# 注册路由
app.include_router(
    user.router,
    prefix="/user",
    tags=["用户管理"],
    responses={
        404: {"description": "用户不存在"},
        422: {"description": "数据验证错误"}
    }
)

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["认证授权"],
    responses={
        401: {"description": "认证失败"},
        403: {"description": "权限不足"}
    }
)

# 根路径欢迎页面
@app.get("/", tags=["系统"])
async def root():
    """API根路径，返回服务信息"""
    return {
        "message": "欢迎使用FastAPI用户服务",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }

# 健康检查接口
@app.get("/health", tags=["系统"])
async def health_check():
    """服务健康检查"""
    try:
        # 检查数据库连接
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "app_name": settings.APP_NAME,
            "version": settings.VERSION,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e),
                "database": "disconnected"
            }
        )

# API信息接口
@app.get("/info", tags=["系统"])
async def api_info():
    """获取API详细信息"""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "description": "基于FastAPI的用户管理服务",
        "features": [
            "用户注册",
            "用户登录",
            "JWT认证",
            "密码加密",
            "数据验证",
            "API文档"
        ],
        "endpoints": {
            "用户注册": "POST /user/register",
            "用户登录": "POST /user/login",
            "用户信息": "GET /user/profile",
            "更新信息": "PUT /user/profile",
            "刷新Token": "POST /auth/refresh",
            "健康检查": "GET /health"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"启动{settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info(f"数据库: {settings.DATABASE_URL}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True
    )