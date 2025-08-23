<template>
  <Layout>
    <div class="diet-plans">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>减肥计划管理</span>
            <el-button type="primary" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon>
              新建计划
            </el-button>
          </div>
        </template>
        
        <el-empty v-if="plans.length === 0" description="暂无减肥计划，创建一个开始吧！" />
        
        <div v-else class="plans-grid">
          <el-card v-for="plan in plans" :key="plan.id" class="plan-card" :class="{ active: plan.is_active }">
            <div class="plan-header">
              <h3>{{ plan.name }}</h3>
              <el-tag v-if="plan.is_active" type="success">当前计划</el-tag>
            </div>
            <p class="plan-description">{{ plan.description || '暂无描述' }}</p>
            <div class="plan-details">
              <div class="detail-item">
                <span class="label">开始日期:</span>
                <span>{{ plan.start_date }}</span>
              </div>
              <div class="detail-item" v-if="plan.end_date">
                <span class="label">结束日期:</span>
                <span>{{ plan.end_date }}</span>
              </div>
              <div class="detail-item" v-if="plan.target_calories">
                <span class="label">目标卡路里:</span>
                <span>{{ plan.target_calories }}kcal/天</span>
              </div>
            </div>
            <div class="plan-actions">
              <el-button size="small" @click="editPlan(plan)">编辑</el-button>
              <el-button v-if="!plan.is_active" size="small" type="success" @click="activatePlan(plan)">
                激活
              </el-button>
            </div>
          </el-card>
        </div>
      </el-card>
      
      <!-- 创建/编辑对话框 -->
      <el-dialog 
        v-model="showCreateDialog" 
        :title="editingPlan ? '编辑计划' : '新建计划'"
        width="600px"
      >
        <el-form :model="planForm" :rules="planRules" ref="planFormRef" label-width="120px">
          <el-form-item label="计划名称" prop="name">
            <el-input v-model="planForm.name" placeholder="请输入计划名称" />
          </el-form-item>
          <el-form-item label="计划描述">
            <el-input v-model="planForm.description" type="textarea" :rows="3" placeholder="请输入计划描述" />
          </el-form-item>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="开始日期" prop="start_date">
                <el-date-picker v-model="planForm.start_date" type="date" placeholder="选择开始日期" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="结束日期">
                <el-date-picker v-model="planForm.end_date" type="date" placeholder="选择结束日期" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="目标卡路里">
            <el-input-number v-model="planForm.target_calories" :min="800" :max="5000" />
            <span class="input-suffix">kcal/天</span>
          </el-form-item>
        </el-form>
        
        <template #footer>
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="savePlan" :loading="saving">
            {{ editingPlan ? '更新' : '创建' }}
          </el-button>
        </template>
      </el-dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import dayjs from 'dayjs'

const plans = ref([])
const showCreateDialog = ref(false)
const editingPlan = ref(null)
const saving = ref(false)
const planFormRef = ref()

const planForm = reactive({
  name: '',
  description: '',
  start_date: null,
  end_date: null,
  target_calories: 2000,
  target_protein: null,
  target_carbs: null,
  target_fat: null
})

const planRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }]
}

const fetchPlans = async () => {
  try {
    const response = await axios.get('/api/diet-plans')
    plans.value = response.data
  } catch (error) {
    console.error('Failed to fetch plans:', error)
    ElMessage.error('获取计划列表失败')
  }
}

const editPlan = (plan) => {
  editingPlan.value = plan
  Object.assign(planForm, {
    name: plan.name,
    description: plan.description,
    start_date: new Date(plan.start_date),
    end_date: plan.end_date ? new Date(plan.end_date) : null,
    target_calories: plan.target_calories,
    target_protein: plan.target_protein,
    target_carbs: plan.target_carbs,
    target_fat: plan.target_fat
  })
  showCreateDialog.value = true
}

const savePlan = async () => {
  try {
    await planFormRef.value.validate()
    saving.value = true
    
    const data = {
      ...planForm,
      start_date: dayjs(planForm.start_date).format('YYYY-MM-DD'),
      end_date: planForm.end_date ? dayjs(planForm.end_date).format('YYYY-MM-DD') : null
    }
    
    if (editingPlan.value) {
      await axios.put(`/api/diet-plans/${editingPlan.value.id}`, data)
      ElMessage.success('计划更新成功')
    } else {
      await axios.post('/api/diet-plans', data)
      ElMessage.success('计划创建成功')
    }
    
    showCreateDialog.value = false
    resetForm()
    fetchPlans()
  } catch (error) {
    console.error('Failed to save plan:', error)
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

const activatePlan = async (plan) => {
  try {
    await axios.put(`/api/diet-plans/${plan.id}`, { is_active: true })
    ElMessage.success('计划已激活')
    fetchPlans()
  } catch (error) {
    console.error('Failed to activate plan:', error)
    ElMessage.error('激活失败，请重试')
  }
}

const resetForm = () => {
  editingPlan.value = null
  Object.assign(planForm, {
    name: '',
    description: '',
    start_date: null,
    end_date: null,
    target_calories: 2000,
    target_protein: null,
    target_carbs: null,
    target_fat: null
  })
}

onMounted(() => {
  fetchPlans()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.plan-card {
  cursor: pointer;
  transition: all 0.3s;
}

.plan-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.plan-card.active {
  border-color: #67c23a;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.plan-header h3 {
  margin: 0;
  color: #303133;
}

.plan-description {
  color: #606266;
  margin-bottom: 15px;
  min-height: 20px;
}

.plan-details {
  margin-bottom: 15px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
  font-size: 14px;
}

.detail-item .label {
  color: #909399;
}

.plan-actions {
  display: flex;
  gap: 10px;
}

.input-suffix {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}
</style>