from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Child, Task, Reward, TaskRecord, RewardRecord, Badge, ChildBadge, TaskStreak, TaskCategory, LearningCategory, LearningResource, LearningProgress
from datetime import datetime
from app.main import main

# 登录路由
@main.route('/login', methods=['GET', 'POST'])
def login():
    try:
        print('登录路由被访问')
        if current_user.is_authenticated:
            print('用户已认证，重定向到仪表盘')
            # 根据用户类型决定重定向目标
            if hasattr(current_user, 'children'):  # 家长用户
                return redirect(url_for('main.dashboard'))
            else:  # 孩子用户
                return redirect(url_for('main.child_dashboard'))
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            print(f'接收到登录请求，用户名: {username}')
            
            # 先尝试查找家长用户
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                print('家长登录成功，重定向到仪表盘')
                return redirect(url_for('main.dashboard'))
            
            # 再尝试查找孩子用户
            child = Child.query.filter_by(username=username).first()
            if child and check_password_hash(child.password, password):
                login_user(child)
                print('孩子登录成功，重定向到孩子仪表盘')
                return redirect(url_for('main.child_dashboard'))
            
            flash('用户名或密码错误')
            print('登录失败：用户名或密码错误')
        
        return render_template('login.html')
    except Exception as e:
        print(f'登录路由发生异常: {str(e)}')
        import traceback
        print(traceback.format_exc())
        return f'发生错误: {str(e)}', 500

# 修改密码路由
@main.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    try:
        if request.method == 'POST':
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            # 检查新旧密码是否相同
            if new_password == old_password:
                flash('新密码不能与原密码相同', 'error')
                return redirect(url_for('main.change_password'))
            
            # 检查两次输入的新密码是否一致
            if new_password != confirm_password:
                flash('两次输入的新密码不一致', 'error')
                return redirect(url_for('main.change_password'))
            
            # 检查原密码是否正确
            if not check_password_hash(current_user.password, old_password):
                flash('原密码错误', 'error')
                return redirect(url_for('main.change_password'))
            
            # 更新密码
            from werkzeug.security import generate_password_hash
            current_user.password = generate_password_hash(new_password)
            db.session.commit()
            
            flash('密码修改成功', 'success')
            
            # 根据用户类型重定向
            if hasattr(current_user, 'children'):  # 家长用户
                return redirect(url_for('main.dashboard'))
            else:  # 孩子用户
                return redirect(url_for('main.child_dashboard'))
        
        return render_template('change_password.html')
    except Exception as e:
        print(f'修改密码路由发生异常: {str(e)}')
        import traceback
        print(traceback.format_exc())
        flash('修改密码时发生错误', 'error')
        return redirect(url_for('main.change_password'))

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
    # 家长仪表盘
    if not hasattr(current_user, 'children'):  # 如果是孩子用户访问
        return redirect(url_for('main.child_dashboard'))
    # 仪表盘现在显示规则说明，不再需要传递children数据
    return render_template('dashboard.html')

# 孩子仪表盘路由
@main.route('/child_dashboard')
@login_required
def child_dashboard():
    # 确保是孩子用户
    if hasattr(current_user, 'children'):  # 如果是家长用户访问
        return redirect(url_for('main.dashboard'))
    
    # 获取当前孩子的任务记录和积分
    task_records = current_user.task_records.filter_by(is_confirmed=True).all()
    points = current_user.points
    
    # 获取可用奖励（孩子只能查看活跃的奖励）
    active_rewards = Reward.query.filter_by(is_active=True).all()
    
    # 获取孩子的勋章
    badges = current_user.badges.all()
    
    return render_template('child_dashboard.html', 
                           points=points, 
                           task_records=task_records,
                           active_rewards=active_rewards,
                           badges=badges)

# 孩子管理路由
@main.route('/children')
@login_required
def list_children():
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    children = current_user.children.all()
    return render_template('children.html', children=children)

@main.route('/child/add', methods=['GET', 'POST'])
@login_required
def add_child():
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        age = request.form.get('age', type=int)
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first() or Child.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('main.add_child'))
        
        child = Child(name=name, age=age, user_id=current_user.id, username=username, password=password)
        db.session.add(child)
        db.session.commit()
        flash('孩子添加成功')
        return redirect(url_for('main.list_children'))
    return render_template('add_child.html')

@main.route('/child/edit/<int:child_id>', methods=['GET', 'POST'])
@login_required
def edit_child(child_id):
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    child = Child.query.get_or_404(child_id)
    # 确保是当前用户的孩子
    if child.parent != current_user:
        flash('无权操作')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        child.name = request.form['name']
        age = request.form.get('age')
        child.age = int(age) if age else None
        
        # 可以选择是否更新密码
        if 'password' in request.form and request.form['password']:
            child.password = generate_password_hash(request.form['password'])
            
        # 如果更新用户名，需要检查唯一性
        if 'username' in request.form and request.form['username'] != child.username:
            new_username = request.form['username']
            if User.query.filter_by(username=new_username).first() or Child.query.filter_by(username=new_username).first():
                flash('用户名已存在')
                return redirect(url_for('main.edit_child', child_id=child.id))
            child.username = new_username
            
        db.session.commit()
        flash('孩子信息更新成功')
        return redirect(url_for('main.child_detail', child_id=child.id))
    
    return render_template('edit_child.html', child=child)
    



# 在线学习功能相关路由
@main.route('/learning')
@login_required
def learning_resources():
    """学习资源首页，展示所有分类"""
    categories = LearningCategory.query.all()
    # 如果是家长，可能需要选择孩子
    if hasattr(current_user, 'children'):
        children = current_user.children
        selected_child_id = request.args.get('child_id')
        selected_child = None
        if selected_child_id:
            selected_child = Child.query.get(int(selected_child_id))
        elif children:
            selected_child = children[0]  # 默认选择第一个孩子
        return render_template('learning/index.html', categories=categories, 
                              children=children, selected_child=selected_child)
    else:  # 孩子用户
        child = current_user
        return render_template('learning/index.html', categories=categories, child=child)


@main.route('/learning/category/<int:category_id>')
@login_required
def learning_category(category_id):
    """查看特定分类的学习资源"""
    category = LearningCategory.query.get_or_404(category_id)
    resources = LearningResource.query.filter_by(category_id=category_id, is_active=True).all()
    
    # 获取孩子信息
    child = None
    if hasattr(current_user, 'children'):  # 家长用户
        child_id = request.args.get('child_id')
        if child_id:
            child = Child.query.get_or_404(int(child_id))
    else:  # 孩子用户
        child = current_user
    
    # 获取孩子的学习进度信息
    progress_info = {}
    if child:
        progress_records = LearningProgress.query.filter_by(child_id=child.id).all()
        for record in progress_records:
            progress_info[record.resource_id] = {
                'progress': record.progress,
                'is_completed': record.is_completed,
                'last_accessed': record.last_accessed
            }
    
    return render_template('learning/category.html', category=category, 
                          resources=resources, child=child, progress_info=progress_info)


@main.route('/learning/resource/<int:resource_id>')
@login_required
def learning_resource_detail(resource_id):
    """学习资源详情页"""
    resource = LearningResource.query.get_or_404(resource_id)
    
    # 获取孩子信息
    child = None
    if hasattr(current_user, 'children'):  # 家长用户
        child_id = request.args.get('child_id')
        if child_id:
            child = Child.query.get_or_404(int(child_id))
    else:  # 孩子用户
        child = current_user
    
    # 获取或创建学习进度记录
    progress = None
    if child:
        progress = LearningProgress.query.filter_by(
            child_id=child.id,
            resource_id=resource_id
        ).first()
        
        if not progress and child == current_user:  # 孩子用户可以自动创建进度记录
            progress = LearningProgress(
                child_id=child.id,
                resource_id=resource_id
            )
            db.session.add(progress)
            db.session.commit()
    
    return render_template('learning/resource.html', resource=resource, 
                          child=child, progress=progress)


@main.route('/learning/progress/update', methods=['POST'])
@login_required
def update_learning_progress():
    """更新学习进度"""
    if not isinstance(current_user, Child):
        return {'success': False, 'message': '只有孩子用户可以更新学习进度'}
    
    try:
        resource_id = int(request.form.get('resource_id'))
        progress = float(request.form.get('progress', 0))
        last_watched_time = int(request.form.get('last_watched_time', 0))
        
        # 获取或创建进度记录
        record = LearningProgress.query.filter_by(
            child_id=current_user.id,
            resource_id=resource_id
        ).first()
        
        if not record:
            record = LearningProgress(
                child_id=current_user.id,
                resource_id=resource_id
            )
            db.session.add(record)
        
        # 更新进度信息
        record.progress = min(progress, 100.0)  # 限制进度最大为100%
        record.last_watched_time = last_watched_time
        record.last_accessed = datetime.utcnow()
        record.access_count += 1
        
        # 检查是否完成
        if record.progress >= 100 and not record.is_completed:
            record.is_completed = True
            # 可以在这里添加完成学习资源的积分奖励逻辑
            current_user.points += 10  # 例如完成一个学习资源奖励10积分
        
        db.session.commit()
        return {'success': True}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}


@main.route('/learning/stats/<int:child_id>')
@login_required
def learning_statistics(child_id):
    """查看孩子的学习统计信息"""
    child = Child.query.get_or_404(child_id)
    
    # 权限检查
    if hasattr(current_user, 'children') and child not in current_user.children:
        flash('无权访问此孩子的学习统计')
        return redirect(url_for('main.dashboard'))
    
    # 获取学习统计数据
    total_resources = LearningResource.query.filter_by(is_active=True).count()
    completed_resources = LearningProgress.query.filter_by(
        child_id=child_id,
        is_completed=True
    ).count()
    
    # 获取最近学习记录
    recent_progress = LearningProgress.query.filter_by(child_id=child_id).order_by(
        LearningProgress.last_accessed.desc()
    ).limit(5).all()
    
    # 获取学习时长统计（基于最后访问时间差）
    # 这里可以添加更复杂的学习时长计算逻辑
    
    return render_template('learning/stats.html', child=child,
                          total_resources=total_resources,
                          completed_resources=completed_resources,
                          recent_progress=recent_progress)

# 删除功能已移至POST方法实现，见文件底部

# 荣誉墙路由
@main.route('/honor_wall')
@login_required
def honor_wall():
    # 检查是否是家长用户
    if hasattr(current_user, 'children'):  # 家长用户
        # 获取当前用户的所有孩子
        children = current_user.children.all()
        children_with_badges = []
        
        for child in children:
            # 获取孩子获得的所有勋章
            badges = ChildBadge.query.filter_by(child_id=child.id).all()
            
            # 获取孩子的所有任务连续记录
            streaks = TaskStreak.query.filter_by(child_id=child.id).all()
            
            # 计算每个任务距离下一个勋章还需要的天数
            next_badges = {}
            for streak in streaks:
                # 查找该任务的勋章中，天数要求大于当前连续天数且最小的那个
                next_badge = Badge.query.filter(
                    Badge.task_id == streak.task_id,
                    Badge.days_required > streak.current_streak
                ).order_by(Badge.days_required.asc()).first()
                
                if next_badge:
                    next_badges[streak.task_id] = next_badge
            
            children_with_badges.append({
                'child': child,
                'badges': badges,
                'streaks': streaks,
                'next_badges': next_badges
            })
        
        return render_template('honor_wall.html', children_with_badges=children_with_badges, is_parent=True)
    else:  # 孩子用户
        # 只能查看自己的勋章
        badges = current_user.badges.all()
        
        # 获取自己的所有任务连续记录
        streaks = TaskStreak.query.filter_by(child_id=current_user.id).all()
        
        # 计算每个任务距离下一个勋章还需要的天数
        next_badges = {}
        for streak in streaks:
            # 查找该任务的勋章中，天数要求大于当前连续天数且最小的那个
            next_badge = Badge.query.filter(
                Badge.task_id == streak.task_id,
                Badge.days_required > streak.current_streak
            ).order_by(Badge.days_required.asc()).first()
            
            if next_badge:
                next_badges[streak.task_id] = next_badge
        
        # 创建兼容的结构
        children_with_badges = [{
            'child': current_user,
            'badges': badges,
            'streaks': streaks,
            'next_badges': next_badges
        }]
        
        return render_template('honor_wall.html', children_with_badges=children_with_badges, is_parent=False)

# 任务管理路由
@main.route('/tasks')
@login_required
def list_tasks():
    # 获取排序参数，默认为按名称升序排序
    sort_by = request.args.get('sort_by', 'name')
    sort_dir = request.args.get('sort_dir', 'asc')
    
    # 构建排序表达式
    if sort_by == 'points':
        if sort_dir == 'asc':
            tasks = Task.query.order_by(Task.points.asc()).all()
        else:
            tasks = Task.query.order_by(Task.points.desc()).all()
    elif sort_by == 'category':
        if sort_dir == 'asc':
            tasks = Task.query.order_by(Task.category.asc()).all()
        else:
            tasks = Task.query.order_by(Task.category.desc()).all()
    else:  # 默认按名称排序
        if sort_dir == 'asc':
            tasks = Task.query.order_by(Task.name.asc()).all()
        else:
            tasks = Task.query.order_by(Task.name.desc()).all()
    
    # 检查是否是家长用户
    is_parent = hasattr(current_user, 'children')
    
    # 将当前排序信息和用户类型传递给模板
    return render_template('tasks.html', tasks=tasks, current_sort=sort_by, current_dir=sort_dir, is_parent=is_parent)

@main.route('/task/add', methods=['GET', 'POST'])
@login_required
def add_task():
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    # 获取所有任务分类
    categories = TaskCategory.query.all()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        points = int(request.form['points'])
        category_id = int(request.form['category_id'])
        task = Task(name=name, description=description, points=points, category_id=category_id, is_active=True)
        db.session.add(task)
        db.session.commit()
        # 为新任务创建默认的30天勋章
        badge = Badge(
            name=f'{name}连续达人',
            description=f'连续完成{name}30天',
            icon='🏆',
            task_id=task.id,
            days_required=30
        )
        db.session.add(badge)
        db.session.commit()
        flash('任务添加成功')
        return redirect(url_for('main.list_tasks'))
    return render_template('add_task.html', categories=categories)

@main.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    task = Task.query.get_or_404(task_id)
    # 获取所有任务分类
    categories = TaskCategory.query.all()
    
    if request.method == 'POST':
        task.name = request.form['name']
        task.description = request.form.get('description', '')
        task.points = int(request.form['points'])
        task.category_id = int(request.form['category_id'])
        task.is_active = 'is_active' in request.form
        db.session.commit()
        flash('任务更新成功')
        return redirect(url_for('main.list_tasks'))
    return render_template('edit_task.html', task=task, categories=categories)

@main.route('/task/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    try:
        task = Task.query.get_or_404(task_id)
        
        # 检查是否有任务记录使用该任务
        task_record_count = TaskRecord.query.filter_by(task_id=task_id).count()
        if task_record_count > 0:
            flash(f'无法删除该任务，因为有{task_record_count}条任务记录正在使用它')
            return redirect(url_for('main.edit_task', task_id=task_id))
        
        # 检查是否有徽章关联到该任务
        badge_count = Badge.query.filter_by(task_id=task_id).count()
        if badge_count > 0:
            flash(f'无法删除该任务，因为有{badge_count}个徽章关联到它。请先删除相关徽章。')
            return redirect(url_for('main.edit_task', task_id=task_id))
        
        # 删除任务
        db.session.delete(task)
        db.session.commit()
        flash('任务删除成功')
    except Exception as e:
        db.session.rollback()
        flash(f'删除任务失败: {str(e)}')
    
    return redirect(url_for('main.list_tasks'))



# 徽章管理路由
@main.route('/badges')
@login_required
def list_badges():
    badges = Badge.query.join(Task).all()
    # 检查是否是家长用户
    is_parent = hasattr(current_user, 'children')
    return render_template('badges.html', badges=badges, is_parent=is_parent)

@main.route('/badge/add', methods=['GET', 'POST'])
@login_required
def add_badge():
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    # 获取所有任务供选择
    tasks = Task.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            description = request.form.get('description', '')
            icon = request.form.get('icon', '🏆')
            
            # 安全地获取并转换整数字段
            task_id = int(request.form['task_id'])
            
            completions_required = request.form.get('completions_required', '0')
            completions_required = int(completions_required) if completions_required else 0
            
            days_required = request.form.get('days_required', '0')
            days_required = int(days_required) if days_required else 0
            
            level = request.form.get('level', '初级')
            
            points_reward = request.form.get('points_reward', '10')
            points_reward = int(points_reward) if points_reward else 10
            
            # 创建新徽章
            badge = Badge(
                name=name,
                description=description,
                icon=icon,
                task_id=task_id,
                completions_required=completions_required,
                days_required=days_required,
                level=level,
                points_reward=points_reward
            )
            db.session.add(badge)
            db.session.commit()
            flash('徽章添加成功')
            return redirect(url_for('main.list_badges'))
        except ValueError as e:
            flash(f'数据格式错误，请确保所有数字字段输入正确: {str(e)}')
            return redirect(url_for('main.add_badge'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加徽章时发生错误: {str(e)}')
            return redirect(url_for('main.add_badge'))
    
    return render_template('add_badge.html', tasks=tasks)

@main.route('/badge/edit/<int:badge_id>', methods=['GET', 'POST'])
@login_required
def edit_badge(badge_id):
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    badge = Badge.query.get_or_404(badge_id)
    # 获取所有任务供选择
    tasks = Task.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        try:
            badge.name = request.form['name']
            badge.description = request.form.get('description', '')
            badge.icon = request.form.get('icon', '🏆')
            badge.task_id = int(request.form['task_id'])
            
            # 安全地获取并转换整数字段
            completions_required = request.form.get('completions_required', '0')
            badge.completions_required = int(completions_required) if completions_required else 0
            
            days_required = request.form.get('days_required', '0')
            badge.days_required = int(days_required) if days_required else 0
            
            badge.level = request.form.get('level', '初级')
            
            points_reward = request.form.get('points_reward', '10')
            badge.points_reward = int(points_reward) if points_reward else 10
            
            db.session.commit()
            flash('徽章更新成功')
            return redirect(url_for('main.list_badges'))
        except ValueError as e:
            flash(f'数据格式错误，请确保所有数字字段输入正确: {str(e)}')
            return redirect(url_for('main.edit_badge', badge_id=badge_id))
        except Exception as e:
            db.session.rollback()
            flash(f'更新徽章时发生错误: {str(e)}')
            return redirect(url_for('main.edit_badge', badge_id=badge_id))
    
    return render_template('edit_badge.html', badge=badge, tasks=tasks)

@main.route('/badge/delete/<int:badge_id>', methods=['POST'])
@login_required
def delete_badge(badge_id):
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    try:
        badge = Badge.query.get_or_404(badge_id)
        
        # 检查是否有孩子已获得此徽章
        child_badge_count = ChildBadge.query.filter_by(badge_id=badge_id).count()
        if child_badge_count > 0:
            flash(f'无法删除该徽章，因为有{child_badge_count}个孩子已获得它')
            return redirect(url_for('main.edit_badge', badge_id=badge_id))
        
        # 删除徽章
        db.session.delete(badge)
        db.session.commit()
        flash('徽章删除成功')
    except Exception as e:
        db.session.rollback()
        flash(f'删除徽章失败: {str(e)}')
    
    return redirect(url_for('main.list_badges'))

# 奖励管理路由
@main.route('/rewards')
@login_required
def list_rewards():
    rewards = Reward.query.all()
    # 检查是否是家长用户
    is_parent = hasattr(current_user, 'children')
    return render_template('rewards.html', rewards=rewards, is_parent=is_parent)

@main.route('/reward/add', methods=['GET', 'POST'])
@login_required
def add_reward():
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
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
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
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
    from datetime import datetime, date, timedelta
    
    record = TaskRecord.query.get_or_404(record_id)
    if record.child.parent != current_user:
        flash('无权操作')
        return redirect(url_for('main.dashboard'))
    
    if not record.is_confirmed:
        record.is_confirmed = True
        # 增加孩子积分
        record.child.points += record.task.points
        
        # 计算连续完成天数
        task_date = record.completed_at.date()
        
        # 获取或创建TaskStreak记录
        streak = TaskStreak.query.filter_by(child_id=record.child_id, task_id=record.task_id).first()
        
        if not streak:
            # 创建新的连续记录，确保初始化为1天
            streak = TaskStreak(
                child_id=record.child_id,
                task_id=record.task_id,
                current_streak=1,
                last_completed_date=task_date,
                longest_streak=1
            )
            db.session.add(streak)
            # 确保任务有对应的勋章
            existing_badge = Badge.query.filter_by(task_id=record.task_id).first()
            if not existing_badge:
                # 为该任务创建默认勋章
                badge = Badge(
                    name=f"{record.task.name}坚持达人",
                    description=f"连续30天完成{record.task.name}任务，获得此勋章！",
                    icon="🏆",
                    task_id=record.task_id,
                    days_required=30,
                    level="初级",
                    points_reward=10
                )
                db.session.add(badge)
                flash(f"系统已为任务 '{record.task.name}' 自动创建了勋章！")
        else:
            # 计算与上一次完成的日期差
            if streak.last_completed_date:
                days_diff = (task_date - streak.last_completed_date).days
                
                if days_diff == 1 or (days_diff == 0 and task_date == date.today()):
                    # 连续完成，增加连续天数
                    streak.current_streak += 1
                elif days_diff > 1:
                    # 中断了，重置连续天数
                    streak.current_streak = 1
                # 如果是同一天，不改变连续天数（避免重复计数）
            else:
                streak.current_streak = 1
            
            streak.last_completed_date = task_date
            # 更新最长连续天数
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
            
            # 检查并颁发勋章
            # 获取该任务的所有勋章（按要求从低到高排序）
            badges = Badge.query.filter_by(task_id=record.task_id).all()
            
            # 记录是否有新勋章被颁发
            new_badge_earned = False
            
            for badge in badges:
                # 检查是否已经获得该勋章
                existing_badge = ChildBadge.query.filter_by(child_id=record.child_id, badge_id=badge.id).first()
                
                # 判断是基于完成次数还是连续天数
                if badge.completions_required > 0:
                    # 基于完成次数的勋章
                    # 计算该任务的完成次数
                    completion_count = db.session.query(func.count(TaskRecord.id)).filter(
                        TaskRecord.child_id == record.child_id,
                        TaskRecord.task_id == record.task_id,
                        TaskRecord.is_confirmed == True
                    ).scalar()
                    
                    # 如果未获得该勋章，且完成次数达到要求
                    if not existing_badge and completion_count >= badge.completions_required:
                        # 创建勋章记录
                        child_badge = ChildBadge(child_id=record.child_id, badge_id=badge.id)
                        db.session.add(child_badge)
                        
                        # 给予积分奖励
                        record.child.points += badge.points_reward
                        flash(f"🎉 {record.child.name} 获得了「{badge.name}」勋章！额外奖励 {badge.points_reward} 积分！")
                        new_badge_earned = True
                else:
                    # 基于连续天数的勋章
                    # 如果未获得该勋章，且连续天数达到要求
                    if not existing_badge and streak.current_streak >= badge.days_required:
                        # 创建勋章记录
                        child_badge = ChildBadge(child_id=record.child_id, badge_id=badge.id)
                        db.session.add(child_badge)
                        
                        # 给予积分奖励
                        record.child.points += badge.points_reward
                        flash(f"🎉 {record.child.name} 获得了「{badge.name}」勋章！额外奖励 {badge.points_reward} 积分！")
                        new_badge_earned = True
            
            # 如果没有新勋章被颁发但连续天数有更新，也显示进度更新信息
            if not new_badge_earned and streak.current_streak > 0:
                # 查找该任务的下一个勋章
                next_badge = Badge.query.filter(
                    Badge.task_id == record.task_id,
                    Badge.days_required > streak.current_streak
                ).order_by(Badge.days_required).first()
                
                if next_badge:
                    days_remaining = next_badge.days_required - streak.current_streak
                    flash(f"🔥 {record.child.name} 已连续完成 {record.task.name} {streak.current_streak} 天，距离获得「{next_badge.name}」勋章还需 {days_remaining} 天！")
                else:
                    flash(f"🎉 {record.child.name} 已连续完成 {record.task.name} {streak.current_streak} 天，已达到最高连续记录！")
        
        db.session.commit()
        flash('任务已确认，积分已发放')
    
    return redirect(url_for('main.child_detail', child_id=record.child.id))

# 编辑任务记录
@main.route('/task_record/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_task_record(record_id):
    record = TaskRecord.query.get_or_404(record_id)
    # 确保是当前用户的孩子的记录
    if record.child.parent != current_user:
        flash('无权操作')
        return redirect(url_for('main.dashboard'))
    
    # 获取所有激活的任务供选择
    tasks = Task.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            task_id = int(request.form['task_id'])
            date_str = request.form['date']
            
            # 转换日期字符串为datetime对象
            from datetime import datetime, date
            completed_at = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            task_date = completed_at.date()
            
            # 获取新任务信息
            new_task = Task.query.get_or_404(task_id)
            
            # 保存原任务ID用于后续处理
            old_task_id = record.task_id
            
            # 如果记录已确认，需要调整积分
            if record.is_confirmed:
                # 先减去原任务的积分
                record.child.points -= record.task.points
                # 再加上新任务的积分
                record.child.points += new_task.points
            
            # 更新记录信息
            record.task_id = task_id
            record.completed_at = completed_at
            
            # 如果记录已确认且修改了任务或日期，需要重新计算连续天数和勋章
            if record.is_confirmed:
                # 如果修改了任务类型，需要处理旧任务的连续记录
                if old_task_id != task_id:
                    # 对于原任务，需要重新计算连续记录
                    old_streak = TaskStreak.query.filter_by(child_id=record.child_id, task_id=old_task_id).first()
                    if old_streak:
                        # 重新计算原任务的连续天数（这里简化处理，实际可能需要重新计算所有记录）
                        # 获取该任务的所有已确认记录
                        old_records = TaskRecord.query.filter_by(
                            child_id=record.child_id,
                            task_id=old_task_id,
                            is_confirmed=True
                        ).order_by(TaskRecord.completed_at.desc()).all()
                        
                        if old_records:
                            # 重新计算连续天数逻辑（简化版）
                            last_date = old_records[0].completed_at.date()
                            current_streak = 1
                            
                            for r in old_records[1:]:
                                r_date = r.completed_at.date()
                                if (last_date - r_date).days == 1:
                                    current_streak += 1
                                    last_date = r_date
                                else:
                                    break
                            
                            old_streak.current_streak = current_streak
                            old_streak.last_completed_date = old_records[0].completed_at.date()
                    
                # 对于新任务，获取或创建连续记录
                streak = TaskStreak.query.filter_by(child_id=record.child_id, task_id=task_id).first()
                
                if not streak:
                    # 创建新的连续记录
                    streak = TaskStreak(
                        child_id=record.child_id,
                        task_id=task_id,
                        current_streak=1,
                        last_completed_date=task_date,
                        longest_streak=1
                    )
                    db.session.add(streak)
                    
                    # 确保任务有对应的勋章
                    existing_badge = Badge.query.filter_by(task_id=task_id).first()
                    if not existing_badge:
                        # 为该任务创建默认勋章
                        badge = Badge(
                            name=f"{new_task.name}坚持达人",
                            description=f"连续30天完成{new_task.name}任务，获得此勋章！",
                            icon="🏆",
                            task_id=task_id,
                            days_required=30,
                            level="初级",
                            points_reward=10
                        )
                        db.session.add(badge)
                else:
                    # 重新计算连续天数（基于所有已确认的记录）
                    # 获取该任务的所有已确认记录
                    all_records = TaskRecord.query.filter_by(
                        child_id=record.child_id,
                        task_id=task_id,
                        is_confirmed=True
                    ).order_by(TaskRecord.completed_at.desc()).all()
                    
                    if all_records:
                        # 重新计算连续天数
                        last_date = all_records[0].completed_at.date()
                        current_streak = 1
                        
                        for r in all_records[1:]:
                            r_date = r.completed_at.date()
                            if (last_date - r_date).days == 1:
                                current_streak += 1
                                last_date = r_date
                            else:
                                break
                        
                        streak.current_streak = current_streak
                        streak.last_completed_date = all_records[0].completed_at.date()
                        
                        # 更新最长连续天数
                        if current_streak > streak.longest_streak:
                            streak.longest_streak = current_streak
                    
                    # 检查并颁发勋章
                    badges = Badge.query.filter_by(task_id=task_id).all()
                    new_badge_earned = False
                    
                    for badge in badges:
                        # 检查是否已经获得该勋章
                        existing_badge = ChildBadge.query.filter_by(child_id=record.child_id, badge_id=badge.id).first()
                        
                        # 判断是基于完成次数还是连续天数
                        if badge.completions_required > 0:
                            # 基于完成次数的勋章
                            # 计算该任务的完成次数
                            completion_count = db.session.query(func.count(TaskRecord.id)).filter(
                                TaskRecord.child_id == record.child_id,
                                TaskRecord.task_id == task_id,
                                TaskRecord.is_confirmed == True
                            ).scalar()
                            
                            # 如果未获得该勋章，且完成次数达到要求
                            if not existing_badge and completion_count >= badge.completions_required:
                                # 创建勋章记录
                                child_badge = ChildBadge(child_id=record.child_id, badge_id=badge.id)
                                db.session.add(child_badge)
                                
                                # 给予积分奖励
                                record.child.points += badge.points_reward
                                flash(f"🎉 {record.child.name} 获得了「{badge.name}」勋章！额外奖励 {badge.points_reward} 积分！")
                                new_badge_earned = True
                        else:
                            # 基于连续天数的勋章
                            # 如果未获得该勋章，且连续天数达到要求
                            if not existing_badge and streak.current_streak >= badge.days_required:
                                # 创建勋章记录
                                child_badge = ChildBadge(child_id=record.child_id, badge_id=badge.id)
                                db.session.add(child_badge)
                                
                                # 给予积分奖励
                                record.child.points += badge.points_reward
                                flash(f"🎉 {record.child.name} 获得了「{badge.name}」勋章！额外奖励 {badge.points_reward} 积分！")
                                new_badge_earned = True
            
            db.session.commit()
            flash('任务记录更新成功')
            return redirect(url_for('main.child_detail', child_id=record.child.id))
            
        except ValueError:
            flash('日期格式错误，请使用YYYY-MM-DD格式')
        except Exception as e:
            flash(f'更新任务记录时发生错误：{str(e)}')
            db.session.rollback()
    
    # 准备默认日期时间
    from datetime import datetime
    default_date = record.completed_at.strftime('%Y-%m-%dT%H:%M')
    
    return render_template('edit_task_record.html', record=record, tasks=tasks, default_date=default_date)

# 删除任务记录
@main.route('/task_record/delete/<int:record_id>', methods=['POST'])
@login_required
def delete_task_record(record_id):
    try:
        record = TaskRecord.query.get_or_404(record_id)
        # 确保是当前用户的孩子的记录
        if record.child.parent != current_user:
            flash('无权操作')
            return redirect(url_for('main.dashboard'))
        
        # 如果记录已确认，需要扣除积分
        if record.is_confirmed:
            record.child.points -= record.task.points
        
        # 保存孩子ID用于重定向
        child_id = record.child.id
        
        # 删除记录
        db.session.delete(record)
        db.session.commit()
        flash('任务记录已删除')
        
    except Exception as e:
        db.session.rollback()
        flash(f'删除任务记录失败: {str(e)}')
        # 如果出错，尝试获取孩子ID
        try:
            child_id = record.child.id
        except:
            child_id = None
    
    # 重定向回孩子详情页
    if child_id:
        return redirect(url_for('main.child_detail', child_id=child_id))
    else:
        return redirect(url_for('main.dashboard'))



# 给孩子添加积分
@main.route('/add_points', methods=['GET', 'POST'])
@login_required
def add_points():
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
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
            completed_at = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            task_date = completed_at.date()
            
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
            
            # 更新连续天数和检查勋章
            # 查找该任务的连续记录
            streak = TaskStreak.query.filter_by(child_id=child_id, task_id=task_id).first()
            
            if not streak:
                # 创建新的连续记录
                streak = TaskStreak(
                    child_id=child_id,
                    task_id=task_id,
                    current_streak=1,
                    last_completed_date=task_date,
                    longest_streak=1
                )
                db.session.add(streak)
                
                # 检查是否需要为该任务创建默认勋章
                existing_badges = Badge.query.filter_by(task_id=task_id).all()
                if not existing_badges:
                    # 创建默认的30天勋章
                    badge = Badge(
                        name=f'{task.name}连续达人',
                        description=f'连续完成{task.name}30天',
                        icon='🏆',
                        task_id=task_id,
                        days_required=30,
                        level="初级",
                        points_reward=10
                    )
                    db.session.add(badge)
                    flash(f"系统已为任务 '{task.name}' 自动创建了勋章！")
            else:
                # 计算与上一次完成的日期差
                if streak.last_completed_date:
                    days_diff = (task_date - streak.last_completed_date).days
                    
                    if days_diff == 1 or (days_diff == 0 and task_date == date.today()):
                        # 连续完成，增加连续天数
                        streak.current_streak += 1
                    elif days_diff > 1:
                        # 中断了，重置连续天数
                        streak.current_streak = 1
                    # 如果是同一天，不改变连续天数（避免重复计数）
                else:
                    streak.current_streak = 1
                
                streak.last_completed_date = task_date
                # 更新最长连续天数
                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak
                
                # 检查并颁发勋章
                # 获取该任务的所有勋章
                badges = Badge.query.filter_by(task_id=task_id).all()
                
                # 记录是否有新勋章被颁发
                new_badge_earned = False
                
                for badge in badges:
                    # 检查是否已经获得该勋章
                    existing_badge = ChildBadge.query.filter_by(child_id=child_id, badge_id=badge.id).first()
                    
                    # 判断是基于完成次数还是连续天数
                    if badge.completions_required > 0:
                        # 基于完成次数的勋章
                        # 计算该任务的完成次数
                        completion_count = db.session.query(func.count(TaskRecord.id)).filter(
                            TaskRecord.child_id == child_id,
                            TaskRecord.task_id == task_id,
                            TaskRecord.is_confirmed == True
                        ).scalar()
                        
                        # 如果未获得该勋章，且完成次数达到要求
                        if not existing_badge and completion_count >= badge.completions_required:
                            # 创建勋章记录
                            child_badge = ChildBadge(child_id=child_id, badge_id=badge.id)
                            db.session.add(child_badge)
                            
                            # 给予积分奖励
                            child.points += badge.points_reward
                            flash(f"🎉 {child.name} 获得了「{badge.name}」勋章！额外奖励 {badge.points_reward} 积分！")
                            new_badge_earned = True
                    else:
                        # 基于连续天数的勋章
                        # 如果未获得该勋章，且连续天数达到要求
                        if not existing_badge and streak.current_streak >= badge.days_required:
                            # 创建勋章记录
                            child_badge = ChildBadge(child_id=child_id, badge_id=badge.id)
                            db.session.add(child_badge)
                            
                            # 给予积分奖励
                            child.points += badge.points_reward
                            flash(f"🎉 {child.name} 获得了「{badge.name}」勋章！额外奖励 {badge.points_reward} 积分！")
                            new_badge_earned = True
                
                # 如果没有新勋章被颁发但连续天数有更新，也显示进度更新信息
                if not new_badge_earned and streak.current_streak > 0:
                    # 查找该任务的下一个勋章
                    next_badge = Badge.query.filter(
                        Badge.task_id == task_id,
                        Badge.days_required > streak.current_streak
                    ).order_by(Badge.days_required).first()
                    
                    if next_badge:
                        days_remaining = next_badge.days_required - streak.current_streak
                        flash(f"🔥 {child.name} 已连续完成 {task.name} {streak.current_streak} 天，距离获得「{next_badge.name}」勋章还需 {days_remaining} 天！")
                    else:
                        flash(f"🎉 {child.name} 已连续完成 {task.name} {streak.current_streak} 天，已达到最高连续记录！")
            
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
    
    # 获取当前日期时间，用于默认值
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
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
# 任务分类管理路由
@main.route('/task_categories')
@login_required
def manage_task_categories():
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    categories = TaskCategory.query.all()
    return render_template('manage_task_categories.html', categories=categories)

@main.route('/task_category/add', methods=['GET', 'POST'])
@login_required
def add_task_category():
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        
        # 检查分类名称是否已存在
        existing = TaskCategory.query.filter_by(name=name).first()
        if existing:
            flash('该分类名称已存在')
            return redirect(url_for('main.add_task_category'))
        
        category = TaskCategory(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash('分类添加成功')
        return redirect(url_for('main.manage_task_categories'))
    
    return render_template('add_task_category.html')

@main.route('/task_category/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_task_category(category_id):
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    category = TaskCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        
        # 检查分类名称是否已存在（排除当前分类）
        existing = TaskCategory.query.filter(TaskCategory.name == name, TaskCategory.id != category_id).first()
        if existing:
            flash('该分类名称已存在')
            return redirect(url_for('main.edit_task_category', category_id=category_id))
        
        category.name = name
        category.description = description
        db.session.commit()
        flash('分类更新成功')
        return redirect(url_for('main.manage_task_categories'))
    
    return render_template('edit_task_category.html', category=category)

@main.route('/task_category/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_task_category(category_id):
    # 只有家长用户可以访问
    if not hasattr(current_user, 'children'):
        flash('权限不足')
        return redirect(url_for('main.child_dashboard'))
    
    category = TaskCategory.query.get_or_404(category_id)
    
    # 检查是否有任务使用该分类
    task_count = Task.query.filter_by(category_id=category_id).count()
    if task_count > 0:
        flash(f'无法删除该分类，因为有{task_count}个任务正在使用它')
        return redirect(url_for('main.manage_task_categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('分类删除成功')
    return redirect(url_for('main.manage_task_categories'))

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

# 积分商城
@main.route('/mall')
@login_required
def mall():
    # 获取所有激活的奖励（用于积分商城展示）
    available_rewards = Reward.query.filter_by(is_active=True).all()
    
    # 检查是否是家长用户
    if hasattr(current_user, 'children'):  # 家长用户
        # 获取当前用户的所有孩子
        children = current_user.children.all()
        
        # 为每个奖励计算每个孩子的可兑换数量
        rewards_with_availability = []
        for reward in available_rewards:
            child_availability = []
            for child in children:
                # 计算孩子可以兑换该奖励的数量
                can_redeem_count = child.points // reward.cost if reward.cost > 0 else 0
                child_availability.append({
                    'child': child,
                    'can_redeem_count': can_redeem_count,
                    'has_enough_points': can_redeem_count > 0
                })
            
            rewards_with_availability.append({
                'reward': reward,
                'children_availability': child_availability
            })
        
        return render_template('mall.html', 
                              children=children, 
                              rewards_with_availability=rewards_with_availability,
                              is_parent=True)
    else:  # 孩子用户
        # 只能查看自己的兑换情况
        rewards_with_availability = []
        for reward in available_rewards:
            # 计算自己可以兑换该奖励的数量
            can_redeem_count = current_user.points // reward.cost if reward.cost > 0 else 0
            # 直接检查积分是否足够，而不仅仅依赖于can_redeem_count
            has_enough_points = current_user.points >= reward.cost if reward.cost > 0 else True
            rewards_with_availability.append({
                'reward': reward,
                'can_redeem_count': can_redeem_count,
                'has_enough_points': has_enough_points
            })
        
        return render_template('mall.html', 
                              rewards_with_availability=rewards_with_availability,
                              is_parent=False)

# 修改奖励兑换函数，让孩子用户可以为自己兑换
@main.route('/reward/redeem/<int:child_id>/<int:reward_id>')
@login_required
def redeem_reward(child_id, reward_id):
    try:
        child = Child.query.get_or_404(child_id)
        reward = Reward.query.get_or_404(reward_id)
        
        # 权限检查：1. 家长可以为自己的孩子兑换；2. 孩子只能为自己兑换
        if not (hasattr(current_user, 'children') and child.parent == current_user) and current_user.id != child_id:
            flash('无权操作')
            return redirect(url_for('main.dashboard' if hasattr(current_user, 'children') else 'main.child_dashboard'))
        
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
    except Exception as e:
        db.session.rollback()
        flash(f'兑换过程中发生错误: {str(e)}')
        import logging
        logging.error(f'奖励兑换失败: {str(e)}')
    
    # 根据用户类型重定向
    if hasattr(current_user, 'children'):  # 家长用户
        return redirect(url_for('main.child_detail', child_id=child_id))
    else:  # 孩子用户
        return redirect(url_for('main.child_dashboard'))

# 兑现奖励功能
@main.route('/reward/fulfill/<int:record_id>', methods=['POST'])
@login_required
def fulfill_reward(record_id):
    try:
        # 获取奖励记录
        record = RewardRecord.query.get_or_404(record_id)
        child = Child.query.get_or_404(record.child_id)
        
        # 权限检查：只有家长可以兑现奖励
        if not (hasattr(current_user, 'children') and child.parent == current_user):
            flash('无权操作')
            return redirect(url_for('main.dashboard'))
        
        # 更新状态为已兑现
        record.is_fulfilled = True
        db.session.commit()
        flash('奖励已成功兑现')
    except Exception as e:
        db.session.rollback()
        flash(f'兑现过程中发生错误: {str(e)}')
    
    return redirect(url_for('main.child_detail', child_id=child.id))