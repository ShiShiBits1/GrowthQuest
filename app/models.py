from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin

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