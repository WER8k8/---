/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <a-card size="small" class="customs-research-panel mb-4" title="海关买家反查（受限）">
    <a-alert
      type="warning"
      show-icon
      class="mb-3"
      message="须租户书面授权 + 合规确认；结果仅作 research brief，须人工核实 evidence_url"
    />
    <a-form layout="vertical" :model="form">
      <a-row :gutter="12">
        <a-col :span="12">
          <a-form-item label="品名 / 产品" required>
            <a-input v-model:value="form.product" placeholder="如 rock wool insulation" />
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="HS 编码">
            <a-input v-model:value="form.hs_code" placeholder="680610" />
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="目标国">
            <a-input v-model:value="form.country_code" placeholder="DE" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-form-item label="用途说明" required>
        <a-textarea
          v-model:value="form.purpose"
          :rows="2"
          placeholder="说明反查用途，如：竞品出口国采购商调研（不自动群发）"
        />
      </a-form-item>
      <a-form-item>
        <a-checkbox v-model:checked="form.tenant_consent">已获得租户书面授权</a-checkbox>
        <a-checkbox v-model:checked="form.compliance_acknowledged" class="ml-4">
          已确认合规（不冒充已收录/不自动触达）
        </a-checkbox>
      </a-form-item>
      <a-space>
        <a-button type="primary" :loading="loading" @click="runResearch">生成海关 brief</a-button>
        <a-tag v-if="sidecarOk" color="green">Sidecar 在线</a-tag>
        <a-tag v-else color="default">Sidecar 未配置</a-tag>
      </a-space>
    </a-form>

    <div v-if="brief" class="customs-research-panel__result mt-4">
      <p class="text-sm text-gray-600 mb-2">{{ brief.honesty }}</p>
      <a-table
        v-if="buyers.length"
        size="small"
        :pagination="false"
        :columns="columns"
        :data-source="buyers"
        row-key="evidence_url"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'evidence_url'">
            <a
              :href="record.evidence_url"
              target="_blank"
              rel="noopener noreferrer"
            >
              证据链
            </a>
          </template>
        </template>
      </a-table>
      <a-empty v-else description="无 Sidecar 买家线索（仅公开统计）" />
      <a-tag v-if="brief.probe_mode === 'stub'" color="orange" class="mt-2">开发 stub</a-tag>
    </div>
  </a-card>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue';
import { message } from 'ant-design-vue';

import { customsBuyerResearch, foreignTradeSidecarsStatus } from '@/api/foreign-trade';

type BuyerRow = {
  company_name: string;
  country_code?: string;
  evidence_url: string;
};

const form = reactive({
  product: '',
  hs_code: '',
  country_code: 'DE',
  purpose: '竞品出口国采购商调研 brief，仅供人工核实，不自动群发',
  tenant_consent: false,
  compliance_acknowledged: false,
});

const loading = ref(false);
const brief = ref<Record<string, unknown> | null>(null);
const sidecarOk = ref(false);
const sidecarAbort = new AbortController();
onUnmounted(() => sidecarAbort.abort());

const buyers = computed(() => {
  const rows = brief.value?.buyer_history;
  return Array.isArray(rows) ? (rows as BuyerRow[]) : [];
});

const columns = [
  { title: '采购商', dataIndex: 'company_name', key: 'company_name' },
  { title: '国家', dataIndex: 'country_code', key: 'country_code', width: 72 },
  { title: '证据链', key: 'evidence_url', width: 100 },
];

async function loadSidecar() {
  try {
    const res = await foreignTradeSidecarsStatus({ timeoutMs: 10000, signal: sidecarAbort.signal });
    const data = (res as { data?: Record<string, unknown> })?.data ?? res;
    const st = (data as Record<string, { healthy?: boolean }>).customs_data_spider;
    sidecarOk.value = st?.healthy === true;
  } catch {
    sidecarOk.value = false;
  }
}

async function runResearch() {
  if (!form.product.trim()) {
    message.warning('请填写品名');
    return;
  }
  if (!form.purpose.trim() || form.purpose.trim().length < 8) {
    message.warning('用途说明至少 8 字');
    return;
  }
  if (!form.tenant_consent || !form.compliance_acknowledged) {
    message.warning('须勾选租户授权与合规确认');
    return;
  }
  loading.value = true;
  try {
    const res = await customsBuyerResearch({
      product: form.product.trim(),
      hs_code: form.hs_code.trim() || undefined,
      country_code: form.country_code.trim() || undefined,
      purpose: form.purpose.trim(),
      tenant_consent: form.tenant_consent,
      compliance_acknowledged: form.compliance_acknowledged,
    });
    const data = (res as { data?: Record<string, unknown> })?.data ?? res;
    brief.value = data as Record<string, unknown>;
    const count = Array.isArray(data?.buyer_history) ? data.buyer_history.length : 0;
    const hint = data?.probe_mode === 'stub' ? '（开发 stub）' : '';
    message.success(`海关 brief 已生成：${count} 条买家线索${hint}`);
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '海关反查失败');
    brief.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadSidecar();
});
</script>

<style scoped>
.customs-research-panel__result {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
}
</style>
