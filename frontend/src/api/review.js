import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  // 获取评审列表
  getReviews(params) {
    return api.get('/reviews', { params })
  },
  
  // 获取评审详情
  getReviewDetail(id) {
    return api.get(`/reviews/${id}`)
  },
  
  // 获取问题列表
  getIssues(sessionId, params) {
    return api.get(`/reviews/${sessionId}/issues`, { params })
  },
  
  // 更新问题
  updateIssue(issueId, data) {
    return api.put(`/issues/${issueId}`, data)
  },
  
  // 批量更新问题
  batchUpdateIssues(data) {
    return api.put('/issues/batch', data)
  },
  
  // 获取统计数据
  getStatistics(params) {
    return api.get('/statistics/overview', { params })
  }
}
