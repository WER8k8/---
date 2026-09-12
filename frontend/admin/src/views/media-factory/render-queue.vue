<template>
  <YdPage title="渲染队列" subtitle="多媒体渲染任务管理与调度" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="refresh">刷新</a-button>
        <a-button type="primary" @click="clearDone">清空已完成</a-button>
      </a-space>
    </template>
  <div class="space-y-6 animate-fade-in">
    <a-card title="队列任务">

      <a-table :columns="qcol" :data-source="queue" size="small" row-key="id">

        <template #bodyCell="{ column, record }">

          <template v-if="column.key === 'progress'">

            <a-progress :percent="record.progress" :size="'small'" :status="record.raw_status === 'failed' ? 'exception' : record.progress === 100 ? 'success' : 'active'" />

          </template>

          <template v-if="column.key === 'priority'">

            <a-tag :color="record.priority === '高' ? 'red' : record.priority === '中' ? 'orange' : 'blue'">{{ record.priority }}</a-tag>

          </template>

          <template v-if="column.key === 'status'">

            <a-tag :color="statusColor(record.raw_status || record.status)">{{ record.status }}</a-tag>

          </template>

          <template v-if="column.key === 'retention'">

            <span v-if="record.file_purged" class="text-gray-400">已过期</span>

            <span v-else-if="record.seconds_until_purge != null">{{ formatRetention(record) }}</span>

            <span v-else class="text-gray-400">-</span>

          </template>

          <template v-if="column.key === 'result'">

            <a v-if="record.result_url" :href="record.result_url" target="_blank" rel="noopener">预览</a>

            <span v-else class="text-gray-400">-</span>

          </template>

          <template v-if="column.key === 'action'">

            <a-space :size="4">

              <a-button v-if="record.raw_status === 'queued' || record.raw_status === 'failed'" size="small" type="link" @click="runTask(record)">执行</a-button>

              <a-button v-if="record.status === '排队中'" size="small" type="link" @click="pause(record)">暂停</a-button>

              <a-button v-if="record.status === '已暂停'" size="small" type="link" @click="resume(record)">继续</a-button>

              <a-button v-if="record.result_url && !record.file_purged" size="small" type="link" @click="markDownloaded(record)">已下载</a-button>

              <a-popconfirm title="确定取消该任务？" @confirm="cancelTask(record)">

                <a-button size="small" type="link" danger :disabled="record.status === '已完成'">取消</a-button>

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

import { ref, onMounted } from 'vue'

import { message } from 'ant-design-vue'

import { YdPage } from '@/components/youding'

import { getAuthToken } from '@/utils/api'



const qcol = [

  { title: '任务ID', dataIndex: 'id', width: 120, ellipsis: true },

  { title: '任务名', dataIndex: 'name', ellipsis: true },

  { title: '类型', dataIndex: 'type', width: 70 },

  { title: '进度', key: 'progress', width: 160 },

  { title: '优先级', key: 'priority', width: 70 },

  { title: '预估剩余', dataIndex: 'eta', width: 90 },

  { title: '状态', key: 'status', width: 80 },

  { title: '保留', key: 'retention', width: 100 },

  { title: '成品', key: 'result', width: 70 },

  { title: '操作', key: 'action', width: 160 },

]



const queue = ref<any[]>([])



function headers() {

  return { Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' }

}



async function fetchQueue() {

  try {

    const res = await fetch('/api/v1/media-factory/render-queue', { headers: headers() })

    const body = await res.json()

    const data = body.data || body

    const list = data.list || data.items || []

    if (Array.isArray(list)) queue.value = list

  } catch {

    queue.value = []

  }

}



onMounted(() => { fetchQueue() })



function statusColor(s: string) {

  if (s === 'done' || s === '已完成') return 'success'

  if (s === 'rendering' || s === '处理中') return 'processing'

  if (s === 'queued' || s === '排队中') return 'warning'

  if (s === 'failed' || s === '失败') return 'error'

  return 'default'

}



function formatRetention(r: any) {

  const sec = r.seconds_until_purge

  if (sec <= 0) return '即将删除'

  const h = Math.floor(sec / 3600)

  const m = Math.floor((sec % 3600) / 60)

  return h > 0 ? `${h}h${m}m` : `${m}m`

}



async function markDownloaded(r: any) {

  try {

    const res = await fetch(`/api/v1/media-factory/tasks/${r.id}/handoff`, {

      method: 'POST',

      headers: headers(),

      body: JSON.stringify({ action: 'downloaded' }),

    })

    const body = await res.json()

    if (body.code && body.code !== 0) throw new Error(body.message)

    message.success('已登记下载，成品将加速删除')

    await fetchQueue()

  } catch (err: any) {

    message.error(err.message || '登记失败')

  }

}



async function runTask(r: any) {

  try {

    const res = await fetch(`/api/v1/media-factory/tasks/${r.id}/run`, { method: 'POST', headers: headers() })

    const body = await res.json()

    if (body.code && body.code !== 0) throw new Error(body.message)

    message.success(`任务 ${r.id.slice(0, 8)}… 已开始渲染`)

    await fetchQueue()

  } catch (err: any) {

    message.error(err.message || '启动失败')

  }

}



async function pause(r: any) {

  try {

    const res = await fetch(`/api/v1/media-factory/render-queue/${r.id}/pause`, { method: 'POST', headers: headers() })

    const body = await res.json()

    if (body.code && body.code !== 0) throw new Error(body.message)

    await fetchQueue()

    message.warning(`任务 ${r.id.slice(0, 8)}… 已暂停`)

  } catch (err: any) {

    message.error(err.message || '暂停失败')

  }

}



async function resume(r: any) {

  try {

    const res = await fetch(`/api/v1/media-factory/render-queue/${r.id}/resume`, { method: 'POST', headers: headers() })

    const body = await res.json()

    if (body.code && body.code !== 0) throw new Error(body.message)

    await fetchQueue()

    message.success(`任务 ${r.id.slice(0, 8)}… 已恢复`)

  } catch (err: any) {

    message.error(err.message || '恢复失败')

  }

}



async function cancelTask(r: any) {

  if (r.status === '已完成') return

  try {

    const res = await fetch(`/api/v1/media-factory/render-queue/${r.id}`, { method: 'DELETE', headers: headers() })

    const body = await res.json()

    if (body.code && body.code !== 0) throw new Error(body.message)

    queue.value = queue.value.filter(q => q.id !== r.id)

    message.success(`任务 ${r.id.slice(0, 8)}… 已取消`)

  } catch (err: any) {

    message.error(err.message || '取消失败')

  }

}



async function clearDone() {

  try {

    const res = await fetch('/api/v1/media-factory/render-queue/clear-done', { method: 'POST', headers: headers() })

    const body = await res.json()

    const count = body.data?.cleared ?? 0

    await fetchQueue()

    if (count > 0) message.success(`已清空 ${count} 个已完成任务`)

    else message.warning('没有已完成的任务')

  } catch {

    queue.value = queue.value.filter(q => q.status !== '已完成')

    message.success('队列已更新')

  }

}



async function refresh() {

  await fetchQueue()

  message.success('队列已刷新')

}

</script>


