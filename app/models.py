from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin

# 用户登录加载函数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    """家长用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    # 关联到孩子
    children = db.relationship('Child', backref='parent', lazy='dynamic')

class Child(db.Model):
    """孩子模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    age = db.Column(db.Integer)
    points = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 关联到任务记录和奖励记录
    task_records = db.relationship('TaskRecord', backref='child', lazy='dynamic')
    reward_records = db.relationship('RewardRecord', backref='child', lazy='dynamic')

class Task(db.Model):
    """任务模板模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    points = db.Column(db.Integer, nullable=False)  # 完成任务获得的积分
    category = db.Column(db.String(64), nullable=False, default='学习任务')  # 任务分类：学习任务、生活习惯、品德行为
    is_active = db.Column(db.Boolean, default=True)
    # 关联到任务记录
    records = db.relationship('TaskRecord', backref='task', lazy='dynamic')

class Reward(db.Model):
    """奖励模板模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    cost = db.Column(db.Integer, nullable=False)  # 兑换奖励所需的积分
    level = db.Column(db.String(64), nullable=False, default='小奖励')  # 奖励等级：小奖励、中奖励、大奖励
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