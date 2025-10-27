from flask import Blueprint

# 创建分析蓝图
analytics = Blueprint('analytics', __name__, template_folder='templates')

# 导入视图模块，确保路由被注册
from app.analytics import views