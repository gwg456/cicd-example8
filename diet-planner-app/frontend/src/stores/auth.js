import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value)

  // 设置axios默认headers
  const setAuthHeader = (authToken) => {
    if (authToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`
      localStorage.setItem('token', authToken)
    } else {
      delete axios.defaults.headers.common['Authorization']
      localStorage.removeItem('token')
    }
  }

  // 检查认证状态
  const checkAuth = async () => {
    if (!token.value) return false

    try {
      setAuthHeader(token.value)
      const response = await axios.get('/auth/verify')
      if (response.data.valid) {
        await fetchUser()
        return true
      } else {
        logout()
        return false
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      logout()
      return false
    }
  }

  // 获取用户信息
  const fetchUser = async () => {
    try {
      const response = await axios.get('/auth/user')
      user.value = response.data
    } catch (error) {
      console.error('Failed to fetch user:', error)
      throw error
    }
  }

  // 处理登录回调
  const handleAuthCallback = (authToken) => {
    token.value = authToken
    setAuthHeader(authToken)
    return fetchUser()
  }

  // 登出
  const logout = () => {
    token.value = null
    user.value = null
    setAuthHeader(null)
  }

  // 更新用户信息
  const updateUser = async (userData) => {
    try {
      await axios.put('/auth/user', userData)
      await fetchUser() // 重新获取用户信息
    } catch (error) {
      console.error('Failed to update user:', error)
      throw error
    }
  }

  // 初始化时设置认证头
  if (token.value) {
    setAuthHeader(token.value)
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    checkAuth,
    fetchUser,
    handleAuthCallback,
    logout,
    updateUser
  }
})