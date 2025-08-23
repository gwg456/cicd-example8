from flask import Blueprint, request, jsonify, redirect, current_app, session
from auth import oauth, generate_jwt_token, create_or_update_user, token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login')
def login():
    """启动OIDC登录流程"""
    try:
        # 生成授权URL并重定向到Azure AD
        redirect_uri = current_app.config['AZURE_REDIRECT_URI']
        return oauth.azure.authorize_redirect(redirect_uri)
    except Exception as e:
        return jsonify({'error': 'Failed to initiate login', 'details': str(e)}), 500

@auth_bp.route('/callback')
def callback():
    """处理OIDC回调"""
    try:
        # 获取授权码并交换token
        token = oauth.azure.authorize_access_token()
        
        # 获取用户信息
        user_info = token.get('userinfo')
        if not user_info:
            # 如果userinfo不在token中，尝试从ID token解析
            id_token = token.get('id_token')
            if id_token:
                user_info = oauth.azure.parse_id_token(token)
        
        if not user_info:
            return jsonify({'error': 'Failed to get user information'}), 400
        
        # 创建或更新用户
        user = create_or_update_user(user_info)
        
        # 生成JWT token
        jwt_token = generate_jwt_token(user.id, user.azure_id, user.email)
        
        # 重定向到前端，带上token
        frontend_url = current_app.config['FRONTEND_URL']
        return redirect(f"{frontend_url}/auth/callback?token={jwt_token}")
        
    except Exception as e:
        return jsonify({'error': 'Authentication failed', 'details': str(e)}), 500

@auth_bp.route('/user')
@token_required
def get_user():
    """获取当前用户信息"""
    user = request.current_user
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'age': user.age,
        'gender': user.gender,
        'height': user.height,
        'current_weight': user.current_weight,
        'target_weight': user.target_weight,
        'activity_level': user.activity_level
    })

@auth_bp.route('/user', methods=['PUT'])
@token_required
def update_user():
    """更新用户信息"""
    try:
        user = request.current_user
        data = request.get_json()
        
        # 更新允许的字段
        if 'age' in data:
            user.age = data['age']
        if 'gender' in data:
            user.gender = data['gender']
        if 'height' in data:
            user.height = data['height']
        if 'current_weight' in data:
            user.current_weight = data['current_weight']
        if 'target_weight' in data:
            user.target_weight = data['target_weight']
        if 'activity_level' in data:
            user.activity_level = data['activity_level']
        
        from models import db
        db.session.commit()
        
        return jsonify({'message': 'User updated successfully'})
        
    except Exception as e:
        return jsonify({'error': 'Failed to update user', 'details': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """用户登出"""
    # 在前后端分离架构中，登出主要是前端清除token
    # 这里可以添加token黑名单逻辑（如果需要的话）
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/verify')
@token_required
def verify_token():
    """验证token有效性"""
    return jsonify({'valid': True, 'user_id': request.current_user.id})