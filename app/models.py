from datetime import datetime, date, timedelta
from app import db, login_manager
from flask_login import UserMixin
from sqlalchemy import func, and_, extract

# 用户登录加载函数
@login_manager.user_loader
def load_user(user_id):
    # 格式: type_id:id，type_id 1表示家长，2表示孩子
    if ':' in user_id:
        type_id, actual_id = user_id.split(':', 1)
        if type_id == '2':  # 孩子用户
            return Child.query.get(int(actual_id))
        else:  # 家长用户
            return User.query.get(int(actual_id))
    # 处理纯数字ID（兼容旧格式）
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    """家长用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    # 关联到孩子
    children = db.relationship('Child', backref='parent', lazy='dynamic')

class Child(UserMixin, db.Model):
    """孩子模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    age = db.Column(db.Integer)
    points = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 登录相关字段
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    # 关联到任务记录和奖励记录
    task_records = db.relationship('TaskRecord', backref='child', lazy='dynamic')
    reward_records = db.relationship('RewardRecord', backref='child', lazy='dynamic')

class TaskCategory(db.Model):
    """任务分类模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)  # 分类名称
    description = db.Column(db.Text)  # 分类描述
    # 关联到任务
    tasks = db.relationship('Task', backref='task_category', lazy='dynamic')

class Task(db.Model):
    """任务模板模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    points = db.Column(db.Integer, nullable=False)  # 完成任务获得的积分
    category_id = db.Column(db.Integer, db.ForeignKey('task_category.id'), nullable=False)  # 外键关联到分类
    is_active = db.Column(db.Boolean, default=True)
    # 关联到任务记录
    records = db.relationship('TaskRecord', backref='task', lazy='dynamic')
    # 为了向后兼容，添加属性访问器
    @property
    def category(self):
        if self.task_category:
            return self.task_category.name
        return ''

class Reward(db.Model):
    """奖励模板模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    cost = db.Column(db.Integer, nullable=False)  # 兑换奖励所需的积分
    # 奖励等级：小奖励、中奖励、大奖励、特大奖励、终极大奖、许愿池
    level = db.Column(db.String(64), nullable=False, default='小奖励')
    is_active = db.Column(db.Boolean, default=True)
    # 关联到奖励记录
    records = db.relationship('RewardRecord', backref='reward', lazy='dynamic')

class TaskRecord(db.Model):
    """任务完成记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_confirmed = db.Column(db.Boolean, default=False)  # 家长确认

class RewardRecord(db.Model):
    """奖励兑换记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    reward_id = db.Column(db.Integer, db.ForeignKey('reward.id'), nullable=False)
    redeemed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_fulfilled = db.Column(db.Boolean, default=False)  # 家长兑现

class Badge(db.Model):
    """勋章模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)  # 勋章名称
    description = db.Column(db.Text)  # 勋章描述
    icon = db.Column(db.String(64), default='🌟')  # 勋章图标，默认使用emoji
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)  # 关联的任务
    task = db.relationship('Task', backref='badges', lazy='joined')  # 添加与Task的关联关系
    days_required = db.Column(db.Integer, default=30)  # 连续完成天数要求
    level = db.Column(db.String(32), nullable=False, default='初级')  # 勋章等级：初级、中级、高级、毕业
    points_reward = db.Column(db.Integer, default=10)  # 获得勋章奖励的积分
    # 关联到孩子获得的勋章
    child_badges = db.relationship('ChildBadge', backref='badge', lazy='dynamic')

class ChildBadge(db.Model):
    """孩子获得的勋章模型"""
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)  # 获得时间
    # 关联到孩子
    child = db.relationship('Child', backref=db.backref('badges', lazy='dynamic'))

# 添加统计方法到各个模型类
# 为Child模型添加数据分析方法
def add_analysis_methods(cls):
    # 获取指定时间段内完成的任务数量
    @classmethod
    def get_task_completion_by_period(cls, child_id, start_date=None, end_date=None):
        query = db.session.query(
            func.count(TaskRecord.id).label('task_count'),
            Task.category_id,
            TaskCategory.name.label('category_name')
        ).join(
            TaskRecord.task
        ).join(
            Task.task_category
        ).filter(
            TaskRecord.child_id == child_id,
            TaskRecord.is_confirmed == True
        )
        
        if start_date:
            query = query.filter(TaskRecord.completed_at >= start_date)
        if end_date:
            query = query.filter(TaskRecord.completed_at <= end_date)
            
        return query.group_by(Task.category_id, TaskCategory.name).all()
    
    # 获取积分获取趋势
    @classmethod
    def get_points_trend(cls, child_id, days=30):
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 按天分组统计获得的积分
        daily_points = db.session.query(
            func.date(TaskRecord.completed_at).label('date'),
            func.sum(Task.points).label('daily_points')
        ).join(
            TaskRecord.task
        ).filter(
            TaskRecord.child_id == child_id,
            TaskRecord.is_confirmed == True,
            TaskRecord.completed_at >= start_date
        ).group_by(func.date(TaskRecord.completed_at)).all()
        
        return daily_points
    
    # 获取任务连续完成统计
    @classmethod
    def get_streak_statistics(cls, child_id):
        # 获取所有任务的连续完成情况
        streaks = TaskStreak.query.filter_by(child_id=child_id).all()
        
        # 获取当前活跃的连续记录（当前streak>0）
        active_streaks = [s for s in streaks if s.current_streak > 0]
        
        # 获取最大的连续天数记录
        max_streak = max([s.longest_streak for s in streaks]) if streaks else 0
        
        return {
            'streaks': streaks,
            'active_streaks_count': len(active_streaks),
            'max_streak': max_streak
        }
    
    # 获取勋章获取统计
    @classmethod
    def get_badge_statistics(cls, child_id):
        # 获取已获得的勋章
        earned_badges = ChildBadge.query.filter_by(child_id=child_id).all()
        
        # 按等级统计勋章
        badges_by_level = db.session.query(
            Badge.level,
            func.count(ChildBadge.id).label('count')
        ).join(
            ChildBadge.badge
        ).filter(
            ChildBadge.child_id == child_id
        ).group_by(Badge.level).all()
        
        # 计算最近获得的勋章
        recent_badges = ChildBadge.query.filter_by(child_id=child_id).order_by(
            ChildBadge.earned_at.desc()
        ).limit(5).all()
        
        return {
            'total_badges': len(earned_badges),
            'badges_by_level': badges_by_level,
            'recent_badges': recent_badges
        }
    
    # 获取详细的勋章和成就分析
    @classmethod
    def get_detailed_badge_analysis(cls, child_id, days=30):
        """
        获取详细的勋章和成就分析数据
        
        Args:
            child_id: 孩子ID
            days: 统计时间范围（天）
            
        Returns:
            包含勋章分析数据的字典
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 获取所有勋章信息
        all_badges = Badge.query.all()
        earned_badges = ChildBadge.query.filter_by(child_id=child_id).all()
        earned_badge_ids = {badge.badge_id for badge in earned_badges}
        
        # 分类统计：已获得 vs 未获得
        earned_count = len(earned_badges)
        unearned_count = len(all_badges) - earned_count
        
        # 按等级统计勋章（替代badge_type，因为当前模型没有badge_type字段）
        badges_by_level_query = db.session.query(
            Badge.level,
            func.count(ChildBadge.id).label('earned_count'),
            func.count(Badge.id).label('total_count')
        ).outerjoin(
            ChildBadge, and_(
                Badge.id == ChildBadge.badge_id,
                ChildBadge.child_id == child_id
            )
        ).group_by(Badge.level).all()
        
        # 将Row对象转换为字典，使其可以JSON序列化
        badges_by_level = [
            {
                'level': row.level,
                'earned_count': row.earned_count,
                'total_count': row.total_count
            }
            for row in badges_by_level_query
        ]
        
        # 最近获得的勋章（时间范围内）
        recent_badges_query = ChildBadge.query.filter_by(child_id=child_id).filter(
            ChildBadge.earned_at >= start_date
        ).order_by(ChildBadge.earned_at.desc()).all()
        
        # 将ChildBadge对象转换为可序列化的字典
        recent_badges_in_period = [
            {
                'id': badge.id,
                'badge_id': badge.badge_id,
                'badge_name': badge.badge.name,
                'badge_level': badge.badge.level,
                'earned_at': badge.earned_at.isoformat()
            }
            for badge in recent_badges_query
        ]
        
        # 勋章获取趋势（按月统计） - 使用SQLite兼容的strftime函数
        badge_trend_query = db.session.query(
            func.strftime('%Y-%m', ChildBadge.earned_at).label('month'),
            func.count(ChildBadge.id).label('badge_count')
        ).filter(
            ChildBadge.child_id == child_id
        ).group_by(func.strftime('%Y-%m', ChildBadge.earned_at)).order_by('month').all()
        
        # 将Row对象转换为字典，使其可以JSON序列化
        badge_acquisition_trend = [
            {
                'month': row.month,
                'badge_count': row.badge_count
            }
            for row in badge_trend_query
        ]
        
        # 找出最接近获得的未获得勋章 - 基于任务完成情况的智能分析
        closest_badges = cls._find_closest_badges(child_id, all_badges, earned_badge_ids)
        
        # 格式化返回数据，确保数据结构清晰一致
        # 将closest_badges转换为可序列化的字典
        closest_badges_serializable = [
            {
                'id': badge.id,
                'name': badge.name,
                'task_id': badge.task_id,
                'task_name': badge.task.name if badge.task else '',
                'days_required': badge.days_required,
                'level': badge.level,
                'points_reward': badge.points_reward,
                'progress': getattr(badge, 'progress', 0),
                'current_streak': getattr(badge, 'current_streak', 0)
            }
            for badge in closest_badges[:5]  # 限制返回数量
        ]
        
        # 将all_badges转换为可序列化的字典
        all_badges_serializable = [
            {
                'id': badge.id,
                'name': badge.name,
                'task_id': badge.task_id,
                'task_name': badge.task.name if badge.task else '',
                'days_required': badge.days_required,
                'level': badge.level,
                'points_reward': badge.points_reward,
                'is_earned': badge.id in earned_badge_ids
            }
            for badge in all_badges
        ]
        
        # 将earned_badges转换为可序列化的字典
        earned_badges_serializable = [
            {
                'id': child_badge.id,
                'badge_id': child_badge.badge_id,
                'badge_name': child_badge.badge.name,
                'badge_level': child_badge.badge.level,
                'earned_at': child_badge.earned_at.isoformat()
            }
            for child_badge in earned_badges
        ]
        
        return {
            'earned_count': earned_count,
            'unearned_count': unearned_count,
            'completion_rate': (earned_count / len(all_badges) * 100) if all_badges else 0,
            'badges_by_level': badges_by_level,  # 重命名为更准确的字段名
            'recent_badges_in_period': recent_badges_in_period,
            'badge_acquisition_trend': badge_acquisition_trend,
            'closest_badges': closest_badges_serializable,
            'all_badges': all_badges_serializable,
            'earned_badges': earned_badges_serializable,
            'days_analyzed': days
        }
    
    @classmethod
    def _find_closest_badges(cls, child_id, all_badges, earned_badge_ids):
        """
        智能分析找出最接近获得条件的未获得勋章
        
        策略：
        1. 过滤出未获得的勋章
        2. 计算每个任务的当前连续完成天数
        3. 基于连续完成天数与勋章要求的比例进行排序
        
        Args:
            child_id: 孩子ID
            all_badges: 所有勋章列表
            earned_badge_ids: 已获得的勋章ID集合
            
        Returns:
            排序后的接近获得的勋章列表
        """
        unearned_badges = [badge for badge in all_badges if badge.id not in earned_badge_ids]
        
        # 计算每个任务的当前连续完成天数
        task_streaks = {}
        streaks = TaskStreak.query.filter_by(child_id=child_id).all()
        for streak in streaks:
            task_streaks[streak.task_id] = streak.current_streak
        
        # 对未获得勋章进行评分和排序
        badges_with_progress = []
        for badge in unearned_badges:
            # 获取该任务的连续完成天数（如果有）
            current_streak = task_streaks.get(badge.task_id, 0)
            # 计算完成进度比例
            progress_percentage = min(100, (current_streak / badge.days_required) * 100) if badge.days_required > 0 else 0
            
            # 添加进度信息到勋章对象
            badge.progress = progress_percentage
            badge.current_streak = current_streak
            badges_with_progress.append((badge, progress_percentage))
        
        # 按进度百分比降序排序
        badges_with_progress.sort(key=lambda x: x[1], reverse=True)
        
        # 返回排序后的勋章列表
        return [badge for badge, _ in badges_with_progress]
    
    # 获取任务完成率统计
    @classmethod
    def get_task_completion_rate(cls, child_id, days=7):
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 计算这段时间内所有活跃任务数量
        active_tasks_count = Task.query.filter_by(is_active=True).count()
        
        # 计算已完成的不同任务数量
        completed_tasks_count = db.session.query(
            func.count(func.distinct(TaskRecord.task_id))
        ).filter(
            TaskRecord.child_id == child_id,
            TaskRecord.is_confirmed == True,
            TaskRecord.completed_at >= start_date
        ).scalar() or 0
        
        # 计算完成率
        completion_rate = (completed_tasks_count / active_tasks_count * 100) if active_tasks_count > 0 else 0
        
        return {
            'completion_rate': completion_rate,
            'completed_tasks': completed_tasks_count,
            'total_active_tasks': active_tasks_count
        }
    
    # 获取任务分类分布
    @classmethod
    def get_task_category_distribution(cls, child_id, start_date, end_date=None):
        query = db.session.query(
            TaskCategory.name.label('category_name'),
            func.count(TaskRecord.id).label('count')
        ).join(
            TaskRecord.task
        ).join(
            Task.task_category
        ).filter(
            TaskRecord.child_id == child_id,
            TaskRecord.is_confirmed == True,
            TaskRecord.completed_at >= start_date
        )
        
        if end_date:
            query = query.filter(TaskRecord.completed_at <= end_date)
        
        distribution = query.group_by(TaskCategory.name).all()
        
        # 转换为字典列表格式
        result = []
        for category_name, count in distribution:
            result.append({
                'category_name': category_name,
                'count': count
            })
        
        return result
    
    # 获取分类完成统计
    @classmethod
    def get_category_completion_stats(cls, child_id, start_date, end_date=None):
        query = db.session.query(
            TaskCategory.name.label('category_name'),
            func.count(Task.id).label('total_tasks'),
            func.count(func.distinct(TaskRecord.task_id)).label('completed_tasks')
        ).join(
            Task.task_category
        ).outerjoin(
            TaskRecord, and_(
                Task.id == TaskRecord.task_id,
                TaskRecord.child_id == child_id,
                TaskRecord.is_confirmed == True,
                TaskRecord.completed_at >= start_date
            )
        ).filter(
            Task.is_active == True
        )
        
        if end_date:
            query = query.filter(TaskRecord.completed_at <= end_date)
        
        stats = query.group_by(TaskCategory.name).all()
        
        # 计算完成率并转换为字典列表格式
        result = []
        for category_name, total_tasks, completed_tasks in stats:
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            result.append({
                'category_name': category_name,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'completion_rate': completion_rate
            })
        
        return result
    
    # 获取习惯养成时间线
    @classmethod
    def get_habit_timeline(cls, child_id, days=30):
        start_date = date.today() - timedelta(days=days)
        
        # 查询指定时间范围内的任务完成记录，按日期分组
        daily_completions = db.session.query(
            func.date(TaskRecord.completed_at).label('date'),
            func.count(TaskRecord.id).label('completed_count'),
            func.count(func.distinct(Task.id)).label('unique_tasks')
        ).filter(
            TaskRecord.child_id == child_id,
            TaskRecord.is_confirmed == True,
            TaskRecord.completed_at >= start_date
        ).group_by(func.date(TaskRecord.completed_at)).all()
        
        # 构建完整的时间线，包括没有任务完成的日期
        timeline = []
        current_date = start_date
        while current_date <= date.today():
            completion_data = next((item for item in daily_completions if item.date == current_date), None)
            timeline.append({
                'date': current_date,
                'completed_count': completion_data.completed_count if completion_data else 0,
                'unique_tasks': completion_data.unique_tasks if completion_data else 0,
                'has_completions': completion_data is not None
            })
            current_date += timedelta(days=1)
        
        return timeline
    
    # 获取详细的连续完成天数统计
    @classmethod
    def get_detailed_streak_statistics(cls, child_id):
        # 获取所有任务的连续完成记录
        streaks = TaskStreak.query.filter_by(child_id=child_id).all()
        
        # 按状态分类
        active_streaks = []
        broken_streaks = []
        
        for streak in streaks:
            streak_data = {
                'task_id': streak.task_id,
                'task_name': streak.task.name,
                'current_streak': streak.current_streak,
                'longest_streak': streak.longest_streak,
                'last_completed_date': streak.last_completed_date,
                'status': 'active' if streak.is_active() else 'broken',
                'status_description': streak.get_status_description()
            }
            
            if streak.is_active():
                active_streaks.append(streak_data)
            elif streak.current_streak > 0:
                broken_streaks.append(streak_data)
        
        # 按当前连续天数降序排序
        active_streaks.sort(key=lambda x: x['current_streak'], reverse=True)
        broken_streaks.sort(key=lambda x: x['current_streak'], reverse=True)
        
        return {
            'active_streaks': active_streaks,
            'broken_streaks': broken_streaks,
            'total_streaks': len(streaks),
            'active_count': len(active_streaks),
            'broken_count': len(broken_streaks)
        }
    
    # 将方法添加到类
    cls.get_task_completion_by_period = get_task_completion_by_period
    cls.get_points_trend = get_points_trend
    cls.get_streak_statistics = get_streak_statistics
    cls.get_badge_statistics = get_badge_statistics
    cls.get_detailed_badge_analysis = get_detailed_badge_analysis
    cls._find_closest_badges = _find_closest_badges
    cls.get_task_completion_rate = get_task_completion_rate
    cls.get_task_category_distribution = get_task_category_distribution
    cls.get_category_completion_stats = get_category_completion_stats
    cls.get_habit_timeline = get_habit_timeline
    cls.get_detailed_streak_statistics = get_detailed_streak_statistics

# 为Child模型添加分析方法
add_analysis_methods(Child)

# 修改User和Child的get_id方法，以支持不同类型的用户
User.get_id = lambda self: f'1:{self.id}'
Child.get_id = lambda self: f'2:{self.id}'

class TaskStreak(db.Model):
    """任务连续完成记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    current_streak = db.Column(db.Integer, default=0)  # 当前连续天数
    last_completed_date = db.Column(db.Date)  # 最后完成日期
    longest_streak = db.Column(db.Integer, default=0)  # 最长连续天数记录
    
    # 关联任务
    task = db.relationship('Task', backref=db.backref('streaks', lazy='dynamic'))
    
    # 计算连续完成状态
    def is_active(self):
        """判断连续记录是否仍然活跃（昨天或今天有完成）"""
        if not self.last_completed_date:
            return False
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        return self.last_completed_date in [today, yesterday]
    
    # 获取友好的连续状态描述
    def get_status_description(self):
        if self.current_streak == 0:
            return "尚未开始连续挑战"
        elif self.is_active():
            return f"🔥 已连续完成 {self.current_streak} 天"
        else:
            today = date.today()
            days_lost = (today - self.last_completed_date).days
            return f"已中断 {days_lost} 天，最长记录 {self.longest_streak} 天"

# 将分析方法添加到Child类
add_analysis_methods(Child)