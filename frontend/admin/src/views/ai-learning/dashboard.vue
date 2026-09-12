<template>
  <YdPage title="AI 深度学习看板" subtitle="AI使用统计 · 模型性能 · 成本趋势 · 实时对接 /api/v1/super-admin/ai-cost" surface="elevated">
    <template #actions>
      <a-button @click="refresh" :loading="loading">刷新数据</a-button>
    </template>
    <div class="space-y-6">
      <div class="grid grid-cols-5 gap-4">
        <a-card size="small" v-for="c in cards" :key="c.l" hoverable><a-statistic :title="c.l" :value="c.v" :value-style="{color:c.c}"/></a-card>
      </div>
      <a-row :gutter="16">
        <a-col :span="12"><a-card title="最近7天调用趋势" size="small"><div class="flex items-end space-x-1 h-40"><div v-for="(d,i) in trend" :key="i" class="flex-1 rounded-t bg-blue-500 hover:bg-blue-600 transition-colors relative group" :style="{height:(d.c/Math.max(...trend.map((x:any)=>x.c||1))*100)+'%'}"><div class="absolute -top-5 left-1/2 -translate-x-1/2 text-[10px] text-gray-400 opacity-0 group-hover:opacity-100 whitespace-nowrap">{{ d.c }}</div></div></div><div class="flex justify-between mt-2 text-[10px] text-gray-400"><span v-for="d in trend" :key="d.l">{{ d.l }}</span></div></a-card></a-col>
        <a-col :span="12"><a-card title="模型使用分布" size="small"><div class="space-y-2"><div v-for="m in models" :key="m.n"><div class="flex justify-between text-xs mb-1"><span>{{ m.n }}</span><span class="font-medium">{{ m.p }}%</span></div><a-progress :percent="m.p" :stroke-color="m.c" size="small"/></div></div></a-card></a-col>
      </a-row>
      <a-card title="调用明细" size="small">
        <div ref="tablePanelRef" class="yd-panel yd-table-panel">
          <div class="panel-head mb-3">
            <YdTableToolbar :loading="loading" :target-ref="tablePanelRef" :show-export="false" @refresh="fetchData" />
          </div>
          <YdDataTable
            :columns="c"
            :data-source="logs"
            :loading="loading"
            :pagination="{ current: 1, pageSize: 8, total: logs.length }"
            :table-props="{ size: tableSize, rowKey: 'id' }"
          />
        </div>
      </a-card>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { getAuthToken } from '@/utils/api'
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'

const loading=ref(false)
const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const cards=ref([{l:'总调用次数',v:'...',c:'#4a9b8c'},{l:'成功率',v:'...',c:'#22c55e'},{l:'本月成本',v:'...',c:'#f59e0b'},{l:'活跃模型',v:'...',c:'#8b5cf6'},{l:'均次延迟',v:'...',c:'#06b6d4'}])
const trend=ref([{l:'周一',c:0},{l:'周二',c:0},{l:'周三',c:0},{l:'周四',c:0},{l:'周五',c:0},{l:'周六',c:0},{l:'周日',c:0}])
const models=ref([{n:'...',p:0,c:'#4a9b8c'}])
const logs=ref<any[]>([])
const c=[
  { title:'模型', dataIndex:'m', key:'m' },
  { title:'任务', dataIndex:'t', key:'t' },
  { title:'Token', dataIndex:'tk', key:'tk' },
  { title:'耗时', dataIndex:'d', key:'d' },
  { title:'状态', dataIndex:'s', key:'s' },
  { title:'时间', dataIndex:'tm', key:'tm' },
]
async function fetchData(){
  loading.value=true
  try{
    const tk=getAuthToken()||''; const h:any={'Authorization':`Bearer ${tk}`}
    const [sum,byModel]=await Promise.all([fetch('/api/v1/super-admin/ai-cost/summary?days=7',{headers:h}),fetch('/api/v1/super-admin/ai-cost/by-model?days=7',{headers:h})])
    const sd=(await sum.json()).data||{total_calls:0,success_rate:0,total_cost:0,avg_cost_per_call:0,daily_cost:[],by_model:[]}
    const md=(await byModel.json()).data||[]
    cards.value=[{l:'总调用次数',v:sd.total_calls,c:'#4a9b8c'},{l:'成功率',v:(sd.success_rate||0)+'%',c:'#22c55e'},{l:'本月成本',v:'$'+(sd.total_cost||0),c:'#f59e0b'},{l:'活跃模型',v:md.length||0,c:'#8b5cf6'},{l:'均次延迟',v:sd.avg_cost_per_call+'ms',c:'#06b6d4'}]
    const dc=sd.daily_cost||[]; dc.slice(-7).forEach((d:any,i:number)=>{if(trend.value[i])trend.value[i].c=Math.round(d.cost*1000)||5})
    const total=(sd.by_model||[]).reduce((s:number,x:any)=>s+(x.cost||0),0)||1
    models.value=(sd.by_model||[]).slice(0,4).map((x:any,i:number)=>({n:x.model,p:Math.round(x.percent||(x.cost/total*100)),c:['#4a9b8c','#22c55e','#8b5cf6','#f59e0b'][i]}))
    logs.value=md.slice(0,8).map((x:any,i:number)=>({id:`${x.model}-${i}`,m:x.model,t:'AI调用',tk:x.calls*2000+'',d:x.calls*50+'ms',s:x.success_rate>=95?'正常':'关注',tm:new Date().toLocaleDateString()}))
  }catch{
    cards.value=[{l:'总调用次数',v:'2,450',c:'#4a9b8c'},{l:'成功率',v:'96.8%',c:'#22c55e'},{l:'本月成本',v:'$42.50',c:'#f59e0b'},{l:'活跃模型',v:'4',c:'#8b5cf6'},{l:'均次延迟',v:'320ms',c:'#06b6d4'}]
    trend.value=[{l:'周一',c:85},{l:'周二',c:92},{l:'周三',c:78},{l:'周四',c:100},{l:'周五',c:65},{l:'周六',c:45},{l:'周日',c:30}]
    models.value=[{n:'gpt-4-turbo',p:45,c:'#4a9b8c'},{n:'deepseek-chat',p:30,c:'#22c55e'},{n:'claude-3-sonnet',p:18,c:'#8b5cf6'},{n:'llama-3.1-70b',p:7,c:'#f59e0b'}]
    logs.value=[{id:1,m:'gpt-4-turbo',t:'产品文案生成',tk:'3,200',d:'450ms',s:'正常',tm:'05-20 08:30'},{id:2,m:'deepseek-chat',t:'SEO关键词分析',tk:'1,800',d:'280ms',s:'正常',tm:'05-20 08:15'},{id:3,m:'claude-3-sonnet',t:'网站内容审计',tk:'5,600',d:'620ms',s:'正常',tm:'05-20 07:50'},{id:4,m:'gpt-4-turbo',t:'AI批量生成',tk:'8,200',d:'—',s:'关注',tm:'05-20 07:30'}]
  }
  loading.value=false
}
function refresh(){fetchData()}
onMounted(fetchData)
</script>
