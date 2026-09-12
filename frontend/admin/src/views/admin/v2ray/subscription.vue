<template>
  <YdPage title="订阅管理" subtitle="订阅链接导入 · 自动更新 · 节点提取" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showAdd=true">+ 添加订阅</a-button>
    </template>
    <div class="space-y-6">
      <div class="grid grid-cols-3 gap-4">
        <a-card size="small"><a-statistic title="订阅数" :value="subs.length" :value-style="{ color: 'var(--uj-brand, #4a9b8c)' }"/></a-card>
        <a-card size="small"><a-statistic title="可用节点" :value="totalNodes" :value-style="{ color: '#22c55e' }"/></a-card>
        <a-card size="small"><a-statistic title="最后更新" :value="lastUpdate" :value-style="{ color: '#8b5cf6' }"/></a-card>
      </div>
      <a-card title="订阅列表" size="small"><a-table :columns="c" :dataSource="subs" rowKey="id" size="small">
        <template #bodyCell="{column,record}">
          <template v-if="column.key==='s'"><a-tag :color="record.s==='active'?'green':'red'">{{ record.s==='active'?'有效':'失效' }}</a-tag></template>
          <template v-if="column.key==='a'"><a-space><a-button size="small" @click="updateSub(record)" :loading="record._loading">更新</a-button><a-button size="small" @click="copyUrl(record)">复制</a-button><a-button size="small" danger @click="delSub(record)">删除</a-button></a-space></template>
        </template>
      </a-table></a-card>
      <a-modal v-model:open="showAdd" title="添加订阅" @ok="addSub">
        <a-form layout="vertical">
          <a-form-item label="订阅名称"><a-input v-model:value="f.name" placeholder="如: 机场A-套餐1"/></a-form-item>
          <a-form-item label="订阅链接"><a-textarea v-model:value="f.url" :rows="3" placeholder="vmess://... 或 https://sub.example.com"/></a-form-item>
          <a-form-item label="自动更新"><a-switch v-model:checked="f.autoUpdate"/> 每6小时更新</a-form-item>
        </a-form>
      </a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { v2rayAPI } from '@/api'

interface SubscriptionItem {
  id: number
  name: string
  url: string
  nodes: number
  s: string
  updated: string
  _loading?: boolean
}

const showAdd = ref(false)
const loading = ref(false)
const f = reactive({ name: '', url: '', autoUpdate: true })

const subs = ref<SubscriptionItem[]>([])

const totalNodes = computed(() =>
  subs.value.filter((s) => s.s === 'active').reduce((a, s) => a + s.nodes, 0)
)
const lastUpdate = computed(() => subs.value[0]?.updated || '—')

const c = [
  { title: '名称', dataIndex: 'name' },
  { title: '订阅链接', dataIndex: 'url' },
  { title: '节点数', dataIndex: 'nodes' },
  { title: '状态', dataIndex: 's', key: 's' },
  { title: '更新时间', dataIndex: 'updated' },
  { title: '操作', key: 'a' },
]

function fmtNow(): string {
  return new Date().toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function fetchSubscriptions() {
  loading.value = true
  try {
    const res = await v2rayAPI.listSubscriptions()
    subs.value = (res as any)?.data?.subscriptions || (res as any)?.subscriptions || []
  } catch {
    if (import.meta.env.DEV) console.warn('[V2Ray] 加载订阅列表失败，使用空列表')
    subs.value = []
  } finally {
    loading.value = false
  }
}

async function addSub() {
  if (!f.url.trim()) {
    message.warning('请填写订阅链接')
    return
  }
  try {
    const res = await v2rayAPI.createSubscription({ name: f.name || '新订阅', url: f.url })
    const newSub: SubscriptionItem = {
      id: Date.now(),
      name: f.name || '新订阅',
      url: f.url,
      nodes: 0,
      s: 'active',
      updated: fmtNow(),
    }
    if ((res as any)?.data) {
      Object.assign(newSub, (res as any).data)
    }
    subs.value.unshift(newSub)
    showAdd.value = false
    f.name = ''
    f.url = ''
    message.success('订阅已添加')
  } catch (e: any) {
    message.error(e?.message || '添加失败')
  }
}

async function updateSub(r: any) {
  r._loading = true
  try {
    const res = await v2rayAPI.updateSubscription(r.id)
    if ((res as any)?.data) {
      r.nodes = (res as any).data.nodes ?? r.nodes
    } else {
      r.nodes = Number((res as any)?.data?.nodes ?? r.nodes ?? 0)
    }
    r.updated = fmtNow()
    r.s = 'active'
    message.success(`已更新，获取 ${r.nodes} 个节点`)
  } catch (e: any) {
    message.error(e?.message || '更新失败')
  } finally {
    r._loading = false
  }
}

async function delSub(r: any) {
  try {
    await v2rayAPI.deleteSubscription(r.id)
    subs.value = subs.value.filter((x) => x.id !== r.id)
  } catch {
    subs.value = subs.value.filter((x) => x.id !== r.id)
  }
}

function copyUrl(r: any) {
  navigator.clipboard.writeText(r.url)
  message.success('已复制到剪贴板')
}

onMounted(() => {
  fetchSubscriptions()
})
</script>
