from app import create_app, db
from sqlalchemy import text
import sys

# 创建应用实例
app = create_app()

def migrate_badge_table():
    with app.app_context():
        try:
            # 直接使用db.session执行SQL
            # 添加level字段
            try:
                db.session.execute(text("ALTER TABLE badge ADD COLUMN level VARCHAR(32) NOT NULL DEFAULT '初级'"))
                db.session.commit()
                print("已添加level字段")
            except Exception as e:
                db.session.rollback()
                if 'duplicate column name' in str(e).lower() or 'duplicate column' in str(e).lower():
                    print("level字段已存在")
                else:
                    raise
            
            # 添加points_reward字段
            try:
                db.session.execute(text("ALTER TABLE badge ADD COLUMN points_reward INTEGER DEFAULT 10"))
                db.session.commit()
                print("已添加points_reward字段")
            except Exception as e:
                db.session.rollback()
                if 'duplicate column name' in str(e).lower() or 'duplicate column' in str(e).lower():
                    print("points_reward字段已存在")
                else:
                    raise
            
            print("数据库迁移完成！")
            
        except Exception as e:
            print(f"数据库迁移时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    migrate_badge_table()