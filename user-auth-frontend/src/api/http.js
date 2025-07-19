import axios from 'axios'
import Cookies from 'js-cookie'
import { ElMessage } from 'element-plus'

// 创建axios实例
const http = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
http.interceptors.request.use(
  (config) => {
    // 添加token到请求头
    const token = Cookies.get('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('Response error:', error)
    
    // 处理认证错误
    if (error.response?.status === 401) {
      // Token过期或无效，清除登录状态
      Cookies.remove('access_token')
      ElMessage.error('登录已过期，请重新登录')
      // 重定向到登录页
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else if (error.response?.status === 403) {
      ElMessage.error('权限不足')
    } else if (error.response?.status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

export default http