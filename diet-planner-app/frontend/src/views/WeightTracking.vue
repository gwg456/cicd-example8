<template>
  <Layout>
    <div class="weight-tracking">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>体重变化趋势</span>
                <el-button type="primary" @click="showAddDialog = true">
                  <el-icon><Plus /></el-icon>
                  记录体重
                </el-button>
              </div>
            </template>
            
            <div class="chart-container">
              <v-chart v-if="weightRecords.length > 0" :option="chartOption" style="height: 400px;" />
              <el-empty v-else description="暂无体重记录，开始记录吧！" />
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>统计信息</span>
            </template>
            
            <div class="stats-container">
              <div class="stat-item">
                <div class="stat-label">当前体重</div>
                <div class="stat-value">{{ currentWeight }}<span class="unit">kg</span></div>
              </div>
              
              <div class="stat-item" v-if="initialWeight">
                <div class="stat-label">初始体重</div>
                <div class="stat-value">{{ initialWeight }}<span class="unit">kg</span></div>
              </div>
              
              <div class="stat-item" v-if="weightChange !== null">
                <div class="stat-label">体重变化</div>
                <div class="stat-value" :class="weightChangeClass">
                  {{ weightChange > 0 ? '+' : '' }}{{ weightChange }}<span class="unit">kg</span>
                </div>
              </div>
              
              <div class="stat-item" v-if="targetWeight">
                <div class="stat-label">目标体重</div>
                <div class="stat-value">{{ targetWeight }}<span class="unit">kg</span></div>
              </div>
              
              <div class="stat-item" v-if="remainingWeight !== null">
                <div class="stat-label">还需减重</div>
                <div class="stat-value">{{ remainingWeight }}<span class="unit">kg</span></div>
              </div>
            </div>
          </el-card>
          
          <el-card style="margin-top: 20px;">
            <template #header>
              <span>最近记录</span>
            </template>
            
            <div class="recent-records">
              <div v-if="weightRecords.length === 0" class="empty-records">
                <el-empty :image-size="60" description="暂无记录" />
              </div>
              <div v-else class="record-list">
                <div 
                  v-for="record in recentRecords" 
                  :key="record.id" 
                  class="record-item"
                >
                  <div class="record-date">{{ formatDate(record.recorded_date) }}</div>
                  <div class="record-weight">{{ record.weight }}kg</div>
                  <div v-if="record.notes" class="record-notes">{{ record.notes }}</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 添加体重记录对话框 -->
      <el-dialog v-model="showAddDialog" title="记录体重" width="400px">
        <el-form :model="weightForm" :rules="weightRules" ref="weightFormRef" label-width="80px">
          <el-form-item label="体重" prop="weight">
            <el-input-number 
              v-model="weightForm.weight" 
              :min="30" 
              :max="300" 
              :precision="1" 
              :step="0.1"
            />
            <span class="input-suffix">kg</span>
          </el-form-item>
          <el-form-item label="日期" prop="recorded_date">
            <el-date-picker 
              v-model="weightForm.recorded_date" 
              type="date" 
              placeholder="选择日期"
              style="width: 100%;"
            />
          </el-form-item>
          <el-form-item label="备注">
            <el-input 
              v-model="weightForm.notes" 
              type="textarea" 
              :rows="3" 
              placeholder="记录当天的感受、状态等"
            />
          </el-form-item>
        </el-form>
        
        <template #footer>
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="addWeightRecord" :loading="saving">保存</el-button>
        </template>
      </el-dialog>
    </div>
  </Layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { 
  TitleComponent, 
  TooltipComponent, 
  GridComponent,
  DataZoomComponent 
} from 'echarts/components'
import VChart from 'vue-echarts'
import Layout from '@/components/Layout.vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'
import dayjs from 'dayjs'

// 注册ECharts组件
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  DataZoomComponent
])

const authStore = useAuthStore()
const weightRecords = ref([])
const showAddDialog = ref(false)
const saving = ref(false)
const weightFormRef = ref()

const weightForm = reactive({
  weight: null,
  recorded_date: new Date(),
  notes: ''
})

const weightRules = {
  weight: [{ required: true, message: '请输入体重', trigger: 'blur' }],
  recorded_date: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

const currentWeight = computed(() => {
  return weightRecords.value.length > 0 ? weightRecords.value[0].weight : '--'
})

const initialWeight = computed(() => {
  return weightRecords.value.length > 0 ? 
    weightRecords.value[weightRecords.value.length - 1].weight : null
})

const weightChange = computed(() => {
  if (weightRecords.value.length < 2) return null
  return (currentWeight.value - initialWeight.value).toFixed(1)
})

const weightChangeClass = computed(() => {
  if (weightChange.value === null) return ''
  return weightChange.value < 0 ? 'positive' : 'negative'
})

const targetWeight = computed(() => {
  return authStore.user?.target_weight || null
})

const remainingWeight = computed(() => {
  if (!targetWeight.value || currentWeight.value === '--') return null
  const remaining = currentWeight.value - targetWeight.value
  return remaining > 0 ? remaining.toFixed(1) : 0
})

const recentRecords = computed(() => {
  return weightRecords.value.slice(0, 5)
})

const chartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: function(params) {
      const point = params[0]
      return `${point.name}<br/>体重: ${point.value}kg`
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: weightRecords.value.slice().reverse().map(record => 
      dayjs(record.recorded_date).format('MM-DD')
    )
  },
  yAxis: {
    type: 'value',
    name: 'kg',
    min: function(value) {
      return Math.floor(value.min - 2)
    },
    max: function(value) {
      return Math.ceil(value.max + 2)
    }
  },
  series: [{
    name: '体重',
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 6,
    lineStyle: {
      color: '#409eff',
      width: 3
    },
    itemStyle: {
      color: '#409eff'
    },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0,
        y: 0,
        x2: 0,
        y2: 1,
        colorStops: [{
          offset: 0, color: 'rgba(64, 158, 255, 0.3)'
        }, {
          offset: 1, color: 'rgba(64, 158, 255, 0.05)'
        }]
      }
    },
    data: weightRecords.value.slice().reverse().map(record => record.weight)
  }]
}))

const fetchWeightRecords = async () => {
  try {
    const response = await axios.get('/api/weight-records?limit=50')
    weightRecords.value = response.data
  } catch (error) {
    console.error('Failed to fetch weight records:', error)
    ElMessage.error('获取体重记录失败')
  }
}

const addWeightRecord = async () => {
  try {
    await weightFormRef.value.validate()
    saving.value = true
    
    const data = {
      weight: weightForm.weight,
      recorded_date: dayjs(weightForm.recorded_date).format('YYYY-MM-DD'),
      notes: weightForm.notes
    }
    
    await axios.post('/api/weight-records', data)
    ElMessage.success('体重记录添加成功')
    
    showAddDialog.value = false
    resetForm()
    fetchWeightRecords()
  } catch (error) {
    console.error('Failed to add weight record:', error)
    ElMessage.error('添加失败，请重试')
  } finally {
    saving.value = false
  }
}

const resetForm = () => {
  Object.assign(weightForm, {
    weight: null,
    recorded_date: new Date(),
    notes: ''
  })
}

const formatDate = (dateStr) => {
  return dayjs(dateStr).format('MM月DD日')
}

onMounted(() => {
  fetchWeightRecords()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  padding: 20px 0;
}

.stats-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-value.positive {
  color: #67c23a;
}

.stat-value.negative {
  color: #f56c6c;
}

.stat-value .unit {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
}

.recent-records {
  max-height: 300px;
  overflow-y: auto;
}

.empty-records {
  text-align: center;
  padding: 20px 0;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #409eff;
}

.record-date {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.record-weight {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.record-notes {
  font-size: 14px;
  color: #606266;
  line-height: 1.4;
}

.input-suffix {
  margin-left: 8px;
  color: #909399;
  font-size: 14px;
}
</style>