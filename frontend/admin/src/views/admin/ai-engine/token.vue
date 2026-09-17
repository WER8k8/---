/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="Token 账本" subtitle="查看租户 Token 余额、消费记录与充值" surface="elevated">
  <div class="token-ledger">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <a-card size="small" v-for="s in stats" :key="s.label">
        <a-statistic :title="s.label" :value="s.value" :suffix="s.suffix" :value-style="{color:s.color}" />
      </a-card>
    </div>

    <!-- 租户选择 -->
    <div class="panel">
      <h3 class="panel-title">租户 Token 状态</h3>
      <a-row :gutter="16">
        <a-col :span="8">
          <a-select v-model:value="selectedTenant" placeholder="选择租户" style="width:100%" @change="loadTenantData">
            <a-select-option v-for="t in tenants" :key="t.id" :value="t.id">
              {{ t.name }} ({{ t.id }})
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-button type="primary" @click="loadTenantData" :loading="loading">刷新</a-button>
        </a-col>
      </a-row>

      <a-descriptions v-if="quotaStatus" :column="4" size="small" style="margin-top:16px">
        <a-descriptions-item label="租户ID">{{ quotaStatus.tenant_id }}</a-descriptions-item>
        <a-descriptions-item label="套餐上限">{{ quotaStatus.quota_limit?.toLocaleString() || '-' }}</a-descriptions-item>
        <a-descriptions-item label="已用">{{ quotaStatus.quota_used?.toLocaleString() || 0 }}</a-descriptions-item>
        <a-descriptions-item label="剩余">
          <span :style="{color: quotaStatus.balance <= 0 ? 'red' : 'green'}">
            {{ quotaStatus.balance?.toLocaleString() || 0 }}
          </span>
        </a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="quotaStatus.is_suspended ? 'red' : 'green'">
            {{ quotaStatus.is_suspended ? '已停服' : '正常' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="套餐">{{ quotaStatus.plan_name || '-' }}</a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- 充值操作 -->
    <div class="panel" v-if="selectedTenant">
      <h3 class="panel-title">充值 Token</h3>
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input-number v-model:value="topupAmount" :min="1" :max="1000000" placeholder="充值数量" style="width:100%" />
        </a-col>
        <a-col :span="8">
          <a-input v-model:value="topupReason" placeholder="充值原因（如：手动充值、套餐升级）" />
        </a-col>
        <a-col :span="4">
          <a-button type="primary" @click="doTopup" :loading="topupLoading">确认充值</a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 账本记录 -->
    <div class="panel" v-if="selectedTenant">
      <h3 class="panel-title">账本记录</h3>
      <a-table :columns="ledgerCols" :data-source="ledgerEntries" :loading="ledgerLoading" :pagination="ledgerPagination" row-key="id" size="small" @change="handleTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key==='amount'">
            <span :style="{color: record.amount > 0 ? 'green' : 'red'}">
              {{ record.amount > 0 ? '+' + record.amount : record.amount }}
            </span>
          </template>
          <template v-if="column.key==='reason'">
            <a-tag>{{ record.reason }}</a-tag>
          </template>
          <template v-if="column.key==='created_at'">
            {{ formatTime(record.created_at) }}
          </template>
        </template>
      </a-table>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { apiGet, apiPost } from '@/utils/api';

const tenants = ref<any[]>([]);
const selectedTenant = ref<string>('');
const quotaStatus = ref<any>(null);
const loading = ref(false);

const stats = ref<any[]>([]);

const topupAmount = ref<number>(1000);
const topupReason = ref<string>('手动充值');
const topupLoading = ref(false);

const ledgerEntries = ref<any[]>([]);
const ledgerLoading = ref(false);
const ledgerPagination = ref({ current: 1, pageSize: 20, total: 0 });

const ledgerCols = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '租户ID', dataIndex: 'tenant_id', key: 'tenant_id', width: 120 },
  { title: '变化量', dataIndex: 'amount', key: 'amount', width: 100 },
  { title: '余额快照', dataIndex: 'balance_after', key: 'balance_after', width: 120 },
  { title: '原因', key: 'reason', width: 150 },
  { title: '关联ID', dataIndex: 'reference_id', key: 'reference_id', width: 120 },
  { title: '时间', key: 'created_at', width: 180 },
];

async function loadTenants() {
  try {
    const res = await apiGet<{ items?: any[]; total?: number }>('/tenants/', {
      page: 1,
      page_size: 1000,
    });
    tenants.value = res?.items ?? [];
    if (!stats.value.length) {
      stats.value = [
        { label: '租户总数', value: tenants.value.length, suffix: '', color: '#1677ff' },
        { label: '停服租户', value: tenants.value.filter((t: any) => t.status === 'suspended').length, suffix: '', color: '#ff4d4f' },
      ];
    } else {
      stats.value[0].value = tenants.value.length;
      stats.value[1].value = tenants.value.filter((t: any) => t.status === 'suspended').length;
    }
  } catch (e: any) {
    message.error('加载租户列表失败: ' + e.message);
  }
}

async function loadTenantData() {
  if (!selectedTenant.value) return;
  loading.value = true;
  try {
    quotaStatus.value = await apiGet(`/token/quota-status/${selectedTenant.value}`);
    await loadLedger();
  } catch (e: any) {
    message.error('加载租户数据失败: ' + e.message);
  } finally {
    loading.value = false;
  }
}

async function loadLedger() {
  if (!selectedTenant.value) return;
  ledgerLoading.value = true;
  try {
    const res = await apiGet<{ items?: any[]; total?: number }>('/token/ledger', {
      tenant_id: selectedTenant.value,
      page: ledgerPagination.value.current,
      page_size: ledgerPagination.value.pageSize,
    });
    ledgerEntries.value = res?.items ?? [];
    ledgerPagination.value.total = res?.total ?? 0;
  } catch (e: any) {
    message.error('加载账本记录失败: ' + e.message);
  } finally {
    ledgerLoading.value = false;
  }
}

async function doTopup() {
  if (!selectedTenant.value || !topupAmount.value || topupAmount.value <= 0) {
    message.warning('请输入有效的充值数量');
    return;
  }
  topupLoading.value = true;
  try {
    const res = await apiPost<{ balance?: number }>('/token/topup', {
      tenant_id: selectedTenant.value,
      amount: topupAmount.value,
      reason: topupReason.value || '手动充值',
    });
    message.success(`充值成功！当前余额: ${res?.balance ?? '-'}`);
    await loadTenantData();
  } catch (e: any) {
    message.error('充值失败: ' + e.message);
  } finally {
    topupLoading.value = false;
  }
}

function handleTableChange(pagination: any) {
  ledgerPagination.value.current = pagination.current;
  ledgerPagination.value.pageSize = pagination.pageSize;
  loadLedger();
}

function formatTime(ts: string): string {
  if (!ts) return '-';
  return new Date(ts).toLocaleString('zh-CN');
}

onMounted(() => {
  stats.value = [
    { label: '租户总数', value: 0, suffix: '', color: '#1677ff' },
    { label: '停服租户', value: 0, suffix: '', color: '#ff4d4f' },
  ];
  loadTenants();
});
</script>

<style scoped>
.token-ledger { padding: 24px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 600; margin: 0 0 8px 0; }
.page-desc { color: #8c8c8c; margin: 0; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.panel { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.panel-title { font-size: 16px; font-weight: 600; margin: 0 0 16px 0; padding-bottom: 12px; border-bottom: 1px solid #f0f0f0; }
</style>
