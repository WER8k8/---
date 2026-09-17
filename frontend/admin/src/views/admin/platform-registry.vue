/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    title="平台来源审计"
    subtitle="客户自填/连接平台时自动同步至超管（客户侧无提示）"
    surface="elevated"
  >
    <div class="mb-4 flex flex-wrap gap-3 items-center">
      <a-select
        v-model:value="filterSource"
        allow-clear
        placeholder="来源"
        style="min-width: 160px"
        :options="sourceOptions"
        @change="load"
      />
      <a-button type="primary" :loading="loading" @click="load">刷新</a-button>
    </div>

    <a-table
      :columns="columns"
      :data-source="rows"
      :loading="loading"
      row-key="id"
      :pagination="pagination"
      size="middle"
      @change="onTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_new_platform'">
          <a-tag :color="record.is_new_platform ? 'green' : 'default'">
            {{ record.is_new_platform ? '新建平台' : '已有平台' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'source'">
          {{ sourceLabel(record.source) }}
        </template>
        <template v-else-if="column.key === 'nurture_rules'">
          <span class="text-xs text-gray-500">
            {{ nurtureSummary(record.nurture_rules) }}
          </span>
        </template>
      </template>
    </a-table>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'

interface OriginRow {
  id: string
  tenant_id: string
  tenant_name?: string
  platform_id: string
  platform_name?: string
  platform_type?: string
  region?: string
  source: string
  is_new_platform: boolean
  nurture_rules?: Record<string, unknown>
  browser_profile_id?: string
  created_at?: string
}

const loading = ref(false)
const rows = ref<OriginRow[]>([])
const filterSource = ref<string | undefined>()
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const sourceOptions = [
  { value: 'customer_custom', label: '自填平台名' },
  { value: 'customer_connect', label: '连接账号' },
]

const columns = [
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '租户', dataIndex: 'tenant_name', key: 'tenant_name', width: 140 },
  { title: '平台', dataIndex: 'platform_name', key: 'platform_name', width: 120 },
  { title: '区域', dataIndex: 'region', key: 'region', width: 72 },
  { title: '来源', key: 'source', width: 110 },
  { title: '平台状态', key: 'is_new_platform', width: 100 },
  { title: '养号模板', key: 'nurture_rules', ellipsis: true },
  { title: '指纹 ID', dataIndex: 'browser_profile_id', key: 'browser_profile_id', width: 120, ellipsis: true },
]

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (t: number) => `共 ${t} 条`,
})

function sourceLabel(s: string) {
  if (s === 'customer_custom') return '自填平台名'
  if (s === 'customer_connect') return '连接账号'
  return s
}

function nurtureSummary(rules?: Record<string, unknown>) {
  if (!rules || typeof rules !== 'object') return '—'
  const d = rules.warmup_days
  const posts = rules.daily_posts
  return `暖号 ${d ?? '?'} 天 · 日发 ${posts ?? '?'}`
}

async function load() {
  const tk = getAuthToken()
  if (!tk) {
    message.warning('请先登录超管账号')
    return
  }
  loading.value = true
  try {
    const qs = new URLSearchParams({
      page: String(page.value),
      page_size: String(pageSize.value),
    })
    if (filterSource.value) qs.set('source', filterSource.value)
    const res = await fetch(`/api/v1/super-admin/platform-origins?${qs}`, {
      headers: { Authorization: `Bearer ${tk}` },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const body = await res.json()
    const data = body.data || body
    rows.value = data.items || []
    total.value = data.total ?? rows.value.length
    pagination.current = page.value
    pagination.pageSize = pageSize.value
    pagination.total = total.value
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '加载失败'
    message.error(msg)
  } finally {
    loading.value = false
  }
}

function onTableChange(pag: { current?: number; pageSize?: number }) {
  page.value = pag.current ?? 1
  pageSize.value = pag.pageSize ?? 20
  load()
}

onMounted(load)
</script>
