# 新功能使用说明

本文档介绍代码评审系统新增的三大功能及其使用方法。

## 功能一：时间过滤评审

### 功能说明
支持按时间范围筛选提交进行评审，可以评审当天、昨天或自定义时间范围的代码提交。

### 使用方法

#### 1. 命令行方式

```bash
# 评审今天的提交
python main.py --today

# 评审昨天的提交
python main.py --yesterday

# 评审最近3天的提交
python main.py --last-n-days 3

# 评审自定义时间范围的提交
python main.py --since "2025-01-15" --until "2025-01-20"
python main.py --since "2025-01-15 09:00:00" --until "2025-01-15 18:00:00"
```

#### 2. 配置文件方式

在 `config.yaml` 中添加时间过滤配置：

```yaml
time_filter:
  enabled: true            # 启用时间过滤
  mode: "today"            # 模式: today, yesterday, last_n_days, custom
  last_n_days: 1           # 当mode为last_n_days时使用
  since: "2025-01-15"      # 自定义起始时间
  until: "2025-01-20"      # 自定义截止时间
  timezone: "Asia/Shanghai" # 时区设置
```

### 注意事项
- 命令行参数优先级高于配置文件
- 时间过滤与分支对比可以同时使用
- 评审报告中会显示时间过滤信息

---

## 功能二：评审结果落库及问题管理

### 功能说明
- 将评审结果持久化到MySQL数据库
- 支持技术经理对问题进行复核和状态管理
- 提供问题统计和历史追溯功能

### 数据库初始化

#### 1. 配置数据库连接

在 `config.yaml` 中添加存储配置：

```yaml
storage:
  enabled: true              # 启用数据库存储
  type: "mysql"              # 存储类型
  connection:
    host: "localhost"
    port: 3306
    database: "code_review"
    username: "review_user"
    password: "your_password"
    charset: "utf8mb4"
  pool_size: 10              # 连接池大小
  auto_save: true            # 评审完成后自动保存
```

#### 2. 创建数据库表

```bash
# 创建数据库表
python init_database.py

# 使用自定义配置文件
python init_database.py -c config.local.yaml

# 重建表（警告：会删除现有数据）
python init_database.py --drop
```

### 使用方法

#### 1. 自动保存评审结果

配置 `auto_save: true` 后，每次评审完成会自动保存到数据库。

#### 2. 问题状态管理

使用Python脚本管理问题状态：

```python
from src.storage.mysql_storage import MySQLStorage

# 初始化存储
config = {...}  # 从配置文件加载
storage = MySQLStorage(config['storage'])

# 查询待复核问题
pending_issues = storage.list_issues_by_status('pending', limit=50)

# 更新问题状态
storage.update_issue_status(
    issue_id='xxx',
    status='confirmed',  # confirmed, false_positive, ignored, resolved
    verified_by='张三',
    note='确认为真实问题'
)

# 查询某次评审的所有问题
issues = storage.list_issues_by_review(review_id='xxx')

# 获取问题统计
stats = storage.get_issue_statistics(project_id=123, time_range=30)
```

### 问题状态说明

| 状态 | 说明 |
|------|------|
| `pending` | 待复核（默认状态） |
| `confirmed` | 已确认为真实问题 |
| `false_positive` | 误报 |
| `ignored` | 已忽略 |
| `resolved` | 已解决 |

---

## 功能三：定时评审任务

### 功能说明
支持配置定时任务，自动对项目进行周期性评审。

### 配置定时任务

在 `config.yaml` 中添加调度器配置：

```yaml
scheduler:
  enabled: true                 # 启用调度器
  timezone: "Asia/Shanghai"     # 时区
  max_instances: 3              # 最大并发任务数
  misfire_grace_time: 300       # 错过执行的宽限时间（秒）
  coalesce: true                # 是否合并错过的执行
  
  jobs:
    - job_id: "daily-review-main"
      job_name: "主分支每日评审"
      enabled: true
      schedule_type: "cron"
      schedule_expr: "0 2 * * *"  # 每天凌晨2点
      project_id: 123
      review_branch: "develop"
      base_branch: "main"
      report_format: "html"
      notify_on_completion: false
    
    - job_id: "hourly-review-feature"
      job_name: "特性分支每小时评审"
      enabled: true
      schedule_type: "interval"
      schedule_expr: "interval:hours=1"  # 每小时
      project_id: 123
      review_branch: "feature/new-feature"
      base_branch: "develop"
      report_format: "excel"
```

### 调度表达式格式

| 格式 | 示例 | 说明 |
|------|------|------|
| Cron | `0 2 * * *` | 每天凌晨2点 |
| Interval | `interval:hours=6` | 每6小时 |
| Daily | `daily:10:00` | 每天10点 |
| Weekly | `weekly:MON:09:00` | 每周一上午9点 |

### 启动调度服务

```bash
# 启动调度服务
python scheduler_service.py start

# 使用自定义配置文件
python scheduler_service.py start -c config.local.yaml

# 查看服务状态（功能开发中）
python scheduler_service.py status

# 停止服务（使用Ctrl+C或发送SIGTERM信号）
```

### 日志查看

调度服务日志保存在 `./logs/scheduler_YYYYMMDD.log`

---

## 完整使用示例

### 示例1：评审今天的提交并保存到数据库

```bash
# 1. 配置数据库（config.local.yaml）
storage:
  enabled: true
  auto_save: true

# 2. 初始化数据库
python init_database.py

# 3. 执行评审
python main.py --today -s develop -t main

# 评审完成后，结果自动保存到数据库
```

### 示例2：配置定时任务

```yaml
# config.local.yaml
scheduler:
  enabled: true
  jobs:
    - job_id: "daily-review"
      job_name: "每日评审"
      enabled: true
      schedule_expr: "0 2 * * *"
      project_id: 123
      review_branch: "develop"
      base_branch: "main"
      report_format: "html"
```

```bash
# 启动调度服务（后台运行）
nohup python scheduler_service.py start > scheduler.log 2>&1 &
```

---

## 依赖安装

新功能需要额外的Python依赖：

```bash
pip install -r requirements.txt
```

新增依赖包括：
- `APScheduler>=3.10.0` - 任务调度
- `SQLAlchemy>=2.0.0` - 数据库ORM
- `PyMySQL>=1.1.0` - MySQL驱动
- `python-dateutil>=2.8.0` - 日期时间处理

---

## 故障排查

### 数据库连接失败
- 检查MySQL服务是否运行
- 确认数据库用户名和密码正确
- 确保数据库已创建

### 时间过滤无结果
- 确认时间范围内确实有提交
- 检查时区设置是否正确
- 查看日志了解详细信息

### 调度任务不执行
- 确认 `scheduler.enabled = true`
- 检查任务配置中 `enabled = true`
- 查看调度服务日志

---

## 更多帮助

查看命令行帮助：
```bash
python main.py --help
python scheduler_service.py --help
python init_database.py --help
```
