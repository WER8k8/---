/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="Rank Scheduler" subtitle="关键词排名调度 · DB 同步 · 即时检测" surface="elevated">
    <template #actions>
      <a-space>
        <a-button :loading="syncing" @click="syncKeywords">同步关键词</a-button>
        <a-button type="primary" :loading="running" @click="runCheck">立即检测</a-button>
        <a-button :loading="loading" @click="load">刷新</a-button>
      </a-space>
    </template>

    <div v-if="snap" class="stat-row">
      <a-statistic title="调度开关" :value="schedulerEnabledLabel" />
      <a-statistic title="DB 活跃词" :value="dbKeywordCount" />
      <a-statistic title="内存追踪" :value="trackedCount" />
      <a-statistic title="运行次数" :value="runCount" />
      <a-statistic title="最近运行" :value="lastRunLabel" />
    </div>

    <a-alert
      v-if="snap?.hint"
      type="info"
      show-icon
      :message="snap.hint"
      class="mb-3"
    />

    <a-tabs>
      <a-tab-pane key="tracked" tab="追踪关键词">
        <a-table
          :loading="loading"
          :data-source="tracked"
          :columns="trackedCols"
          row-key="keyword"
          size="small"
          :pagination="false"
        />
      </a-tab-pane>
      <a-tab-pane key="rankings" tab="最近排名">
        <a-table
          :loading="loading"
          :data-source="rankings"
          :columns="rankCols"
          row-key="rowKey"
          size="small"
          :pagination="{ pageSize: 20 }"
        />
      </a-tab-pane>
    </a-tabs>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet, apiPost } from '@/utils/api'

type RankRow = {
  keyword: string
  search_engine: string
  current_position: number | null
  previous_position: number | null
  best_position: number | null
  last_checked_at: string | null
  rowKey?: string
}

const loading = ref(false)
const syncing = ref(false)
const running = ref(false)
const snap = ref<Record<string, unknown> | null>(null)

const schedulerMeta = computed(() => (snap.value?.scheduler as Record<string, unknown>) || {})
const dbKeywordCount = computed(() => Number(snap.value?.db_keyword_count ?? 0))
const schedulerEnabledLabel = computed(() => (snap.value?.enabled ? 'ON' : 'OFF'))
const trackedCount = computed(() => Number(schedulerMeta.value.tracked_count ?? 0))
const runCount = computed(() => Number(schedulerMeta.value.run_count ?? 0))
const tracked = computed(() => (snap.value?.tracked_keywords as Record<string, unknown>[]) || [])
const rankings = computed(() => {
  const rows = (snap.value?.recent_rankings as RankRow[]) || []
  return rows.map((r, i) => ({
    ...r,
    rowKey: `${r.keyword}-${r.search_engine}-${i}`,
  }))
})

const lastRunLabel = computed(() => {
  const t = (snap.value?.scheduler as Record<string, unknown> | undefined)?.last_run
  return t ? String(t).slice(0, 19) : '—'
})

const trackedCols = [
  { title: '关键词', dataIndex: 'keyword', key: 'keyword' },
  { title: '域名', dataIndex: 'domain', key: 'domain' },
]

const rankCols = [
  { title: '关键词', dataIndex: 'keyword', key: 'keyword' },
  { title: '引擎', dataIndex: 'search_engine', key: 'search_engine', width: 90 },
  { title: '当前', dataIndex: 'current_position', key: 'current_position', width: 70 },
  { title: '上次', dataIndex: 'previous_position', key: 'previous_position', width: 70 },
  { title: '最佳', dataIndex: 'best_position', key: 'best_position', width: 70 },
  { title: '检测时间', dataIndex: 'last_checked_at', key: 'last_checked_at', width: 180 },
]

async function load() {
  loading.value = true
  try {
    const res = await apiGet<{ data?: Record<string, unknown> }>('/hermes/ops/rank-scheduler')
    snap.value = (res as { data?: Record<string, unknown> }).data ?? (res as Record<string, unknown>)
  } catch (e: unknown) {
    message.error((e as Error).message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function syncKeywords() {
  syncing.value = true
  try {
    await apiPost('/hermes/ops/rank-scheduler/sync')
    message.success('关键词已同步')
    await load()
  } catch (e: unknown) {
    message.error((e as Error).message || '同步失败')
  } finally {
    syncing.value = false
  }
}

async function runCheck() {
  running.value = true
  try {
    const res = await apiPost<{ data?: { checked?: number } }>('/hermes/ops/rank-scheduler/run')
    const checked = (res as { data?: { checked?: number } }).data?.checked ?? 0
    message.success(`检测完成：${checked} 个关键词`)
    await load()
  } catch (e: unknown) {
    message.error((e as Error).message || '检测失败')
  } finally {
    running.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.mb-3 {
  margin-bottom: 12px;
}
</style>
