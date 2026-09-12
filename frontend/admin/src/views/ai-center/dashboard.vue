<template>
  <YdPage class="ai-dashboard" title="AI 控制台" subtitle="AI 引擎整体状态 · 用量统计 · 快速入口" surface="elevated">
    <template #actions>
      <a-button type="primary" :loading="loading" @click="refresh">
        <ReloadOutlined />
        刷新
      </a-button>
    </template>

    <!-- AI Engine Health Status -->
    <a-card class="health-card">
      <template #title>
        <div class="health-title">
          <CpuOutlined class="mr-2" />
          AI 引擎状态
          <a-tag :color="engineHealthy ? 'green' : 'red'" class="ml-3">
            {{ engineHealthy ? '运行正常' : '异常' }}
          </a-tag>
        </div>
      </template>
      <a-row :gutter="[16, 16]">
        <a-col :span="6" v-for="p in providerStatusList" :key="p.name">
          <div class="provider-item" :class="{ configured: p.configured, unconfigured: !p.configured }">
            <div class="provider-icon">{{ p.name.charAt(0).toUpperCase() }}</div>
            <div class="provider-info">
              <span class="provider-name">{{ p.name }}</span>
              <a-tag :color="p.configured ? 'green' : 'orange'" size="small">{{ p.configured ? '已配置' : '待配置' }}</a-tag>
            </div>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <!-- Stats Row -->
    <div class="stats-row">
      <a-card size="small" v-for="s in stats" :key="s.label">
        <a-statistic :title="s.label" :value="s.value" :suffix="s.suffix" :value-style="{ color: s.color }" />
      </a-card>
    </div>

    <!-- Quick Actions & Recent Tasks -->
    <a-row :gutter="16">
      <a-col :span="14">
        <a-card title="最近 AI 任务" size="small">
          <div ref="tablePanelRef" class="yd-panel yd-table-panel">
            <YdTableToolbar :loading="loading" :target-ref="tablePanelRef" :show-export="false" @refresh="refresh" />
            <YdDataTable
              :columns="taskColumns"
              :data-source="recentTasks"
              :loading="loading"
              :pagination="false"
              :table-props="{ size: tableSize, rowKey: 'id' }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'status'">
                  <a-tag :color="record.status === 'success' ? 'green' : record.status === 'running' ? 'blue' : 'red'">
                    {{ record.status === 'success' ? '成功' : record.status === 'running' ? '进行中' : '失败' }}
                  </a-tag>
                </template>
              </template>
            </YdDataTable>
          </div>
        </a-card>
      </a-col>
      <a-col :span="10">
        <a-card title="快速入口" size="small">
          <div class="quick-actions">
            <a-button block class="quick-btn quick-content" @click="goToContent">
              <EditOutlined />
              <span>AI 内容助手</span>
            </a-button>
            <a-button block class="quick-btn quick-seo" @click="goToAnalytics">
              <BarChartOutlined />
              <span>智能分析</span>
            </a-button>
            <a-button block class="quick-btn quick-model" @click="goToModels">
              <LayersOutlined />
              <span>模型管理</span>
            </a-button>
            <a-button block class="quick-btn quick-logs" @click="goToLogs">
              <FileTextOutlined />
              <span>调用日志</span>
            </a-button>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { message } from 'ant-design-vue'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import {
  ApiOutlined as CpuOutlined, ReloadOutlined, EditOutlined,
  BarChartOutlined, BarsOutlined as LayersOutlined, FileTextOutlined,
} from '@ant-design/icons-vue'
import { apiGet } from '@/utils/api'
import { readStoredAccessToken } from '@/utils/sessionAuth'

const router = useRouter()
const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const loading = ref(false)
const providers = ref<any[]>([])
const engineHealthy = ref(true)

const providerStatusList = computed(() => {
  const names = ['OpenAI', 'DeepSeek', 'Anthropic', 'Gemini', 'NVIDIA', '硅基流动']
  const configuredNames = new Set(providers.value.filter((p: any) => p.api_key).map((p: any) => p.name))
  return names.map(name => ({
    name,
    configured: configuredNames.has(name),
  }))
})

const stats = ref([
  { label: '今日调用', value: '--', suffix: '次', color: '#4a9b8c' },
  { label: '成功率', value: '--', suffix: '%', color: '#22c55e' },
  { label: '本月费用', value: '--', suffix: '', color: '#f59e0b' },
  { label: '活跃模型', value: '--', suffix: '个', color: '#8b5cf6' },
])

const taskColumns = [
  { title: '任务', dataIndex: 'task', key: 'task' },
  { title: '模型', dataIndex: 'model', key: 'model' },
  { title: '状态', key: 'status' },
  { title: '时间', dataIndex: 'time', key: 'time' },
]

const recentTasks = ref<any[]>([
  { id: 1, task: '产品文案生成', model: 'gpt-4o', status: 'success', time: '10:30:25' },
  { id: 2, task: 'SEO关键词分析', model: 'deepseek-chat', status: 'success', time: '10:15:00' },
  { id: 3, task: '批量内容优化', model: 'claude-3-sonnet', status: 'running', time: '09:58:12' },
  { id: 4, task: '翻译任务', model: 'gpt-4o', status: 'failed', time: '09:30:45' },
])

async function loadStats() {
  try {
    const tk = readStoredAccessToken()
    const h: any = { Authorization: `Bearer ${tk}` }
    const sum = await fetch('/api/v1/super-admin/ai-cost/summary?days=1', { headers: h })
    const sd = (await sum.json()).data || {}
    stats.value = [
      { label: '今日调用', value: sd.total_calls ?? '--', suffix: '次', color: '#4a9b8c' },
      { label: '成功率', value: sd.success_rate != null ? sd.success_rate + '%' : '--', suffix: '', color: '#22c55e' },
      { label: '本月费用', value: sd.total_cost ? '$' + sd.total_cost : '--', suffix: '', color: '#f59e0b' },
      { label: '活跃模型', value: sd.active_models ?? '--', suffix: '个', color: '#8b5cf6' },
    ]
  } catch {
    // keep default mock values
  }
}

async function loadProviders() {
  try {
    providers.value = await apiGet('/super-admin/ai-config/providers')
    engineHealthy.value = providers.value.some((p: any) => p.enabled && p.api_key)
  } catch {
    engineHealthy.value = false
  }
}

function refresh() {
  loading.value = true
  Promise.all([loadStats(), loadProviders()]).finally(() => {
    loading.value = false
    message.success('已刷新')
  })
}

function goToContent() { router.push('/admin/ai-center/content') }
function goToAnalytics() { router.push('/admin/ai-center/analytics') }
function goToModels() { router.push('/admin/ai-center/models') }
function goToLogs() { router.push('/admin/ai-center/logs') }

onMounted(() => {
  loadStats()
  loadProviders()
})
</script>

<style scoped lang="scss">
.ai-dashboard {
  .health-card {
    margin-bottom: 20px;
    border-radius: 12px;

    .health-title {
      display: flex;
      align-items: center;
      font-size: 15px;
      font-weight: 600;
    }

    .provider-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 12px;
      border-radius: 10px;
      background: #f8fafc;
      transition: all 0.2s;

      &.configured {
        border-left: 3px solid #22c55e;
      }
      &.unconfigured {
        border-left: 3px solid #f59e0b;
      }

      .provider-icon {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        background: linear-gradient(135deg, #4a9b8c, #2a6b60);
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 14px;
        flex-shrink: 0;
      }

      .provider-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
        .provider-name {
          font-size: 13px;
          font-weight: 600;
          color: #1f2937;
        }
      }
    }
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 20px;
  }

  .quick-actions {
    display: flex;
    flex-direction: column;
    gap: 10px;

    .quick-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      height: 44px;
      border-radius: 10px;
      border: none;
      font-size: 14px;
      font-weight: 500;
      color: #fff;
      transition: transform 0.2s;

      &:hover {
        transform: translateY(-2px);
      }
    }

    .quick-content {
      background: linear-gradient(135deg, #4a9b8c, #2a6b60);
    }
    .quick-seo {
      background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), #6366f1);
    }
    .quick-model {
      background: linear-gradient(135deg, #10b981, #059669);
    }
    .quick-logs {
      background: linear-gradient(135deg, #f59e0b, #d97706);
    }
  }
}

@media (max-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
