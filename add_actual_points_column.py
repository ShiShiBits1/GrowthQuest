from app import create_app, db
from app.models import TaskRecord
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
        
        # 检查并添加actual_points列
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('task_record')]
        
        if 'actual_points' not in columns:
            logger.info('添加actual_points列到task_record表')
            conn.execute(db.text('ALTER TABLE task_record ADD COLUMN actual_points INTEGER'))
        
        # 更新现有记录的actual_points值为对应的任务默认积分
        logger.info('更新现有记录的actual_points值')
        task_records = TaskRecord.query.all()
        for record in task_records:
            if record.is_confirmed:  # 只更新已确认的记录
                record.actual_points = record.task.points
        
        db.session.commit()
        logger.info(f'成功更新了{len(task_records)}条记录的actual_points值')
        
        trans.commit()
        logger.info('数据库更新成功')
        
    except Exception as e:
        logger.error(f'数据库更新失败: {str(e)}')
        if 'trans' in locals():
            trans.rollback()
        raise