# 代码评审系统 - 前端项目

## 项目介绍

基于Vue 3 + Element Plus的代码评审系统前端界面。

## 功能特性

- ✅ 评审列表展示（支持筛选和分页）
- ✅ 评审详情查看
- ✅ 问题列表展示和筛选
- 🚧 问题在线标注（待开发）
- 🚧 代码片段高亮显示（待开发）
- 🚧 统计看板（待开发）

## 技术栈

- Vue 3 (Composition API)
- Vue Router 4
- Element Plus
- Axios
- Vite

## 开发环境

### 前置要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:5173

### 构建生产版本

```bash
npm run build
```

构建产物在`dist`目录。

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/            # API接口
│   │   └── review.js   # 评审相关API
│   ├── views/          # 页面组件
│   │   ├── ReviewList.vue    # 评审列表页
│   │   └── ReviewDetail.vue  # 评审详情页
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── index.html          # HTML模板
├── vite.config.js      # Vite配置
└── package.json        # 项目配置
```

## 配置说明

### API代理

开发环境下，Vite会将`/api`请求代理到后端服务器（默认http://localhost:8000）。

配置在`vite.config.js`：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 页面功能

### 评审列表页 (/reviews)

- 展示所有评审会话
- 支持筛选：项目名称、分支、日期范围
- 显示问题统计（彩色标签）
- 分页查询

### 评审详情页 (/reviews/:id)

- 展示评审基本信息
- 问题列表展示
- 支持筛选：严重程度、提交人
- 分页查询

## 待开发功能

1. **问题在线标注**
   - 确认意见选择（采纳/不采纳/忽略）
   - 是否已改标记
   - 评审意见编辑

2. **代码片段展示**
   - 语法高亮
   - 行号显示
   - 上下文展示

3. **统计看板**
   - 问题趋势图
   - 严重程度分布
   - 提交人排名

## 注意事项

1. 确保后端API服务已启动（http://localhost:8000）
2. 开发环境下使用代理，生产环境需配置实际API地址
3. 建议使用现代浏览器（Chrome、Firefox、Edge）

## 故障排除

### 无法连接API

检查后端服务是否启动：
```bash
python start_api.py
```

### 依赖安装失败

尝试清除缓存：
```bash
rm -rf node_modules package-lock.json
npm install
```

## 开发计划

- [ ] 完善问题编辑功能
- [ ] 添加代码高亮显示
- [ ] 实现统计看板
- [ ] 添加搜索功能
- [ ] 优化移动端适配
- [ ] 添加单元测试
# 代码评审系统 - 前端项目

## 项目介绍

基于Vue 3 + Element Plus的代码评审系统前端界面。

## 功能特性

- ✅ 评审列表展示（支持筛选和分页）
- ✅ 评审详情查看
- ✅ 问题列表展示和筛选
- 🚧 问题在线标注（待开发）
- 🚧 代码片段高亮显示（待开发）
- 🚧 统计看板（待开发）

## 技术栈

- Vue 3 (Composition API)
- Vue Router 4
- Element Plus
- Axios
- Vite

## 开发环境

### 前置要求

- Node.js >= 16.0.0
- npm >= 8.0.0

### 安装依赖

```bash
cd frontend
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:5173

### 构建生产版本

```bash
npm run build
```

构建产物在`dist`目录。

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/            # API接口
│   │   └── review.js   # 评审相关API
│   ├── views/          # 页面组件
│   │   ├── ReviewList.vue    # 评审列表页
│   │   └── ReviewDetail.vue  # 评审详情页
│   ├── router/         # 路由配置
│   │   └── index.js
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── index.html          # HTML模板
├── vite.config.js      # Vite配置
└── package.json        # 项目配置
```

## 配置说明

### API代理

开发环境下，Vite会将`/api`请求代理到后端服务器（默认http://localhost:8000）。

配置在`vite.config.js`：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 页面功能

### 评审列表页 (/reviews)

- 展示所有评审会话
- 支持筛选：项目名称、分支、日期范围
- 显示问题统计（彩色标签）
- 分页查询

### 评审详情页 (/reviews/:id)

- 展示评审基本信息
- 问题列表展示
- 支持筛选：严重程度、提交人
- 分页查询

## 待开发功能

1. **问题在线标注**
   - 确认意见选择（采纳/不采纳/忽略）
   - 是否已改标记
   - 评审意见编辑

2. **代码片段展示**
   - 语法高亮
   - 行号显示
   - 上下文展示

3. **统计看板**
   - 问题趋势图
   - 严重程度分布
   - 提交人排名

## 注意事项

1. 确保后端API服务已启动（http://localhost:8000）
2. 开发环境下使用代理，生产环境需配置实际API地址
3. 建议使用现代浏览器（Chrome、Firefox、Edge）

## 故障排除

### 无法连接API

检查后端服务是否启动：
```bash
python start_api.py
```

### 依赖安装失败

尝试清除缓存：
```bash
rm -rf node_modules package-lock.json
npm install
```

## 开发计划

- [ ] 完善问题编辑功能
- [ ] 添加代码高亮显示
- [ ] 实现统计看板
- [ ] 添加搜索功能
- [ ] 优化移动端适配
- [ ] 添加单元测试
