<template>
  <div class="profile">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>个人资料</span>
        </div>
      </template>

      <el-form
        ref="profileFormRef"
        :model="profileForm"
        :rules="profileRules"
        label-width="100px"
        class="profile-form"
      >
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="profileForm.username"
                placeholder="请输入用户名"
                disabled
              />
            </el-form-item>

            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="profileForm.email"
                placeholder="请输入邮箱地址"
              />
            </el-form-item>

            <el-form-item label="真实姓名" prop="full_name">
              <el-input
                v-model="profileForm.full_name"
                placeholder="请输入真实姓名"
              />
            </el-form-item>
          </el-col>

          <el-col :xs="24" :md="12">
            <el-form-item label="账户状态">
              <el-tag :type="authStore.user?.is_active ? 'success' : 'danger'">
                {{ authStore.user?.is_active ? '激活' : '未激活' }}
              </el-tag>
            </el-form-item>

            <el-form-item label="用户角色">
              <div class="role-tags">
                <el-tag
                  v-for="role in authStore.user?.roles"
                  :key="role.id"
                  type="info"
                  size="small"
                >
                  {{ role.name }}
                </el-tag>
                <el-tag v-if="authStore.user?.is_superuser" type="warning" size="small">
                  超级管理员
                </el-tag>
              </div>
            </el-form-item>

            <el-form-item label="注册时间">
              <span>{{ formatDate(authStore.user?.created_at) }}</span>
            </el-form-item>

            <el-form-item label="更新时间">
              <span>{{ formatDate(authStore.user?.updated_at) }}</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            @click="handleUpdateProfile"
          >
            保存修改
          </el-button>
          <el-button @click="resetForm">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 修改密码 -->
    <el-card class="password-card">
      <template #header>
        <div class="card-header">
          <span>修改密码</span>
        </div>
      </template>

      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
        class="password-form"
      >
        <el-row :gutter="20">
          <el-col :xs="24" :md="12">
            <el-form-item label="新密码" prop="password">
              <el-input
                v-model="passwordForm.password"
                type="password"
                placeholder="请输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="danger"
                :loading="passwordLoading"
                @click="handleChangePassword"
              >
                修改密码
              </el-button>
              <el-button @click="resetPasswordForm">
                重置
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authAPI } from '@/api/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const loading = ref(false)
const passwordLoading = ref(false)

const profileFormRef = ref()
const passwordFormRef = ref()

const profileForm = reactive({
  username: '',
  email: '',
  full_name: ''
})

const passwordForm = reactive({
  password: '',
  confirmPassword: ''
})

const validatePasswordConfirm = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== passwordForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const profileRules = {
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }
  ],
  full_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ]
}

const passwordRules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validatePasswordConfirm, trigger: 'blur' }
  ]
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  return new Date(dateString).toLocaleString('zh-CN')
}

const initForm = () => {
  if (authStore.user) {
    profileForm.username = authStore.user.username
    profileForm.email = authStore.user.email
    profileForm.full_name = authStore.user.full_name || ''
  }
}

const handleUpdateProfile = async () => {
  if (!profileFormRef.value) return

  try {
    await profileFormRef.value.validate()
    
    loading.value = true
    
    await authAPI.updateCurrentUser({
      email: profileForm.email,
      full_name: profileForm.full_name
    })
    
    // 刷新用户信息
    await authStore.fetchUserProfile()
    
    ElMessage.success('个人资料更新成功')
  } catch (error) {
    console.error('Update profile error:', error)
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    loading.value = false
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
    
    passwordLoading.value = true
    
    await authAPI.updateCurrentUser({
      password: passwordForm.password
    })
    
    ElMessage.success('密码修改成功')
    resetPasswordForm()
  } catch (error) {
    console.error('Change password error:', error)
    ElMessage.error(error.response?.data?.detail || '密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

const resetForm = () => {
  initForm()
}

const resetPasswordForm = () => {
  passwordForm.password = ''
  passwordForm.confirmPassword = ''
  passwordFormRef.value?.clearValidate()
}

onMounted(() => {
  initForm()
})
</script>

<style scoped>
.profile {
  max-width: 800px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profile-form {
  margin-bottom: 0;
}

.password-card {
  margin-top: 20px;
}

.role-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  border-radius: 6px;
}

@media (max-width: 768px) {
  .profile {
    max-width: 100%;
  }
  
  :deep(.el-form-item__label) {
    text-align: left !important;
  }
}
</style>