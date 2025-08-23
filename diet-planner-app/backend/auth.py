import jwt
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, request, jsonify, session, redirect, url_for
from authlib.integrations.flask_client import OAuth
from models import db, User

oauth = OAuth()

def init_oauth(app):
    """初始化OAuth配置"""
    oauth.init_app(app)
    
    oauth.register(
        name='azure',
        client_id=app.config['AZURE_CLIENT_ID'],
        client_secret=app.config['AZURE_CLIENT_SECRET'],
        server_metadata_url=f"{app.config['AZURE_AUTHORITY']}/v2.0/.well-known/openid_configuration",
        client_kwargs={
            'scope': ' '.join(app.config['AZURE_SCOPE'])
        }
    )

def generate_jwt_token(user_id, azure_id, email):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'azure_id': azure_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_jwt_token(token):
    """验证JWT token"""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """JWT token验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从Authorization header获取token
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_jwt_token(token)
        if payload is None:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # 获取当前用户
        current_user = User.query.get(payload['user_id'])
        if not current_user:
            return jsonify({'error': 'User not found'}), 401
        
        # 将当前用户信息添加到请求上下文
        request.current_user = current_user
        
        return f(*args, **kwargs)
    
    return decorated

def create_or_update_user(user_info):
    """创建或更新用户信息"""
    azure_id = user_info.get('sub') or user_info.get('oid')
    email = user_info.get('email') or user_info.get('preferred_username')
    name = user_info.get('name') or user_info.get('given_name', '') + ' ' + user_info.get('family_name', '')
    
    if not azure_id or not email:
        raise ValueError("Missing required user information")
    
    # 查找现有用户
    user = User.query.filter_by(azure_id=azure_id).first()
    
    if user:
        # 更新现有用户信息
        user.email = email
        user.name = name.strip()
    else:
        # 创建新用户
        user = User(
            azure_id=azure_id,
            email=email,
            name=name.strip()
        )
        db.session.add(user)
    
    db.session.commit()
    return user