# 最基础的Flask测试应用
from flask import Flask, Response
import sys

# 创建Flask应用
app = Flask(__name__)

# 最简单的路由
@app.route('/')
def hello():
    print('Hello路由被访问', file=sys.stderr)
    return Response('Hello, World!', mimetype='text/plain')

@app.route('/test')
def test():
    print('Test路由被访问', file=sys.stderr)
    return Response('Test successful!', mimetype='text/plain')

if __name__ == '__main__':
    print('启动最基础的Flask应用', file=sys.stderr)
    app.run(host='0.0.0.0', port=5001, debug=True)