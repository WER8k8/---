/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="V2RayN 服务器配置" subtitle="V2Ray / Xray 服务器节点管理 · 已接后端 CRUD" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="openCreate">+ 添加节点</a-button>
    </template>
    <div class="space-y-6">
      <a-alert
        v-if="speedNote"
        type="info"
        show-icon
        message="测速未配置"
        :description="speedNote"
        closable
        style="margin-bottom: 12px"
        @close="speedNote = ''"
      />
      <div class="grid grid-cols-4 gap-4">
        <a-card size="small"><a-statistic title="总节点" :value="servers.length" :value-style="{ color: 'var(--uj-brand, #4a9b8c)' }"/></a-card>
        <a-card size="small"><a-statistic title="已登记备注" :value="servers.filter((s:any)=>s.remarks).length" :value-style="{ color: '#10b981' }"/></a-card>
        <a-card size="small"><a-statistic title="延迟" value="未探测" :value-style="{ color: '#8b5cf6' }"/></a-card>
        <a-card size="small"><a-statistic title="流量" value="未采集" :value-style="{ color: '#f59e0b' }"/></a-card>
      </div>
      <a-card title="节点列表" size="small">
        <a-table :columns="cols" :dataSource="servers" rowKey="id" size="small" :loading="loading">
          <template #bodyCell="{column,record}">
            <template v-if="column.key==='status'">
              <a-tag color="default">{{ record.status || 'unknown' }}</a-tag>
            </template>
            <template v-if="column.key==='protocol'"><a-tag>{{ record.protocol }}</a-tag></template>
            <template v-if="column.key==='latency'">{{ record.latency == null ? '—' : record.latency + 'ms' }}</template>
            <template v-if="column.key==='actions'">
              <a-space>
                <a-button size="small" :loading="speedingId===record.id" @click="speedTest(record)">测试</a-button>
                <a-button size="small" @click="openEdit(record)">编辑</a-button>
                <a-popconfirm title="确认删除该节点？" @confirm="remove(String(record.id))">
                  <a-button size="small" danger :loading="deletingId===record.id">删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-modal v-model:open="showModal" :title="editing ? '编辑节点' : '添加节点'" :footer="null">
        <a-form layout="vertical">
          <a-form-item label="名称" required>
            <a-input v-model:value="form.name" placeholder="节点名称" allow-clear />
          </a-form-item>
          <a-form-item label="地址" required>
            <a-input v-model:value="form.address" placeholder="host 或 IP" allow-clear />
          </a-form-item>
          <a-form-item label="端口">
            <a-input-number v-model:value="form.port" :min="1" :max="65535" style="width: 100%" placeholder="可选" />
          </a-form-item>
          <a-form-item label="协议">
            <a-input v-model:value="form.protocol" placeholder="vmess / vless / trojan" allow-clear />
          </a-form-item>
          <a-form-item label="UUID">
            <a-input v-model:value="form.uuid" allow-clear />
          </a-form-item>
          <a-form-item label="备注">
            <a-textarea v-model:value="form.remarks" :rows="2" />
          </a-form-item>
          <div class="flex justify-end gap-2">
            <a-button @click="showModal=false">取消</a-button>
            <a-button type="primary" :loading="saving" @click="save">{{ editing ? '保存' : '添加' }}</a-button>
          </div>
        </a-form>
      </a-modal>
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api'

const servers = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const deletingId = ref<string | null>(null)
const speedingId = ref<string | null>(null)
const speedNote = ref('')
const showModal = ref(false)
const editing = ref<any | null>(null)

const form = reactive({
  name: '',
  address: '',
  port: undefined as number | undefined,
  protocol: 'vmess',
  uuid: '',
  remarks: '',
})

async function loadServers() {
  loading.value = true
  try {
    const d = await apiGet('/super-admin/v2ray/servers') as any
    const items = d?.items ?? d?.data?.items
    servers.value = Array.isArray(items) ? items : []
  } catch (e: any) {
    servers.value = []
    message.error(e?.message || '节点列表加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.name = ''
  form.address = ''
  form.port = undefined
  form.protocol = 'vmess'
  form.uuid = ''
  form.remarks = ''
  showModal.value = true
}

function openEdit(row: any) {
  editing.value = row
  form.name = String(row.name ?? '')
  form.address = String(row.address ?? '')
  form.port = row.port ?? undefined
  form.protocol = String(row.protocol ?? 'vmess')
  form.uuid = String(row.uuid ?? '')
  form.remarks = String(row.remarks ?? '')
  showModal.value = true
}

async function save() {
  if (!form.name.trim() || !form.address.trim()) {
    message.warning('请填写名称与地址')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      address: form.address.trim(),
      port: form.port ?? null,
      protocol: form.protocol.trim() || 'vmess',
      uuid: form.uuid.trim(),
      remarks: form.remarks.trim(),
    }
    if (editing.value?.id) {
      await apiPut(`/super-admin/v2ray/servers/${editing.value.id}`, payload)
      message.success('节点已更新')
    } else {
      await apiPost('/super-admin/v2ray/servers', payload)
      message.success('节点已添加')
    }
    showModal.value = false
    await loadServers()
  } catch (e: any) {
    message.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function remove(id: string) {
  deletingId.value = id
  try {
    await apiDelete(`/super-admin/v2ray/servers/${id}`)
    message.success('已删除')
    await loadServers()
  } catch (e: any) {
    message.error(e?.message || '删除失败')
  } finally {
    deletingId.value = null
  }
}

async function speedTest(row: any) {
  speedingId.value = String(row.id)
  try {
    const d = await apiGet(`/super-admin/v2ray/servers/${row.id}/speed-test`) as any
    speedNote.value = String(d?.reason || d?.data?.reason || '测速探针未配置，不返回编造延迟')
  } catch (e: any) {
    speedNote.value = e?.message || '测速接口不可用'
  } finally {
    speedingId.value = null
  }
}

onMounted(loadServers)
const cols=[
  {title:'名称',dataIndex:'name'},
  {title:'协议',dataIndex:'protocol',key:'protocol'},
  {title:'地址',dataIndex:'address'},
  {title:'端口',dataIndex:'port'},
  {title:'UUID',dataIndex:'uuid',ellipsis:true},
  {title:'状态',dataIndex:'status',key:'status'},
  {title:'延迟',key:'latency'},
  {title:'备注',dataIndex:'remarks',ellipsis:true},
  {title:'操作',key:'actions'},
]
</script>
