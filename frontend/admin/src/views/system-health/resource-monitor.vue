/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="资源监控" subtitle="实时系统资源与进程管理" surface="elevated">
    <template #actions>
      <a-button @click="refreshData" :loading="loading">刷新</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <a-card v-for="m in metrics" :key="m.label" hoverable>
        <a-statistic :title="m.label" :value="m.value" :suffix="m.suffix" :value-style="{ color: m.color }" />
        <a-progress :percent="m.percent" :show-info="false" size="small" :stroke-color="m.color" class="mt-2" />
      </a-card>
    </div>

    <a-card title="网络流量">
      <div class="grid grid-cols-2 gap-6">
        <div><p class="text-sm text-gray-500 mb-2">入站流量</p>
          <div class="text-2xl font-bold text-blue-600">{{ net.inbound }}</div>
          <a-progress :percent="net.inboundPercent" :show-info="false" stroke-color="var(--uj-brand, #4a9b8c)" class="mt-1" />
        </div>
        <div><p class="text-sm text-gray-500 mb-2">出站流量</p>
          <div class="text-2xl font-bold text-green-600">{{ net.outbound }}</div>
          <a-progress :percent="net.outboundPercent" :show-info="false" stroke-color="#22c55e" class="mt-1" />
        </div>
      </div>
    </a-card>

    <a-card title="活跃进程">
      <a-table :columns="processColumns" :data-source="processes" :pagination="{ pageSize: 8 }" size="small" row-key="pid">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-badge :status="record.status === 'running' ? 'success' : 'warning'" :text="record.status === 'running' ? '运行中' : '空闲'" />
          </template>
          <template v-if="column.key === 'cpu'">
            <a-progress :percent="record.cpu" :show-info="false" size="small" :stroke-color="record.cpu > 70 ? '#ef4444' : 'var(--uj-brand, #4a9b8c)'" />
          </template>
        </template>
      </a-table>
    </a-card>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Card, Statistic, Progress, Button, Badge, Table, message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'

const loading = ref(false)
let _timer: ReturnType<typeof setInterval> | null = null

const metrics = reactive([
  { label: 'CPU 使用率', value: 34.2, suffix: '%', percent: 34, color: '#4a9b8c' },
  { label: '内存使用率', value: 61.8, suffix: '%', percent: 62, color: '#f59e0b' },
  { label: '磁盘 I/O', value: 45.6, suffix: 'MB/s', percent: 46, color: '#8b5cf6' },
])

const net = reactive({ inbound: '2.4 MB/s', inboundPercent: 48, outbound: '1.8 MB/s', outboundPercent: 36 })

const processColumns = [
  { title: 'PID', dataIndex: 'pid', key: 'pid', width: 80 },
  { title: '进程名', dataIndex: 'name', key: 'name' },
  { title: 'CPU', dataIndex: 'cpu', key: 'cpu', width: 140 },
  { title: '内存(MB)', dataIndex: 'mem', key: 'mem', width: 100 },
  { title: '状态', key: 'status', width: 100 },
  { title: '运行时间', dataIndex: 'uptime', key: 'uptime', width: 120 },
]
const processes = ref([
  { pid: 1024, name: 'uvicorn', cpu: 23, mem: 156, status: 'running', uptime: '12h 34m' },
  { pid: 1025, name: 'celery-worker', cpu: 45, mem: 289, status: 'running', uptime: '12h 30m' },
  { pid: 1026, name: 'postgres', cpu: 8, mem: 512, status: 'running', uptime: '3d 5h' },
  { pid: 1027, name: 'redis-server', cpu: 2, mem: 48, status: 'running', uptime: '3d 5h' },
  { pid: 1028, name: 'nginx', cpu: 1, mem: 24, status: 'running', uptime: '3d 4h' },
  { pid: 1029, name: 'minio', cpu: 12, mem: 198, status: 'running', uptime: '3d 2h' },
  { pid: 1030, name: 'seo-scheduler', cpu: 35, mem: 124, status: 'running', uptime: '1d 8h' },
  { pid: 1031, name: 'sync-job', cpu: 0, mem: 12, status: 'idle', uptime: '8h 15m' },
])

async function loadResourceMonitor() {
  const tk = getAuthToken() || ''
  const r = await fetch('/api/v1/system-health/resource-monitor', { headers: { Authorization: `Bearer ${tk}` } })
  if (!r.ok) throw new Error('HTTP ' + r.status)
  const d = await r.json()
  const payload = (d.data ?? d) as Record<string, unknown>
  if (Array.isArray(payload.metrics)) payload.metrics.forEach((m: any, i: number) => { if (metrics[i]) Object.assign(metrics[i], m) })
  if (payload.net && typeof payload.net === 'object') Object.assign(net, payload.net)
  if (Array.isArray(payload.processes)) processes.value = payload.processes as typeof processes.value
  const cpuPct = Number(payload.cpu_usage_percent)
  if (!Number.isNaN(cpuPct)) {
    metrics[0].value = cpuPct
    metrics[0].percent = Math.round(cpuPct)
  }
  const memPct = Number(payload.memory_usage_percent)
  if (!Number.isNaN(memPct)) {
    metrics[1].value = memPct
    metrics[1].percent = Math.round(memPct)
  }
  const diskPct = Number(payload.disk_usage_percent)
  if (!Number.isNaN(diskPct)) {
    metrics[2].value = diskPct
    metrics[2].percent = Math.round(diskPct)
  }
}

async function refreshData() {
  loading.value = true
  try {
    await loadResourceMonitor()
  } catch {
    message.warning('刷新失败，请检查 /api/v1/system-health/resource-monitor')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await loadResourceMonitor()
  } catch {
    message.warning('API不可用，请点击刷新')
  }
})
onUnmounted(() => { if (_timer) clearInterval(_timer) })
</script>
