<template>
  <Layout>
    <div class="meals">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>饮食记录</span>
            <div class="header-actions">
              <el-date-picker
                v-model="selectedDate"
                type="date"
                placeholder="选择日期"
                @change="fetchMeals"
                style="margin-right: 10px;"
              />
              <el-button type="primary" @click="showAddDialog = true">
                <el-icon><Plus /></el-icon>
                添加饮食
              </el-button>
            </div>
          </div>
        </template>
        
        <div class="meals-content">
          <div class="meal-sections">
            <div v-for="mealType in mealTypes" :key="mealType.value" class="meal-section">
              <h3 class="meal-title">{{ mealType.label }}</h3>
              <div v-if="getMealsByType(mealType.value).length === 0" class="empty-meal">
                <el-empty :image-size="60" description="暂无记录" />
              </div>
              <div v-else class="meal-items">
                <el-card v-for="meal in getMealsByType(mealType.value)" :key="meal.id" class="meal-item">
                  <div class="meal-info">
                    <div class="meal-name">{{ meal.food_name }}</div>
                    <div class="meal-details">
                      {{ meal.quantity }}{{ meal.unit }} • {{ meal.calories || 0 }}kcal
                    </div>
                  </div>
                </el-card>
              </div>
            </div>
          </div>
          
          <div class="nutrition-summary">
            <el-card>
              <template #header>
                <span>今日营养摄入</span>
              </template>
              <div class="summary-stats">
                <div class="stat-item">
                  <div class="stat-value">{{ totalCalories }}</div>
                  <div class="stat-label">卡路里 (kcal)</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ totalProtein.toFixed(1) }}</div>
                  <div class="stat-label">蛋白质 (g)</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ totalCarbs.toFixed(1) }}</div>
                  <div class="stat-label">碳水 (g)</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ totalFat.toFixed(1) }}</div>
                  <div class="stat-label">脂肪 (g)</div>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </el-card>
      
      <!-- 添加饮食对话框 -->
      <el-dialog v-model="showAddDialog" title="添加饮食记录" width="500px">
        <el-form :model="mealForm" :rules="mealRules" ref="mealFormRef" label-width="80px">
          <el-form-item label="餐次" prop="meal_type">
            <el-select v-model="mealForm.meal_type" placeholder="请选择餐次">
              <el-option v-for="type in mealTypes" :key="type.value" :label="type.label" :value="type.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="食物" prop="food_name">
            <el-input v-model="mealForm.food_name" placeholder="请输入食物名称" />
          </el-form-item>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="数量" prop="quantity">
                <el-input-number v-model="mealForm.quantity" :min="0.1" :precision="1" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="单位" prop="unit">
                <el-select v-model="mealForm.unit" placeholder="选择单位">
                  <el-option label="克(g)" value="g" />
                  <el-option label="毫升(ml)" value="ml" />
                  <el-option label="个" value="个" />
                  <el-option label="份" value="份" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="卡路里">
            <el-input-number v-model="mealForm.calories" :min="0" />
          </el-form-item>
        </el-form>
        
        <template #footer>
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="addMeal" :loading="saving">添加</el-button>
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

const meals = ref([])
const selectedDate = ref(new Date())
const showAddDialog = ref(false)
const saving = ref(false)
const mealFormRef = ref()

const mealTypes = [
  { label: '早餐', value: 'breakfast' },
  { label: '午餐', value: 'lunch' },
  { label: '晚餐', value: 'dinner' },
  { label: '加餐', value: 'snack' }
]

const mealForm = reactive({
  meal_type: '',
  food_name: '',
  quantity: 100,
  unit: 'g',
  calories: 0,
  protein: 0,
  carbs: 0,
  fat: 0
})

const mealRules = {
  meal_type: [{ required: true, message: '请选择餐次', trigger: 'change' }],
  food_name: [{ required: true, message: '请输入食物名称', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  unit: [{ required: true, message: '请选择单位', trigger: 'change' }]
}

const getMealsByType = (type) => {
  return meals.value.filter(meal => meal.meal_type === type)
}

const totalCalories = computed(() => {
  return meals.value.reduce((sum, meal) => sum + (meal.calories || 0), 0)
})

const totalProtein = computed(() => {
  return meals.value.reduce((sum, meal) => sum + (meal.protein || 0), 0)
})

const totalCarbs = computed(() => {
  return meals.value.reduce((sum, meal) => sum + (meal.carbs || 0), 0)
})

const totalFat = computed(() => {
  return meals.value.reduce((sum, meal) => sum + (meal.fat || 0), 0)
})

const fetchMeals = async () => {
  try {
    const dateStr = dayjs(selectedDate.value).format('YYYY-MM-DD')
    const response = await axios.get(`/api/meal-records?date=${dateStr}`)
    meals.value = response.data
  } catch (error) {
    console.error('Failed to fetch meals:', error)
    ElMessage.error('获取饮食记录失败')
  }
}

const addMeal = async () => {
  try {
    await mealFormRef.value.validate()
    saving.value = true
    
    const data = {
      ...mealForm,
      meal_date: dayjs(selectedDate.value).format('YYYY-MM-DD')
    }
    
    await axios.post('/api/meal-records', data)
    ElMessage.success('饮食记录添加成功')
    
    showAddDialog.value = false
    resetForm()
    fetchMeals()
  } catch (error) {
    console.error('Failed to add meal:', error)
    ElMessage.error('添加失败，请重试')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  Object.assign(mealForm, {
    meal_type: '',
    food_name: '',
    quantity: 100,
    unit: 'g',
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0
  })
}

onMounted(() => {
  fetchMeals()
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

.meals-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
}

.meal-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.meal-section {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
}

.meal-title {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.empty-meal {
  text-align: center;
  padding: 20px;
}

.meal-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meal-item {
  border: 1px solid #f0f0f0;
}

.meal-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meal-name {
  font-weight: 500;
  color: #303133;
}

.meal-details {
  font-size: 14px;
  color: #909399;
}

.nutrition-summary {
  position: sticky;
  top: 20px;
}

.summary-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

@media (max-width: 768px) {
  .meals-content {
    grid-template-columns: 1fr;
  }
}
</style>