<template>
  <div class="users-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新增用户
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-form :inline="true" :model="searchForm" class="search-form">
          <el-form-item label="用户名">
            <el-input
              v-model="searchForm.username"
              placeholder="请输入用户名"
              clearable
            />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input
              v-model="searchForm.email"
              placeholder="请输入邮箱"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 用户表格 -->
      <el-table
        v-loading="loading"
        :data="users"
        style="width: 100%"
        border
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
        <el-table-column label="角色" min-width="150">
          <template #default="{ row }">
            <div class="role-tags">
              <el-tag
                v-for="role in row.roles"
                :key="role.id"
                type="info"
                size="small"
              >
                {{ role.name }}
              </el-tag>
              <el-tag v-if="row.is_superuser" type="warning" size="small">
                超级管理员
              </el-tag>
            </div>
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
              type="warning"
              size="small"
              @click="handleManageRoles(row)"
            >
              角色
            </el-button>
            <el-button
              v-if="row.id !== authStore.user?.id"
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
          @size-change="fetchUsers"
          @current-change="fetchUsers"
        />
      </div>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="600px"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="userForm.email"
            placeholder="请输入邮箱地址"
          />
        </el-form-item>
        <el-form-item label="真实姓名" prop="full_name">
          <el-input
            v-model="userForm.full_name"
            placeholder="请输入真实姓名"
          />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="userForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="账户状态">
          <el-switch
            v-model="userForm.is_active"
            active-text="激活"
            inactive-text="禁用"
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

    <!-- 角色管理对话框 -->
    <el-dialog
      v-model="showRoleDialog"
      title="角色管理"
      width="500px"
    >
      <div v-if="selectedUser">
        <h4>用户：{{ selectedUser.username }}</h4>
        <p>当前角色：</p>
        <div class="current-roles">
          <el-tag
            v-for="role in selectedUser.roles"
            :key="role.id"
            type="info"
            closable
            @close="removeRole(selectedUser.id, role.id)"
          >
            {{ role.name }}
          </el-tag>
        </div>
        
        <el-divider />
        
        <p>可分配角色：</p>
        <div class="available-roles">
          <el-tag
            v-for="role in availableRoles"
            :key="role.id"
            type="success"
            style="cursor: pointer; margin: 4px;"
            @click="assignRole(selectedUser.id, role.id)"
          >
            + {{ role.name }}
          </el-tag>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showRoleDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { usersAPI } from '@/api/users'
import { rolesAPI } from '@/api/roles'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const loading = ref(false)
const submitLoading = ref(false)
const showCreateDialog = ref(false)
const showRoleDialog = ref(false)
const isEdit = ref(false)
const selectedUser = ref(null)

const users = ref([])
const roles = ref([])

const searchForm = reactive({
  username: '',
  email: ''
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

const userForm = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  is_active: true
})

const userFormRef = ref()

const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }
  ],
  full_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' }
  ]
}

const availableRoles = computed(() => {
  if (!selectedUser.value || !roles.value) return []
  const userRoleIds = selectedUser.value.roles.map(r => r.id)
  return roles.value.filter(role => !userRoleIds.includes(role.id))
})

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const fetchUsers = async () => {
  try {
    loading.value = true
    const params = {
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize
    }
    
    const data = await usersAPI.getUsers(params)
    users.value = data
    pagination.total = data.length // 实际应该从API返回总数
  } catch (error) {
    console.error('Failed to fetch users:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const fetchRoles = async () => {
  try {
    const data = await rolesAPI.getRoles()
    roles.value = data
  } catch (error) {
    console.error('Failed to fetch roles:', error)
  }
}

const handleSearch = () => {
  pagination.current = 1
  fetchUsers()
}

const handleReset = () => {
  searchForm.username = ''
  searchForm.email = ''
  handleSearch()
}

const handleEdit = (user) => {
  isEdit.value = true
  Object.assign(userForm, {
    username: user.username,
    email: user.email,
    full_name: user.full_name,
    is_active: user.is_active
  })
  selectedUser.value = user
  showCreateDialog.value = true
}

const handleDelete = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？`,
      '警告',
      { type: 'warning' }
    )
    
    await usersAPI.deleteUser(user.id)
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete user error:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleManageRoles = (user) => {
  selectedUser.value = user
  showRoleDialog.value = true
}

const assignRole = async (userId, roleId) => {
  try {
    await usersAPI.assignRole(userId, roleId)
    ElMessage.success('角色分配成功')
    fetchUsers()
    
    // 更新选中用户的角色
    const user = users.value.find(u => u.id === userId)
    const role = roles.value.find(r => r.id === roleId)
    if (user && role) {
      user.roles.push(role)
      selectedUser.value = user
    }
  } catch (error) {
    console.error('Assign role error:', error)
    ElMessage.error('角色分配失败')
  }
}

const removeRole = async (userId, roleId) => {
  try {
    await usersAPI.removeRole(userId, roleId)
    ElMessage.success('角色移除成功')
    fetchUsers()
    
    // 更新选中用户的角色
    const user = users.value.find(u => u.id === userId)
    if (user) {
      user.roles = user.roles.filter(r => r.id !== roleId)
      selectedUser.value = user
    }
  } catch (error) {
    console.error('Remove role error:', error)
    ElMessage.error('角色移除失败')
  }
}

const handleSubmit = async () => {
  if (!userFormRef.value) return

  try {
    await userFormRef.value.validate()
    
    submitLoading.value = true
    
    if (isEdit.value) {
      await usersAPI.updateUser(selectedUser.value.id, userForm)
      ElMessage.success('用户更新成功')
    } else {
      await usersAPI.createUser(userForm)
      ElMessage.success('用户创建成功')
    }
    
    showCreateDialog.value = false
    fetchUsers()
    resetForm()
  } catch (error) {
    console.error('Submit user error:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  Object.assign(userForm, {
    username: '',
    email: '',
    full_name: '',
    password: '',
    is_active: true
  })
  isEdit.value = false
  selectedUser.value = null
  userFormRef.value?.clearValidate()
}

onMounted(() => {
  fetchUsers()
  fetchRoles()
})
</script>

<style scoped>
.users-management {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.search-form {
  margin: 0;
}

.role-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.current-roles,
.available-roles {
  margin: 10px 0;
  min-height: 40px;
  padding: 10px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
}

.available-roles .el-tag {
  margin: 4px;
}

@media (max-width: 768px) {
  .search-form {
    display: block;
  }
  
  .search-form .el-form-item {
    margin-bottom: 16px;
  }
}
</style>