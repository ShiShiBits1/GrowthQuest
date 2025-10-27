# WSGI入口点文件，用于uWSGI和Gunicorn等WSGI服务器
import os
import sys
import logging
import traceback
from flask import Flask, request

# 配置日志，支持在宝塔环境中正确输出
log_level = os.environ.get('LOG_LEVEL', 'DEBUG')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加额外的访问日志记录
def setup_access_logging(app):
    # 添加请求日志中间件
    @app.before_request
    def log_request_info():
        app.logger.debug(f'请求路径: {request.path}')
        app.logger.debug(f'请求方法: {request.method}')
        app.logger.debug(f'请求IP: {request.remote_addr}')
        app.logger.debug(f'请求参数: {request.args}')
    
    @app.after_request
    def log_response_info(response):
        app.logger.debug(f'响应状态码: {response.status_code}')
        return response
logger = logging.getLogger(__name__)

# 添加当前目录到Python路径
base_dir = os.path.dirname(os.path.abspath(__file__))
logger.debug(f'当前文件路径: {os.path.abspath(__file__)}')
logger.debug(f'基础目录: {base_dir}')

# 确保基础目录在Python路径中
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
    logger.debug(f'添加到Python路径: {base_dir}')

# 确保app目录也在Python路径中
app_dir = os.path.join(base_dir, 'app')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
    logger.debug(f'添加app目录到Python路径: {app_dir}')

logger.debug('WSGI入口点初始化开始')

# 全局变量初始化
app = None
application = None

try:
    # 尝试导入应用创建函数而不是直接导入app
    logger.debug('尝试导入create_app函数')
    from app import create_app
    
    # 创建应用实例
    logger.debug('创建Flask应用实例')
    app = create_app()
    
    # 设置application变量以兼容WSGI服务器
    application = app
    
    # 设置访问日志记录
    setup_access_logging(app)
    
    # 添加额外的调试输出
    logger.info(f'应用已启动并监听: 0.0.0.0:8086')
    logger.info(f'可通过 http://<服务器IP>:8086 访问应用')
    logger.info(f'健康检查地址: http://<服务器IP>:8086/health')
    
    # 记录应用配置信息用于调试
    logger.debug(f'应用实例创建成功: {app}')
    logger.debug(f'应用配置 - SECRET_KEY已设置: {bool(app.config.get("SECRET_KEY"))}')
    logger.debug(f'应用配置 - DATABASE_URI: {app.config.get("SQLALCHEMY_DATABASE_URI")}')
    logger.debug(f'已注册的蓝图数量: {len(app.blueprints)}')
    logger.debug(f'应用URL规则数量: {len(list(app.url_map.iter_rules()))}')
    
    # 列出所有路由，帮助调试
    logger.debug('应用URL路由:')
    for rule in app.url_map.iter_rules():
        logger.debug(f'  {rule} -> {rule.endpoint}')
    
    # 测试数据库连接
    try:
        with app.app_context():
            from app import db
            from sqlalchemy import text
            logger.debug('测试数据库连接')
            db.session.execute(text('SELECT 1'))
            logger.debug('数据库连接测试成功')
    except Exception as db_e:
        logger.error(f'数据库连接测试失败: {str(db_e)}')
        logger.error(traceback.format_exc())
    
    logger.debug('WSGI应用准备就绪')
    
    # 确保全局变量正确设置
    globals()['app'] = app
    globals()['application'] = application
    
    # 打印关键信息到标准输出，宝塔面板可以捕获
    print(f'[INFO] WSGI应用初始化成功，监听端口: {os.environ.get("PORT", "未指定")}')
    print(f'[INFO] 数据库URI: {app.config.get("SQLALCHEMY_DATABASE_URI")}')
    
# 捕获所有可能的异常，确保提供详细的错误信息
except ImportError as ie:
    error_msg = f'导入模块失败: {str(ie)}'
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    print(f'[ERROR] {error_msg}')
    # 重新抛出异常，让WSGI服务器知道启动失败
    raise
except FileNotFoundError as fnf:
    error_msg = f'文件未找到: {str(fnf)}'
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    print(f'[ERROR] {error_msg}')
    raise
except Exception as e:
    error_msg = f'WSGI应用初始化失败: {str(e)}'
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    print(f'[ERROR] {error_msg}')
    # 确保提供完整的错误栈信息
    raise Exception(f'应用启动失败: {error_msg}\n{traceback.format_exc()}')

# 最后的保障检查
if application is None:
    error_msg = '严重错误: application变量未正确初始化'
    logger.critical(error_msg)
    print(f'[CRITICAL] {error_msg}')
    raise RuntimeError(error_msg)

if __name__ == '__main__':
    # 直接运行时使用开发服务器
    logger.debug('直接运行模式，启动开发服务器')
    # 使用标准的0.0.0.0监听所有接口
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8086))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    logger.info(f'启动开发服务器在 {host}:{port}, debug={debug}')
    
    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f'开发服务器启动失败: {str(e)}')
        logger.error(traceback.format_exc())
        raise
