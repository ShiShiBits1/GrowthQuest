# 简化版应用，用于排查问题
from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 简单的用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

# 用户加载器
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 健康检查路由
@app.route('/health')
def health_check():
    logger.debug('健康检查路由被访问')
    return jsonify({'status': 'healthy', 'message': '简化版应用运行正常'})

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        logger.debug('登录路由被访问')
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            logger.debug(f'登录请求: {username}')
            
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return jsonify({'message': '登录成功'})
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # 简单的登录表单
        return render_template_string('''
        <html>
        <body>
            <h1>登录</h1>
            <form method="post">
                <input type="text" name="username" placeholder="用户名"><br>
                <input type="password" name="password" placeholder="密码"><br>
                <button type="submit">登录</button>
            </form>
        </body>
        </html>
        ''')
    except Exception as e:
        logger.error(f'登录错误: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# 主页路由
@app.route('/')
def index():
    return jsonify({'message': '欢迎使用简化版成长奖励系统'})

# 初始化数据库
with app.app_context():
    db.create_all()
    # 创建测试用户
    if not User.query.first():
        user = User(
            username='admin',
            password=generate_password_hash('admin123')
        )
        db.session.add(user)
        db.session.commit()
        print('测试用户创建成功: admin/admin123')

if __name__ == '__main__':
    logger.debug('启动简化版应用')
    app.run(host='0.0.0.0', port=5000, debug=True)