/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
 <YdPage title="租户支付订单" subtitle="全平台租户付款单 · 与分润/财务台账同源" surface="elevated">
 <template #actions>
 <a-space>
 <a-button @click="openSupplement">补单</a-button>
 <a-button @click="openRefunds">退款审核</a-button>
 <YdTableToolbar
 :loading="loading"
 :target-ref="tablePanelRef"
 show-export
 @refresh="load"
 @export="exportCsv"
 />
 </a-space>
 </template>

 <YdFinanceNav />

 <a-space wrap class="mb-4">
 <a-select
 v-model:value="statusFilter"
 allow-clear
 placeholder="订单状态"
 style="min-width: 140px"
 @change="load"
 >
 <a-select-option value="paid">已支付</a-select-option>
 <a-select-option value="pending">待支付</a-select-option>
 <a-select-option value="failed">失败</a-select-option>
 <a-select-option value="cancelled">已取消</a-select-option>
 <a-select-option value="closed">已关闭</a-select-option>
 <a-select-option value="reconciled">已核销</a-select-option>
 <a-select-option value="refunded">已退款</a-select-option>
 </a-select>
 </a-space>

 <div ref="tablePanelRef" class="yd-panel yd-table-panel">
 <YdDataTable
 :columns="columns"
 :data-source="items"
 :loading="loading"
 :pagination="{ current: 1, pageSize: 100, total }"
 :table-props="{ rowKey: 'id' }"
 >
 <template #bodyCell="{ column, record }">
 <template v-if="column.key === 'amount'">
 ¥{{ centsToYuan(record.amount) }}
</template>
 <template v-else-if="column.key === 'status'">
 <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
</template>
 <template v-else-if="column.key === 'actions'">
 <a-space>
 <a-button
 v-if="record.status === 'paid'"
 type="link"
 size="small"
 @click="openReconcile(record)"
 >
 核销
</a-button>
 <a-button
 v-if="record.status === 'paid' || record.status === 'reconciled'"
 type="link"
 size="small"
 @click="openRefund(record)"
 >
 退款
</a-button>
 <a-button
 v-if="['pending', 'failed', 'paid', 'reconciled'].includes(record.status)"
 type="link"
 danger
 size="small"
 @click="openClose(record)"
 >
 关单
</a-button>
 </a-space>
</template>
</template>
 </YdDataTable>
 </div>

 <a-modal v-model:open="refundOpen" title="发起退款申请" @ok="submitRefund" :confirm-loading="actionLoading">
 <p class="text-sm text-gray-500 mb-3">创建后进入退款审核队列，超管批准后才触达支付通道。</p>
 <a-form layout="vertical">
 <a-form-item label="订单号">
 <a-input :value="actionTarget?.order_no" disabled />
</a-form-item>
 <a-form-item label="退款金额（元）" required>
 <a-input-number
 v-model:value="refundForm.amount_yuan"
 :min="0.01"
 :max="Number(((actionTarget?.amount || 0) / 100).toFixed(2))"
 :precision="2"
 style="width: 100%"
 />
</a-form-item>
 <a-form-item label="退款原因" required>
 <a-textarea v-model:value="refundForm.reason" :rows="3" :maxlength="500" />
</a-form-item>
 </a-form>
 </a-modal>

 <a-modal v-model:open="closeOpen" title="关闭订单" @ok="submitClose" :confirm-loading="actionLoading">
 <a-alert
 v-if="actionTarget && ['paid', 'reconciled'].includes(actionTarget.status)"
 type="warning"
 show-icon
 class="mb-3"
 message="已支付订单关单不会自动退款，资金请另发起退款申请。"
 />
 <a-form layout="vertical">
 <a-form-item label="关单原因" required>
 <a-textarea v-model:value="closeReason" :rows="3" :maxlength="500" />
</a-form-item>
 </a-form>
 </a-modal>

 <a-modal v-model:open="reconcileOpen" title="订单核销确认" @ok="submitReconcile" :confirm-loading="actionLoading">
 <a-form layout="vertical">
 <a-form-item label="对账流水/银行回单号">
 <a-input v-model:value="reconcileForm.external_ref" :maxlength="120" />
</a-form-item>
 <a-form-item label="备注">
 <a-textarea v-model:value="reconcileForm.note" :rows="2" :maxlength="500" />
</a-form-item>
 </a-form>
 </a-modal>

 <a-modal v-model:open="supplementOpen" title="补单（线下到账登记）" @ok="submitSupplement" :confirm-loading="actionLoading">
 <a-alert
 type="info"
 show-icon
 class="mb-3"
 message="补单会走与支付回调一致的发放链路；发放失败将标记 failed，禁止假成功。"
 />
 <a-form layout="vertical">
 <a-form-item label="租户 ID" required>
 <a-input v-model:value="supplementForm.tenant_id" :maxlength="64" />
</a-form-item>
 <a-form-item label="金额（元）" required>
 <a-input-number v-model:value="supplementForm.amount_yuan" :min="0.01" :precision="2" style="width: 100%" />
</a-form-item>
 <a-form-item label="主题" required>
 <a-input v-model:value="supplementForm.subject" :maxlength="200" />
</a-form-item>
 <a-form-item label="线下流水/回单号">
 <a-input v-model:value="supplementForm.external_ref" :maxlength="120" />
</a-form-item>
 <a-form-item label="备注">
 <a-textarea v-model:value="supplementForm.note" :rows="2" :maxlength="500" />
</a-form-item>
 </a-form>
 </a-modal>

 <a-modal v-model:open="refundsOpen" title="退款审核队列" width="880px" :footer="null">
 <a-table
 :loading="refundsLoading"
 :data-source="refunds"
 :columns="refundCols"
 row-key="id"
 size="small"
 :pagination="{ pageSize: 10 }"
 >
 <template #bodyCell="{ column, record }">
 <template v-if="column.key === 'amount'">
 ¥{{ centsToYuan(record.amount) }}
</template>
 <template v-else-if="column.key === 'status'">
 <a-tag>{{ record.status }}</a-tag>
</template>
 <template v-else-if="column.key === 'actions'">
 <a-space v-if="record.status === 'pending_review'">
 <a-button size="small" type="primary" @click="reviewRefund(record as RefundRow, 'approve')">批准</a-button>
 <a-button size="small" danger @click="openRefundReview(record as RefundRow, 'reject')">驳回</a-button>
 <a-button size="small" @click="openRefundReview(record as RefundRow, 'cancel')">取消</a-button>
 </a-space>
 <a-button
 v-else-if="record.status === 'failed'"
 size="small"
 @click="reviewRefund(record as RefundRow, 'approve')"
 >
 重试批准
</a-button>
</template>
 </template>
 </a-table>
 </a-modal>

 <a-modal v-model:open="refundReviewOpen" :title="refundReviewAction === 'reject' ? '驳回退款' : '取消退款'" @ok="submitRefundReview">
 <a-form layout="vertical">
 <a-form-item label="原因" required>
 <a-textarea v-model:value="refundReviewReason" :rows="3" :maxlength="500" />
</a-form-item>
 </a-form>
 </a-modal>
</YdPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage, YdDataTable, YdTableToolbar } from '@/components/youding';
import YdFinanceNav from '@/components/youding/YdFinanceNav.vue';
import { apiGet, apiPost } from '@/utils/api';

type OrderRow = {
 id: string;
 order_no: string;
 tenant_id: string;
 tenant_name: string;
 amount: number;
 channel: string;
 subject: string;
 status: string;
 paid_at?: string;
 created_at: string;
};

type RefundRow = {
 id: string;
 order_no: string;
 amount: number;
 status: string;
 reason?: string;
 reject_reason?: string;
 result_message?: string;
};

const loading = ref(false);
const items = ref<OrderRow[]>([]);
const total = ref(0);
const statusFilter = ref<string | undefined>(undefined);
const tablePanelRef = ref<HTMLElement | null>(null);
const actionLoading = ref(false);

const actionTarget = ref<OrderRow | null>(null);
const refundOpen = ref(false);
const refundForm = reactive({ amount_yuan: 0.01, reason: '' });
const closeOpen = ref(false);
const closeReason = ref('');
const reconcileOpen = ref(false);
const reconcileForm = reactive({ external_ref: '', note: '' });
const supplementOpen = ref(false);
const supplementForm = reactive({
 tenant_id: '',
 amount_yuan: 0.01,
 subject: '',
 external_ref: '',
 note: '',
});

const refundsOpen = ref(false);
const refundsLoading = ref(false);
const refunds = ref<RefundRow[]>([]);
const refundReviewOpen = ref(false);
const refundReviewAction = ref<'reject' | 'cancel'>('reject');
const refundReviewReason = ref('');
const refundReviewTarget = ref<RefundRow | null>(null);

const columns = [
 { title: '订单号', dataIndex: 'order_no', key: 'order_no', width: 200 },
 { title: '租户', dataIndex: 'tenant_name', key: 'tenant_name', width: 160 },
 { title: '主题', dataIndex: 'subject', key: 'subject', ellipsis: true },
 { title: '金额', key: 'amount', width: 100 },
 { title: '渠道', dataIndex: 'channel', key: 'channel', width: 90 },
 { title: '状态', key: 'status', width: 100 },
 { title: '支付时间', dataIndex: 'paid_at', key: 'paid_at', width: 170 },
 { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
 { title: '操作', key: 'actions', width: 180 },
];

const refundCols = [
 { title: '订单号', dataIndex: 'order_no', key: 'order_no', width: 180 },
 { title: '金额', key: 'amount', width: 100 },
 { title: '原因', dataIndex: 'reason', key: 'reason', ellipsis: true },
 { title: '状态', key: 'status', width: 110 },
 { title: '结果', dataIndex: 'result_message', key: 'result_message', ellipsis: true },
 { title: '操作', key: 'actions', width: 180 },
];

function centsToYuan(cents: number) {
 return (Number(cents || 0) / 100).toFixed(2);
}

function statusLabel(s: string) {
 const map: Record<string, string> = {
 paid: '已支付',
 pending: '待支付',
 failed: '失败',
 cancelled: '已取消',
 closed: '已关闭',
 reconciled: '已核销',
 refunded: '已退款',
 };
 return map[s] || s;
}

function statusColor(s: string) {
 const map: Record<string, string> = {
 paid: 'green',
 pending: 'orange',
 failed: 'red',
 cancelled: 'default',
 closed: 'default',
 reconciled: 'blue',
 refunded: 'purple',
 };
 return map[s] || 'default';
}

async function load() {
 loading.value = true;
 try {
 const data = await apiGet<OrderRow[]>('/payment/orders', {
 page: 1,
 page_size: 100,
 status: statusFilter.value || undefined,
 });
 items.value = Array.isArray(data) ? data : [];
 total.value = items.value.length;
 } finally {
 loading.value = false;
 }
}

function exportCsv() {
 const header = ['订单号', '租户', '主题', '金额(元)', '渠道', '状态', '支付时间', '创建时间'];
 const rows = items.value.map((r) => [
 r.order_no,
 r.tenant_name,
 r.subject,
 centsToYuan(r.amount),
 r.channel,
 statusLabel(r.status),
 r.paid_at || '',
 r.created_at,
 ]);
 const csv = [header, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
 const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
 const url = URL.createObjectURL(blob);
 const a = document.createElement('a');
 a.href = url;
 a.download = `payment-orders-${Date.now()}.csv`;
 a.click();
 URL.revokeObjectURL(url);
}

function openRefund(row: OrderRow) {
 actionTarget.value = row;
 refundForm.amount_yuan = Number((Number(row.amount || 0) / 100).toFixed(2));
 refundForm.reason = '';
 refundOpen.value = true;
}

async function submitRefund() {
 if (!actionTarget.value) return;
 if (!refundForm.reason.trim()) {
 message.error('请填写退款原因');
 return;
 }
 actionLoading.value = true;
 try {
 await apiPost('/payment/refund', {
 order_no: actionTarget.value.order_no,
 refund_amount: refundForm.amount_yuan,
 reason: refundForm.reason,
 });
 message.success('退款申请已提交，待审核');
 refundOpen.value = false;
 await loadRefunds();
 } catch (e: unknown) {
 message.error((e as Error).message || '退款申请失败');
 } finally {
 actionLoading.value = false;
 }
}

function openClose(row: OrderRow) {
 actionTarget.value = row;
 closeReason.value = '';
 closeOpen.value = true;
}

async function submitClose() {
 if (!actionTarget.value) return;
 if (!closeReason.value.trim()) {
 message.error('请填写关单原因');
 return;
 }
 actionLoading.value = true;
 try {
 await apiPost(`/payment/orders/${actionTarget.value.id}/close`, { reason: closeReason.value });
 message.success('订单已关闭');
 closeOpen.value = false;
 await load();
 } catch (e: unknown) {
 message.error((e as Error).message || '关单失败');
 } finally {
 actionLoading.value = false;
 }
}

function openReconcile(row: OrderRow) {
 actionTarget.value = row;
 reconcileForm.external_ref = '';
 reconcileForm.note = '';
 reconcileOpen.value = true;
}

async function submitReconcile() {
 if (!actionTarget.value) return;
 actionLoading.value = true;
 try {
 await apiPost(`/payment/orders/${actionTarget.value.id}/reconcile`, {
 external_ref: reconcileForm.external_ref || undefined,
 note: reconcileForm.note || undefined,
 });
 message.success('订单已核销确认');
 reconcileOpen.value = false;
 await load();
 } catch (e: unknown) {
 message.error((e as Error).message || '核销失败');
 } finally {
 actionLoading.value = false;
 }
}

function openSupplement() {
 supplementForm.tenant_id = items.value[0]?.tenant_id || '';
 supplementForm.amount_yuan = 0.01;
 supplementForm.subject = '';
 supplementForm.external_ref = '';
 supplementForm.note = '';
 supplementOpen.value = true;
}

async function submitSupplement() {
 if (!supplementForm.tenant_id.trim() || !supplementForm.subject.trim()) {
 message.error('请填写租户与主题');
 return;
 }
 actionLoading.value = true;
 try {
 await apiPost('/payment/orders/supplement', {
 tenant_id: supplementForm.tenant_id,
 amount: Math.round(supplementForm.amount_yuan * 100),
 subject: supplementForm.subject,
 channel: 'manual',
 external_ref: supplementForm.external_ref || undefined,
 note: supplementForm.note || undefined,
 });
 message.success('补单已完成');
 supplementOpen.value = false;
 await load();
 } catch (e: unknown) {
 message.error((e as Error).message || '补单失败');
 } finally {
 actionLoading.value = false;
 }
}

async function loadRefunds() {
 refundsLoading.value = true;
 try {
 const res = await apiGet<{ items?: RefundRow[] }>('/payment/refunds', { page: 1, page_size: 50 });
 refunds.value = res?.items || (Array.isArray(res) ? (res as RefundRow[]) : []);
 } catch {
 refunds.value = [];
 } finally {
 refundsLoading.value = false;
 }
}

function openRefunds() {
 refundsOpen.value = true;
 void loadRefunds();
}

async function reviewRefund(row: RefundRow, action: 'approve' | 'reject' | 'cancel', reason?: string) {
 actionLoading.value = true;
 try {
 await apiPost(`/payment/refunds/${row.id}/review`, { action, reason });
 message.success(action === 'approve' ? '已批准退款' : action === 'reject' ? '已驳回' : '已取消');
 await loadRefunds();
 await load();
 } catch (e: unknown) {
 message.error((e as Error).message || '审核失败');
 } finally {
 actionLoading.value = false;
 }
}

function openRefundReview(row: RefundRow, action: 'reject' | 'cancel') {
 refundReviewTarget.value = row;
 refundReviewAction.value = action;
 refundReviewReason.value = '';
 refundReviewOpen.value = true;
}

async function submitRefundReview() {
 if (!refundReviewTarget.value) return;
 if (!refundReviewReason.value.trim()) {
 message.error('请填写原因');
 return;
 }
 refundReviewOpen.value = false;
 await reviewRefund(refundReviewTarget.value, refundReviewAction.value, refundReviewReason.value);
}

onMounted(() => {
 void load();
});
</script>
