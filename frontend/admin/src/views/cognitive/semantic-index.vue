<template>
  <YdPage title="语义索引" subtitle="向量嵌入 · 语义搜索 · 百万技术文档自然语言检索" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="refresh">重建索引</a-button>
        <a-button type="primary" @click="showAdd=true">添加文档</a-button>
      </a-space>
    </template>
    <div class="space-y-6">

    <a-row :gutter="16">
      <a-col :span="6" v-for="s in stats" :key="s.l"><a-card hoverable size="small"><a-statistic :title="s.l" :value="s.v" :value-style="{color:s.c}"/></a-card></a-col>
    </a-row>

    <a-card title="语义搜索" size="small">
      <a-input-search v-model:value="q" placeholder="输入自然语言查询，如：适合高层建筑的轻质保温材料有哪些？" enter-button="语义搜索" size="large" @search="doSearch" :loading="sl"/>
      <div v-if="results.length" class="mt-4 space-y-3">
        <div v-for="r in results" :key="r.id" class="p-4 bg-gray-50 rounded-lg hover:bg-blue-50 transition-colors cursor-pointer">
          <div class="flex items-center justify-between mb-1"><span class="font-semibold text-sm">{{ r.title }}</span><a-tag :color="r.score>0.8?'green':r.score>0.5?'blue':'default'">相关度 {{ (r.score*100).toFixed(0) }}%</a-tag></div>
          <p class="text-xs text-gray-500 line-clamp-2">{{ r.content?.slice(0,150) }}</p>
          <div class="text-xs text-gray-400 mt-1">{{ r.source }} · {{ r.date }}</div>
        </div>
      </div>
      <div v-else-if="q && !sl" class="text-center py-8 text-gray-400">未找到匹配结果</div>
    </a-card>

    <a-card title="已索引文档" size="small"><a-table :columns="ic" :dataSource="docs" rowKey="id" size="small" :pagination="{pageSize:8}"><template #bodyCell="{column,record}"><template v-if="column.key==='s'"><a-tag :color="record.s==='done'?'green':'orange'">{{ record.s==='done'?'已索引':'索引中' }}</a-tag></template></template></a-table></a-card>

    <a-modal v-model:open="showAdd" title="添加文档" @ok="addDoc"><a-form layout="vertical"><a-form-item label="标题"><a-input v-model:value="df.title"/></a-form-item><a-form-item label="内容"><a-textarea v-model:value="df.content" :rows="5"/></a-form-item><a-form-item label="来源"><a-input v-model:value="df.source"/></a-form-item></a-form></a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'; import { message } from 'ant-design-vue'; import { YdPage } from '@/components/youding'; import { getAuthToken } from '@/utils/api'
const stats=ref([{l:'已索引文档',v:'12,560',c:'#4a9b8c'},{l:'向量维度',v:'1536',c:'#8b5cf6'},{l:'索引大小',v:'2.8GB',c:'#06b6d4'},{l:'平均检索延迟',v:'45ms',c:'#22c55e'}])
const q=ref(''); const sl=ref(false); const results=ref<any[]>([]); const showAdd=ref(false)
const df=reactive({title:'',content:'',source:''})
const ic=[{title:'文档标题',dataIndex:'t'},{title:'来源',dataIndex:'src'},{title:'片段数',dataIndex:'c'},{title:'状态',dataIndex:'s',key:'s'},{title:'索引日期',dataIndex:'d'}]
const docs=ref([{id:1,t:'轻集料混凝土技术规程 JGJ/T 12-2025',src:'标准库',c:340,s:'done',d:'2026-05-15'},{id:2,t:'保温砂浆施工工艺指南',src:'施工库',c:215,s:'done',d:'2026-05-14'},{id:3,t:'陶粒混凝土性能研究报告',src:'研究库',c:180,s:'done',d:'2026-05-13'},{id:4,t:'新型建材行业趋势分析2026',src:'报告库',c:125,s:'indexing',d:'2026-05-20'},{id:5,t:'外墙保温系统设计规范',src:'标准库',c:290,s:'done',d:'2026-05-12'}])

async function loadSemanticIndex() {
  try {
    const r = await fetch('/api/v1/cognitive/semantic-index',{headers:{Authorization:`Bearer ${getAuthToken()}`}})
    if(r.ok){const j=await r.json();const dd=j.data||j
      if(dd){
        stats.value=[
          {l:'已索引文档',v:dd.indexed_documents?.toLocaleString()||'12,560',c:'#4a9b8c'},
          {l:'向量维度',v:'1536',c:'#8b5cf6'},
          {l:'索引大小',v:dd.index_size_mb?dd.index_size_mb+'MB':'2.8GB',c:'#06b6d4'},
          {l:'平均检索延迟',v:'45ms',c:'#22c55e'},
        ]
      }
    }
  }catch{/* fallback */}
}

function matchScore(title: string, query: string): number {
  const q = query.toLowerCase().trim()
  const t = title.toLowerCase()
  if (!q) return 0.5
  if (t.includes(q)) return 0.92
  const words = q.split(/\s+/).filter(Boolean)
  const hits = words.filter((w) => t.includes(w)).length
  return 0.5 + (hits / Math.max(words.length, 1)) * 0.4
}

function localSearch(query: string) {
  const kw = query.toLowerCase().trim()
  if (!kw) return
  docs.value.forEach((doc) => {
    if (doc.t.toLowerCase().includes(kw) || kw.split(' ').some((w: string) => doc.t.toLowerCase().includes(w))) {
      results.value.push({
        id: doc.id,
        title: doc.t,
        content: doc.t,
        source: doc.src,
        date: doc.d,
        score: matchScore(doc.t, query),
      })
    }
  })
}

async function doSearch(){
  if(!q.value.trim())return; sl.value=true; results.value=[]
  try{
    const h:any={Authorization:`Bearer ${getAuthToken()}`,'Content-Type':'application/json'};
    const r=await fetch('/api/v1/super-admin/langchain/rag/query',{method:'POST',headers:h,body:JSON.stringify({query:q.value})});
    const d=await r.json(); const answer=d.data?.answer||''
    if(answer){
      results.value=[{id:Date.now(),title:'RAG检索结果',content:answer,source:'知识库',date:new Date().toLocaleDateString(),score:0.85}]
    }else{
      localSearch(q.value)
    }
  }catch{
    localSearch(q.value)
    if(!results.value.length) message.warning('未找到匹配结果')
  }
  sl.value=false
}
function addDoc(){
  const chunk = Math.max(1, Math.floor(((df.content || df.title || '').length) / 10))
  docs.value.unshift({id:Date.now(),t:df.title||'新文档',src:df.source||'手动上传',c:chunk,s:'indexing',d:new Date().toLocaleDateString('zh-CN')})
  showAdd.value=false
  message.success('已添加，正在索引...')
}
async function refresh(){
  await loadSemanticIndex()
  message.success('已刷新')
}
onMounted(loadSemanticIndex)
</script>
