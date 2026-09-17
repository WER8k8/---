/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="A/B 自动化测试" subtitle="千组文案并行测试 · 自动筛选最优解 · 对接后端 /ai-learning/auto-ab-test API" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showCreate=true">+ 新建实验</a-button>
    </template>
    <div class="space-y-6">
    <div class="grid grid-cols-4 gap-4">
      <a-card size="small"><a-statistic title="活跃实验" :value="activeCount" :value-style="{ color: 'var(--uj-brand, #4a9b8c)' }"/></a-card>
      <a-card size="small"><a-statistic title="已完成" :value="doneCount" :value-style="{ color: '#22c55e' }"/></a-card>
      <a-card size="small"><a-statistic title="平均置信度" :value="avgConf+'%'" :value-style="{ color: '#8b5cf6' }"/></a-card>
      <a-card size="small"><a-statistic title="胜出方案" :value="winnerCount" :value-style="{ color: '#f59e0b' }"/></a-card>
    </div>
    <a-card title="实验列表" size="small">
      <div ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar :loading="loading" :target-ref="tablePanelRef" :show-export="false" @refresh="loadTests" />
        </div>
        <YdDataTable
          :columns="columns"
          :data-source="tests"
          :loading="loading"
          :pagination="false"
          :table-props="{ size: tableSize, rowKey: 'id' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key==='s'">
              <a-tag :color="record.s==='running'?'blue':record.s==='done'?'green':'default'">
                {{ { running:'运行中', done:'已完成', draft:'草稿' }[record.s as 'running'|'done'|'draft'] }}
              </a-tag>
            </template>
            <template v-if="column.key==='a'">
              <a-space>
                <a-button size="small" v-if="record.s==='running'" @click="stopTest(record)">停止</a-button>
                <a-button size="small" v-if="record.s==='draft'" @click="startTest(record)">启动</a-button>
                <a-button size="small" @click="viewResult(record)">结果</a-button>
              </a-space>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>
    <a-modal v-model:open="showCreate" title="新建 A/B 实验" @ok="createTest">
      <a-form layout="vertical">
        <a-form-item label="实验名称"><a-input v-model:value="form.name" placeholder="如：产品标题优化测试"/></a-form-item>
        <a-form-item label="测试页面"><a-input v-model:value="form.page" placeholder="/products/lightweight-concrete"/></a-form-item>
        <a-form-item label="变体A (对照组)"><a-textarea v-model:value="form.variantA" :rows="2" placeholder="原标题或内容"/></a-form-item>
        <a-form-item label="变体B (实验组)"><a-textarea v-model:value="form.variantB" :rows="2" placeholder="新的标题或内容"/></a-form-item>
        <a-row :gutter="16"><a-col :span="12"><a-form-item label="流量分配"><a-select v-model:value="form.traffic"><a-select-option value="50-50">50/50 均分</a-select-option><a-select-option value="30-70">30/70 倾向B</a-select-option></a-select></a-form-item></a-col><a-col :span="12"><a-form-item label="最小样本量"><a-input-number v-model:value="form.sampleSize" :min="100"/></a-form-item></a-col></a-row>
      </a-form>
    </a-modal>
    <a-modal v-model:open="showResult" title="实验结果" width="600px" :footer="null">
      <div v-if="resultTest" class="space-y-4">
        <a-descriptions size="small" :column="2"><a-descriptions-item label="实验">{{ resultTest.n }}</a-descriptions-item><a-descriptions-item label="状态"><a-tag :color="resultTest.s==='done'?'green':'blue'">{{ resultTest.s }}</a-tag></a-descriptions-item><a-descriptions-item label="A转化率">{{ resultTest.aRate }}%</a-descriptions-item><a-descriptions-item label="B转化率">{{ resultTest.bRate }}%</a-descriptions-item><a-descriptions-item label="置信度">{{ resultTest.conf }}%</a-descriptions-item><a-descriptions-item label="胜出">{{ resultTest.winner||'待定' }}</a-descriptions-item></a-descriptions>
        <a-alert type="success" :message="`结论: ${resultTest.winner||'B'} 方案胜出，转化率提升 ${Math.abs((resultTest.bRate||0)-(resultTest.aRate||0)).toFixed(1)}%` "/>
      </div>
    </a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { message } from 'ant-design-vue'
import { apiGet, apiPost } from '@/utils/api'

const showCreate = ref(false)
const showResult = ref(false)
const resultTest = ref<any>(null)
const loading = ref(false)
const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const form = reactive({ name: '', page: '', variantA: '', variantB: '', traffic: '50-50', sampleSize: 500 })
const tests = ref<any[]>([])

const activeCount = computed(() => tests.value.filter((t: any) => t.s === 'running').length)
const doneCount = computed(() => tests.value.filter((t: any) => t.s === 'done').length)
const avgConf = computed(() => {
  const r = tests.value.filter((t: any) => t.s === 'running')
  return r.length ? Math.round(r.reduce((s: number, t: any) => s + t.conf, 0) / r.length) : 0
})
const winnerCount = computed(() => tests.value.filter((t: any) => t.winner).length)

const columns = [
  { title: '实验名称', dataIndex: 'n', key: 'n' },
  { title: '页面', dataIndex: 'p', key: 'p', width: 180 },
  { title: 'A转化', dataIndex: 'aRate', key: 'aRate', width: 80 },
  { title: 'B转化', dataIndex: 'bRate', key: 'bRate', width: 80 },
  { title: '置信度', dataIndex: 'conf', key: 'conf', width: 80 },
  { title: '状态', key: 's', width: 90 },
  { title: '操作', key: 'a', width: 180 },
]

async function loadTests() {
  loading.value = true
  try {
    const d = await apiGet('/ai-learning/auto-ab-test')
    if (Array.isArray(d?.tests)) tests.value = d.tests
  } catch {
    message.error('数据加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

async function createTest() {
  try {
    await apiPost('/ai-learning/auto-ab-test', {
      name: form.name,
      page: form.page,
      variantA: form.variantA,
      variantB: form.variantB,
      traffic: form.traffic,
      sampleSize: form.sampleSize,
    })
    showCreate.value = false
    message.success('实验已创建')
    await loadTests()
  } catch {
    message.error('创建失败，请稍后重试')
  }
}

async function startTest(r: any) {
  try {
    const d = await apiPost(`/ai-learning/auto-ab-test/${r.id}/start`, {})
    tests.value = tests.value.map((t) => (t.id === r.id ? { ...t, ...d } : t))
    message.success('实验已启动')
  } catch {
    message.error('启动失败，请稍后重试')
  }
}

async function stopTest(r: any) {
  try {
    const d = await apiPost(`/ai-learning/auto-ab-test/${r.id}/stop`, {})
    tests.value = tests.value.map((t) => (t.id === r.id ? { ...t, ...d } : t))
    message.success('实验已停止')
  } catch {
    message.error('停止失败，请稍后重试')
  }
}

function viewResult(r: any) {
  resultTest.value = r
  showResult.value = true
}

onMounted(loadTests)
</script>
