/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage class="ai-center-models" title="模型管理" subtitle="管理 AI 提供商与模型配置" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showProvModal = true">
        <PlusOutlined />
        添加提供商
      </a-button>
    </template>

    <!-- Provider Cards -->
    <a-card title="提供商管理" class="section-card">
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" :lg="8" v-for="p in providers" :key="p.id">
          <a-card size="small" class="provider-card" :hoverable="true">
            <template #title>
              <span class="provider-name">{{ p.name }}</span>
              <a-tag :color="providerConfiguredTagColor(p)" style="margin-left:8px">
                {{ providerConfiguredLabel(p) }}
              </a-tag>
            </template>
            <template #extra>
              <a-switch :checked="p.enabled" size="small" @change="(v:any) => toggleProvider(p.id, !!v)" />
            </template>
            <div class="provider-detail">
              <div class="detail-row">
                <span class="detail-label">类型:</span>
                <span class="detail-value">{{ p.provider_type }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">API Key:</span>
                <span class="detail-value key-masked">{{ maskApiKey(p.api_key || p.api_key_masked) }}</span>
              </div>
              <div class="detail-row" v-if="p.base_url">
                <span class="detail-label">Base URL:</span>
                <span class="detail-value url-text">{{ p.base_url }}</span>
              </div>
              <div class="detail-row" v-if="p.default_model">
                <span class="detail-label">默认模型:</span>
                <span class="detail-value">{{ p.default_model }}</span>
              </div>
            </div>
            <div class="card-actions">
              <a-button size="small" @click="editProvider(p)">编辑</a-button>
              <a-button size="small" danger @click="delProvider(p.id)">删除</a-button>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </a-card>

    <!-- Models Table -->
    <a-card title="模型列表" class="section-card">
      <template #extra>
        <a-button type="dashed" size="small" @click="showModelModal = true">添加模型</a-button>
      </template>
      <div ref="modelsPanelRef" class="yd-panel yd-table-panel">
        <YdTableToolbar
          :loading="modelsLoading"
          :target-ref="modelsPanelRef"
          :show-export="false"
          @refresh="loadModels"
        />
        <YdDataTable
          :columns="modelCols"
          :data-source="models"
          :loading="modelsLoading"
          :pagination="false"
          :table-props="{ size: tableSize, rowKey: 'id' }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'provider_name'">
              <a-tag>{{ record.provider_name }}</a-tag>
            </template>
            <template v-if="column.key === 'active'">
              <a-switch :checked="record.active" size="small" @change="(v:any) => toggleModel(record.id, !!v)" />
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>

    <!-- Add/Edit Provider Modal -->
    <a-modal v-model:open="showProvModal" :title="editId ? '编辑提供商' : '添加提供商'" @ok="saveProvider">
      <a-form :model="pf" layout="vertical">
        <a-form-item label="名称"><a-input v-model:value="pf.name" placeholder="如 OpenAI" /></a-form-item>
        <a-form-item label="类型"><a-select v-model:value="pf.provider_type">
          <a-select-option value="openai">OpenAI</a-select-option>
          <a-select-option value="deepseek">DeepSeek</a-select-option>
          <a-select-option value="nvidia">NVIDIA</a-select-option>
          <a-select-option value="anthropic">Anthropic</a-select-option>
          <a-select-option value="gemini">Gemini</a-select-option>
          <a-select-option value="siliconflow">硅基流动</a-select-option>
        </a-select></a-form-item>
        <a-form-item label="API Key"><a-input-password v-model:value="pf.api_key" placeholder="sk-..." /></a-form-item>
        <a-form-item label="Base URL"><a-input v-model:value="pf.base_url" placeholder="https://api.openai.com/v1" /></a-form-item>
        <a-form-item label="默认模型"><a-input v-model:value="pf.default_model" placeholder="gpt-4o" /></a-form-item>
      </a-form>
    </a-modal>

    <!-- Add Model Modal -->
    <a-modal v-model:open="showModelModal" title="添加模型" @ok="saveModel">
      <a-form :model="mf" layout="vertical">
        <a-form-item label="提供商"><a-select v-model:value="mf.provider_id">
          <a-select-option v-for="p in providers" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
        </a-select></a-form-item>
        <a-form-item label="模型名"><a-input v-model:value="mf.model_name" placeholder="gpt-4o" /></a-form-item>
        <a-form-item label="类型"><a-select v-model:value="mf.model_type">
          <a-select-option value="chat">Chat</a-select-option>
          <a-select-option value="embedding">Embedding</a-select-option>
          <a-select-option value="image">Image</a-select-option>
        </a-select></a-form-item>
        <a-form-item label="Temperature"><a-input-number v-model:value="mf.temperature" :min="0" :max="2" :step="0.1" style="width:100%" /></a-form-item>
        <a-form-item label="Max Tokens"><a-input-number v-model:value="mf.max_tokens" :min="128" :step="128" style="width:100%" /></a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { message } from 'ant-design-vue'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { PlusOutlined } from '@ant-design/icons-vue'
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api'
import {
  apiErrorMessage,
  maskApiKey,
  providerConfiguredLabel,
  providerConfiguredTagColor,
} from '@/utils/aiConfigHelpers'

const modelsPanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const providers = ref<any[]>([])
const models = ref<any[]>([])
const modelsLoading = ref(false)
const showProvModal = ref(false)
const showModelModal = ref(false)
const editId = ref<string | null>(null)
const pf = ref({ name: '', provider_type: 'openai', api_key: '', base_url: '', default_model: '' })
const mf = ref({ provider_id: '', model_name: '', model_type: 'chat', temperature: 0.7, max_tokens: 4096 })

const modelCols = [
  { title: '提供商', key: 'provider_name', width: 120 },
  { title: '模型名称', dataIndex: 'model_name', width: 160 },
  { title: '类型', dataIndex: 'model_type', width: 100 },
  { title: 'Temperature', dataIndex: 'temperature', width: 110 },
  { title: 'Max Tokens', dataIndex: 'max_tokens', width: 110 },
  { title: '启用', key: 'active', width: 80 },
]


async function loadProviders() {
  try { providers.value = await apiGet('/super-admin/ai-config/providers') } catch { message.error('加载提供商失败') }
}
async function loadModels() {
  modelsLoading.value = true
  try { models.value = await apiGet('/super-admin/ai-config/models') } catch { message.error('加载模型失败') } finally { modelsLoading.value = false }
}
async function toggleProvider(id: string, v: boolean) {
  try {
    await apiPut(`/super-admin/ai-config/providers/${id}`, { enabled: v })
    message.success('已更新')
    loadProviders()
  } catch (e: unknown) {
    message.error(apiErrorMessage(e, '切换失败'))
  }
}
async function toggleModel(id: string, v: boolean) {
  try {
    await apiPut(`/super-admin/ai-config/models/${id}`, { active: v })
    message.success('已更新')
    loadModels()
  } catch (e: unknown) {
    message.error(apiErrorMessage(e, '切换失败'))
  }
}
async function saveProvider() {
  try {
    const payload = { ...pf.value, enabled: true }
    if (editId.value) await apiPut(`/super-admin/ai-config/providers/${editId.value}`, payload)
    else await apiPost('/super-admin/ai-config/providers', payload)
    showProvModal.value = false; editId.value = null
    pf.value = { name: '', provider_type: 'openai', api_key: '', base_url: '', default_model: '' }
    message.success('保存成功'); loadProviders()
  } catch (e: unknown) { message.error(apiErrorMessage(e, '保存失败')) }
}
function editProvider(p: any) {
  editId.value = p.id
  pf.value = { name: p.name, provider_type: p.provider_type, api_key: '', base_url: p.base_url || '', default_model: p.default_model || '' }
  showProvModal.value = true
}
async function delProvider(id: string) {
  try { await apiDelete(`/super-admin/ai-config/providers/${id}`); message.success('已删除'); loadProviders() } catch { message.error('删除失败') }
}
async function saveModel() {
  try {
    await apiPost('/super-admin/ai-config/models', mf.value)
    showModelModal.value = false; message.success('添加成功')
    mf.value = { provider_id: '', model_name: '', model_type: 'chat', temperature: 0.7, max_tokens: 4096 }
    loadModels()
  } catch { message.error('添加失败') }
}

onMounted(() => { loadProviders(); loadModels() })
</script>

<style scoped lang="scss">
.ai-center-models {
  .section-card {
    margin-bottom: 20px;
    border-radius: 12px;
  }

  .provider-card {
    height: 100%;

    .provider-name {
      font-weight: 600;
    }

    .provider-detail {
      margin: 8px 0;

      .detail-row {
        display: flex;
        gap: 6px;
        font-size: 13px;
        margin-bottom: 4px;

        .detail-label {
          color: #94a3b8;
          flex-shrink: 0;
        }
        .detail-value {
          color: #1f2937;
          word-break: break-all;
        }
        .key-masked {
          font-family: monospace;
          color: #64748b;
        }
        .url-text {
          font-size: 12px;
        }
      }
    }

    .card-actions {
      display: flex;
      gap: 8px;
      justify-content: flex-end;
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #f3f4f6;
    }
  }
}
</style>
