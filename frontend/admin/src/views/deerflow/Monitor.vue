/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
      <span class="mr-3">🦌</span>DeerFlow 执行引擎
    </h1>

    <!-- 状态统计 -->
    <div class="grid grid-cols-5 gap-4 mb-8">
      <div
        v-for="s in statusStats"
        :key="s.status"
        class="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition-shadow"
        :class="{ 'ring-2 ring-blue-400': filterStatus === s.status }"
        @click="filterStatus = filterStatus === s.status ? '' : s.status"
      >
        <div class="text-sm text-gray-500">{{ s.label }}</div>
        <div class="text-2xl font-bold mt-1" :class="s.color">{{ s.count }}</div>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="bg-white rounded-lg shadow">
      <div class="px-6 py-4 border-b flex items-center justify-between">
        <h2 class="text-lg font-semibold">任务列表</h2>
        <div class="flex items-center space-x-2">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索任务ID或意图..."
            class="px-3 py-1.5 border rounded text-sm w-64"
          />
          <button class="px-3 py-1.5 bg-blue-500 text-white rounded text-sm hover:bg-blue-600" @click="fetchJobs">
            刷新
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="px-4 py-3 text-left">任务ID</th>
              <th class="px-4 py-3 text-left">意图</th>
              <th class="px-4 py-3 text-left">状态</th>
              <th class="px-4 py-3 text-left">创建时间</th>
              <th class="px-4 py-3 text-left">耗时</th>
              <th class="px-4 py-3 text-left">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="job in filteredJobs" :key="job.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 font-mono text-xs">{{ job.id?.slice(0, 8) }}...</td>
              <td class="px-4 py-3">
                <span class="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">{{ job.intent }}</span>
              </td>
              <td class="px-4 py-3">
                <span :class="getStatusClass(job.status)">{{ job.status }}</span>
              </td>
              <td class="px-4 py-3 text-gray-500">{{ formatTime(job.created_at) }}</td>
              <td class="px-4 py-3 text-gray-500">{{ getDuration(job) }}</td>
              <td class="px-4 py-3 space-x-2">
                <button class="text-blue-500 hover:underline" @click="viewJob(job)">详情</button>
                <button
                  v-if="job.status === 'failed'"
                  class="text-green-500 hover:underline"
                  @click="retryJob(job)"
                >
                  重试
                </button>
                <button
                  v-if="job.status === 'wait_human'"
                  class="text-yellow-500 hover:underline"
                  @click="approveJob(job)"
                >
                  审批
                </button>
                <button
                  v-if="['created', 'planning', 'executing'].includes(job.status)"
                  class="text-red-500 hover:underline"
                  @click="cancelJob(job)"
                >
                  取消
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="filteredJobs.length === 0" class="px-6 py-10 text-center text-gray-400">
        暂无任务记录
      </div>
    </div>

    <!-- 任务详情Modal -->
    <div v-if="selectedJob" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg w-full max-w-2xl p-6 max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">任务详情</h3>
          <button class="text-gray-400 hover:text-gray-600 text-xl" @click="selectedJob = null">×</button>
        </div>
        <div class="space-y-3 text-sm">
          <div class="grid grid-cols-2 gap-3">
            <div><span class="text-gray-500">ID:</span> <code class="bg-gray-100 px-1 rounded">{{ selectedJob.id }}</code></div>
            <div><span class="text-gray-500">状态:</span> <span :class="getStatusClass(selectedJob.status)">{{ selectedJob.status }}</span></div>
            <div><span class="text-gray-500">意图:</span> {{ selectedJob.intent }}</div>
            <div><span class="text-gray-500">创建者:</span> {{ selectedJob.created_by || '系统' }}</div>
          </div>
          <div v-if="selectedJob.error_message" class="bg-red-50 border border-red-200 rounded p-3">
            <div class="text-red-700 font-medium mb-1">错误信息</div>
            <pre class="text-red-600 text-xs whitespace-pre-wrap">{{ selectedJob.error_message }}</pre>
          </div>
          <div v-if="selectedJob.log_text" class="bg-gray-50 rounded p-3">
            <div class="text-gray-700 font-medium mb-1">执行日志</div>
            <pre class="text-gray-600 text-xs whitespace-pre-wrap max-h-40 overflow-y-auto">{{ selectedJob.log_text }}</pre>
          </div>
          <div v-if="selectedJob.result_json" class="bg-green-50 rounded p-3">
            <div class="text-green-700 font-medium mb-1">执行结果</div>
            <pre class="text-green-600 text-xs whitespace-pre-wrap">{{ selectedJob.result_json }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const jobs = ref<any[]>([])
const searchQuery = ref('')
const filterStatus = ref('')
const selectedJob = ref<any>(null)

const statusStats = computed(() => {
  const statuses = [
    { status: 'created', label: '已创建', color: 'text-gray-600' },
    { status: 'planning', label: '规划中', color: 'text-blue-600' },
    { status: 'executing', label: '执行中', color: 'text-yellow-600' },
    { status: 'review', label: '待审核', color: 'text-purple-600' },
    { status: 'done', label: '已完成', color: 'text-green-600' },
  ]
  return statuses.map(s => ({
    ...s,
    count: jobs.value.filter(j => j.status === s.status).length,
  }))
})

const filteredJobs = computed(() => {
  let result = jobs.value
  if (filterStatus.value) {
    result = result.filter(j => j.status === filterStatus.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(j => j.id?.toLowerCase().includes(q) || j.intent?.toLowerCase().includes(q))
  }
  return result
})

onMounted(fetchJobs)

async function fetchJobs() {
  try {
    const { data } = await axios.get('/api/v1/deerflow/jobs')
    jobs.value = data.items || []
  } catch {
    jobs.value = []
  }
}

function getStatusClass(status: string) {
  const classes: Record<string, string> = {
    created: 'text-gray-600 bg-gray-100 px-2 py-0.5 rounded',
    planning: 'text-blue-600 bg-blue-50 px-2 py-0.5 rounded',
    executing: 'text-yellow-600 bg-yellow-50 px-2 py-0.5 rounded',
    review: 'text-purple-600 bg-purple-50 px-2 py-0.5 rounded',
    wait_human: 'text-orange-600 bg-orange-50 px-2 py-0.5 rounded',
    done: 'text-green-600 bg-green-50 px-2 py-0.5 rounded',
    failed: 'text-red-600 bg-red-50 px-2 py-0.5 rounded',
    cancelled: 'text-gray-400 bg-gray-50 px-2 py-0.5 rounded',
  }
  return classes[status] || 'text-gray-600 bg-gray-100 px-2 py-0.5 rounded'
}

function formatTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function getDuration(job: any) {
  if (!job.started_at) return '-'
  const start = new Date(job.started_at).getTime()
  const end = job.finished_at ? new Date(job.finished_at).getTime() : Date.now()
  const ms = end - start
  if (ms < 60000) return `${(ms / 1000).toFixed(0)}s`
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`
  return `${(ms / 3600000).toFixed(1)}h`
}

function viewJob(job: any) {
  selectedJob.value = job
}

async function retryJob(job: any) {
  await axios.post(`/api/v1/deerflow/jobs/${job.id}/retry`)
  fetchJobs()
}

async function approveJob(job: any) {
  await axios.post(`/api/v1/deerflow/jobs/${job.id}/approve`)
  fetchJobs()
}

async function cancelJob(job: any) {
  if (!confirm('确定要取消此任务吗？')) return
  await axios.post(`/api/v1/deerflow/jobs/${job.id}/cancel`)
  fetchJobs()
}
</script>
