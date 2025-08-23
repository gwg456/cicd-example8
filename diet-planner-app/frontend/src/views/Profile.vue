<template>
  <Layout>
    <div class="profile">
      <el-card>
        <template #header>
          <span>个人资料</span>
        </template>
        
        <el-form :model="userForm" :rules="rules" ref="formRef" label-width="100px">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="姓名" prop="name">
                <el-input v-model="userForm.name" disabled />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="userForm.email" disabled />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="年龄" prop="age">
                <el-input-number v-model="userForm.age" :min="1" :max="120" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="性别" prop="gender">
                <el-select v-model="userForm.gender" placeholder="请选择性别">
                  <el-option label="男" value="male" />
                  <el-option label="女" value="female" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="身高(cm)" prop="height">
                <el-input-number v-model="userForm.height" :min="100" :max="250" :precision="1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="当前体重(kg)" prop="current_weight">
                <el-input-number v-model="userForm.current_weight" :min="30" :max="300" :precision="1" />
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="目标体重(kg)" prop="target_weight">
                <el-input-number v-model="userForm.target_weight" :min="30" :max="300" :precision="1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="活动水平" prop="activity_level">
                <el-select v-model="userForm.activity_level" placeholder="请选择活动水平">
                  <el-option label="久坐不动" value="sedentary" />
                  <el-option label="轻度活动" value="light" />
                  <el-option label="中度活动" value="moderate" />
                  <el-option label="高度活动" value="active" />
                  <el-option label="极高活动" value="very_active" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item>
            <el-button type="primary" @click="updateProfile" :loading="loading">
              更新资料
            </el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Layout from '@/components/Layout.vue'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const userForm = reactive({
  name: '',
  email: '',
  age: null,
  gender: '',
  height: null,
  current_weight: null,
  target_weight: null,
  activity_level: ''
})

const rules = {
  age: [{ type: 'number', message: '请输入有效的年龄', trigger: 'blur' }],
  height: [{ type: 'number', message: '请输入有效的身高', trigger: 'blur' }],
  current_weight: [{ type: 'number', message: '请输入有效的体重', trigger: 'blur' }],
  target_weight: [{ type: 'number', message: '请输入有效的目标体重', trigger: 'blur' }]
}

const loadUserData = () => {
  const user = authStore.user
  if (user) {
    Object.assign(userForm, {
      name: user.name || '',
      email: user.email || '',
      age: user.age,
      gender: user.gender || '',
      height: user.height,
      current_weight: user.current_weight,
      target_weight: user.target_weight,
      activity_level: user.activity_level || ''
    })
  }
}

const updateProfile = async () => {
  try {
    await formRef.value.validate()
    loading.value = true
    
    const updateData = {
      age: userForm.age,
      gender: userForm.gender,
      height: userForm.height,
      current_weight: userForm.current_weight,
      target_weight: userForm.target_weight,
      activity_level: userForm.activity_level
    }
    
    await authStore.updateUser(updateData)
    ElMessage.success('个人资料更新成功')
  } catch (error) {
    console.error('Failed to update profile:', error)
    ElMessage.error('更新失败，请重试')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  loadUserData()
}

onMounted(() => {
  loadUserData()
})
</script>

<style scoped>
.profile {
  max-width: 800px;
  margin: 0 auto;
}
</style>