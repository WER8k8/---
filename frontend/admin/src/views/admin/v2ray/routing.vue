/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="路由规则" subtitle="代理路由策略 · 分流规则 · 已接后端 CRUD" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="openCreate">+ 添加规则</a-button>
    </template>
    <div class="space-y-6">
      <a-card title="分流规则" size="small">
        <a-table :columns="c" :dataSource="rules" rowKey="id" size="small" :loading="loading">
          <template #bodyCell="{column,record}">
            <template v-if="column.key==='a'">
              <a-tag :color="record.action==='proxy'?'blue':record.action==='direct'?'green':'orange'">
                {{ {proxy:'代理',direct:'直连',block:'阻止'}[record.action as string] || record.action }}
              </a-tag>
            </template>
            <template v-if="column.key==='en'">
              <a-switch :checked="record.enabled" size="small" :loading="togglingId===record.id" @change="(v: any) => toggle(record, Boolean(v))" />
            </template>
            <template v-if="column.key==='ac'">
              <a-space>
                <a-button size="small" @click="openEdit(record)">编辑</a-button>
                <a-popconfirm title="确认删除该规则？" @confirm="remove(String(record.id))">
                  <a-button size="small" danger :loading="deletingId===record.id">删除</a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-modal v-model:open="showModal" :title="editing ? '编辑规则' : '添加规则'" :footer="null">
        <a-form layout="vertical">
          <a-form-item label="类型" required>
            <a-select v-model:value="form.rule" placeholder="匹配类型">
              <a-select-option value="domain">域名</a-select-option>
              <a-select-option value="ip">IP</a-select-option>
              <a-select-option value="geoip">GeoIP</a-select-option>
              <a-select-option value="other">其他</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="匹配值" required>
            <a-input v-model:value="form.value" placeholder="如 example.com / 10.0.0.0/8" allow-clear />
          </a-form-item>
          <a-form-item label="动作">
            <a-radio-group v-model:value="form.action">
              <a-radio value="proxy">代理</a-radio>
              <a-radio value="direct">直连</a-radio>
              <a-radio value="block">阻止</a-radio>
            </a-radio-group>
          </a-form-item>
          <a-form-item label="启用">
            <a-switch v-model:checked="form.enabled" />
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

const rules = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const deletingId = ref<string | null>(null)
const togglingId = ref<string | null>(null)
const showModal = ref(false)
const editing = ref<any | null>(null)

const form = reactive({
  rule: 'domain',
  value: '',
  action: 'proxy' as 'proxy' | 'direct' | 'block',
  enabled: true,
})

const c = [
  { title: '类型', dataIndex: 'rule' },
  { title: '匹配值', dataIndex: 'value' },
  { title: '动作', key: 'a' },
  { title: '启用', key: 'en' },
  { title: '操作', key: 'ac' },
]

async function load() {
  loading.value = true
  try {
    const d = await apiGet('/super-admin/v2ray/routing') as any
    const items = d?.items ?? d?.data?.items
    rules.value = Array.isArray(items) ? items : []
  } catch (e: any) {
    rules.value = []
    message.error(e?.message || '路由规则加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  form.rule = 'domain'
  form.value = ''
  form.action = 'proxy'
  form.enabled = true
  showModal.value = true
}

function openEdit(row: any) {
  editing.value = row
  form.rule = String(row.rule ?? 'domain')
  form.value = String(row.value ?? '')
  form.action = (row.action as any) || 'proxy'
  form.enabled = row.enabled !== false
  showModal.value = true
}

async function save() {
  if (!form.rule || !form.value.trim()) {
    message.warning('请填写类型与匹配值')
    return
  }
  saving.value = true
  try {
    const payload = {
      rule: form.rule,
      value: form.value.trim(),
      action: form.action,
      enabled: form.enabled,
    }
    if (editing.value?.id) {
      await apiPut(`/super-admin/v2ray/routing/${editing.value.id}`, payload)
      message.success('规则已更新')
    } else {
      await apiPost('/super-admin/v2ray/routing', payload)
      message.success('规则已添加')
    }
    showModal.value = false
    await load()
  } catch (e: any) {
    message.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function toggle(row: any, enabled: boolean) {
  togglingId.value = String(row.id)
  try {
    await apiPut(`/super-admin/v2ray/routing/${row.id}`, { enabled })
    await load()
  } catch (e: any) {
    message.error(e?.message || '启停失败')
  } finally {
    togglingId.value = null
  }
}

async function remove(id: string) {
  deletingId.value = id
  try {
    await apiDelete(`/super-admin/v2ray/routing/${id}`)
    message.success('已删除')
    await load()
  } catch (e: any) {
    message.error(e?.message || '删除失败')
  } finally {
    deletingId.value = null
  }
}

onMounted(load)
</script>
