# 小孩成长奖励系统

一个基于Flask框架的小孩成长奖励系统，使用SQLite作为数据库，支持多种部署方式，包括开发环境运行和生产环境uWSGI部署。

## 功能特点

- 用户认证（登录/登出）
- 孩子管理（添加、查看、编辑）
- 任务管理（创建任务、设置积分、分类管理）
- 奖励管理（创建奖励、设置积分消耗）
- 任务完成记录和积分确认
- 奖励兑换功能
- 数据保存在本地SQLite数据库
- 荣誉墙功能（展示孩子成就）
- 任务分类管理

## 安装与运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python init_db.py
```

这将创建数据库表并初始化一个默认管理员账户：
- 用户名: admin
- 密码: admin123

### 3. 运行应用

#### 开发环境运行

```bash
python run.py
```

应用将在端口8086上运行，您可以通过浏览器访问：`http://localhost:8086`

如果在NAS上运行，可以通过NAS的IP地址访问：`http://<NAS_IP>:8086`

#### 生产环境部署（uWSGI）

项目已配置uWSGI支持，可通过以下命令启动：

```bash
uwsgi --ini uwsgi.ini
```

默认配置下，应用将在端口8086上运行，可通过以下地址访问：`http://<服务器IP>:8086`

## 项目结构

```
成长奖励系统/
├── app/
│   ├── __init__.py    # Flask应用初始化
│   ├── models.py      # 数据库模型
│   ├── main/
│   │   ├── __init__.py  # 蓝图初始化
│   │   └── views.py     # 视图函数
│   └── templates/     # HTML模板
├── requirements.txt   # 依赖列表
├── run.py             # 开发环境应用入口
├── wsgi.py            # 生产环境WSGI入口
├── uwsgi.ini          # uWSGI配置文件
├── init_db.py         # 数据库初始化脚本
├── data.sqlite        # SQLite数据库文件（运行后生成）
├── local_access_test.py  # 本地访问测试工具
├── network_diagnostics.py # 网络诊断工具
└── DEPLOYMENT_GUIDE.md # 部署指南文档
```

## 使用说明

1. 登录系统（使用默认管理员账户或创建新账户）
2. 添加孩子信息
3. 创建任务分类（可选）
4. 创建任务和奖励
5. 孩子完成任务后，家长确认并发放积分
6. 孩子可以使用积分兑换奖励
7. 查看荣誉墙了解孩子成就

## 生产环境配置

### uWSGI配置

uWSGI配置文件(`uwsgi.ini`)已针对生产环境进行了优化，包括：

- 绑定到0.0.0.0，允许外部访问
- 配置多个进程和线程以提高性能
- 设置超时和缓冲区大小
- 详细的日志记录
- 用户权限设置

## 问题排查

项目包含多个诊断工具，用于排查部署和访问问题：

1. **网络诊断**：`python network_diagnostics.py`
2. **本地访问测试**：`python local_access_test.py`
3. **应用测试**：`python test_app.py`

详细的问题排查指南请参考`DEPLOYMENT_GUIDE.md`。

## 注意事项

- 为了安全起见，建议在生产环境中修改默认密码
- 数据库文件data.sqlite会在首次运行时自动生成，请定期备份
- 生产环境部署时，请确保正确配置uWSGI和反向代理设置
- 定期检查日志文件，及时发现和解决问题
- 如需修改端口或其他配置，请参考uwsgi.ini和DEPLOYMENT_GUIDE.md