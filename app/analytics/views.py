from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.analytics import analytics
from app.models import Child, TaskRecord, TaskCategory, Task, Reward, RewardRecord, ChildBadge, Badge, TaskStreak
from app import db
from sqlalchemy import func, and_

@analytics.route('/analytics')
@login_required
def analytics_dashboard():
    """数据分析仪表盘"""
    # 家长用户可以查看所有孩子的数据分析
    if hasattr(current_user, 'children'):
        # 获取所有孩子
        children = current_user.children.all()
        # 如果有多个孩子，默认显示第一个孩子的数据
        selected_child_id = request.args.get('child_id')
        if selected_child_id:
            selected_child = Child.query.get(selected_child_id)
            # 确保选择的孩子属于当前家长
            if not selected_child or selected_child.parent != current_user:
                flash('无效的孩子选择')
                return redirect(url_for('analytics.analytics_dashboard'))
        elif children:
            selected_child = children[0]
        else:
            # 如果没有孩子，显示提示信息
            return render_template('analytics/empty.html')
    else:
        # 孩子用户只能查看自己的数据
        selected_child = current_user
        children = [selected_child]
    
    # 获取时间范围参数
    time_range = request.args.get('time_range', '7')
    days = int(time_range)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 获取任务完成统计数据
    task_completion_data = Child.get_task_completion_by_period(
        selected_child.id, start_date, end_date
    )
    
    # 获取积分趋势数据
    points_trend_data = Child.get_points_trend(selected_child.id, days)
    
    # 获取连续完成统计
    streak_stats = Child.get_streak_statistics(selected_child.id)
    
    # 获取勋章统计
    badge_stats = Child.get_badge_statistics(selected_child.id)
    
    # 获取任务完成率
    completion_rate_data = Child.get_task_completion_rate(selected_child.id, days)
    
    # 获取任务分类分布数据
    category_distribution = Child.get_task_category_distribution(selected_child.id, start_date, end_date)
    
    # 获取习惯养成时间线数据（使用用户选择的时间范围）
    habit_timeline = Child.get_habit_timeline(selected_child.id, days=days)
    
    # 获取详细连续天数统计
    detailed_streak_stats = Child.get_detailed_streak_statistics(selected_child.id)
    
    # 添加当前时间
    current_time = datetime.utcnow()
    
    return render_template(
        'analytics/dashboard.html',
        children=children,
        selected_child=selected_child,
        time_range=time_range,
        task_completion_data=task_completion_data,
        points_trend_data=points_trend_data,
        streak_stats=streak_stats,
        badge_stats=badge_stats,
        completion_rate_data=completion_rate_data,
        category_distribution=category_distribution,
        habit_timeline=habit_timeline,
        detailed_streak_stats=detailed_streak_stats,
        current_time=current_time
    )

@analytics.route('/analytics/detail/<child_id>/<metric>')
@login_required
def analytics_detail(child_id, metric):
    """详细的数据分析页面"""
    # 获取指定的孩子
    child = Child.query.get(child_id)
    
    # 权限检查
    if not child or (hasattr(current_user, 'children') and child.parent != current_user):
        flash('无权访问此数据')
        return redirect(url_for('analytics.analytics_dashboard'))
    
    # 获取时间范围参数
    time_range = request.args.get('time_range', '30')
    days = int(time_range)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 根据不同的指标加载不同的数据
    if metric == 'tasks':
        # 任务完成详情
        task_records = TaskRecord.query.filter_by(
            child_id=child.id,
            is_confirmed=True
        ).filter(
            TaskRecord.completed_at >= start_date
        ).order_by(TaskRecord.completed_at.desc()).all()
        
        # 获取任务分类完成情况统计
        category_completion_stats = Child.get_category_completion_stats(child.id, start_date, end_date)
        
        return render_template(
            'analytics/detail/tasks.html',
            child=child,
            time_range=time_range,
            task_records=task_records,
            metric=metric,
            category_completion_stats=category_completion_stats
        )
    
    elif metric == 'points':
        # 积分获取详情
        points_records = db.session.query(
            TaskRecord,
            Task.name.label('task_name'),
            Task.points.label('task_points')
        ).join(
            Task
        ).filter(
            TaskRecord.child_id == child.id,
            TaskRecord.is_confirmed == True,
            TaskRecord.completed_at >= start_date
        ).order_by(TaskRecord.completed_at.desc()).all()
        
        # 积分消耗记录
        reward_claims = RewardRecord.query.filter_by(
            child_id=child.id
        ).filter(
            RewardRecord.redeemed_at >= start_date
        ).order_by(RewardRecord.redeemed_at.desc()).all()
        
        return render_template(
            'analytics/detail/points.html',
            child=child,
            time_range=time_range,
            points_records=points_records,
            reward_claims=reward_claims,
            metric=metric
        )
    
    elif metric == 'badges':
        # 勋章获取详情
        earned_badges = ChildBadge.query.filter_by(
            child_id=child.id
        ).filter(
            ChildBadge.earned_at >= start_date
        ).order_by(ChildBadge.earned_at.desc()).all()
        
        # 获取详细的勋章分析数据
        badge_analysis = Child.get_detailed_badge_analysis(child_id, days)
        
        # 构建已获得勋章ID集合，供模板使用
        earned_badge_ids = [child_badge.badge_id for child_badge in earned_badges]
        
        return render_template(
            'analytics/detail/badges.html',
            child=child,
            time_range=time_range,
            earned_badges=earned_badges,
            metric=metric,
            badge_analysis=badge_analysis,
            earned_badge_ids=earned_badge_ids
        )
    
    elif metric == 'habits':
        # 习惯养成详情
        # 获取习惯养成时间线（使用用户选择的时间范围）
        habit_timeline = Child.get_habit_timeline(child.id, days=days)
        
        # 获取详细连续天数统计
        detailed_streak_stats = Child.get_detailed_streak_statistics(child.id)
        
        return render_template(
            'analytics/detail/habits.html',
            child=child,
            time_range=time_range,
            habit_timeline=habit_timeline,
            detailed_streak_stats=detailed_streak_stats,
            metric=metric
        )
    
    elif metric == 'streaks':
        # 连续完成详情
        streaks = TaskStreak.query.filter_by(child_id=child.id).all()
        
        return render_template(
            'analytics/detail/streaks.html',
            child=child,
            time_range=time_range,
            streaks=streaks,
            metric=metric
        )
    
    # 如果没有找到对应的指标，重定向到仪表盘
    flash('无效的分析指标')
    return redirect(url_for('analytics.analytics_dashboard'))

@analytics.route('/analytics/api/task-category-data/<child_id>')
@login_required
def task_category_data(child_id):
    """获取任务分类数据的API端点"""
    # 获取指定的孩子
    child = Child.query.get(child_id)
    
    # 权限检查
    if not child or (hasattr(current_user, 'children') and child.parent != current_user):
        return jsonify({'error': '无权访问此数据'}), 403
    
    # 获取时间范围参数
    time_range = request.args.get('time_range', '7')
    days = int(time_range)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 获取任务分类分布数据
    category_data = Child.get_task_category_distribution(child.id, start_date, end_date)
    
    # 转换为Chart.js需要的格式
    labels = [item['category_name'] for item in category_data]
    data = [item['count'] for item in category_data]
    backgroundColors = [
        'rgba(255, 99, 132, 0.6)',
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(153, 102, 255, 0.6)',
        'rgba(255, 159, 64, 0.6)'
    ]
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'data': data,
            'backgroundColor': backgroundColors[:len(labels)],
            'borderColor': backgroundColors[:len(labels)],
            'borderWidth': 1
        }]
    })