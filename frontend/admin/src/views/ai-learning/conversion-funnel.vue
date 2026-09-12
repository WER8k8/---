<template>
  <YdPage title="转化漏斗" subtitle="访问→浏览→询盘→成交 全链路转化分析" surface="elevated">
    <template #actions>
      <a-select v-model:value="period" style="width:120px" @change="refresh">
        <a-select-option value="7d">近7天</a-select-option>
        <a-select-option value="30d">近30天</a-select-option>
      </a-select>
    </template>
    <a-alert
      v-if="disclaimer"
      type="info"
      show-icon
      class="mb-4"
      :message="disclaimer"
    />
    <a-empty v-if="isEmpty && !loading" description="所选周期暂无站点访问，完成绑域与首发后再看漏斗" />
    <div v-else class="space-y-6">
      <div class="grid grid-cols-4 gap-4">
        <a-card v-for="(l,i) in funnel" :key="l.name" class="text-center" :class="'border-t-4 '+l.border">
          <div class="funnel-icon mb-2">
            <YdNavIcon :name="l.iconKey" size="lg" />
          </div>
          <a-statistic :title="l.name" :value="l.count"/>
          <div class="text-xs mt-1" :class="i>0?'text-red-500':'text-gray-400'">{{ i>0 ? `流失 ${l.loss}%` : '' }}</div>
          <div class="text-xs text-gray-400 mt-1">转化率 {{ l.rate }}%</div>
        </a-card>
      </div>
      <a-card title="漏斗可视化" size="small">
        <div class="space-y-3">
          <div v-for="(l,i) in funnel" :key="l.name"><div class="flex justify-between text-sm mb-1"><span>{{ l.name }}</span><span class="font-medium">{{ l.count }} 人 ({{ l.rate }}%)</span></div><a-progress :percent="l.rate" :stroke-color="['var(--uj-brand, #4a9b8c)','#818cf8','#a78bfa','#f472b6'][i]" size="small"/></div>
        </div>
      </a-card>
      <a-card title="流失原因分析" size="small">
        <a-empty v-if="!lossReasons.length" description="暂无显著流失段，或样本量不足" />
        <div v-else ref="tablePanelRef" class="yd-panel yd-table-panel">
          <div class="panel-head mb-3">
            <YdTableToolbar :loading="loading" :target-ref="tablePanelRef" :show-export="false" @refresh="refresh" />
          </div>
          <YdDataTable
            :columns="c"
            :data-source="lossReasons"
            :pagination="false"
            :table-props="{ size: tableSize, rowKey: 'id' }"
          />
        </div>
      </a-card>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdNavIcon, YdPage, YdTableToolbar } from '@/components/youding'
import { FUNNEL_STAGE_ICONS } from '@/constants/iconCatalog'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { apiGet } from '@/utils/api'

const period=ref('7d')
const loading = ref(false)
const isEmpty = ref(false)
const disclaimer = ref('')
const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
type FunnelStep = { name: string; iconKey: string; count: number; loss: number; rate: number; border: string }
const funnel = ref<FunnelStep[]>([
  { name: '访问页面', iconKey: FUNNEL_STAGE_ICONS[0], count: 0, loss: 0, rate: 0, border: 'border-blue-500' },
  { name: '浏览内容', iconKey: FUNNEL_STAGE_ICONS[1], count: 0, loss: 0, rate: 0, border: 'border-indigo-500' },
  { name: '提交询盘', iconKey: FUNNEL_STAGE_ICONS[2], count: 0, loss: 0, rate: 0, border: 'border-violet-500' },
  { name: '成交转化', iconKey: FUNNEL_STAGE_ICONS[3], count: 0, loss: 0, rate: 0, border: 'border-pink-500' },
])
const c=[
  { title:'流失环节', dataIndex:'s', key:'s' },
  { title:'原因', dataIndex:'r', key:'r' },
  { title:'影响用户数', dataIndex:'n', key:'n' },
  { title:'建议', dataIndex:'a', key:'a' },
]
const lossReasons=ref<{id:number;s:string;r:string;n:number;a:string}[]>([])

async function refresh(){
  loading.value = true
  try {
    const data = await apiGet<{
      funnel?: Array<{ name: string; count: number; loss: number; rate: number; border: string }>
      loss_reasons?: typeof lossReasons.value
      is_empty?: boolean
      disclaimer?: string
    }>(`/ai-learning/conversion-funnel?period=${period.value}`)
    isEmpty.value = Boolean(data?.is_empty)
    disclaimer.value = data?.disclaimer || '基于租户站点真实埋点'
    const rows = data?.funnel || []
    funnel.value = rows.map((row, i) => ({
      name: row.name,
      iconKey: FUNNEL_STAGE_ICONS[i] || FUNNEL_STAGE_ICONS[0],
      count: row.count ?? 0,
      loss: row.loss ?? 0,
      rate: row.rate ?? 0,
      border: row.border || funnel.value[i]?.border || 'border-blue-500',
    }))
    lossReasons.value = data?.loss_reasons || []
  } catch {
    isEmpty.value = true
    disclaimer.value = '暂时无法加载漏斗数据'
  } finally {
    loading.value = false
  }
}
onMounted(refresh)
</script>
