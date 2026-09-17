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
    <div class="model-grid">
      <div
        class="model-card"
        v-for="model in models"
        :key="model.id"
      >
        <div class="card-header">
          <div class="model-icon">
            <ExperimentOutlined />
          </div>
          <div class="model-header-info">
            <h3 class="model-name">
              {{ model.name }}
            </h3>
            <span class="model-type">{{ model.type }}</span>
          </div>
          <a-badge :status="model.status === 'active' ? 'success' : 'warning'" />
        </div>
        <div class="card-body">
          <p class="model-desc">
            {{ model.description }}
          </p>
          <div class="model-meta">
            <span class="meta-item">版本: {{ model.version }}</span>
            <span class="meta-item">Token限制: {{ model.maxTokens }}</span>
            <span class="meta-item">价格: {{ model.price }}</span>
          </div>
        </div>
        <div class="card-footer">
          <a-button
            size="small"
            @click="editModel(model)"
          >
            配置
          </a-button>
          <a-button
            size="small"
            :type="model.enabled ? 'default' : 'primary'"
            @click="toggleModel(model)"
          >
            {{ model.enabled ? '禁用' : '启用' }}
          </a-button>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="showModelModal"
      :title="editingId ? '配置 AI 模型' : '添加 AI 模型'"
      :footer="null"
    >
      <a-form
        :model="modelForm"
        :rules="modelRules"
        ref="modelFormRef"
      >
        <a-form-item
          label="模型名称"
          name="name"
        >
          <a-input
            v-model:value="modelForm.name"
            placeholder="请输入模型名称"
          />
        </a-form-item>
        <a-form-item
          label="模型类型"
          name="type"
        >
          <a-select v-model:value="modelForm.type">
            <a-select-option value="chat">
              对话模型
            </a-select-option>
            <a-select-option value="completion">
              补全模型
            </a-select-option>
            <a-select-option value="embedding">
              嵌入模型
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item
          label="版本号"
          name="version"
        >
          <a-input
            v-model:value="modelForm.version"
            placeholder="请输入版本号"
          />
        </a-form-item>
        <a-form-item
          label="最大Token"
          name="maxTokens"
        >
          <a-input-number
            v-model:value="modelForm.maxTokens"
            :min="100"
            :max="100000"
          />
        </a-form-item>
        <a-form-item
          label="模型描述"
          name="description"
        >
          <a-textarea
            v-model:value="modelForm.description"
            placeholder="请输入模型描述"
            :rows="3"
          />
        </a-form-item>
        <div class="modal-footer">
          <a-button @click="closeModelModal">
            取消
          </a-button>
          <a-button
            type="primary"
            @click="submitModelForm"
          >
            确定
          </a-button>
        </div>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import { PlusOutlined, ExperimentOutlined } from '@ant-design/icons-vue';

onMounted(async () => {
  try { await apiGet('/ai-config'); } catch { /* 空状态 */ }
});

interface Model {
  id: number;
  name: string;
  type: string;
  version: string;
  description: string;
  maxTokens: string;
  price: string;
  status: string;
  enabled: boolean;
}

const showModelModal = ref(false);
const editingId = ref<number | null>(null);

const modelForm = reactive({
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
};

const models = ref<Model[]>([
  {
    id: 1,
    name: 'GPT-4o',
    type: '对话模型',
    version: 'v1.0',
    description: 'OpenAI最新一代大语言模型，支持多模态输入',
    maxTokens: '128K',
    price: '$0.01/1K',
    status: 'active',
    enabled: true,
  },
  {
    id: 2,
    name: 'Claude 3.5 Sonnet',
    type: '对话模型',
    version: 'v3.5',
    description: 'Anthropic推出的高性能AI模型',
    maxTokens: '200K',
    price: '$0.008/1K',
    status: 'active',
    enabled: true,
  },
  {
    id: 3,
    name: 'Doubao Seed 2.0',
    type: '对话模型',
    version: 'v2.0',
    description: '字节跳动自研大模型，中文能力优秀',
    maxTokens: '64K',
    price: '$0.005/1K',
    status: 'active',
    enabled: true,
  },
  {
    id: 4,
    name: 'GLM-5.1',
    type: '对话模型',
    version: 'v5.1',
    description: '智谱AI大模型，数学推理能力强',
    maxTokens: '128K',
    price: '$0.006/1K',
    status: 'active',
    enabled: false,
  },
  {
    id: 5,
    name: 'Qwen 3.6',
    type: '对话模型',
    version: 'v3.6',
    description: '阿里云通义千问最新版本',
    maxTokens: '128K',
    price: '$0.007/1K',
    status: 'active',
    enabled: true,
  },
]);

function openModelModal(model?: Model) {
  if (model) {
    editingId.value = model.id;
    modelForm.name = model.name;
    modelForm.type = model.type.includes('对话') ? 'chat' : model.type.includes('补全') ? 'completion' : 'embedding';
    modelForm.version = model.version;
    modelForm.description = model.description;
    const parsed = parseInt(String(model.maxTokens).replace(/\D/g, ''), 10);
    modelForm.maxTokens = Number.isFinite(parsed) && parsed > 0 ? parsed : 4096;
  } else {
    editingId.value = null;
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

const toggleModel = (model: Model) => {
  model.enabled = !model.enabled;
  message.success(model.enabled ? `已启用 ${model.name}` : `已禁用 ${model.name}`);
};

const typeLabels: Record<string, string> = {
  chat: '对话模型',
  completion: '补全模型',
  embedding: '嵌入模型',
};

const submitModelForm = () => {
  const typeLabel = typeLabels[modelForm.type] || modelForm.type;
  if (editingId.value != null) {
    const idx = models.value.findIndex((m) => m.id === editingId.value);
    if (idx > -1) {
      models.value[idx] = {
        ...models.value[idx],
        name: modelForm.name,
        type: typeLabel,
        version: modelForm.version,
        description: modelForm.description,
        maxTokens: String(modelForm.maxTokens),
      };
      message.success('模型配置已更新');
    }
  } else {
    models.value.push({
      id: Date.now(),
      name: modelForm.name,
      type: typeLabel,
      version: modelForm.version,
      description: modelForm.description,
      maxTokens: String(modelForm.maxTokens),
      price: '$0.01/1K',
      status: 'active',
      enabled: true,
    });
    message.success('模型已添加');
  }
  closeModelModal();
};
</script>

<style scoped lang="scss">
.models-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  .header-left {
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: #1f2937;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .page-desc {
      font-size: 14px;
      color: #6b7280;
      margin-top: 4px;
    }
  }

  .add-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
    color: #fff;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
  }
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.model-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition:
    transform 0.2s,
    box-shadow 0.2s;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;

    .model-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: #fff;
    }

    .model-header-info {
      flex: 1;

      .model-name {
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
        margin-bottom: 2px;
      }

      .model-type {
        font-size: 12px;
        color: #6b7280;
        background: #f3f4f6;
        padding: 2px 8px;
        border-radius: 4px;
      }
    }
  }

  .card-body {
    .model-desc {
      font-size: 13px;
      color: #6b7280;
      line-height: 1.5;
      margin: 0;
      margin-bottom: 12px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .model-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;

      .meta-item {
        font-size: 12px;
        color: #9ca3af;
        background: #f9fafb;
        padding: 4px 8px;
        border-radius: 4px;
      }
    }
  }

  .card-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #f3f4f6;
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

@media (max-width: 1200px) {
  .model-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .model-grid {
    grid-template-columns: 1fr;
  }
}
</style>
