"""
Client Authentication Module
客户端认证模块 - 支持外部客户端的API认证
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from jose import jwt

from .config import settings
from . import models, schemas, crud


class ClientAuthService:
    """客户端认证服务"""
    
    def __init__(self):
        self.algorithm = "HS256"
    
    def generate_client_credentials(self) -> Dict[str, str]:
        """生成客户端凭据 (Client ID 和 Client Secret)"""
        client_id = f"client_{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32)
        
        return {
            "client_id": client_id,
            "client_secret": client_secret
        }
    
    def generate_api_key(self, client_id: str) -> str:
        """生成API密钥"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        data = f"{client_id}:{timestamp}:{secrets.token_urlsafe(16)}"
        return f"ak_{hashlib.sha256(data.encode()).hexdigest()[:32]}"
    
    def create_client_access_token(
        self, 
        client_id: str, 
        scopes: List[str], 
        expires_minutes: Optional[int] = None
    ) -> str:
        """创建客户端访问令牌"""
        if expires_minutes is None:
            expires_minutes = settings.client_token_expire_minutes
        
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
        
        payload = {
            "sub": client_id,
            "client_id": client_id,
            "scopes": scopes,
            "token_type": "client_credentials",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, settings.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_client_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证客户端令牌"""
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[self.algorithm])
            
            # 检查令牌类型
            if payload.get("token_type") != "client_credentials":
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def verify_api_key_signature(
        self, 
        api_key: str, 
        timestamp: str, 
        signature: str, 
        client_secret: str
    ) -> bool:
        """验证API密钥签名"""
        # 构建签名字符串
        string_to_sign = f"{api_key}:{timestamp}"
        
        # 计算期望的签名
        expected_signature = hmac.new(
            client_secret.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 比较签名
        return hmac.compare_digest(signature, expected_signature)
    
    def check_client_permissions(
        self, 
        client_id: str, 
        required_scopes: List[str],
        db: Session
    ) -> bool:
        """检查客户端权限"""
        client = crud.get_api_client_by_id(db, client_id)
        if not client or not client.is_active:
            return False
        
        # 检查客户端是否有所需的权限范围
        client_scopes = client.scopes or []
        return all(scope in client_scopes for scope in required_scopes)


# 全局客户端认证服务实例
client_auth_service = ClientAuthService()