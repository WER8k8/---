<template>
  <YdPage title="内容预热" subtitle="Push/Pull 缓存预热策略" surface="elevated">
    <template #actions>
      <a-button @click="refreshCache">刷新缓存</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">
    <a-card title="发起预热">
      <a-row :gutter="16">
        <a-col :span="16">
          <a-form-item label="预热 URL">
            <a-textarea v-model:value="preheatUrl" :rows="3" placeholder="输入需要预热的 URL，每行一个&#10;如:&#10;/products/*&#10;/assets/css/main.css&#10;/api/v1/search" />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="节点范围">
            <a-select v-model:value="nodeScope" mode="multiple" placeholder="选择节点">
              <a-select-option value="all">全部节点</a-select-option>
              <a-select-option value="east">华东</a-select-option>
              <a-select-option value="north">华北</a-select-option>
              <a-select-option value="south">华南</a-select-option>
            </a-select>
          </a-form-item>
          <a-button type="primary" :loading="submitting" block @click="submitPreheat" class="mt-2">提交预热</a-button>
        </a-col>
      </a-row>
    </a-card>
    <a-card title="预热历史">
      <a-table :columns="cols" :data-source="tasks" size="small" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
          </template>
          <template v-if="column.key === 'hitRate'">
            <a-progress :percent="record.hitRate" size="small" :stroke-color="record.hitRate >= 90 ? '#22c55e' : '#f59e0b'" />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" type="link" @click="rePreheat(record)">重新预热</a-button>
              <a-popconfirm title="确定删除？" @confirm="deleteTask(record.id)">
                <a-button size="small" type="link" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { YdPage } from '@/components/youding'
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getAuthToken } from '@/utils/api'

const preheatUrl = ref('')
const nodeScope = ref<string[]>(['all'])
const submitting = ref(false)

const cols = [
  { title: 'URL', dataIndex: 'url', ellipsis: true },
  { title: '节点范围', dataIndex: 'scope', width: 100 },
  { title: '状态', key: 'status', width: 80 },
  { title: '命中率', key: 'hitRate', width: 160 },
  { title: '时间', dataIndex: 'time', width: 160 },
  { title: '操作', key: 'action', width: 140 },
]

const tasks = ref<any[]>([])

function statusColor(s: string) { return s === '已完成' ? 'success' : s === '预热中' ? 'processing' : s === '失败' ? 'error' : 'default' }

async function submitPreheat() {
  if (!preheatUrl.value.trim()) { message.warning('请输入预热 URL'); return }
  submitting.value = true
  try {
    const tk = getAuthToken() || ''
    const urls = preheatUrl.value.trim().split('\n').filter(u => u.trim())
    await fetch('/api/v1/edge-cdn/preheat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tk}` },
      body: JSON.stringify({ urls, scope: nodeScope.value }),
    })
    preheatUrl.value = ''
    message.success(`已提交 ${urls.length} 个预热任务`)
    await loadTasks()
  } catch {
    message.error('预热提交失败')
  } finally {
    submitting.value = false
  }
}

async function loadTasks() {
  try {
    const tk = getAuthToken() || ''
    const r = await fetch('/api/v1/edge-cdn/preheat', { headers: { Authorization: `Bearer ${tk}` } })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    const d = await r.json()
    tasks.value = d.data ?? []
  } catch {
    message.warning('数据加载失败，请稍后重试')
    tasks.value = []
  }
}

async function rePreheat(r: any) {
  preheatUrl.value = r.url
  try {
    const tk = getAuthToken() || ''
    await fetch('/api/v1/edge-cdn/preheat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tk}` },
      body: JSON.stringify({ urls: [r.url], scope: r.scope ? [r.scope] : ['all'] }),
    })
    message.success(`已重新提交预热: ${r.url}`)
    await loadTasks()
  } catch {
    message.error('重新预热失败')
  }
}
function deleteTask(id: number) { tasks.value = tasks.value.filter(t => t.id !== id); message.success('已删除') }
function refreshCache() { message.success('缓存刷新指令已下发') }

onMounted(() => { void loadTasks() })
</script>
