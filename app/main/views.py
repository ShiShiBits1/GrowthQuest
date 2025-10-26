from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Child, Task, Reward, TaskRecord, RewardRecord
from app.main import main

# 登录路由
@main.route('/login', methods=['GET', 'POST'])
def login():
    try:
        print('登录路由被访问')
        if current_user.is_authenticated:
            print('用户已认证，重定向到仪表盘')
            return redirect(url_for('main.dashboard'))
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            print(f'接收到登录请求，用户名: {username}')
            
            # 测试数据库连接
            print('尝试连接数据库...')
            users = User.query.all()
            print(f'数据库连接成功，发现 {len(users)} 个用户')
            
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                print('登录成功，重定向到仪表盘')
                return redirect(url_for('main.dashboard'))
            flash('用户名或密码错误')
            print('登录失败：用户名或密码错误')
        
        return render_template('login.html')
    except Exception as e:
        print(f'登录路由发生异常: {str(e)}')
        import traceback
        print(traceback.format_exc())
        return f'发生错误: {str(e)}', 500

# 登出路由
@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

# 仪表盘路由
@main.route('/')
@login_required
def dashboard():
    children = current_user.children.all()
    return render_template('dashboard.html', children=children)

# 孩子管理路由
@main.route('/children')
@login_required
def list_children():
    children = current_user.children.all()
    return render_template('children.html', children=children)

@main.route('/child/add', methods=['GET', 'POST'])
@login_required
def add_child():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form.get('age', type=int)
        child = Child(name=name, age=age, user_id=current_user.id)
        db.session.add(child)
        db.session.commit()
        flash('孩子添加成功')
        return redirect(url_for('main.list_children'))
    return render_template('add_child.html')

# 任务管理路由
@main.route('/tasks')
@login_required
def list_tasks():
    tasks = Task.query.all()
    return render_template('tasks.html', tasks=tasks)

@main.route('/task/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        points = request.form.get('points', type=int)
        task = Task(name=name, description=description, points=points)
        db.session.add(task)
        db.session.commit()
        flash('任务添加成功')
        return redirect(url_for('main.list_tasks'))
    return render_template('add_task.html')

# 奖励管理路由
@main.route('/rewards')
@login_required
def list_rewards():
    rewards = Reward.query.all()
    return render_template('rewards.html', rewards=rewards)

@main.route('/reward/add', methods=['GET', 'POST'])
@login_required
def add_reward():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        cost = request.form.get('cost', type=int)
        reward = Reward(name=name, description=description, cost=cost)
        db.session.add(reward)
        db.session.commit()
        flash('奖励添加成功')
        return redirect(url_for('main.list_rewards'))
    return render_template('add_reward.html')

# 孩子详情和积分管理
@main.route('/child/<int:child_id>')
@login_required
def child_detail(child_id):
    child = Child.query.get_or_404(child_id)
    # 确保是当前用户的孩子
    if child.parent != current_user:
        flash('无权访问')
        return redirect(url_for('main.dashboard'))
    task_records = child.task_records.order_by(TaskRecord.completed_at.desc()).all()
    reward_records = child.reward_records.order_by(RewardRecord.redeemed_at.desc()).all()
    # 查询可用的奖励（符合MVC模式，在视图层处理数据库查询）
    available_rewards = Reward.query.filter_by(is_active=True).filter(Reward.cost <= child.points).all()
    return render_template('child_detail.html', child=child, task_records=task_records, reward_records=reward_records, available_rewards=available_rewards)

# 任务记录确认
@main.route('/task_record/confirm/<int:record_id>')
@login_required
def confirm_task_record(record_id):
    record = TaskRecord.query.get_or_404(record_id)
    if record.child.parent != current_user:
        flash('无权操作')
        return redirect(url_for('main.dashboard'))
    if not record.is_confirmed:
        record.is_confirmed = True
        # 增加孩子积分
        record.child.points += record.task.points
        db.session.commit()
        flash('任务已确认，积分已发放')
    return redirect(url_for('main.child_detail', child_id=record.child.id))

# 奖励兑换
@main.route('/reward/redeem/<int:child_id>/<int:reward_id>')
@login_required
def redeem_reward(child_id, reward_id):
    child = Child.query.get_or_404(child_id)
    reward = Reward.query.get_or_404(reward_id)
    if child.parent != current_user:
        flash('无权操作')
        return redirect(url_for('main.dashboard'))
    if child.points >= reward.cost:
        # 创建兑换记录
        record = RewardRecord(child_id=child_id, reward_id=reward_id)
        # 扣除积分
        child.points -= reward.cost
        db.session.add(record)
        db.session.commit()
        flash('奖励兑换成功')
    else:
        flash('积分不足')
    return redirect(url_for('main.child_detail', child_id=child_id))