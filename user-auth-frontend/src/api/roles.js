import http from './http'

export const rolesAPI = {
  // 获取角色列表
  getRoles(params = {}) {
    return http.get('/roles', { params })
  },

  // 获取指定角色信息
  getRole(roleId) {
    return http.get(`/roles/${roleId}`)
  },

  // 创建角色
  createRole(roleData) {
    return http.post('/roles', roleData)
  },

  // 更新角色
  updateRole(roleId, roleData) {
    return http.put(`/roles/${roleId}`, roleData)
  },

  // 删除角色
  deleteRole(roleId) {
    return http.delete(`/roles/${roleId}`)
  },
}