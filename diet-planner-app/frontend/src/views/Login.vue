<template>
  <div class="login-container">
    <el-card class="login-card">
      <div class="login-header">
        <h1>减肥日程计划</h1>
        <p>使用Microsoft账号登录，开始您的健康之旅</p>
      </div>
      
      <div class="login-content">
        <el-button 
          type="primary" 
          size="large" 
          @click="login"
          :loading="loading"
          class="login-btn"
        >
          <el-icon><User /></el-icon>
          使用Microsoft账号登录
        </el-button>
        
        <div class="features">
          <div class="feature-item">
            <el-icon><TrendCharts /></el-icon>
            <span>体重追踪</span>
          </div>
          <div class="feature-item">
            <el-icon><Food /></el-icon>
            <span>饮食记录</span>
          </div>
          <div class="feature-item">
            <el-icon><Trophy /></el-icon>
            <span>运动管理</span>
          </div>
          <div class="feature-item">
            <el-icon><Calendar /></el-icon>
            <span>计划制定</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { User, TrendCharts, Food, Trophy, Calendar } from '@element-plus/icons-vue'

const loading = ref(false)

const login = () => {
  loading.value = true
  // 重定向到后端登录端点
  window.location.href = '/auth/login'
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #303133;
  margin-bottom: 10px;
  font-size: 28px;
  font-weight: 600;
}

.login-header p {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
}

.login-content {
  text-align: center;
}

.login-btn {
  width: 100%;
  height: 50px;
  font-size: 16px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  color: #606266;
}

.feature-item .el-icon {
  font-size: 24px;
  color: #409eff;
}

.feature-item span {
  font-size: 12px;
  font-weight: 500;
}
</style>