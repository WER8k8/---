<template>
  <YdPage title="静态 IP 池" subtitle="长期固定 · 纯静态住宅 IP · 平台池与租户分配" surface="elevated">
    <template #actions>
      <YdTableToolbar
        :loading="loading"
        :target-ref="tablePanelRef"
        show-export
        @refresh="loadAll"
        @export="exportCsv"
      />
    </template>

    <YdFinanceNav />

    <a-alert
      v-if="!loading && (overview.total ?? 0) === 0"
      type="warning"
      show-icon
      class="mb-4"
      message="平台 IP 池为空"
      description="请先选择上游供应商：推荐 IPRoyal 纯静态住宅（长期固定 + 自动续费），或用手工录入添加外采固定 IP。"
    />

    <div class="yd-panel mb-4 p-4 supplier-panel">
      <div class="panel-head mb-3">
        <div>
          <span class="panel-title">上游供应商列表</span>
          <p class="text-muted text-sm mb-0">可新增、编辑、删除、切换启用；养号请选「长期固定 · 纯静态住宅」。</p>
        </div>
        <a-space wrap>
          <a-button type="primary" size="small" @click="openSupplierModal()">新增供应商</a-button>
          <a-button
            size="small"
            :loading="replenishing"
            :disabled="!activeSupplier?.supports_pool_replenish || !activeSupplier?.ready"
            @click="replenishPool"
          >
            向当前供应商补池
          </a-button>
          <a-button size="small" @click="openCreateModal">录入固定 IP</a-button>
        </a-space>
      </div>

      <YdDataTable
        :columns="supplierColumns"
        :data-source="supplierList"
        :loading="loadingSuppliers"
        :pagination="false"
        :table-props="{ rowKey: 'id', size: 'small' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="sup-name">{{ record.name }}</div>
            <div class="sup-code">{{ record.code }}</div>
          </template>
          <template v-else-if="column.key === 'type'">
            <a-tag :color="record.long_term_fixed ? 'green' : 'orange'">
              {{ record.long_term_fixed ? '固定静态' : '非固定' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'pool'">
            {{ record.pool?.available ?? 0 }} / {{ record.pool?.total ?? 0 }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag v-if="record.is_active" color="blue">当前启用</a-tag>
            <a-tag v-else-if="record.ready" color="green">就绪</a-tag>
            <a-tag v-else color="default">未配置</a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button
                type="link"
                size="small"
                :disabled="record.is_active"
                @click="activateSupplier(record.id)"
              >
                启用
              </a-button>
              <a-button type="link" size="small" @click="openSupplierModal(record)">编辑</a-button>
              <a-button type="link" size="small" danger @click="deleteSupplier(record)">删除</a-button>
            </a-space>
          </template>
        </template>
      </YdDataTable>
    </div>

    <template v-if="loading">
      <SkeletonCard variant="kpi" />
      <div class="mt-4">
        <SkeletonCard variant="chart" />
      </div>
      <div class="mt-4">
        <SkeletonCard variant="table" :rows="5" />
      </div>
    </template>
    <template v-else>
      <YdStatsRow :cols="4">
        <YdStatsCard label="池内总槽位" :value="String(overview.total ?? 0)" compact />
        <YdStatsCard label="已分配" :value="String(overview.assigned ?? 0)" tone="amber" compact />
        <YdStatsCard label="可用" :value="String(overview.available ?? 0)" tone="green" compact />
        <YdStatsCard
          label="池使用率"
          :value="`${overview.usage_rate ?? 0}%`"
          :tone="usageTone"
          compact
        />
      </YdStatsRow>

      <div class="yd-panel mt-4 p-4">
        <div class="panel-head mb-3">
          <span class="panel-title">整体使用率</span>
          <span class="text-muted text-sm">
            已分配 {{ overview.assigned ?? 0 }} / 可分配 {{ overview.assignable ?? 0 }}
            · 禁用 {{ overview.disabled ?? 0 }}
          </span>
        </div>
        <a-progress
          :percent="overview.usage_rate ?? 0"
          :status="progressStatus"
          :stroke-color="progressColor"
        />
        <a-row :gutter="16" class="mt-4">
          <a-col :span="12">
            <div class="region-block">
              <div class="region-head">
                <span>国内 (cn)</span>
                <span>{{ regionCn.usage_rate ?? 0 }}%</span>
              </div>
              <a-progress :percent="regionCn.usage_rate ?? 0" size="small" />
              <p class="region-meta">
                已用 {{ regionCn.assigned ?? 0 }} · 可用 {{ regionCn.available ?? 0 }} · 共 {{ regionCn.total ?? 0 }}
              </p>
            </div>
          </a-col>
          <a-col :span="12">
            <div class="region-block">
              <div class="region-head">
                <span>海外 (global)</span>
                <span>{{ regionGlobal.usage_rate ?? 0 }}%</span>
              </div>
              <a-progress :percent="regionGlobal.usage_rate ?? 0" size="small" />
              <p class="region-meta">
                已用 {{ regionGlobal.assigned ?? 0 }} · 可用 {{ regionGlobal.available ?? 0 }} · 共 {{ regionGlobal.total ?? 0 }}
              </p>
            </div>
          </a-col>
        </a-row>
      </div>

      <div class="yd-panel mt-4 p-4">
        <div class="panel-head mb-2">
          <span class="panel-title">租户配额消耗</span>
        </div>
        <p class="text-muted text-sm mb-2">
          各租户套餐/加购 IP 配额合计 {{ overview.tenant_quota_total ?? 0 }} 槽 ·
          已占用 {{ overview.tenant_quota_used ?? 0 }} 槽
        </p>
        <a-progress
          :percent="overview.tenant_quota_usage_rate ?? 0"
          size="small"
          stroke-color="var(--uj-brand, #4a9b8c)"
        />
      </div>

      <a-tabs v-model:activeKey="activeTab" class="mt-4">
        <a-tab-pane key="ip" tab="IP 槽位列表">
          <a-space wrap class="mb-3">
            <a-select
              v-model:value="filterRegion"
              allow-clear
              placeholder="区域"
              style="min-width: 120px"
              @change="loadEndpoints"
            >
              <a-select-option value="cn">国内</a-select-option>
              <a-select-option value="global">海外</a-select-option>
            </a-select>
            <a-select
              v-model:value="filterStatus"
              allow-clear
              placeholder="状态"
              style="min-width: 120px"
              @change="loadEndpoints"
            >
              <a-select-option value="available">可用</a-select-option>
              <a-select-option value="assigned">已分配</a-select-option>
              <a-select-option value="disabled">禁用</a-select-option>
            </a-select>
          </a-space>
          <div ref="tablePanelRef" class="yd-panel yd-table-panel">
            <YdDataTable
              :columns="ipColumns"
              :data-source="endpoints"
              :loading="loadingTable"
              :pagination="false"
              :table-props="{ rowKey: 'id', size: 'small' }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'region'">
                  {{ record.region === 'global' ? '海外' : '国内' }}
                </template>
                <template v-else-if="column.key === 'slot_status'">
                  <a-tag :color="statusColor(record.slot_status)">
                    {{ statusLabel(record.slot_status) }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'tenant'">
                  {{ record.tenant_name || record.tenant_id || '—' }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button
                      type="link"
                      size="small"
                      :disabled="record.slot_status === 'assigned'"
                      @click="assignSlot(record.id)"
                    >
                      分配
                    </a-button>
                    <a-button type="link" size="small" danger @click="releaseSlot(record.id)">
                      释放
                    </a-button>
                  </a-space>
                </template>
              </template>
            </YdDataTable>
          </div>
        </a-tab-pane>
        <a-tab-pane key="profile" tab="指纹环境">
          <YdDataTable
            :columns="profileColumns"
            :data-source="profiles"
            :loading="loadingProfiles"
            :pagination="false"
            :table-props="{ rowKey: 'id', size: 'small' }"
          />
        </a-tab-pane>
      </a-tabs>
    </template>

    <a-modal
      v-model:open="supplierModalOpen"
      :title="supplierForm.id ? '编辑供应商' : '新增供应商'"
      ok-text="保存"
      :confirm-loading="savingSupplier"
      @ok="submitSupplier"
    >
      <a-form layout="vertical">
        <a-form-item label="供应商代码" required>
          <a-input
            v-model:value="supplierForm.code"
            :disabled="!!supplierForm.id"
            placeholder="小写英文，如 iproyal、my-proxy"
          />
        </a-form-item>
        <a-form-item label="显示名称" required>
          <a-input v-model:value="supplierForm.name" placeholder="如 IPRoyal 静态住宅" />
        </a-form-item>
        <a-form-item label="对接方式">
          <a-select v-model:value="supplierForm.adapter">
            <a-select-option value="iproyal">IPRoyal API（自动补池）</a-select-option>
            <a-select-option value="manual">手工录入（外采固定 IP）</a-select-option>
            <a-select-option value="asocks">ASocks（按流量，非固定）</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="IP 类型">
          <a-checkbox v-model:checked="supplierForm.long_term_fixed">长期固定 · 纯静态住宅</a-checkbox>
        </a-form-item>
        <a-form-item v-if="supplierForm.adapter === 'iproyal'" label="API Token">
          <a-input-password v-model:value="supplierForm.api_token" placeholder="留空则不修改已有 Token" />
        </a-form-item>
        <a-form-item v-if="supplierForm.adapter === 'iproyal'" label="套餐（天）">
          <a-select v-model:value="supplierForm.plan_id">
            <a-select-option :value="4">60 天（推荐养号）</a-select-option>
            <a-select-option :value="5">90 天</a-select-option>
            <a-select-option :value="3">30 天</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="说明">
          <a-textarea v-model:value="supplierForm.description" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="createOpen"
      title="录入真实静态 IP"
      ok-text="保存"
      :confirm-loading="creating"
      @ok="submitCreate"
    >
      <a-form layout="vertical">
        <a-form-item label="区域" required>
          <a-select v-model:value="createForm.region">
            <a-select-option value="cn">国内</a-select-option>
            <a-select-option value="global">海外</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Host" required>
          <a-input v-model:value="createForm.host" placeholder="真实出口 IP 或域名" />
        </a-form-item>
        <a-form-item label="端口" required>
          <a-input-number v-model:value="createForm.port" :min="1" :max="65535" class="w-full" />
        </a-form-item>
        <a-form-item label="供应商">
          <a-select v-model:value="createForm.provider">
            <a-select-option value="iproyal">IPRoyal 静态住宅</a-select-option>
            <a-select-option value="manual">手工 / 外采</a-select-option>
            <a-select-option value="custom">其它固定静态</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-input v-model:value="createForm.label" placeholder="节点说明" />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { YdPage, YdDataTable, YdStatsCard, YdStatsRow, YdTableToolbar } from '@/components/youding';
import YdFinanceNav from '@/components/youding/YdFinanceNav.vue';
import { apiDelete, apiGet, apiPost, apiPut } from '@/utils/api';
import SkeletonCard from '@/components/common/SkeletonCard.vue';

type RegionStats = {
  total?: number;
  assigned?: number;
  available?: number;
  disabled?: number;
  usage_rate?: number;
};

type Overview = {
  total?: number;
  available?: number;
  assigned?: number;
  disabled?: number;
  assignable?: number;
  usage_rate?: number;
  tenant_quota_total?: number;
  tenant_quota_used?: number;
  tenant_quota_usage_rate?: number;
  by_region?: Record<string, RegionStats>;
};

type EndpointRow = {
  id: string;
  region: string;
  host: string;
  port?: number;
  slot_status: string;
  tenant_id?: string;
  tenant_name?: string;
  provider?: string;
  label?: string;
};

type SupplierRow = {
  id: string;
  code: string;
  name: string;
  adapter: string;
  long_term_fixed: boolean;
  is_active: boolean;
  is_builtin?: boolean;
  ready: boolean;
  supports_pool_replenish?: boolean;
  description?: string;
  pool?: { total?: number; available?: number; assigned?: number };
  config?: { plan_id?: number; api_token?: string };
};

type SuppliersPayload = {
  providers?: SupplierRow[];
  active_supplier_id?: string;
};

const loading = ref(false);
const loadingTable = ref(false);
const loadingProfiles = ref(false);
const loadingSuppliers = ref(false);
const activeTab = ref('ip');
const filterRegion = ref<string | undefined>();
const filterStatus = ref<string | undefined>();
const endpoints = ref<EndpointRow[]>([]);
const profiles = ref<Array<Record<string, unknown>>>([]);
const overview = ref<Overview>({});
const tablePanelRef = ref<HTMLElement | null>(null);
const supplierList = ref<SupplierRow[]>([]);
const replenishing = ref(false);
const supplierModalOpen = ref(false);
const savingSupplier = ref(false);
const supplierForm = ref({
  id: '',
  code: '',
  name: '',
  adapter: 'manual',
  long_term_fixed: true,
  api_token: '',
  plan_id: 4,
  description: '',
});
const createOpen = ref(false);
const creating = ref(false);
const createForm = ref({
  region: 'global',
  host: '',
  port: 1080,
  provider: 'iproyal',
  label: '',
});

const activeSupplier = computed(
  () => supplierList.value.find((s) => s.is_active) ?? null,
);

const supplierColumns = [
  { title: '供应商', key: 'name', width: 160 },
  { title: '对接', dataIndex: 'adapter', key: 'adapter', width: 90 },
  { title: '类型', key: 'type', width: 100 },
  { title: '可用/总数', key: 'pool', width: 100 },
  { title: '状态', key: 'status', width: 110 },
  { title: '操作', key: 'actions', width: 180 },
];

const regionCn = computed(() => overview.value.by_region?.cn || {});
const regionGlobal = computed(() => overview.value.by_region?.global || {});

const usageTone = computed(() => {
  const rate = overview.value.usage_rate ?? 0;
  if (rate >= 90) return 'amber';
  if (rate >= 70) return 'amber';
  return 'green';
});

const progressStatus = computed(() => {
  const rate = overview.value.usage_rate ?? 0;
  if (rate >= 95) return 'exception';
  if (rate >= 80) return 'active';
  return 'normal';
});

const progressColor = computed(() => {
  const rate = overview.value.usage_rate ?? 0;
  if (rate >= 90) return '#ef4444';
  if (rate >= 70) return '#f59e0b';
  return '#4a9b8c';
});

const ipColumns = [
  { title: '区域', key: 'region', width: 80 },
  { title: 'Host', dataIndex: 'host', key: 'host', ellipsis: true },
  { title: '端口', dataIndex: 'port', key: 'port', width: 72 },
  { title: '状态', key: 'slot_status', width: 100 },
  { title: '租户', key: 'tenant', width: 140, ellipsis: true },
  { title: '供应商', dataIndex: 'provider', key: 'provider', width: 100, ellipsis: true },
  { title: '操作', key: 'actions', width: 140 },
];

const profileColumns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '租户 ID', dataIndex: 'tenant_id', key: 'tenant_id', ellipsis: true },
  { title: '绑定 IP', dataIndex: 'egress_endpoint_id', key: 'egress_endpoint_id', ellipsis: true },
];

function statusLabel(s: string) {
  const map: Record<string, string> = {
    available: '可用',
    assigned: '已分配',
    disabled: '禁用',
  };
  return map[s] || s;
}

function statusColor(s: string) {
  const map: Record<string, string> = {
    available: 'green',
    assigned: 'blue',
    disabled: 'default',
  };
  return map[s] || 'default';
}

async function loadOverview() {
  try {
    overview.value = (await apiGet<Overview>('/egress/overview')) || {};
  } catch (e: unknown) {
    const err = e as { message?: string };
    message.error(err.message || '加载 IP 池概览失败');
    overview.value = {};
  }
}

async function loadEndpoints() {
  loadingTable.value = true;
  try {
    endpoints.value =
      (await apiGet<EndpointRow[]>('/egress/endpoints', {
        region: filterRegion.value,
        slot_status: filterStatus.value,
      })) || [];
  } catch (e: unknown) {
    const err = e as { message?: string };
    message.error(err.message || '加载 IP 列表失败');
  } finally {
    loadingTable.value = false;
  }
}

async function loadProfiles() {
  loadingProfiles.value = true;
  try {
    profiles.value = (await apiGet('/egress/profiles')) || [];
  } catch (e: unknown) {
    const err = e as { message?: string };
    message.error(err.message || '加载指纹环境失败');
  } finally {
    loadingProfiles.value = false;
  }
}

async function loadSuppliers() {
  loadingSuppliers.value = true;
  try {
    const data = (await apiGet<SuppliersPayload>('/egress/suppliers')) || {};
    supplierList.value = data.providers ?? [];
  } catch (e: unknown) {
    const err = e as { message?: string };
    message.error(err.message || '加载供应商列表失败');
    supplierList.value = [];
  } finally {
    loadingSuppliers.value = false;
  }
}

function openSupplierModal(row?: SupplierRow) {
  if (row) {
    supplierForm.value = {
      id: row.id,
      code: row.code,
      name: row.name,
      adapter: row.adapter,
      long_term_fixed: row.long_term_fixed,
      api_token: '',
      plan_id: row.config?.plan_id ?? 4,
      description: row.description || '',
    };
  } else {
    supplierForm.value = {
      id: '',
      code: '',
      name: '',
      adapter: 'manual',
      long_term_fixed: true,
      api_token: '',
      plan_id: 4,
      description: '',
    };
  }
  supplierModalOpen.value = true;
}

async function submitSupplier() {
  const f = supplierForm.value;
  if (!f.code?.trim() || !f.name?.trim()) {
    message.warning('请填写代码与名称');
    return;
  }
  savingSupplier.value = true;
  try {
    const config: Record<string, unknown> = { plan_id: f.plan_id };
    if (f.api_token?.trim()) config.api_token = f.api_token.trim();
    if (f.id) {
      await apiPut('/egress/suppliers/' + f.id, {
        name: f.name.trim(),
        adapter: f.adapter,
        long_term_fixed: f.long_term_fixed,
        description: f.description?.trim() || undefined,
        supports_pool_replenish: f.adapter === 'iproyal',
        config,
      });
      message.success('供应商已更新');
    } else {
      await apiPost('/egress/suppliers', {
        code: f.code.trim().toLowerCase(),
        name: f.name.trim(),
        adapter: f.adapter,
        long_term_fixed: f.long_term_fixed,
        description: f.description?.trim() || undefined,
        supports_pool_replenish: f.adapter === 'iproyal',
        config,
      });
      message.success('供应商已添加');
    }
    supplierModalOpen.value = false;
    await loadAll();
  } catch (e: unknown) {
    const err = e as { message?: string };
    message.error(err.message || '保存失败');
  } finally {
    savingSupplier.value = false;
  }
}

async function activateSupplier(id: string) {
  try {
    await apiPost('/egress/suppliers/' + id + '/activate');
    message.success('已切换启用供应商');
    await loadAll();
  } catch (e: unknown) {
    const err = e as { message?: string };
    message.error(err.message || '切换失败');
  }
}

function deleteSupplier(row: SupplierRow) {
  Modal.confirm({
    title: `删除供应商「${row.name}」？`,
    content: row.is_builtin
      ? '内置供应商将停用；自定义供应商将永久删除。'
      : '删除后不可恢复。',
    okType: 'danger',
    onOk: async () => {
      try {
        await apiDelete('/egress/suppliers/' + row.id);
        message.success('已删除');
        await loadAll();
      } catch (e: unknown) {
        const err = e as { message?: string };
        message.error(err.message || '删除失败');
      }
    },
  });
}

async function replenishPool() {
  if (!activeSupplier.value?.supports_pool_replenish) {
    message.warning('当前启用的供应商不支持自动补池');
    return;
  }
  replenishing.value = true;
  try {
    const res = (await apiPost('/egress/pool/replenish')) as { message?: string };
    message.success(res?.message || '已提交补池采购');
    await loadAll();
  } catch (e: unknown) {
    const err = e as { message?: string };
    message.error(err.message || '补池失败');
  } finally {
    replenishing.value = false;
  }
}

function openCreateModal() {
  createOpen.value = true;
}

async function submitCreate() {
  if (!createForm.value.host?.trim() || !createForm.value.port) {
    message.warning('请填写 Host 与端口');
    return;
  }
  creating.value = true;
  try {
    let provider = createForm.value.provider?.trim() || 'manual';
    if (provider === 'custom') provider = 'manual';
    await apiPost('/egress/endpoints', {
      region: createForm.value.region,
      host: createForm.value.host.trim(),
      port: createForm.value.port,
      provider,
      label: createForm.value.label?.trim() || undefined,
    });
    message.success('已录入真实 IP 槽位');
    createOpen.value = false;
    createForm.value = {
      region: 'global',
      host: '',
      port: 1080,
      provider: 'iproyal',
      label: '',
    };
    await loadAll();
  } catch (e: unknown) {
    const err = e as { message?: string };
    message.error(err.message || '录入失败');
  } finally {
    creating.value = false;
  }
}

async function loadAll() {
  loading.value = true;
  try {
    await Promise.all([loadOverview(), loadEndpoints(), loadProfiles(), loadSuppliers()]);
  } finally {
    loading.value = false;
  }
}

async function assignSlot(endpointId: string) {
  const tenantId = window.prompt('请输入租户 ID（tenant_id）');
  if (!tenantId?.trim()) return;
  try {
    await apiPost(`/egress/endpoints/${endpointId}/assign`, { tenant_id: tenantId.trim() });
    message.success('已分配');
    await loadAll();
  } catch (e: unknown) {
    const err = e as { message?: string };
    message.error(err.message || '分配失败');
  }
}

function releaseSlot(endpointId: string) {
  Modal.confirm({
    title: '确认释放该 IP 槽位？',
    onOk: async () => {
      try {
        await apiPost(`/egress/endpoints/${endpointId}/release`);
        message.success('已释放');
        await loadAll();
      } catch (e: unknown) {
        const err = e as { message?: string };
        message.error(err.message || '释放失败');
      }
    },
  });
}

function exportCsv() {
  const header = ['区域', 'Host', '端口', '状态', '租户', '供应商'];
  const rows = endpoints.value.map((r) => [
    r.region === 'global' ? '海外' : '国内',
    r.host,
    String(r.port ?? ''),
    statusLabel(r.slot_status),
    r.tenant_name || r.tenant_id || '',
    r.provider || '',
  ]);
  const csv = [header, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ip-pool-${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

onMounted(() => {
  void loadAll();
});
</script>

<style scoped>
.mt-4 {
  margin-top: 16px;
}

.mb-2 {
  margin-bottom: 8px;
}

.mb-3 {
  margin-bottom: 12px;
}

.text-muted {
  color: #64748b;
}

.text-sm {
  font-size: 13px;
}

.region-block {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
}

.region-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-weight: 600;
}

.region-meta {
  margin: 8px 0 0;
  font-size: 12px;
  color: #64748b;
}

.panel-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.panel-title {
  font-weight: 600;
}

.hint-warn {
  color: #b45309;
  margin: 0;
}

.w-full {
  width: 100%;
}

.supplier-panel {
  border: 1px solid #e2e8f0;
}

.sup-name {
  font-weight: 600;
}

.sup-code {
  font-size: 12px;
  color: #64748b;
}

.mb-0 {
  margin-bottom: 0;
}
</style>
