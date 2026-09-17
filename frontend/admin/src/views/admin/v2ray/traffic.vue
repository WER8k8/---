/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="流量统计" subtitle="代理流量使用情况 · 按节点/按天统计" surface="elevated">
    <template #actions>
      <a-space>
        <a-select v-model:value="period" style="width: 120px" @change="loadData">
          <a-select-option value="today">今日</a-select-option>
          <a-select-option value="week">本周</a-select-option>
          <a-select-option value="month">本月</a-select-option>
        </a-select>
        <a-button :loading="loading" @click="loadData">刷新</a-button>
      </a-space>
    </template>
    <div class="space-y-6">
      <PageDataBar
        v-if="mode !== 'live'"
        :mode="mode"
        :error="loadError"
        @retry="loadData"
      />

      <div class="grid grid-cols-4 gap-4">
        <a-card size="small"><a-statistic title="总流量" :value="stats.total" :value-style="{ color: 'var(--uj-brand, #4a9b8c)' }" /></a-card>
        <a-card size="small"><a-statistic title="上传" :value="stats.upload" :value-style="{ color: '#22c55e' }" /></a-card>
        <a-card size="small"><a-statistic title="下载" :value="stats.download" :value-style="{ color: '#8b5cf6' }" /></a-card>
        <a-card size="small"><a-statistic title="剩余配额" :value="stats.remaining" :value-style="{ color: '#f59e0b' }" /></a-card>
      </div>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-card title="按节点统计" size="small">
            <a-empty v-if="!nodeTraffic.length" description="暂无节点流量数据" />
            <div v-else class="space-y-3">
              <div v-for="n in nodeTraffic" :key="n.name">
                <div class="flex justify-between text-xs mb-1">
                  <span>{{ n.name }}</span>
                  <span class="font-medium">{{ n.used }}</span>
                </div>
                <a-progress :percent="Math.min(n.pct, 100)" :stroke-color="n.color" size="small" />
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :span="12">
          <a-card title="每日流量趋势" size="small">
            <a-empty v-if="!daily.length" description="暂无趋势数据" />
            <template v-else>
              <div class="flex items-end space-x-1 h-32">
                <div
                  v-for="(d, i) in daily"
                  :key="i"
                  class="flex-1 rounded-t bg-blue-500"
                  :style="{ height: `${Math.max(4, (d.v / maxDaily) * 100)}%` }"
                  :title="`${d.v} GB`"
                />
              </div>
              <div class="flex justify-between mt-2 text-[10px] text-gray-400">
                <span v-for="d in daily" :key="d.l">{{ d.l }}</span>
              </div>
            </template>
          </a-card>
        </a-col>
      </a-row>

      <a-card title="流量明细" size="small">
        <a-table
          :columns="columns"
          :data-source="logs"
          row-key="id"
          size="small"
          :loading="loading"
          :pagination="{ pageSize: 8 }"
        />
      </a-card>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import PageDataBar from '@/components/common/PageDataBar.vue'
import { apiGet } from '@/utils/api'
import type { PageDataMode } from '@/composables/usePageData'

const period = ref('month')
const loading = ref(false)
const mode = ref<PageDataMode>('empty')
const loadError = ref<string | null>(null)

const stats = ref({ total: '—', upload: '—', download: '—', remaining: '—' })
const nodeTraffic = ref<Array<{ name: string; used: string; pct: number; color: string }>>([])
const daily = ref<Array<{ l: string; v: number }>>([])
const logs = ref<Array<Record<string, unknown>>>([])

const maxDaily = computed(() => Math.max(1, ...daily.value.map((d) => d.v)))

const columns = [
  { title: '时间', dataIndex: 't' },
  { title: '节点', dataIndex: 'n' },
  { title: '方向', dataIndex: 'd' },
  { title: '流量', dataIndex: 's' },
  { title: '协议', dataIndex: 'p' },
]

async function loadData() {
  loading.value = true
  loadError.value = null
  try {
    const data = await apiGet<{
      stats?: typeof stats.value
      nodes?: typeof nodeTraffic.value
      daily?: typeof daily.value
      logs?: typeof logs.value
    }>('/super-admin/v2ray-tracker/traffic', { period: period.value })

    stats.value = data.stats || { total: '0 GB', upload: '0 GB', download: '0 GB', remaining: '—' }
    nodeTraffic.value = data.nodes || []
    daily.value = data.daily || []
    logs.value = data.logs || []
    mode.value = 'live'
  } catch (e: unknown) {
    mode.value = 'empty'
    loadError.value = e instanceof Error ? e.message : '加载失败'
    stats.value = { total: '0 GB', upload: '0 GB', download: '0 GB', remaining: '—' }
    nodeTraffic.value = []
    daily.value = []
    logs.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadData()
})
</script>
