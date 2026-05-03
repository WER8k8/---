<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h2>数据看板</h2>
      <p>实时查看SEO矩阵系统运行状态</p>
    </div>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409EFF">
              <el-icon :size="32"><Location /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalRegions }}</div>
              <div class="stat-label">覆盖县域数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67C23A">
              <el-icon :size="32"><Key /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.totalKeywords) }}</div>
              <div class="stat-label">关键词总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #E6A23C">
              <el-icon :size="32"><Files /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(stats.totalArticles) }}</div>
              <div class="stat-label">文章总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #F56C6C">
              <el-icon :size="32"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.successRate }}%</div>
              <div class="stat-label">发布成功率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="chart-row">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>发布趋势（近7天）</span>
            </div>
          </template>
          <div ref="trendChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>今日统计</span>
            </div>
          </template>
          <div class="today-stats">
            <div class="stat-item">
              <span class="label">生成文章</span>
              <span class="value">{{ stats.todayStats?.generated || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">发布成功</span>
              <span class="value success">{{ stats.todayStats?.published || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">发布失败</span>
              <span class="value danger">{{ stats.todayStats?.failed || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="label">收录数量</span>
              <span class="value">{{ stats.todayStats?.indexed || 0 }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="alert-row">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>异常预警</span>
              <el-badge :value="alerts.length" :max="99" />
            </div>
          </template>
          <el-empty v-if="alerts.length === 0" description="暂无异常预警" />
          <el-alert
            v-for="(alert, index) in alerts"
            :key="index"
            :title="alert.title"
            :description="alert.description"
            :type="alert.type"
            show-icon
            closable
            style="margin-bottom: 12px"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Location, Key, Files, SuccessFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import api from '@/api'

const stats = ref({
  totalRegions: 0,
  totalKeywords: 0,
  totalArticles: 0,
  publishedArticles: 0,
  successRate: 0,
  indexedCount: 0,
  homepageCount: 0,
  todayStats: { generated: 0, published: 0, failed: 0, indexed: 0 }
})

const alerts = ref([])
const trendChartRef = ref(null)
let trendChart = null
let refreshTimer = null

const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num?.toLocaleString() || 0
}

const fetchStats = async () => {
  try {
    const res = await api.get('/api/v1/dashboard/overview')
    stats.value = res.data
  } catch (e) {
    console.error('获取统计数据失败:', e)
  }
}

const fetchAlerts = async () => {
  try {
    const res = await api.get('/api/v1/monitoring/alerts')
    const allAlerts = []
    
    if (res.data.accountAlerts?.length) {
      res.data.accountAlerts.forEach(a => {
        allAlerts.push({ title: `账号异常: ${a.accountName}`, description: a.reason, type: 'error' })
      })
    }
    
    if (res.data.publishAlerts?.length) {
      res.data.publishAlerts.forEach(a => {
        allAlerts.push({ title: `发布异常: ${a.platformName}`, description: `失败率: ${a.failRate}%`, type: 'warning' })
      })
    }
    
    alerts.value = allAlerts
  } catch (e) {
    console.error('获取预警数据失败:', e)
  }
}

const initTrendChart = () => {
  if (!trendChartRef.value) return
  
  trendChart = echarts.init(trendChartRef.value)
  
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['生成', '发布', '收录'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: []
    },
    yAxis: { type: 'value' },
    series: [
      { name: '生成', type: 'line', data: [], smooth: true, itemStyle: { color: '#409EFF' } },
      { name: '发布', type: 'line', data: [], smooth: true, itemStyle: { color: '#67C23A' } },
      { name: '收录', type: 'line', data: [], smooth: true, itemStyle: { color: '#E6A23C' } }
    ]
  }
  
  trendChart.setOption(option)
}

const fetchTrendData = async () => {
  try {
    const res = await api.get('/api/v1/dashboard/trends', { params: { type: 'publish', days: 7 } })
    if (trendChart && res.data.dates) {
      trendChart.setOption({
        xAxis: { data: res.data.dates },
        series: [
          { data: res.data.generated || [] },
          { data: res.data.published || [] },
          { data: res.data.indexed || [] }
        ]
      })
    }
  } catch (e) {
    console.error('获取趋势数据失败:', e)
  }
}

onMounted(() => {
  fetchStats()
  fetchAlerts()
  initTrendChart()
  fetchTrendData()
  
  refreshTimer = setInterval(() => {
    fetchStats()
    fetchAlerts()
  }, 60000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (trendChart) trendChart.dispose()
})
</script>

<style scoped lang="scss">
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.today-stats {
  .stat-item {
    display: flex;
    justify-content: space-between;
    padding: 12px 0;
    border-bottom: 1px solid #ebeef5;
    
    &:last-child {
      border-bottom: none;
    }
    
    .label {
      color: #606266;
    }
    
    .value {
      font-weight: 600;
      font-size: 18px;
      
      &.success {
        color: #67C23A;
      }
      
      &.danger {
        color: #F56C6C;
      }
    }
  }
}

.alert-row {
  margin-bottom: 20px;
}
</style>
