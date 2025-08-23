<template>
  <Layout>
    <div class="dashboard">
      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon calories">
                <el-icon><Food /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ todayStats.calories }}<span class="unit">kcal</span></div>
                <div class="stat-label">今日摄入</div>
                <div class="stat-progress">
                  <el-progress 
                    :percentage="caloriesProgress" 
                    :show-text="false" 
                    :stroke-width="4"
                  />
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon exercise">
                <el-icon><Trophy /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ todayStats.exerciseCalories }}<span class="unit">kcal</span></div>
                <div class="stat-label">今日消耗</div>
                <div class="stat-progress">
                  <el-progress 
                    :percentage="exerciseProgress" 
                    :show-text="false" 
                    :stroke-width="4"
                    color="#67c23a"
                  />
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon weight">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ latestWeight }}<span class="unit">kg</span></div>
                <div class="stat-label">当前体重</div>
                <div class="stat-change" :class="weightChangeClass">
                  {{ weightChangeText }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon target">
                <el-icon><Aim /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-value">{{ targetWeight }}<span class="unit">kg</span></div>
                <div class="stat-label">目标体重</div>
                <div class="stat-change">
                  还需减重 {{ remainingWeight }}kg
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 图表区域 -->
      <el-row :gutter="20" class="charts-row">
        <el-col :span="12">
          <el-card title="体重变化趋势">
            <template #header>
              <div class="card-header">
                <span>体重变化趋势</span>
                <el-button type="text" @click="goToWeightTracking">查看更多</el-button>
              </div>
            </template>
            <div class="chart-container">
              <v-chart :option="weightChartOption" style="height: 300px;" />
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>今日营养摄入</span>
                <el-button type="text" @click="goToMeals">查看详情</el-button>
              </div>
            </template>
            <div class="chart-container">
              <v-chart :option="nutritionChartOption" style="height: 300px;" />
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 快速操作 -->
      <el-row :gutter="20" class="actions-row">
        <el-col :span="24">
          <el-card>
            <template #header>
              <span>快速操作</span>
            </template>
            <div class="quick-actions">
              <el-button type="primary" @click="addMeal">
                <el-icon><Plus /></el-icon>
                添加饮食
              </el-button>
              <el-button type="success" @click="addExercise">
                <el-icon><Plus /></el-icon>
                记录运动
              </el-button>
              <el-button type="warning" @click="recordWeight">
                <el-icon><Plus /></el-icon>
                记录体重
              </el-button>
              <el-button type="info" @click="createPlan">
                <el-icon><Plus /></el-icon>
                制定计划
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { 
  TitleComponent, 
  TooltipComponent, 
  LegendComponent,
  GridComponent 
} from 'echarts/components'
import VChart from 'vue-echarts'
import axios from 'axios'
import Layout from '@/components/Layout.vue'
import { Food, Trophy, TrendCharts, Aim, Plus } from '@element-plus/icons-vue'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const router = useRouter()

const dashboardData = ref({
  today_nutrition: {
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0
  },
  today_exercise_calories: 0,
  latest_weight: null,
  weight_date: null,
  active_plan: null
})

const weightHistory = ref([])

// 计算属性
const todayStats = computed(() => ({
  calories: dashboardData.value.today_nutrition.calories || 0,
  exerciseCalories: dashboardData.value.today_exercise_calories || 0
}))

const latestWeight = computed(() => 
  dashboardData.value.latest_weight ? dashboardData.value.latest_weight.toFixed(1) : '--'
)

const targetWeight = computed(() => 
  dashboardData.value.active_plan?.target_weight || '--'
)

const remainingWeight = computed(() => {
  if (dashboardData.value.latest_weight && dashboardData.value.active_plan?.target_weight) {
    const remaining = dashboardData.value.latest_weight - dashboardData.value.active_plan.target_weight
    return remaining > 0 ? remaining.toFixed(1) : 0
  }
  return '--'
})

const caloriesProgress = computed(() => {
  const target = dashboardData.value.active_plan?.target_calories || 2000
  const current = todayStats.value.calories
  return Math.min((current / target) * 100, 100)
})

const exerciseProgress = computed(() => {
  const target = 300 // 默认目标消耗300kcal
  const current = todayStats.value.exerciseCalories
  return Math.min((current / target) * 100, 100)
})

const weightChangeClass = computed(() => {
  // 这里可以根据体重变化趋势设置样式
  return 'positive'
})

const weightChangeText = computed(() => {
  return '本周 -0.5kg'
})

// 图表配置
const weightChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: '{b}: {c}kg'
  },
  xAxis: {
    type: 'category',
    data: weightHistory.value.map(item => item.date)
  },
  yAxis: {
    type: 'value',
    name: 'kg'
  },
  series: [{
    name: '体重',
    type: 'line',
    smooth: true,
    data: weightHistory.value.map(item => item.weight),
    itemStyle: {
      color: '#409eff'
    }
  }]
}))

const nutritionChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: '{a} <br/>{b}: {c}g ({d}%)'
  },
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  series: [{
    name: '营养摄入',
    type: 'pie',
    radius: '50%',
    data: [
      { value: dashboardData.value.today_nutrition.protein || 0, name: '蛋白质' },
      { value: dashboardData.value.today_nutrition.carbs || 0, name: '碳水化合物' },
      { value: dashboardData.value.today_nutrition.fat || 0, name: '脂肪' }
    ],
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowOffsetX: 0,
        shadowColor: 'rgba(0, 0, 0, 0.5)'
      }
    }
  }]
}))

// 方法
const fetchDashboardData = async () => {
  try {
    const response = await axios.get('/api/dashboard')
    dashboardData.value = response.data
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

const fetchWeightHistory = async () => {
  try {
    const response = await axios.get('/api/weight-records?limit=7')
    weightHistory.value = response.data.map(record => ({
      date: record.recorded_date,
      weight: record.weight
    })).reverse()
  } catch (error) {
    console.error('Failed to fetch weight history:', error)
  }
}

const goToWeightTracking = () => {
  router.push('/weight-tracking')
}

const goToMeals = () => {
  router.push('/meals')
}

const addMeal = () => {
  router.push('/meals')
}

const addExercise = () => {
  router.push('/exercises')
}

const recordWeight = () => {
  router.push('/weight-tracking')
}

const createPlan = () => {
  router.push('/diet-plans')
}

onMounted(() => {
  fetchDashboardData()
  fetchWeightHistory()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.stat-icon.calories {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.exercise {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.weight {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.target {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-value .unit {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.stat-progress {
  margin-bottom: 4px;
}

.stat-change {
  font-size: 12px;
  color: #67c23a;
}

.stat-change.positive {
  color: #67c23a;
}

.stat-change.negative {
  color: #f56c6c;
}

.charts-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  padding: 10px 0;
}

.actions-row .el-card {
  margin-bottom: 20px;
}

.quick-actions {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  flex: 1;
  min-width: 120px;
}
</style>