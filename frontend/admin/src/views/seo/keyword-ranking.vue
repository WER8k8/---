<template>
  <div class="keyword-ranking-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2 class="page-title">
        关键词排名追踪
      </h2>
      <div class="header-actions">
        <a-button
          type="primary"
          @click="showImportModal = true"
        >
          <template #icon>
            <PlusOutlined />
          </template>
          导入关键词
        </a-button>
        <a-button
          @click="refreshRankings"
          :loading="tracking"
        >
          <template #icon>
            <ReloadOutlined />
          </template>
          更新排名
        </a-button>
      </div>
    </div>

    <!-- 仪表盘卡片 -->
    <a-row
      :gutter="16"
      class="dashboard-cards"
    >
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="追踪关键词"
            :value="summary.total_keywords"
            suffix="个"
          >
            <template #prefix>
              <SearchOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="前10名"
            :value="summary.top_10"
            suffix="个"
            value-style="color: #3f8600"
          >
            <template #prefix>
              <TrophyOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="排名提升"
            :value="summary.improved"
            suffix="个"
            value-style="color: #3f8600"
          >
            <template #prefix>
              <ArrowUpOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="平均排名"
            :value="summary.avg_position"
            :precision="1"
            suffix="位"
          >
            <template #prefix>
              <BarChartOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 筛选器 -->
    <a-card class="filter-card">
      <a-form layout="inline">
        <a-form-item label="搜索引擎">
          <a-select
            v-model:value="filters.search_engine"
            style="width: 150px"
            allow-clear
          >
            <a-select-option value="baidu">
              百度
            </a-select-option>
            <a-select-option value="360">
              360
            </a-select-option>
            <a-select-option value="sogou">
              搜狗
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="分类">
          <a-input
            v-model:value="filters.category"
            placeholder="输入分类"
            style="width: 150px"
          />
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            @click="loadKeywords"
          >
            查询
          </a-button>
          <a-button
            style="margin-left: 8px"
            @click="resetFilters"
          >
            重置
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 关键词表格 -->
    <a-card class="table-card">
      <a-table
        :columns="columns"
        :data-source="keywords"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <!-- 排名列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'current_position'">
            <a-tag
              v-if="record.current_position"
              :color="getPositionColor(record.current_position)"
            >
              第{{ record.current_position }}名
            </a-tag>
            <span
              v-else
              class="text-muted"
            >未收录</span>
          </template>

          <!-- 排名变化 -->
          <template v-else-if="column.key === 'position_change'">
            <span
              v-if="record.previous_position"
              :class="getPositionChangeClass(record)"
            >
              <ArrowUpOutlined v-if="record.position_improved" />
              <ArrowDownOutlined v-else-if="record.position_declined" />
              <MinusOutlined v-else />
              {{ Math.abs(record.position_change()) }}
            </span>
            <span v-else>-</span>
          </template>

          <!-- 难度 -->
          <template v-else-if="column.key === 'difficulty'">
            <a-badge
              :status="getDifficultyStatus(record.difficulty)"
              :text="record.difficulty"
            />
          </template>

          <!-- 操作 -->
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button
                type="link"
                size="small"
                @click="viewHistory(record)"
              >
                历史
              </a-button>
              <a-button
                type="link"
                size="small"
                @click="editKeyword(record)"
              >
                编辑
              </a-button>
              <a-popconfirm
                title="确定删除?"
                @confirm="deleteKeyword(record.id)"
              >
                <a-button
                  type="link"
                  danger
                  size="small"
                >
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 导入关键词弹窗 -->
    <a-modal
      v-model:open="showImportModal"
      title="导入关键词"
      width="600px"
      @ok="importKeywords"
    >
      <a-alert
        message="将导入轻集料混凝土行业默认关键词列表"
        type="info"
        show-icon
        style="margin-bottom: 16px"
      />
      <a-textarea
        v-model:value="importText"
        placeholder="每行一个关键词，例如：&#10;轻集料混凝土&#10;LC5.0轻集料混凝土&#10;轻质混凝土"
        :rows="10"
      />
      <div class="import-tip">
        提示：留空将导入默认关键词列表（{{ defaultKeywords.length }}个）
      </div>
    </a-modal>

    <!-- 排名历史弹窗 -->
    <a-modal
      v-model:open="showHistoryModal"
      title="排名历史"
      width="700px"
      :footer="null"
    >
      <v-chart
        v-if="historyData.length"
        :option="chartOption"
        style="height: 300px"
      />
      <a-empty
        v-else
        description="暂无历史数据"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined, ReloadOutlined, SearchOutlined, TrophyOutlined,
  ArrowUpOutlined, ArrowDownOutlined, MinusOutlined, BarChartOutlined
} from '@ant-design/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

// API请求函数（实际项目中应替换为真实API调用）
const apiBase = '/api/v1/seo/keywords'

// 状态
const loading = ref(false)
const tracking = ref(false)
const keywords = ref([])
const summary = ref({
  total_keywords: 0,
  top_10: 0,
  top_50: 0,
  improved: 0,
  declined: 0,
  avg_position: 0
})

const filters = reactive({
  search_engine: undefined,
  category: undefined
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`
})

const showImportModal = ref(false)
const importText = ref('')
const defaultKeywords = [
  '轻集料混凝土', 'LC5.0轻集料混凝土', 'LC7.5轻集料混凝土',
  'LC10轻集料混凝土', 'LC15轻集料混凝土', 'LC20轻集料混凝土',
  '轻质混凝土', '泡沫混凝土', '陶粒混凝土', '保温混凝土'
]

const showHistoryModal = ref(false)
const historyData = ref([])
const currentKeyword = ref(null)

// 表格列定义
const columns = [
  { title: '关键词', dataIndex: 'keyword', key: 'keyword', width: 200 },
  { title: '搜索引擎', dataIndex: 'search_engine', key: 'search_engine', width: 100 },
  { title: '当前排名', key: 'current_position', width: 100 },
  { title: '变化', key: 'position_change', width: 80 },
  { title: '最佳排名', dataIndex: 'best_position', key: 'best_position', width: 100 },
  { title: '搜索量', dataIndex: 'search_volume', key: 'search_volume', width: 100 },
  { title: '难度', key: 'difficulty', width: 80 },
  { title: '分类', dataIndex: 'category', key: 'category', width: 120 },
  { title: '最后更新', dataIndex: 'last_checked_at', key: 'last_checked_at', width: 160 },
  { title: '操作', key: 'action', width: 180, fixed: 'right' }
]

// 图表配置
const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: {
    type: 'category',
    data: historyData.value.map(h => h.date)
  },
  yAxis: {
    type: 'value',
    inverse: true,
    min: 1,
    max: 100
  },
  series: [{
    name: '排名',
    type: 'line',
    data: historyData.value.map(h => h.position),
    smooth: true,
    lineStyle: { color: '#1890ff' },
    areaStyle: { color: 'rgba(24, 144, 255, 0.1)' }
  }]
}))

// 方法
const loadKeywords = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      skip: (pagination.current - 1) * pagination.pageSize,
      limit: pagination.pageSize
    })

    if (filters.search_engine) params.append('search_engine', filters.search_engine)
    if (filters.category) params.append('category', filters.category)

    const response = await fetch(`${apiBase}?${params}`)
    const data = await response.json()
    keywords.value = data
    pagination.total = data.length // 实际应从后端获取总数
  } catch (error) {
    message.error('加载关键词失败')
  } finally {
    loading.value = false
  }
}

const loadSummary = async () => {
  try {
    const response = await fetch(`${apiBase}/dashboard/summary`)
    summary.value = await response.json()
  } catch (error) {
    console.error('加载摘要失败', error)
  }
}

const refreshRankings = async () => {
  tracking.value = true
  try {
    const response = await fetch(`${apiBase}/track`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        keywords: keywords.value.map(k => k.keyword),
        search_engine: 'baidu'
      })
    })
    const result = await response.json()
    message.success(`已更新 ${result.total} 个关键词排名`)
    await loadKeywords()
    await loadSummary()
  } catch (error) {
    message.error('更新排名失败')
  } finally {
    tracking.value = false
  }
}

const importKeywords = async () => {
  try {
    let keywordList = importText.value.trim().split('\n').filter(k => k.trim())
    if (keywordList.length === 0) {
      keywordList = defaultKeywords
    }

    const response = await fetch(`${apiBase}/batch-import-defaults`, {
      method: 'POST'
    })
    const result = await response.json()
    message.success(result.message)
    showImportModal.value = false
    importText.value = ''
    await loadKeywords()
    await loadSummary()
  } catch (error) {
    message.error('导入失败')
  }
}

const deleteKeyword = async (id) => {
  try {
    await fetch(`${apiBase}/${id}`, { method: 'DELETE' })
    message.success('删除成功')
    await loadKeywords()
    await loadSummary()
  } catch (error) {
    message.error('删除失败')
  }
}

const viewHistory = async (record) => {
  currentKeyword.value = record
  showHistoryModal.value = true

  try {
    const response = await fetch(`${apiBase}/${record.id}/history?days=30`)
    historyData.value = await response.json()
  } catch (error) {
    message.error('加载历史失败')
  }
}

const editKeyword = (record) => {
  message.info('编辑功能开发中')
}

const resetFilters = () => {
  filters.search_engine = undefined
  filters.category = undefined
  loadKeywords()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadKeywords()
}

const getPositionColor = (position) => {
  if (position <= 3) return 'success'
  if (position <= 10) return 'processing'
  if (position <= 50) return 'warning'
  return 'default'
}

const getPositionChangeClass = (record) => {
  if (record.position_improved()) return 'text-success'
  if (record.position_declined()) return 'text-danger'
  return 'text-muted'
}

const getDifficultyStatus = (difficulty) => {
  const map = { easy: 'success', medium: 'processing', hard: 'error' }
  return map[difficulty] || 'default'
}

onMounted(() => {
  loadKeywords()
  loadSummary()
})
</script>

<style scoped lang="scss">
.keyword-ranking-page {
  padding: 24px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    .page-title {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .dashboard-cards {
    margin-bottom: 24px;
  }

  .filter-card {
    margin-bottom: 16px;
  }

  .table-card {
    margin-bottom: 16px;
  }

  .text-muted { color: #999; }
  .text-success { color: #52c41a; }
  .text-danger { color: #ff4d4f; }

  .import-tip {
    margin-top: 8px;
    font-size: 12px;
    color: #999;
  }
}
</style>
