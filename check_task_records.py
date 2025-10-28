from datetime import date, datetime, timedelta
from app import create_app, db
from app.models import TaskRecord

# 创建Flask应用实例
app = create_app()

# 连接数据库
with app.app_context():
    # 定义10-27的日期范围
    target_date = date(2025, 10, 27)  # 假设是2025年，如果是其他年份请修改
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())
    
    print(f"查询 {target_date} 的任务完成记录...")
    
    # 查询所有子孩子在10-27的任务完成记录
    task_records = TaskRecord.query.filter(
        TaskRecord.is_confirmed == True,
        TaskRecord.completed_at >= start_datetime,
        TaskRecord.completed_at <= end_datetime
    ).all()
    
    print(f"找到 {len(task_records)} 条任务完成记录")
    
    # 按孩子ID分组统计
    from collections import defaultdict
    child_counts = defaultdict(int)
    
    for record in task_records:
        child_counts[record.child_id] += 1
        print(f"记录ID: {record.id}, 孩子ID: {record.child_id}, 任务ID: {record.task_id}, 完成时间: {record.completed_at}, 已确认: {record.is_confirmed}")
    
    print("\n各孩子完成任务统计:")
    for child_id, count in child_counts.items():
        print(f"孩子ID {child_id}: 完成 {count} 个任务")

    # 测试get_habit_timeline方法
    from app.models import Child
    
    print("\n测试get_habit_timeline方法:")
    for child_id in child_counts.keys():
        print(f"\n孩子ID {child_id} 的习惯养成时间线:")
        timeline = Child.get_habit_timeline(child_id, days=7)
        
        # 查找10-27的数据
        target_data = next((item for item in timeline if item['date'] == target_date), None)
        if target_data:
            print(f"10-27数据: completed_count={target_data['completed_count']}, unique_tasks={target_data['unique_tasks']}")
        
        # 打印所有时间线数据
        print("时间线数据:")
        for item in timeline:
            print(f"日期: {item['date']}, 完成数: {item['completed_count']}, 唯一任务数: {item['unique_tasks']}")