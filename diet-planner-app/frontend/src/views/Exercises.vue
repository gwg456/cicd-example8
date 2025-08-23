<template>
  <Layout>
    <div class="exercises">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>运动记录</span>
            <div class="header-actions">
              <el-date-picker
                v-model="selectedDate"
                type="date"
                placeholder="选择日期"
                @change="fetchExercises"
                style="margin-right: 10px;"
              />
              <el-button type="primary" @click="showAddDialog = true">
                <el-icon><Plus /></el-icon>
                添加运动
              </el-button>
            </div>
          </div>
        </template>
        
        <div v-if="exercises.length === 0" class="empty-state">
          <el-empty description="今天还没有运动记录，开始记录吧！" />
        </div>
        
        <div v-else class="exercises-list">
          <el-card v-for="exercise in exercises" :key="exercise.id" class="exercise-item">
            <div class="exercise-info">
              <div class="exercise-main">
                <h4 class="exercise-name">{{ exercise.exercise_name }}</h4>
                <div class="exercise-details">
                  <span class="duration">{{ exercise.duration }}分钟</span>
                  <span class="calories" v-if="exercise.calories_burned">
                    消耗 {{ exercise.calories_burned }}kcal
                  </span>
                </div>
                <p v-if="exercise.notes" class="exercise-notes">{{ exercise.notes }}</p>
              </div>
              <div class="exercise-actions">
                <el-button size="small" type="text">编辑</el-button>
                <el-button size="small" type="text" class="delete-btn">删除</el-button>
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- 统计信息 -->
        <div v-if="exercises.length > 0" class="exercise-summary">
          <el-card>
            <template #header>
              <span>今日运动统计</span>
            </template>
            <div class="summary-stats">
              <div class="stat-item">
                <div class="stat-value">{{ totalDuration }}</div>
                <div class="stat-label">总时长 (分钟)</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ totalCalories }}</div>
                <div class="stat-label">总消耗 (kcal)</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ exercises.length }}</div>
                <div class="stat-label">运动项目</div>
              </div>
            </div>
          </el-card>
        </div>
      </el-card>
      
      <!-- 添加运动对话框 -->
      <el-dialog v-model="showAddDialog" title="添加运动记录" width="500px">
        <el-form :model="exerciseForm" :rules="exerciseRules" ref="exerciseFormRef" label-width="100px">
          <el-form-item label="运动名称" prop="exercise_name">
            <el-input v-model="exerciseForm.exercise_name" placeholder="如：跑步、游泳、瑜伽等" />
          </el-form-item>
          <el-form-item label="运动时长" prop="duration">
            <el-input-number v-model="exerciseForm.duration" :min="1" :max="600" />
            <span class="input-suffix">分钟</span>
          </el-form-item>
          <el-form-item label="消耗卡路里">
            <el-input-number v-model="exerciseForm.calories_burned" :min="0" />
            <span class="input-suffix">kcal</span>
          </el-form-item>
          <el-form-item label="备注">
            <el-input 
              v-model="exerciseForm.notes" 
              type="textarea" 
              :rows="3" 
              placeholder="记录运动感受、强度等"
            />
          </el-form-item>
        </el-form>
        
        <template #footer>
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="addExercise" :loading="saving">添加</el-button>
        </template>
      </el-dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import dayjs from 'dayjs'

const exercises = ref([])
const selectedDate = ref(new Date())
const showAddDialog = ref(false)
const saving = ref(false)
const exerciseFormRef = ref()

const exerciseForm = reactive({
  exercise_name: '',
  duration: 30,
  calories_burned: 0,
  notes: ''
})

const exerciseRules = {
  exercise_name: [{ required: true, message: '请输入运动名称', trigger: 'blur' }],
  duration: [{ required: true, message: '请输入运动时长', trigger: 'blur' }]
}

const totalDuration = computed(() => {
  return exercises.value.reduce((sum, ex) => sum + ex.duration, 0)
})

const totalCalories = computed(() => {
  return exercises.value.reduce((sum, ex) => sum + (ex.calories_burned || 0), 0)
})

const fetchExercises = async () => {
  try {
    const dateStr = dayjs(selectedDate.value).format('YYYY-MM-DD')
    const response = await axios.get(`/api/exercises?date=${dateStr}`)
    exercises.value = response.data
  } catch (error) {
    console.error('Failed to fetch exercises:', error)
    ElMessage.error('获取运动记录失败')
  }
}

const addExercise = async () => {
  try {
    await exerciseFormRef.value.validate()
    saving.value = true
    
    const data = {
      ...exerciseForm,
      exercise_date: dayjs(selectedDate.value).format('YYYY-MM-DD')
    }
    
    await axios.post('/api/exercises', data)
    ElMessage.success('运动记录添加成功')
    
    showAddDialog.value = false
    resetForm()
    fetchExercises()
  } catch (error) {
    console.error('Failed to add exercise:', error)
    ElMessage.error('添加失败，请重试')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  Object.assign(exerciseForm, {
    exercise_name: '',
    duration: 30,
    calories_burned: 0,
    notes: ''
  })
}

onMounted(() => {
  fetchExercises()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.empty-state {
  padding: 40px 0;
}

.exercises-list {
  margin-bottom: 20px;
}

.exercise-item {
  margin-bottom: 12px;
}

.exercise-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.exercise-main {
  flex: 1;
}

.exercise-name {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.exercise-details {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
  font-size: 14px;
}

.duration {
  color: #409eff;
  font-weight: 500;
}

.calories {
  color: #67c23a;
  font-weight: 500;
}

.exercise-notes {
  margin: 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.exercise-actions {
  display: flex;
  gap: 8px;
}

.delete-btn {
  color: #f56c6c;
}

.exercise-summary {
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.input-suffix {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}

@media (max-width: 768px) {
  .summary-stats {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .exercise-info {
    flex-direction: column;
    gap: 12px;
  }
}
</style>