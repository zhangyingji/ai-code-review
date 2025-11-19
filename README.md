# 代码评审系统

自动化代码评审工具，对接 GitLab，使用大模型进行智能评审，按提交人生成评审报告。

## 环境要求

- Python 3.8+
- Git

## 核心功能

- ✅ **GitLab 集成** - 自动拉取代码差异，支持分支对比
- ✅ **智能评审** - 集成大模型进行代码分析  
- ✅ **可配置规则** - 支持自定义评审规则
- ✅ **多格式报告** - 支持 HTML、Markdown、JSON 格式
- ✅ **按作者分组** - 自动统计每位开发者的代码问题
- ✅ **并发加速** - 支持并发评审，提升速度3倍

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

### 3. 运行

```bash
# 使用默认配置
python main.py

# 指定源分支，自动检测创建起点
python main.py -s feature/new-feature

# 指定源分支和目标分支
python main.py -s develop -t main

# 指定报告格式
python main.py -f html  # 或 markdown, json
```

> 💡 **智能检测**：如果不指定目标分支，系统会自动检测源分支的创建起点（分离点），从 main/master/develop 中自动选择。

### 4. 查看报告

报告生成在 `./reports/` 目录，用浏览器打开 HTML 文件查看。

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
  -c, --config       配置文件路径
  -s, --source       源分支
  -t, --target       目标分支
  -f, --format       报告格式 (html/markdown/json)
  -o, --output       输出目录
  --log-level        日志级别 (DEBUG/INFO/WARNING/ERROR)
  --no-group-by-author  不按作者分组
```

## 项目结构

```
code-review/
├── src/
│   ├── gitlab_client.py     # GitLab API 集成
│   ├── llm_client.py        # 大模型客户端
│   ├── review_engine.py     # 评审引擎
│   └── report_generator.py  # 报告生成器
├── main.py                   # 主程序
├── config.yaml              # 配置文件
└── requirements.txt         # 依赖列表
```

## 许可证

MIT License
