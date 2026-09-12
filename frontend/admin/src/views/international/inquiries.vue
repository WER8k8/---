<template>
  <YdPage class="intl-inquiries" title="海外询盘" subtitle="按地区、状态筛选并管理国际客户询盘" surface="elevated">
    <!-- 筛选栏 -->
    <a-card size="small" class="mb-4">
      <a-row :gutter="[16, 12]" align="middle">
        <a-col :span="6">
          <span class="filter-label">地区</span>
          <a-select v-model:value="filters.region" allow-clear placeholder="全部地区" style="width:100%" @change="() => loadData()">
            <a-select-option v-for="r in regionOptions" :key="r.value" :value="r.value">{{ r.label }} ({{ r.value }})</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <span class="filter-label">状态</span>
          <a-select v-model:value="filters.status" allow-clear placeholder="全部状态" style="width:100%" @change="() => loadData()">
            <a-select-option value="pending">待处理</a-select-option>
            <a-select-option value="contacted">已联系</a-select-option>
            <a-select-option value="converted">已转换</a-select-option>
            <a-select-option value="closed">已关闭</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <span class="filter-label">时间</span>
          <a-date-picker v-model:value="filters.date" style="width:100%" @change="() => loadData()" />
        </a-col>
        <a-col :span="6" class="text-right">
          <a-space>
            <a-button @click="resetFilters">重置</a-button>
            <a-button type="primary" @click="loadData">
              <template #icon><SearchOutlined /></template>
              查询
            </a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- 统计条 -->
    <a-row :gutter="12" class="mb-4">
      <a-col :span="6" v-for="s in summaryStats" :key="s.key">
        <a-card size="small">
          <a-statistic :title="s.title" :value="s.value" :value-style="{ color: s.color }" />
        </a-card>
      </a-col>
    </a-row>

    <a-card size="small">
      <div ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar
            :loading="loading"
            :target-ref="tablePanelRef"
            :show-export="false"
            @refresh="loadData"
          />
        </div>
        <YdDataTable
          :columns="columns"
          :data-source="list"
          :loading="loading"
          :pagination="tablePagination"
          :table-props="{ size: tableSize, rowKey: 'id', scroll: { x: 1200 } }"
          @page-change="onPageChange"
        >
          <template #expandedRowRender="{ record }">
            <div class="p-3 bg-gray-50 rounded text-sm text-gray-800">
              {{ record.detail || record.requirement || '暂无详细需求原文' }}
            </div>
          </template>
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'country'">
              <span class="country-cell">{{ record.country }}</span>
            </template>
            <template v-if="column.key === 'language'">
              <a-tag>{{ record.language }}</a-tag>
            </template>
            <template v-if="column.key === 'budget'">
              <span v-if="record.budget" class="budget-cell">{{ record.budget }}</span>
              <span v-else class="text-gray-400">--</span>
            </template>
            <template v-if="column.key === 'status'">
              <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
            </template>
            <template v-if="column.key === 'actions'">
              <a-space>
                <a-button size="small" type="link" @click="markContacted(record)" :disabled="record.status !== 'pending'">标记已联系</a-button>
                <a-button size="small" type="primary" ghost @click="markConverted(record)" :disabled="record.status === 'converted' || record.status === 'closed'">标记转换</a-button>
                <a-button size="small" danger @click="markClosed(record)" :disabled="record.status === 'closed'">关闭</a-button>
              </a-space>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { message } from 'ant-design-vue'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import {
  Card as ACard, Row as ARow, Col as ACol, Statistic as AStatistic,
  Tag as ATag, Button as AButton, Space as ASpace,
  Select as ASelect, SelectOption as ASelectOption,
  DatePicker as ADatePicker,
} from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import { apiGet, apiPut } from '@/utils/api'
import { COUNTRY_OPTIONS } from '@/constants/countryOptions'

const loading = ref(false)
const list = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const tablePagination = computed(() => ({
  current: page.value,
  pageSize: pageSize.value,
  total: total.value,
}))

const filters = reactive({
  region: undefined as string | undefined,
  status: undefined as string | undefined,
  date: undefined as any,
})

const regionOptions = COUNTRY_OPTIONS.map((c) => ({ value: c.value, label: c.label }))

const summaryStats = ref<any[]>([])

const columns = [
  { title: '国家', key: 'country', width: 110 },
  { title: '客户名', dataIndex: 'customer', width: 120 },
  { title: '电话', dataIndex: 'phone', width: 130 },
  { title: '邮箱', dataIndex: 'email', width: 170 },
  { title: '意向产品', dataIndex: 'product', width: 160 },
  { title: '预算', key: 'budget', width: 110 },
  { title: '语言', key: 'language', width: 80 },
  { title: '来源网站', dataIndex: 'source', width: 140 },
  { title: '采集时间', dataIndex: 'created_at', width: 150 },
  { title: '状态', key: 'status', width: 90 },
  { title: '操作', key: 'actions', width: 280, fixed: 'right' as const },
]

function onPageChange(p: { current: number; pageSize: number }) {
  page.value = p.current
  pageSize.value = p.pageSize
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, string> = {
      page: String(page.value),
      page_size: String(pageSize.value),
    }
    if (filters.region) params.region = filters.region
    if (filters.status) params.status = filters.status
    if (filters.date) params.date = filters.date.format?.('YYYY-MM-DD') || String(filters.date)

    const result = await apiGet<any>('/international/inquiries', params)
    if (result && Array.isArray(result.list)) {
      list.value = result.list
      total.value = result.total ?? result.list.length
      if (result.stats) {
        summaryStats.value[0].value = result.stats.total ?? 0
        summaryStats.value[1].value = result.stats.pending ?? 0
        summaryStats.value[2].value = result.stats.contacted ?? 0
        summaryStats.value[3].value = result.stats.converted ?? 0
      }
    } else if (Array.isArray(result)) {
      list.value = result
      total.value = result.length
    } else {
      list.value = []
      total.value = 0
    }
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.region = undefined
  filters.status = undefined
  filters.date = undefined
  page.value = 1
  loadData()
}

function statusColor(s: string) {
  const map: Record<string, string> = { pending: 'blue', contacted: 'orange', converted: 'green', closed: 'default' }
  return map[s] || 'default'
}
function statusLabel(s: string) {
  const map: Record<string, string> = { pending: '待处理', contacted: '已联系', converted: '已转换', closed: '已关闭' }
  return map[s] || s
}

async function markContacted(record: any) {
  try {
    await apiPut(`/international/inquiries/${record.id}`, { status: 'contacted' })
    message.success(`已将 ${record.customer} 标记为「已联系」`)
    await loadData()
  } catch {
    message.error('状态更新失败')
  }
}

async function markConverted(record: any) {
  try {
    await apiPut(`/international/inquiries/${record.id}`, { status: 'converted' })
    message.success(`已将 ${record.customer} 标记为「已转换」`)
    await loadData()
  } catch {
    message.error('状态更新失败')
  }
}

async function markClosed(record: any) {
  try {
    await apiPut(`/international/inquiries/${record.id}`, { status: 'closed' })
    message.success(`已将 ${record.customer} 标记为「已关闭」`)
    await loadData()
  } catch {
    message.error('状态更新失败')
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.filter-label { font-size: 0.75rem; color: #64748b; margin-bottom: 4px; display: block; }
.country-cell { font-weight: 500; }
.budget-cell { font-weight: 500; color: #059669; }
.text-right { text-align: right; }
</style>
