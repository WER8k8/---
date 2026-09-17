/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="AI 配置" subtitle="管理 AI 提供商与模型配置" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showProviderModal = true">添加提供商</a-button>
    </template>

    <div class="glass panel">
      <h2 class="h2">提供商管理</h2>
      <a-row :gutter="16">
        <a-col v-for="p in providers" :key="p.id" :span="8">
          <a-card size="small" class="provider-card" :hoverable="true">
            <template #title>
              <span class="provider-name">{{ p.name }}</span>
              <a-tag :color="providerConfiguredTagColor(p)" style="margin-left: 8px">
                {{ providerConfiguredLabel(p) }}
              </a-tag>
            </template>
            <template #extra>
              <a-switch :checked="p.enabled" size="small" @change="(v) => toggleProvider(p.id, v as boolean)" />
            </template>
            <p class="card-meta">
              {{ providerModelStats(p) }}
            </p>
            <div class="card-actions">
              <a :href="providerLinks[p.name]" target="_blank" class="link-btn">获取 Key</a>
              <a-space size="small">
                <a-button size="small" @click="openEditProvider(p)">编辑</a-button>
                <a-button size="small" danger @click="deleteProvider(p.id)">删除</a-button>
              </a-space>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <div class="glass panel">
      <div class="panel-head">
        <h2 class="h2">模型配置</h2>
        <a-space>
          <a-button size="small" :loading="probeLoading" @click="probeModels">探测可用性</a-button>
          <a-button type="dashed" size="small" @click="showModelModal = true">添加模型</a-button>
        </a-space>
      </div>

      <a-alert
        v-if="modelSummary.total > 0"
        :type="modelSummary.unavailable > 0 ? 'warning' : 'success'"
        show-icon
        style="margin-bottom: 12px"
        :message="modelSummaryMessage"
      />

      <a-table
        :columns="modelCols"
        :data-source="models"
        row-key="id"
        :pagination="false"
        size="small"
        :loading="modelsLoading"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'provider_name'">
            <a-tag>{{ record.provider_name }}</a-tag>
          </template>
          <template v-else-if="column.key === 'capability'">
            <div class="cap-cell">
              <a-tag color="blue">{{ record.capability_label || record.model_type }}</a-tag>
              <a-tag :color="endpointColor(record.endpoint)" size="small">
                {{ endpointLabel(record.endpoint) }}
              </a-tag>
              <div class="cap-desc">{{ record.capability_desc || inputModesLabel(record.input_modes) }}</div>
            </div>
          </template>
          <template v-else-if="column.key === 'sort_order'">
            <div class="rank-cell">
              <span class="rank-num">{{ displayRank(record as AiModelEnrichedRow) }}</span>
              <div class="rank-actions">
                <a-button
                  type="text"
                  size="small"
                  class="rank-btn"
                  :disabled="!canMoveRank(record as AiModelEnrichedRow, 'up') || rankBusy === record.id"
                  aria-label="上移"
                  @click="moveModelRank(record as AiModelEnrichedRow, 'up')"
                >
                  <ArrowUpOutlined />
                </a-button>
                <a-button
                  type="text"
                  size="small"
                  class="rank-btn"
                  :disabled="!canMoveRank(record as AiModelEnrichedRow, 'down') || rankBusy === record.id"
                  aria-label="下移"
                  @click="moveModelRank(record as AiModelEnrichedRow, 'down')"
                >
                  <ArrowDownOutlined />
                </a-button>
              </div>
            </div>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tooltip v-if="record.error || record.note" :title="record.error || record.note">
              <a-tag :color="modelStatusColor(record.status)">
                {{ record.status_label || '未检测' }}
                <span v-if="record.latency_ms"> · {{ record.latency_ms }}ms</span>
              </a-tag>
            </a-tooltip>
            <a-tag v-else :color="modelStatusColor(record.status)">
              {{ record.status_label || '未检测' }}
              <span v-if="record.latency_ms"> · {{ record.latency_ms }}ms</span>
            </a-tag>
          </template>
          <template v-else-if="column.key === 'active'">
            <a-switch :checked="record.active" size="small" @change="(v) => toggleModel(record.id, v as boolean)" />
          </template>
        </template>
      </a-table>
    </div>

    <div class="glass panel">
      <h2 class="h2">API Key 注册链接</h2>
      <a-row :gutter="[12, 12]">
        <a-col v-for="link in quickLinks" :key="link.name" :span="8">
          <a-card
            size="small"
            :hoverable="true"
            class="link-card"
            style="cursor: pointer"
            @click="openLink(link.url)"
          >
            <span class="link-name">{{ link.name }}</span><br />
            <span class="link-url">{{ link.url }}</span>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <a-modal v-model:open="showProviderModal" title="添加提供商" @ok="saveProvider">
      <a-form :model="provForm" layout="vertical">
        <a-form-item label="名称">
          <a-input v-model:value="provForm.name" placeholder="如 OpenAI" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="provForm.provider_type">
            <a-select-option value="openai">OpenAI</a-select-option>
            <a-select-option value="deepseek">DeepSeek</a-select-option>
            <a-select-option value="nvidia">NVIDIA</a-select-option>
            <a-select-option value="anthropic">Anthropic</a-select-option>
            <a-select-option value="gemini">Gemini</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="API Key">
          <a-input-password v-model:value="provForm.api_key" placeholder="sk-..." />
        </a-form-item>
        <a-form-item label="Base URL">
          <a-input v-model:value="provForm.base_url" placeholder="https://api.openai.com/v1" />
        </a-form-item>
        <a-form-item label="默认模型">
          <a-input v-model:value="provForm.default_model" placeholder="gpt-4o" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal v-model:open="showModelModal" title="添加模型" @ok="saveModel">
      <a-form :model="modelForm" layout="vertical">
        <a-form-item label="提供商">
          <a-select v-model:value="modelForm.provider_id">
            <a-select-option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="模型名">
          <a-input v-model:value="modelForm.model_name" placeholder="gpt-4o" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="modelForm.model_type">
            <a-select-option value="chat">Chat</a-select-option>
            <a-select-option value="embedding">Embedding</a-select-option>
            <a-select-option value="image">Image</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Temperature">
          <a-input v-model:value="modelForm.temperature" placeholder="0.7" />
        </a-form-item>
        <a-form-item label="Max Tokens">
          <a-input v-model:value="modelForm.max_tokens" placeholder="4096" />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { message } from 'ant-design-vue';
import { ArrowDownOutlined, ArrowUpOutlined } from '@ant-design/icons-vue';
import { YdPage } from '@/components/youding';
import { apiDelete, apiGet, apiPost, apiPut } from '@/utils/api';
import {
  apiErrorMessage,
  providerConfiguredLabel,
  providerConfiguredTagColor,
} from '@/utils/aiConfigHelpers';
import {
  type AiModelEnrichedRow,
  endpointColor,
  endpointLabel,
  inputModesLabel,
  mergeProbeResults,
  modelStatusColor,
  summarizeModelStatus,
} from '@/utils/aiModelCapability';

const providers = ref<any[]>([]);
const models = ref<AiModelEnrichedRow[]>([]);
const modelsLoading = ref(false);
const probeLoading = ref(false);
const rankBusy = ref<string | null>(null);
const showProviderModal = ref(false);
const showModelModal = ref(false);
const provForm = ref({
  name: '',
  provider_type: 'openai',
  api_key: '',
  base_url: '',
  default_model: '',
});
const modelForm = ref({
  provider_id: '',
  model_name: '',
  model_type: 'chat',
  temperature: '0.7',
  max_tokens: '4096',
});
const editProvId = ref<string | null>(null);

const providerLinks: Record<string, string> = {
  OpenAI: 'https://platform.openai.com/api-keys',
  DeepSeek: 'https://platform.deepseek.com/api_keys',
  NVIDIA: 'https://build.nvidia.com/explore/discover',
  Anthropic: 'https://console.anthropic.com/settings/keys',
  Gemini: 'https://aistudio.google.com/apikey',
};
const quickLinks = Object.entries(providerLinks).map(([name, url]) => ({ name, url }));
const modelCols = [
  { title: '提供商', key: 'provider_name', width: 110 },
  { title: '模型名称', dataIndex: 'model_name', width: 220, ellipsis: true },
  { title: '能力与接口', key: 'capability', width: 260 },
  { title: '排名顺序', key: 'sort_order', width: 108, align: 'center' as const },
  { title: '状态', key: 'status', width: 130 },
  { title: 'Temperature', dataIndex: 'temperature', width: 90 },
  { title: 'Max Tokens', dataIndex: 'max_tokens', width: 100 },
  { title: '启用', key: 'active', width: 70 },
];

const modelSummary = computed(() => summarizeModelStatus(models.value));
const modelSummaryMessage = computed(() => {
  const s = modelSummary.value;
  if (!s.total) return '暂无已启用模型';
  return `已启用 ${s.total} 个模型 · 可用 ${s.available} · 不可用 ${s.unavailable}${s.unknown ? ` · 未检测 ${s.unknown}` : ''}`;
});

function providerModelStats(p: any): string {
  const rows = models.value.filter((m) => m.provider_name === p.name && m.active !== false);
  if (!rows.length) return `模型: ${(p.models || []).length || 0} 个（加载中…）`;
  const stats = summarizeModelStatus(rows);
  return `${rows.length} 个模型 · 可用 ${stats.available} · 不可用 ${stats.unavailable}`;
}

async function loadProviders() {
  try {
    providers.value = await apiGet('/super-admin/ai-config/providers');
  } catch {
    /* non-blocking */
  }
}

async function loadModels() {
  modelsLoading.value = true;
  try {
    const rows = await apiGet<AiModelEnrichedRow[]>('/super-admin/ai-config/models', { enriched: true });
    models.value = sortModels(rows);
  } catch {
    try {
      const rows = await apiGet<AiModelEnrichedRow[]>('/super-admin/ai-config/models');
      models.value = sortModels(rows);
    } catch {
      /* non-blocking */
    }
  } finally {
    modelsLoading.value = false;
  }
}

function sortModels(rows: AiModelEnrichedRow[]): AiModelEnrichedRow[] {
  return [...rows].sort((a, b) => {
    const pa = a.provider_name || '';
    const pb = b.provider_name || '';
    if (pa !== pb) return pa.localeCompare(pb, 'zh-CN');
    return (a.sort_order || 0) - (b.sort_order || 0);
  });
}

function providerGroupKey(row: AiModelEnrichedRow): string {
  return row.provider_id || row.provider_name || '';
}

function providerSiblings(record: AiModelEnrichedRow): AiModelEnrichedRow[] {
  const key = providerGroupKey(record);
  return models.value
    .filter((m) => providerGroupKey(m) === key)
    .sort(
      (a, b) =>
        (a.sort_order || 0) - (b.sort_order || 0)
        || (a.model_name || '').localeCompare(b.model_name || '', 'zh-CN'),
    );
}

function rankIndex(record: AiModelEnrichedRow): number {
  return providerSiblings(record).findIndex((m) => m.id === record.id);
}

function displayRank(record: AiModelEnrichedRow): number {
  const idx = rankIndex(record);
  return idx >= 0 ? idx + 1 : record.sort_order || 0;
}

function canMoveRank(record: AiModelEnrichedRow, dir: 'up' | 'down'): boolean {
  const idx = rankIndex(record);
  if (idx < 0) return false;
  const last = providerSiblings(record).length - 1;
  return dir === 'up' ? idx > 0 : idx < last;
}

async function moveModelRank(record: AiModelEnrichedRow, dir: 'up' | 'down') {
  const siblings = providerSiblings(record);
  const idx = rankIndex(record);
  const targetIdx = dir === 'up' ? idx - 1 : idx + 1;
  if (idx < 0 || targetIdx < 0 || targetIdx >= siblings.length) return;

  const other = siblings[targetIdx];
  let myOrder = record.sort_order || idx + 1;
  let otherOrder = other.sort_order || targetIdx + 1;
  if (myOrder === otherOrder) {
    myOrder = idx + 1;
    otherOrder = targetIdx + 1;
  }

  rankBusy.value = record.id;
  try {
    await Promise.all([
      apiPut(`/super-admin/ai-config/models/${record.id}`, { sort_order: otherOrder }),
      apiPut(`/super-admin/ai-config/models/${other.id}`, { sort_order: myOrder }),
    ]);
    record.sort_order = otherOrder;
    other.sort_order = myOrder;
    models.value = sortModels([...models.value]);
  } catch (e: unknown) {
    message.error(apiErrorMessage(e, '调整排名失败'));
    await loadModels();
  } finally {
    rankBusy.value = null;
  }
}

async function probeModels() {
  probeLoading.value = true;
  try {
    const report = await apiPost<{ models: AiModelEnrichedRow[]; available_count: number; total: number }>(
      '/super-admin/ai-config/models/probe',
    );
    models.value = mergeProbeResults(models.value, report.models || []);
    message.success(`探测完成：${report.available_count}/${report.total} 可用`);
  } catch (e: unknown) {
    message.error(apiErrorMessage(e, '探测失败'));
  } finally {
    probeLoading.value = false;
  }
}

async function toggleProvider(id: string, v: boolean) {
  try {
    await apiPut(`/super-admin/ai-config/providers/${id}`, { enabled: v });
    message.success('已更新');
    loadProviders();
  } catch (e: unknown) {
    message.error(apiErrorMessage(e, '切换失败'));
  }
}

async function toggleModel(id: string, v: boolean) {
  try {
    await apiPut(`/super-admin/ai-config/models/${id}`, { active: v });
    message.success('已更新');
    loadModels();
  } catch (e: unknown) {
    message.error(apiErrorMessage(e, '切换失败'));
  }
}

async function saveProvider() {
  try {
    const payload = { ...provForm.value, enabled: true };
    if (editProvId.value) {
      await apiPut(`/super-admin/ai-config/providers/${editProvId.value}`, payload);
    } else {
      await apiPost('/super-admin/ai-config/providers', payload);
    }
    showProviderModal.value = false;
    editProvId.value = null;
    provForm.value = { name: '', provider_type: 'openai', api_key: '', base_url: '', default_model: '' };
    message.success('保存成功');
    await loadProviders();
    await loadModels();
  } catch (e: unknown) {
    message.error(apiErrorMessage(e, '保存失败'));
  }
}

function openEditProvider(p: any) {
  editProvId.value = p.id;
  provForm.value = {
    name: p.name,
    provider_type: p.provider_type,
    api_key: '',
    base_url: p.base_url || '',
    default_model: p.default_model || '',
  };
  showProviderModal.value = true;
}

async function deleteProvider(id: string) {
  try {
    await apiDelete(`/super-admin/ai-config/providers/${id}`);
    message.success('已删除');
    loadProviders();
  } catch {
    message.error('删除失败');
  }
}

function openLink(url: string) {
  window.open(url, '_blank');
}

async function saveModel() {
  try {
    await apiPost('/super-admin/ai-config/models', modelForm.value);
    showModelModal.value = false;
    message.success('添加成功');
    loadModels();
  } catch {
    message.error('添加失败');
  }
}

onMounted(() => {
  loadProviders();
  loadModels();
});
</script>

<style scoped lang="scss">
.glass {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 22px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.08);
  backdrop-filter: blur(16px);
}

.panel {
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
}

.h2 {
  margin: 0 0 0.75rem;
  font-size: 1.05rem;
  font-weight: 600;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  gap: 12px;

  .h2 {
    margin: 0;
  }
}

.cap-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
}

.cap-desc {
  font-size: 0.72rem;
  color: #64748b;
  line-height: 1.35;
  max-width: 240px;
}

.rank-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.rank-num {
  min-width: 18px;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: #334155;
}

.rank-actions {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.rank-btn {
  width: 22px;
  height: 18px;
  padding: 0;
  line-height: 1;
  color: #64748b;

  &:not(:disabled):hover {
    color: var(--uj-brand, #4a9b8c);
  }
}

.provider-card {
  margin-bottom: 12px;
}

.card-meta {
  font-size: 0.8rem;
  color: #64748b;
  margin: 4px 0;
}

.card-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.link-btn {
  font-size: 0.8rem;
  color: #1890ff;
}

.link-card {
  cursor: pointer;
  text-align: center;

  .link-name {
    font-weight: 600;
  }

  .link-url {
    font-size: 0.72rem;
    color: #94a3b8;
    word-break: break-all;
  }
}
</style>
