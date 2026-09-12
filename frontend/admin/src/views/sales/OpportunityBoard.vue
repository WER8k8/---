<template>
  <YdPage surface="elevated">
    <div class="opportunity-board">
      <div class="flex items-center justify-between mb-6">
        <div><h2 class="text-xl font-bold text-gray-900">销售管道</h2><p class="text-sm text-gray-400">Pipeline 总值: ${{ pipelineValue.toLocaleString() }} | {{ totalOpportunities }} 个机会</p></div>
        <div class="flex gap-2">
          <a-select v-model:value="filterStage" placeholder="筛选阶段" allow-clear style="width:160px" @change="fetchData">
            <a-select-option v-for="s in stages" :key="s" :value="s">{{ s }}</a-select-option>
          </a-select>
          <a-input-search v-model:value="searchText" placeholder="搜索公司/名称" style="width:200px" @search="fetchData" />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div v-for="s in stages" :key="s" class="stage-card" :class="stageColor(s)" @click="filterStage = s; fetchData()">
          <p class="text-xs text-white/70">{{ s }}</p>
          <p class="text-2xl font-bold text-white">{{ stageCounts[s] || 0 }}</p>
        </div>
      </div>

      <a-table :dataSource="opportunities" :columns="columns" :loading="loading" :pagination="{ total, pageSize: 20, current: page }" rowKey="id" @change="handleTableChange" size="middle">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'stage'">
            <a-select :value="record.stage" size="small" style="width:130px" @change="(v) => updateStage(record.id, v as string)">
              <a-select-option v-for="s in stages" :key="s" :value="s">{{ s }}</a-select-option>
            </a-select>
          </template>
          <template v-else-if="column.key === 'value'">
            ${{ (record.value || 0).toLocaleString() }} ({{ record.probability }}%)
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" size="small" @click="viewDetail(record)">详情</a-button>
          </template>
        </template>
      </a-table>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { YdPage } from '@/components/youding'
import { message } from 'ant-design-vue'

const stages = ['Lead','Qualified','Contacted','Engaged','RFQ','Quotation','Negotiation','Won','Lost']
const stageColor = (s: string) => ({ 'bg-blue-600': ['Lead','Qualified','Contacted'].includes(s), 'bg-emerald-600': ['Engaged','RFQ','Quotation'].includes(s), 'bg-amber-600': ['Negotiation'].includes(s), 'bg-green-600': s === 'Won', 'bg-red-500': s === 'Lost' })

const authHeaders = () => ({ Authorization: `Bearer ${localStorage.getItem('admin_token') || sessionStorage.getItem('admin_token')}` })

const opportunities = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filterStage = ref<string | undefined>(undefined)
const searchText = ref('')
const stageCounts = ref<Record<string, number>>({})
const pipelineValue = ref(0)
const totalOpportunities = ref(0)

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name', width: 200 },
  { title: '公司', dataIndex: 'company', key: 'company', width: 150 },
  { title: '阶段', dataIndex: 'stage', key: 'stage', width: 150 },
  { title: '金额(概率)', key: 'value', width: 140 },
  { title: '负责人', dataIndex: 'assigned_to', key: 'assigned_to', width: 100 },
  { title: '操作', key: 'action', width: 60 },
]

async function fetchData() {
  loading.value = true
  try {
    const params = new URLSearchParams({ page: String(page.value), page_size: '20' })
    if (filterStage.value) params.set('stage', filterStage.value)
    if (searchText.value) params.set('search', searchText.value)
    const [listRes, statsRes] = await Promise.all([
      fetch(`/api/v1/opportunity?${params}`, { headers: authHeaders() }),
      fetch('/api/v1/opportunity/stats', { headers: authHeaders() }),
    ])
    const list = await listRes.json()
    const stats = await statsRes.json()
    if (list.code === 0) { opportunities.value = list.data.items; total.value = list.data.total }
    if (stats.code === 0) { stageCounts.value = stats.data.by_stage; pipelineValue.value = stats.data.pipeline_value; totalOpportunities.value = stats.data.total }
  } catch { message.error('加载失败') }
  finally { loading.value = false }
}

async function updateStage(id: string, stage: string) {
  try {
    const r = await fetch(`/api/v1/opportunity/${id}/stage`, { method: 'PUT', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ stage }) })
    const j = await r.json()
    if (j.code === 0) { message.success('阶段已更新'); fetchData() }
    else message.error(j.message)
  } catch { message.error('更新失败') }
}

function handleTableChange(p: any) { page.value = p.current; fetchData() }
function viewDetail(r: any) { /* TODO: detail drawer */ message.info(`看板: ${r.name}`) }
onMounted(fetchData)
</script>
<style scoped>
.opportunity-board { animation: fadeIn .3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.stage-card { padding: 1rem; border-radius: 12px; cursor: pointer; transition: transform .15s; }
.stage-card:hover { transform: scale(1.03); }
</style>
