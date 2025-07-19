<template>
  <div class="roles-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>角色管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新增角色
          </el-button>
        </div>
      </template>

      <!-- 角色表格 -->
      <el-table
        v-loading="loading"
        :data="roles"
        style="width: 100%"
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="角色名称" min-width="120" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="用户数量" width="120">
          <template #default="{ row }">
            <el-tag type="info">{{ getUserCount(row.id) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="handleViewUsers(row)"
            >
              用户
            </el-button>
            <el-button
              v-if="!isSystemRole(row.name)"
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchRoles"
          @current-change="fetchRoles"
        />
      </div>
    </el-card>

    <!-- 创建/编辑角色对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEdit ? '编辑角色' : '新增角色'"
      width="500px"
    >
      <el-form
        ref="roleFormRef"
        :model="roleForm"
        :rules="roleRules"
        label-width="100px"
      >
        <el-form-item label="角色名称" prop="name">
          <el-input
            v-model="roleForm.name"
            placeholder="请输入角色名称"
            :disabled="isEdit && isSystemRole(selectedRole?.name)"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="roleForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitLoading"
          @click="handleSubmit"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看角色用户对话框 -->
    <el-dialog
      v-model="showUsersDialog"
      :title="`角色用户 - ${selectedRole?.name}`"
      width="600px"
    >
      <div v-if="selectedRole">
        <el-table
          :data="roleUsers"
          style="width: 100%"
          max-height="400"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column prop="email" label="邮箱" min-width="180" />
          <el-table-column prop="full_name" label="真实姓名" min-width="120" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '激活' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <div v-if="roleUsers.length === 0" class="empty-state">
          <el-empty description="该角色暂无用户" />
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showUsersDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { rolesAPI } from '@/api/roles'
import { usersAPI } from '@/api/users'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const submitLoading = ref(false)
const showCreateDialog = ref(false)
const showUsersDialog = ref(false)
const isEdit = ref(false)
const selectedRole = ref(null)

const roles = ref([])
const users = ref([])
const roleUsers = ref([])

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const roleForm = reactive({
  name: '',
  description: ''
})

const roleFormRef = ref()

const roleRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 255, message: '描述不能超过 255 个字符', trigger: 'blur' }
  ]
}

// 系统角色不能删除或修改名称
const systemRoles = ['admin', 'manager', 'user']

const isSystemRole = (roleName) => {
  return systemRoles.includes(roleName)
}

const getUserCount = (roleId) => {
  return users.value.filter(user => 
    user.roles.some(role => role.id === roleId)
  ).length
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const fetchRoles = async () => {
  try {
    loading.value = true
    const params = {
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize
    }
    
    const data = await rolesAPI.getRoles(params)
    roles.value = data
    pagination.total = data.length // 实际应该从API返回总数
  } catch (error) {
    console.error('Failed to fetch roles:', error)
    ElMessage.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

const fetchUsers = async () => {
  try {
    const data = await usersAPI.getUsers({ limit: 1000 })
    users.value = data
  } catch (error) {
    console.error('Failed to fetch users:', error)
  }
}

const handleEdit = (role) => {
  isEdit.value = true
  selectedRole.value = role
  Object.assign(roleForm, {
    name: role.name,
    description: role.description || ''
  })
  showCreateDialog.value = true
}

const handleDelete = async (role) => {
  try {
    const userCount = getUserCount(role.id)
    if (userCount > 0) {
      ElMessage.error(`无法删除角色，还有 ${userCount} 个用户正在使用此角色`)
      return
    }
    
    await ElMessageBox.confirm(
      `确定要删除角色 "${role.name}" 吗？`,
      '警告',
      { type: 'warning' }
    )
    
    await rolesAPI.deleteRole(role.id)
    ElMessage.success('删除成功')
    fetchRoles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete role error:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleViewUsers = (role) => {
  selectedRole.value = role
  roleUsers.value = users.value.filter(user => 
    user.roles.some(userRole => userRole.id === role.id)
  )
  showUsersDialog.value = true
}

const handleSubmit = async () => {
  if (!roleFormRef.value) return

  try {
    await roleFormRef.value.validate()
    
    submitLoading.value = true
    
    if (isEdit.value) {
      await rolesAPI.updateRole(selectedRole.value.id, roleForm)
      ElMessage.success('角色更新成功')
    } else {
      await rolesAPI.createRole(roleForm)
      ElMessage.success('角色创建成功')
    }
    
    showCreateDialog.value = false
    fetchRoles()
    resetForm()
  } catch (error) {
    console.error('Submit role error:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  Object.assign(roleForm, {
    name: '',
    description: ''
  })
  isEdit.value = false
  selectedRole.value = null
  roleFormRef.value?.clearValidate()
}

onMounted(() => {
  fetchRoles()
  fetchUsers()
})
</script>

<style scoped>
.roles-management {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.empty-state {
  padding: 20px;
  text-align: center;
}

:deep(.el-table .el-button + .el-button) {
  margin-left: 8px;
}
</style>