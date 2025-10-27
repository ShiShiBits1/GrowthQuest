from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

# 创建应用实例
app = create_app()

# 初始化数据库
with app.app_context():
    # 创建所有数据库表
    db.create_all()
    
    # 检查是否已有用户，如果没有则创建默认管理员
    if not User.query.first():
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
    # 允许在所有网络接口上运行，方便NAS访问
    host = '0.0.0.0'  # 使用标准的0.0.0.0监听所有网络接口
    port = 8086
    debug = False
    print(f'启动应用服务器，监听地址: {host}:{port}')
    app.run(host=host, port=port, debug=debug)
