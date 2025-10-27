#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加任务分类表并初始化默认分类
由于SQLite不支持直接修改表结构，我们创建一个新的脚本来处理迁移
"""

import sqlite3
import os

def migrate_database():
    """使用SQL直接执行数据库迁移"""
    try:
        db_path = 'data.sqlite'
        
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            print(f"错误：数据库文件 {db_path} 不存在！")
            return False
        
        # 连接到SQLite数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建任务分类表（如果不存在）
        print("创建任务分类表...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(64) NOT NULL UNIQUE,
            description TEXT
        )
        ''')
        
        # 检查是否需要添加分类数据
        cursor.execute("SELECT COUNT(*) FROM task_category")
        if cursor.fetchone()[0] == 0:
            print("初始化默认任务分类...")
            default_categories = [
                ('学习任务', '与学习相关的任务，如做作业、阅读等'),
                ('生活习惯', '日常生活习惯养成，如刷牙、整理房间等'),
                ('品德行为', '培养良好品德的行为，如帮助他人、分享等')
            ]
            cursor.executemany(
                "INSERT INTO task_category (name, description) VALUES (?, ?)",
                default_categories
            )
        
        # 检查Task表是否已经有category_id列
        cursor.execute("PRAGMA table_info(task)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'category_id' not in columns:
            print("向Task表添加category_id列...")
            # SQLite不支持直接添加外键约束到现有表，所以我们创建一个临时表
            cursor.execute('''
            CREATE TABLE task_new AS SELECT * FROM task
            ''')
            
            # 删除旧表
            cursor.execute("DROP TABLE task")
            
            # 创建新表，包含category_id列
            cursor.execute('''
            CREATE TABLE task (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(128) NOT NULL,
                description TEXT,
                points INTEGER NOT NULL,
                category VARCHAR(64) NOT NULL DEFAULT '学习任务',
                category_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES task_category (id)
            )
            ''')
            
            # 重新插入数据
            cursor.execute("SELECT * FROM task_new")
            tasks = cursor.fetchall()
            
            # 获取所有分类
            cursor.execute("SELECT id, name FROM task_category")
            categories = {name: id for id, name in cursor.fetchall()}
            
            # 插入数据并设置category_id
            for task in tasks:
                task_id, name, description, points, category, is_active = task
                category_id = categories.get(category, 1)  # 默认使用第一个分类
                cursor.execute('''
                INSERT INTO task (id, name, description, points, category, category_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (task_id, name, description, points, category, category_id, is_active))
            
            # 删除临时表
            cursor.execute("DROP TABLE task_new")
        
        # 提交所有更改
        conn.commit()
        conn.close()
        
        print("数据库迁移完成！")
        return True
        
    except Exception as e:
        print(f"迁移过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    success = migrate_database()
    import sys
    sys.exit(0 if success else 1)