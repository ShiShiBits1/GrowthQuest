from flask import Blueprint

# 创建main蓝图
main = Blueprint('main', __name__)# 导入视图函数
from app.main import views