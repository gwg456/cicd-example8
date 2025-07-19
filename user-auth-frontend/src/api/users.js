import http from './http'

export const usersAPI = {
  // 获取用户列表
  getUsers(params = {}) {
    return http.get('/users', { params })
  },

  // 获取指定用户信息
  getUser(userId) {
    return http.get(`/users/${userId}`)
  },

  // 更新用户信息
  updateUser(userId, userData) {
    return http.put(`/users/${userId}`, userData)
  },

  // 删除用户
  deleteUser(userId) {
    return http.delete(`/users/${userId}`)
  },

  // 为用户分配角色
  assignRole(userId, roleId) {
    return http.post(`/users/${userId}/roles/${roleId}`)
  },

  // 移除用户角色
  removeRole(userId, roleId) {
    return http.delete(`/users/${userId}/roles/${roleId}`)
  },
}