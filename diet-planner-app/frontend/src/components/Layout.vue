<template>
  <el-container class="app-container">
    <!-- 侧边栏 -->
    <el-aside width="250px" class="sidebar">
      <div class="logo">
        <h2>减肥计划</h2>
      </div>
      
      <el-menu
        :default-active="$route.path"
        router
        class="sidebar-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表板</span>
        </el-menu-item>
        
        <el-menu-item index="/diet-plans">
          <el-icon><Calendar /></el-icon>
          <span>减肥计划</span>
        </el-menu-item>
        
        <el-menu-item index="/meals">
          <el-icon><Food /></el-icon>
          <span>饮食记录</span>
        </el-menu-item>
        
        <el-menu-item index="/exercises">
          <el-icon><Trophy /></el-icon>
          <span>运动记录</span>
        </el-menu-item>
        
        <el-menu-item index="/weight-tracking">
          <el-icon><TrendCharts /></el-icon>
          <span>体重追踪</span>
        </el-menu-item>
        
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <span>个人资料</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 主内容区域 -->
    <el-container class="main-container">
      <!-- 顶部导航栏 -->
      <el-header class="header">
        <div class="header-left">
          <h3>{{ pageTitle }}</h3>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="userAvatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ user?.name || '用户' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人资料
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容 -->
      <el-main class="main-content">
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { 
  Odometer, Calendar, Food, Trophy, TrendCharts, User, 
  ArrowDown, SwitchButton 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const user = computed(() => authStore.user)
const userAvatar = computed(() => user.value?.avatar || '')

const pageTitle = computed(() => {
  const routeMap = {
    '/dashboard': '仪表板',
    '/diet-plans': '减肥计划',
    '/meals': '饮食记录',
    '/exercises': '运动记录',
    '/weight-tracking': '体重追踪',
    '/profile': '个人资料'
  }
  return routeMap[router.currentRoute.value.path] || '减肥计划'
})

const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'logout':
      try {
        await ElMessageBox.confirm(
          '确定要退出登录吗？',
          '确认退出',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        authStore.logout()
        ElMessage.success('已退出登录')
        router.push('/login')
      } catch {
        // 用户取消
      }
      break
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  overflow: hidden;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #434a5a;
}

.logo h2 {
  color: #fff;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.sidebar-menu {
  border: none;
}

.main-container {
  background-color: #f0f2f5;
}

.header {
  background-color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.header-left h3 {
  margin: 0;
  color: #303133;
  font-size: 18px;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #606266;
}

.main-content {
  padding: 24px;
  overflow-y: auto;
}
</style>