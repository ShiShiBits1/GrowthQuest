import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
try:
    from app import app, db
    print('成功导入app和db')
except ImportError as e:
    print(f'导入错误: {e}')
    sys.exit(1)

try:
    from app.models import User, Child, Task, Reward, TaskRecord, RewardRecord
    print('成功导入所有模型')
except ImportError as e:
    print(f'导入模型错误: {e}')
    sys.exit(1)

# 初始化数据库
def init_database():
    try:
        with app.app_context():
            print('开始创建数据库表...')
            db.create_all()
            print('数据库表创建成功!')
            
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
                
    except Exception as e:
        print(f'数据库初始化过程中发生错误: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)

# 执行数据库初始化
if __name__ == '__main__':
    print('初始化数据库...')
    init_database()
    print('数据库初始化完成!')