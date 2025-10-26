from flask import Flask
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 创建一个最简单的Flask应用
app = Flask(__name__)

@app.route('/')
def hello():
    logger.debug('Hello路由被访问')
    return 'Hello, Flask is working!'

if __name__ == '__main__':
    logger.debug('启动测试Flask应用')
    app.run(host='0.0.0.0', port=5001, debug=True)