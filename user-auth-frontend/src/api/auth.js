import http from './http'

export const authAPI = {
  // 用户注册
  register(userData) {
    return http.post('/auth/register', userData)
  },

  // 用户登录 (JSON格式)
  login(credentials) {
    return http.post('/auth/login/json', credentials)
  },

  // 用户登录 (表单格式)
  loginForm(credentials) {
    const formData = new FormData()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)
    
    return http.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },

  // 获取当前用户信息
  getCurrentUser() {
    return http.get('/users/me')
  },

  // 更新当前用户信息
  updateCurrentUser(userData) {
    return http.put('/users/me', userData)
  },
}