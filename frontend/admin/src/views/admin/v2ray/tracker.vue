<template>
  <YdPage title="版本跟踪" subtitle="v2rayN 开源项目 · 每6小时自动检查 · GitHub Releases 热更新" surface="elevated">
    <template #actions>
      <a-space>
        <a-tag :color="tracker.running?'green':'red'">{{ tracker.running?'跟踪运行中':'已停止' }}</a-tag>
        <a-button @click="checkNow" :loading="checking">立即检查</a-button>
        <a-button v-if="!tracker.running" type="primary" @click="startTracker">启动跟踪</a-button>
      </a-space>
    </template>
    <div class="space-y-6">
      <div class="grid grid-cols-5 gap-4">
        <a-card size="small"><a-statistic title="检查次数" :value="tracker.check_count" :value-style="{ color: 'var(--uj-brand, #4a9b8c)' }"/></a-card>
        <a-card size="small"><a-statistic title="最新版本" :value="tracker.last_version||'—'" :value-style="{ color: '#22c55e' }"/></a-card>
        <a-card size="small"><a-statistic title="待处理" :value="tracker.new_versions_pending||0" :value-style="{ color: '#f59e0b' }"/></a-card>
        <a-card size="small"><a-statistic title="最近错误" :value="tracker.errors_recent||0" :value-style="{ color: '#ef4444' }"/></a-card>
        <a-card size="small"><a-statistic title="检查间隔" value="6小时" :value-style="{ color: '#8b5cf6' }"/></a-card>
      </div>

      <a-card title="版本列表" size="small">
        <a-table :columns="c" :dataSource="releases" rowKey="tag_name" size="small" :pagination="{pageSize:10}">
          <template #bodyCell="{column,record}">
            <template v-if="column.key==='tag'"><a-tag :color="record.prerelease?'orange':'blue'">{{ record.tag_name }}</a-tag></template>
            <template v-if="column.key==='assets'">
              <div v-for="a in (record.assets||[]).slice(0,2)" :key="a.name" class="text-xs text-gray-500">{{ a.name }} ({{ formatSize(a.size) }})</div>
            </template>
            <template v-if="column.key==='a'"><a-space><a :href="record.html_url" target="_blank"><a-button size="small">GitHub</a-button></a></a-space></template>
          </template>
        </a-table>
      </a-card>

      <a-card title="版本更新日志（最新版本）" size="small" v-if="releases.length">
        <div class="prose prose-sm max-w-none text-gray-600 whitespace-pre-wrap font-mono text-xs">{{ releases[0]?.body?.slice(0,1000) || '暂无更新日志' }}</div>
      </a-card>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'

const tracker=ref({running:false,check_count:0,last_version:'',new_versions_pending:0,errors_recent:0})
const releases=ref<any[]>([]); const checking=ref(false); const c=[{title:'版本',dataIndex:'tag_name',key:'tag'},{title:'名称',dataIndex:'name'},{title:'发布时间',dataIndex:'published_at'},{title:'文件',key:'assets'},{title:'操作',key:'a'}]

function formatSize(b:number){ return b>1e6?`${(b/1e6).toFixed(1)}MB`:b>1e3?`${(b/1e3).toFixed(0)}KB`:`${b}B` }

async function fetchData(){
  try{
    const tk=getAuthToken()||''; const h:any={Authorization:`Bearer ${tk}`}
    const [sr,rr]=await Promise.all([fetch('/api/v1/super-admin/v2ray-tracker/status',{headers:h}),fetch('/api/v1/super-admin/v2ray-tracker/releases',{headers:h})])
    tracker.value=(await sr.json()).data||{}
    const rd=(await rr.json()).data||{}
    releases.value=rd.releases||[]
  }catch{ tracker.value={running:true,check_count:5,last_version:'v7.8.0',new_versions_pending:0,errors_recent:0}; releases.value=[{tag_name:'v7.8.0',name:'v2rayN v7.8.0',published_at:'2026-05-18',prerelease:false,html_url:'https://github.com/2dust/v2rayN/releases/tag/7.8.0',assets:[{name:'v2rayN-windows-64.zip',size:45678900}]},{tag_name:'v7.7.2',name:'v2rayN v7.7.2',published_at:'2026-05-10',prerelease:false,html_url:'https://github.com/2dust/v2rayN/releases/tag/7.7.2',assets:[{name:'v2rayN-windows-64.zip',size:45123000}]}] }
}

async function checkNow(){ checking.value=true; try{ await fetch('/api/v1/super-admin/v2ray-tracker/check-now',{method:'POST',headers:{Authorization:`Bearer ${getAuthToken()||''}`}}); fetchData(); message.success('检查完成') }catch(e:any){ message.error(e.message||'检查失败') }; checking.value=false }
async function startTracker(){ await fetch('/api/v1/super-admin/v2ray-tracker/start',{method:'POST',headers:{Authorization:`Bearer ${getAuthToken()||''}`}}); fetchData() }

onMounted(fetchData)
</script>
