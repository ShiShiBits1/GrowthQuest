#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库初始化脚本

此脚本用于创建数据库表并初始化默认管理员账户。
运行方式: python init_db.py
"""

import sys
import logging
from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('init_db')

def init_database():
    """初始化数据库"""
    try:
        # 创建应用实例
        app = create_app()
        
        with app.app_context():
            # 创建所有数据库表
            logger.info("开始创建数据库表...")
            db.create_all()
            logger.info("数据库表创建完成")
            
            # 检查是否已有用户，如果没有则创建默认管理员
            logger.info("检查用户表状态...")
            if not User.query.first():
                admin = User(
                    username='admin',
                    password=generate_password_hash('admin123')
                )
                db.session.add(admin)
                db.session.commit()
                logger.info('默认管理员用户已创建')
                
                print('\n==== 数据库初始化成功 ====')
                print('默认管理员账户信息:')
                print('  用户名: admin')
                print('  密码: admin123')
                print('\n请在首次登录后修改默认密码!')
            else:
                logger.info('数据库已存在用户记录')
                print('\n==== 数据库检查完成 ====')
                print('数据库已初始化，用户账户已存在')
                print('如果需要重置管理员密码，请手动修改数据库')
                
            # 检查数据库连接状态
            logger.info("验证数据库连接...")
            # 尝试简单查询以验证连接
            user_count = db.session.query(User).count()
            logger.info(f"当前系统用户数量: {user_count}")
            
            return True
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}", exc_info=True)
        print(f"\n错误: 数据库初始化失败 - {str(e)}")
        print("请检查数据库连接配置和权限设置")
        return False

def main():
    """主函数"""
    print("=== 小孩成长奖励系统 - 数据库初始化 ===")
    print("开始初始化数据库...")
    
    success = init_database()
    
    if success:
        print("\n数据库初始化成功! 您现在可以运行应用了。")
        print("开发环境: python run.py")
        print("生产环境: uwsgi --ini uwsgi.ini")
        return 0
    else:
        print("\n数据库初始化失败，请检查错误信息并解决问题。")
        return 1

if __name__ == '__main__':
    sys.exit(main())