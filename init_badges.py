from app import create_app, db
from app.models import Task, Badge
from datetime import datetime

# 创建Flask应用
app = create_app()

# 在应用上下文中运行
with app.app_context():
    print("开始初始化勋章系统...")
    
    # 获取所有激活的任务
    tasks = Task.query.filter_by(is_active=True).all()
    print(f"找到 {len(tasks)} 个激活的任务")
    
    created_count = 0
    
    # 为每个任务创建默认的30天勋章
    for task in tasks:
        # 检查是否已经为该任务创建了勋章
        existing_badge = Badge.query.filter_by(task_id=task.id, days_required=30).first()
        
        if not existing_badge:
            # 创建新勋章
            badge = Badge(
                name=f"{task.name}坚持达人",
                description=f"连续30天完成{task.name}任务，获得此勋章！",
                icon="🏆",
                task_id=task.id,
                days_required=30
            )
            db.session.add(badge)
            created_count += 1
            print(f"为任务 '{task.name}' 创建了勋章")
        else:
            print(f"任务 '{task.name}' 已存在勋章，跳过")
    
    # 提交更改
    if created_count > 0:
        db.session.commit()
        print(f"成功创建 {created_count} 个勋章")
    else:
        print("没有创建新勋章，所有任务已有默认勋章")
    
    print("勋章系统初始化完成！")