<template>
  <YdPage title="物流看板" subtitle="建材物流运输全局监控" surface="elevated">
    <template #actions>
      <a-button @click="refresh"><ReloadOutlined /> 刷新</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">
    <a-row :gutter="16">
      <a-col :span="6" v-for="s in st" :key="s.l">
        <a-card hoverable><a-statistic :title="s.l" :value="s.v" :value-style="{ color: s.c }" /></a-card>
      </a-col>
    </a-row>
    <a-card title="运费统计概览">
      <a-row :gutter="16">
        <a-col :span="8" v-for="f in freightStats" :key="f.title">
          <a-card size="small" hoverable class="text-center">
            <p class="text-gray-400 text-sm">{{ f.title }}</p>
            <p class="text-2xl font-bold" :style="{ color: f.color }">{{ f.value }}</p>
            <p class="text-xs text-gray-400">{{ f.sub }}</p>
          </a-card>
        </a-col>
      </a-row>
    </a-card>
    <a-card title="最近订单 / 运单">
      <YdEmptyState
        v-if="!tableLoading && !orders.length"
        variant="inquiry"
        title="暂无订单数据"
        description="订单创建并填写运单号后，将在此展示真实物流状态。"
        @action="router.push('/logistics/orders-track')"
      />
      <div v-else ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar
            :loading="tableLoading"
            :target-ref="tablePanelRef"
            :show-export="false"
            @refresh="fetchDashboard"
          />
        </div>
        <YdDataTable
          :columns="cols"
          :data-source="orders"
          :loading="tableLoading"
          :pagination="{ current: 1, pageSize: 8, total: orders.length }"
          :table-props="{ size: tableSize, rowKey: 'id' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="record.status === 'delivered' ? 'success' : record.status === 'intransit' ? 'processing' : 'default'">
                {{ record.status === 'delivered' ? '已签收' : record.status === 'intransit' ? '在途' : record.has_tracking === false ? '待填单号' : '待发' }}
              </a-tag>
            </template>
            <template v-if="column.key === 'price'">
              <span class="font-semibold text-blue-600">¥{{ Number(record.price || 0).toLocaleString() }}</span>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { YdDataTable, YdEmptyState, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { apiGet } from '@/utils/api'

const router = useRouter()
const tablePanelRef = ref<HTMLElement | null>(null)
const tableLoading = ref(false)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const st = ref<{ l: string; v: number; c: string }[]>([])
const freightStats = ref<{ title: string; value: string; sub: string; color: string }[]>([])
const orders = ref<any[]>([])

const cols = [
  { title: '运单号', dataIndex: 'no', key: 'no' },
  { title: '发货地', dataIndex: 'from', key: 'from' },
  { title: '目的地', dataIndex: 'to', key: 'to' },
  { title: '货物', dataIndex: 'cargo', key: 'cargo', width: 140 },
  { title: '运费', key: 'price', width: 100 },
  { title: '状态', key: 'status', width: 80 },
  { title: '时效', dataIndex: 'eta', key: 'eta', width: 120 },
]

async function fetchDashboard() {
  tableLoading.value = true
  try {
    const data = await apiGet<any>('/logistics/')
    if (data.stats) st.value = data.stats
    if (data.freight_stats) freightStats.value = data.freight_stats
    if (data.orders) orders.value = data.orders
  } catch {
    st.value = []
    freightStats.value = []
    orders.value = []
  } finally {
    tableLoading.value = false
  }
}

async function refresh() {
  await fetchDashboard()
  message.success('看板已刷新')
}

onMounted(() => { fetchDashboard() })
</script>

<style scoped>
.panel-head {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}
</style>
