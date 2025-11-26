# 测试执行指南

本指南说明如何执行代码评审系统的测试套件。

## 测试前准备

### 1. 安装依赖

测试需要以下 Python 包：

```bash
pip install -r requirements.txt
```

这将安装：
- PyYAML - 配置文件解析
- SQLAlchemy - 数据库 ORM
- PyMySQL - MySQL 驱动
- APScheduler - 任务调度
- openpyxl - Excel 报告生成
- 其他项目依赖

### 2. 检查测试环境

运行环境检查脚本：

```bash
python tests\check_environment.py
```

该脚本会检查：
- ✓ Python 版本（需要 3.8+）
- ✓ 必需的依赖包
- ✓ 配置文件是否存在
- ✓ 数据库连接（如果启用）

### 3. 配置准备

#### 基础配置（必需）

确保 `config.yaml` 存在并包含基本配置：

```yaml
gitlab:
  url: "https://your-gitlab.com"
  private_token: "your_token"
  project_id: 123

llm:
  api_url: "https://api.openai.com/v1/chat/completions"
  api_key: "your_api_key"
  model: "gpt-4"

review_rules:
  代码风格:
    enabled: true
    rules:
      - "检查代码格式"
```

#### 数据库配置（可选）

如果要测试数据库功能，在 `config.yaml` 或 `config.local.yaml` 中添加：

```yaml
storage:
  enabled: true
  connection:
    host: localhost
    port: 3306
    username: root
    password: your_password
    database: code_review_test
    charset: utf8mb4
  pool_size: 10
```

然后初始化数据库：

```bash
python init_database.py
```

## 运行测试

### 方式一：运行所有测试

```bash
python tests\run_tests.py
```

或者：

```bash
python tests\run_tests.py all
```

### 方式二：运行特定测试套件

**调度器测试**（不需要外部服务）：
```bash
python tests\run_tests.py scheduler
```

**数据库测试**（需要 MySQL）：
```bash
python tests\run_tests.py database
```

**集成测试**（需要 GitLab 和 LLM）：
```bash
python tests\run_tests.py integration
```

### 方式三：直接运行测试文件

```bash
# 调度器测试
python tests\test_scheduler.py

# 数据库测试
python tests\test_database_connection.py

# 集成测试
python tests\test_integration.py
```

## 测试说明

### 调度器测试 (test_scheduler.py)

**测试内容**：
- 调度器初始化、启动和停止
- 不同类型的调度表达式（间隔、Cron、每日、每周）
- 任务管理（查询、取消、更新）
- 多任务并发调度
- 异常处理

**前置条件**：
- ✓ 无特殊要求（纯本地测试）
- ✓ 不需要外部服务
- ✓ 运行快速（约 30 秒）

**预期结果**：
```
总测试数: 11
成功: 11
失败: 0
错误: 0
```

### 数据库测试 (test_database_connection.py)

**测试内容**：
- 数据库连接
- 表结构创建和验证
- 数据写入、读取、更新、删除
- 统计查询
- 连接错误处理

**前置条件**：
- ✓ MySQL 5.7+ 运行中
- ✓ 配置文件启用存储功能
- ✓ 数据库已初始化（运行 init_database.py）

**预期结果**：
```
总测试数: 9
成功: 9
失败: 0
错误: 0
```

**如果未配置数据库**：
```
总测试数: 0
跳过: 测试类级别跳过（存储功能未启用）
```

### 集成测试 (test_integration.py)

**测试内容**：
- 配置加载
- GitLab 连接
- LLM 客户端初始化
- 评审引擎初始化
- 报告生成
- 数据库存储集成
- 端到端工作流

**前置条件**：
- ✓ GitLab 访问令牌和项目配置
- ✓ LLM API 配置
- ✓ 至少两个可对比的分支（用于端到端测试）
- ✓ 数据库配置（可选）

**预期结果**：
```
总测试数: 7
成功: 6-7（取决于配置）
跳过: 0-1（取决于配置）
```

**部分测试可能被跳过**：
- 如果未配置 GitLab → 跳过 GitLab 相关测试
- 如果未配置 LLM → 跳过 LLM 相关测试
- 如果未配置分支 → 跳过端到端测试
- 如果未启用存储 → 跳过存储测试

## 测试输出示例

### 成功的测试输出

```
======================================================================
定时任务调度测试
======================================================================

============================================================
执行测试: test_01_scheduler_initialization
============================================================
测试调度器初始化...
✓ 调度器创建成功
✓ 时区: Asia/Shanghai
✓ 最大实例数: 3

test_01_scheduler_initialization (test_scheduler.TestScheduler) ... ok

============================================================
执行测试: test_03_schedule_interval_job
============================================================
测试间隔调度...
✓ 间隔任务注册成功
✓ 调度器已启动，等待任务执行...
[2025-11-25 10:30:02] 任务执行: interval_test
[2025-11-25 10:30:04] 任务执行: interval_test
✓ 任务执行 2 次

test_03_schedule_interval_job (test_scheduler.TestScheduler) ... ok

...

======================================================================
测试总结
======================================================================
总测试数: 11
成功: 11
失败: 0
错误: 0
跳过: 0
```

### 跳过的测试输出

```
test_06_storage_integration (test_integration.TestIntegration) ... skipped '存储功能未启用'
```

### 失败的测试输出

```
test_02_gitlab_connection (test_integration.TestIntegration) ... FAIL

======================================================================
FAIL: test_02_gitlab_connection (test_integration.TestIntegration)
----------------------------------------------------------------------
Traceback (most recent call last):
  ...
AssertionError: GitLab 连接失败: 401 Unauthorized

----------------------------------------------------------------------
```

## 常见问题

### 1. 导入错误

**问题**：`ModuleNotFoundError: No module named 'xxx'`

**解决**：
```bash
pip install -r requirements.txt
```

### 2. 数据库连接失败

**问题**：`MySQL连接失败: Can't connect to MySQL server`

**检查**：
- MySQL 服务是否运行
- 配置文件中的连接信息是否正确
- 数据库是否存在
- 用户是否有权限

**解决**：
```bash
# 启动 MySQL 服务（Windows）
net start MySQL80

# 创建数据库
mysql -u root -p
CREATE DATABASE code_review_test CHARACTER SET utf8mb4;

# 初始化表结构
python init_database.py
```

### 3. GitLab 连接失败

**问题**：`GitLab 连接失败: 401 Unauthorized`

**检查**：
- GitLab URL 是否正确
- Private Token 是否有效
- 项目 ID 是否正确
- 网络是否可达

### 4. LLM API 调用失败

**问题**：`LLM 初始化失败` 或 API 调用超时

**检查**：
- API URL 是否正确
- API Key 是否有效
- 模型名称是否正确
- 网络是否可达
- API 配额是否充足

### 5. 测试超时

**问题**：调度器测试执行时间过长

**原因**：等待任务触发和执行

**正常情况**：
- `test_03_schedule_interval_job` 需要等待约 5 秒
- `test_09_multiple_jobs` 需要等待约 8 秒
- 其他测试通常在 1 秒内完成

## 测试最佳实践

### 1. 渐进式测试

先运行不依赖外部服务的测试：

```bash
# 第一步：调度器测试（最快、无依赖）
python tests\run_tests.py scheduler

# 第二步：数据库测试（需要 MySQL）
python tests\run_tests.py database

# 第三步：集成测试（需要完整配置）
python tests\run_tests.py integration
```

### 2. 测试数据隔离

- 数据库测试使用独立的测试数据库
- 每个测试完成后清理数据
- 避免影响生产数据

### 3. 持续集成

可以在 CI/CD 流程中集成测试：

```yaml
# .gitlab-ci.yml 示例
test:
  script:
    - pip install -r requirements.txt
    - python tests/run_tests.py scheduler
```

## 扩展测试

### 添加新测试用例

1. 在相应的测试文件中添加新方法：

```python
def test_xx_new_feature(self):
    """测试 XX: 新功能"""
    print("测试新功能...")
    
    # 测试代码
    ...
    
    self.assertTrue(result, "应该成功")
    print("✓ 新功能测试通过")
```

2. 方法名必须以 `test_` 开头
3. 使用 `self.assert*` 方法进行断言
4. 添加清晰的日志输出

### 创建新测试文件

1. 创建 `test_xxx.py`
2. 继承 `unittest.TestCase`
3. 实现 `setUp()` 和 `tearDown()`
4. 在 `run_tests.py` 中注册

## 测试覆盖目标

当前测试覆盖率目标：

- ✅ 核心功能 > 80%
- ✅ 数据库操作 100%
- ✅ 调度器功能 100%
- ⏳ 异常处理路径 > 60%

## 获取帮助

如遇到问题：

1. 查看测试输出的详细错误信息
2. 运行 `check_environment.py` 检查环境
3. 查看项目 README.md
4. 检查配置文件是否正确
