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

@main.route('/child/edit/<int:child_id>', methods=['GET', 'POST'])
@login_required
def edit_child(child_id):
    child = Child.query.get_or_404(child_id)
    # 确保是当前用户的孩子
    if child.parent != current_user:
        flash('无权操作')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        child.name = request.form['name']
        age = request.form.get('age')
        child.age = int(age) if age else None
        db.session.commit()
        flash('孩子信息更新成功')
        return redirect(url_for('main.child_detail', child_id=child.id))
    
    return render_template('edit_child.html', child=child)

@main.route('/child/delete/<int:child_id>')
@login_required
def delete_child(child_id):
    child = Child.query.get_or_404(child_id)
    # 确保是当前用户的孩子
    if child.parent != current_user:
        flash('无权操作')
        return redirect(url_for('main.dashboard'))
    
    # 删除孩子（级联删除会自动删除相关的任务记录和奖励记录）
    child_name = child.name
    db.session.delete(child)
    db.session.commit()
    flash(f'孩子 {child_name} 已成功删除')
    return redirect(url_for('main.list_children'))

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
        points = int(request.form['points'])
        category = request.form['category']
        task = Task(name=name, description=description, points=points, category=category, is_active=True)
        db.session.add(task)
        db.session.commit()
        flash('任务添加成功')
        return redirect(url_for('main.list_tasks'))
    return render_template('add_task.html')

@main.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        task.name = request.form['name']
        task.description = request.form.get('description', '')
        task.points = int(request.form['points'])
        task.category = request.form['category']
        task.is_active = 'is_active' in request.form
        db.session.commit()
        flash('任务更新成功')
        return redirect(url_for('main.list_tasks'))
    return render_template('edit_task.html', task=task)

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
        cost = int(request.form['cost'])
        level = request.form['level']
        reward = Reward(name=name, description=description, cost=cost, level=level, is_active=True)
        db.session.add(reward)
        db.session.commit()
        flash('奖励添加成功')
        return redirect(url_for('main.list_rewards'))
    return render_template('add_reward.html')

@main.route('/reward/edit/<int:reward_id>', methods=['GET', 'POST'])
@login_required
def edit_reward(reward_id):
    reward = Reward.query.get_or_404(reward_id)
    if request.method == 'POST':
        reward.name = request.form['name']
        reward.description = request.form.get('description', '')
        reward.cost = int(request.form['cost'])
        reward.level = request.form['level']
        reward.is_active = 'is_active' in request.form
        db.session.commit()
        flash('奖励更新成功')
        return redirect(url_for('main.list_rewards'))
    return render_template('edit_reward.html', reward=reward)

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
        from datetime import datetime
        record = RewardRecord(child_id=child_id, reward_id=reward_id, redeemed_at=datetime.now())
        # 扣除积分
        child.points -= reward.cost
        db.session.add(record)
        db.session.commit()
        flash('奖励兑换成功')
    else:
        flash('积分不足')
    return redirect(url_for('main.child_detail', child_id=child_id))

# 给孩子添加积分
@main.route('/add_points', methods=['GET', 'POST'])
@login_required
def add_points():
    # 获取当前用户的所有孩子
    children = current_user.children.all()
    # 获取所有激活的任务
    tasks = Task.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            child_id = request.form.get('child_id')
            task_id = request.form.get('task_id')
            date_str = request.form.get('date')
            
            # 验证表单数据
            if not child_id or not task_id or not date_str:
                flash('请填写所有必填字段')
                return redirect(url_for('main.add_points'))
            
            # 转换数据类型
            child_id = int(child_id)
            task_id = int(task_id)
            
            # 验证孩子是否属于当前用户
            child = Child.query.get_or_404(child_id)
            if child.parent != current_user:
                flash('无权操作')
                return redirect(url_for('main.dashboard'))
            
            # 获取任务信息
            task = Task.query.get_or_404(task_id)
            
            # 转换日期字符串为datetime对象
            from datetime import datetime
            completed_at = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 创建任务记录
            task_record = TaskRecord(
                child_id=child_id,
                task_id=task_id,
                completed_at=completed_at,
                is_confirmed=True  # 直接确认，立即发放积分
            )
            
            # 添加任务记录
            db.session.add(task_record)
            
            # 更新孩子积分
            child.points += task.points
            
            # 提交数据库更改
            db.session.commit()
            
            flash(f'已成功为{child.name}添加{task.points}积分！')
            return redirect(url_for('main.add_points'))
            
        except ValueError:
            flash('日期格式错误，请使用YYYY-MM-DD格式')
            return redirect(url_for('main.add_points'))
        except Exception as e:
            flash(f'添加积分时发生错误：{str(e)}')
            db.session.rollback()
            return redirect(url_for('main.add_points'))
    
    # 获取当前日期，用于默认值
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('add_points.html', children=children, tasks=tasks, today=today)

@main.route('/child/<int:child_id>/progress')
@login_required
def child_progress(child_id):
    child = Child.query.filter_by(id=child_id, user_id=current_user.id).first_or_404()
    
    # 获取最近的积分记录
    from datetime import datetime
    task_records = TaskRecord.query.filter_by(child_id=child_id, is_confirmed=True).order_by(TaskRecord.completed_at.desc()).limit(20).all()
    reward_records = RewardRecord.query.filter_by(child_id=child_id).order_by(RewardRecord.redeemed_at.desc()).limit(20).all()
    
    # 合并并排序记录
    all_records = []
    for record in task_records:
        all_records.append({
            'type': 'earned',
            'amount': record.task.points,
            'description': f'完成任务: {record.task.name}',
            'time': record.completed_at,
            'category': record.task.category
        })
    
    for record in reward_records:
        all_records.append({
            'type': 'spent',
            'amount': record.reward.cost,
            'description': f'兑换奖励: {record.reward.name}',
            'time': record.redeemed_at,
            'level': record.reward.level
        })
    
    # 按时间排序
    all_records.sort(key=lambda x: x['time'], reverse=True)
    
    # 按月汇总积分
    monthly_summary = {}
    for record in task_records:
        month_key = record.completed_at.strftime('%Y-%m')
        if month_key not in monthly_summary:
            monthly_summary[month_key] = {'earned': 0, 'spent': 0}
        monthly_summary[month_key]['earned'] += record.task.points
    
    for record in reward_records:
        month_key = record.redeemed_at.strftime('%Y-%m')
        if month_key not in monthly_summary:
            monthly_summary[month_key] = {'earned': 0, 'spent': 0}
        monthly_summary[month_key]['spent'] += record.reward.cost
    
    # 计算积分目标进度
    reward_goals = []
    available_rewards = Reward.query.filter_by(is_active=True).order_by(Reward.cost).all()
    for reward in available_rewards:
        reward_goals.append({
            'name': reward.name,
            'cost': reward.cost,
            'progress': min(100, (child.points / reward.cost) * 100) if reward.cost > 0 else 100,
            'level': reward.level
        })
    
    return render_template('child_progress.html', child=child, records=all_records, 
                          monthly_summary=monthly_summary, reward_goals=reward_goals)

# 删除孩子
@main.route('/child/delete/<int:child_id>', methods=['POST'])
@login_required
def delete_child(child_id):
    try:
        child = Child.query.get_or_404(child_id)
        # 确保是当前用户的孩子
        if child.parent != current_user:
            flash('无权操作')
            return redirect(url_for('main.list_children'))
        
        # 删除相关记录
        # 先删除任务记录
        TaskRecord.query.filter_by(child_id=child_id).delete()
        # 再删除奖励记录
        RewardRecord.query.filter_by(child_id=child_id).delete()
        # 最后删除孩子
        db.session.delete(child)
        db.session.commit()
        flash('孩子信息已删除')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}')
    
    return redirect(url_for('main.list_children'))