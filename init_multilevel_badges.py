from app import create_app, db
from app.models import Task, Badge
import sys

# 创建应用实例
app = create_app()

# 定义勋章等级配置
badge_configs = [
    {'level': '初级', 'days_required': 30, 'points_reward': 10, 'icon': '🥉'},
    {'level': '中级', 'days_required': 90, 'points_reward': 20, 'icon': '🥈'},
    {'level': '高级', 'days_required': 180, 'points_reward': 30, 'icon': '🥇'},
    {'level': '毕业', 'days_required': 365, 'points_reward': 50, 'icon': '🏆'}
]

def init_badges():
    with app.app_context():
        try:
            # 获取所有任务
            tasks = Task.query.all()
            
            if not tasks:
                print("没有找到任务，无法初始化勋章")
                return
            
            print(f"找到 {len(tasks)} 个任务，开始初始化勋章...")
            
            for task in tasks:
                # 检查是否已存在该任务的勋章
                existing_badges = Badge.query.filter_by(task_id=task.id).all()
                existing_levels = [badge.level for badge in existing_badges]
                
                for config in badge_configs:
                    if config['level'] not in existing_levels:
                        # 创建新勋章
                        badge = Badge(
                            name=f"{task.name} {config['level']}勋章",
                            description=f"连续完成{task.name}任务{config['days_required']}天，获得{config['points_reward']}积分奖励",
                            icon=config['icon'],
                            task_id=task.id,
                            days_required=config['days_required'],
                            level=config['level'],
                            points_reward=config['points_reward']
                        )
                        db.session.add(badge)
                        print(f"创建了 {task.name} 的 {config['level']}勋章")
                    else:
                        print(f"{task.name} 的 {config['level']}勋章已存在，跳过")
            
            # 提交所有更改
            db.session.commit()
            print("所有勋章初始化完成！")
            
        except Exception as e:
            print(f"初始化勋章时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    init_badges()