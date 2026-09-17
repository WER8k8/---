/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage class="ai-logs" title="调用日志" subtitle="AI 调用记录 · Token 用量 · 费用统计" surface="elevated">
    <template #actions>
      <a-space>
        <a-range-picker v-model:value="dateRange" @change="loadLogs" />
        <a-button type="primary" :loading="loading" @click="loadLogs">
          <ReloadOutlined />
          刷新
        </a-button>
      </a-space>
    </template>

    <!-- Cost Summary Cards -->
    <a-row :gutter="[16, 16]" class="mb-5">
      <a-col :span="6" v-for="c in costCards" :key="c.label">
        <a-card size="small" hoverable>
          <a-statistic :title="c.label" :value="c.value" :suffix="c.suffix" :value-style="{ color: c.color }" />
        </a-card>
      </a-col>
    </a-row>

    <!-- Model Usage Distribution -->
    <a-row :gutter="16" class="mb-5">
      <a-col :span="8">
        <a-card title="模型调用分布" size="small">
          <div class="space-y-3">
            <div v-for="m in modelDistribution" :key="m.name">
              <div class="flex justify-between text-xs mb-1">
                <span>{{ m.name }}</span>
                <span class="font-medium">{{ m.percent }}%</span>
              </div>
              <a-progress :percent="m.percent" :stroke-color="m.color" size="small" />
            </div>
          </div>
        </a-card>
      </a-col>
      <a-col :span="16">
        <a-card title="近7天调用趋势" size="small">
          <div class="trend-chart">
            <div v-for="(d, i) in trend" :key="i" class="trend-bar-wrap">
              <div
                class="trend-bar"
                :style="{ height: (d.count / maxTrend * 160) + 'px' }"
              >
                <span class="trend-value">{{ d.count }}</span>
              </div>
              <span class="trend-label">{{ d.date }}</span>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- Logs Table -->
    <a-card title="调用记录" size="small">
      <div ref="logsPanelRef" class="yd-panel yd-table-panel">
        <YdTableToolbar
          :loading="loading"
          :target-ref="logsPanelRef"
          :show-export="false"
          @refresh="loadLogs"
        />
        <YdDataTable
          :columns="logCols"
          :data-source="logs"
          :loading="loading"
          :pagination="logsPagination"
          :table-props="{ size: tableSize, rowKey: 'id' }"
          @page-change="onLogsPageChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="record.status === 'success' ? 'green' : record.status === 'running' ? 'blue' : 'red'">
                {{ record.status === 'success' ? '成功' : record.status === 'running' ? '进行中' : '失败' }}
              </a-tag>
            </template>
            <template v-if="column.key === 'cost'">
              <span>${{ record.cost }}</span>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>

    <!-- Total Cost -->
    <a-card title="费用统计" class="mt-5" size="small">
      <a-row :gutter="16">
        <a-col :span="8">
          <div class="cost-stat">
            <span class="cost-label">今日费用</span>
            <span class="cost-value">${{ todayCost }}</span>
          </div>
        </a-col>
        <a-col :span="8">
          <div class="cost-stat">
            <span class="cost-label">本月累计</span>
            <span class="cost-value">${{ monthCost }}</span>
          </div>
        </a-col>
        <a-col :span="8">
          <div class="cost-stat">
            <span class="cost-label">预算使用</span>
            <a-progress :percent="budgetPercent" :stroke-color="budgetPercent > 80 ? '#ef4444' : '#22c55e'" />
          </div>
        </a-col>
      </a-row>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { getAuthToken } from '@/utils/api'

const loading = ref(false)
const logsPanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const logsPage = ref({ current: 1, pageSize: 10 })
const logsPagination = computed(() => ({
  current: logsPage.value.current,
  pageSize: logsPage.value.pageSize,
  total: logs.value.length,
}))
function onLogsPageChange(p: { current: number; pageSize: number }) {
  logsPage.value = { current: p.current, pageSize: p.pageSize }
}
const dateRange = ref<[string, string] | undefined>(undefined)
const logs = ref<any[]>([])
const todayCost = ref('0.00')
const monthCost = ref('0.00')
const budgetPercent = ref(45)

const logCols = [
  { title: '时间', dataIndex: 'time', key: 'time', width: 160 },
  { title: '模型', dataIndex: 'model', key: 'model', width: 140 },
  { title: '类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: 'Token 数', dataIndex: 'tokens', key: 'tokens', width: 100 },
  { title: '耗时', dataIndex: 'duration', key: 'duration', width: 100 },
  { title: '费用', key: 'cost', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '用户', dataIndex: 'user', key: 'user', width: 100 },
]

const costCards = [
  { label: '今日调用', value: '--', suffix: '次', color: '#4a9b8c' },
  { label: 'Token 总数', value: '--', suffix: '', color: '#8b5cf6' },
  { label: '平均延迟', value: '--', suffix: 'ms', color: '#22c55e' },
  { label: '错误率', value: '--', suffix: '%', color: '#f59e0b' },
]

const modelDistribution = ref<{ name: string; percent: number; color: string }[]>([])

const trend = ref<{ date: string; count: number }[]>([])

const maxTrend = computed(() => Math.max(...trend.value.map(d => d.count), 1))

async function loadLogs() {
  loading.value = true
  try {
    const tk = getAuthToken() || ''
    const h: any = { Authorization: `Bearer ${tk}` }

    const [sumRes, logRes, modelsRes, trendRes] = await Promise.all([
      fetch('/api/v1/ai-usage/overview', { headers: h }).catch(() => null),
      fetch('/api/v1/ai-usage/logs', { headers: h }).catch(() => null),
      fetch('/api/v1/ai-usage/models', { headers: h }).catch(() => null),
      fetch('/api/v1/ai-usage/trend?days=7', { headers: h }).catch(() => null),
    ])

    if (sumRes && sumRes.ok) {
      const sd = (await sumRes.json()).data || {}
      costCards[0].value = sd.total_calls ?? '--'
      costCards[1].value = sd.total_tokens ?? '--'
      costCards[2].value = sd.avg_latency ?? '--'
      costCards[3].value = sd.error_rate ?? '--'
      todayCost.value = sd.today_cost?.toFixed(2) || '0.00'
      monthCost.value = sd.month_cost?.toFixed(2) || '0.00'
      if (sd.budget_percent != null) budgetPercent.value = sd.budget_percent
    }

    if (logRes && logRes.ok) {
      const ld = (await logRes.json()).data || []
      logs.value = ld.map((item: any, idx: number) => ({
        id: idx + 1,
        time: item.created_at || new Date().toLocaleString('zh-CN'),
        model: item.model || '--',
        type: item.task_type || 'AI调用',
        tokens: item.total_tokens || '--',
        duration: item.duration_ms ? item.duration_ms + 'ms' : '--',
        cost: item.cost?.toFixed(4) || '0',
        status: item.status || 'success',
        user: item.user || 'admin',
      }))
    }

    if (modelsRes && modelsRes.ok) {
      const md = (await modelsRes.json()).data || []
      if (Array.isArray(md)) modelDistribution.value = md
    }

    if (trendRes && trendRes.ok) {
      const td = (await trendRes.json()).data || []
      if (Array.isArray(td)) trend.value = td
    }
  } catch {
    // API not available, show empty state
  } finally {
    loading.value = false
  }
}

onMounted(loadLogs)
</script>

<style scoped lang="scss">
.ai-logs {
  .mb-5 {
    margin-bottom: 20px;
  }
  .mt-5 {
    margin-top: 20px;
  }

  .trend-chart {
    display: flex;
    align-items: flex-end;
    gap: 8px;
    height: 200px;
    padding: 8px 0;

    .trend-bar-wrap {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 100%;
      justify-content: flex-end;
    }

    .trend-bar {
      width: 100%;
      max-width: 40px;
      background: linear-gradient(180deg, #4a9b8c, #2a6b60);
      border-radius: 4px 4px 0 0;
      position: relative;
      transition: height 0.3s;
      min-height: 4px;

      .trend-value {
        position: absolute;
        top: -18px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 10px;
        color: #64748b;
        white-space: nowrap;
      }
    }

    .trend-label {
      font-size: 10px;
      color: #94a3b8;
      margin-top: 4px;
    }
  }

  .cost-stat {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .cost-label {
      font-size: 13px;
      color: #94a3b8;
    }
    .cost-value {
      font-size: 24px;
      font-weight: 700;
      color: #1f2937;
    }
  }
}
</style>
