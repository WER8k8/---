/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="健康看板" subtitle="实时系统状态监控" surface="elevated">
    <template #actions>
      <a-button @click="refreshAll" :loading="refreshing">刷新数据</a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <a-alert
      v-if="overviewError"
      type="warning"
      show-icon
      class="mb-4"
      :message="overviewError"
    />

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <a-card v-for="s in services" :key="s.name" hoverable class="stat-card">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="s.bgColor">
              <component :is="s.icon" class="w-5 h-5" :class="s.iconColor" />
            </div>
            <div>
              <p class="text-sm text-gray-500">{{ s.name }}</p>
              <p class="text-lg font-semibold text-gray-900">{{ s.status }}</p>
            </div>
          </div>
          <a-badge :status="s.online ? 'success' : 'error'" />
        </div>
      </a-card>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <a-card title="CPU 使用率" class="col-span-1">
        <div class="flex flex-col items-center py-4">
          <a-progress type="circle" :percent="cpuPercent" :stroke-color="{ '0%': 'var(--uj-brand, #4a9b8c)', '100%': '#06b6d4' }" :size="160" />
          <p class="mt-4 text-sm text-gray-500">核心数: {{ cpu.cores }} | 进程: {{ cpu.processes }}</p>
        </div>
      </a-card>

      <a-card title="内存使用" class="col-span-1">
        <div class="flex flex-col items-center py-4">
          <a-progress type="circle" :percent="memPercent" :stroke-color="{ '0%': '#22c55e', '70%': '#f59e0b', '90%': '#ef4444' }" :size="160" />
          <p class="mt-4 text-sm text-gray-500">已用 {{ memory.usedGB }}GB / 总计 {{ memory.totalGB }}GB</p>
        </div>
      </a-card>

      <a-card title="磁盘使用" class="col-span-1">
        <div class="flex flex-col items-center py-4">
          <a-progress type="circle" :percent="diskPercent" :stroke-color="{ '0%': '#8b5cf6', '100%': '#ec4899' }" :size="160" />
          <p class="mt-4 text-sm text-gray-500">已用 {{ disk.usedGB }}GB / 总计 {{ disk.totalGB }}GB</p>
        </div>
      </a-card>
    </div>

    <a-card title="API 响应时间（最近60秒）">
      <div class="h-64 flex items-end gap-1 px-2">
        <div v-for="(pt, i) in apiChartBars" :key="i" class="flex-1 rounded-t transition-all duration-300"
          :style="{ height: `${(pt.value / maxApiLatency) * 100}%`, backgroundColor: pt.color }"
          :title="`${pt.label}: ${pt.value}ms`" />
      </div>
      <div class="flex justify-between mt-2 text-xs text-gray-400 px-2">
        <span>{{ apiChartBars[0]?.label }}</span>
        <span>avg: {{ avgLatency }}ms</span>
        <span>{{ apiChartBars[apiChartBars.length - 1]?.label }}</span>
      </div>
    </a-card>

    <a-card title="最近事件">
      <a-empty v-if="!events.length" description="暂无系统事件记录。接入运维事件源后此处才会出现真实日志。" />
      <a-timeline v-else>
        <a-timeline-item v-for="e in events" :key="e.time" :color="e.type === 'warn' ? 'orange' : e.type === 'error' ? 'red' : 'blue'">
          <p class="text-sm font-medium">{{ e.message }}</p>
          <p class="text-xs text-gray-400">{{ e.time }}</p>
        </a-timeline-item>
      </a-timeline>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { YdPage } from '@/components/youding'
import { Badge, Card, Progress, Button, Timeline, TimelineItem, message } from 'ant-design-vue'
import { CloudServerOutlined, DatabaseOutlined, FileTextOutlined, ApiOutlined } from '@ant-design/icons-vue'
import { getAuthToken } from '@/utils/api'

const refreshing = ref(false)
const overviewError = ref('')
const overviewLoaded = ref(false)
const cpuPercent = ref(0)
const memPercent = ref(0)
const diskPercent = ref(0)

const cpu = reactive({ cores: 0, processes: 0 })
const memory = reactive({ usedGB: '—', totalGB: '—' })
const disk = reactive({ usedGB: '—', totalGB: '—' })

const services = reactive([
  { name: 'API', status: '待探测', online: false, bgColor: 'bg-gray-100', iconColor: 'text-gray-500', icon: ApiOutlined },
  { name: '数据库', status: '待探测', online: false, bgColor: 'bg-gray-100', iconColor: 'text-gray-500', icon: DatabaseOutlined },
])

interface BarEntry { label: string; value: number; color: string }
const apiChartBars = ref<BarEntry[]>([])
const maxApiLatency = ref(200)
let _timer: ReturnType<typeof setInterval> | null = null

const avgLatency = computed(() => {
  const b = apiChartBars.value
  if (!b.length) return 0
  return Math.round(b.reduce((s, v) => s + v.value, 0) / b.length)
})

const events = ref<{ time: string; message: string; type: string }[]>([])

function mapOverview(x: Record<string, unknown>) {
  overviewLoaded.value = true
  overviewError.value = ''
  if (x.cpu_usage_percent != null) cpuPercent.value = Math.round(Number(x.cpu_usage_percent))
  if (x.memory_usage_percent != null) memPercent.value = Math.round(Number(x.memory_usage_percent))
  if (x.disk_usage_percent != null) diskPercent.value = Math.round(Number(x.disk_usage_percent))
  if (x.cpuPercent != null) cpuPercent.value = Math.round(Number(x.cpuPercent))
  if (x.memPercent != null) memPercent.value = Math.round(Number(x.memPercent))
  if (x.diskPercent != null) diskPercent.value = Math.round(Number(x.diskPercent))
  if (x.cpu && typeof x.cpu === 'object') Object.assign(cpu, x.cpu)
  if (x.memory && typeof x.memory === 'object') Object.assign(memory, x.memory)
  if (x.disk && typeof x.disk === 'object') Object.assign(disk, x.disk)
  if (Array.isArray(x.services)) x.services.forEach((s: any, i: number) => { if (services[i]) Object.assign(services[i], s) })
  if (Array.isArray(x.events)) events.value = x.events as typeof events.value
  const dbStatus = String(x.database ?? '')
  if (services[1]) {
    services[1].online = dbStatus === 'ok'
    services[1].status = dbStatus === 'ok' ? '正常' : (dbStatus || '未知')
    services[1].bgColor = dbStatus === 'ok' ? 'bg-blue-100' : 'bg-gray-100'
    services[1].iconColor = dbStatus === 'ok' ? 'text-blue-600' : 'text-gray-500'
  }
  if (services[0]) {
    services[0].online = String(x.status ?? '') === 'healthy'
    services[0].status = String(x.status ?? '') === 'healthy' ? '正常' : '降级'
    services[0].bgColor = services[0].online ? 'bg-green-100' : 'bg-orange-100'
    services[0].iconColor = services[0].online ? 'text-green-600' : 'text-orange-600'
  }
}

async function measureLatencyBars(sampleCount = 20) {
  const bars: BarEntry[] = []
  const tk = getAuthToken() || ''
  for (let i = 0; i < sampleCount; i++) {
    const t0 = performance.now()
    try {
      await fetch('/api/v1/health', { headers: { Authorization: `Bearer ${tk}` } })
    } catch { /* 单次采样失败仍记录耗时 */ }
    const v = Math.max(1, Math.round(performance.now() - t0))
    const c = v > 120 ? '#ef4444' : v > 70 ? '#f59e0b' : '#22c55e'
    bars.push({ label: `${sampleCount - i}s`, value: v, color: c })
  }
  apiChartBars.value = bars
  maxApiLatency.value = Math.max(150, ...bars.map((b) => b.value))
}

async function loadOverview() {
  const tk = getAuthToken() || ''
  const r = await fetch('/api/v1/system-health/', { headers: { Authorization: `Bearer ${tk}` } })
  if (!r.ok) throw new Error('HTTP ' + r.status)
  const d = await r.json()
  const x = (d.data ?? d) as Record<string, unknown>
  mapOverview(x)
}

async function refreshAll() {
  refreshing.value = true
  try {
    await loadOverview()
    await measureLatencyBars()
  } catch {
    message.warning('刷新失败，请检查登录与 /api/v1/system-health')
  } finally {
    refreshing.value = false
  }
}

onMounted(async () => {
  try {
    await loadOverview()
    await measureLatencyBars()
  } catch {
    overviewError.value = '健康数据加载失败，请检查登录与 /api/v1/system-health'
    overviewLoaded.value = false
    apiChartBars.value = []
  }
})
onUnmounted(() => { if (_timer) clearInterval(_timer) })
</script>
