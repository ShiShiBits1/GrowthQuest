from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import logging
import traceback
from datetime import datetime

# 配置日志
log_level = os.environ.get('LOG_LEVEL', 'DEBUG')
try:
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
except (AttributeError, ValueError):
    # 如果日志级别无效，回退到DEBUG
    logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.session_protection = 'strong'  # 增强会话保护

# 用户登录加载函数
@login_manager.user_loader
def load_user(user_id):
    # 延迟导入以避免循环导入
    try:
        from app.models import User
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f'加载用户时发生错误: {str(e)}')
        logger.error(traceback.format_exc())
        return None

def create_app(config_name=None):
    """创建应用实例的工厂函数"""
    logger.debug('正在创建Flask应用实例')
    app = Flask(__name__)
    
    # 配置 - 支持从环境变量加载配置
    # 从环境变量获取SECRET_KEY，如果没有则使用默认值
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hard-to-guess-string')
    
    # 数据库配置 - 支持从环境变量覆盖
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(basedir, "data.sqlite")}')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    
    # 会话配置
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24  # 24小时
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 初始化扩展
    logger.debug('初始化数据库扩展')
    db.init_app(app)
    logger.debug('初始化登录扩展')
    login_manager.init_app(app)
    
    # 添加Python内置函数到Jinja2模板全局上下文
    app.jinja_env.globals.update(hasattr=hasattr)
    
    # 添加简单的健康检查路由
    @app.route('/health')
    def health_check():
        logger.debug('健康检查路由被访问')
        logger.info('健康检查请求')
        
        # 简化版本：只返回基本状态信息，不进行数据库检查
        # 这样即使数据库有问题，健康检查也能响应
        try:
            return jsonify({
                'status': 'running',
                'message': '应用正在运行',
                'app_name': '成长奖励系统',
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f'健康检查路由异常: {str(e)}')
            logger.error(traceback.format_exc())
            # 返回一个最基本的成功响应
            return jsonify({
                'status': 'unknown',
                'message': '应用响应中',
                'timestamp': datetime.utcnow().isoformat()
            })
    
    # 移除重复的根路径路由，避免与main蓝图中的dashboard路由冲突
    # 根路径路由将由main蓝图中的dashboard函数处理
    
    # 添加全局错误处理 - 捕获所有异常
    @app.errorhandler(Exception)
    def handle_all_exceptions(error):
        logger.error(f'捕获到未处理的异常: {str(error)}')
        logger.error(traceback.format_exc())
          
        # 确定错误码，确保是整数类型
        error_code = getattr(error, 'code', None)
        status_code = int(error_code) if error_code is not None else 500
        
        # 对于开发环境，返回详细错误信息
        if app.debug:
            return jsonify({
                'error': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc().split('\n')
            }), status_code
        else:
            # 生产环境只返回安全的错误信息
            return jsonify({
                'error': '服务器错误' if status_code >= 500 else '请求错误',
                'message': '服务器暂时无法处理您的请求，请稍后再试'
            }), status_code
    
    # 404错误处理
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f'404错误: 路径 {request.path} 不存在')
        return jsonify({'error': '页面不存在', 'path': request.path}), 404
    
    # 添加全局请求处理
    @app.before_request
    def before_request():
        logger.debug(f'请求: {request.method} {request.path}')
    
    # 添加strftime过滤器
    @app.template_filter('strftime')
    def strftime_filter(date, format_str='%Y-%m-%d %H:%M:%S'):
        return date.strftime(format_str)
    
    # 延迟导入蓝图以避免循环导入
    logger.debug('准备注册蓝图')
    try:
        with app.app_context():
            # 导入并注册蓝图
            from app.main import main as main_blueprint
            logger.debug('注册main蓝图')
            app.register_blueprint(main_blueprint)
            
            from app.analytics import analytics as analytics_blueprint
            logger.debug('注册analytics蓝图')
            app.register_blueprint(analytics_blueprint)
        logger.debug('蓝图注册成功')
    except Exception as e:
        logger.error(f'注册蓝图时发生错误: {str(e)}')
        logger.error(traceback.format_exc())
        # 继续执行，让应用能够启动，即使蓝图注册失败
    
    # 直接初始化数据库，而不依赖before_first_request（在Flask新版本中已移除）
    try:
        with app.app_context():
            # 确保数据库表存在
            db.create_all()
            logger.info('数据库表创建成功')
    except Exception as e:
        logger.error(f'数据库初始化失败: {str(e)}')
        logger.error(traceback.format_exc())
    
    logger.debug(f'应用实例创建完成，数据库URI: {app.config["SQLALCHEMY_DATABASE_URI"]}')
    return app

# 创建应用实例
try:
    app = create_app()
    logger.info('应用实例创建成功')
except Exception as e:
    logger.critical(f'应用实例创建失败: {str(e)}')
    logger.critical(traceback.format_exc())
    raise

# 导出必要的变量
__all__ = ['app', 'db', 'login_manager', 'create_app']

# 导入request对象用于请求处理
from flask import request