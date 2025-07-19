<template>
  <div class="dashboard">
    <div class="welcome-section">
      <el-card class="welcome-card">
        <div class="welcome-content">
          <div class="welcome-text">
            <h1>欢迎回来，{{ authStore.user?.full_name || authStore.user?.username }}！</h1>
            <p>今天是 {{ currentDate }}，祝您工作愉快！</p>
          </div>
          <div class="welcome-avatar">
            <el-avatar :size="80">
              <el-icon><User /></el-icon>
            </el-avatar>
          </div>
        </div>
      </el-card>
    </div>

    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-icon user-icon">
                <el-icon><User /></el-icon>
              </div>
              <div class="stats-content">
                <div class="stats-number">{{ userStats.totalUsers }}</div>
                <div class="stats-label">总用户数</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-icon online-icon">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="stats-content">
                <div class="stats-number">{{ userStats.onlineUsers }}</div>
                <div class="stats-label">在线用户</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-icon role-icon">
                <el-icon><Key /></el-icon>
              </div>
              <div class="stats-content">
                <div class="stats-number">{{ userStats.totalRoles }}</div>
                <div class="stats-label">角色数量</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-icon login-icon">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="stats-content">
                <div class="stats-number">{{ userStats.todayLogins }}</div>
                <div class="stats-label">今日登录</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="info-section">
      <el-row :gutter="20">
        <el-col :xs="24" :md="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>个人信息</span>
                <el-button type="primary" text @click="$router.push('/profile')">
                  编辑资料
                </el-button>
              </div>
            </template>
            
            <div class="user-info">
              <div class="info-item">
                <strong>用户名：</strong>
                <span>{{ authStore.user?.username }}</span>
              </div>
              <div class="info-item">
                <strong>邮箱：</strong>
                <span>{{ authStore.user?.email }}</span>
              </div>
              <div class="info-item">
                <strong>真实姓名：</strong>
                <span>{{ authStore.user?.full_name || '未设置' }}</span>
              </div>
              <div class="info-item">
                <strong>账户状态：</strong>
                <el-tag :type="authStore.user?.is_active ? 'success' : 'danger'">
                  {{ authStore.user?.is_active ? '激活' : '未激活' }}
                </el-tag>
              </div>
              <div class="info-item">
                <strong>用户角色：</strong>
                <div class="role-tags">
                  <el-tag
                    v-for="role in authStore.user?.roles"
                    :key="role.id"
                    type="info"
                    size="small"
                  >
                    {{ role.name }}
                  </el-tag>
                  <el-tag v-if="authStore.user?.is_superuser" type="warning" size="small">
                    超级管理员
                  </el-tag>
                </div>
              </div>
              <div class="info-item">
                <strong>注册时间：</strong>
                <span>{{ formatDate(authStore.user?.created_at) }}</span>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="12">
          <el-card>
            <template #header>
              <span>快捷操作</span>
            </template>
            
            <div class="quick-actions">
              <el-button 
                type="primary" 
                @click="$router.push('/profile')"
                class="action-btn"
              >
                <el-icon><Edit /></el-icon>
                修改个人信息
              </el-button>
              
              <el-button 
                v-if="authStore.isAdmin"
                type="success" 
                @click="$router.push('/admin/users')"
                class="action-btn"
              >
                <el-icon><UserFilled /></el-icon>
                用户管理
              </el-button>
              
              <el-button 
                v-if="authStore.isAdmin"
                type="warning" 
                @click="$router.push('/admin/roles')"
                class="action-btn"
              >
                <el-icon><Key /></el-icon>
                角色管理
              </el-button>
              
              <el-button 
                type="info" 
                @click="refreshData"
                class="action-btn"
                :loading="loading"
              >
                <el-icon><Refresh /></el-icon>
                刷新数据
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usersAPI } from '@/api/users'
import { rolesAPI } from '@/api/roles'

const authStore = useAuthStore()
const loading = ref(false)

const userStats = reactive({
  totalUsers: 0,
  onlineUsers: 0,
  totalRoles: 0,
  todayLogins: 0
})

const currentDate = computed(() => {
  return new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const fetchStats = async () => {
  try {
    loading.value = true
    
    // 获取统计数据（这里模拟数据，实际应该从API获取）
    if (authStore.isManager) {
      const users = await usersAPI.getUsers({ limit: 1000 })
      const roles = await rolesAPI.getRoles({ limit: 1000 })
      
      userStats.totalUsers = users.length
      userStats.totalRoles = roles.length
      userStats.onlineUsers = Math.floor(Math.random() * users.length) + 1
      userStats.todayLogins = Math.floor(Math.random() * 50) + 10
    } else {
      // 普通用户只能看到一些基本统计
      userStats.totalUsers = '***'
      userStats.totalRoles = '***'
      userStats.onlineUsers = '***'
      userStats.todayLogins = '***'
    }
  } catch (error) {
    console.error('Failed to fetch stats:', error)
    // 设置默认值
    userStats.totalUsers = '***'
    userStats.totalRoles = '***'
    userStats.onlineUsers = '***'
    userStats.todayLogins = '***'
  } finally {
    loading.value = false
  }
}

const refreshData = async () => {
  await Promise.all([
    authStore.fetchUserProfile(),
    fetchStats()
  ])
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.welcome-section {
  margin-bottom: 20px;
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
}

:deep(.welcome-card .el-card__body) {
  padding: 30px;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-text h1 {
  font-size: 28px;
  margin-bottom: 8px;
  font-weight: 600;
}

.welcome-text p {
  font-size: 16px;
  opacity: 0.9;
}

.stats-section {
  margin-bottom: 20px;
}

.stats-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.stats-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.user-icon {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.online-icon {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.role-icon {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.login-icon {
  background: linear-gradient(135deg, #43e97b, #38f9d7);
}

.stats-content {
  flex: 1;
}

.stats-number {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  line-height: 1;
}

.stats-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.info-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-info {
  space-y: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  line-height: 1.6;
}

.info-item strong {
  min-width: 100px;
  color: #333;
}

.info-item span {
  color: #666;
}

.role-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-actions {
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr;
}

.action-btn {
  justify-content: flex-start;
  padding: 12px 16px;
  height: auto;
}

@media (max-width: 768px) {
  .welcome-content {
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }
  
  .stats-section {
    margin-bottom: 16px;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>