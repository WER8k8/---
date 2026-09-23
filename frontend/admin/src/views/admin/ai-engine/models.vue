/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
 <YdPage title="模型管理" subtitle="管理 AI 模型、版本和部署配置" surface="elevated">
 <template #actions>
 <a-button type="primary" @click="openModelModal()">
 <PlusOutlined />
 添加模型
 </a-button>
 </template>
 <div class="models-page">
 <a-alert
 v-if="loadError"
 type="warning"
 show-icon
 :message="loadError"
 style="margin-bottom: 16px"
 />
 <div class="model-grid">
 <div class="model-card" v-for="model in models" :key="model.id">
 <div class="card-header">
 <div class="model-icon">
 <ExperimentOutlined />
 </div>
 <div class="model-header-info">
 <h3 class="model-name">{{ model.name }}</h3>
 <span class="model-type">{{ model.type }}</span>
 </div>
 <a-badge :status="model.enabled ? 'success' : 'warning'" />
 </div>
 <div class="card-body">
 <p class="model-desc">{{ model.description }}</p>
 <div class="model-meta">
 <span class="meta-item">版本: {{ model.version }}</span>
 <span class="meta-item">Token限制: {{ model.maxTokens }}</span>
 <span class="meta-item">价格: {{ model.price }}</span>
 </div>
 </div>
 <div class="card-footer">
 <a-button size="small" @click="editModel(model)">配置</a-button>
 <a-button size="small" :type="model.enabled ? 'default' : 'primary'" :loading="togglingId === model.id" @click="toggleModel(model)">
 {{ model.enabled ? '禁用' : '启用' }}
 </a-button>
 </div>
 </div>
 </div>

 <a-modal v-model:open="showModelModal" :title="editingId ? '配置 AI 模型' : '添加 AI 模型'" :footer="null">
 <a-form :model="modelForm" :rules="modelRules" ref="modelFormRef">
 <a-form-item label="提供商" name="provider_id" v-if="!editingId">
 <a-select v-model:value="modelForm.provider_id" placeholder="请选择提供商">
 <a-select-option v-for="p in providers" :key="p.id" :value="p.id">
 {{ p.name }}
 </a-select-option>
 </a-select>
 </a-form-item>
 <a-form-item label="模型名称" name="name">
 <a-input v-model:value="modelForm.name" placeholder="请输入模型名称" />
 </a-form-item>
 <a-form-item label="模型类型" name="type">
 <a-select v-model:value="modelForm.type">
 <a-select-option value="chat">对话模型</a-select-option>
 <a-select-option value="completion">补全模型</a-select-option>
 <a-select-option value="embedding">嵌入模型</a-select-option>
 </a-select>
 </a-form-item>
 <a-form-item label="版本号" name="version">
 <a-input v-model:value="modelForm.version" placeholder="请输入版本号" />
 </a-form-item>
 <a-form-item label="最大Token" name="maxTokens">
 <a-input-number v-model:value="modelForm.maxTokens" :min="100" :max="100000" />
 </a-form-item>
 <a-form-item label="模型描述" name="description">
 <a-textarea v-model:value="modelForm.description" placeholder="请输入模型描述" :rows="3" />
 </a-form-item>
 <div class="modal-footer">
 <a-button @click="closeModelModal">取消</a-button>
 <a-button type="primary" :loading="saving" @click="submitModelForm">确定</a-button>
 </div>
 </a-form>
 </a-modal>
 </div>
 </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet, apiPost, apiPut } from '@/utils/api';
import { YdPage } from '@/components/youding';
import { PlusOutlined, ExperimentOutlined } from '@ant-design/icons-vue';

interface Model {
 id: string;
 name: string;
 type: string;
 version: string;
 description: string;
 maxTokens: string;
 price: string;
 status: string;
 enabled: boolean;
 provider_id: string;
 is_default: boolean;
}

interface Provider {
 id: string;
 name: string;
}

const showModelModal = ref(false);
const editingId = ref<string | null>(null);
const saving = ref(false);
const togglingId = ref<string | null>(null);
const loadError = ref('');
const models = ref<Model[]>([]);
const providers = ref<Provider[]>([]);

const modelForm = reactive({
 provider_id: '',
 name: '',
 type: 'chat',
 version: '',
 maxTokens: 4096,
 description: '',
});

const modelRules = {
 name: [{ required: true, message: '请输入模型名称' }],
 type: [{ required: true, message: '请选择模型类型' }],
 version: [{ required: true, message: '请输入版本号' }],
 provider_id: [{ required: true, message: '请选择提供商' }],
};

const typeLabels: Record<string, string> = {
 chat: '对话模型',
 completion: '补全模型',
 embedding: '嵌入模型',
};

function mapModel(raw: any): Model {
 const type = String(raw.model_type ?? 'chat');
 return {
 id: String(raw.id),
 name: String(raw.model_name ?? ''),
 type: typeLabels[type] || type,
 version: String(raw.temperature ?? '-'),
 description: raw.provider_name ? `提供商：${raw.provider_name}` : 'AI 模型配置',
 maxTokens: String(raw.max_tokens ?? '-'),
 price: raw.is_default ? '默认' : '-',
 status: raw.is_active || raw.active ? 'active' : 'disabled',
 enabled: !!(raw.is_active ?? raw.active),
 provider_id: String(raw.provider_id ?? ''),
 is_default: !!raw.is_default,
 };
}

async function loadProviders() {
 try {
 const res = await apiGet<any>('/super-admin/ai-config/providers');
 const list = Array.isArray(res) ? res : res?.data ?? [];
 providers.value = list.map((p: any) => ({ id: String(p.id), name: String(p.name ?? '') }));
 } catch {
 providers.value = [];
 }
}

async function loadModels() {
 loadError.value = '';
 try {
 const res = await apiGet<any>('/super-admin/ai-config/models');
 const list = Array.isArray(res) ? res : res?.data ?? [];
 models.value = list.map(mapModel);
 } catch (e: any) {
 loadError.value = e?.message || '模型列表加载失败';
 models.value = [];
 }
}

function openModelModal(model?: Model) {
 if (model) {
 editingId.value = model.id;
 modelForm.provider_id = model.provider_id;
 modelForm.name = model.name;
 const key = Object.keys(typeLabels).find((k) => typeLabels[k] === model.type) || 'chat';
 modelForm.type = key;
 modelForm.version = model.version === '-' ? '' : model.version;
 const parsed = parseInt(String(model.maxTokens).replace(/\D/g, ''), 10);
 modelForm.maxTokens = Number.isFinite(parsed) && parsed > 0 ? parsed : 4096;
 modelForm.description = model.description;
 } else {
 editingId.value = null;
 modelForm.provider_id = providers.value[0]?.id ?? '';
 modelForm.name = '';
 modelForm.type = 'chat';
 modelForm.version = '';
 modelForm.maxTokens = 4096;
 modelForm.description = '';
 }
 showModelModal.value = true;
}

function closeModelModal() {
 showModelModal.value = false;
 editingId.value = null;
}

const editModel = (model: Model) => {
 openModelModal(model);
};

const toggleModel = async (model: Model) => {
 togglingId.value = model.id;
 const next = !model.enabled;
 try {
 await apiPut(`/super-admin/ai-config/models/${model.id}`, { active: next });
 model.enabled = next;
 model.status = next ? 'active' : 'disabled';
 message.success(next ? `已启用 ${model.name}` : `已禁用 ${model.name}`);
 await loadModels();
 } catch (e: any) {
 message.error(e?.message || '模型状态更新失败');
 } finally {
 togglingId.value = null;
 }
};

const submitModelForm = async () => {
 if (!modelForm.name.trim()) {
 message.warning('请输入模型名称');
 return;
 }
 if (!editingId.value && !modelForm.provider_id) {
 message.warning('请选择提供商');
 return;
 }
 saving.value = true;
 try {
 const payload: Record<string, unknown> = {
 model_name: modelForm.name.trim(),
 model_type: modelForm.type,
 max_tokens: String(modelForm.maxTokens),
 temperature: modelForm.version || '0.7',
 };
 if (editingId.value) {
 await apiPut(`/super-admin/ai-config/models/${editingId.value}`, payload);
 message.success('模型配置已更新');
 } else {
 await apiPost('/super-admin/ai-config/models', {
 ...payload,
 provider_id: modelForm.provider_id,
 is_active: true,
 });
 message.success('模型已添加');
 }
 closeModelModal();
 await loadModels();
 } catch (e: any) {
 message.error(e?.message || '模型保存失败');
 } finally {
 saving.value = false;
 }
};

onMounted(async () => {
 await Promise.all([loadProviders(), loadModels()]);
});
</script>

<style scoped lang="scss">
.models-page {
 padding: 24px;
}

.model-grid {
 display: grid;
 grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
 gap: 16px;
}

.model-card {
 background: #fff;
 border-radius: 12px;
 padding: 20px;
 box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
 display: flex;
 flex-direction: column;
 gap: 12px;
}

.card-header {
 display: flex;
 align-items: center;
 gap: 12px;
}

.model-icon {
 width: 40px;
 height: 40px;
 border-radius: 10px;
 background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
 color: #fff;
 display: flex;
 align-items: center;
 justify-content: center;
 font-size: 18px;
}

.model-header-info {
 flex: 1;
 min-width: 0;

 .model-name {
 margin: 0;
 font-size: 16px;
 font-weight: 500;
 color: #1f2937;
 }

 .model-type {
 font-size: 12px;
 color: #6b7280;
 }
}

.model-desc {
 margin: 0;
 font-size: 13px;
 color: #6b7280;
 min-height: 40px;
}

.model-meta {
 display: flex;
 flex-wrap: wrap;
 gap: 8px 12px;
 font-size: 12px;
 color: #9ca3af;
}

.card-footer {
 display: flex;
 justify-content: flex-end;
 gap: 8px;
}

.modal-footer {
 display: flex;
 justify-content: flex-end;
 gap: 12px;
 margin-top: 24px;
}
</style>
