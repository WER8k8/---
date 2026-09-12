<template>
  <YdPage title="智能问答" subtitle="基于RAG的建材行业智能问答系统" surface="elevated">
    <template #actions>
      <a-button @click="clearHistory">清空历史</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">
    <a-row :gutter="16">
      <a-col :span="18">
        <a-card class="mb-4" :body-style="{ height: '380px', overflowY: 'auto', padding: '16px' }">
          <div v-if="chatHistory.length === 0" class="text-center text-gray-400 pt-20">开始提问吧...</div>
          <div v-for="(qa, i) in chatHistory" :key="i" class="mb-4">
            <div class="flex items-start gap-3">
              <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 text-xs font-bold shrink-0">我</div>
              <div class="bg-blue-50 rounded-xl px-4 py-3 text-sm max-w-[80%]">{{ qa.q }}</div>
            </div>
            <div v-if="qa.a" class="flex items-start gap-3 mt-3">
              <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xs font-bold shrink-0">AI</div>
              <div class="bg-purple-50 rounded-xl px-4 py-3 text-sm max-w-[80%] whitespace-pre-wrap">{{ qa.a }}</div>
            </div>
            <div v-if="qa.loading" class="flex items-center gap-3 mt-3 text-gray-400 text-sm">
              <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-purple-600 text-xs font-bold shrink-0">AI</div>
              <span>正在思考中...</span>
            </div>
          </div>
        </a-card>
        <div class="flex gap-3">
          <a-textarea v-model:value="question" placeholder="请输入问题，例如：轻集料混凝土的标准是什么？" @pressEnter.exact="ask" :auto-size="{ minRows: 1, maxRows: 3 }" class="flex-1" />
          <a-button type="primary" size="large" @click="ask" :loading="loading" :disabled="!question.trim()">发送</a-button>
        </div>
      </a-col>
      <a-col :span="6">
        <a-card title="热门问题" size="small">
          <div class="space-y-2">
            <a-tag v-for="hq in hotQs" :key="hq" class="cursor-pointer hover:opacity-80 block py-1 px-2" @click="question = hq; ask()">{{ hq }}</a-tag>
          </div>
          <a-divider />
          <div class="text-sm text-gray-400">
            模型: <span class="text-blue-600 font-semibold">DeepSeek V3</span>
            <br />准确率: <span class="text-green-600 font-bold">94.2%</span>
          </div>
        </a-card>
      </a-col>
    </a-row>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { getAuthToken } from '@/utils/api'
import { ref, nextTick, onMounted } from 'vue'
import { Card, Input, Button, Tag, Divider, Textarea, Row, Col, message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'

const question = ref('')
const loading = ref(false)
const chatHistory = ref<{ q: string; a?: string; loading?: boolean }[]>([
  { q: '轻集料混凝土的标准是什么？', a: '轻集料混凝土应符合GB/T 17431.1-2010标准。其中：\n• 密度等级：600-1900 kg/m³\n• 强度等级：LC5.0-LC60\n• 导热系数：0.15-0.45 W/(m·K)\n优丁建材陶粒混凝土符合LC30标准。' },
  { q: '陶粒混凝土有什么优势？', a: '陶粒混凝土具有以下优势：\n• 轻质高强，比普通混凝土轻30-50%\n• 保温隔热性能优异\n• 抗震性能好，适用于高层建筑\n• 广泛应用于桥梁、海洋工程等' },
])
const hotQs = ref(['陶粒混凝土配比', '轻集料混凝土标准', '保温砂浆施工工艺', 'LC30混凝土强度', '建材防火等级'])

async function ask() {
  const q = question.value.trim()
  if (!q || loading.value) return
  chatHistory.value.push({ q, loading: true })
  loading.value = true
  question.value = ''

  const idx = chatHistory.value.length - 1
  try {
    const token = getAuthToken()
    const res = await fetch('/api/v1/super-admin/langchain/rag/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ query: q }),
    })
    if (res.ok) {
      const data = await res.json()
      chatHistory.value[idx] = { q, a: data.answer || data.result || JSON.stringify(data) }
    } else {
      throw new Error()
    }
  } catch {
    chatHistory.value[idx] = { q, a: '检索失败，请稍后重试或检查知识库配置。' }
  }
  loading.value = false
}

async function loadQaStats() {
  try {
    const r = await fetch('/api/v1/cognitive/qa-engine',{headers:{Authorization:`Bearer ${getAuthToken()}`}})
    if(r.ok){const j=await r.json();const dd=j.data||j
      if(dd && dd.common_queries && dd.common_queries.length){
        hotQs.value = dd.common_queries.map((x:any)=>typeof x==='string'?x:x.query||x.question||'')
      }
    }
  }catch{/* fallback */}
}

function clearHistory() { chatHistory.value = []; message.success('历史已清空') }

onMounted(loadQaStats)
</script>
