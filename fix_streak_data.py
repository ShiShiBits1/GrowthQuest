from app import create_app, db
from app.models import Task, TaskRecord, TaskStreak, Badge, Child
from datetime import datetime, date

# 创建Flask应用
app = create_app()

# 在应用上下文中运行
with app.app_context():
    print("开始修复连续任务挑战数据...")
    
    # 获取所有孩子
    children = Child.query.all()
    print(f"找到 {len(children)} 个孩子")
    
    # 为每个孩子处理
    for child in children:
        print(f"处理孩子: {child.name}")
        
        # 获取该孩子所有已确认的任务记录，按日期排序
        confirmed_records = TaskRecord.query.filter_by(
            child_id=child.id,
            is_confirmed=True
        ).order_by(TaskRecord.completed_at).all()
        
        print(f"  找到 {len(confirmed_records)} 条已确认的任务记录")
        
        # 按任务ID分组处理
        task_records_map = {}
        for record in confirmed_records:
            if record.task_id not in task_records_map:
                task_records_map[record.task_id] = []
            task_records_map[record.task_id].append(record)
        
        # 为每个任务创建或更新连续记录
        for task_id, records in task_records_map.items():
            # 获取任务
            task = Task.query.get(task_id)
            if not task:
                continue
            
            print(f"  处理任务: {task.name}")
            
            # 检查是否已有连续记录
            streak = TaskStreak.query.filter_by(child_id=child.id, task_id=task_id).first()
            
            if not streak:
                # 创建新的连续记录
                # 找到该任务的最后完成日期
                last_record = max(records, key=lambda r: r.completed_at)
                last_date = last_record.completed_at.date()
                
                # 创建连续记录（保守设置为1天）
                streak = TaskStreak(
                    child_id=child.id,
                    task_id=task_id,
                    current_streak=1,  # 保守设置为1天
                    last_completed_date=last_date,
                    longest_streak=1  # 保守设置为1天
                )
                db.session.add(streak)
                print(f"    创建了连续任务记录: {task.name}")
            
            # 确保该任务有勋章
            existing_badge = Badge.query.filter_by(task_id=task_id).first()
            if not existing_badge:
                # 创建默认勋章
                badge = Badge(
                    name=f"{task.name}坚持达人",
                    description=f"连续30天完成{task.name}任务，获得此勋章！",
                    icon="🏆",
                    task_id=task_id,
                    days_required=30,
                    level="初级",
                    points_reward=10
                )
                db.session.add(badge)
                print(f"    为任务 '{task.name}' 创建了默认勋章")
    
    # 提交所有更改
    try:
        db.session.commit()
        print("\n连续任务挑战数据修复成功！")
        print("现在荣誉墙应该可以正确显示挑战任务了。")
    except Exception as e:
        print(f"\n错误：保存更改时出错 - {e}")
        db.session.rollback()