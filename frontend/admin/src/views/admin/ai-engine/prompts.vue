/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
 <YdPage title="提示词管理" subtitle="管理和优化 AI 提示词模板" surface="elevated">
 <template #actions>
 <a-button type="primary" @click="openCreate">
 <PlusOutlined />
 添加提示词
 </a-button>
 </template>
 <div class="prompts-page">
 <div class="tabs-container">
 <a-tabs v-model:active-key="activeTab">
 <a-tab-pane key="list" tab="提示词列表">
 <div class="table-container">
 <a-table
 :columns="columns"
 :data-source="prompts"
 :loading="loading"
 :pagination="pagination"
 row-key="id"
 @change="handleTableChange"
 >
 <template #bodyCell="{ column, record }">
 <template v-if="column.key === 'category'">
 <a-tag :color="getCategoryColor(record.category)">
 {{ record.category }}
 </a-tag>
 </template>
 <template v-else-if="column.key === 'actions'">
 <a-space>
 <a-button size="small" @click="editPrompt(record as Prompt)">编辑</a-button>
 <a-popconfirm title="确认删除该提示词？" @confirm="deletePrompt(record as Prompt)">
 <a-button size="small" danger>删除</a-button>
 </a-popconfirm>
 </a-space>
 </template>
 </template>
 </a-table>
 </div>
 </a-tab-pane>
 <a-tab-pane key="templates" tab="提示词模板">
 <div class="templates-grid">
 <div class="template-card" v-for="template in templates" :key="template.id">
 <div class="template-icon" :class="getTemplateIconClass(template.category)">
 <component :is="template.icon" />
 </div>
 <h3 class="template-name">{{ template.name }}</h3>
 <p class="template-desc">{{ template.description }}</p>
 <button class="use-template-btn" @click="useTemplate(template)">使用模板</button>
 </div>
 </div>
 </a-tab-pane>
 </a-tabs>
 </div>

 <a-modal v-model:open="showPromptModal" :title="editingId ? '编辑提示词' : '添加提示词'" :footer="null">
 <a-form :model="promptForm" :rules="promptRules" ref="promptFormRef">
 <a-form-item label="提示词名称" name="name">
 <a-input v-model:value="promptForm.name" placeholder="请输入提示词名称" />
 </a-form-item>
 <a-form-item label="分类" name="category">
 <a-select v-model:value="promptForm.category">
 <a-select-option value="代码生成">代码生成</a-select-option>
 <a-select-option value="文档撰写">文档撰写</a-select-option>
 <a-select-option value="数据分析">数据分析</a-select-option>
 <a-select-option value="创意写作">创意写作</a-select-option>
 </a-select>
 </a-form-item>
 <a-form-item label="提示词内容" name="content">
 <a-textarea v-model:value="promptForm.content" placeholder="请输入提示词内容" :rows="6" />
 </a-form-item>
 <div class="modal-footer">
 <a-button @click="closePromptModal">取消</a-button>
 <a-button type="primary" :loading="saving" @click="submitPromptForm">确定</a-button>
 </div>
 </a-form>
 </a-modal>
 </div>
 </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';
import { YdPage } from '@/components/youding';
import {
 PlusOutlined,
 CodeOutlined,
 FileTextOutlined,
 BarChartOutlined,
 EditOutlined,
} from '@ant-design/icons-vue';
import type { TableColumnsType } from 'ant-design-vue';

interface Prompt {
 id: string;
 name: string;
 category: string;
 content: string;
 usageCount: number;
 createTime: string;
 is_active: boolean;
 task_type: string;
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
const editingId = ref<string | null>(null);
const loading = ref(false);
const saving = ref(false);

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
 { title: '名称', dataIndex: 'name', key: 'name' },
 { title: '分类', dataIndex: 'category', key: 'category' },
 { title: '使用次数', dataIndex: 'usageCount', key: 'usageCount', width: 100 },
 { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 160 },
 { title: '操作', key: 'actions' },
];

const prompts = ref<Prompt[]>([]);

const templates = ref<Template[]>([
 { id: 1, name: '代码审查', category: '代码生成', description: '审查代码质量和潜在问题', icon: CodeOutlined },
 { id: 2, name: '单元测试', category: '代码生成', description: '为现有代码生成单元测试', icon: CodeOutlined },
 { id: 3, name: '技术方案', category: '文档撰写', description: '生成技术方案文档', icon: FileTextOutlined },
 { id: 4, name: '数据报告', category: '数据分析', description: '分析数据并生成报告', icon: BarChartOutlined },
 { id: 5, name: '营销文案', category: '创意写作', description: '生成营销推广文案', icon: EditOutlined },
]);

const pagination = reactive({
 current: 1,
 pageSize: 10,
 total: 0,
 showSizeChanger: true,
});

const categoryToTaskType: Record<string, string> = {
 代码生成: 'code_gen',
 文档撰写: 'doc_gen',
 数据分析: 'data_analysis',
 创意写作: 'creative_writing',
};

const taskTypeToCategory: Record<string, string> = {
 code_gen: '代码生成',
 doc_gen: '文档撰写',
 data_analysis: '数据分析',
 creative_writing: '创意写作',
 product_gen: '文档撰写',
};

function mapPrompt(raw: any): Prompt {
 const taskType = String(raw.task_type ?? '');
 return {
 id: String(raw.id),
 name: String(raw.name ?? ''),
 category: taskTypeToCategory[taskType] || taskType || '文档撰写',
 content: String(raw.system_prompt ?? raw.user_prompt_template ?? ''),
 usageCount: 0,
 createTime: String(raw.created_at ?? '').slice(0, 19).replace('T', ' ') || '-',
 is_active: raw.is_active !== false,
 task_type: taskType,
 };
}

async function loadPrompts() {
 loading.value = true;
 try {
 const res = await apiGet<any>('/ai/templates', {
 page: pagination.current,
 page_size: pagination.pageSize,
 });
 const items = res?.data?.items ?? res?.items ?? (Array.isArray(res) ? res : []);
 prompts.value = items.map(mapPrompt);
 pagination.total = Number(res?.data?.total ?? res?.total ?? prompts.value.length);
 } catch (e: any) {
 message.error(e?.message || '提示词列表加载失败');
 prompts.value = [];
 pagination.total = 0;
 } finally {
 loading.value = false;
 }
}

function handleTableChange(pag: any) {
 pagination.current = pag.current ?? 1;
 pagination.pageSize = pag.pageSize ?? 10;
 void loadPrompts();
}

function openCreate() {
 editingId.value = null;
 promptForm.name = '';
 promptForm.category = '代码生成';
 promptForm.content = '';
 showPromptModal.value = true;
}

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

const deletePrompt = async (record: Prompt) => {
 try {
 await apiDelete(`/ai/templates/${record.id}`);
 message.success('删除成功');
 await loadPrompts();
 } catch (e: any) {
 message.error(e?.message || '删除失败');
 }
};

const useTemplate = (template: Template) => {
 editingId.value = null;
 promptForm.name = `${template.name}（基于模板）`;
 promptForm.category = template.category;
 promptForm.content = '';
 activeTab.value = 'list';
 showPromptModal.value = true;
};

const submitPromptForm = async () => {
 if (!promptForm.name.trim() || !promptForm.content.trim()) {
 message.warning('请填写名称与内容');
 return;
 }
 saving.value = true;
 try {
 const payload = {
 name: promptForm.name.trim(),
 task_type: categoryToTaskType[promptForm.category] || 'doc_gen',
 system_prompt: promptForm.content,
 user_prompt_template: promptForm.content,
 variables_json: '[]',
 default_params_json: '{"temperature":0.7,"max_tokens":2000}',
 is_active: true,
 };
 if (editingId.value) {
 await apiPut(`/ai/templates/${editingId.value}`, payload);
 message.success('提示词已更新');
 } else {
 await apiPost('/ai/templates', payload);
 message.success('提示词已添加');
 }
 closePromptModal();
 await loadPrompts();
 } catch (e: any) {
 message.error(e?.message || '提示词保存失败');
 } finally {
 saving.value = false;
 }
};

onMounted(() => {
 void loadPrompts();
});
</script>

<style scoped lang="scss">
.prompts-page {
 padding: 24px;
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
 font-weight: 500;
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
