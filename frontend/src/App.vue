<template>
  <div id="app">
    <el-container style="height: 100vh">
      <!-- 顶部导航栏 -->
      <el-header style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; display: flex; align-items: center; padding: 0 20px; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3)">
        <div style="display: flex; align-items: center; flex: 1">
          <el-icon :size="24" style="margin-right: 10px"><Document /></el-icon>
          <h2 style="margin: 0">代码评审系统</h2>
        </div>
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          background-color="#545c64"
          text-color="#fff"
          active-text-color="#ffd04b"
          router
          style="flex: 1; border: none"
        >
          <el-menu-item index="/">评审列表</el-menu-item>
        </el-menu>
      </el-header>

      <!-- 主内容区 -->
      <el-main style="padding: 20px; background-color: #f0f2f5">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Document } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = ref('/')

watch(
  () => route.path,
  (newPath) => {
    if (newPath.startsWith('/reviews/')) {
      activeMenu.value = '/'
    } else {
      activeMenu.value = newPath
    }
  },
  { immediate: true }
)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
}
</style>
