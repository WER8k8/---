/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 * 待办提醒板 · 销售任务中心：契约对齐 + follow-up 引擎接线（无假成功）
 */
<template>
  <YdPage
    surface="elevated"
    title="销售任务中心"
    subtitle="待办提醒板 · RFQ 响应 / 报价审批 / 跟进提醒"
  >
    <div class="task-center">
      <div class="flex flex-wrap items-center justify-between gap-3 mb-4">
        <a-space wrap>
          <a-select
            v-model:value="filterStatus"
            placeholder="状态"
            allow-clear
            style="width: 140px"
            @change="() => fetchData(1)"
          >
            <a-select-option value="open">待处理</a-select-option>
            <a-select-option value="done">已完成</a-select-option>
            <a-select-option value="cancelled">已取消</a-select-option>
          </a-select>
          <a-select
            v-model:value="filterType"
            placeholder="类型"
            allow-clear
            style="width: 140px"
            @change="() => fetchData(1)"
          >
            <a-select-option v-for="t in typeOptions" :key="t.value" :value="t.value">
              {{ t.label }}
            </a-select-option>
          </a-select>
          <a-button @click="() => fetchData()">刷新</a-button>
          <a-button type="primary" @click="openCreate">新建任务</a-button>
        </a-space>
        <span class="text-xs text-slate-400">状态真相：open / done / cancelled（兼容 pending/completed 别名）</span>
      </div>

      <div class="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <a-table
          :dataSource="items"
          :columns="columns"
          :loading="loading"
          :pagination="{ total, pageSize: pageSize, current: page, showSizeChanger: false }"
          rowKey="id"
          size="middle"
          @change="handleTableChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'task_type'">
              <a-tag>{{ typeLabel(String(record.task_type || '')) }}</a-tag>
            </template>
            <template v-else-if="column.key === 'priority'">
              <a-tag :color="priorityColor(String(record.priority || ''))">
                {{ priorityLabel(String(record.priority || '')) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'due_at'">
              <span :class="isOverdue(record.due_at, record.status) ? 'text-red-500 font-medium' : ''">
                {{ formatDue(record.due_at) }}
              </span>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-select
                :value="canonicalStatus(String(record.status || 'open'))"
                size="small"
                style="width: 110px"
                @change="(v: unknown) => updateStatus(String(record.id), String(v))"
              >
                <a-select-option value="open">待处理</a-select-option>
                <a-select-option value="done">已完成</a-select-option>
                <a-select-option value="cancelled">已取消</a-select-option>
              </a-select>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button
                  v-if="record.rfq_id"
                  size="small"
                  type="link"
                  @click="goRfq(String(record.rfq_id))"
                >
                  关联 RFQ
                </a-button>
                <a-button size="small" type="link" @click="openFollowUpFor(record as SalesTaskItem)">跟进建议</a-button>
              </a-space>
            </template>
          </template>
        </a-table>

        <a-card size="small" title="跟进提醒（Follow-up 引擎）">
          <a-alert
            class="mb-3"
            type="info"
            show-icon
            message="建议来自后端 /follow-up/*，未配置外发时不会伪造已发送"
          />
          <div class="space-y-2 text-sm">
            <div>
              <div class="text-slate-500">建议发送时刻</div>
              <div v-if="bestSend.best_time_utc">{{ bestSend.best_time_utc }}（{{ bestSend.timezone || 'default' }}）</div>
              <div v-else class="text-slate-400">{{ bestSendError || '加载中…' }}</div>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <div class="text-slate-500 mb-1">阶段</div>
                <a-select v-model:value="fuStage" style="width: 100%" size="small">
                  <a-select-option v-for="s in FOLLOW_UP_STAGES" :key="s.value" :value="s.value">
                    {{ s.label }}
                  </a-select-option>
                </a-select>
              </div>
              <div>
                <div class="text-slate-500 mb-1">触发</div>
                <a-select v-model:value="fuTrigger" style="width: 100%" size="small">
                  <a-select-option v-for="t in FOLLOW_UP_TRIGGERS" :key="t.value" :value="t.value">
                    {{ t.label }}
                  </a-select-option>
                </a-select>
              </div>
            </div>
            <a-space>
              <a-button size="small" type="primary" :loading="fuLoading" @click="loadNextAction">下一步动作</a-button>
              <a-button size="small" :loading="fuLoading" @click="loadShouldStop">是否停跟</a-button>
              <a-button size="small" :loading="fuLoading" @click="loadAnalyze">策略摘要</a-button>
            </a-space>
            <a-alert v-if="fuError" type="error" show-icon :message="fuError" />
            <div v-if="nextAction" class="p-2 bg-slate-50 rounded text-xs whitespace-pre-wrap">
              <div class="font-medium mb-1">下一步建议</div>
              <div v-if="'message' in nextAction && nextAction.message">{{ nextAction.message }}</div>
              <template v-else>
                <div>渠道：{{ (nextAction as FollowUpActionDict).channel || '—' }}</div>
                <div>主题：{{ (nextAction as FollowUpActionDict).subject || '—' }}</div>
                <div>延迟：{{ (nextAction as FollowUpActionDict).delay || '—' }}</div>
                <div>原因：{{ (nextAction as FollowUpActionDict).reason || '—' }}</div>
              </template>
            </div>
            <div v-if="shouldStop" class="p-2 bg-amber-50 rounded text-xs">
              停跟判断：{{ shouldStop.should_stop ? '建议停止' : '可继续' }}
              <span v-if="shouldStop.reason"> — {{ shouldStop.reason }}</span>
            </div>
            <div v-if="analyze" class="p-2 bg-slate-50 rounded text-xs">
              <div class="font-medium mb-1">策略矩阵</div>
              <div v-for="(s, k) in analyze.strategies" :key="k">
                {{ s.label || k }} · 步骤 {{ s.steps ?? '—' }} · 效果 {{ s.total_effect ?? '—' }}
              </div>
            </div>
          </div>
        </a-card>
      </div>
    </div>

    <a-modal
      v-model:open="createOpen"
      title="新建销售任务"
      :confirm-loading="creating"
      @ok="submitCreate"
    >
      <a-form layout="vertical">
        <a-form-item label="标题" required>
          <a-input v-model:value="createForm.title" placeholder="例如：跟进 SA 仓库保温项目报价" />
        </a-form-item>
        <a-form-item label="说明">
          <a-textarea v-model:value="createForm.description" :rows="3" />
        </a-form-item>
        <div class="grid grid-cols-2 gap-3">
          <a-form-item label="类型">
            <a-select v-model:value="createForm.task_type">
              <a-select-option v-for="t in typeOptions" :key="t.value" :value="t.value">
                {{ t.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="优先级">
            <a-select v-model:value="createForm.priority">
              <a-select-option value="high">高</a-select-option>
              <a-select-option value="normal">中</a-select-option>
              <a-select-option value="low">低</a-select-option>
            </a-select>
          </a-form-item>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <a-form-item label="到期">
            <a-input v-model:value="createForm.due_at" placeholder="2026-09-25T10:00:00+08:00" />
          </a-form-item>
          <a-form-item label="关联 RFQ ID（可选）">
            <a-input v-model:value="createForm.rfq_id" allow-clear />
          </a-form-item>
        </div>
        <a-form-item label="关联线索 ID（可选）">
          <a-input v-model:value="createForm.lead_id" allow-clear />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import {
  FOLLOW_UP_STAGES,
  FOLLOW_UP_TRIGGERS,
  TASK_TYPE_LABELS,
  createSalesTask,
  fetchBestSendTime,
  fetchFollowUpAnalyze,
  fetchFollowUpNextAction,
  fetchShouldStop,
  listSalesTasks,
  updateSalesTaskStatus,
  type FollowUpActionDict,
  type SalesTaskItem,
} from '@/api/salesTask'

const router = useRouter()

const items = ref<SalesTaskItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const filterStatus = ref<string | undefined>(undefined)
const filterType = ref<string | undefined>(undefined)

const typeOptions = [
  { value: 'followup', label: TASK_TYPE_LABELS.followup! },
  { value: 'rfq_response', label: TASK_TYPE_LABELS.rfq_response! },
  { value: 'quote_approval', label: TASK_TYPE_LABELS.quote_approval! },
  { value: 'outbound', label: TASK_TYPE_LABELS.outbound! },
  { value: 'review', label: TASK_TYPE_LABELS.review! },
]

const columns = [
  { title: '任务', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '类型', key: 'task_type', width: 110 },
  { title: '优先级', key: 'priority', width: 90 },
  { title: '到期', key: 'due_at', width: 170 },
  { title: '状态', key: 'status', width: 130 },
  { title: '操作', key: 'actions', width: 160 },
]

const createOpen = ref(false)
const creating = ref(false)
const createForm = reactive({
  title: '',
  description: '',
  task_type: 'followup',
  priority: 'normal',
  due_at: '',
  rfq_id: '',
  lead_id: '',
})

const bestSend = ref<{ best_time_utc?: string; timezone?: string }>({})
const bestSendError = ref('')
const fuStage = ref('initial')
const fuTrigger = ref('no_response')
const fuLoading = ref(false)
const fuError = ref('')
const nextAction = ref<(FollowUpActionDict & { action?: null; message?: string }) | null>(null)
const shouldStop = ref<{ should_stop?: boolean; reason?: string } | null>(null)
const analyze = ref<{
  strategies?: Record<string, { label?: string; steps?: number; total_effect?: number }>
} | null>(null)

function typeLabel(t: string) {
  return TASK_TYPE_LABELS[t] || t || '—'
}

function priorityLabel(p: string) {
  if (p === 'high') return '高'
  if (p === 'low') return '低'
  return '中'
}

function priorityColor(p: string) {
  if (p === 'high') return 'red'
  if (p === 'low') return 'default'
  return 'blue'
}

function canonicalStatus(s: string) {
  const v = (s || '').toLowerCase()
  if (v === 'done' || v === 'completed') return 'done'
  if (v === 'cancelled' || v === 'archived') return 'cancelled'
  return 'open'
}

function formatDue(d?: string | null) {
  if (!d) return '—'
  return String(d).slice(0, 16).replace('T', ' ')
}

function isOverdue(d?: string | null, status?: string) {
  if (!d) return false
  if (canonicalStatus(String(status || 'open')) !== 'open') return false
  const t = Date.parse(d)
  return Number.isFinite(t) && t < Date.now()
}

async function fetchData(nextPage?: number) {
  if (typeof nextPage === 'number') page.value = nextPage
  loading.value = true
  try {
    const data = await listSalesTasks({
      page: page.value,
      page_size: pageSize.value,
      status: filterStatus.value,
      task_type: filterType.value,
    })
    items.value = data?.items || []
    total.value = data?.total || 0
  } catch (e) {
    message.error(e instanceof Error ? e.message : '加载销售任务失败')
  } finally {
    loading.value = false
  }
}

async function updateStatus(id: string, status: string) {
  try {
    const canonical = canonicalStatus(status)
    await updateSalesTaskStatus(id, canonical as 'open' | 'done' | 'cancelled')
    message.success('状态已更新')
    await fetchData()
  } catch (e) {
    message.error(e instanceof Error ? e.message : '状态更新失败')
  }
}

function handleTableChange(p: { current?: number }) {
  fetchData(p?.current || 1)
}

function openCreate() {
  createForm.title = ''
  createForm.description = ''
  createForm.task_type = 'followup'
  createForm.priority = 'normal'
  createForm.due_at = ''
  createForm.rfq_id = ''
  createForm.lead_id = ''
  createOpen.value = true
}

async function submitCreate() {
  if (!createForm.title.trim()) {
    message.warning('请填写任务标题')
    return
  }
  creating.value = true
  try {
    await createSalesTask({
      title: createForm.title.trim(),
      description: createForm.description || undefined,
      task_type: createForm.task_type,
      priority: createForm.priority,
      due_at: createForm.due_at || undefined,
      rfq_id: createForm.rfq_id || undefined,
      lead_id: createForm.lead_id || undefined,
    })
    message.success('任务已创建')
    createOpen.value = false
    await fetchData(1)
  } catch (e) {
    message.error(e instanceof Error ? e.message : '创建失败（销售角色无创建权限时会 403）')
  } finally {
    creating.value = false
  }
}

function goRfq(rfqId: string) {
  void router.push({ path: '/sales/rfqs', query: { rfq_id: rfqId } })
}

function openFollowUpFor(record: SalesTaskItem | Record<string, unknown>) {
  const rec = record as SalesTaskItem
  const t = String(rec.task_type || '')
  if (t === 'rfq_response') {
    fuTrigger.value = 'no_response'
    fuStage.value = 'follow_up_1'
  } else if (t === 'quote_approval') {
    fuTrigger.value = 'opened_no_reply'
    fuStage.value = 'follow_up_2'
  } else {
    fuStage.value = 'initial'
    fuTrigger.value = 'no_response'
  }
  void loadNextAction()
}

async function loadBestSend() {
  try {
    bestSend.value = await fetchBestSendTime('default')
    bestSendError.value = ''
  } catch (e) {
    bestSend.value = {}
    bestSendError.value = e instanceof Error ? e.message : '发送时刻不可用'
  }
}

async function loadNextAction() {
  fuLoading.value = true
  fuError.value = ''
  try {
    nextAction.value = (await fetchFollowUpNextAction({
      trigger: fuTrigger.value,
      current_stage: fuStage.value,
    })) as FollowUpActionDict & { action?: null; message?: string }
    shouldStop.value = null
    analyze.value = null
  } catch (e) {
    nextAction.value = null
    fuError.value = e instanceof Error ? e.message : '跟进建议获取失败'
  } finally {
    fuLoading.value = false
  }
}

async function loadShouldStop() {
  fuLoading.value = true
  fuError.value = ''
  try {
    shouldStop.value = await fetchShouldStop({
      current_stage: fuStage.value,
      trigger: fuTrigger.value,
    })
  } catch (e) {
    shouldStop.value = null
    fuError.value = e instanceof Error ? e.message : '停跟判断失败'
  } finally {
    fuLoading.value = false
  }
}

async function loadAnalyze() {
  fuLoading.value = true
  fuError.value = ''
  try {
    analyze.value = await fetchFollowUpAnalyze()
  } catch (e) {
    analyze.value = null
    fuError.value = e instanceof Error ? e.message : '策略摘要获取失败'
  } finally {
    fuLoading.value = false
  }
}

onMounted(() => {
  void fetchData()
  void loadBestSend()
})
</script>

<style scoped>
.task-center {
  animation: fadeIn 0.3s ease;
}
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
