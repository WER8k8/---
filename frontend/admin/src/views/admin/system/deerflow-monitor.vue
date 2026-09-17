/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="DeerFlow 队列监控" subtitle="全平台任务 · SLO · 失败率" surface="elevated">
    <template #actions>
      <a-space>
        <a-select v-model:value="statusFilter" allow-clear placeholder="状态" style="width: 120px" @change="load">
          <a-select-option value="queued">queued</a-select-option>
          <a-select-option value="running">running</a-select-option>
          <a-select-option value="success">success</a-select-option>
          <a-select-option value="failed">failed</a-select-option>
        </a-select>
        <a-button :loading="loading" @click="load">刷新</a-button>
      </a-space>
    </template>

    <div v-if="slo" class="slo-row">
      <a-statistic title="7天失败率" :value="(slo.failure_rate || 0) * 100" suffix="%" />
      <a-statistic title="平均排队(s)" :value="slo.avg_queue_seconds ?? '—'" />
      <a-statistic title="平均执行(s)" :value="slo.avg_run_seconds ?? '—'" />
      <a-statistic title="当前 queued" :value="slo.current_counts?.queued ?? 0" />
    </div>

    <a-table
      :loading="loading"
      :data-source="items"
      :columns="cols"
      row-key="id"
      size="small"
      :pagination="{ current: page, pageSize, total, onChange: onPage }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
        </template>
        <template v-else-if="column.key === 'steps'">
          <span v-if="!(record.steps || []).length">—</span>
          <a-tooltip v-else :title="(record.steps || []).map((s: Step) => s.title).join(' → ')">
            {{ (record.steps || []).length }} 步
          </a-tooltip>
        </template>
      </template>
    </a-table>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet } from '@/utils/api'

type Step = { index: number; title: string; status: string }

const loading = ref(false)
const items = ref<Record<string, unknown>[]>([])
type SloSnapshot = {
  failure_rate?: number
  avg_queue_seconds?: number | string
  avg_run_seconds?: number | string
  current_counts?: { queued?: number }
}

const slo = ref<SloSnapshot | null>(null)
const page = ref(1)
const pageSize = 20
const total = ref(0)
const statusFilter = ref<string | undefined>()

const cols = [
  { title: 'ID', dataIndex: 'id', key: 'id', ellipsis: true, width: 120 },
  { title: '租户', dataIndex: 'tenant_id', key: 'tenant_id', ellipsis: true, width: 100 },
  { title: '意图', dataIndex: 'intent', key: 'intent', width: 140 },
  { title: '状态', key: 'status', width: 90 },
  { title: '步骤', key: 'steps', width: 70 },
  { title: '创建', dataIndex: 'created_at', key: 'created_at', width: 160 },
]

function statusColor(s: string) {
  if (s === 'success') return 'green'
  if (s === 'failed') return 'red'
  if (s === 'running') return 'blue'
  return 'default'
}

async function load() {
  loading.value = true
  try {
    const params: Record<string, string | number> = { page: page.value, page_size: pageSize }
    if (statusFilter.value) params.status = statusFilter.value
    const data = await apiGet<{
      items: Record<string, unknown>[]
      total: number
      slo: Record<string, unknown>
    }>('/hermes/ops/deerflow/jobs', params)
    items.value = data.items || []
    total.value = data.total || 0
    slo.value = data.slo || null
  } catch (e: unknown) {
    message.error((e as Error)?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function onPage(p: number) {
  page.value = p
  void load()
}

onMounted(load)
</script>

<style scoped>
.slo-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
</style>
