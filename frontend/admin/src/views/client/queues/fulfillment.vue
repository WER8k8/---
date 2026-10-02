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
            <div class="ff-steps" :aria-label="'外贸7步进度 ' + progressLabel(row)">
              <span v-for="(st, si) in stepList" :key="st.key" class="ff-step" :class="stepClass(row, si)" :title="st.hint">
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
                  <a-menu-item key="pi">形式发票 (PI)</a-menu-item>
                  <a-menu-item key="ci">商业发票 (CI)</a-menu-item>
                  <a-menu-item key="pl">装箱单 (Packing List)</a-menu-item>
                  <a-menu-item key="co">原产地证草案 (CO)</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
        </article>
      </div>
    </a-spin>

    <!-- ③ 详情 / 单证（浮层，全闭环操作台） -->
    <a-drawer
      v-model:open="drawerOpen"
      :width="640"
      :title="activeOrder?.order_number ? `订单履约工作台 · ${activeOrder.order_number}` : '订单详情'"
      placement="right"
    >
      <div v-if="activeOrder" class="ff-drawer">
        <div class="ff-kv">
          <div><span>客户</span><b>{{ (activeOrder as any).customer_name || '—' }}</b></div>
          <div><span>订单总额</span><b>{{ formatMoney((activeOrder as any).total_amount) }} {{ (activeOrder as any).currency || 'USD' }}</b></div>
          <div><span>履约阶段</span><b><span class="ff-badge" :class="statusLevel(activeOrder.status)">{{ formatStatusLabel(activeOrder.status) }}</span></b></div>
          <div><span>提单/运单</span><b>{{ (activeOrder as any).tracking_number || (activeOrder as any).bl_number || '—' }}</b></div>
        </div>

        <a-alert type="info" show-icon class="ff-alert" message="下一步建议" :description="nextHint(activeOrder)" />

        <div class="ff-primary-row">
          <a-button
            type="primary"
            size="large"
            block
            :loading="hermesLoading"
            @click="dispatchGoldenPathFulfillment(activeOrder)"
          >
            爱马仕（Hermes L2）智能推进这一步
          </a-button>
        </div>

        <!-- 外贸 7 步履约专属推进器 -->
        <a-divider orientation="left" plain>外贸 7 步状态跃迁推进</a-divider>
        <div class="ff-stepper-box">
          <div class="ff-stepper-header">
            <span>当前步：<b>{{ progressLabel(activeOrder) }}</b></span>
          </div>
          <div class="ff-verify golden-actions-grid">
            <a-button size="large" :loading="docLoading==='pi'" @click="handleDocumentAction(activeOrder, 'pi')">
              1 · 出具形式发票 (PI)
            </a-button>
            <a-button size="large" :loading="actionLoading==='deposit'" @click="markDeposit">
              2 · 记定金已收 (30%)
            </a-button>
            <a-button size="large" :loading="actionLoading==='production'" @click="markProduction">
              3 · 下达排产生产 (PO)
            </a-button>
            <a-button size="large" :loading="actionLoading==='ship'" @click="markShipped">
              4 · 登记已发货 (B/L)
            </a-button>
            <a-button size="large" :loading="docLoading==='ci'" @click="handleDocumentAction(activeOrder, 'ci')">
              5 · 出具商业发票 (CI)
            </a-button>
            <a-button size="large" :loading="actionLoading==='balance'" @click="markBalance">
              6 · 记尾款已收 (70%)
            </a-button>
            <a-button type="primary" size="large" :loading="actionLoading==='win'" style="grid-column: span 2;" @click="markWon">
              7 · 结案成单（沉淀至经验库与经营看板）
            </a-button>
          </div>
        </div>

        <!-- 单证自动化套打中心 -->
        <a-divider orientation="left" plain>外贸单证套打中心</a-divider>
        <div class="ff-docs">
          <a-button size="middle" :type="currentDocType==='pi' ? 'primary' : 'default'" :loading="docLoading==='pi'" @click="handleDocumentAction(activeOrder, 'pi')">
            形式发票 (PI)
          </a-button>
          <a-button size="middle" :type="currentDocType==='ci' ? 'primary' : 'default'" :loading="docLoading==='ci'" @click="handleDocumentAction(activeOrder, 'ci')">
            商业发票 (CI)
          </a-button>
          <a-button size="middle" :type="currentDocType==='packing-list' ? 'primary' : 'default'" :loading="docLoading==='packing-list'" @click="handleDocumentAction(activeOrder, 'pl')">
            装箱单 (Packing List)
          </a-button>
          <a-button size="middle" :type="currentDocType==='certificate-of-origin' ? 'primary' : 'default'" :loading="docLoading==='certificate-of-origin'" @click="handleDocumentAction(activeOrder, 'co')">
            原产地证草案 (CO)
          </a-button>
        </div>

        <!-- 单证可视化卡片展示 -->
        <div v-if="currentDocResult" class="ff-doc-result">
          <div class="ff-doc-header">
            <div class="ff-doc-title">
              <span class="ff-doc-badge">{{ currentDocTitle }}</span>
              <span class="ff-doc-no">{{ (currentDocResult as any).document_number || (currentDocResult as any).invoice_number || (currentDocResult as any).co_number || '' }}</span>
            </div>
            <div class="ff-doc-view-toggle">
              <a-radio-group v-model:value="docViewMode" size="small">
                <a-radio-button value="card">单据卡片</a-radio-button>
                <a-radio-button value="json">数据源</a-radio-button>
              </a-radio-group>
            </div>
          </div>

          <!-- 卡片视图 -->
          <div v-if="docViewMode === 'card'" class="ff-doc-card-view">
            <!-- 双方信息 -->
            <div class="ff-doc-parties">
              <div class="ff-party-box">
                <div class="ff-party-tag">SELLER / 出口方</div>
                <div class="ff-party-name">{{ (currentDocResult as any).seller?.name || (currentDocResult as any).exporter?.name || '优丁出海供应链' }}</div>
                <div class="ff-party-sub">{{ (currentDocResult as any).seller?.address || (currentDocResult as any).exporter?.address || 'Guangdong, China' }}</div>
              </div>
              <div class="ff-party-box">
                <div class="ff-party-tag">BUYER / 进口方</div>
                <div class="ff-party-name">{{ (currentDocResult as any).buyer?.name || (currentDocResult as any).consignee?.name || (currentDocResult as any).buyer?.company || '海外买家' }}</div>
                <div class="ff-party-sub">{{ (currentDocResult as any).buyer?.address || (currentDocResult as any).consignee?.address || 'Overseas Port' }}</div>
              </div>
            </div>

            <!-- 条款行 -->
            <div class="ff-doc-terms">
              <span><b>贸易术语:</b> {{ (currentDocResult as any).terms?.delivery_terms || (currentDocResult as any).incoterms || 'FOB Shenzhen' }}</span>
              <span><b>付款条款:</b> {{ (currentDocResult as any).terms?.payment_terms || (currentDocResult as any).payment_terms || '30% Deposit, 70% before Shipment' }}</span>
              <span v-if="(currentDocResult as any).shipping?.port_of_loading"><b>起运港:</b> {{ (currentDocResult as any).shipping?.port_of_loading }}</span>
              <span v-if="(currentDocResult as any).shipping?.port_of_discharge"><b>目的港:</b> {{ (currentDocResult as any).shipping?.port_of_discharge }}</span>
            </div>

            <!-- 明细表格 -->
            <div class="ff-doc-table-wrap">
              <table class="ff-doc-table">
                <thead>
                  <tr>
                    <th>品名 Description</th>
                    <th style="text-align: right;">数量</th>
                    <th style="text-align: right;">单价</th>
                    <th style="text-align: right;">金额</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(it, lidx) in ((currentDocResult as any).line_items || (currentDocResult as any).lines || (currentDocResult as any).items || [])" :key="lidx">
                    <td>{{ it.description || it.product_name || '外贸定制商品' }}</td>
                    <td style="text-align: right;">{{ it.quantity }} {{ it.unit || 'pcs' }}</td>
                    <td style="text-align: right;">{{ formatMoney(it.unit_price) }}</td>
                    <td style="text-align: right;"><b>{{ formatMoney(it.amount || ((it.quantity || 1) * (it.unit_price || 0))) }}</b></td>
                  </tr>
                  <tr v-if="!((currentDocResult as any).line_items || (currentDocResult as any).lines || (currentDocResult as any).items)?.length">
                    <td colspan="4" style="text-align: center; color: #888;">详见单据货物总则清单</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 汇总与印章 -->
            <div class="ff-doc-footer-row">
              <div class="ff-doc-stamp-box">
                <div class="ff-stamp-circle">
                  <span>YOUDING</span>
                  <b>CERTIFIED</b>
                  <small>OFFICIAL SEAL</small>
                </div>
              </div>
              <div class="ff-doc-amounts">
                <div v-if="(currentDocResult as any).financials?.total_amount || (currentDocResult as any).total_amount">
                  <span>总金额:</span>
                  <b>{{ formatMoney((currentDocResult as any).financials?.total_amount || (currentDocResult as any).total_amount) }} {{ (currentDocResult as any).currency || 'USD' }}</b>
                </div>
                <div v-if="(currentDocResult as any).financials?.deposit_paid || (currentDocResult as any).deposit_paid">
                  <span>已收定金:</span>
                  <span class="text-green">- {{ formatMoney((currentDocResult as any).financials?.deposit_paid || (currentDocResult as any).deposit_paid) }}</span>
                </div>
                <div v-if="(currentDocResult as any).financials?.balance_due || (currentDocResult as any).balance_due">
                  <span>待付尾款:</span>
                  <b class="text-red">{{ formatMoney((currentDocResult as any).financials?.balance_due || (currentDocResult as any).balance_due) }}</b>
                </div>
              </div>
            </div>
          </div>

          <!-- 源码视图 -->
          <pre v-else class="code-block">{{ currentDocFormatted }}</pre>

          <div class="ff-doc-actions">
            <a-button type="primary" @click="exportDocFile('html')">在独立窗口打印 / 预览 (HTML)</a-button>
            <a-button @click="exportDocFile('docx')">导出 Word 格式 (.docx)</a-button>
          </div>
        </div>

        <a-divider orientation="left" plain>排产与核销信息登记</a-divider>
        <div class="ff-verify">
          <div class="ff-verify-row">
            <a-input v-model:value="verifyForm.deposit_ref" placeholder="定金水单号（电汇参考号）" />
            <a-input-number
              v-model:value="verifyForm.deposit_ref_amount"
              placeholder="定金金额（默认 30%）"
              :min="0"
              style="width: 100%"
            />
          </div>
          <div class="ff-verify-row">
            <a-date-picker
              v-model:value="productionForm.estimated_delivery_date"
              placeholder="预计工厂交期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
            <a-input v-model:value="productionForm.production_notes" placeholder="生产批次/排产备注" />
          </div>
          <div class="ff-verify-row">
            <a-input v-model:value="verifyForm.bl_number" placeholder="海运提单号 (B/L)" />
            <a-input v-model:value="verifyForm.container_no" placeholder="集装箱柜号" />
          </div>
          <a-input v-model:value="verifyForm.settle_ref" placeholder="尾款水单凭证号" />
          <a-button size="large" :loading="actionLoading==='verify'" @click="verifyFulfillment">统一保存核销与调度信息</a-button>
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
const docViewMode = ref<'card' | 'json'>('card');

const verifyForm = ref({
  deposit_ref: '',
  deposit_ref_amount: undefined as number | undefined,
  bl_number: '',
  container_no: '',
  settle_ref: '',
});

const productionForm = ref({
  estimated_delivery_date: '',
  production_notes: '',
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
    ? '外贸 7 步全自动化推进：询盘、核价、PI发票、定金核销、排产、CI/PL单证、尾款结案。'
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
    pending: '待处理/待定金',
    deposit_received: '定金已收(30%)',
    in_production: '工厂生产中',
    shipped: '已出运(提单生效)',
    completed: '已结清成单',
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
  if (s === 'pending') return '下一步：确认定金核销，或出具 PI 形式发票发送给买方。';
  if (s === 'deposit_received') return '下一步：定金已到账，请点击「下达排产生产 (PO)」启动工厂备料。';
  if (s === 'in_production') return '下一步：产线完工，出具商业发票 (CI) 与装箱单 (PL)，登记发货出运。';
  if (s === 'shipped') return '下一步：提单已交割，登记 70% 尾款核销流水，完成全单结案。';
  if (s === 'completed') return '这单已全额结清，经验库沉淀完毕，经营概览可见。';
  return '点「下一步」让系统自动推进当前阶段。';
}

const stepList = [
  { key: 'inquiry', label: '1·询盘', hint: '商机捕获' },
  { key: 'quote', label: '2·核价', hint: 'BOQ算料成单' },
  { key: 'pi', label: '3·发票', hint: '形式发票出具' },
  { key: 'deposit', label: '4·定金', hint: '30%首款核销' },
  { key: 'production', label: '5·生产', hint: '工厂排产跟单' },
  { key: 'shipping', label: '6·发运', hint: '提单/装箱单 CI+PL' },
  { key: 'settled', label: '7·尾款', hint: '70%尾款与结案' },
];

function stepClass(row: Record<string, unknown> | null, idx: number): string {
  const s = String(row?.status || '').toLowerCase();
  const map: Record<string, number> = {
    pending: 2,           // 待定金/形式发票
    deposit_received: 3,  // 第4步定金已核销，待排产
    in_production: 4,     // 第5步生产中
    shipped: 5,           // 第6步已出运
    completed: 6,         // 第7步尾款已结清成单
    cancelled: -1,
  };
  const stage = map[s] ?? 1;
  if (s === 'cancelled') return 'is-bad';
  if (idx < stage) return 'is-done';
  if (idx === stage) return 'is-active';
  return '';
}

function progressLabel(row: Record<string, unknown> | null): string {
  const s = String(row?.status || '').toLowerCase();
  const map: Record<string, string> = {
    pending: '3/7 待形式发票 / 待付定金',
    deposit_received: '4/7 定金已收 / 待下达生产',
    in_production: '5/7 工厂排产中',
    shipped: '6/7 货物出运装船 / 提单在途',
    completed: '7/7 尾款全额结清 / 履约结案',
    cancelled: '已取消',
  };
  return map[s] || '2/7 推进中';
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
  const endpointMap: Record<string, string> = {
    pi: 'pi',
    ci: 'ci',
    pl: 'packing-list',
    co: 'certificate-of-origin',
  };
  await fetchOrderDoc(endpointMap[docType] || docType);
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
    const nameMap: Record<string, string> = {
      pi: 'PROFORMA INVOICE 形式发票',
      ci: 'COMMERCIAL INVOICE 商业发票',
      'packing-list': 'PACKING LIST 装箱单',
      'certificate-of-origin': 'CERTIFICATE OF ORIGIN 原产地证',
    };
    currentDocTitle.value = nameMap[endpointDoc] || `${String(data.doc_type || endpointDoc.toUpperCase())} 单据`;
    message.success(`${currentDocTitle.value} 已成功生成并准备就绪`);
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
    message.success('核销与调度信息已统一登记');
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
        note: verifyForm.value.deposit_ref || '定金已收（30%首款核销完成）',
      });
    }
    message.success('已记定金(30%) → 进入生产/备料阶段');
    await reload();
    if (activeOrder.value?.id) await openOrderDetail(activeOrder.value as Record<string, unknown>);
  } catch (e) {
    message.error(e instanceof Error ? e.message : '定金登记失败');
  } finally {
    actionLoading.value = '';
  }
}

async function markProduction() {
  const orderId = orderIdOf(activeOrder.value);
  if (!orderId) return message.warning('缺少订单编号');
  actionLoading.value = 'production';
  try {
    await apiPost(`/orders/${orderId}/start-production`, {
      estimated_delivery: productionForm.value.estimated_delivery_date || undefined,
      production_notes: productionForm.value.production_notes || undefined,
    });
    message.success('工厂排产已下达 (Step 5) → 进入生产跟单');
    await reload();
    if (activeOrder.value?.id) await openOrderDetail(activeOrder.value as Record<string, unknown>);
  } catch (e) {
    message.error(e instanceof Error ? e.message : '下达排产失败');
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
    message.success('已登记发货出运 (Step 6) → 提单与集装箱号已绑定');
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
  padding: 14px;
  margin-bottom: 16px;
}
.ff-doc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e3efea;
}
.ff-doc-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #122622;
}
.ff-doc-badge {
  font-size: 0.85rem;
  font-weight: 600;
  color: #24705a;
  background: #eaf7f2;
  padding: 2px 8px;
  border-radius: 6px;
}
.ff-doc-no {
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
  font-size: 0.88rem;
  color: #55706b;
}

.ff-doc-card-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #fff;
  border: 1px solid #e3efea;
  border-radius: 10px;
  padding: 14px;
  box-shadow: 0 1px 3px rgba(31, 74, 66, 0.04);
}
.ff-doc-parties {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.ff-party-box {
  background: #fafcfb;
  border: 1px dashed #d5e5e0;
  border-radius: 8px;
  padding: 10px;
}
.ff-party-tag {
  font-size: 0.72rem;
  font-weight: 600;
  color: #55706b;
  letter-spacing: 0.05em;
  margin-bottom: 4px;
}
.ff-party-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: #122622;
}
.ff-party-sub {
  font-size: 0.78rem;
  color: #7a918d;
  margin-top: 2px;
}

.ff-doc-terms {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  background: #f3faf7;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
  color: #2f6a5f;
}
.ff-doc-terms span b {
  color: #122622;
}

.ff-doc-table-wrap {
  overflow-x: auto;
}
.ff-doc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}
.ff-doc-table th {
  background: #fafcfb;
  color: #55706b;
  font-weight: 500;
  padding: 6px 8px;
  border-bottom: 1px solid #e3efea;
  text-align: left;
}
.ff-doc-table td {
  padding: 8px;
  border-bottom: 1px solid #f0f6f4;
  color: #1c322d;
}

.ff-doc-footer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px dashed #e3efea;
}
.ff-doc-stamp-box {
  display: flex;
  align-items: center;
}
.ff-stamp-circle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 76px;
  height: 76px;
  border: 2px dashed #b83c30;
  color: #b83c30;
  border-radius: 50%;
  transform: rotate(-10deg);
  opacity: 0.82;
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
  font-size: 0.65rem;
  line-height: 1.1;
  text-align: center;
}
.ff-stamp-circle b {
  font-size: 0.72rem;
  letter-spacing: 0.05em;
}
.ff-doc-amounts {
  display: grid;
  gap: 4px;
  text-align: right;
  font-size: 0.85rem;
}
.ff-doc-amounts b {
  font-family: var(--font-num, ui-monospace, Consolas, monospace);
  margin-left: 6px;
}
.text-green { color: #24705a; }
.text-red { color: #b83c30; }

.ff-stepper-box {
  background: #f9fdfb;
  border: 1px solid #e3efea;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
}
.ff-stepper-header {
  font-size: 0.85rem;
  color: #55706b;
  margin-bottom: 8px;
}
.golden-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.ff-verify-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.ff-doc-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
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
.ff-docs .ant-btn,
.golden-actions-grid .ant-btn {
  transition: transform 160ms cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 160ms ease;
}
.ff-card-actions .ant-btn:active,
.ff-primary-row .ant-btn:active,
.ff-docs .ant-btn:active,
.golden-actions-grid .ant-btn:active {
  transform: scale(0.96);
  box-shadow: inset 0 2px 6px rgba(31, 74, 66, 0.12);
}

@media (max-width: 720px) {
  .ff-stats { width: 100%; }
  .ff-stat { flex: 1; }
  .ff-card-actions { width: 100%; }
  .ff-card-actions .ant-btn { flex: 1; }
  .golden-actions-grid { grid-template-columns: 1fr; }
  .golden-actions-grid .ant-btn { grid-column: span 1 !important; }
  .ff-doc-parties { grid-template-columns: 1fr; }
  .ff-verify-row { grid-template-columns: 1fr; }
}
</style>
