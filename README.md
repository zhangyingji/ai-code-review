# 代码评审系统

自动化代码评审工具，对接 GitLab，使用大模型进行评审

## 环境要求

- Python 3.8+
- Git

## 核心功能

### 评审功能
- ✅ **GitLab 集成** - 自动拉取代码差异，支持分支对比与新增文件评审
- ✅ **智能评审** - 集成大模型进行代码分析，支持深度思考模式
- ✅ **代码段落展示** - 显示问题所在的具体代码片段及上下文
- ✅ **问题定位信息** - 指示问题所在的文件、行号、方法等详细信息
- ✅ **严重程度分类** - 拥有可配置的严重程度标准（严重/主要/次要/建议）
- ✅ **可配置规则** - 支持自定义评审规则与其启用控制
- ✅ **并发评审** - 使用线程池实现高效的并发评审
- ✅ **文件格式过滤** - 自定义忽略文件类型和目录
- ✅ **提交人过滤** - 仅评审指定提交人的代码修改

### 输出方式
- ✅ **报告文件** - 支持 HTML 和 Excel 两种格式报告
- ✅ **数据库存储** - 将评审结果保存到SQLite数据库
- ✅ **Web查询界面** - 基于Vue 3 + Element Plus的在线查询系统
- ✅ **REST API** - 提供RESTful API接口，支持第三方集成

## 快速开始

### 1. 安装依赖

**环境要求**：
- Python 3.8 或更高版本
- Git

```bash
# 检查 Python 版本
python --version  # 应显示 3.8.0 或更高

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

复制配置示例并修改：

```bash
cp config.local.yaml.example config.local.yaml
# 编辑 config.local.yaml，填入 GitLab 和大模型配置
```

最小配置：

```yaml
gitlab:
  url: "https://your-gitlab.com"
  private_token: "your_gitlab_token"  # GitLab 设置中创建
  project_id: 123

branch:
  review_branch: "feature/new-feature"  # 要评审的分支
  base_branch: "main"                   # 必须指定，不能为空

llm:
  api_url: "http://your-api-server:port/path/to/model/v1/chat/completions"
  api_key: "your_api_key"
  model: "gpt-4"
```

### 3. 运行评审

#### 方式1：生成报告文件（默认）

```bash
# 生成HTML报告
python main.py -s feature/new-feature -t main -f html

# 生成Excel报告
python main.py -s feature/new-feature -t main -f excel
```

#### 方式2：保存到数据库（新功能）

```bash
# 保存到数据库
python main.py -s feature/new-feature -t main -f database

# 评审完成后会显示：
# - 会话UUID
# - 数据库路径
# - Web界面地址
# - API文档地址
```

### 4. 查看结果

#### 报告文件模式
报告生成在 `./reports/` 目录：
- **HTML 报告**：用浏览器打开，支持互动式筛选
- **Excel 报告**：用Excel打开，便于数据分析

#### 数据库模式

**启动API服务器**：
```bash
python start_api.py
```

**查看数据**：
- API文档：http://localhost:8000/api/docs
- Web界面：http://localhost:5173 （需先启动前端）

**启动前端**（可选）：
```bash
cd frontend
npm install
npm run dev
```

详细使用请参考：[DATABASE_GUIDE.md](DATABASE_GUIDE.md)

## 配置说明

### 大模型配置

支持所有 OpenAI 兼容格式的 API，只需配置 `api_url` 和 `api_key`：

**OpenAI**：
```yaml
llm:
  api_url: "https://api.openai.com/v1/chat/completions"
  api_key: "sk-..."
  model: "gpt-4"
```

**DeepSeek**：
```yaml
llm:
  api_url: "https://api.deepseek.com/v1/chat/completions"
  api_key: "sk-..."
  model: "deepseek-chat"
```

**通义千问**（自建或云服务）：
```yaml
llm:
  api_url: "http://your-api-server:port/r/ai-deploy-dsfp-prd/qwen-max/v1/chat/completions"
  api_key: "your_api_key"
  model: "qwen-max"
```

### 自定义评审规则

编辑 `config.yaml` 添加你的规则：

```yaml
review_rules:
  # 添加自定义规则类别
  company_standards:
    enabled: true
    rules:
      - "检查是否使用公司统一框架"
      - "检查是否符合团队编码规范"
```

### 并发加速

```yaml
performance:
  enable_concurrent: true  # 启用并发
  max_workers: 3          # 并发数量
```

### 深度思考模式

```yaml
llm:
  enable_thinking: true  # 启用深度思考模式
```

在消息中添加 `/think` 标签可强制启用，添加 `/no_think` 标签可禁用。

### 日志配置

默认会自动保存日志到 `./logs/` 目录，可自定义：

```yaml
logging:
  enabled: true            # 启用文件日志
  log_dir: "./logs"        # 日志目录
  level: "INFO"            # 日志级别: DEBUG, INFO, WARNING, ERROR
  max_file_size: 10        # 单个日志文件最大大小(MB)
  backup_count: 5          # 保留的日志文件数量
  console_output: true     # 同时输出到控制台
```

命令行指定日志级别：

```bash
python main.py --log-level DEBUG  # 详细调试信息
```

## 命令行参数

```bash
python main.py --help

选项:
  -c, --config           配置文件路径
  -p, --project          项目名称 (当配置中有多个项目时,用此参数选择特定项目)
  -s, --source           源分支
  -t, --target           目标分支
  -f, --format           报告格式 (html/excel/database)
  -o, --output           输出目录
  --log-level            日志级别 (DEBUG/INFO/WARNING/ERROR)
  --no-group-by-author   不按作者分组
```

## 项目结构

```
code-review/
├── src/
│   ├── api/                   # 新增：API和数据库模块
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic数据模式
│   │   ├── services/          # 业务服务
│   │   ├── routers/           # API路由
│   │   └── main.py            # FastAPI应用
│   ├── formatters/            # 报告格式化器
│   ├── templates/             # HTML模板
│   ├── utils/                 # 工具函数
│   ├── gitlab_client.py       # GitLab客户端
│   ├── llm_client.py          # 大模型客户端
│   ├── review_engine.py       # 评审引擎
│   └── report_generator.py    # 报告生成器
├── frontend/                  # 新增：Vue前端项目
│   ├── src/
│   │   ├── api/              # API封装
│   │   ├── views/            # 页面组件
│   │   └── router/           # 路由配置
│   ├── package.json
│   └── vite.config.js
├── main.py                    # 主程序
├── start_api.py               # 新增：API服务器启动脚本
├── config.yaml                # 配置文件
├── requirements.txt           # 依赖列表
├── DATABASE_GUIDE.md          # 新增：数据库功能指南
├── IMPLEMENTATION.md          # 新增：实施总结
└── TESTING.md                 # 新增：快速测试指南
```

## 许可证

MIT License
