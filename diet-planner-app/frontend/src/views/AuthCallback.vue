<template>
  <div class="callback-container">
    <el-card class="callback-card">
      <div v-if="loading" class="loading-content">
        <el-icon class="loading-icon">
          <Loading />
        </el-icon>
        <h3>正在登录...</h3>
        <p>请稍候，我们正在验证您的身份</p>
      </div>
      
      <div v-else-if="error" class="error-content">
        <el-icon class="error-icon">
          <Warning />
        </el-icon>
        <h3>登录失败</h3>
        <p>{{ error }}</p>
        <el-button type="primary" @click="goToLogin">重新登录</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Loading, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const token = route.query.token
    
    if (!token) {
      throw new Error('未收到认证令牌')
    }
    
    // 处理认证回调
    await authStore.handleAuthCallback(token)
    
    ElMessage.success('登录成功！')
    
    // 跳转到仪表板
    router.replace('/dashboard')
    
  } catch (err) {
    console.error('Auth callback error:', err)
    error.value = err.message || '登录过程中发生错误'
    loading.value = false
  }
})

const goToLogin = () => {
  router.replace('/login')
}
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.callback-card {
  width: 100%;
  max-width: 400px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.loading-content,
.error-content {
  text-align: center;
  padding: 20px;
}

.loading-icon,
.error-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.loading-icon {
  color: #409eff;
  animation: spin 1s linear infinite;
}

.error-icon {
  color: #f56c6c;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

h3 {
  color: #303133;
  margin-bottom: 10px;
  font-size: 20px;
}

p {
  color: #606266;
  margin-bottom: 20px;
  line-height: 1.6;
}
</style>