from app import create_app, db
from app.models import Child
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建应用实例
app = create_app()

with app.app_context():
    try:
        # 获取数据库连接
        conn = db.engine.connect()
        trans = conn.begin()
        
        # 检查并添加username列
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('child')]
        
        if 'username' not in columns:
            logger.info('添加username列到child表')
            conn.execute(db.text('ALTER TABLE child ADD COLUMN username VARCHAR(64)'))
        
        if 'password' not in columns:
            logger.info('添加password列到child表')
            conn.execute(db.text('ALTER TABLE child ADD COLUMN password VARCHAR(128)'))
        
        # 设置默认值
        if 'username' in columns and 'password' in columns:
            logger.info('更新现有记录的默认值')
            children = Child.query.all()
            for child in children:
                if not child.username:
                    child.username = f'child_{child.id}'
                    child.password = 'default_password'  # 生产环境中应该生成随机密码
            db.session.commit()
        
        # 创建唯一索引
        conn.execute(db.text('CREATE UNIQUE INDEX IF NOT EXISTS ix_child_username ON child(username)'))
        
        trans.commit()
        logger.info('数据库更新成功')
        
    except Exception as e:
        logger.error(f'数据库更新失败: {str(e)}')
        if 'trans' in locals():
            trans.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()