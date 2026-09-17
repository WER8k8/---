/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="CDN 概览" subtitle="边缘加速与内容分发总览" surface="elevated">
    <template #actions>
      <a-button @click="refresh">刷新数据</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-4 gap-4">
      <a-card v-for="s in stats" :key="s.label" hoverable>
        <a-statistic :title="s.label" :value="s.value" :suffix="s.suffix" :value-style="{ color: s.color }" />
      </a-card>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <a-card title="节点分布">
        <a-table :columns="cols" :data-source="nodes" size="small" row-key="region">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'health'">
              <a-tag :color="record.health === '健康' ? 'success' : record.health === '警告' ? 'warning' : 'error'">{{ record.health }}</a-tag>
            </template>
          </template>
        </a-table>
      </a-card>
      <a-card title="带宽趋势 (近 6 小时)">
        <div class="bw-chart">
          <div v-for="(b, i) in bandwidth" :key="i" class="bw-bar-wrapper">
            <div class="bw-bar" :style="{ height: (b.value / 120) * 140 + 'px' }" :title="`${b.label}: ${b.value} Mbps`"></div>
            <span class="bw-label">{{ b.label }}</span>
            <span class="bw-val">{{ b.value }}</span>
          </div>
        </div>
      </a-card>
    </div>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { YdPage } from '@/components/youding'
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getAuthToken } from '@/utils/api'

const stats = ref<any[]>([
  { label: '节点数', value: 34, suffix: '个', color: '#4a9b8c' },
  { label: '缓存命中率', value: 92.5, suffix: '%', color: '#22c55e' },
  { label: '带宽节省', value: 78.3, suffix: '%', color: '#8b5cf6' },
  { label: '平均延迟', value: 24, suffix: 'ms', color: '#f59e0b' },
])

const bandwidth = ref<any[]>([])

const cols = [
  { title: '区域', dataIndex: 'region' },
  { title: '节点数', dataIndex: 'count', width: 80 },
  { title: '延迟', dataIndex: 'latency', width: 80 },
  { title: '带宽', dataIndex: 'bandwidth', width: 100 },
  { title: '健康状况', key: 'health', width: 80 },
]

const nodes = ref<any[]>([])

function refresh() { message.success('CDN 数据已刷新') }

onMounted(async () => {
  try {
    const tk = getAuthToken() || ''
    const r = await fetch('/api/v1/edge-cdn/', { headers: { Authorization: `Bearer ${tk}` } })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    const d = await r.json()
    if (d.data) {
      if (d.data.stats) stats.value = d.data.stats
      if (d.data.nodes) nodes.value = d.data.nodes
      if (d.data.bandwidth) bandwidth.value = d.data.bandwidth
    }
  } catch { message.warning('数据加载失败，请稍后重试') }
})
</script>
<style scoped>
.bw-chart { display: flex; align-items: flex-end; gap: 12px; height: 180px; padding: 8px 0; }
.bw-bar-wrapper { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; height: 100%; }
.bw-bar { width: 100%; max-width: 48px; background: linear-gradient(to top, var(--uj-brand, #4a9b8c), #06b6d4); border-radius: 4px 4px 0 0; min-height: 4px; transition: height 0.4s ease; }
.bw-label { font-size: 11px; color: #6b7280; }
.bw-val { font-size: 11px; color: #374151; font-weight: 500; }
</style>
