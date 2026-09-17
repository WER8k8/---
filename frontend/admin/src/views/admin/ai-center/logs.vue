/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="AI 调用日志" subtitle="按场景、模型查看真实调用记录（来自 AIUsageLog）。" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="loadLogs">刷新</a-button>
        <router-link to="/admin/ai-center/scenario-models">
          <a-button type="primary">场景模型切换</a-button>
        </router-link>
      </a-space>
    </template>
  <div class="page space-y-4">

    <a-card size="small">
      <a-space wrap style="margin-bottom: 12px">
        <a-select
          v-model:value="taskFilter"
          allow-clear
          placeholder="按场景筛选"
          style="width: 200px"
          @change="loadLogs"
        >
          <a-select-option value="article">article</a-select-option>
          <a-select-option value="inference">inference</a-select-option>
          <a-select-option value="article_to_video_script">article_to_video_script</a-select-option>
          <a-select-option value="optimize:seo">optimize:seo</a-select-option>
        </a-select>
      </a-space>

      <a-table
        :columns="cols"
        :data-source="logs"
        row-key="id"
        size="small"
        :loading="loading"
        :pagination="{ pageSize: 20 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'success'">
            <a-tag :color="record.success ? 'success' : 'error'">
              {{ record.success ? '成功' : '失败' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ formatTime(record.created_at) }}
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet } from '@/utils/api'

interface UsageLogRow {
  id: string
  task_type: string
  model_name: string
  provider_name?: string
  total_tokens: number
  duration_ms: number
  success: boolean
  error_message?: string
  created_at?: string
}

const loading = ref(false)
const taskFilter = ref<string | undefined>()
const logs = ref<UsageLogRow[]>([])

const cols = [
  { title: '时间', key: 'created_at', width: 170 },
  { title: '场景', dataIndex: 'task_type', key: 'task_type', width: 160 },
  { title: '模型', dataIndex: 'model_name', key: 'model_name' },
  { title: '提供商', dataIndex: 'provider_name', key: 'provider_name', width: 120 },
  { title: 'Tokens', dataIndex: 'total_tokens', key: 'total_tokens', width: 90 },
  { title: '耗时(ms)', dataIndex: 'duration_ms', key: 'duration_ms', width: 90 },
  { title: '结果', key: 'success', width: 80 },
]

function formatTime(iso?: string) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString('zh-CN')
  } catch {
    return iso
  }
}

async function loadLogs() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (taskFilter.value) params.task_type = taskFilter.value
    const q = new URLSearchParams(params).toString()
    const data = await apiGet<{ items: UsageLogRow[] }>(`/ai-usage/logs${q ? `?${q}` : ''}`)
    logs.value = data?.items || []
  } catch {
    message.error('加载调用日志失败')
    logs.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadLogs)
</script>
