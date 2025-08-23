<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1>页面未找到</h1>
      <p>抱歉，您访问的页面不存在</p>
      <el-button type="primary" @click="goHome">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.not-found-content {
  text-align: center;
  color: white;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  margin-bottom: 20px;
  opacity: 0.8;
}

h1 {
  font-size: 36px;
  margin-bottom: 16px;
  font-weight: 600;
}

p {
  font-size: 18px;
  margin-bottom: 32px;
  opacity: 0.9;
}
</style>