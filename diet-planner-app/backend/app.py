from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from config import Config
from models import db
from auth import init_oauth
from routes.auth_routes import auth_bp
from routes.diet_routes import diet_bp

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # 配置CORS，允许前端跨域访问
    CORS(app, origins=[app.config['FRONTEND_URL']], supports_credentials=True)
    
    # 初始化OAuth
    init_oauth(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(diet_bp)
    
    # 健康检查端点
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'Diet Planner API is running'})
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000)