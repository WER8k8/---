/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="边缘节点管理" subtitle="全球 CDN 节点配置与监控" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showForm = true">添加节点</a-button>
    </template>
    <div class="space-y-6 animate-fade-in">
    <a-card title="节点列表">
      <a-table :columns="cols" :data-source="nodes" size="small" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
          </template>
          <template v-if="column.key === 'load'">
            <a-progress :percent="record.load" size="small" :stroke-color="record.load > 80 ? '#ef4444' : record.load > 60 ? '#f59e0b' : '#22c55e'" />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" type="link" @click="editNode(record)">编辑</a-button>
              <a-popconfirm title="确定删除该节点？" @confirm="deleteNode(record.id)">
                <a-button size="small" type="link" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
    <a-modal v-model:open="showForm" :title="editingId ? '编辑节点' : '添加节点'" @ok="saveNode" @cancel="resetForm">
      <a-form :model="form" layout="vertical">
        <a-form-item label="节点名称"><a-input v-model:value="form.name" placeholder="如: 华东节点-上海" /></a-form-item>
        <a-form-item label="区域"><a-select v-model:value="form.region">
          <a-select-option value="华东">华东</a-select-option><a-select-option value="华北">华北</a-select-option>
          <a-select-option value="华南">华南</a-select-option><a-select-option value="亚太">亚太</a-select-option>
          <a-select-option value="北美">北美</a-select-option><a-select-option value="欧洲">欧洲</a-select-option>
        </a-select></a-form-item>
        <a-form-item label="IP 地址"><a-input v-model:value="form.ip" placeholder="如: 103.45.12.1" /></a-form-item>
        <a-form-item label="状态"><a-select v-model:value="form.status">
          <a-select-option value="在线">在线</a-select-option><a-select-option value="离线">离线</a-select-option><a-select-option value="维护">维护</a-select-option>
        </a-select></a-form-item>
        <a-form-item label="负载 (%)">
          <a-slider v-model:value="form.load" :min="0" :max="100" /> {{ form.load }}%
        </a-form-item>
      </a-form>
    </a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { YdPage } from '@/components/youding'
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getAuthToken } from '@/utils/api'

const cols = [
  { title: '节点名', dataIndex: 'name' },
  { title: '区域', dataIndex: 'region', width: 80 },
  { title: 'IP', dataIndex: 'ip', width: 140 },
  { title: '状态', key: 'status', width: 70 },
  { title: '负载', key: 'load', width: 160 },
  { title: '带宽', dataIndex: 'bandwidth', width: 90 },
  { title: '操作', key: 'action', width: 130 },
]

const nodes = ref([
  { id: 1, name: '华东节点-上海', region: '华东', ip: '103.45.12.1', status: '在线', load: 42, bandwidth: '120Mbps' },
  { id: 2, name: '华北节点-北京', region: '华北', ip: '203.45.12.2', status: '在线', load: 65, bandwidth: '95Mbps' },
  { id: 3, name: '华南节点-广州', region: '华南', ip: '203.45.12.3', status: '在线', load: 38, bandwidth: '88Mbps' },
  { id: 4, name: '亚太节点-新加坡', region: '亚太', ip: '203.45.12.4', status: '在线', load: 72, bandwidth: '45Mbps' },
  { id: 5, name: '北美节点-洛杉矶', region: '北美', ip: '198.45.12.5', status: '离线', load: 0, bandwidth: '-' },
  { id: 6, name: '欧洲节点-法兰克福', region: '欧洲', ip: '198.45.12.6', status: '维护', load: 0, bandwidth: '-' },
])

const showForm = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ name: '', region: '华东', ip: '', status: '在线', load: 0 })

function statusColor(s: string) { return s === '在线' ? 'success' : s === '维护' ? 'warning' : 'error' }
function editNode(r: any) {
  editingId.value = r.id; Object.assign(form, { name: r.name, region: r.region, ip: r.ip, status: r.status, load: r.load }); showForm.value = true
}
function saveNode() {
  if (!form.name.trim() || !form.ip.trim()) { message.warning('请填写完整信息'); return }
  if (editingId.value) {
    const n = nodes.value.find(n => n.id === editingId.value)
    if (n) { Object.assign(n, { ...form }); message.success('节点已更新') }
  } else {
    nodes.value.push({ id: Date.now(), name: form.name, region: form.region, ip: form.ip, status: form.status, load: form.load, bandwidth: '0Mbps' })
    message.success('节点已添加')
  }
  showForm.value = false; resetForm()
}
function deleteNode(id: number) { nodes.value = nodes.value.filter(n => n.id !== id); message.success('节点已删除') }
function resetForm() { editingId.value = null; Object.assign(form, { name: '', region: '华东', ip: '', status: '在线', load: 0 }) }

onMounted(async () => {
  try {
    const tk = getAuthToken() || ''
    const r = await fetch('/api/v1/edge-cdn/nodes', { headers: { Authorization: `Bearer ${tk}` } })
    if (!r.ok) throw new Error('HTTP ' + r.status)
    const d = await r.json()
    if (Array.isArray(d.data?.items)) nodes.value = d.data.items
  } catch { message.warning('数据加载失败，请稍后重试') }
})
</script>
