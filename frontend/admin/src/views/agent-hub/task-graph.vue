/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="任务图" subtitle="统一编排链 · AiTask 任务图（Hermes）" surface="elevated">
    <template #actions>
      <a-button @click="refreshAll" :loading="loading"><ReloadOutlined /> 刷新</a-button>
    </template>

    <div class="space-y-6">
      <!-- ① 提交编排任务 -->
      <a-card title="提交编排任务">
        <a-form layout="vertical">
          <a-form-item label="提交方式">
            <a-radio-group v-model:value="mode" button-style="solid">
              <a-radio-button value="intent">自然语言（自动拆解）</a-radio-button>
              <a-radio-button value="direct">指定任务类型</a-radio-button>
            </a-radio-group>
          </a-form-item>

          <!-- 自然语言模式：一句话 → 后端 decompose() 拆图 -->
          <template v-if="mode === 'intent'">
            <a-form-item label="意图描述" required>
              <a-textarea
                v-model:value="form.intent"
                :rows="3"
                placeholder="例如：帮我用这些产品图建一个英文官网并推广 / 找德国保温材料买家并写开发信"
              />
            </a-form-item>
            <a-form-item label="业务参数（JSON，可选）">
              <a-textarea
                v-model:value="form.input_json"
                :rows="3"
                placeholder='例如：{"product_name": "轻集料混凝土", "product_images": ["https://..."]}'
              />
            </a-form-item>
          </template>

          <!-- 指定类型模式：直连 /orchestration/tasks -->
          <template v-else>
            <a-row :gutter="16">
              <a-col :xs="24" :md="8">
                <a-form-item label="任务类型" required>
                  <a-select v-model:value="form.task_type" :options="taskTypeOptions" show-search />
                </a-form-item>
              </a-col>
              <a-col :xs="24" :md="8">
                <a-form-item label="优先级（1 高 – 10 低）">
                  <a-input-number v-model:value="form.priority" :min="1" :max="10" style="width: 100%" />
                </a-form-item>
              </a-col>
              <a-col :xs="24" :md="8">
                <a-form-item label="幂等键（可选，防重复派发）">
                  <a-input v-model:value="form.idempotency_key" placeholder="留空则不校验" />
                </a-form-item>
              </a-col>
            </a-row>
            <a-form-item label="任务输入（JSON）">
              <a-textarea
                v-model:value="form.input_json"
                :rows="4"
                placeholder='例如：{"product_name": "轻集料混凝土", "product_images": ["https://..."]}'
              />
            </a-form-item>
          </template>

          <a-form-item>
            <a-space>
              <a-button type="primary" :loading="submitting" @click="submit">
                <ThunderboltOutlined /> {{ mode === 'intent' ? '拆解并派发' : '提交并派发' }}
              </a-button>
              <a-checkbox v-model:checked="form.auto_dispatch">创建后立即执行</a-checkbox>
            </a-space>
          </a-form-item>
        </a-form>

        <!-- 提交结果：只显示后端真实返回，不伪造 -->
        <a-alert
          v-if="submitResult"
          :type="submitResult.ok ? 'success' : 'error'"
          show-icon
          class="mt-2"
        >
          <template #message>
            {{ submitResult.ok ? '已提交' : '提交失败' }}
          </template>
          <template #description>
            <div v-if="submitResult.ok">
              <div v-if="submitResult.taskId">task_id：<code>{{ submitResult.taskId }}</code></div>
              <div v-if="submitResult.status">status：{{ submitResult.status }}</div>
              <div v-if="submitResult.planId">plan_id：<code>{{ submitResult.planId }}</code></div>
              <div v-if="submitResult.graphSource">
                拆解来源：<a-tag>{{ submitResult.graphSource }}</a-tag>
                · 节点数：{{ submitResult.nodeCount }}
              </div>
              <div v-if="submitResult.detail">{{ submitResult.detail }}</div>
            </div>
            <div v-else>{{ submitResult.error }}</div>
          </template>
        </a-alert>
      </a-card>

      <!-- ② 待人工审核 / 待干预 -->
      <a-card title="待人工审核 / 待干预">
        <div ref="tablePanelRef" class="yd-panel yd-table-panel">
          <div class="panel-head mb-3">
            <YdTableToolbar
              :loading="loading"
              :target-ref="tablePanelRef"
              :show-export="false"
              @refresh="refreshAll"
            />
          </div>

          <YdDataTable
            :columns="columns"
            :data-source="pending"
            :loading="loading"
            :pagination="{ current: page, pageSize: pageSize, total: total }"
            :table-props="{ size: tableSize, rowKey: 'id' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="statusColor(String(record.status))">{{ statusText(String(record.status)) }}</a-tag>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button size="small" @click="act('resume', record)">恢复</a-button>
                  <a-button size="small" danger @click="act('cancel', record)">取消</a-button>
                  <a-button size="small" @click="act('retry', record)">重试</a-button>
                </a-space>
              </template>
            </template>
          </YdDataTable>
        </div>
      </a-card>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { Card, Alert, Tag, Button, Space, Row, Col, Form, FormItem, Input, InputNumber, Select, Checkbox, message } from 'ant-design-vue'
import { ReloadOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import {
  createOrchestrationTask,
  createTaskFromIntent,
  listPendingReviews,
  resumeTask,
  cancelTask,
  retryTask,
  type TaskControlItem,
} from '@/api/orchestration'

const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const tablePanelRef = ref<HTMLElement | null>(null)
const loading = ref(false)
const submitting = ref(false)
const pending = ref<TaskControlItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

/** 提交方式：intent=自然语言自动拆解；direct=直接指定 task_type */
const mode = ref<'intent' | 'direct'>('intent')

/** 可派发的任务类型（来自 hermes_task_bridge.ROUTERS + 已注册执行器） */
const taskTypeOptions = [
  { value: 'hermes_node:site_builder', label: '建站（site_builder）' },
  { value: 'hermes_node:deerflow', label: '研究/内容（deerflow）' },
  { value: 'hermes_node:accio', label: '销售飞轮（accio）' },
  { value: 'hermes_node:trade_ai_agent', label: '社媒拓客（trade_ai_agent）' },
  { value: 'hermes_node:goodjob_crm', label: '履约单证（goodjob_crm）' },
  { value: 'site_build', label: '建站（ROUTERS 直连）' },
  { value: 'ubrain_intent', label: 'UBrain 意图' },
  { value: 'deepseek_harness', label: 'DeepSeek Harness' },
]

const form = reactive({
  intent: '',
  task_type: 'hermes_node:site_builder',
  priority: 5,
  idempotency_key: '',
  input_json: '{\n  "product_name": ""\n}',
  auto_dispatch: true,
})

interface SubmitResult {
  ok: boolean
  taskId?: string
  status?: string
  detail?: string
  error?: string
  planId?: string
  graphSource?: string
  nodeCount?: number
}
const submitResult = ref<SubmitResult | null>(null)

const columns = [
  { title: '任务 ID', dataIndex: 'id', key: 'id', width: 300 },
  { title: '类型', dataIndex: 'task_type', key: 'task_type', width: 220 },
  { title: '状态', key: 'status', width: 110 },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
  { title: '父任务', dataIndex: 'parent_task_id', key: 'parent_task_id', width: 300 },
  { title: '操作', key: 'action', width: 200 },
]

function statusColor(s: string) {
  return ({
    review: 'processing',
    wait_human: 'warning',
    paused: 'default',
    created: 'default',
    running: 'processing',
    done: 'success',
    failed: 'error',
  } as Record<string, string>)[s] || 'default'
}
function statusText(s: string) {
  return ({
    review: '待审核',
    wait_human: '待人工',
    paused: '已暂停',
    created: '待执行',
    planning: '规划中',
    executing: '执行中',
    done: '完成',
    failed: '失败',
    cancelled: '已取消',
    skipped: '已跳过',
  } as Record<string, string>)[s] || s
}

/** 拉取待审核任务 —— 失败即如实报错，绝不伪造本地数据 */
async function loadPending() {
  loading.value = true
  try {
    const d = await listPendingReviews({ page: page.value, page_size: pageSize.value })
    pending.value = d.items || []
    total.value = d.total || 0
  } catch (e: any) {
    pending.value = []
    total.value = 0
    message.error(`待审核任务加载失败：${e?.message || e}`)
  } finally {
    loading.value = false
  }
}

async function refreshAll() {
  await loadPending()
}

async function submit() {
  let inputData: Record<string, unknown> = {}
  const raw = (form.input_json || '').trim()
  if (raw) {
    try {
      inputData = JSON.parse(raw)
    } catch {
      message.error('业务参数不是合法 JSON')
      return
    }
  }

  submitting.value = true
  submitResult.value = null

  try {
    if (mode.value === 'intent') {
      // 自然语言模式：后端 decompose() 自动拆图
      if (!form.intent.trim()) {
        message.warning('请填写意图描述')
        submitting.value = false
        return
      }
      const r = await createTaskFromIntent({
        intent: form.intent.trim(),
        payload: inputData,
        channel: 'web',
        auto_dispatch: form.auto_dispatch,
      })
      submitResult.value = {
        ok: true,
        planId: r.plan_id,
        graphSource: r.graph_source,
        nodeCount: r.node_count,
        status: r.dispatched ? '已派发' : '已入库未派发',
        detail: `节点任务 ${r.node_tasks.length} 个`,
      }
      message.success('已拆解并入库')
    } else {
      // 指定类型模式：直连
      const r = await createOrchestrationTask({
        task_type: form.task_type,
        input_data: inputData,
        idempotency_key: form.idempotency_key || undefined,
        priority: form.priority,
        auto_dispatch: form.auto_dispatch,
      })
      submitResult.value = { ok: true, taskId: r.task_id, status: r.status, detail: r.detail }
      message.success('已提交并派发')
    }
    if (form.auto_dispatch) await loadPending()
  } catch (e: any) {
    // 如实报错，不造本地假任务
    submitResult.value = { ok: false, error: String(e?.message || e) }
    message.error('提交失败，详见下方提示')
  } finally {
    submitting.value = false
  }
}

async function act(kind: 'resume' | 'cancel' | 'retry', record: TaskControlItem) {
  try {
    if (kind === 'resume') await resumeTask(String(record.id))
    else if (kind === 'cancel') await cancelTask(String(record.id))
    else await retryTask(String(record.id))
    message.success(kind === 'resume' ? '已恢复' : kind === 'cancel' ? '已取消' : '已重试')
    await loadPending()
  } catch (e: any) {
    message.error(`${kind} 失败：${e?.message || e}`)
  }
}

onMounted(loadPending)
</script>
