/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="租户管理" subtitle="多租户隔离与资源配额管理" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="openCreateModal">+ 创建租户</a-button>
    </template>

    <!-- 统计卡片 -->
    <YdStatsRow :cols="6">
      <YdStatsCard label="总租户数" :value="stats.total_tenants" tone="default" />
      <YdStatsCard label="活跃" :value="stats.active_tenants" tone="blue" />
      <YdStatsCard label="试用中" :value="stats.trial_tenants" tone="green" />
      <YdStatsCard label="已暂停" :value="stats.suspended_tenants" tone="amber" />
      <YdStatsCard label="即将到期" :value="stats.expiring_soon" tone="purple" />
      <YdStatsCard label="本月实收" :value="formatMonthlyRevenue(stats.monthly_revenue)" tone="default" />
    </YdStatsRow>

    <!-- 搜索栏 -->
    <YdSearchBar @search="onSearch" @reset="onReset">
      <a-input v-model:value="query.search" placeholder="搜索租户名称/域名/邮箱" allow-clear style="width: 260px" />
      <a-select v-model:value="query.status" placeholder="状态" allow-clear style="width: 120px">
        <a-select-option value="">全部</a-select-option>
        <a-select-option value="active">活跃</a-select-option>
        <a-select-option value="trial">试用</a-select-option>
        <a-select-option value="suspended">暂停</a-select-option>
        <a-select-option value="cancelled">已取消</a-select-option>
      </a-select>
      <a-select v-model:value="query.plan" placeholder="套餐" allow-clear style="width: 140px">
        <a-select-option value="">全部</a-select-option>
        <a-select-option v-for="p in planOptions" :key="p.id" :value="p.id">
          {{ p.name }}
        </a-select-option>
      </a-select>
      <template #extra>
        <YdTableColumnSettings
          :columns="orderedColumns"
          :hidden-keys="hiddenColumnKeys"
          @toggle="toggleColumnVisibility"
          @move-up="moveColumnUp"
          @move-down="moveColumnDown"
          @reset="resetColumnLayout"
        />
        <YdTableToolbar :loading="loading" :target-ref="tablePanelRef" :show-export="false" @refresh="reload" />
      </template>
    </YdSearchBar>

    <!-- 批量操作栏 -->
    <div v-if="selectedRowKeys.length > 0" class="batch-action-bar">
      <a-alert type="info" show-icon>
        <template #message>
          已选择 <strong>{{ selectedRowKeys.length }}</strong> 个租户
        </template>
        <template #description>
          <a-space>
            <a-button size="small" type="primary" @click="batchResume">批量恢复</a-button>
            <a-button size="small" danger @click="batchSuspend">批量暂停</a-button>
            <a-divider type="vertical" />
            <a-button size="small" @click="batchExport">导出选中</a-button>
            <a-button size="small" type="text" @click="selectedRowKeys = []">取消选择</a-button>
          </a-space>
        </template>
      </a-alert>
    </div>

    <!-- 租户表格 -->
    <div ref="tablePanelRef" class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="visibleColumns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        :table-props="{
          rowKey: 'id',
          size: tableSize,
          rowSelection: {
            selectedRowKeys,
            onChange: (keys) => { selectedRowKeys = keys as string[]; },
          },
        }"
        @page-change="(p) => onPageChange(p.current, p.pageSize)"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <a @click="openDetail(record)" class="tenant-name-link">{{ record.name }}</a>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">
              {{ statusLabel(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'plan'">
            <a-tag :color="planColor(record.plan_code)">{{ record.plan_name || '--' }}</a-tag>
          </template>
          <template v-else-if="column.key === 'trial_ends_at' || column.key === 'created_at'">
            {{ formatDate(record[column.key]) }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" type="link" class="yd-action-link" @click="openDetail(record)">详情</a-button>
              <a-button
                size="small"
                type="link"
                class="yd-action-link"
                @click="openAitoearnModal(record)"
              >
                AiToEarn
              </a-button>
              <a-button
                size="small"
                type="link"
                :class="record.status === 'suspended' ? 'yd-action-link-success' : 'yd-action-link-warn'"
                @click="toggleStatus(record)"
              >
                {{ record.status === 'suspended' ? '恢复' : '暂停' }}
              </a-button>
            </a-space>
          </template>
        </template>
      </YdDataTable>
    </div>

    <!-- ==================== 创建租户 Modal ==================== -->
    <a-modal
      v-model:open="createModalOpen"
      title="创建租户"
      :confirm-loading="creating"
      @ok="handleCreate"
      width="560px"
    >
      <a-form :model="createForm" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="公司/租户名称" required>
              <a-input v-model:value="createForm.name" placeholder="输入公司名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="子域名" required>
              <a-input v-model:value="createForm.domain" placeholder="如 my-company" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="联系人">
              <a-input v-model:value="createForm.contact_name" placeholder="联系人姓名" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="联系邮箱">
              <a-input v-model:value="createForm.contact_email" placeholder="contact@company.com" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="联系电话">
              <a-input v-model:value="createForm.contact_phone" placeholder="手机或座机" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="套餐" required>
              <a-select v-model:value="createForm.plan_id" placeholder="选择套餐">
                <a-select-option v-for="p in planOptions" :key="p.id" :value="p.id">
                  {{ p.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="初始状态">
          <a-radio-group v-model:value="createForm.status">
            <a-radio-button value="trial">试用</a-radio-button>
            <a-radio-button value="active">活跃</a-radio-button>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="aitoearnModalOpen"
      title="AiToEarn 矩阵槽位"
      :confirm-loading="aitoearnAssigning"
      ok-text="自动分配"
      cancel-text="关闭"
      @ok="handleAutoAssignAitoearn"
    >
      <p v-if="aitoearnTenant">租户：<strong>{{ aitoearnTenant.name }}</strong>（{{ aitoearnTenant.domain }}）</p>
      <a-alert
        v-if="aitoearnPoolHint"
        type="info"
        show-icon
        :message="aitoearnPoolHint"
        class="mb-4"
      />
      <template v-if="aitoearnPoolLoading">
        <SkeletonCard variant="table" :rows="3" />
      </template>
      <template v-else>
        <p>可用未分配账号：{{ aitoearnPool.length }} 个</p>
        <ul v-if="aitoearnPool.length" class="aitoearn-pool-list">
          <li v-for="acc in aitoearnPool.slice(0, 8)" :key="acc.account_id">
            {{ acc.nickname }} · {{ acc.platform }} · {{ acc.account_id.slice(0, 12) }}…
          </li>
        </ul>
      </template>
      <p class="aitoearn-footnote">分配后租户可在「内容分发」同步矩阵号并真发视频/回评。</p>
    </a-modal>

    <!-- ==================== 租户详情 Drawer ==================== -->
    <a-drawer
      v-model:open="detailDrawerOpen"
      :title="detailTenant?.name || '租户详情'"
      placement="right"
      width="520"
    >
      <template v-if="detailTenant">
        <a-tabs v-model:activeKey="detailTab" size="small">
          <a-tab-pane key="overview" tab="基本信息">
            <a-descriptions :column="1" size="small" bordered class="mb-4">
              <a-descriptions-item label="租户ID">
                <span style="font-family:monospace;font-size:12px">{{ detailTenant.id }}</span>
              </a-descriptions-item>
              <a-descriptions-item label="名称">{{ detailTenant.name }}</a-descriptions-item>
              <a-descriptions-item label="域名">{{ detailTenant.domain || '--' }}</a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag :color="statusColor(detailTenant.status)">{{ statusLabel(detailTenant.status) }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="套餐">
                {{ detailTenant.plan_name || '--' }}
                <a-tag :color="planColor(detailTenant.plan_code)" class="ml-2">{{ detailTenant.plan_code }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="联系人">{{ detailTenant.contact_name || '--' }}</a-descriptions-item>
              <a-descriptions-item label="联系邮箱">{{ detailTenant.contact_email || '--' }}</a-descriptions-item>
              <a-descriptions-item label="联系电话">{{ detailTenant.contact_phone || '--' }}</a-descriptions-item>
              <a-descriptions-item label="激活状态">
                <a-tag :color="detailTenant.is_active ? 'green' : 'default'">{{ detailTenant.is_active ? '已激活' : '未激活' }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="注册时间">{{ formatDate(detailTenant.created_at) }}</a-descriptions-item>
              <a-descriptions-item label="到期时间">{{ trialEndLabel(detailTenant) }}</a-descriptions-item>
            </a-descriptions>

            <a-divider orientation="left" orientation-margin="0">用量统计</a-divider>
            <a-descriptions :column="1" size="small" bordered>
              <a-descriptions-item label="AI 配额用量">{{ detailTenant.ai_quota_used || 0 }}</a-descriptions-item>
              <a-descriptions-item label="存储用量">{{ formatStorage(detailTenant.storage_used) }}</a-descriptions-item>
            </a-descriptions>
          </a-tab-pane>

          <a-tab-pane key="settings" tab="设置">
            <a-form layout="vertical" :model="editForm" size="small">
              <a-form-item label="状态">
                <a-select v-model:value="editForm.status">
                  <a-select-option value="trial">试用</a-select-option>
                  <a-select-option value="active">活跃</a-select-option>
                  <a-select-option value="suspended">暂停</a-select-option>
                  <a-select-option value="cancelled">已取消</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="套餐">
                <a-select v-model:value="editForm.plan_id">
                  <a-select-option v-for="p in planOptions" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="激活状态">
                <a-switch v-model:checked="editForm.is_active" />
              </a-form-item>
              <a-form-item>
                <a-button type="primary" :loading="saving" @click="saveDetail">保存修改</a-button>
              </a-form-item>
            </a-form>
          </a-tab-pane>
        </a-tabs>
      </template>
    </a-drawer>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { storeToRefs } from 'pinia';
import {
  YdDataTable,
  YdPage,
  YdSearchBar,
  YdStatsCard,
  YdStatsRow,
  YdTableColumnSettings,
  YdTableToolbar,
} from '@/components/youding';
import { useYoudingTable } from '@/composables/useYoudingTableBridge';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import { apiGet, apiPost, apiPut } from '@/utils/api';
import SkeletonCard from '@/components/common/SkeletonCard.vue';

// ============================================================================
// 类型定义
// ============================================================================
interface TenantPlan {
  id: string;
  name: string;
  code: string;
}

interface TenantStats {
  total_tenants: number;
  active_tenants: number;
  trial_tenants: number;
  suspended_tenants: number;
  expiring_soon: number;
  monthly_revenue: number;
}

interface TenantRecord {
  id: string;
  name: string;
  contact_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  domain: string;
  plan_id: string;
  plan_code: string;
  plan_name: string;
  status: string;
  trial_ends_at: string | null;
  ai_quota_used: number;
  storage_used: number;
  is_active: boolean;
  created_at: string;
}

// ============================================================================
// 套餐选项
// ============================================================================
const planOptions = ref<TenantPlan[]>([]);

async function loadPlanOptions() {
  try {
    const data = await apiGet<TenantPlan[]>('/tenants/plans');
    planOptions.value = Array.isArray(data) ? data : [];
  } catch {
    planOptions.value = [];
  }
}

// ============================================================================
// 统计
// ============================================================================
const stats = reactive<TenantStats>({
  total_tenants: 0,
  active_tenants: 0,
  trial_tenants: 0,
  suspended_tenants: 0,
  expiring_soon: 0,
  monthly_revenue: 0,
});

function formatMonthlyRevenue(cents: number): string {
  if (!cents || cents <= 0) return '暂无实收';
  return `¥${(cents / 100).toFixed(2)}`;
}

function updateStats(overview: Record<string, unknown>) {
  const s = (overview.stats || overview) as Record<string, number>;
  stats.total_tenants = s.total_tenants ?? 0;
  stats.active_tenants = s.active_tenants ?? 0;
  stats.trial_tenants = s.trial_tenants ?? 0;
  stats.suspended_tenants = s.suspended_tenants ?? 0;
  stats.expiring_soon = s.expiring_soon ?? 0;
  stats.monthly_revenue = s.monthly_revenue ?? 0;
}

// ============================================================================
// 表格
// ============================================================================
const ui = useUiPreferencesStore();
const { antTableSize: tableSize } = storeToRefs(ui);
const tablePanelRef = ref<HTMLElement | null>(null);

const baseColumns = [
  { key: 'name', title: '租户名称', dataIndex: 'name', ellipsis: true },
  { key: 'domain', title: '域名', dataIndex: 'domain', width: 140, ellipsis: true },
  { key: 'plan', title: '套餐', dataIndex: 'plan_code', width: 100, align: 'center' as const },
  { key: 'status', title: '状态', dataIndex: 'status', width: 80, align: 'center' as const },
  { key: 'contact_name', title: '联系人', dataIndex: 'contact_name', width: 100 },
  { key: 'ai_quota_used', title: 'AI用量', dataIndex: 'ai_quota_used', width: 90, align: 'center' as const },
  { key: 'created_at', title: '注册时间', dataIndex: 'created_at', width: 110, align: 'center' as const },
  { key: 'trial_ends_at', title: '到期时间', dataIndex: 'trial_ends_at', width: 110, align: 'center' as const },
  { key: 'actions', title: '操作', width: 180, align: 'center' as const },
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
} = useYoudingTable<TenantRecord, { search?: string; status?: string; plan?: string }>({
  columnOrderKey: 'tenants-dashboard-cols',
  columns: baseColumns,
  pageSize: 15,
  defaultQuery: { search: '', status: '', plan: '' },
  fetcher: async (q) => {
    stats.monthly_revenue = 0;
    const data = await apiGet<Record<string, unknown>>('/tenants/', {
      search: q.search || undefined,
      status: q.status || undefined,
      plan: q.plan || undefined,
      page: q.page,
      page_size: q.pageSize,
    });
    const overview = data as Record<string, unknown>;
    if (overview.stats) {
      updateStats(overview);
    }
    const rawItems = (overview.items || overview.recent_tenants || []) as Record<string, unknown>[];
    const rows: TenantRecord[] = rawItems.map((t) => ({
      id: String(t.id ?? ''),
      name: String(t.name ?? ''),
      contact_name: t.contact_name ? String(t.contact_name) : null,
      contact_email: t.contact_email ? String(t.contact_email) : null,
      contact_phone: t.contact_phone ? String(t.contact_phone) : null,
      domain: String(t.domain ?? ''),
      plan_id: String(t.plan_id ?? ''),
      plan_code: (() => {
        const plan = t.plan as Record<string, unknown> | undefined
        return plan?.code ? String(plan.code) : String(t.plan_code ?? '')
      })(),
      plan_name: (() => {
        const plan = t.plan as Record<string, unknown> | undefined
        return plan?.name ? String(plan.name) : String(t.plan_name ?? '')
      })(),
      status: String(t.status ?? ''),
      trial_ends_at: t.trial_ends_at ? String(t.trial_ends_at) : null,
      ai_quota_used: Number(t.ai_quota_used ?? 0),
      storage_used: Number(t.storage_used ?? 0),
      is_active: Boolean(t.is_active),
      created_at: String(t.created_at ?? ''),
    }));
    const total = Number(overview.total ?? rows.length);
    return { items: rows, total };
  },
});

function onSearch() {
  void search();
}
function onReset() {
  void reset();
}

// ============================================================================
// 创建租户
// ============================================================================
const createModalOpen = ref(false);
const creating = ref(false);
const createForm = reactive({
  name: '',
  domain: '',
  contact_name: '',
  contact_email: '',
  contact_phone: '',
  plan_id: '',
  status: 'trial',
});

function openCreateModal() {
  createForm.name = '';
  createForm.domain = '';
  createForm.contact_name = '';
  createForm.contact_email = '';
  createForm.contact_phone = '';
  createForm.plan_id = planOptions.value[0]?.id || '';
  createForm.status = 'trial';
  createModalOpen.value = true;
}

/** 校验域名格式 */
function validateDomain(domain: string): string | null {
  if (!domain) return '请输入子域名';
  if (domain.length < 3 || domain.length > 32) return '子域名长度需在3-32个字符之间';
  if (!/^[a-z0-9][a-z0-9-]*[a-z0-9]$/i.test(domain)) return '子域名只能包含字母、数字、中划线，且不能以中划线开头或结尾';
  return null;
}

/** 校验邮箱格式 */
function validateEmail(email: string): string | null {
  if (!email) return null; // 邮箱可选
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) return '邮箱格式不正确';
  return null;
}

/** 校验手机号格式 */
function validatePhone(phone: string): string | null {
  if (!phone) return null; // 电话可选
  // 支持国际格式和中国大陆手机号
  const phoneRegex = /^[\d\s\-\+\(\)]{7,20}$/;
  if (!phoneRegex.test(phone)) return '电话号码格式不正确';
  return null;
}

async function handleCreate() {
  // 基本必填校验
  if (!createForm.name.trim()) {
    message.warning('请输入租户名称');
    return;
  }
  if (!createForm.plan_id) {
    message.warning('请选择套餐');
    return;
  }

  // 域名格式校验
  const domainError = validateDomain(createForm.domain);
  if (domainError) {
    message.warning(domainError);
    return;
  }

  // 邮箱格式校验
  const emailError = validateEmail(createForm.contact_email);
  if (emailError) {
    message.warning(emailError);
    return;
  }

  // 手机号格式校验
  const phoneError = validatePhone(createForm.contact_phone);
  if (phoneError) {
    message.warning(phoneError);
    return;
  }

  creating.value = true;
  try {
    // 检查域名是否已被使用
    const domainCheck = await apiGet<{ exists?: boolean }>(`/tenants/check-domain?domain=${encodeURIComponent(createForm.domain)}`);
    if (domainCheck?.exists) {
      message.error(`域名 "${createForm.domain}" 已被其他租户使用，请更换域名`);
      creating.value = false;
      return;
    }

    await apiPost('/tenants/', {
      name: createForm.name.trim(),
      domain: createForm.domain.trim().toLowerCase(),
      contact_name: createForm.contact_name.trim() || undefined,
      contact_email: createForm.contact_email.trim() || undefined,
      contact_phone: createForm.contact_phone.trim() || undefined,
      plan_id: createForm.plan_id,
      status: createForm.status,
    });
    message.success('租户创建成功');
    createModalOpen.value = false;
    await reload();
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '创建失败');
  } finally {
    creating.value = false;
  }
}

// ============================================================================
// 详情/编辑
// ============================================================================
const detailDrawerOpen = ref(false);
const detailTenant = ref<TenantRecord | null>(null);
const detailTab = ref('overview');
const saving = ref(false);
const editForm = reactive({
  status: '',
  plan_id: '',
  is_active: true,
});

function openDetail(record: TenantRecord) {
  detailTenant.value = record;
  editForm.status = record.status;
  editForm.plan_id = record.plan_id;
  editForm.is_active = record.is_active;
  detailTab.value = 'overview';
  detailDrawerOpen.value = true;
}

async function toggleStatus(record: TenantRecord) {
  const newStatus = record.status === 'suspended' ? 'active' : 'suspended';
  const actionText = newStatus === 'active' ? '恢复' : '暂停';

  // 确认对话框
  const confirmed = await new Promise<boolean>((resolve) => {
    Modal.confirm({
      title: `确认${actionText}租户`,
      content: `确定要${actionText}租户"${record.name}"吗？${newStatus === 'suspended' ? '暂停后该租户将无法登录和使用服务。' : '恢复后该租户将恢复正常使用。'}`,
      okText: `确认${actionText}`,
      cancelText: '取消',
      okButtonProps: { danger: newStatus === 'suspended' },
      onOk: () => resolve(true),
      onCancel: () => resolve(false),
    });
  });

  if (!confirmed) return;

  try {
    await apiPut(`/tenants/${record.id}`, { status: newStatus });
    message.success(`租户已${actionText}`);
    await reload();
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '操作失败');
  }
}

// ============================================================================
// 批量操作
// ============================================================================
const selectedRowKeys = ref<string[]>([]);

async function batchResume() {
  if (!selectedRowKeys.value.length) return;
  const ids = selectedRowKeys.value;
  const confirmed = await new Promise<boolean>((resolve) => {
    Modal.confirm({
      title: '确认批量恢复',
      content: `确定要恢复选中的 ${ids.length} 个租户吗？`,
      okText: '确认恢复',
      cancelText: '取消',
      onOk: () => resolve(true),
      onCancel: () => resolve(false),
    });
  });
  if (!confirmed) return;

  let success = 0, failed = 0;
  for (const id of ids) {
    try {
      await apiPut(`/tenants/${id}`, { status: 'active' });
      success++;
    } catch {
      failed++;
    }
  }
  message.success(`批量恢复完成：成功 ${success} 个${failed > 0 ? `，失败 ${failed} 个` : ''}`);
  selectedRowKeys.value = [];
  await reload();
}

async function batchSuspend() {
  if (!selectedRowKeys.value.length) return;
  const ids = selectedRowKeys.value;
  const confirmed = await new Promise<boolean>((resolve) => {
    Modal.confirm({
      title: '确认批量暂停',
      content: `确定要暂停选中的 ${ids.length} 个租户吗？暂停后这些租户将无法登录和使用服务。`,
      okText: '确认暂停',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: () => resolve(true),
      onCancel: () => resolve(false),
    });
  });
  if (!confirmed) return;

  let success = 0, failed = 0;
  for (const id of ids) {
    try {
      await apiPut(`/tenants/${id}`, { status: 'suspended' });
      success++;
    } catch {
      failed++;
    }
  }
  message.success(`批量暂停完成：成功 ${success} 个${failed > 0 ? `，失败 ${failed} 个` : ''}`);
  selectedRowKeys.value = [];
  await reload();
}

function batchExport() {
  const selectedItems = items.value.filter((item) => selectedRowKeys.value.includes(item.id));
  const csvHeaders = ['ID', '名称', '域名', '状态', '套餐', '联系人', '邮箱', '创建时间'];
  const csvRows = selectedItems.map((t) => [
    t.id,
    t.name,
    t.domain || '',
    statusLabel(t.status),
    t.plan_name || '',
    t.contact_name || '',
    t.contact_email || '',
    formatDate(t.created_at),
  ]);
  const csvContent = [csvHeaders.join(','), ...csvRows.map((r) => r.map((c) => `"${c}"`).join(','))].join('\n');
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `租户导出_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  message.success(`已导出 ${selectedItems.length} 条租户数据`);
}

async function saveDetail() {
  if (!detailTenant.value) return;
  saving.value = true;
  try {
    await apiPut(`/tenants/${detailTenant.value.id}`, {
      status: editForm.status,
      plan_id: editForm.plan_id,
      is_active: editForm.is_active,
    });
    message.success('租户信息已更新');
    detailDrawerOpen.value = false;
    await reload();
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败');
  } finally {
    saving.value = false;
  }
}

// ============================================================================
// AiToEarn 槽位分配
// ============================================================================
const aitoearnModalOpen = ref(false);
const aitoearnAssigning = ref(false);
const aitoearnPoolLoading = ref(false);
const aitoearnTenant = ref<TenantRecord | null>(null);
const aitoearnPool = ref<{ account_id: string; platform: string; nickname: string }[]>([]);
const aitoearnPoolHint = ref('');

async function loadAitoearnPool() {
  aitoearnPoolLoading.value = true;
  aitoearnPoolHint.value = '';
  try {
    const data = await apiGet<{ accounts?: typeof aitoearnPool.value; total?: number }>(
      '/publish/video/admin/aitoearn-pool',
    );
    aitoearnPool.value = Array.isArray(data?.accounts) ? data.accounts : [];
    if (!aitoearnPool.value.length) {
      aitoearnPoolHint.value = '池中暂无未分配账号，请先在 AiToEarn 侧绑号或配置 AITOEARN_API_KEY';
    }
  } catch (e: unknown) {
    aitoearnPool.value = [];
    aitoearnPoolHint.value = e instanceof Error ? e.message : '无法加载 AiToEarn 池';
  } finally {
    aitoearnPoolLoading.value = false;
  }
}

function openAitoearnModal(record: TenantRecord) {
  aitoearnTenant.value = record;
  aitoearnModalOpen.value = true;
  void loadAitoearnPool();
}

async function handleAutoAssignAitoearn() {
  if (!aitoearnTenant.value) return;
  aitoearnAssigning.value = true;
  try {
    await apiPost(
      `/publish/video/admin/auto-assign-aitoearn-slot?tenant_id=${encodeURIComponent(aitoearnTenant.value.id)}`,
      {},
    );
    message.success('AiToEarn 矩阵号已分配');
    aitoearnModalOpen.value = false;
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '分配失败');
  } finally {
    aitoearnAssigning.value = false;
  }
}

// ============================================================================
// 工具函数
// ============================================================================
function statusColor(s: string): string {
  const map: Record<string, string> = { active: 'green', trial: 'blue', suspended: 'orange', cancelled: 'red' };
  return map[s] || 'default';
}

function statusLabel(s: string): string {
  const map: Record<string, string> = { active: '活跃', trial: '试用中', suspended: '已暂停', cancelled: '已取消' };
  return map[s] || s || '未知';
}

function planColor(code: string): string {
  const map: Record<string, string> = { enterprise: 'purple', professional: 'blue', basic: 'default', trial: 'green', free: 'default' };
  return map[code] || 'default';
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '--';
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
  } catch {
    return dateStr;
  }
}

function trialEndLabel(record: TenantRecord): string {
  return formatDate(record.trial_ends_at);
}

function formatStorage(bytes: number | null): string {
  if (!bytes) return '0 MB';
  if (bytes < 1024) return `${bytes} MB`;
  return `${(bytes / 1024).toFixed(1)} GB`;
}

// ============================================================================
// 初始化
// ============================================================================
onMounted(() => {
  loadPlanOptions();
});
</script>

<style scoped>
.tenant-name-link {
  color: var(--uj-brand);
  cursor: pointer;
}
.tenant-name-link:hover {
  color: var(--uj-brand-hover);
}
.yd-action-link {
  color: var(--uj-brand) !important;
  padding: 0 4px;
}
.yd-action-link-warn {
  color: #ef4444 !important;
  padding: 0 4px;
}
.yd-action-link-success {
  color: #22c55e !important;
  padding: 0 4px;
}
.mb-4 {
  margin-bottom: 16px;
}
.ml-2 {
  margin-left: 8px;
}
.batch-action-bar {
  margin-bottom: 12px;
}
.aitoearn-pool-list {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 13px;
  color: #64748b;
}
.aitoearn-footnote {
  margin-top: 12px;
  font-size: 12px;
  color: #94a3b8;
}
.batch-action-bar :deep(.ant-alert) {
  padding: 8px 16px;
}
.batch-action-bar :deep(.ant-alert-message) {
  font-size: 14px;
}
.batch-action-bar :deep(.ant-alert-description) {
  margin-top: 4px;
}
</style>
