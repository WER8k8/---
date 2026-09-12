<template>
  <YdPage title="MCP桥接" subtitle="Model Context Protocol 服务管理与工具发现" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showAddModal = true"><PlusOutlined /> 添加MCP服务</a-button>
    </template>
    <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <a-card v-for="s in servers" :key="s.id" hoverable class="server-card">
        <div class="flex items-center justify-between mb-3">
          <h3 class="font-semibold">{{ s.name }}</h3>
          <a-badge :status="s.healthy ? 'success' : 'error'" />
        </div>
        <p class="text-xs text-gray-500 mb-2">{{ s.url }}</p>
        <a-tag>{{ s.protocol }}</a-tag>
        <p class="text-xs text-gray-400 mt-2">工具: {{ s.toolCount }} | 延迟: {{ s.latency }}ms</p>
        <div class="mt-3 flex gap-2">
          <a-button size="small" @click="testConnection(s)">测试</a-button>
          <a-button size="small" @click="showTools(s)">工具</a-button>
          <a-popconfirm title="确定删除？" @confirm="removeServer(s.id)"><a-button size="small" danger>删除</a-button></a-popconfirm>
        </div>
      </a-card>
    </div>
    <a-modal v-model:open="showAddModal" title="添加MCP服务" @ok="addServer" ok-text="添加">
      <a-form :model="newServer" layout="vertical">
        <a-form-item label="服务名称" required><a-input v-model:value="newServer.name" placeholder="例如: fbs-connector" /></a-form-item>
        <a-form-item label="服务URL" required><a-input v-model:value="newServer.url" placeholder="http://localhost:9001" /></a-form-item>
        <a-form-item label="协议类型"><a-select v-model:value="newServer.protocol"><a-select-option value="stdio">STDIO</a-select-option><a-select-option value="sse">SSE</a-select-option><a-select-option value="http">HTTP</a-select-option></a-select></a-form-item>
      </a-form>
    </a-modal>
    <a-modal v-model:open="toolsModal.open" :title="`工具列表 — ${toolsModal.serverName}`" :footer="null" width="700">
      <div ref="toolsPanelRef" class="yd-panel yd-table-panel">
        <YdDataTable
          :columns="toolColumns"
          :data-source="toolsModal.tools"
          :pagination="false"
          :table-props="{ size: tableSize, rowKey: 'name' }"
        />
      </div>
    </a-modal>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { Card, Badge, Tag, Button, Modal, Form, FormItem, Input, Select, SelectOption, Popconfirm, message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { apiGet, apiPost } from '@/utils/api'

const showAddModal = ref(false)
const toolsPanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const newServer = reactive({ name: '', url: '', protocol: 'http' })

const servers = ref<any[]>([])

const toolsModal = reactive({ open: false, serverName: '', tools: [] as any[] })

const toolColumns = [
  { title: '工具名', dataIndex: 'name', key: 'name' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '参数数', dataIndex: 'paramCount', key: 'paramCount', width: 80 },
]

async function loadServers() {
  try {
    const d = await apiGet('/agent-hub/mcp-bridge')
    if (d && d.tools && d.tools.length) {
      servers.value = d.tools.map((t: any, i: number) => ({
        id: i + 1, name: t.name || `服务${i+1}`, url: t.url || '',
        protocol: t.protocol || 'HTTP', healthy: t.healthy !== false,
        toolCount: t.tool_count || 0, latency: t.latency || 0,
      }))
    }
  } catch {
    servers.value = []
    message.warning('MCP 服务列表加载失败')
  }
}

async function loadTools(serverName: string) {
  try {
    const d = await apiGet('/agent-hub/mcp-bridge/tools')
    if (d && d.items && d.items.length) {
      toolsModal.tools = d.items.map((t: any) => ({
        name: t.name, description: t.description || '',
        paramCount: t.param_count || 0,
      }))
    } else {
      toolsModal.tools = []
    }
  } catch {
    toolsModal.tools = []
    message.warning('工具列表加载失败')
  }
}

function testConnection(s: any) {
  message.loading(`正在测试 ${s.name}...`, 1)
  apiGet(`/agent-hub/mcp-bridge/health?name=${encodeURIComponent(s.name)}`)
    .then((d: any) => {
      s.healthy = d?.healthy !== false
      s.latency = Number(d?.latency_ms ?? 0)
      message[s.healthy ? 'success' : 'error'](s.healthy ? `${s.name} 连接正常` : `${s.name} 连接失败`)
    })
    .catch(() => {
      s.healthy = false
      s.latency = 0
      message.error(`${s.name} 连接失败`)
    })
}

function showTools(s: any) {
  toolsModal.serverName = s.name
  toolsModal.tools = []
  loadTools(s.name)
  toolsModal.open = true
}

async function addServer() {
  if (!newServer.name || !newServer.url) { message.warning('请填写完整信息'); return }
  try {
    await apiPost('/agent-hub/mcp-bridge', {
      name: newServer.name, url: newServer.url, protocol: newServer.protocol,
    })
    loadServers()
    message.success('已添加')
  } catch {
    message.error('添加失败，请检查后端服务')
  }
  showAddModal.value = false
  newServer.name = ''
  newServer.url = ''
}

function removeServer(id: number) { servers.value = servers.value.filter(s => s.id !== id); message.success('已删除') }

onMounted(loadServers)
</script>
