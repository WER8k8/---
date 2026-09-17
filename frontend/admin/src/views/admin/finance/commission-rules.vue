/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="分润规则配置" subtitle="首单合计 ≤30%，续费合计 ≤10%（L1 平台留存）" surface="elevated">
    <template #actions>
      <YdTableToolbar
        :loading="loading"
        :target-ref="tablePanelRef"
        :show-export="false"
        @refresh="load"
      />
    </template>

    <YdFinanceNav />

    <div ref="tablePanelRef" class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="columns"
        :data-source="rules"
        :loading="loading"
        :pagination="false"
        :table-props="{ rowKey: 'id' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'kind'">
            {{ record.payment_kind === 'first' ? '首单' : '续费' }}
          </template>
          <template v-else-if="column.key === 'rate'">
            <a-input-number
              v-model:value="editRates[record.id]"
              :min="0"
              :max="100"
              :step="0.1"
              size="small"
              style="width: 90px"
            />
            <span class="ml-1 text-xs text-slate-400">%</span>
          </template>
          <template v-else-if="column.key === 'active'">
            <a-switch v-model:checked="editActive[record.id]" size="small" />
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" :loading="savingId === record.id" @click="save(record)">保存</a-button>
          </template>
        </template>
      </YdDataTable>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

import { YdDataTable, YdFinanceNav, YdPage, YdTableToolbar } from '@/components/youding'
import api from '@/api'

type Rule = {
  id: string
  payment_kind: string
  agent_level: string
  rate_bp: number
  label: string
  is_active: boolean
}

const tablePanelRef = ref<HTMLElement | null>(null)
const loading = ref(false)
const savingId = ref('')
const rules = ref<Rule[]>([])
const editRates = reactive<Record<string, number>>({})
const editActive = reactive<Record<string, boolean>>({})

const columns = [
  { title: '类型', key: 'kind', width: 80, align: 'center' as const },
  { title: '层级', dataIndex: 'agent_level', key: 'agent_level', width: 80, align: 'center' as const },
  { title: '说明', dataIndex: 'label', key: 'label', align: 'center' as const },
  { title: '比例', key: 'rate', width: 130, align: 'center' as const },
  { title: '启用', key: 'active', width: 80, align: 'center' as const },
  { title: '操作', key: 'actions', width: 80, align: 'center' as const },
]

async function load() {
  loading.value = true
  try {
    const res = (await api.get('/finance/commission-rules')) as Rule[]
    rules.value = Array.isArray(res) ? res : []
    for (const r of rules.value) {
      editRates[r.id] = r.rate_bp / 100
      editActive[r.id] = r.is_active
    }
  } finally {
    loading.value = false
  }
}

async function save(record: Record<string, unknown>) {
  const id = String(record.id ?? '')
  if (!id) return
  savingId.value = id
  try {
    await api.put(`/finance/commission-rules/${id}`, {
      rate_bp: Math.round((editRates[id] || 0) * 100),
      is_active: editActive[id],
    })
    message.success('已保存')
    await load()
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.error(err.message || '保存失败')
  } finally {
    savingId.value = ''
  }
}

onMounted(load)
</script>
