<template>
  <YdPage title="合规治理中心" subtitle="/api/v1/compliance 全局治理视图" surface="elevated">
    <template #actions>
      <a-space>
        <a-button class="rounded-xl" :loading="reportLoading" @click="fetchReport">合规报告</a-button>
        <a-button type="primary" class="rounded-xl" :loading="auditLoading" @click="runAudit">运行审计</a-button>
      </a-space>
    </template>
  <div class="page-wrap">
    <div v-if="overview" class="stats">
      <div v-for="s in statCards" :key="s.label" class="stat glass"><span class="stat-val">{{ s.value }}</span><span class="stat-lab">{{ s.label }}</span></div>
    </div>
    <div v-else class="glass panel text-center py-8 text-gray-400">加载中...</div>

    <div ref="issuesTablePanelRef" class="glass panel">
      <div class="panel-head-row">
        <h2 class="panel-title">问题列表</h2>
        <YdTableToolbar
          :loading="issuesLoading"
          :target-ref="issuesTablePanelRef"
          :show-export="false"
          @refresh="loadIssues"
        />
      </div>
      <YdDataTable
        :columns="issueCols"
        :data-source="issues"
        :loading="issuesLoading"
        :pagination="false"
        :table-props="{ rowKey: 'id', size: tableSize }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'severity'">
            <a-tag :color="record.severity === 'critical' ? 'red' : record.severity === 'warning' ? 'orange' : 'blue'">
              {{ record.severity === 'critical' ? '严重' : record.severity === 'warning' ? '警告' : '提示' }}
            </a-tag>
          </template>
        </template>
      </YdDataTable>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { message } from 'ant-design-vue';
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import { getAuthToken } from '@/utils/api';

const overview = ref<any>(null); const auditLoading = ref(false); const reportLoading = ref(false)
const issuesLoading = ref(false); const issues = ref<any[]>([])
const issuesTablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const statCards = computed(() => {
  const o = overview.value; if (!o) return []
  return [{label:'综合得分',value:o.overall_score??'—'},{label:'问题总数',value:o.total_issues??0},{label:'严重',value:o.critical_issues??0},{label:'警告',value:o.warnings??0},{label:'已通过',value:o.passed_checks??0}]
})

const issueCols = [{title:'ID',dataIndex:'id',width:120},{title:'标题',dataIndex:'title'},{title:'级别',dataIndex:'severity',key:'severity',width:100}]

async function api(path:string,method='GET',body?:any){
  const h:any={Authorization:`Bearer ${getAuthToken()}`}; if(body)h['Content-Type']='application/json'
  const r=await fetch(`/api/v1${path}`,{method,headers:h,body:body?JSON.stringify(body):undefined})
  if(!r.ok)throw new Error(`HTTP ${r.status}`); const d=await r.json(); return d.data||d
}

async function loadOverview(){
  try{
    const res=await api('/compliance')
    overview.value=res||null
  } catch {
    overview.value = null
    message.error('无法加载合规概览，请检查后端服务')
  }
}

async function loadIssues(){
  issuesLoading.value=true
  try{
    const res=await api('/compliance/issues', 'GET')
    if(Array.isArray(res)) issues.value=res
    else if(res?.items) issues.value=res.items
    else issues.value = []
  }catch{
    issues.value=[]
    message.error('无法加载问题列表')
  }
  issuesLoading.value=false
}

async function runAudit(){
  auditLoading.value=true
  try{await api('/compliance/audit'); message.success('审计已完成'); await loadOverview(); await loadIssues()}
  catch{ message.error('审计提交失败') }
  auditLoading.value=false
}

async function fetchReport(){
  reportLoading.value=true
  try{const res=await api('/compliance/report'); message.success('报告已生成')}
  catch{message.warning('报告生成中，请稍后刷新页面查看')}
  reportLoading.value=false
}

onMounted(()=>{loadOverview();loadIssues()})
</script>

<style scoped lang="scss">
.page-wrap{display:flex;flex-direction:column;gap:1.25rem}
.glass{background:rgba(255,255,255,0.55);border:1px solid rgba(255,255,255,0.65);border-radius:22px;box-shadow:0 8px 32px rgba(31,38,135,0.08);backdrop-filter:blur(16px)}
.head{padding:1.25rem 1.5rem;display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:1rem}
.title{margin:0;font-size:1.5rem;font-weight:700;color:#0f172a}
.sub{margin:0.35rem 0 0;font-size:0.85rem;color:#64748b}
.code{font-size:0.78rem;background:rgba(15,23,42,0.06);padding:0.1rem 0.35rem;border-radius:6px}
.panel{padding:1rem 1.25rem 1.25rem}
.panel-head-row{display:flex;justify-content:space-between;align-items:center;gap:1rem;margin-bottom:1rem;flex-wrap:wrap}
.panel-title{font-size:1rem;font-weight:600;margin:0}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:1rem}
.stat{padding:1rem 1.25rem;display:flex;flex-direction:column;align-items:center}
.stat-val{font-size:1.5rem;font-weight:700;color:#1e293b}
.stat-lab{font-size:0.75rem;color:#64748b}
</style>
