# 导入app包中的主要组件
from app import app, db, create_app
from app.models import User, Child, Task, Reward, TaskRecord, RewardRecord

# 添加一个简单的测试路由
@app.route('/test')
def test():
    return '测试页面正常工作！'

# 初始化数据库的函数
def init_database():
    with app.app_context():
        db.create_all()
        # 检查是否已有用户，如果没有则创建默认管理员
        if not User.query.first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username='admin',
                password=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print('默认管理员用户已创建')
            print('用户名: admin')
            print('密码: admin123')
        else:
            print('数据库已初始化，用户已存在')

if __name__ == '__main__':
    # 允许在所有网络接口上运行
    app.run(host='0.0.0.0', port=5000, debug=True)