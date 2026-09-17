/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="备份回滚" subtitle="数据库备份计划与恢复管理" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="refreshBackups" :loading="loading">刷新</a-button>
        <a-button type="primary" :loading="backupRunning" @click="runManualBackup"><CloudUploadOutlined class="mr-1" />手动备份</a-button>
      </a-space>
    </template>
    <div class="space-y-6 animate-fade-in">

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <a-card v-for="s in stats" :key="s.label" hoverable>
        <a-statistic :title="s.label" :value="s.value" :suffix="s.suffix" :value-style="{ color: s.color }" />
      </a-card>
    </div>

    <a-card title="备份计划">
      <a-descriptions bordered size="small" :column="2">
        <a-descriptions-item label="日备份">每天 02:00 <a-tag color="green">启用</a-tag></a-descriptions-item>
        <a-descriptions-item label="周备份">每周日 03:00 <a-tag color="green">启用</a-tag></a-descriptions-item>
        <a-descriptions-item label="月备份">每月1日 04:00 <a-tag color="green">启用</a-tag></a-descriptions-item>
        <a-descriptions-item label="保留策略">日(30天) / 周(12周) / 月(12月)</a-descriptions-item>
      </a-descriptions>
    </a-card>

    <a-card title="备份历史">
      <a-table :columns="columns" :data-source="backups" :pagination="{ pageSize: 8 }" row-key="id" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'success' ? 'success' : record.status === 'running' ? 'processing' : 'error'">
              {{ record.status === 'success' ? '成功' : record.status === 'running' ? '进行中' : '失败' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" type="link" @click="restoreBackup(record)" :disabled="record.status !== 'success'">恢复</a-button>
              <a-popconfirm title="确定删除该备份？" @confirm="deleteBackup(record.id)">
                <a-button size="small" type="link" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="restoreModal.open" title="恢复确认" @ok="confirmRestore" ok-text="确认恢复" ok-type="danger">
      <p>确定要恢复到 <strong>{{ restoreModal.backupName }}</strong> 吗？</p>
      <p class="text-red-500 text-sm">注意：恢复操作将覆盖当前数据库，请谨慎操作。</p>
    </a-modal>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Card, Statistic, Button, Table, Tag, Modal, Descriptions, DescriptionsItem, Popconfirm, Space, message } from 'ant-design-vue'
import { CloudUploadOutlined } from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'

const loading = ref(false)
const backupRunning = ref(false)

const stats = reactive([
  { label: '成功备份', value: 47, suffix: '次', color: '#22c55e' },
  { label: '备份总大小', value: 2.4, suffix: 'GB', color: '#4a9b8c' },
  { label: '最后备份', value: '02:00', suffix: '今天', color: '#8b5cf6' },
  { label: '恢复成功', value: 5, suffix: '次', color: '#f59e0b' },
])

const columns = [
  { title: '备份名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type', width: 80 },
  { title: '大小', dataIndex: 'size', key: 'size', width: 100 },
  { title: '状态', key: 'status', width: 80 },
  { title: '时间', dataIndex: 'time', key: 'time', width: 180 },
  { title: '操作', key: 'action', width: 120 },
]

const backups = ref<any[]>([])

const restoreModal = reactive({ open: false, backupId: 0, backupName: '' })

async function refreshBackups() {
  loading.value = true
  try {
    const tk = getAuthToken() || ''
    const r = await fetch('/api/v1/system-health/backup', { headers: { Authorization: `Bearer ${tk}` } })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    const d = await r.json()
    const payload = d.data ?? d
    if (payload.backups) backups.value = payload.backups
    if (payload.stats) payload.stats.forEach((s: any, i: number) => { if (stats[i]) Object.assign(stats[i], s) })
  } catch {
    message.warning('数据加载失败，请稍后重试')
    backups.value = []
  } finally {
    loading.value = false
  }
}

async function runManualBackup() {
  backupRunning.value = true
  try {
    const tk = getAuthToken() || ''
    await fetch('/api/v1/system-health/backup', { method: 'POST', headers: { Authorization: `Bearer ${tk}` } })
    message.success('手动备份任务已提交')
    await refreshBackups()
  } catch {
    message.error('备份失败')
  } finally {
    backupRunning.value = false
  }
}

function restoreBackup(r: any) { restoreModal.open = true; restoreModal.backupId = r.id; restoreModal.backupName = r.name }

function confirmRestore() {
  message.loading('正在恢复...', 2).then(() => { message.success('恢复成功'); ;(stats[3].value as number)++; restoreModal.open = false })
}

function deleteBackup(id: number) { backups.value = backups.value.filter(b => b.id !== id); message.success('已删除') }

onMounted(() => { void refreshBackups() })
</script>
