<template>
  <YdPage title="协同看板" subtitle="AI Agent集群运行状态概览" surface="elevated">
    <template #actions>
      <a-button @click="refresh"><ReloadOutlined /> 刷新</a-button>
    </template>
    <div class="space-y-6">
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <a-card v-for="a in agents" :key="a.id" hoverable class="agent-card">
        <div class="flex items-start justify-between mb-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg" :style="{ background: a.color }">{{ a.name.charAt(0) }}</div>
          <a-badge :status="a.online ? 'success' : 'default'" />
        </div>
        <h3 class="font-semibold text-gray-900">{{ a.name }}</h3>
        <p class="text-xs text-gray-500 mt-1">{{ a.desc }}</p>
        <div class="mt-3 flex flex-wrap gap-1">
          <a-tag v-for="c in a.capabilities.slice(0,3)" :key="c" size="small">{{ c }}</a-tag>
        </div>
        <div class="mt-3 flex justify-between text-xs text-gray-400">
          <span>调用 {{ a.calls }}次</span><span>成功率 {{ a.successRate }}%</span>
        </div>
      </a-card>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <a-card title="最近协作任务">
        <a-timeline>
          <a-timeline-item v-for="t in recentTasks" :key="t.id" :color="t.status === 'done' ? 'green' : t.status === 'failed' ? 'red' : 'blue'">
            <p class="text-sm font-medium">{{ t.title }}</p>
            <p class="text-xs text-gray-400">{{ t.agents }} | {{ t.time }}</p>
          </a-timeline-item>
        </a-timeline>
      </a-card>
      <a-card title="能力标签云">
        <div class="flex flex-wrap gap-2">
          <a-tag v-for="(tag, i) in capabilityTags" :key="i" :color="tag.color" class="cursor-pointer px-3 py-1">{{ tag.name }}<span class="ml-1 text-xs opacity-70">{{ tag.count }}</span></a-tag>
        </div>
      </a-card>
    </div>
    <a-card title="Agent调用统计（最近7天）">
      <div class="h-48 flex items-end gap-2">
        <div v-for="(b, i) in chartBars" :key="i" class="flex-1 flex flex-col items-center">
          <span class="text-xs text-gray-500 mb-1">{{ b.value }}</span>
          <div class="w-full rounded-t bg-gradient-to-t from-blue-500 to-cyan-400 transition-all" :style="{ height: `${(b.value / maxVal) * 140}px` }" />
          <span class="text-xs text-gray-400 mt-1">{{ b.label }}</span>
        </div>
      </div>
    </a-card>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { YdPage } from '@/components/youding'
import { Card, Badge, Tag, Timeline, TimelineItem, Button, message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { apiGet } from '@/utils/api'

const agents = ref<any[]>([])

const recentTasks = ref<any[]>([])

const capabilityTags = ref<any[]>([])

const chartBars = ref<any[]>([])
const maxVal = ref(Math.max(...chartBars.value.map(b => b.value)))

async function loadData() {
  try {
    const d = await apiGet('/agent-hub/')
    if (d && d.agents && d.agents.length) agents.value = d.agents
    if (d && d.completed_tasks != null) {
      recentTasks.value = [
        { id: 1, title: '已完成任务', agents: `${d.completed_tasks}次`, time: '累计', status: 'done' },
        { id: 2, title: '待处理任务', agents: `${d.pending_tasks}次`, time: '当前', status: 'idle' },
        { id: 3, title: '失败任务', agents: `${d.failed_tasks}次`, time: '累计', status: 'failed' },
      ]
    }
  } catch {
    agents.value = []
    recentTasks.value = []
    message.warning('协同看板加载失败')
  }
}

async function refresh() {
  await loadData()
  message.success('已刷新')
}

onMounted(loadData)
</script>
