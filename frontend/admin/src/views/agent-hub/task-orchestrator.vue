/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="任务调度" subtitle="多Agent协作任务编排" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showCreateModal = true"><PlusOutlined /> 创建编排</a-button>
    </template>
    <div class="space-y-6">
    <a-card title="编排列表">
      <div ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar
            :loading="listLoading"
            :target-ref="tablePanelRef"
            :show-export="false"
            @refresh="loadOrchestrations"
          />
        </div>
        <YdDataTable
          :columns="orchColumns"
          :data-source="orchestrations"
          :loading="listLoading"
          :pagination="{ current: 1, pageSize: 6, total: orchestrations.length }"
          :table-props="{ size: tableSize, rowKey: 'id' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="statusColor(record.status)">{{ statusText(record.status) }}</a-tag>
            </template>
            <template v-if="column.key === 'agents'">
              <a-tag v-for="a in record.agents" :key="a" size="small" class="mr-1">{{ a }}</a-tag>
            </template>
            <template v-if="column.key === 'action'">
              <a-space>
                <a-button size="small" @click="runOrch(record)" :disabled="record.status==='running'">执行</a-button>
                <a-button size="small" @click="viewLog(record)">日志</a-button>
              </a-space>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>
    <a-modal v-model:open="showCreateModal" title="创建任务编排" @ok="createOrch" ok-text="创建" width="600">
      <a-form :model="orchForm" layout="vertical">
        <a-form-item label="编排名称" required><a-input v-model:value="orchForm.name" placeholder="例如：周报自动生成链路" /></a-form-item>
        <a-form-item label="选择Agent" required>
          <a-select v-model:value="orchForm.agents" mode="multiple" placeholder="按顺序选择Agent"><a-select-option value="SEO分析师">SEO分析师</a-select-option><a-select-option value="文案生成器">文案生成器</a-select-option><a-select-option value="代码助手">代码助手</a-select-option><a-select-option value="翻译引擎">翻译引擎</a-select-option></a-select>
        </a-form-item>
        <a-form-item label="优先级"><a-select v-model:value="orchForm.priority"><a-select-option value="high">高</a-select-option><a-select-option value="normal">普通</a-select-option><a-select-option value="low">低</a-select-option></a-select></a-form-item>
        <a-form-item label="触发条件"><a-radio-group v-model:value="orchForm.trigger"><a-radio value="manual">手动</a-radio><a-radio value="schedule">定时</a-radio><a-radio value="webhook">Webhook</a-radio></a-radio-group></a-form-item>
      </a-form>
    </a-modal>
    <a-modal v-model:open="logModal.open" :title="`执行日志 — ${logModal.name}`" :footer="null" width="600">
      <div class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs max-h-80 overflow-y-auto">
        <div v-for="(l, i) in logModal.lines" :key="i" class="py-0.5">
          <span class="text-gray-500 mr-2">{{ l.ts }}</span>{{ l.msg }}
        </div>
      </div>
    </a-modal>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { Card, Tag, Button, Modal, Form, FormItem, Input, Select, SelectOption, RadioGroup, Radio, Space, message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { apiGet, apiPost } from '@/utils/api'

const showCreateModal = ref(false)
const tablePanelRef = ref<HTMLElement | null>(null)
const listLoading = ref(false)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const orchForm = reactive({ name: '', agents: [] as string[], priority: 'normal', trigger: 'manual' })

const orchColumns = [
  { title: '名称', dataIndex: 'name', key: 'name' }, { title: 'Agent链路', key: 'agents', width: 250 },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
  { title: '状态', key: 'status', width: 80 }, { title: '最后执行', dataIndex: 'lastRun', key: 'lastRun', width: 160 },
  { title: '操作', key: 'action', width: 140 },
]

const orchestrations = ref<any[]>([])

const logModal = reactive({ open: false, name: '', lines: [] as any[] })

function statusColor(s: string) { return { idle: 'default', running: 'processing', done: 'success', failed: 'error' }[s] || 'default' }
function statusText(s: string) { return { idle: '待执行', running: '执行中', done: '完成', failed: '失败' }[s] || s }

async function loadOrchestrations() {
  listLoading.value = true
  try {
    const d = await apiGet('/agent-hub/task-orchestrator')
    if (d && d.task_queue && d.task_queue.length) {
      orchestrations.value = d.task_queue.map((t: any, i: number) => ({
        id: i + 1, name: t.name || `任务${i+1}`, agents: t.agents || [],
        priority: t.priority || '普通', status: t.status || 'idle', lastRun: t.lastRun || '-',
      }))
    }
  } catch {
    orchestrations.value = []
    message.warning('任务列表加载失败，请稍后重试')
  }
  finally {
    listLoading.value = false
  }
}

async function runOrch(r: any) {
  r.status = 'running'
  try {
    const res: any = await apiPost('/agent-hub/task-orchestrator/run', { id: r.id, name: r.name })
    // 以后端返回为准，不再无条件判成功
    const ok = res?.success !== false && res?.status !== 'failed'
    r.status = ok ? 'done' : 'failed'
    r.lastRun = new Date().toLocaleString()
    if (ok) message.success(res?.message || '执行完成')
    else message.error(res?.message || res?.error || '执行失败')
  } catch (e: any) {
    // 如实报错，不伪造状态
    r.status = 'failed'
    message.error(`执行失败：${e?.message || e}`)
  }
}

async function viewLog(r: any) {
  logModal.name = r.name
  try {
    const d = await apiGet<{ lines?: { ts: string; msg: string }[]; name?: string }>(
      `/agent-hub/task-orchestrator/logs?job_id=${encodeURIComponent(String(r.id))}`,
    )
    logModal.lines = d?.lines?.length ? d.lines : [{ ts: '', msg: '暂无执行日志' }]
    if (d?.name) logModal.name = d.name
  } catch {
    logModal.lines = [{ ts: '', msg: '日志加载失败' }]
  }
  logModal.open = true
}

async function createOrch() {
  if (!orchForm.name || !orchForm.agents.length) { message.warning('请填写完整'); return }
  try {
    await apiPost('/agent-hub/task-orchestrator', {
      name: orchForm.name, agents: orchForm.agents,
      priority: orchForm.priority, trigger: orchForm.trigger,
    })
    showCreateModal.value = false
    orchForm.name = ''; orchForm.agents = []
    message.success('已创建')
    // 以后端为准刷新列表，不再本地伪造记录
    await loadOrchestrations()
  } catch (e: any) {
    // 创建失败即失败：不写入本地假记录，不提示"已创建"
    message.error(`创建失败：${e?.message || e}`)
  }
}

onMounted(loadOrchestrations)
</script>
