from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'

# 用户登录加载函数
@login_manager.user_loader
def load_user(user_id):
    # 延迟导入以避免循环导入
    from app.models import User
    return User.query.get(int(user_id))

def create_app(config_name=None):
    """创建应用实例的工厂函数"""
    logger.debug('正在创建Flask应用实例')
    app = Flask(__name__)
    
    # 配置
    app.config['SECRET_KEY'] = 'hard-to-guess-string'
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    
    # 添加简单的健康检查路由
    @app.route('/health')
    def health_check():
        logger.debug('健康检查路由被访问')
        return jsonify({
            'status': 'healthy',
            'message': '应用运行正常'
        })
    
    # 添加全局错误处理
    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error(f'发生500错误: {str(error)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'error': '内部服务器错误',
            'message': str(error)
        }), 500
    
    # 延迟导入蓝图以避免循环导入
    logger.debug('准备注册蓝图')
    try:
        with app.app_context():
            # 导入并注册蓝图
            from app.main import main as main_blueprint
            logger.debug('注册main蓝图')
            app.register_blueprint(main_blueprint)
        logger.debug('蓝图注册成功')
    except Exception as e:
        logger.error(f'注册蓝图时发生错误: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
    
    logger.debug('应用实例创建完成')
    return app

# 创建应用实例
app = create_app()

# 导出必要的变量
__all__ = ['app', 'db', 'login_manager', 'create_app']