import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import Cookies from 'js-cookie'
import { authAPI } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(Cookies.get('access_token') || null)
  const user = ref(null)
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => {
    if (!user.value) return false
    return user.value.is_superuser || user.value.roles?.some(role => role.name === 'admin')
  })
  const isManager = computed(() => {
    if (!user.value) return false
    return isAdmin.value || user.value.roles?.some(role => role.name === 'manager')
  })

  // 登录
  const login = async (credentials) => {
    try {
      loading.value = true
      const response = await authAPI.login(credentials)
      token.value = response.access_token
      
      // 保存token到cookie
      Cookies.set('access_token', response.access_token, { expires: 1 }) // 1天过期
      
      // 获取用户信息
      await fetchUserProfile()
      
      return { success: true }
    } catch (error) {
      console.error('Login error:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败'
      }
    } finally {
      loading.value = false
    }
  }

  // 注册
  const register = async (userData) => {
    try {
      loading.value = true
      await authAPI.register(userData)
      return { success: true }
    } catch (error) {
      console.error('Register error:', error)
      return {
        success: false,
        message: error.response?.data?.detail || '注册失败'
      }
    } finally {
      loading.value = false
    }
  }

  // 获取用户信息
  const fetchUserProfile = async () => {
    try {
      const userData = await authAPI.getCurrentUser()
      user.value = userData
    } catch (error) {
      console.error('Fetch user profile error:', error)
      // 如果获取用户信息失败，可能token已过期
      logout()
    }
  }

  // 登出
  const logout = () => {
    token.value = null
    user.value = null
    Cookies.remove('access_token')
  }

  // 初始化（检查token有效性）
  const initialize = async () => {
    if (token.value) {
      try {
        await fetchUserProfile()
      } catch (error) {
        // Token可能已过期
        logout()
      }
    }
  }

  return {
    // 状态
    token,
    user,
    loading,
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    isManager,
    
    // 方法
    login,
    register,
    logout,
    fetchUserProfile,
    initialize
  }
})