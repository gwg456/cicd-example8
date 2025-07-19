import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import router from './router'
import { API_BASE_URL } from './api/http'

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

// 开发环境信息
if (import.meta.env.DEV) {
  console.log('🚀 用户认证系统 - 开发环境')
  console.log('📡 API Base URL:', API_BASE_URL)
  console.log('🏷️ App Version:', import.meta.env.VITE_APP_VERSION)
  console.log('🔧 Vite Mode:', import.meta.env.MODE)
}

app.mount('#app')