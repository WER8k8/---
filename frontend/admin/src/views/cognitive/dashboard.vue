<template>
  <YdPage title="知识图谱" subtitle="建材行业知识库 · 语义索引 · RAG检索" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="fetchData">刷新</a-button>
        <a-button type="primary" @click="showImport=true">导入数据</a-button>
      </a-space>
    </template>
    <div class="space-y-6">
    <a-row :gutter="16"><a-col :span="6" v-for="s in stats" :key="s.l"><a-card hoverable size="small"><a-statistic :title="s.l" :value="s.v" :value-style="{color:s.c}"/></a-card></a-col></a-row>
    <a-row :gutter="16">
      <a-col :span="12"><a-card title="知识库分布" size="small"><a-table :columns="kc" :dataSource="kb" rowKey="name" size="small" :pagination="false"/></a-card></a-col>
      <a-col :span="12"><a-card title="语义搜索" size="small"><a-input-search v-model:value="sq" placeholder="如：LC20混凝土适用场景？" enter-button="搜索" @search="doSearch" :loading="sl"/><div v-if="sr" class="mt-3 p-3 bg-blue-50 rounded-lg text-sm whitespace-pre-wrap">{{ sr }}</div></a-card></a-col>
    </a-row>
    <a-card title="查询历史" size="small"><a-table :columns="qc" :dataSource="queries" rowKey="id" size="small" :pagination="{pageSize:8}"><template #bodyCell="{column,record}"><template v-if="column.key==='s'"><a-tag :color="record.h>0?'green':'red'">{{ record.h>0?'命中':'未找到' }}</a-tag></template></template></a-table></a-card>
    <a-modal v-model:open="showImport" title="导入知识数据" @ok="doImport"><a-form layout="vertical"><a-form-item label="类型"><a-select v-model:value="it"><a-select-option value="pdf">PDF文档</a-select-option><a-select-option value="csv">CSV数据</a-select-option></a-select></a-form-item><a-form-item label="文件/URL"><a-input v-model:value="iu"/></a-form-item></a-form></a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue'; import { message } from 'ant-design-vue'; import { YdPage } from '@/components/youding'; import { getAuthToken } from '@/utils/api'
const stats = ref<any[]>([])
const kb = ref<any[]>([])
const kc=[{title:'知识库',dataIndex:'name'},{title:'文档',dataIndex:'docs'},{title:'片段',dataIndex:'chunks'},{title:'状态',dataIndex:'status'}]
const sq=ref(''); const sl=ref(false); const sr=ref(''); const showImport=ref(false); const it=ref('pdf'); const iu=ref('')
const qc=[{title:'查询',dataIndex:'q'},{title:'命中',dataIndex:'h'},{title:'结果',key:'s'},{title:'时间',dataIndex:'t'}]
const queries = ref<any[]>([])
async function api(p:string,m='GET',b?:any){const h:any={Authorization:`Bearer ${getAuthToken()}`};if(b)h['Content-Type']='application/json';const r=await fetch(`/api/v1/super-admin${p}`,{method:m,headers:h,body:b?JSON.stringify(b):undefined});if(!r.ok)throw new Error(`HTTP ${r.status}`);const d=await r.json();return d.data||d}
async function doSearch(){if(!sq.value)return;sl.value=true;try{const r=await api('/langchain/rag/query','POST',{query:sq.value});sr.value=r.answer||'未找到相关知识'}catch{sr.value='检索失败，请稍后重试'};sl.value=false}
function doImport(){message.success(`已提交导入: ${it.value}`);showImport.value=false}
async function fetchData(){
  try {
    const r = await fetch('/api/v1/cognitive/',{headers:{Authorization:`Bearer ${getAuthToken()}`}})
    if(r.ok){const j=await r.json();const dd=j.data||j
      if(dd){
        stats.value=[
          {l:'文档数',v:(dd.knowledge_graph_nodes ?? 0).toLocaleString(),c:'#4a9b8c'},
          {l:'知识片段',v:(dd.knowledge_graph_edges ?? 0).toLocaleString(),c:'#8b5cf6'},
          {l:'向量维度',v:dd.vector_dim ?? '-',c:'#06b6d4'},
          {l:'数据源',v:(dd.data_sources ?? 0).toString(),c:'#22c55e'},
        ]
      }
    }
  }catch{message.error('知识图谱数据加载失败')}
}
onMounted(fetchData)
</script>
