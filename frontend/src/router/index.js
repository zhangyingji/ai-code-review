import { createRouter, createWebHistory } from 'vue-router'
import ReviewList from '../views/ReviewList.vue'
import ReviewDetail from '../views/ReviewDetail.vue'

const routes = [
  {
    path: '/',
    name: 'ReviewList',
    component: ReviewList
  },
  {
    path: '/reviews/:id',
    name: 'ReviewDetail',
    component: ReviewDetail
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
