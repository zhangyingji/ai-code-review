<template>
  <div class="review-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>评审列表</span>
        </div>
      </template>

      <!-- 筛选区 -->
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="项目名称">
          <el-input v-model="filterForm.project_name" placeholder="请输入项目名称" clearable />
        </el-form-item>
        <el-form-item label="评审分支">
          <el-input v-model="filterForm.review_branch" placeholder="请输入分支名" clearable />
        </el-form-item>
        <el-form-item label="基准分支">
          <el-input v-model="filterForm.base_branch" placeholder="请输入分支名" clearable />
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格区 -->
      <el-table :data="tableData" stripe v-loading="loading">
        <el-table-column prop="project_name" label="项目名称" width="150" />
        <el-table-column prop="review_branch" label="评审分支" width="180" />
        <el-table-column prop="base_branch" label="基准分支" width="150" />
        <el-table-column prop="review_time" label="评审时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.review_time) }}
          </template>
        </el-table-column>
        <el-table-column label="问题统计" width="280">
          <template #default="{ row }">
            <el-tag type="danger" size="small" v-if="row.severity_stats.critical > 0">
              严重: {{ row.severity_stats.critical }}
            </el-tag>
            <el-tag type="warning" size="small" v-if="row.severity_stats.major > 0">
              主要: {{ row.severity_stats.major }}
            </el-tag>
            <el-tag type="info" size="small" v-if="row.severity_stats.minor > 0">
              次要: {{ row.severity_stats.minor }}
            </el-tag>
            <el-tag size="small" v-if="row.severity_stats.suggestion > 0">
              建议: {{ row.severity_stats.suggestion }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_files_reviewed" label="评审文件数" width="120" align="center" />
        <el-table-column prop="total_issues" label="总问题数" width="120" align="center" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row.id)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页区 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../api/review'

const router = useRouter()

const loading = ref(false)
const tableData = ref([])
const dateRange = ref([])

const filterForm = reactive({
  project_name: '',
  review_branch: '',
  base_branch: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 格式化日期时间
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

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...filterForm
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await api.getReviews(params)
    tableData.value = res.items
    pagination.total = res.total
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 查询
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 重置
const handleReset = () => {
  Object.assign(filterForm, {
    project_name: '',
    review_branch: '',
    base_branch: ''
  })
  dateRange.value = []
  pagination.page = 1
  loadData()
}

// 分页变化
const handleSizeChange = () => {
  pagination.page = 1
  loadData()
}

const handlePageChange = () => {
  loadData()
}

// 查看详情
const viewDetail = (id) => {
  router.push({ name: 'ReviewDetail', params: { id } })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.review-list {
  max-width: 1400px;
  margin: 0 auto;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.filter-form {
  margin-bottom: 20px;
}

.el-tag {
  margin-right: 8px;
}
</style>
