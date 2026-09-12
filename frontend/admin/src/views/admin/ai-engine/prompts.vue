<template>
  <YdPage title="提示词管理" subtitle="管理和优化 AI 提示词模板" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showPromptModal = true">
        <PlusOutlined />
        添加提示词
      </a-button>
    </template>
  <div class="prompts-page">
    <div class="tabs-container">
      <a-tabs v-model:active-key="activeTab">
        <a-tab-pane
          key="list"
          tab="提示词列表"
        >
          <div class="table-container">
            <a-table
              :columns="columns"
              :data-source="prompts"
              :pagination="pagination"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'category'">
                  <a-tag :color="getCategoryColor(record.category)">
                    {{ record.category }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button
                      size="small"
                      @click="editPrompt(record as Prompt)"
                    >
                      编辑
                    </a-button>
                    <a-button
                      size="small"
                      danger
                      @click="deletePrompt(record as Prompt)"
                    >
                      删除
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </div>
        </a-tab-pane>
        <a-tab-pane
          key="templates"
          tab="提示词模板"
        >
          <div class="templates-grid">
            <div
              class="template-card"
              v-for="template in templates"
              :key="template.id"
            >
              <div
                class="template-icon"
                :class="getTemplateIconClass(template.category)"
              >
                <component :is="template.icon" />
              </div>
              <h3 class="template-name">
                {{ template.name }}
              </h3>
              <p class="template-desc">
                {{ template.description }}
              </p>
              <button
                class="use-template-btn"
                @click="useTemplate(template)"
              >
                使用模板
              </button>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>

    <a-modal
      v-model:open="showPromptModal"
      :title="editingId ? '编辑提示词' : '添加提示词'"
      :footer="null"
    >
      <a-form
        :model="promptForm"
        :rules="promptRules"
        ref="promptFormRef"
      >
        <a-form-item
          label="提示词名称"
          name="name"
        >
          <a-input
            v-model:value="promptForm.name"
            placeholder="请输入提示词名称"
          />
        </a-form-item>
        <a-form-item
          label="分类"
          name="category"
        >
          <a-select v-model:value="promptForm.category">
            <a-select-option value="代码生成">
              代码生成
            </a-select-option>
            <a-select-option value="文档撰写">
              文档撰写
            </a-select-option>
            <a-select-option value="数据分析">
              数据分析
            </a-select-option>
            <a-select-option value="创意写作">
              创意写作
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item
          label="提示词内容"
          name="content"
        >
          <a-textarea
            v-model:value="promptForm.content"
            placeholder="请输入提示词内容"
            :rows="6"
          />
        </a-form-item>
        <div class="modal-footer">
          <a-button @click="closePromptModal">
            取消
          </a-button>
          <a-button
            type="primary"
            @click="submitPromptForm"
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
import {
  PlusOutlined,
  CodeOutlined,
  FileTextOutlined,
  BarChartOutlined,
  EditOutlined,
} from '@ant-design/icons-vue';
import type { TableColumnsType } from 'ant-design-vue';

onMounted(async () => {
  try { await apiGet('/ai/templates'); } catch { /* 空状态 */ }
});

interface Prompt {
  id: number;
  name: string;
  category: string;
  content: string;
  usageCount: number;
  createTime: string;
}

interface Template {
  id: number;
  name: string;
  category: string;
  description: string;
  icon: any;
}

const activeTab = ref('list');
const showPromptModal = ref(false);
const editingId = ref<number | null>(null);

const promptForm = reactive({
  name: '',
  category: '代码生成',
  content: '',
});

const promptRules = {
  name: [{ required: true, message: '请输入提示词名称' }],
  content: [{ required: true, message: '请输入提示词内容' }],
};

const columns: TableColumnsType<Prompt> = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '分类', dataIndex: 'category', key: 'category' },
  { title: '使用次数', dataIndex: 'usageCount', key: 'usageCount', width: 100 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 160 },
  { title: '操作', key: 'actions' },
];

const prompts = ref<Prompt[]>([
  {
    id: 1,
    name: '代码生成模板',
    category: '代码生成',
    content: '请帮我生成一个Vue3组件...',
    usageCount: 128,
    createTime: '2024-01-15 10:30:00',
  },
  {
    id: 2,
    name: 'API文档生成',
    category: '文档撰写',
    content: '根据以下API定义生成文档...',
    usageCount: 86,
    createTime: '2024-01-14 15:20:00',
  },
  {
    id: 3,
    name: 'SQL查询优化',
    category: '数据分析',
    content: '请优化以下SQL查询...',
    usageCount: 64,
    createTime: '2024-01-13 09:45:00',
  },
  {
    id: 4,
    name: '产品描述撰写',
    category: '创意写作',
    content: '请为以下产品撰写描述...',
    usageCount: 42,
    createTime: '2024-01-12 14:10:00',
  },
]);

const templates = ref<Template[]>([
  {
    id: 1,
    name: '代码审查',
    category: '代码生成',
    description: '审查代码质量和潜在问题',
    icon: CodeOutlined,
  },
  {
    id: 2,
    name: '单元测试',
    category: '代码生成',
    description: '为现有代码生成单元测试',
    icon: CodeOutlined,
  },
  {
    id: 3,
    name: '技术方案',
    category: '文档撰写',
    description: '生成技术方案文档',
    icon: FileTextOutlined,
  },
  {
    id: 4,
    name: '数据报告',
    category: '数据分析',
    description: '分析数据并生成报告',
    icon: BarChartOutlined,
  },
  {
    id: 5,
    name: '营销文案',
    category: '创意写作',
    description: '生成营销推广文案',
    icon: EditOutlined,
  },
]);

const pagination = {
  pageSize: 10,
  showSizeChanger: true,
};

const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    代码生成: 'blue',
    文档撰写: 'purple',
    数据分析: 'green',
    创意写作: 'orange',
  };
  return colors[category] || 'gray';
};

const getTemplateIconClass = (category: string) => {
  const classes: Record<string, string> = {
    代码生成: 'bg-blue',
    文档撰写: 'bg-purple',
    数据分析: 'bg-green',
    创意写作: 'bg-orange',
  };
  return classes[category] || 'bg-gray';
};

const editPrompt = (record: Prompt) => {
  editingId.value = record.id;
  promptForm.name = record.name;
  promptForm.category = record.category;
  promptForm.content = record.content;
  showPromptModal.value = true;
};

function closePromptModal() {
  showPromptModal.value = false;
  editingId.value = null;
  promptForm.name = '';
  promptForm.category = '代码生成';
  promptForm.content = '';
}

const deletePrompt = (record: Prompt) => {
  const index = prompts.value.findIndex((p) => p.id === record.id);
  if (index > -1) {
    prompts.value.splice(index, 1);
  }
};

const useTemplate = (template: Template) => {
  promptForm.name = `${template.name}（基于模板）`;
  promptForm.category = template.category;
  promptForm.content = '';
  activeTab.value = 'list';
  showPromptModal.value = true;
  message.success(`已载入「${template.name}」模板，请补充内容后保存`);
};

const submitPromptForm = () => {
  if (editingId.value != null) {
    const idx = prompts.value.findIndex((p) => p.id === editingId.value);
    if (idx > -1) {
      prompts.value[idx] = {
        ...prompts.value[idx],
        name: promptForm.name,
        category: promptForm.category,
        content: promptForm.content,
      };
      message.success('提示词已更新');
    }
  } else {
    prompts.value.unshift({
      id: Date.now(),
      ...promptForm,
      usageCount: 0,
      createTime: new Date().toLocaleString('zh-CN'),
    });
    message.success('提示词已添加');
  }
  closePromptModal();
};
</script>

<style scoped lang="scss">
.prompts-page {
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

.tabs-container {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.table-container {
  padding: 20px;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 20px;

  .template-card {
    background: #f9fafb;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: transform 0.2s;

    &:hover {
      transform: translateY(-4px);
    }

    .template-icon {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: #fff;
      margin: 0 auto 12px;

      &.bg-blue {
        background: linear-gradient(135deg, #4a9b8c 0%, #2a6b60 100%);
      }
      &.bg-purple {
        background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
      }
      &.bg-green {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      }
      &.bg-orange {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
      }
    }

    .template-name {
      font-size: 15px;
      font-weight: 600;
      color: #1f2937;
      margin: 0;
      margin-bottom: 6px;
    }

    .template-desc {
      font-size: 13px;
      color: #6b7280;
      margin: 0;
      margin-bottom: 12px;
    }

    .use-template-btn {
      padding: 6px 16px;
      background: #fff;
      border: 1px solid #4a9b8c;
      color: #4a9b8c;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      transition: all 0.2s;

      &:hover {
        background: #4a9b8c;
        color: #fff;
      }
    }
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

@media (max-width: 1024px) {
  .templates-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
