# 数据库存储和Web查询功能使用指南

## 功能概述

本系统新增了数据库存储和Web查询功能，提供两种并列的评审结果输出方式：

1. **报告文件模式**（html/excel）：生成本地报告文件，适合临时评审和离线查看
2. **数据库模式**（database）：保存到数据库并通过Web界面查询，适合持续评审和团队协作

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖包括：
- `fastapi`: Web API框架
- `uvicorn`: ASGI服务器
- `sqlalchemy`: ORM框架
- `pydantic`: 数据验证

### 2. 配置database模式

编辑`config.yaml`（或`config.local.yaml`），设置输出格式为database：

```yaml
report:
  format: "database"  # 选择database模式
  
database:
  path: "./data/review.db"  # 数据库文件路径
  
api:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "http://localhost:5173"  # Vue前端地址
```

### 3. 运行评审

使用database格式运行评审：

```bash
# 使用配置文件中的设置
python main.py

# 或通过命令行指定
python main.py -f database -s feature/new-feature -t main
```

评审完成后会输出：
- 会话UUID
- 数据库文件路径
- Web界面访问地址
- API文档地址

### 4. 启动API服务器

评审完成后，启动API服务器查看结果：

```bash
python start_api.py
```

访问：
- Web界面：http://localhost:8000 （前端开发中）
- API文档：http://localhost:8000/api/docs
- API接口：http://localhost:8000/api/v1/

## API接口说明

### 评审会话接口

#### 获取评审列表
```
GET /api/v1/reviews
```

查询参数：
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `project_name`: 项目名称筛选
- `review_branch`: 评审分支筛选
- `base_branch`: 基准分支筛选
- `start_date`: 开始日期（YYYY-MM-DD）
- `end_date`: 结束日期（YYYY-MM-DD）
- `min_issues`: 最小问题数

#### 获取评审详情
```
GET /api/v1/reviews/{session_id}
```

#### 获取问题列表
```
GET /api/v1/reviews/{session_id}/issues
```

查询参数：
- `page`: 页码
- `page_size`: 每页数量
- `severity`: 严重程度筛选（逗号分隔，默认"critical,major"）
- `author`: 提交人筛选
- `confirm_status`: 确认意见筛选
- `is_fixed`: 是否已修改筛选
- `file_path`: 文件路径模糊搜索

### 问题管理接口

#### 更新问题
```
PUT /api/v1/issues/{issue_id}
```

请求体：
```json
{
  "confirm_status": "accepted",  // pending/accepted/rejected/ignored
  "is_fixed": true,
  "review_comment": "已修复"
}
```

#### 批量更新问题
```
PUT /api/v1/issues/batch
```

请求体：
```json
{
  "issue_ids": [1, 2, 3],
  "confirm_status": "accepted",
  "is_fixed": true
}
```

### 统计接口

#### 获取统计概览
```
GET /api/v1/statistics/overview
```

查询参数：
- `start_date`: 开始日期
- `end_date`: 结束日期
- `project_name`: 项目筛选

## 数据库结构

系统使用SQLite数据库，包含以下数据表：

1. **review_sessions**: 评审会话表
2. **review_files**: 评审文件表
3. **review_issues**: 评审问题表
4. **commit_infos**: 提交信息表
5. **issue_comments**: 问题评论表（预留）

数据库文件默认保存在`./data/review.db`。

## 使用场景对比

| 场景 | 推荐模式 | 理由 |
|------|---------|------|
| 一次性评审 | html/excel | 快速生成，便于分发 |
| 持续集成评审 | database | 历史追溯，趋势分析 |
| 团队协作评审 | database | 在线标注，问题跟踪 |
| 离线查看 | html/excel | 无需服务器 |
| 数据分析 | database | 支持复杂查询 |

## 前端开发

前端项目正在开发中，将提供以下功能：

1. **评审列表页**
   - 展示所有评审会话
   - 支持多维度筛选
   - 分页查询

2. **评审详情页**
   - 展示问题列表
   - 问题筛选（严重程度、提交人等）
   - 在线标注（确认意见、是否已改）
   - 代码片段展示

3. **统计看板**（后期扩展）
   - 问题趋势图
   - 严重程度分布
   - 提交人排名

## 注意事项

1. **模式选择**：`database`和`html/excel`是互斥的，选择database时不会生成报告文件
2. **数据库备份**：定期备份`./data/review.db`文件
3. **并发访问**：SQLite适合小团队使用，大规模使用建议迁移到MySQL/PostgreSQL
4. **API安全**：生产环境建议配置CORS白名单和添加认证

## 故障排除

### 1. 数据库初始化失败

检查`./data`目录是否有写权限：
```bash
mkdir -p ./data
```

### 2. API服务器启动失败

检查端口是否被占用：
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### 3. 前端无法访问API

检查CORS配置，确保前端地址在`api.cors_origins`列表中。

## 下一步计划

- [ ] 完成Vue前端开发
- [ ] 添加用户认证
- [ ] 支持问题评论
- [ ] 数据导出功能
- [ ] 邮件通知
- [ ] 集成CI/CD

## 参考资料

- FastAPI文档：https://fastapi.tiangolo.com/
- SQLAlchemy文档：https://docs.sqlalchemy.org/
- Vue 3文档：https://vuejs.org/
- Element Plus文档：https://element-plus.org/
# 数据库存储和Web查询功能使用指南

## 功能概述

本系统新增了数据库存储和Web查询功能，提供两种并列的评审结果输出方式：

1. **报告文件模式**（html/excel）：生成本地报告文件，适合临时评审和离线查看
2. **数据库模式**（database）：保存到数据库并通过Web界面查询，适合持续评审和团队协作

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖包括：
- `fastapi`: Web API框架
- `uvicorn`: ASGI服务器
- `sqlalchemy`: ORM框架
- `pydantic`: 数据验证

### 2. 配置database模式

编辑`config.yaml`（或`config.local.yaml`），设置输出格式为database：

```yaml
report:
  format: "database"  # 选择database模式
  
database:
  path: "./data/review.db"  # 数据库文件路径
  
api:
  host: "0.0.0.0"
  port: 8000
  cors_origins:
    - "http://localhost:5173"  # Vue前端地址
```

### 3. 运行评审

使用database格式运行评审：

```bash
# 使用配置文件中的设置
python main.py

# 或通过命令行指定
python main.py -f database -s feature/new-feature -t main
```

评审完成后会输出：
- 会话UUID
- 数据库文件路径
- Web界面访问地址
- API文档地址

### 4. 启动API服务器

评审完成后，启动API服务器查看结果：

```bash
python start_api.py
```

访问：
- Web界面：http://localhost:8000 （前端开发中）
- API文档：http://localhost:8000/api/docs
- API接口：http://localhost:8000/api/v1/

## API接口说明

### 评审会话接口

#### 获取评审列表
```
GET /api/v1/reviews
```

查询参数：
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `project_name`: 项目名称筛选
- `review_branch`: 评审分支筛选
- `base_branch`: 基准分支筛选
- `start_date`: 开始日期（YYYY-MM-DD）
- `end_date`: 结束日期（YYYY-MM-DD）
- `min_issues`: 最小问题数

#### 获取评审详情
```
GET /api/v1/reviews/{session_id}
```

#### 获取问题列表
```
GET /api/v1/reviews/{session_id}/issues
```

查询参数：
- `page`: 页码
- `page_size`: 每页数量
- `severity`: 严重程度筛选（逗号分隔，默认"critical,major"）
- `author`: 提交人筛选
- `confirm_status`: 确认意见筛选
- `is_fixed`: 是否已修改筛选
- `file_path`: 文件路径模糊搜索

### 问题管理接口

#### 更新问题
```
PUT /api/v1/issues/{issue_id}
```

请求体：
```json
{
  "confirm_status": "accepted",  // pending/accepted/rejected/ignored
  "is_fixed": true,
  "review_comment": "已修复"
}
```

#### 批量更新问题
```
PUT /api/v1/issues/batch
```

请求体：
```json
{
  "issue_ids": [1, 2, 3],
  "confirm_status": "accepted",
  "is_fixed": true
}
```

### 统计接口

#### 获取统计概览
```
GET /api/v1/statistics/overview
```

查询参数：
- `start_date`: 开始日期
- `end_date`: 结束日期
- `project_name`: 项目筛选

## 数据库结构

系统使用SQLite数据库，包含以下数据表：

1. **review_sessions**: 评审会话表
2. **review_files**: 评审文件表
3. **review_issues**: 评审问题表
4. **commit_infos**: 提交信息表
5. **issue_comments**: 问题评论表（预留）

数据库文件默认保存在`./data/review.db`。

## 使用场景对比

| 场景 | 推荐模式 | 理由 |
|------|---------|------|
| 一次性评审 | html/excel | 快速生成，便于分发 |
| 持续集成评审 | database | 历史追溯，趋势分析 |
| 团队协作评审 | database | 在线标注，问题跟踪 |
| 离线查看 | html/excel | 无需服务器 |
| 数据分析 | database | 支持复杂查询 |

## 前端开发

前端项目正在开发中，将提供以下功能：

1. **评审列表页**
   - 展示所有评审会话
   - 支持多维度筛选
   - 分页查询

2. **评审详情页**
   - 展示问题列表
   - 问题筛选（严重程度、提交人等）
   - 在线标注（确认意见、是否已改）
   - 代码片段展示

3. **统计看板**（后期扩展）
   - 问题趋势图
   - 严重程度分布
   - 提交人排名

## 注意事项

1. **模式选择**：`database`和`html/excel`是互斥的，选择database时不会生成报告文件
2. **数据库备份**：定期备份`./data/review.db`文件
3. **并发访问**：SQLite适合小团队使用，大规模使用建议迁移到MySQL/PostgreSQL
4. **API安全**：生产环境建议配置CORS白名单和添加认证

## 故障排除

### 1. 数据库初始化失败

检查`./data`目录是否有写权限：
```bash
mkdir -p ./data
```

### 2. API服务器启动失败

检查端口是否被占用：
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### 3. 前端无法访问API

检查CORS配置，确保前端地址在`api.cors_origins`列表中。

## 下一步计划

- [ ] 完成Vue前端开发
- [ ] 添加用户认证
- [ ] 支持问题评论
- [ ] 数据导出功能
- [ ] 邮件通知
- [ ] 集成CI/CD

## 参考资料

- FastAPI文档：https://fastapi.tiangolo.com/
- SQLAlchemy文档：https://docs.sqlalchemy.org/
- Vue 3文档：https://vuejs.org/
- Element Plus文档：https://element-plus.org/
