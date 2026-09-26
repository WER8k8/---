/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 * 履约队列 · 傻子都行版
 * 原则：用户只确认；一单一步；状态说人话；专家能力收进「更多」
 */
<template>
  <YdPage title="履约队列" subtitle="外贸 7 步：询盘 → 核价 → 形式发票 → 定金 → 生产 → 单证 → 尾款" surface="elevated">
    <template #actions>
      <a-button type="primary" size="large" :loading="hermesLoading" @click="dispatchGoldenPathFulfillment(pickTopOrder())">
        一键推进履约
      </a-button>
    </template>

    <!-- ① 今日要处理 -->
    <div class="ff-hero">
      <div class="ff-hero-text">
        <div class="ff-eyebrow">今天先处理这些</div>
        <h2 class="ff-title">{{ summaryHeadline }}</h2>
        <p class="ff-sub">{{ summarySub }}</p>
      </div>
      <div class="ff-stats">
        <div class="ff-stat">
          <b>{{ items.length }}</b>
          <span>在途订单</span>
        </div>
        <div class="ff-stat warn">
          <b>{{ needActionCount }}</b>
          <span>要你点一下</span>
        </div>
        <div class="ff-stat ok">
          <b>{{ doneCount }}</b>
          <span>已结清</span>
        </div>
      </div>
    </div>

    <!-- 筛选（极简） -->
    <div class="ff-filter">
      <a-input
        v-model:value="query.search"
        placeholder="搜订单号或客户"
        allow-clear
        size="large"
        style="max-width: 280px"
        @pressEnter="onSearch"
      />
      <a-select
        v-model:value="query.status"
        placeholder="全部阶段"
        allow-clear
        size="large"
        style="width: 180px"
        @change="onSearch"
      >
        <a-select-option value="pending">待付款 / 待处理</a-select-option>
        <a-select-option value="deposit_received">定金已收</a-select-option>
        <a-select-option value="in_production">生产中</a-select-option>
        <a-select-option value="shipped">已出运</a-select-option>
        <a-select-option value="completed">已结清</a-select-option>
      </a-select>
      <a-button size="large" @click="onReset">清空</a-button>
      <a-button size="large" :loading="loading" @click="reload">刷新</a-button>
      <span class="ff-hint">不懂状态？看每条右边的色点说明</span>
    </div>

    <!-- ② 订单卡列表 -->
    <a-spin :spinning="loading">
      <div v-if="!items.length" class="ff-empty">
        <YdEmptyState description="还没有履约订单。先在询盘里成单，或点「一键推进履约」试跑。" />
      </div>
      <div v-else class="ff-list">
        <article v-for="(row, idx) in items" :key="String(row.id || idx)" class="ff-card">
          <div class="ff-card-main">
            <div class="ff-card-top">
              <div class="ff-order-no">{{ row.order_number || row.id || '订单' }}</div>
              <span class="ff-badge" :class="statusLevel(row.status)">{{ formatStatusLabel(row.status) }}</span>
            </div>
            <div class="ff-card-meta">
              <span>{{ row.customer_name || row.buyer_name || '客户未填' }}</span>
              <span class="ff-dot">·</span>
              <span class="ff-money">{{ formatMoney(row.total_amount) }}</span>
              <span class="ff-dot">·</span>
              <span class="ff-muted">{{ formatDate(row.created_at) }}</span>
            </div>
            <div class="ff-steps" :aria-label="'进度 ' + progressLabel(row)">
              <span v-for="(st, si) in stepList" :key="st.key" class="ff-step" :class="stepClass(row, si)">
                <i></i>{{ st.label }}
              </span>
            </div>
            <p class="ff-next">{{ nextHint(row) }}</p>
          </div>
          <div class="ff-card-actions">
            <a-button type="primary" size="large" :loading="hermesLoading" @click="dispatchGoldenPathFulfillment(row)">
              下一步
            </a-button>
            <a-button size="large" @click="openOrderDetail(row)">看详情</a-button>
            <a-dropdown>
              <a-button size="large">更多</a-button>
              <template #overlay>
                <a-menu @click="({ key }: any) => onMore(key as string, row)">
                  <a-menu-item key="pi">生成形式发票</a-menu-item>
                  <a-menu-item key="pl">装箱单</a-menu-item>
                  <a-menu-item key="co">原产地证草案</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </article>
      </div>
    </a-spin>

    <!-- ③ 详情 / 单证（浮层，仍只留主按钮） -->
    <a-drawer
      v-model:open="drawerOpen"
      :width="560"
      :title="activeOrder?.order_number || '订单详情'"
      placement="right"
    >
      <div v-if="activeOrder" class="ff-drawer">
        <div class="ff-kv">
          <div><span>客户</span><b>{{ (activeOrder as any).customer_name || '—' }}</b></div>
          <div><span>金额</span><b>{{ formatMoney((activeOrder as any).total_amount) }}</b></div>
          <div><span>阶段</span><b>{{ formatStatusLabel(activeOrder.status) }}</b></div>
          <div><span>提单/运单</span><b>{{ (activeOrder as any).tracking_number || '—' }}</b></div>
        </div>

        <a-alert type="info" show-icon class="ff-alert" message="下一步做什么" :description="nextHint(activeOrder)" />

        <div class="ff-primary-row">
          <a-button
            type="primary"
            size="large"
            block
            :loading="hermesLoading"
            @click="dispatchGoldenPathFulfillment(activeOrder)"
          >
            推进这一步（Hermes）
          </a-button>
        </div>

        <a-divider orientation="left" plain>单证（要出再点）</a-divider>
        <div class="ff-docs">
          <a-button size="large" :loading="docLoading==='pi'" @click="handleDocumentAction(activeOrder, 'pi')">形式发票 PI</a-button>
          <a-button size="large" :loading="docLoading==='packing-list'" @click="handleDocumentAction(activeOrder, 'pl')">装箱单</a-button>
          <a-button size="large" :loading="docLoading==='certificate-of-origin'" @click="handleDocumentAction(activeOrder, 'co')">原产地证草案</a-button>
        </div>

        <div v-if="currentDocResult" class="ff-doc-result">
          <div class="ff-doc-title">{{ currentDocTitle }}</div>
          <pre class="code-block">{{ currentDocFormatted }}</pre>
          <div class="ff-doc-actions">
            <a-button @click="exportDocFile('html')">导出网页</a-button>
            <a-button @click="exportDocFile('docx')">导出 Word</a-button>
          </div>
        </div>

        <a-divider orientation="left" plain>状态推进（黄金单）</a-divider>
        <div class="ff-verify golden-actions">
          <a-button size="large" :loading="actionLoading==='deposit'" @click="markDeposit">1 · 记定金已收</a-button>
          <a-button size="large" :loading="actionLoading==='ship'" @click="markShipped">2 · 登记已发货</a-button>
          <a-button size="large" :loading="actionLoading==='balance'" @click="markBalance">3 · 记尾款已收</a-button>
          <a-button type="primary" size="large" :loading="actionLoading==='win'" @click="markWon">4 · 结案成单</a-button>
        </div>

        <a-divider orientation="left" plain>核销登记（可选）</a-divider>
        <div class="ff-verify">
          <a-input v-model:value="verifyForm.deposit_ref" placeholder="定金水单号（可选）" />
          <a-input-number
            v-model:value="verifyForm.deposit_ref_amount"
            placeholder="定金金额（默认 30%）"
            :min="0"
            style="width: 100%"
          />
          <a-input v-model:value="verifyForm.bl_number" placeholder="提单号" />
          <a-input v-model:value="verifyForm.container_no" placeholder="柜号" />
          <a-input v-model:value="verifyForm.settle_ref" placeholder="尾款凭证号" />
          <a-button size="large" :loading="actionLoading==='verify'" @click="verifyFulfillment">保存核销信息</a-button>
        </div>
      </div>
    </a-drawer>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import { YdEmptyState, YdPage } from '@/components/youding';
import { useYoudingTable } from '@/composables/useYoudingTableBridge';
import { apiGet, apiPost } from '@/utils/api';
import { adaptPaginatedResponse } from '@/utils/ydTableUtils';

const router = useRouter();
const drawerOpen = ref(false);
const activeOrder = ref<Record<string, unknown> | null>(null);
const actionLoading = ref('');
const docLoading = ref('');
const currentDocTitle = ref('');
const currentDocResult = ref<Record<string, unknown> | null>(null);
const currentDocType = ref('');
const hermesLoading = ref(false);

const verifyForm = ref({
  deposit_ref: '',
  deposit_ref_amount: undefined as number | undefined,
  bl_number: '',
  container_no: '',
  settle_ref: '',
});

const baseColumns = [
  { key: 'order_number', title: '订单号', dataIndex: 'order_number', align: 'center' },
  { key: 'total_amount', title: '订单金额', dataIndex: 'total_amount', align: 'right' },
  { key: 'status', title: '履约阶段', dataIndex: 'status', align: 'center' },
  { key: 'tracking_number', title: '提单/运单号', dataIndex: 'tracking_number', align: 'center' },
  { key: 'created_at', title: '创建时间', dataIndex: 'created_at', align: 'center' },
  { key: 'action', title: '操作', align: 'center', width: 220 },
];

const { loading, items, query, search, reset, reload } = useYoudingTable<
  Record<string, unknown>,
  { search?: string; status?: string }
>({
  columnOrderKey: 'client-fulfillment-queue-cols-v2',
  columns: baseColumns,
  fetcher: async (q) => {
    const raw = await apiGet<Record<string, unknown>[]>('/orders', {
      skip: ((q.page || 1) - 1) * (q.pageSize || 50),
      limit: q.pageSize || 50,
      status: q.status || undefined,
    });
    const { rows, total } = adaptPaginatedResponse<Record<string, unknown>>(raw);
    return { items: rows, total };
  },
});

const doneCount = computed(
  () => items.value.filter((r) => String(r.status || '').toLowerCase() === 'completed').length,
);
const needActionCount = computed(
  () =>
    items.value.filter((r) => {
      const s = String(r.status || '').toLowerCase();
      return s === 'pending' || s === 'deposit_received';
    }).length,
);
const summaryHeadline = computed(() => {
  if (needActionCount.value > 0) return `有 ${needActionCount.value} 单等你点「下一步」`;
  if (items.value.length === 0) return '暂无履约订单';
  return '履约都在正常推进';
});
const summarySub = computed(() =>
  needActionCount.value > 0
    ? '点「下一步」系统会自动推：核价、形式发票、单证、状态。'
    : '出问题会标红；正常会标绿。',
);

function pickTopOrder(): Record<string, unknown> | undefined {
  return items.value.find((r) => {
    const s = String(r.status || '').toLowerCase();
    return s === 'pending' || s === 'deposit_received';
  }) || items.value[0];
}

function onSearch() {
  void search();
}

function onReset() {
  query.status = undefined;
  query.search = undefined;
  void reset();
}

function formatMoney(v: unknown): string {
  const n = Number(v);
  if (!Number.isFinite(n) || n <= 0) return '金额待填';
  return `¥ ${n.toLocaleString()}`;
}

function formatDate(v: unknown): string {
  if (!v) return '';
  const d = new Date(String(v));
  if (Number.isNaN(d.getTime())) return String(v).slice(0, 10);
  return d.toLocaleDateString();
}

function formatStatusLabel(status: unknown): string {
  const s = String(status || '').toLowerCase();
  const map: Record<string, string> = {
    pending: '待处理',
    deposit_received: '定金已收',
    in_production: '生产中',
    shipped: '已出运',
    completed: '已结清',
    cancelled: '已取消',
  };
  return map[s] || '待确认';
}

/** 绿=正常 黄=要注意 红=出问题 灰=还没开/未知 */
function statusLevel(status: unknown): string {
  const s = String(status || '').toLowerCase();
  if (s === 'completed') return 'ok';
  if (s === 'shipped' || s === 'in_production') return 'info';
  if (s === 'deposit_received') return 'warn';
  if (s === 'cancelled') return 'bad';
  return 'warn';
}

function nextHint(row: Record<string, unknown> | null): string {
  const s = String(row?.status || '').toLowerCase();
  if (s === 'pending') return '下一步：确认定金或收款，然后生成形式发票。';
  if (s === 'deposit_received') return '下一步：排产跟进；需要时可出装箱单。';
  if (s === 'in_production') return '下一步：盯交期；出运前补齐提单与装箱单。';
  if (s === 'shipped') return '下一步：登记尾款，做结清。';
  if (s === 'completed') return '这单已结清，可点「结案成单」写入经营结果。';
  return '点「下一步」让系统自动推进当前阶段。';
}

const stepList = [
  { key: 'deposit', label: '定金' },
  { key: 'ship', label: '出运' },
  { key: 'balance', label: '尾款' },
  { key: 'win', label: '成单' },
];

function stepClass(row: Record<string, unknown> | null, idx: number): string {
  const s = String(row?.status || '').toLowerCase();
  const map: Record<string, number> = {
    pending: 0,
    deposit_received: 1,
    in_production: 1,
    shipped: 2,
    completed: 3,
    cancelled: -1,
  };
  const stage = map[s] ?? 0;
  if (s === 'cancelled') return 'is-bad';
  if (idx < stage) return 'is-done';
  if (idx === stage) return 'is-active';
  return '';
}

function progressLabel(row: Record<string, unknown> | null): string {
  const s = String(row?.status || '').toLowerCase();
  const map: Record<string, string> = {
    pending: '1/4 待定金',
    deposit_received: '2/4 已定金',
    in_production: '2/4 生产中',
    shipped: '3/4 已出运',
    completed: '4/4 已结清',
    cancelled: '已取消',
  };
  return map[s] || '1/4';
}

async function dispatchGoldenPathFulfillment(record?: Record<string, unknown>) {
  hermesLoading.value = true;
  try {
    const orderId = record?.id ? String(record.id) : '';
    const orderNo = record?.order_number ? String(record.order_number) : '';
    const res = await apiPost<{
      plan_id?: string;
      graph_source?: string;
      node_count?: number;
    }>('/orchestration/golden-path/fulfillment', {
      intent: '履约推进与形式发票',
      payload: {
        order_id: orderId,
        message: orderNo
          ? `订单 ${orderNo} 履约推进与 PI`
          : orderId
            ? `订单 ${orderId} 履约推进与 PI`
            : '履约推进与 PI',
        product: String(record?.product || ''),
      },
      channel: 'web',
      context: { golden_path: 'GP-A', plane: 'task', order_id: orderId || undefined },
      auto_dispatch: true,
    });
    const planId = res?.plan_id || '';
    message.success(`已提交：系统开始推进履约${planId ? `（任务 ${planId}）` : ''}`);
    if (planId) void router.push({ path: '/client/tasks', query: { plan: planId } });
  } catch (e) {
    message.error(e instanceof Error ? e.message : '提交失败，请重试');
  } finally {
    hermesLoading.value = false;
  }
}

async function openOrderDetail(record: Record<string, unknown>) {
  activeOrder.value = record;
  currentDocResult.value = null;
  drawerOpen.value = true;
  try {
    const full = await apiGet<Record<string, unknown>>(`/orders/${record.id}`);
    const data = (full as { data?: Record<string, unknown> })?.data || full;
    activeOrder.value = { ...record, ...data };
  } catch {
    /* 用列表数据 */
  }
}

async function handleDocumentAction(record: Record<string, unknown>, docType: string) {
  if (docType === 'pi') void dispatchGoldenPathFulfillment(record);
  await openOrderDetail(record);
  await fetchOrderDoc(docType === 'co' ? 'certificate-of-origin' : docType === 'pl' ? 'packing-list' : docType);
}

async function fetchOrderDoc(endpointDoc: string) {
  if (!activeOrder.value?.id) return;
  const id = String(activeOrder.value.id);
  docLoading.value = endpointDoc;
  currentDocType.value = endpointDoc;
  try {
    const res = await apiPost<Record<string, unknown>>(`/orders/${id}/documents/${endpointDoc}`);
    const data = (res as { data?: Record<string, unknown> })?.data || res;
    currentDocResult.value = data;
    currentDocTitle.value = `${String(data.doc_type || endpointDoc.toUpperCase())} 单据`;
    message.success(`${currentDocTitle.value} 已生成`);
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '单据生成失败');
  } finally {
    docLoading.value = '';
  }
}

const currentDocFormatted = computed(() =>
  currentDocResult.value ? JSON.stringify(currentDocResult.value, null, 2) : '',
);

function exportDocFile(format: 'html' | 'docx') {
  if (!activeOrder.value?.id) return;
  const id = String(activeOrder.value.id);
  const typeKey =
    currentDocType.value === 'packing-list'
      ? 'pl'
      : currentDocType.value === 'certificate-of-origin'
        ? 'co'
        : currentDocType.value || 'pi';
  window.open(`/api/v1/orders/${id}/documents/${typeKey}/export?format=${format}`, '_blank');
}

async function verifyFulfillment() {
  if (!activeOrder.value?.id) return;
  actionLoading.value = 'verify';
  try {
    await apiPost(`/orders/${String(activeOrder.value.id)}/fulfillment/verify`, {
      ...verifyForm.value,
    });
    message.success('已登记');
    void reload();
  } catch (e) {
    message.error(e instanceof Error ? e.message : '登记失败');
  } finally {
    actionLoading.value = '';
  }
}


function inquiryIdOf(row: Record<string, unknown> | null): string {
  return String(row?.inquiry_id || row?.lead_id || '');
}

function orderIdOf(row: Record<string, unknown> | null): string {
  return String(row?.id || '');
}

async function markDeposit() {
  const orderId = orderIdOf(activeOrder.value);
  const inquiryId = inquiryIdOf(activeOrder.value);
  const total = Number((activeOrder.value as any)?.total_amount || 0);
  const depositAmount = Number(verifyForm.value.deposit_ref_amount || 0) || (total ? round2(total * 0.3) : 0);
  if (!orderId) return message.warning('缺少订单编号');
  actionLoading.value = 'deposit';
  try {
    if (orderId) {
      await apiPost(`/orders/${orderId}/verify-deposit`, {
        deposit_amount: depositAmount,
        payment_reference: verifyForm.value.deposit_ref || undefined,
      });
    }
    if (inquiryId) {
      await apiPost(`/acquisition/ops-card/${inquiryId}/payment`, {
        deposit_amount: depositAmount,
        deposit_paid_at: new Date().toISOString(),
        note: verifyForm.value.deposit_ref || '定金已收（制单后履约推进）',
      });
    }
    message.success('已记定金 → 进入生产/备货');
    await reload();
    if (activeOrder.value?.id) await openOrderDetail(activeOrder.value as Record<string, unknown>);
  } catch (e) {
    message.error(e instanceof Error ? e.message : '定金登记失败');
  } finally {
    actionLoading.value = '';
  }
}

async function markShipped() {
  const orderId = orderIdOf(activeOrder.value);
  const inquiryId = inquiryIdOf(activeOrder.value);
  if (!orderId) return message.warning('缺少订单编号');
  actionLoading.value = 'ship';
  try {
    if (orderId) {
      await apiPost(`/orders/${orderId}/dispatch`, {
        bl_number: verifyForm.value.bl_number || undefined,
        container_no: verifyForm.value.container_no || undefined,
        tracking_number: verifyForm.value.bl_number || undefined,
      });
    }
    if (inquiryId) {
      await apiPost(`/acquisition/ops-card/${inquiryId}/logistics`, {
        bl_no: verifyForm.value.bl_number || '',
        container_no: verifyForm.value.container_no || '',
        milestone: 'shipped',
      });
    }
    message.success('已登记发货');
    await reload();
    if (activeOrder.value?.id) await openOrderDetail(activeOrder.value as Record<string, unknown>);
  } catch (e) {
    message.error(e instanceof Error ? e.message : '发货登记失败');
  } finally {
    actionLoading.value = '';
  }
}

async function markBalance() {
  const orderId = orderIdOf(activeOrder.value);
  const inquiryId = inquiryIdOf(activeOrder.value);
  if (!orderId) return message.warning('缺少订单编号');
  actionLoading.value = 'balance';
  try {
    if (orderId) {
      await apiPost(`/orders/${orderId}/settle-balance`, {
        payment_reference: verifyForm.value.settle_ref || undefined,
      });
    }
    if (inquiryId) {
      await apiPost(`/acquisition/ops-card/${inquiryId}/payment`, {
        balance_status: 'paid',
        note: verifyForm.value.settle_ref || '尾款已收',
      });
    }
    message.success('已记尾款 → 可结案成单');
    await reload();
    if (activeOrder.value?.id) await openOrderDetail(activeOrder.value as Record<string, unknown>);
  } catch (e) {
    message.error(e instanceof Error ? e.message : '尾款登记失败');
  } finally {
    actionLoading.value = '';
  }
}

async function markWon() {
  const inquiryId = inquiryIdOf(activeOrder.value) || orderIdOf(activeOrder.value);
  const orderId = orderIdOf(activeOrder.value);
  if (!inquiryId && !orderId) return message.warning('缺少订单编号');
  actionLoading.value = 'win';
  try {
    const key = inquiryId || orderId;
    await apiPost(`/acquisition/ops-card/${key}/win`, {
      amount: Number((activeOrder.value as any)?.total_amount || 0),
      currency: (activeOrder.value as any)?.currency || 'USD',
      note: '黄金单闭环成单',
      reasons: ['报价清晰', '响应快'],
    });
    if (orderId) {
      try {
        await apiPost(`/orders/${orderId}/confirm-receipt`, {});
      } catch {
        /* 订单侧已结清时忽略 */
      }
    }
    message.success('已结案成单 → 经营概览可见');
    void router.push('/client/dashboard');
  } catch (e) {
    message.error(e instanceof Error ? e.message : '结案失败');
  } finally {
    actionLoading.value = '';
  }
}

function round2(n: number): number {
  return Math.round(n * 100) / 100;
}

function onMore(key: string, row: Record<string, unknown>) {
  void handleDocumentAction(row, key);
}
</script>

<style scoped>
.ff-hero {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 18px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, #e8f5f0, #f7fbfa 55%, #eef7f3);
  border: 1px solid #e3efea;
  margin-bottom: 14px;
}
.ff-eyebrow {
  font-size: 12px;
  letter-spacing: 0.08em;
  color: #2f6a5f;
  margin-bottom: 6px;
}
.ff-title {
  font-size: 1.25rem;
  font-weight: 500;
  color: #122622;
  margin: 0 0 6px;
}
.ff-sub {
  margin: 0;
  color: #55706b;
  font-size: 0.9rem;
}
.ff-stats {
  display: flex;
  gap: 10px;
}
.ff-stat {
  min-width: 96px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e3efea;
  text-align: center;
}
.ff-stat b {
  display: block;
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
  font-size: 1.35rem;
  font-weight: 500;
  color: #122622;
}
.ff-stat span {
  font-size: 0.75rem;
  color: #55706b;
}
.ff-stat.ok b { color: #24705a; }
.ff-stat.warn b { color: #8a6212; }

.ff-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 14px;
}
.ff-hint {
  font-size: 12px;
  color: #7a918d;
  margin-left: 4px;
}

.ff-list {
  display: grid;
  gap: 10px;
}
.ff-card {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #e3efea;
  box-shadow: 0 1px 2px rgba(31, 74, 66, 0.05);
}
.ff-card-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.ff-order-no {
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
  font-weight: 500;
  color: #122622;
}
.ff-badge {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 500;
}
.ff-badge.ok { background: #eaf7f2; color: #24705a; }
.ff-badge.warn { background: #fef7e6; color: #8a6212; }
.ff-badge.bad { background: #fdecec; color: #ae3830; }
.ff-badge.info { background: #eff6fd; color: #2b6295; }

.ff-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 0.9rem;
  color: #1c322d;
  margin-bottom: 6px;
}
.ff-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}
.ff-step {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: #f3faf7;
  color: #7a918d;
}
.ff-step i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c5d6d1;
}
.ff-step.is-done {
  background: #eaf7f2;
  color: #24705a;
}
.ff-step.is-done i { background: #4a9b8c; }
.ff-step.is-active {
  background: #fef7e6;
  color: #8a6212;
}
.ff-step.is-active i { background: #d29b52; }
.ff-step.is-bad {
  background: #fdecec;
  color: #ae3830;
}
.ff-step.is-bad i { background: #ae3830; }
.ff-dot { color: #a9beba; }
.ff-money { font-family: var(--font-num, ui-monospace, Consolas, monospace); }
.ff-muted { color: #7a918d; font-size: 0.82rem; }
.ff-next {
  margin: 0;
  font-size: 0.86rem;
  color: #55706b;
}
.ff-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.ff-empty {
  padding: 32px 12px;
  text-align: center;
}

.ff-kv {
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}
.ff-kv > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px dashed #e3efea;
  font-size: 0.92rem;
}
.ff-kv span { color: #55706b; }
.ff-kv b { font-weight: 500; color: #122622; }

.ff-alert { margin-bottom: 12px; }
.ff-primary-row { margin: 12px 0 18px; }
.ff-docs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.ff-doc-result {
  background: #f7fbfa;
  border: 1px solid #e3efea;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 16px;
}
.ff-doc-title {
  font-weight: 500;
  margin-bottom: 8px;
  color: #122622;
}
.ff-doc-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}
.ff-verify {
  display: grid;
  gap: 8px;
}
.code-block {
  background: #10192a;
  color: #d7e2ef;
  border-radius: 8px;
  padding: 10px 12px;
  overflow: auto;
  max-height: 240px;
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
  font-size: 0.78rem;
}

/* 按压微反馈（#8） */
.ff-card-actions .ant-btn,
.ff-primary-row .ant-btn,
.ff-docs .ant-btn {
  transition: transform 160ms cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 160ms ease;
}
.ff-card-actions .ant-btn:active,
.ff-primary-row .ant-btn:active,
.ff-docs .ant-btn:active {
  transform: scale(0.96);
  box-shadow: inset 0 2px 6px rgba(31, 74, 66, 0.12);
}

@media (max-width: 720px) {
  .ff-stats { width: 100%; }
  .ff-stat { flex: 1; }
  .ff-card-actions { width: 100%; }
  .ff-card-actions .ant-btn { flex: 1; }
}
</style>
