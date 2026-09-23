/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
 <YdPage title="分润结算" subtitle="审核代理分润计提并标记已结算" surface="elevated">
 <template #actions>
 <YdTableToolbar
 :loading="loading"
 :target-ref="tablePanelRef"
 show-export
 @refresh="load"
 @export="exportCsv"
 />
</template>

 <YdFinanceNav />

 <YdStatsRow :cols="4">
 <YdStatsCard label="待结算" :value="`¥${centsToYuan(stats.pending_cents)}`" tone="amber" compact />
 <YdStatsCard label="已结算" :value="`¥${centsToYuan(stats.settled_cents)}`" tone="green" compact />
 <YdStatsCard label="已驳回" :value="`¥${centsToYuan(stats.rejected_cents)}`" tone="red" compact />
 <YdStatsCard label="合计" :value="`¥${centsToYuan(stats.total_cents)}`" compact />
</YdStatsRow>

 <a-tabs v-model:activeKey="statusFilter" class="mt-4" @change="load">
 <a-tab-pane key="pending" tab="待结算" />
 <a-tab-pane key="settled" tab="已结算" />
 <a-tab-pane key="rejected" tab="已驳回" />
 <a-tab-pane key="" tab="全部" />
</a-tabs>

 <div ref="tablePanelRef" class="yd-panel yd-table-panel">
 <YdDataTable
 :columns="columns"
 :data-source="items"
 :loading="loading"
 :pagination="{ current: 1, pageSize: 20, total }"
 :table-props="{ rowKey: 'id' }"
 >
 <template #bodyCell="{ column, record }">
 <template v-if="column.key === 'revenue'">
 ¥{{ centsToYuan(record.revenue_cents) }}
</template>
 <template v-else-if="column.key === 'commission'">
 ¥{{ centsToYuan(record.commission_cents) }}
</template>
 <template v-else-if="column.key === 'rate'">
 {{ (record.commission_rate_bp / 100).toFixed(1) }}%
</template>
 <template v-else-if="column.key === 'status'">
 <a-tag :color="statusColor(record.status)">
 {{ statusLabel(record.status) }}
</a-tag>
</template>
 <template v-else-if="column.key === 'actions'">
 <a-space>
 <a-button
 v-if="record.status === 'pending'"
 type="link"
 size="small"
 :loading="settlingId === record.id"
 @click="settle(record.id)"
 >
 标记已结算
</a-button>
 <a-button
 v-if="record.status === 'pending'"
 type="link"
 danger
 size="small"
 @click="openReason(record, 'reject')"
 >
 驳回
</a-button>
 <a-button
 v-if="record.status === 'pending' || record.status === 'settled'"
 type="link"
 danger
 size="small"
 @click="openReason(record, 'cancel')"
 >
 取消
</a-button>
 <a-button
 v-if="record.status === 'pending'"
 type="link"
 size="small"
 @click="openEdit(record)"
 >
 修正
</a-button>
 </a-space>
</template>
</template>
</YdDataTable>
</div>

 <a-modal
 v-model:open="reasonOpen"
 :title="reasonAction === 'reject' ? '驳回结算单' : '取消结算单'"
 @ok="submitReason"
 :confirm-loading="reasonLoading"
 >
 <a-form layout="vertical">
 <a-form-item label="原因" required>
 <a-textarea v-model:value="reasonText" :rows="3" :maxlength="500" />
</a-form-item>
</a-form>
</a-modal>

 <a-modal
 v-model:open="editOpen"
 title="修正结算单"
 @ok="submitEdit"
 :confirm-loading="editLoading"
 >
 <a-form layout="vertical">
 <a-form-item label="营收（元）">
 <a-input-number v-model:value="editForm.revenue_yuan" :min="0.01" :precision="2" style="width: 100%" />
</a-form-item>
 <a-form-item label="比例（%）">
 <a-input-number v-model:value="editForm.rate_pct" :min="0" :max="100" :precision="1" style="width: 100%" />
</a-form-item>
 <a-form-item label="备注">
 <a-textarea v-model:value="editForm.note" :rows="2" :maxlength="500" />
</a-form-item>
</a-form>
</a-modal>
</YdPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

import {
 YdDataTable,
 YdFinanceNav,
 YdPage,
 YdStatsCard,
 YdStatsRow,
 YdTableToolbar,
} from '@/components/youding'
import api from '@/api'
import { downloadTableCsv } from '@/utils/exportCsv'

type Row = {
 id: string
 agent_node_id: string
 period: string
 revenue_cents: number
 commission_cents: number
 commission_rate_bp: number
 status: string
 note?: string
 reject_reason?: string
 settled_at?: string
}

const tablePanelRef = ref<HTMLElement | null>(null)
const loading = ref(false)
const settlingId = ref('')
const items = ref<Row[]>([])
const total = ref(0)
const statusFilter = ref('pending')
const stats = reactive({
 pending_cents: 0,
 settled_cents: 0,
 rejected_cents: 0,
 total_cents: 0,
})

const reasonOpen = ref(false)
const reasonLoading = ref(false)
const reasonAction = ref<'reject' | 'cancel'>('reject')
const reasonText = ref('')
const reasonTarget = ref<Row | null>(null)

const editOpen = ref(false)
const editLoading = ref(false)
const editTarget = ref<Row | null>(null)
const editForm = reactive({ revenue_yuan: 0, rate_pct: 0, note: '' })

const columns = [
 { title: '代理节点', dataIndex: 'agent_node_id', key: 'agent_node_id', ellipsis: true, align: 'center' as const },
 { title: '周期', dataIndex: 'period', key: 'period', width: 100, align: 'center' as const },
 { title: '营收', key: 'revenue', width: 110, align: 'center' as const },
 { title: '分润', key: 'commission', width: 110, align: 'center' as const },
 { title: '比例', key: 'rate', width: 80, align: 'center' as const },
 { title: '状态', key: 'status', width: 90, align: 'center' as const },
 { title: '结算时间', dataIndex: 'settled_at', key: 'settled_at', width: 170, align: 'center' as const },
 { title: '操作', key: 'actions', width: 120, align: 'center' as const },
]

function centsToYuan(cents: number) {
 return ((cents || 0) / 100).toFixed(2)
}

function statusLabel(s: string) {
 const map: Record<string, string> = {
 pending: '待结算',
 settled: '已结算',
 rejected: '已驳回',
 cancelled: '已取消',
 }
 return map[s] || s
}

function statusColor(s: string) {
 const map: Record<string, string> = {
 pending: 'orange',
 settled: 'green',
 rejected: 'red',
 cancelled: 'default',
 }
 return map[s] || 'default'
}

async function load() {
 loading.value = true
 try {
 const params: Record<string, string> = {}
 if (statusFilter.value) params.status = statusFilter.value
 const res = (await api.get('/finance/commissions', { params })) as {
 items?: Row[]
 total?: number
 stats?: { pending_cents: number; settled_cents: number; rejected_cents: number; total_cents: number }
 }
 items.value = res?.items ?? []
 total.value = res?.total ?? items.value.length
 if (res?.stats) Object.assign(stats, res.stats)
 } finally {
 loading.value = false
 }
}

function exportCsv() {
 downloadTableCsv(
 'commissions.csv',
 ['代理节点', '周期', '营收', '分润', '比例', '状态', '结算时间'],
 items.value.map((r) => [
 r.agent_node_id,
 r.period,
 centsToYuan(r.revenue_cents),
 centsToYuan(r.commission_cents),
 `${(r.commission_rate_bp / 100).toFixed(1)}%`,
 statusLabel(r.status),
 r.settled_at || '',
 ]),
 )
}

async function settle(id: string) {
 settlingId.value = id
 try {
 await api.post(`/finance/commissions/${id}/settle`)
 message.success('已标记为已结算')
 await load()
 } catch (e: unknown) {
 const err = e as { message?: string }
 message.error(err.message || '结算失败')
 } finally {
 settlingId.value = ''
 }
}

function openReason(row: Record<string, unknown>, action: 'reject' | 'cancel') {
 reasonTarget.value = row as Row
 reasonAction.value = action
 reasonText.value = ''
 reasonOpen.value = true
}

async function submitReason() {
 if (!reasonTarget.value) return
 if (!reasonText.value.trim()) {
 message.error('请填写原因')
 return
 }
 reasonLoading.value = true
 try {
 const path =
 reasonAction.value === 'reject'
 ? `/finance/commissions/${reasonTarget.value.id}/reject`
 : `/finance/commissions/${reasonTarget.value.id}/cancel`
 await api.post(path, { reason: reasonText.value })
 message.success(reasonAction.value === 'reject' ? '已驳回' : '已取消')
 reasonOpen.value = false
 await load()
 } catch (e: unknown) {
 const err = e as { message?: string }
 message.error(err.message || '操作失败')
 } finally {
 reasonLoading.value = false
 }
}

function openEdit(row: Record<string, unknown>) {
 editTarget.value = row as Row
 editForm.revenue_yuan = Number(((row as Row).revenue_cents || 0) / 100)
 editForm.rate_pct = Number((((row as Row).commission_rate_bp || 0) / 100).toFixed(1))
 editForm.note = (row as Row).note || ''
 editOpen.value = true
}

async function submitEdit() {
 if (!editTarget.value) return
 editLoading.value = true
 try {
 await api.put(`/finance/commissions/${editTarget.value.id}`, {
 revenue_cents: Math.round(editForm.revenue_yuan * 100),
 commission_rate_bp: Math.round(editForm.rate_pct * 100),
 note: editForm.note || undefined,
 })
 message.success('结算单已修正')
 editOpen.value = false
 await load()
 } catch (e: unknown) {
 const err = e as { message?: string }
 message.error(err.message || '修正失败')
 } finally {
 editLoading.value = false
 }
}

onMounted(load)
</script>

<style scoped>
.mt-4 {
 margin-top: 16px;
}
</style>
