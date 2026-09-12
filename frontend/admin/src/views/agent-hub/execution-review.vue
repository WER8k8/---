<template>
  <YdPage title="执行复盘" subtitle="任务执行记录与对比分析" surface="elevated">
    <template #actions>
      <a-space>
        <a-input-search v-model:value="searchKey" placeholder="搜索任务..." class="w-56" />
        <a-button @click="refresh">刷新</a-button>
      </a-space>
    </template>
    <div class="space-y-6">
    <div class="grid grid-cols-4 gap-4">
      <a-card v-for="s in summary" :key="s.label" hoverable><a-statistic :title="s.label" :value="s.value" :suffix="s.suffix" :value-style="{ color: s.color }" /></a-card>
    </div>
    <a-card>
      <div ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar
            :loading="listLoading"
            :target-ref="tablePanelRef"
            :show-export="false"
            @refresh="refresh"
          />
        </div>
        <YdDataTable
          :columns="columns"
          :data-source="filteredRecords"
          :loading="listLoading"
          :pagination="{ current: 1, pageSize: 8, total: filteredRecords.length }"
          :table-props="{ size: tableSize, rowKey: 'id' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="record.status==='success'?'success':record.status==='failed'?'error':'processing'">{{ record.status==='success'?'成功':record.status==='failed'?'失败':'进行中' }}</a-tag>
            </template>
            <template v-if="column.key === 'action'">
              <a-button size="small" type="link" @click="showDetail(record)">详情</a-button>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>
    <a-modal v-model:open="detailModal.open" title="任务详情" :footer="null" width="650">
      <a-descriptions bordered size="small" :column="2">
        <a-descriptions-item label="任务名称">{{ detailModal.record?.name }}</a-descriptions-item>
        <a-descriptions-item label="Agent链路">{{ detailModal.record?.agents }}</a-descriptions-item>
        <a-descriptions-item label="总耗时">{{ detailModal.record?.duration }}</a-descriptions-item>
        <a-descriptions-item label="Token消耗">{{ detailModal.record?.tokens }}</a-descriptions-item>
        <a-descriptions-item label="输入长度">{{ detailModal.record?.inputLen }}</a-descriptions-item>
        <a-descriptions-item label="输出长度">{{ detailModal.record?.outputLen }}</a-descriptions-item>
        <a-descriptions-item label="状态"><a-tag :color="detailModal.record?.status==='success'?'success':'error'">{{ detailModal.record?.status==='success'?'成功':'失败' }}</a-tag></a-descriptions-item>
        <a-descriptions-item label="时间">{{ detailModal.record?.time }}</a-descriptions-item>
      </a-descriptions>
      <div class="mt-4 bg-gray-50 p-3 rounded-lg text-xs font-mono text-gray-600 max-h-40 overflow-y-auto">
        <div v-for="(s, i) in detailSteps" :key="i" class="step-line">
          <CaretRightOutlined class="step-arrow" />
          <span :class="'step-tone-' + s.tone">{{ s.text }}</span>
        </div>
      </div>
    </a-modal>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { Card, Statistic, Tag, Button, Modal, Descriptions, DescriptionsItem, InputSearch, Space, message } from 'ant-design-vue'
import { CaretRightOutlined } from '@ant-design/icons-vue'
import { apiGet } from '@/utils/api'

const searchKey = ref('')
const tablePanelRef = ref<HTMLElement | null>(null)
const listLoading = ref(false)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const summary = ref<{ label: string; value: number | string; suffix: string; color: string }[]>([])

const columns = [
  { title: '任务名称', dataIndex: 'name', key: 'name' }, { title: 'Agent链路', dataIndex: 'agents', key: 'agents', width: 180 },
  { title: '耗时', dataIndex: 'duration', key: 'duration', width: 80 }, { title: 'Token', dataIndex: 'tokens', key: 'tokens', width: 80 },
  { title: '状态', key: 'status', width: 80 }, { title: '时间', dataIndex: 'time', key: 'time', width: 170 },
  { title: '操作', key: 'action', width: 60 },
]

const records = ref<any[]>([])

const filteredRecords = computed(() => records.value.filter(r => r.name.includes(searchKey.value)))

const detailModal = reactive({ open: false, record: null as any })
const detailSteps = ref<{ text: string; tone: string }[]>([])

function stepTone(status?: string) {
  if (status === 'success' || status === 'done') return 'success'
  if (status === 'failed') return 'error'
  if (status === 'running') return 'info'
  return 'accent'
}

function showDetail(r: any) {
  detailModal.record = r
  const steps = Array.isArray(r?.steps) ? r.steps : []
  detailSteps.value = steps.length
    ? steps.map((s: { title?: string; status?: string }) => ({
        text: s.title || '步骤',
        tone: stepTone(s.status),
      }))
    : [{ text: '暂无步骤日志', tone: 'info' }]
  detailModal.open = true
}

async function loadReviews() {
  listLoading.value = true
  try {
    const d = await apiGet('/agent-hub/execution-review')
    if (d && d.items && d.items.length) {
      records.value = d.items.map((item: any, i: number) => ({
        id: item.id || (i + 1), name: item.name || `任务${i+1}`,
        agents: item.agents || '', duration: item.duration || '0s',
        tokens: item.tokens || '0', status: item.status || 'success',
        time: item.time || '', inputLen: item.input_len || '-',
        outputLen: item.output_len || '-',
        steps: item.steps || [],
      }))
      if (d.summary) {
        summary.value = [
          { label: '总任务数', value: d.summary.total ?? d.total ?? 0, suffix: '次', color: '#4a9b8c' },
          { label: '成功率', value: d.summary.success_rate ?? 0, suffix: '%', color: '#22c55e' },
          { label: '平均耗时', value: d.summary.avg_duration_sec ?? 0, suffix: '秒', color: '#8b5cf6' },
          { label: '失败数', value: d.summary.failed_count ?? 0, suffix: '次', color: '#f59e0b' },
        ]
      } else if (d.total != null) {
        const successCount = records.value.filter(r => r.status === 'success').length
        const total = d.total
        summary.value = [
          { label: '总任务数', value: total, suffix: '次', color: '#4a9b8c' },
          { label: '成功率', value: total ? +((successCount / total) * 100).toFixed(1) : 0, suffix: '%', color: '#22c55e' },
          { label: '平均耗时', value: 0, suffix: '秒', color: '#8b5cf6' },
          { label: '失败数', value: records.value.filter(r => r.status === 'failed').length, suffix: '次', color: '#f59e0b' },
        ]
      }
    }
  } catch {
    records.value = []
    summary.value = []
    message.warning('执行记录加载失败，请稍后重试')
  }
  finally {
    listLoading.value = false
  }
}

async function refresh() {
  await loadReviews()
  message.success('已刷新')
}

onMounted(loadReviews)
</script>
