<template>
  <div class="review-detail">
    <el-page-header @back="goBack" :content="`评审详情 - ${sessionInfo.review_branch || ''}`" />
    
    <el-card style="margin-top: 20px;" v-loading="loading">
      <!-- 评审信息概览 -->
      <template #header>
        <span>评审信息</span>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="评审分支">{{ sessionInfo.review_branch }}</el-descriptions-item>
        <el-descriptions-item label="基准分支">{{ sessionInfo.base_branch }}</el-descriptions-item>
        <el-descriptions-item label="评审时间">{{ formatDateTime(sessionInfo.review_time) }}</el-descriptions-item>
        <el-descriptions-item label="总问题数">{{ sessionInfo.total_issues }}</el-descriptions-item>
        <el-descriptions-item label="评审文件数">{{ sessionInfo.total_files_reviewed }}</el-descriptions-item>
        <el-descriptions-item label="提交数">{{ sessionInfo.total_commits }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>问题列表</span>
      </template>

      <!-- 筛选区 -->
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="严重程度">
          <el-select v-model="filterForm.severity" placeholder="请选择" multiple collapse-tags style="width: 200px">
            <el-option label="严重" value="critical" />
            <el-option label="主要" value="major" />
            <el-option label="次要" value="minor" />
            <el-option label="建议" value="suggestion" />
          </el-select>
        </el-form-item>
        <el-form-item label="提交人">
          <el-input v-model="filterForm.author" placeholder="请输入提交人" clearable style="width: 150px" />
        </el-form-item>
        <el-form-item label="确认意见">
          <el-select v-model="filterForm.confirm_status" placeholder="请选择" clearable style="width: 120px">
            <el-option label="待处理" value="pending" />
            <el-option label="采纳" value="accepted" />
            <el-option label="不采纳" value="rejected" />
            <el-option label="忽略" value="ignored" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否已改">
          <el-select v-model="filterForm.is_fixed" placeholder="请选择" clearable style="width: 120px">
            <el-option label="已修改" :value="true" />
            <el-option label="未修改" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 问题表格 -->
      <el-table :data="issueData" stripe height="400">

        <el-table-column type="index" width="50" fixed="left" />
        <el-table-column prop="severity" label="严重程度" width="100" fixed="left">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ getSeverityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="提交人" width="100" />
        <el-table-column prop="file_path" label="文件" width="200" show-overflow-tooltip />
        <el-table-column prop="line_info" label="行号" width="80" />
        <el-table-column prop="method_name" label="方法" width="150" />
        <el-table-column prop="description" label="问题描述" width="300" />
        <el-table-column prop="suggestion" label="改进建议" width="300" />
        <el-table-column label="确认意见" width="140" fixed="right">
          <template #default="{ row }">
            <el-select 
              v-model="row.confirm_status" 
              size="small" 
              @change="handleUpdateIssue(row)"
              style="width: 100%"
            >
              <el-option label="待处理" value="pending" />
              <el-option label="采纳" value="accepted" />
              <el-option label="不采纳" value="rejected" />
              <el-option label="忽略" value="ignored" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="是否已改" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-switch 
              v-model="row.is_fixed" 
              @change="handleUpdateIssue(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="评审意见" width="200" fixed="right">
          <template #default="{ row }">
            <el-input 
              v-model="row.review_comment" 
              placeholder="添加评审意见"
              size="small"
              @blur="handleUpdateIssue(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewCodeSnippet(row)">查看代码</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 代码片段对话框 -->
    <el-dialog v-model="codeDialogVisible" title="代码片段" width="800px">
      <div v-if="currentCodeSnippet" class="code-snippet">
        <div class="code-header">
          <span>行号: {{ currentCodeSnippet.start_line }} - {{ currentCodeSnippet.end_line }}</span>
        </div>
        <div class="code-content">
          <div 
            v-for="(line, index) in currentCodeSnippet.lines" 
            :key="index"
            :class="['code-line', `line-${line.type}`]"
          >
            <span class="line-num">{{ line.line_num }}</span>
            <span class="line-mark">{{ getLineMark(line.type) }}</span>
            <span class="line-text">{{ line.content }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/review'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const sessionInfo = ref({})
const issueData = ref([])

const filterForm = reactive({
  severity: ['critical', 'major'],  // 默认筛选严重和主要
  author: '',
  confirm_status: '',
  is_fixed: ''
})

const pagination = reactive({
  page: 1,
  page_size: 50,
  total: 0
})

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const getSeverityType = (severity) => {
  const types = {
    critical: 'danger',
    major: 'warning',
    minor: 'info',
    suggestion: ''
  }
  return types[severity] || ''
}

const getSeverityLabel = (severity) => {
  const labels = {
    critical: '严重',
    major: '主要',
    minor: '次要',
    suggestion: '建议'
  }
  return labels[severity] || severity
}

// 模拟数据 - 评审信息
const mockSessionInfo = {
  review_branch: 'feature/new-ui',
  base_branch: 'main',
  review_time: '2025-12-29T15:30:00',
  total_issues: 27,
  total_files_reviewed: 15,
  total_commits: 10
}

// 模拟数据 - 问题列表
const mockIssues = {
  items: [
    {
      id: 1,
      severity: 'critical',
      author: '张三',
      file_path: 'src/review_engine.py',
      line_info: '45-50',
      method_name: 'analyze_code',
      description: '缺少异常处理机制',
      suggestion: '添加try-except块处理可能的异常',
      confirm_status: 'pending',
      is_fixed: false,
      review_comment: ''
    },
    {
      id: 2,
      severity: 'major',
      author: '李四',
      file_path: 'src/utils/string_utils.py',
      line_info: '23',
      method_name: 'format_string',
      description: '字符串格式化使用了不推荐的方法',
      suggestion: '使用f-strings替代传统格式化方法',
      confirm_status: 'accepted',
      is_fixed: true,
      review_comment: '已修复'
    },
    {
      id: 3,
      severity: 'minor',
      author: '张三',
      file_path: 'src/api/main.py',
      line_info: '120',
      method_name: 'create_api_router',
      description: '函数参数过多',
      suggestion: '考虑使用dataclass或字典封装参数',
      confirm_status: 'pending',
      is_fixed: false,
      review_comment: ''
    },
    {
      id: 4,
      severity: 'suggestion',
      author: '王五',
      file_path: 'src/templates/report.html',
      line_info: '56',
      method_name: 'render_report',
      description: 'HTML标签未闭合',
      suggestion: '检查并修复未闭合的HTML标签',
      confirm_status: 'rejected',
      is_fixed: false,
      review_comment: '不影响功能，暂时保留'
    },
    {
      id: 5,
      severity: 'critical',
      author: '李四',
      file_path: 'src/llm_client.py',
      line_info: '89-95',
      method_name: 'call_llm_api',
      description: '缺少超时控制',
      suggestion: '添加超时参数，防止API调用无限等待',
      confirm_status: 'pending',
      is_fixed: false,
      review_comment: ''
    },
    {
      id: 6,
      severity: 'major',
      author: '张三',
      file_path: 'src/gitlab_client.py',
      line_info: '34',
      method_name: 'get_project_info',
      description: '硬编码的API端点',
      suggestion: '将API端点配置化，便于维护',
      confirm_status: 'accepted',
      is_fixed: false,
      review_comment: '计划在下个版本修复'
    },
    {
      id: 7,
      severity: 'minor',
      author: '王五',
      file_path: 'src/formatters/excel_formatter.py',
      line_info: '156',
      method_name: 'write_summary',
      description: '魔法数值使用',
      suggestion: '将魔法数值定义为常量',
      confirm_status: 'pending',
      is_fixed: false,
      review_comment: ''
    },
    {
      id: 8,
      severity: 'suggestion',
      author: '李四',
      file_path: 'src/utils/file_utils.py',
      line_info: '78',
      method_name: 'read_file_content',
      description: '文件读取模式未指定编码',
      suggestion: '添加encoding参数，确保跨平台兼容性',
      confirm_status: 'pending',
      is_fixed: false,
      review_comment: ''
    },
    {
      id: 9,
      severity: 'major',
      author: '张三',
      file_path: 'src/report_generator.py',
      line_info: '201-210',
      method_name: 'generate_html_report',
      description: 'HTML模板渲染逻辑复杂',
      suggestion: '将渲染逻辑拆分为多个子函数',
      confirm_status: 'pending',
      is_fixed: false,
      review_comment: ''
    },
    {
      id: 10,
      severity: 'minor',
      author: '王五',
      file_path: 'src/config.py',
      line_info: '45',
      method_name: 'load_config',
      description: '配置文件路径硬编码',
      suggestion: '支持通过命令行参数指定配置文件路径',
      confirm_status: 'pending',
      is_fixed: false,
      review_comment: ''
    }
  ],
  total: 10
}

const loadSessionInfo = async () => {
  try {
    // 使用模拟数据替代真实API调用
    sessionInfo.value = mockSessionInfo
  } catch (error) {
    ElMessage.error('加载评审信息失败')
    console.error(error)
  }
}

const loadIssues = async () => {
  loading.value = true
  try {
    // 使用模拟数据替代真实API调用
    issueData.value = mockIssues.items
    pagination.total = mockIssues.total
  } catch (error) {
    ElMessage.error('加载问题列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadIssues()
}

const handleReset = () => {
  filterForm.severity = ['critical', 'major']
  filterForm.author = ''
  filterForm.confirm_status = ''
  filterForm.is_fixed = ''
  pagination.page = 1
  loadIssues()
}

const handleUpdateIssue = async (row) => {
  try {
    await api.updateIssue(row.id, {
      confirm_status: row.confirm_status,
      is_fixed: row.is_fixed,
      review_comment: row.review_comment
    })
    ElMessage.success('更新成功')
  } catch (error) {
    ElMessage.error('更新失败')
    console.error(error)
    // 重新加载以恢复原值
    loadIssues()
  }
}

const codeDialogVisible = ref(false)
const currentCodeSnippet = ref(null)

const viewCodeSnippet = (row) => {
  if (row.code_snippet_json) {
    try {
      currentCodeSnippet.value = typeof row.code_snippet_json === 'string' 
        ? JSON.parse(row.code_snippet_json) 
        : row.code_snippet_json
      codeDialogVisible.value = true
    } catch (error) {
      ElMessage.error('代码片段解析失败')
    }
  } else {
    ElMessage.warning('该问题没有代码片段')
  }
}

const handleSizeChange = () => {
  pagination.page = 1
  loadIssues()
}

const handlePageChange = () => {
  loadIssues()
}

const goBack = () => {
  router.back()
}

const getLineMark = (type) => {
  const marks = {
    added: '+',
    deleted: '-',
    context: ' '
  }
  return marks[type] || ' '
}

onMounted(() => {
  loadSessionInfo()
  loadIssues()
})
</script>

<style scoped>
.review-detail {
  margin: 0 auto;
}

.filter-form {
  margin-bottom: 20px;
}

.code-snippet {
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.code-header {
  background-color: #f5f7fa;
  padding: 10px;
  border-bottom: 1px solid #dcdfe6;
  font-weight: bold;
}

.code-content {
  max-height: 500px;
  overflow-y: auto;
  background-color: #fafafa;
}

.code-line {
  display: flex;
  padding: 2px 10px;
  line-height: 20px;
}

.code-line.line-added {
  background-color: #e6ffed;
}

.code-line.line-deleted {
  background-color: #ffebe9;
}

.line-num {
  width: 60px;
  text-align: right;
  color: #999;
  margin-right: 10px;
  flex-shrink: 0;
}

.line-mark {
  width: 20px;
  text-align: center;
  margin-right: 10px;
  flex-shrink: 0;
  font-weight: bold;
}

.line-added .line-mark {
  color: #22863a;
}

.line-deleted .line-mark {
  color: #cb2431;
}

.line-text {
  flex: 1;
  white-space: pre;
}
</style>
