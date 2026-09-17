/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="履约队列" subtitle="外贸7步履约生命周期与单证工作室" surface="elevated">
    <YdSearchBar @search="onSearch" @reset="onReset">
      <a-input v-model:value="query.search" placeholder="订单号/客户" allow-clear style="width: 180px" />
      <a-select v-model:value="query.status" placeholder="状态" allow-clear style="width: 130px">
        <a-select-option value="pending">待付款/待处理</a-select-option>
        <a-select-option value="deposit_received">定金已核销</a-select-option>
        <a-select-option value="in_production">生产排产中</a-select-option>
        <a-select-option value="shipped">已发货/海运中</a-select-option>
        <a-select-option value="completed">履约结清完成</a-select-option>
      </a-select>
      <template #extra>
        <a-button type="default" @click="goToGoodJobAnnex">
          <template #icon><LinkOutlined /></template>
          打开 GoodJob CRM 全景
        </a-button>
        <YdTableColumnSettings
          :columns="orderedColumns"
          :hidden-keys="hiddenColumnKeys"
          @toggle="toggleColumnVisibility"
          @move-up="moveColumnUp"
          @move-down="moveColumnDown"
          @reset="resetColumnLayout"
        />
        <YdTableToolbar
          :loading="loading"
          :target-ref="tablePanelRef"
          show-export
          @refresh="reload"
          @export="exportCsv"
        />
      </template>
    </YdSearchBar>

    <YdEmptyState
      v-if="!loading && !items.length"
      variant="inquiry"
      title="暂无履约任务"
      @action="goInquiries"
    />

    <div v-else ref="tablePanelRef" class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="visibleColumns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        @page-change="(p) => onPageChange(p.current, p.pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusTagColor(record.status)">
              {{ formatStatusLabel(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'total_amount'">
            <span class="font-medium">
              {{ record.currency || 'USD' }} {{ Number(record.total_amount || 0).toLocaleString() }}
            </span>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space size="small">
              <a-button type="link" size="small" @click="openOrderDetail(record)">
                履约详情
              </a-button>
              <a-dropdown>
                <template #overlay>
                  <a-menu @click="({ key }) => handleDocumentAction(record, key as string)">
                    <a-menu-item key="pi">生成形式发票 (PI)</a-menu-item>
                    <a-menu-item key="ci">生成商业发票 (CI)</a-menu-item>
                    <a-menu-item key="pl">生成装箱单 (PL)</a-menu-item>
                    <a-menu-item key="co">生成原产地证 (CO)</a-menu-item>
                  </a-menu>
                </template>
                <a-button type="link" size="small">
                  单证工作室 <DownOutlined />
                </a-button>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </YdDataTable>
    </div>

    <!-- 履约跟进与外贸7步操作抽屉 -->
    <a-drawer v-model:open="drawerOpen" title="外贸7步履约详情与单证套打" width="560">
      <template v-if="activeOrder">
        <a-descriptions bordered size="small" :column="2">
          <a-descriptions-item label="订单号" :span="2">
            <span class="font-bold text-gray-800">{{ activeOrder.order_number || activeOrder.id }}</span>
          </a-descriptions-item>
          <a-descriptions-item label="当前状态">
            <a-tag :color="getStatusTagColor(activeOrder.status)">
              {{ formatStatusLabel(activeOrder.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="总金额">
            {{ activeOrder.currency || 'USD' }} {{ Number(activeOrder.total_amount || 0).toLocaleString() }}
          </a-descriptions-item>
          <a-descriptions-item label="贸易术语">
            {{ activeOrder.incoterms || 'FOB Shenzhen' }}
          </a-descriptions-item>
          <a-descriptions-item label="定金状态">
            {{ activeOrder.deposit_amount ? `${activeOrder.currency || 'USD'} ${activeOrder.deposit_amount}` : '未核销' }}
          </a-descriptions-item>
          <a-descriptions-item label="提单号" :span="2">
            {{ activeOrder.bl_number || activeOrder.tracking_number || '待装船' }}
          </a-descriptions-item>
        </a-descriptions>

        <a-divider style="margin: 16px 0 12px">外贸7步履约流转</a-divider>

        <a-space direction="vertical" style="width: 100%" size="middle">
          <!-- 步骤 ④：定金核销 -->
          <div class="p-3 bg-gray-50 rounded border border-gray-200">
            <div class="flex justify-between items-center mb-1">
              <span class="font-semibold text-sm">④ 阶段：定金核销 (Verify Deposit)</span>
              <a-tag v-if="['deposit_received', 'in_production', 'shipped', 'completed'].includes(String(activeOrder.status))" color="success">
                已核销
              </a-tag>
            </div>
            <p class="text-xs text-gray-500 mb-2">核验买家支付定金流水，确认后转入生产排期。</p>
            <a-button
              type="primary"
              size="small"
              :loading="actionLoading === 'deposit'"
              :disabled="['deposit_received', 'in_production', 'shipped', 'completed'].includes(String(activeOrder.status))"
              @click="submitVerifyDeposit"
            >
              核销 30% 定金
            </a-button>
          </div>

          <!-- 步骤 ⑤：工厂排产 -->
          <div class="p-3 bg-gray-50 rounded border border-gray-200">
            <div class="flex justify-between items-center mb-1">
              <span class="font-semibold text-sm">⑤ 阶段：生产排期与跟单 (Production)</span>
              <a-tag v-if="['in_production', 'shipped', 'completed'].includes(String(activeOrder.status))" color="processing">
                已排产
              </a-tag>
            </div>
            <p class="text-xs text-gray-500 mb-2">通知工厂启动大货生产并设定预计出货交期。</p>
            <a-button
              type="primary"
              size="small"
              :loading="actionLoading === 'production'"
              :disabled="!['deposit_received', 'confirmed'].includes(String(activeOrder.status))"
              @click="submitStartProduction"
            >
              启动大货生产排期
            </a-button>
          </div>

          <!-- 步骤 ⑥：发货装箱与提单 -->
          <div class="p-3 bg-gray-50 rounded border border-gray-200">
            <div class="flex justify-between items-center mb-1">
              <span class="font-semibold text-sm">⑥ 阶段：发运装船与提单绑定 (Dispatch)</span>
              <a-tag v-if="['shipped', 'completed'].includes(String(activeOrder.status))" color="cyan">
                已发货
              </a-tag>
            </div>
            <p class="text-xs text-gray-500 mb-2">绑定集装箱柜号与正本海运提单 (B/L) 号码。</p>
            <a-button
              type="primary"
              size="small"
              :loading="actionLoading === 'dispatch'"
              :disabled="!['in_production', 'deposit_received'].includes(String(activeOrder.status))"
              @click="submitDispatch"
            >
              签发海运提单与出运
            </a-button>
          </div>

          <!-- 步骤 ⑦：尾款与结清 -->
          <div class="p-3 bg-gray-50 rounded border border-gray-200">
            <div class="flex justify-between items-center mb-1">
              <span class="font-semibold text-sm">⑦ 阶段：尾款核销与全链路闭环 (Settle)</span>
              <a-tag v-if="activeOrder.status === 'completed'" color="green">已结清完成</a-tag>
            </div>
            <p class="text-xs text-gray-500 mb-2">收回 70% 见提单副本尾款，全单履约交付完成。</p>
            <a-button
              type="primary"
              size="small"
              :loading="actionLoading === 'settle'"
              :disabled="String(activeOrder.status) !== 'shipped'"
              @click="submitSettleBalance"
            >
              核销尾款并结清全单
            </a-button>
          </div>
        </a-space>

        <!-- 单证预览与套打卡片 -->
        <a-divider style="margin: 16px 0 12px">GoodJob 外贸单证套打</a-divider>
        <div class="flex flex-wrap gap-2 mb-3">
          <a-button size="small" :loading="docLoading === 'pi'" @click="fetchOrderDoc('pi')">形式发票 (PI)</a-button>
          <a-button size="small" :loading="docLoading === 'ci'" @click="fetchOrderDoc('ci')">商业发票 (CI)</a-button>
          <a-button size="small" :loading="docLoading === 'pl'" @click="fetchOrderDoc('packing-list')">装箱单 (PL)</a-button>
          <a-button size="small" :loading="docLoading === 'co'" @click="fetchOrderDoc('certificate-of-origin')">原产地证 (CO)</a-button>
        </div>

        <div v-if="currentDocResult" class="p-3 bg-blue-50 border border-blue-200 rounded text-xs">
          <div class="flex justify-between items-center mb-2">
            <span class="font-bold text-blue-900">{{ currentDocTitle }}</span>
            <a-space size="small">
              <a-button size="small" type="link" @click="exportDocFile('html')">导出打印 HTML</a-button>
              <a-button size="small" type="link" @click="exportDocFile('docx')">导出 Word</a-button>
            </a-space>
          </div>
          <pre class="bg-white p-2 rounded border border-blue-100 text-gray-700 max-h-48 overflow-y-auto font-mono text-xs">{{ currentDocFormatted }}</pre>
        </div>
      </template>
    </a-drawer>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { DownOutlined, LinkOutlined } from '@ant-design/icons-vue';

import {
  YdDataTable,
  YdEmptyState,
  YdPage,
  YdSearchBar,
  YdTableColumnSettings,
  YdTableToolbar,
} from '@/components/youding';
import { useYoudingTable } from '@/composables/useYoudingTableBridge';
import { apiGet, apiPost } from '@/utils/api';
import { downloadTableCsv } from '@/utils/exportCsv';
import { adaptPaginatedResponse } from '@/utils/ydTableUtils';

const router = useRouter();
const tablePanelRef = ref<HTMLElement | null>(null);

const drawerOpen = ref(false);
const activeOrder = ref<Record<string, unknown> | null>(null);
const actionLoading = ref('');
const docLoading = ref('');
const currentDocTitle = ref('');
const currentDocResult = ref<Record<string, unknown> | null>(null);
const currentDocType = ref('');

const baseColumns = [
  { key: 'order_number', title: '订单号', dataIndex: 'order_number', align: 'center' },
  { key: 'total_amount', title: '订单金额', dataIndex: 'total_amount', align: 'right' },
  { key: 'status', title: '履约阶段', dataIndex: 'status', align: 'center' },
  { key: 'tracking_number', title: '提单/运单号', dataIndex: 'tracking_number', align: 'center' },
  { key: 'created_at', title: '创建时间', dataIndex: 'created_at', align: 'center' },
  { key: 'action', title: '操作', align: 'center', width: 220 },
];

const {
  loading,
  items,
  pagination,
  orderedColumns,
  visibleColumns,
  hiddenColumnKeys,
  query,
  search,
  reset,
  reload,
  onPageChange,
  toggleColumnVisibility,
  moveColumnUp,
  moveColumnDown,
  resetColumnLayout,
} = useYoudingTable<Record<string, unknown>, { search?: string; status?: string }>({
  columnOrderKey: 'client-fulfillment-queue-cols-v2',
  columns: baseColumns,
  fetcher: async (q) => {
    const raw = await apiGet<Record<string, unknown>[]>('/orders', {
      skip: ((q.page || 1) - 1) * (q.pageSize || 10),
      limit: q.pageSize || 10,
      status: q.status || undefined,
    });
    const { rows, total } = adaptPaginatedResponse<Record<string, unknown>>(raw);
    return { items: rows, total };
  },
});

function onSearch() {
  void search();
}

function onReset() {
  query.status = undefined;
  query.search = undefined;
  void reset();
}

function goInquiries() {
  router.push('/client/inquiries');
}

function goToGoodJobAnnex() {
  router.push('/client/annex/goodjob');
}

function formatStatusLabel(status: unknown): string {
  const s = String(status || '').toLowerCase();
  const map: Record<string, string> = {
    pending: '待付款/待处理',
    deposit_received: '定金已核销',
    in_production: '生产排产中',
    shipped: '已出运/提单已签发',
    completed: '7步履约完成',
    cancelled: '已取消',
  };
  return map[s] || s || '未知';
}

function getStatusTagColor(status: unknown): string {
  const s = String(status || '').toLowerCase();
  const map: Record<string, string> = {
    pending: 'orange',
    deposit_received: 'blue',
    in_production: 'purple',
    shipped: 'cyan',
    completed: 'green',
    cancelled: 'default',
  };
  return map[s] || 'default';
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
    // 保留列表传入的基础数据
  }
}

async function handleDocumentAction(record: Record<string, unknown>, docType: string) {
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
    currentDocTitle.value = String(data.doc_type || endpointDoc.toUpperCase()) + ' 单据数据';
    message.success(`${currentDocTitle.value} 生成成功`);
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '单据生成失败');
  } finally {
    docLoading.value = '';
  }
}

const currentDocFormatted = computed(() => {
  if (!currentDocResult.value) return '';
  return JSON.stringify(currentDocResult.value, null, 2);
});

function exportDocFile(format: 'html' | 'docx') {
  if (!activeOrder.value?.id) return;
  const id = String(activeOrder.value.id);
  const typeKey = currentDocType.value === 'packing-list' ? 'pl' : currentDocType.value === 'certificate-of-origin' ? 'co' : (currentDocType.value || 'pi');
  window.open(`/api/v1/orders/${id}/documents/${typeKey}/export?format=${format}`, '_blank');
}

async function submitVerifyDeposit() {
  if (!activeOrder.value?.id) return;
  actionLoading.value = 'deposit';
  try {
    await apiPost(`/orders/${activeOrder.value.id}/verify-deposit`, {
      deposit_ratio: 30,
      payment_reference: `TT-DEP-${Date.now()}`,
    });
    message.success('定金核销成功，已更新为 deposit_received');
    await openOrderDetail(activeOrder.value);
    await reload();
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '定金核销失败');
  } finally {
    actionLoading.value = '';
  }
}

async function submitStartProduction() {
  if (!activeOrder.value?.id) return;
  actionLoading.value = 'production';
  try {
    const dateStr = new Date(Date.now() + 25 * 86400000).toISOString().slice(0, 10);
    await apiPost(`/orders/${activeOrder.value.id}/start-production`, {
      estimated_delivery: dateStr,
      production_notes: '工厂已确认原料备齐，安排在1号线生产',
    });
    message.success('生产排产已启动，已更新为 in_production');
    await openOrderDetail(activeOrder.value);
    await reload();
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '生产排期失败');
  } finally {
    actionLoading.value = '';
  }
}

async function submitDispatch() {
  if (!activeOrder.value?.id) return;
  actionLoading.value = 'dispatch';
  try {
    await apiPost(`/orders/${activeOrder.value.id}/dispatch`, {
      bl_number: `COSCO-${Date.now().toString().slice(-8)}`,
      container_no: `CSXU${Date.now().toString().slice(-7)}`,
      carrier: 'COSCO SHIPPING',
      gross_weight: 18500.0,
      volume: 48.5,
    });
    message.success('出运与海运提单已绑定，已更新为 shipped');
    await openOrderDetail(activeOrder.value);
    await reload();
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '出运签发失败');
  } finally {
    actionLoading.value = '';
  }
}

async function submitSettleBalance() {
  if (!activeOrder.value?.id) return;
  actionLoading.value = 'settle';
  try {
    await apiPost(`/orders/${activeOrder.value.id}/settle-balance`, {
      payment_reference: `TT-FINAL-${Date.now()}`,
    });
    message.success('尾款核销结清，订单7步全链路履约完成！');
    await openOrderDetail(activeOrder.value);
    await reload();
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '尾款核销失败');
  } finally {
    actionLoading.value = '';
  }
}

function exportCsv() {
  if (!items.value.length) {
    message.warning('暂无数据可导出');
    return;
  }
  downloadTableCsv(
    `fulfillment_queue_${new Date().toISOString().slice(0, 10)}.csv`,
    ['订单号', '金额', '状态', '提单号', '创建时间'],
    items.value.map((r) => [
      String(r.order_number ?? r.id ?? ''),
      String(r.total_amount ?? ''),
      String(r.status ?? ''),
      String(r.tracking_number ?? ''),
      String(r.created_at ?? ''),
    ]),
  );
  message.success(`已导出 ${items.value.length} 条`);
}
</script>
