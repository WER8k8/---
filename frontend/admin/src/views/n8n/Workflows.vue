/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
      <span class="mr-3">🔗</span>n8n 工作流集成
    </h1>

    <!-- 操作栏 -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center space-x-2">
        <select v-model="filterScene" class="px-3 py-1.5 border rounded text-sm">
          <option value="">全部场景</option>
          <option value="site_built">建站完成</option>
          <option value="content_distributed">内容分发</option>
          <option value="lead_notified">线索通知</option>
        </select>
        <select v-model="filterEnabled" class="px-3 py-1.5 border rounded text-sm">
          <option value="">全部状态</option>
          <option value="true">已启用</option>
          <option value="false">已禁用</option>
        </select>
      </div>
      <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm" @click="showAddModal = true">
        + 注册工作流
      </button>
    </div>

    <!-- 工作流列表 -->
    <div class="bg-white rounded-lg shadow">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="px-4 py-3 text-left">名称</th>
              <th class="px-4 py-3 text-left">场景</th>
              <th class="px-4 py-3 text-left">端点</th>
              <th class="px-4 py-3 text-left">触发次数</th>
              <th class="px-4 py-3 text-left">最后触发</th>
              <th class="px-4 py-3 text-left">状态</th>
              <th class="px-4 py-3 text-left">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr v-for="wf in filteredWorkflows" :key="wf.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 font-medium">{{ wf.name }}</td>
              <td class="px-4 py-3">
                <span class="bg-blue-50 text-blue-600 px-2 py-0.5 rounded text-xs">{{ wf.scene || '通用' }}</span>
              </td>
              <td class="px-4 py-3 text-gray-500 text-xs font-mono max-w-xs truncate">{{ wf.endpoint_url }}</td>
              <td class="px-4 py-3">{{ wf.trigger_count || 0 }}</td>
              <td class="px-4 py-3 text-gray-500">{{ formatTime(wf.last_triggered_at) }}</td>
              <td class="px-4 py-3">
                <button
                  :class="wf.enabled ? 'text-green-600 bg-green-50' : 'text-gray-400 bg-gray-100'"
                  class="px-2 py-0.5 rounded text-xs"
                  @click="toggleWorkflow(wf)"
                >
                  {{ wf.enabled ? '已启用' : '已禁用' }}
                </button>
              </td>
              <td class="px-4 py-3 space-x-2">
                <button class="text-blue-500 hover:underline" @click="triggerWorkflow(wf)">触发</button>
                <button class="text-gray-500 hover:underline" @click="viewWorkflow(wf)">详情</button>
                <button class="text-red-500 hover:underline" @click="deleteWorkflow(wf)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="filteredWorkflows.length === 0" class="px-6 py-10 text-center text-gray-400">
        暂无工作流，点击"注册工作流"开始
      </div>
    </div>

    <!-- 注册工作流Modal -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        <h3 class="text-lg font-semibold mb-4">注册 n8n 工作流</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">工作流名称 *</label>
            <input v-model="newWorkflow.name" type="text" class="w-full px-3 py-2 border rounded" placeholder="如: 自动建站工作流" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">场景</label>
            <select v-model="newWorkflow.scene" class="w-full px-3 py-2 border rounded">
              <option value="site_built">建站完成</option>
              <option value="content_distributed">内容分发</option>
              <option value="lead_notified">线索通知</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Webhook URL *</label>
            <input v-model="newWorkflow.endpoint_url" type="url" class="w-full px-3 py-2 border rounded" placeholder="https://n8n.example.com/webhook/xxx" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">认证方式</label>
            <select v-model="newWorkflow.auth_type" class="w-full px-3 py-2 border rounded">
              <option value="none">无认证</option>
              <option value="header">Header (X-API-Key)</option>
              <option value="hmac">HMAC-SHA256</option>
            </select>
          </div>
          <div v-if="newWorkflow.auth_type !== 'none'">
            <label class="block text-sm font-medium text-gray-700 mb-1">认证密钥</label>
            <input v-model="newWorkflow.auth_secret" type="password" class="w-full px-3 py-2 border rounded" placeholder="输入API Key或HMAC密钥" />
          </div>
        </div>
        <div class="mt-6 flex justify-end space-x-3">
          <button class="px-4 py-2 border rounded hover:bg-gray-50" @click="showAddModal = false">取消</button>
          <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600" @click="addWorkflow">注册</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

const workflows = ref<any[]>([])
const filterScene = ref('')
const filterEnabled = ref('')
const showAddModal = ref(false)

const newWorkflow = reactive({
  name: '',
  scene: 'site_built',
  endpoint_url: '',
  auth_type: 'none',
  auth_secret: '',
})

const filteredWorkflows = computed(() => {
  let result = workflows.value
  if (filterScene.value) {
    result = result.filter(w => w.scene === filterScene.value)
  }
  if (filterEnabled.value !== '') {
    const enabled = filterEnabled.value === 'true'
    result = result.filter(w => w.enabled === enabled)
  }
  return result
})

onMounted(fetchWorkflows)

async function fetchWorkflows() {
  try {
    const { data } = await axios.get('/api/v1/n8n/workflows')
    workflows.value = data.items || []
  } catch {
    workflows.value = []
  }
}

function formatTime(t: string) {
  if (!t) return '从未'
  return new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function addWorkflow() {
  await axios.post('/api/v1/n8n/workflows', {
    ...newWorkflow,
    auth_config: newWorkflow.auth_type !== 'none' ? { secret: newWorkflow.auth_secret } : {},
  })
  showAddModal.value = false
  resetNewWorkflow()
  fetchWorkflows()
}

function resetNewWorkflow() {
  newWorkflow.name = ''
  newWorkflow.scene = 'site_built'
  newWorkflow.endpoint_url = ''
  newWorkflow.auth_type = 'none'
  newWorkflow.auth_secret = ''
}

async function toggleWorkflow(wf: any) {
  await axios.patch(`/api/v1/n8n/workflows/${wf.id}/toggle`)
  fetchWorkflows()
}

async function triggerWorkflow(wf: any) {
  await axios.post(`/api/v1/n8n/trigger-async/${wf.id}`)
  fetchWorkflows()
}

function viewWorkflow(wf: any) {
  alert(JSON.stringify(wf, null, 2))
}

async function deleteWorkflow(wf: any) {
  if (!confirm(`确定要删除工作流 "${wf.name}" 吗？`)) return
  await axios.delete(`/api/v1/n8n/workflows/${wf.id}`)
  fetchWorkflows()
}
</script>
