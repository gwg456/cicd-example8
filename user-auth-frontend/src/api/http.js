import axios from 'axios'
import Cookies from 'js-cookie'
import { ElMessage } from 'element-plus'

// 获取API基础URL
const getBaseURL = () => {
  // 开发环境使用代理，生产环境使用环境变量或默认值
  if (import.meta.env.DEV) {
    return '/api/v1'
  }
  
  // 生产环境从环境变量获取，或使用当前域名
  return import.meta.env.VITE_API_BASE_URL 
    ? `${import.meta.env.VITE_API_BASE_URL}/api/v1`
    : `${window.location.origin}/api/v1`
}

// 创建axios实例
const http = axios.create({
  baseURL: getBaseURL(),
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
    
    // 开发环境日志
    if (import.meta.env.DEV) {
      console.log('🚀 API Request:', config.method?.toUpperCase(), config.url, config.data)
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
    // 开发环境日志
    if (import.meta.env.DEV) {
      console.log('✅ API Response:', response.config.url, response.data)
    }
    
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
    } else if (error.response?.status === 0 || error.code === 'NETWORK_ERROR') {
      ElMessage.error('网络连接失败，请检查网络')
    }
    
    return Promise.reject(error)
  }
)

// 导出基础URL供其他地方使用
export const API_BASE_URL = getBaseURL()

export default http