<template>
  <YdPage title="L4 发布队列" subtitle="摸金校尉 staging · 人工审核通过/驳回" surface="elevated">
    <template #actions>
      <a-space>
        <router-link to="/admin/system/greedy-hub">
          <a-button>摸金总控</a-button>
        </router-link>
        <router-link to="/admin/system/greedy-cumulative">
          <a-button>累计看板</a-button>
        </router-link>
        <a-button :loading="loading" @click="load">刷新</a-button>
      </a-space>
    </template>

    <div v-if="snap" class="stat-row">
      <a-statistic title="队列深度" :value="snap.depth ?? 0" />
      <a-statistic title="自动发布" :value="snap.auto_publish_enabled ? 'ON' : 'OFF'" />
      <a-statistic title="审核历史" :value="history.length" />
    </div>

    <a-alert
      type="info"
      show-icon
      message="人工审核"
      description="通过 → 生成矩阵发布计划并给相关专家大赛加分；驳回 → 移出队列并记入历史。"
      class="mb-3"
    />

    <a-table
      :loading="loading"
      :data-source="items"
      :columns="cols"
      :row-key="rowKey"
      size="small"
      :pagination="{ pageSize: 20 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'channels'">
          <a-tag v-for="ch in record.publish_channels || []" :key="ch" class="ch-tag">{{ ch }}</a-tag>
          <span v-if="!(record.publish_channels || []).length">—</span>
        </template>
        <template v-else-if="column.key === 'preview'">
          <a-tooltip v-if="bodyText(record)" :title="bodyText(record)">
            {{ bodyText(record).slice(0, 60) }}…
          </a-tooltip>
          <span v-else>—</span>
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-space>
            <a-popconfirm title="确认通过并生成发布计划？" @confirm="review(record, 'approve')">
              <a-button type="primary" size="small" :loading="reviewingIndex === record.queue_index">通过</a-button>
            </a-popconfirm>
            <a-button size="small" danger @click="openReject(record)">驳回</a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-divider>审核历史</a-divider>
    <a-table
      :data-source="history"
      :columns="historyCols"
      row-key="rowKey"
      size="small"
      :pagination="{ pageSize: 10 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-tag :color="record.action === 'approved' ? 'green' : 'red'">{{ record.action }}</a-tag>
        </template>
      </template>
    </a-table>

    <a-divider>已创建 PublishTask</a-divider>
    <a-table
      :loading="tasksLoading"
      :data-source="publishTasks"
      :columns="taskCols"
      row-key="id"
      size="small"
      :pagination="{ pageSize: 10 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag>{{ record.status }}</a-tag>
        </template>
        <template v-else-if="column.key === 'actions'">
          <a-button v-if="record.status === 'failed'" size="small" @click="retryTask(String(record.id))">重试</a-button>
        </template>
      </template>
    </a-table>

    <a-modal v-model:open="rejectOpen" title="驳回原因" @ok="confirmReject">
      <a-textarea v-model:value="rejectReason" :rows="3" placeholder="可选：驳回原因" />
    </a-modal>
  </YdPage>
</template>
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import {
  fetchGreedyPublishHistory,
  fetchGreedyPublishQueue,
  fetchGreedySurvivalPublishTasks,
  retryPublishTask,
  reviewGreedyPublishItem,
  type GreedyPublishItem,
  type GreedyPublishQueue,
  type GreedyPublishReviewHistory,
} from '@/api/hermesGreedy'

const loading = ref(false)
const tasksLoading = ref(false)
const reviewingIndex = ref<number | null>(null)
const snap = ref<GreedyPublishQueue | null>(null)
const history = ref<(GreedyPublishReviewHistory & { rowKey: string })[]>([])
const publishTasks = ref<Record<string, unknown>[]>([])
const rejectOpen = ref(false)
const rejectReason = ref('')
const rejectTarget = ref<GreedyPublishItem | null>(null)

const items = computed(() => snap.value?.items || [])

const cols = [
  { title: '#', dataIndex: 'queue_index', key: 'queue_index', width: 48 },
  { title: 'SKU', dataIndex: 'sku', key: 'sku', width: 160, ellipsis: true },
  { title: 'locale', dataIndex: 'locale', key: 'locale', width: 80 },
  { title: '渠道', key: 'channels', width: 160 },
  { title: '预览', key: 'preview', width: 180 },
  { title: '入队时间', dataIndex: 'queued_at', key: 'queued_at', width: 170 },
  { title: '操作', key: 'actions', width: 160 },
]

const historyCols = [
  { title: '动作', key: 'action', width: 90 },
  { title: 'SKU', dataIndex: 'sku', key: 'sku', ellipsis: true },
  { title: '任务数', dataIndex: 'task_count', key: 'task_count', width: 70 },
  { title: '审核人', dataIndex: 'reviewer', key: 'reviewer', width: 100 },
  { title: '原因/备注', dataIndex: 'reason', key: 'reason', ellipsis: true },
  { title: '时间', dataIndex: 'reviewed_at', key: 'reviewed_at', width: 180 },
]

const taskCols = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '平台', dataIndex: 'platform_name', key: 'platform_name', width: 100 },
  { title: '状态', key: 'status', width: 90 },
  { title: '更新', dataIndex: 'updated_at', key: 'updated_at', width: 170 },
  { title: '操作', key: 'actions', width: 80 },
]

function rowKey(record: GreedyPublishItem, index: number) {
  return `${record.sku || 'item'}-${record.queued_at || index}`
}

function bodyText(record: GreedyPublishItem) {
  return String(record.body || record.body_preview || '')
}

async function load() {
  loading.value = true
  tasksLoading.value = true
  try {
    const [q, h, tasks] = await Promise.all([
      fetchGreedyPublishQueue(50),
      fetchGreedyPublishHistory(30),
      fetchGreedySurvivalPublishTasks(20).catch(() => ({ items: [] })),
    ])
    snap.value = q
    history.value = h.map((row, i) => ({
      ...row,
      rowKey: `${row.sku}-${row.reviewed_at || i}`,
    }))
    publishTasks.value = tasks.items || []
  } catch (e: unknown) {
    message.error((e as Error).message || '加载失败')
  } finally {
    loading.value = false
    tasksLoading.value = false
  }
}

async function retryTask(id: string) {
  try {
    await retryPublishTask(id)
    message.success('已重试')
    await load()
  } catch (e: unknown) {
    message.error((e as Error).message || '重试失败')
  }
}

async function review(record: GreedyPublishItem, action: 'approve' | 'reject', reason?: string) {
  if (record.queue_index === undefined || record.queue_index === null) {
    message.error('缺少 queue_index')
    return
  }
  reviewingIndex.value = record.queue_index
  try {
    const result = await reviewGreedyPublishItem({
      queue_index: record.queue_index,
      action,
      reason,
    })
    if (action === 'approve') {
      const exec = (result as { publish_execution?: { count?: number; task_ids?: string[]; status?: string } })
        .publish_execution
      const n = exec?.count ?? exec?.task_ids?.length
      if (n && n > 0) {
        message.success(`已通过 · 已创建 ${n} 个 PublishTask`)
      } else if (exec?.status === 'failed') {
        message.warning(`已通过审核但发布排队失败：${(exec as { error?: string }).error || '见审核历史'}`)
      } else {
        message.success('已通过并生成发布计划')
      }
    } else {
      message.success('已驳回')
    }
    await load()
  } catch (e: unknown) {
    message.error((e as Error).message || '操作失败')
  } finally {
    reviewingIndex.value = null
  }
}

function openReject(record: GreedyPublishItem) {
  rejectTarget.value = record
  rejectReason.value = ''
  rejectOpen.value = true
}

async function confirmReject() {
  rejectOpen.value = false
  if (rejectTarget.value) {
    await review(rejectTarget.value, 'reject', rejectReason.value || undefined)
    rejectTarget.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.mb-3 {
  margin-bottom: 12px;
}
.ch-tag {
  margin-right: 4px;
  margin-bottom: 2px;
}
</style>
