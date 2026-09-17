/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="多语言管理" subtitle="全球化站点语言版本 · 翻译进度 · 质量监控" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="showAddLang=true">+ 添加语言</a-button>
        <a-button type="primary" @click="fullTranslate" :loading="batching">全量翻译</a-button>
        <a-button @click="exportReport">导出报告</a-button>
      </a-space>
    </template>
    <div class="space-y-6">
    <a-alert v-if="loadError" type="warning" show-icon :message="loadError" />
    <a-row :gutter="16">
      <a-col :span="6" v-for="s in stats" :key="s.l"><a-card hoverable size="small"><a-statistic :title="s.l" :value="s.v" :suffix="s.s" :value-style="{color:s.c}"/></a-card></a-col>
    </a-row>
    <a-row :gutter="16">
      <a-col :span="6" v-for="l in langs" :key="l.code"><a-card hoverable size="small" class="text-center" :class="l.coverage>=90?'border-green-500':l.coverage>=50?'border-yellow-500':'border-red-300'">
        <p class="text-xs text-gray-400 mb-1">{{ l.code }}</p><h4 class="font-bold text-sm">{{ l.name }}</h4>
        <a-progress :percent="l.coverage" :stroke-color="l.coverage>=90?'#22c55e':l.coverage>=50?'#f59e0b':'#ef4444'" size="small" class="mt-2"/>
        <div class="mt-2 flex justify-center gap-2"><a-button size="small" @click="startTranslate(l)">翻译</a-button><a-button size="small" danger @click="delLang(l)">删除</a-button></div>
      </a-card></a-col>
    </a-row>
    <a-card title="翻译任务队列" size="small">
      <a-empty v-if="!tasks.length" description="暂无翻译任务" />
      <a-table v-else :columns="tc" :dataSource="tasks" rowKey="id" size="small">
      <template #bodyCell="{column,record}"><template v-if="column.key==='s'"><a-tag :color="record.s==='done'?'green':record.s==='running'?'blue':'default'">{{ {done:'已完成',running:'翻译中',queued:'排队中',failed:'失败'}[record.s as string] }}</a-tag></template>
      <template v-if="column.key==='a'"><a-button size="small" v-if="record.s==='failed'" @click="retry(record)">重试</a-button><a-button size="small" danger @click="delTask(record)">删除</a-button></template></template>
    </a-table></a-card>
    <a-modal v-model:open="showAddLang" title="添加新语言" @ok="addLang"><a-form layout="vertical"><a-form-item label="语言代码"><a-input v-model:value="nl.code" placeholder="fr-FR"/></a-form-item><a-form-item label="语言名称"><a-input v-model:value="nl.name" placeholder="Francais"/></a-form-item></a-form></a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { YdPage } from '@/components/youding'
import { apiGet } from '@/utils/api'
import { downloadTableCsv } from '@/utils/exportCsv'
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'

const batching = ref(false)
const showAddLang = ref(false)
const nl = reactive({ code: '', name: '' })
const loadError = ref('')
const stats = ref<Array<{ l: string; v: string | number; s?: string; c: string }>>([
  { l: '支持语言', v: 0, c: '#4a9b8c' },
  { l: '术语条目', v: 0, c: '#8b5cf6' },
  { l: '翻译任务', v: 0, c: '#22c55e' },
  { l: '今日翻译', v: 0, c: '#f59e0b' },
])
const langs = ref<any[]>([])
const tc = [
  { title: '任务', dataIndex: 'n' },
  { title: '源→目标', dataIndex: 'd' },
  { title: '进度', dataIndex: 'p' },
  { title: '状态', dataIndex: 's', key: 's' },
  { title: '操作', key: 'a' },
]
const tasks = ref<any[]>([])

async function loadOverview() {
  loadError.value = ''
  try {
    const data = await apiGet<{
      languages?: Array<{ code: string; name: string; flag?: string; coverage: number }>
      stats?: { total_languages?: number; glossary_terms?: number; tasks?: number; today_translations?: number }
    }>('/globalization/')
    const s = data.stats || {}
    stats.value = [
      { l: '支持语言', v: s.total_languages ?? 0, c: '#4a9b8c' },
      { l: '术语条目', v: s.glossary_terms ?? 0, c: '#8b5cf6' },
      { l: '翻译任务', v: s.tasks ?? 0, c: '#22c55e' },
      { l: '今日翻译', v: s.today_translations ?? 0, c: '#f59e0b' },
    ]
    langs.value = (data.languages || []).map((l) => ({
      code: l.code,
      name: l.name,
      flag: l.flag || '',
      coverage: Number(l.coverage || 0),
    }))
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : '全球化数据加载失败'
    langs.value = []
  }

  try {
    const taskRes = await apiGet<{ items?: any[] }>('/globalization/tasks', { page: 1, page_size: 20 })
    const taskItems = Array.isArray(taskRes) ? taskRes : (taskRes?.items || [])
    tasks.value = taskItems.map((t: any) => ({
      id: t.id,
      n: t.name || t.source_lang + '→' + t.target_lang,
      d: `${t.source_lang || 'zh'}→${t.target_lang || '—'}`,
      p: t.progress || '—',
      s: t.status || 'queued',
    }))
  } catch {
    tasks.value = []
  }
}
function addLang(){ if(!nl.code||!nl.name)return; langs.value.push({code:nl.code,name:nl.name,flag:'',coverage:0}); showAddLang.value=false; nl.code='';nl.name=''; message.success('已添加') }
function delLang(l:any){ if(l.code==='zh-CN'){message.warning('不能删除默认语言');return}; langs.value=langs.value.filter(x=>x.code!==l.code); message.success('已删除') }
function startTranslate(l:any){ tasks.value.unshift({id:Date.now(),n:`${l.name}全量翻译`,d:`zh→${l.code.split('-')[0]}`,p:'0/—',s:'queued'}); message.success(`已启动 ${l.name} 翻译任务`) }
function fullTranslate(){ batching.value=true; setTimeout(()=>{ tasks.value.unshift({id:Date.now(),n:'全站批量翻译',d:'zh→en/ja/ko/ar/th/vi',p:'0/—',s:'queued'}); batching.value=false; message.success('全量翻译任务已创建') },800) }
function retry(r:any){ tasks.value=tasks.value.map(t=>t.id===r.id?{...t,s:'queued'}:t); message.success('已重新排队') }
function delTask(r:any){ tasks.value=tasks.value.filter(t=>t.id!==r.id) }
function exportReport() {
  downloadTableCsv(
    `globalization-report-${new Date().toISOString().slice(0, 10)}.csv`,
    ['语言代码', '语言名称', '覆盖率%'],
    langs.value.map((l) => [l.code, l.name, l.coverage]),
  )
  message.success('报告已导出')
}
onMounted(loadOverview)
</script>
