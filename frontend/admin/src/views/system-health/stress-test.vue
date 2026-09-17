/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="压测管理" subtitle="性能压力测试与结果分析" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showCreateModal = true"><ThunderboltOutlined class="mr-1" />新建压测</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">

    <a-card title="执行中任务">
      <a-empty v-if="!runningTests.length" description="暂无运行中的压测任务" />
      <div v-else class="space-y-3">
        <a-card v-for="t in runningTests" :key="t.id" size="small" hoverable>
          <div class="flex items-center justify-between">
            <div><span class="font-medium">{{ t.name }}</span><a-tag class="ml-2" color="processing">{{ t.status }}</a-tag></div>
            <a-button size="small" danger @click="stopTest(t.id)">停止</a-button>
          </div>
          <a-progress :percent="t.progress" size="small" class="mt-2" />
        </a-card>
      </div>
    </a-card>

    <a-card title="测试配置">
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="8"><a-form-item label="目标URL"><a-input v-model:value="form.url" placeholder="https://youding.com/api/" /></a-form-item></a-col>
          <a-col :span="4"><a-form-item label="并发数"><a-input-number v-model:value="form.concurrency" :min="1" :max="1000" class="w-full" /></a-form-item></a-col>
          <a-col :span="4"><a-form-item label="持续时间(秒)"><a-input-number v-model:value="form.duration" :min="10" :max="3600" class="w-full" /></a-form-item></a-col>
          <a-col :span="4"><a-form-item label="预热时间(秒)"><a-input-number v-model:value="form.warmup" :min="0" :max="60" class="w-full" /></a-form-item></a-col>
          <a-col :span="4"><a-form-item label="请求方法"><a-select v-model:value="form.method"><a-select-option value="GET">GET</a-select-option><a-select-option value="POST">POST</a-select-option></a-select></a-form-item></a-col>
        </a-row>
      </a-form>
    </a-card>

    <a-card title="历史记录">
      <a-table :columns="histColumns" :data-source="history" :pagination="{ pageSize: 5 }" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'completed' ? 'success' : record.status === 'failed' ? 'error' : 'processing'">{{ record.status === 'completed' ? '完成' : record.status === 'failed' ? '失败' : '运行中' }}</a-tag>
          </template>
          <template v-if="column.key === 'result'">
            <span v-if="record.result">QPS: {{ record.result.qps }} | P99: {{ record.result.p99 }}ms | 成功率: {{ record.result.successRate }}%</span>
            <span v-else class="text-gray-400">-</span>
          </template>
          <template v-if="column.key === 'action'">
            <a-button size="small" type="link" @click="viewDetail(record)">详情</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="showDetailModal" title="压测详情" :footer="null">
      <a-descriptions v-if="detailRecord" bordered size="small" :column="1">
        <a-descriptions-item label="任务">{{ detailRecord.name }}</a-descriptions-item>
        <a-descriptions-item label="目标">{{ detailRecord.url }}</a-descriptions-item>
        <a-descriptions-item label="并发">{{ detailRecord.concurrency }}</a-descriptions-item>
        <a-descriptions-item label="状态">{{ detailRecord.status }}</a-descriptions-item>
        <a-descriptions-item v-if="detailRecord.result" label="QPS">{{ detailRecord.result.qps }}</a-descriptions-item>
        <a-descriptions-item v-if="detailRecord.result" label="P99">{{ detailRecord.result.p99 }}ms</a-descriptions-item>
        <a-descriptions-item v-if="detailRecord.result" label="成功率">{{ detailRecord.result.successRate }}%</a-descriptions-item>
        <a-descriptions-item label="时间">{{ detailRecord.time }}</a-descriptions-item>
      </a-descriptions>
    </a-modal>

    <a-modal v-model:open="showCreateModal" title="新建压测任务" @ok="createTest" ok-text="启动压测">
      <a-descriptions bordered size="small" :column="2">
        <a-descriptions-item label="目标URL">{{ form.url }}</a-descriptions-item>
        <a-descriptions-item label="请求方法">{{ form.method }}</a-descriptions-item>
        <a-descriptions-item label="并发数">{{ form.concurrency }}</a-descriptions-item>
        <a-descriptions-item label="持续时间">{{ form.duration }}秒</a-descriptions-item>
        <a-descriptions-item label="预热时间">{{ form.warmup }}秒</a-descriptions-item>
        <a-descriptions-item label="预计QPS">{{ Math.round(form.concurrency * 0.8) }}</a-descriptions-item>
      </a-descriptions>
    </a-modal>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Card, Button, Form, FormItem, Input, InputNumber, Select, SelectOption, Table, Progress, Tag, Row, Col, Modal, Descriptions, DescriptionsItem, Empty, message } from 'ant-design-vue'
import { ThunderboltOutlined } from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import { apiGet, apiPost, getAuthToken } from '@/utils/api'

const showCreateModal = ref(false)
const showDetailModal = ref(false)
const detailRecord = ref<any>(null)

const form = reactive({
  url: 'https://youding.com/api/v1/products',
  concurrency: 50,
  duration: 60,
  warmup: 5,
  method: 'GET',
})

const runningTests = ref<any[]>([])
const history = ref<any[]>([])

const histColumns = [
  { title: '任务名称', dataIndex: 'name', key: 'name' },
  { title: '目标', dataIndex: 'url', key: 'url', ellipsis: true },
  { title: '并发', dataIndex: 'concurrency', key: 'concurrency', width: 70 },
  { title: '状态', key: 'status', width: 80 },
  { title: '结果摘要', key: 'result', width: 280 },
  { title: '时间', dataIndex: 'time', key: 'time', width: 160 },
  { title: '操作', key: 'action', width: 70 },
]

async function loadHistory() {
  try {
    const d = await apiGet<{ test_history?: any[] }>('/system-health/stress-test')
    history.value = (d as any)?.test_history ?? (Array.isArray(d) ? d : [])
  } catch {
    message.warning('数据加载失败，请稍后重试')
    history.value = []
  }
}

async function createTest() {
  try {
    await apiPost('/system-health/stress-test', {
      url: form.url,
      concurrency: form.concurrency,
      duration: form.duration,
      warmup: form.warmup,
      method: form.method,
    })
    showCreateModal.value = false
    message.success('压测任务已提交')
    await loadHistory()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '启动压测失败')
  }
}

function stopTest(id: number) {
  runningTests.value = runningTests.value.filter(x => x.id !== id)
  message.success('已停止压测')
}

function viewDetail(r: any) { detailRecord.value = r; showDetailModal.value = true }

onMounted(() => { void loadHistory() })
onUnmounted(() => { runningTests.value.forEach(t => { if (t.timer) clearInterval(t.timer) }) })
</script>
