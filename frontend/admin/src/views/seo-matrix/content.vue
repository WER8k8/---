/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="AI 文案生成" subtitle="基于关键词智能生成高质量 SEO 文案" surface="elevated">
    <template #actions>
      <a-button @click="refreshData">
        <ReloadOutlined class="w-4 h-4 mr-2" />
        刷新
      </a-button>
      <a-button type="primary" class="gradient-primary" @click="showGenerateModal = true">
        <BulbOutlined class="w-4 h-4 mr-2" />
        生成文案
      </a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-5">
      <div class="stat-card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-primary-100 text-sm font-medium">
              文案模板
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ templates.length }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <FileTextOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-success-500 to-success-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-success-100 text-sm font-medium">
              已生成文案
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ contents.length }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <EditOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-blue-100 text-sm font-medium">
              已发布
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ publishedCount }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <SendOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>

      <div class="stat-card bg-gradient-to-br from-purple-500 to-purple-600 text-white">
        <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -mr-8 -mt-8" />
        <div class="relative z-10 flex items-center justify-between">
          <div>
            <p class="text-purple-100 text-sm font-medium">
              待发布
            </p>
            <p class="text-3xl font-bold mt-2">
              {{ pendingCount }}
            </p>
          </div>
          <div class="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center">
            <ClockCircleOutlined class="w-7 h-7" />
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-1">
        <div class="bg-white rounded-2xl shadow-card p-4">
          <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <LayoutOutlined class="w-5 h-5 mr-2 text-primary-500" />
            文案模板
          </h3>
          <div class="space-y-2">
            <div
              v-for="template in templates"
              :key="template.id"
              :class="[
                'p-3 rounded-xl cursor-pointer transition-all',
                selectedTemplate?.id === template.id
                  ? 'bg-primary-50 border border-primary-200'
                  : 'hover:bg-gray-50',
              ]"
              @click="selectTemplate(template)"
            >
              <div class="font-medium text-gray-900">
                {{ template.name }}
              </div>
              <p class="text-xs text-gray-400 mt-1">
                {{ template.category }}
              </p>
            </div>
          </div>
          <a-button
            block
            size="small"
            type="dashed"
            class="mt-4"
            @click="showTemplateModal = true"
          >
            <PlusOutlined class="w-4 h-4 mr-2" />
            添加模板
          </a-button>
        </div>
      </div>

      <div class="lg:col-span-2">
        <div class="bg-white rounded-2xl shadow-card p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">
                生成的文案
              </h3>
              <p
                v-if="selectedTemplate"
                class="text-sm text-gray-500 mt-1"
              >
                当前模板: {{ selectedTemplate.name }}
              </p>
            </div>
            <a-select
              v-model:value="statusFilter"
              placeholder="状态筛选"
              class="w-36"
            >
              <a-select-option value="">
                全部
              </a-select-option>
              <a-select-option value="draft">
                草稿
              </a-select-option>
              <a-select-option value="published">
                已发布
              </a-select-option>
              <a-select-option value="pending">
                待发布
              </a-select-option>
            </a-select>
          </div>

          <SkeletonCard v-if="loading && !contents.length" variant="table" :rows="6" />
          <a-table
            v-else
            :columns="columns"
            :data-source="contents"
            :pagination="pagination"
            :loading="loading"
            row-key="id"
            @change="handleTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'title'">
                <a-button
                  type="link"
                  @click="previewContent(record)"
                  class="text-left p-0 h-auto"
                >
                  <span class="font-medium text-gray-900">{{ record.title }}</span>
                </a-button>
              </template>
              <template v-if="column.key === 'keyword'">
                <span class="text-gray-500 text-sm">{{ record.keyword }}</span>
              </template>
              <template v-if="column.key === 'word_count'">
                <span class="text-gray-600">{{ record.word_count }}字</span>
              </template>
              <template v-if="column.key === 'status'">
                <span
                  :class="getStatusClass(record.status)"
                  class="px-3 py-1 rounded-full text-sm font-medium"
                >
                  {{ getStatusText(record.status) }}
                </span>
              </template>
              <template v-if="column.key === 'created_at'">
                <span class="text-gray-500 text-sm">{{ formatTime(record.created_at) }}</span>
              </template>
              <template v-if="column.key === 'actions'">
                <a-space :size="8">
                  <a-button
                    size="small"
                    @click="previewContent(record)"
                  >
                    预览
                  </a-button>
                  <a-button
                    size="small"
                    @click="editContent(record)"
                  >
                    编辑
                  </a-button>
                  <a-button
                    size="small"
                    type="primary"
                    @click="publishContent(record)"
                  >
                    发布
                  </a-button>
                  <a-button
                    size="small"
                    danger
                    @click="deleteContent(record)"
                  >
                    删除
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="showGenerateModal"
      title="AI生成文案"
      :footer="false"
      width="800px"
    >
      <a-form
        :model="generateForm"
        layout="vertical"
      >
        <div class="grid grid-cols-2 gap-6">
          <div>
            <a-form-item label="选择模板">
              <a-select
                v-model:value="generateForm.template_id"
                placeholder="选择文案模板"
                class="w-full"
              >
                <a-select-option
                  v-for="tpl in templates"
                  :key="tpl.id"
                  :value="tpl.id"
                >
                  {{ tpl.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="关键词来源">
              <a-select
                v-model:value="generateForm.keyword_source"
                placeholder="选择关键词来源"
                class="w-full"
              >
                <a-select-option value="auto">
                  自动选择未使用关键词
                </a-select-option>
                <a-select-option value="manual">
                  手动输入关键词
                </a-select-option>
              </a-select>
            </a-form-item>
          </div>
          <div>
            <a-form-item label="生成数量">
              <a-input-number
                v-model:value="generateForm.count"
                :min="1"
                :max="50"
                class="w-40"
              />
            </a-form-item>
            <a-form-item label="内容长度">
              <a-input-number
                v-model:value="generateForm.content_length"
                :min="200"
                :max="3000"
                class="w-40"
              />
            </a-form-item>
          </div>
        </div>
        <a-form-item
          v-if="generateForm.keyword_source === 'manual'"
          label="关键词列表"
        >
          <a-textarea
            v-model:value="generateForm.keywords"
            placeholder="每行一个关键词"
            :rows="4"
          />
        </a-form-item>
      </a-form>
      <div class="flex justify-end space-x-3 mt-6">
        <a-button @click="showGenerateModal = false">
          取消
        </a-button>
        <a-button
          type="primary"
          class="gradient-primary"
          @click="generateContent"
        >
          <BulbOutlined class="w-4 h-4 mr-2" />
          开始生成
        </a-button>
      </div>
    </a-modal>

    <a-modal
      v-model:open="showPreviewModal"
      :title="previewContentData?.title"
      width="800px"
      :footer="false"
    >
      <div class="prose max-w-none">
        <p class="text-sm text-gray-500 mb-4">
          关键词: {{ previewContentData?.keyword }}
        </p>
        <div
          v-html="sanitizeHtml(previewContentData?.content)"
          class="whitespace-pre-wrap"
        />
      </div>
    </a-modal>

    <a-modal
      v-model:open="showTemplateModal"
      :title="editingTemplate ? '编辑模板' : '添加文案模板'"
      @ok="saveTemplate"
    >
      <a-form
        :model="templateForm"
        layout="vertical"
      >
        <a-form-item label="模板名称">
          <a-input
            v-model:value="templateForm.name"
            placeholder="输入模板名称"
          />
        </a-form-item>
        <a-form-item label="模板分类">
          <a-select
            v-model:value="templateForm.category"
            placeholder="选择分类"
          >
            <a-select-option value="article">
              文章
            </a-select-option>
            <a-select-option value="product">
              产品介绍
            </a-select-option>
            <a-select-option value="guide">
              指南教程
            </a-select-option>
            <a-select-option value="review">
              评测对比
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="模板内容">
          <a-textarea
            v-model:value="templateForm.content"
            placeholder="使用 {keyword} {region} 作为占位符"
            :rows="8"
          />
        </a-form-item>
        <a-form-item label="备注">
          <a-input
            v-model:value="templateForm.remark"
            placeholder="备注信息"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="showEditContentModal"
      title="编辑文案"
      ok-text="保存"
      cancel-text="取消"
      @ok="saveContentEdit"
    >
      <a-form layout="vertical">
        <a-form-item label="标题">
          <a-input v-model:value="editContentForm.title" placeholder="文案标题" />
        </a-form-item>
        <a-form-item label="正文">
          <a-textarea v-model:value="editContentForm.content" :rows="12" placeholder="文案内容" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onActivated } from 'vue';
import {
  ReloadOutlined,
  BulbOutlined,
  FileTextOutlined,
  EditOutlined,
  SendOutlined,
  ClockCircleOutlined,
  LayoutOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue';
import { message, Modal } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { seoMatrixAPI, unwrapApiData } from '@/api';
import { useSanitize } from '@/composables/useSanitize';

const { sanitizeHtml } = useSanitize();

const templates = ref<any[]>([]);
const contents = ref<any[]>([]);
const selectedTemplate = ref<any>(null);
const statusFilter = ref('');

const loading = ref(false);
const showGenerateModal = ref(false);
const showPreviewModal = ref(false);
const showTemplateModal = ref(false);
const showEditContentModal = ref(false);
const editingContent = ref<any>(null);
const editingTemplate = ref<any>(null);
const previewContentData = ref<any>(null);

const editContentForm = reactive({
  title: '',
  content: '',
});

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

const generateForm = reactive({
  template_id: '',
  keyword_source: 'auto',
  count: 10,
  content_length: 800,
  keywords: '',
});

const templateForm = reactive({
  name: '',
  category: 'article',
  content: '',
  remark: '',
});

const columns = [
  { title: '标题', key: 'title', width: 300 },
  { title: '关键词', key: 'keyword', width: 150 },
  { title: '字数', key: 'word_count', width: 80 },
  { title: '状态', key: 'status', width: 100 },
  { title: '生成时间', key: 'created_at', width: 150 },
  { title: '操作', key: 'actions', width: 250 },
];

const publishedCount = computed(
  () => contents.value.filter((c) => c.status === 'published').length
);
const pendingCount = computed(() => contents.value.filter((c) => c.status === 'pending').length);

function getStatusClass(status: string) {
  if (status === 'published') return 'bg-success-50 text-success-600';
  if (status === 'pending') return 'bg-warning-50 text-warning-600';
  if (status === 'draft') return 'bg-gray-100 text-gray-500';
  return 'bg-gray-100 text-gray-500';
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    published: '已发布',
    pending: '待发布',
    draft: '草稿',
  };
  return map[status] || status;
}

function formatTime(timeStr: string) {
  if (!timeStr) return '-';
  const date = new Date(timeStr);
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

async function fetchTemplates() {
  try {
    const res = await seoMatrixAPI.getContentTemplates();
    const raw = unwrapApiData<any>(res);
    templates.value = Array.isArray(raw) ? raw : raw?.items || [];
    if (templates.value.length > 0) {
      selectTemplate(templates.value[0]);
    }
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch templates:', e);
  }
}

async function fetchContents(templateId?: string) {
  loading.value = true;
  try {
    const params = {
      template_id: templateId || undefined,
      status: statusFilter.value || undefined,
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    };
    const res = await seoMatrixAPI.getGeneratedContents(params);
    const page = unwrapApiData<{ items?: any[]; total?: number }>(res);
    contents.value = page?.items || [];
    pagination.value.total = page?.total || 0;
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch contents:', e);
  } finally {
    loading.value = false;
  }
}

function selectTemplate(template: any) {
  selectedTemplate.value = template;
  pagination.value.current = 1;
  fetchContents(template.id);
}

function handleTableChange(paginationInfo: any) {
  pagination.value.current = paginationInfo.current;
  pagination.value.pageSize = paginationInfo.pageSize;
  fetchContents(selectedTemplate.value?.id);
}

async function generateContent() {
  try {
    const keywords =
      generateForm.keyword_source === 'manual'
        ? generateForm.keywords.split('\n').filter((k) => k.trim())
        : [];

    await seoMatrixAPI.generateContent({
      template_id: generateForm.template_id,
      keyword_source: generateForm.keyword_source,
      keywords: keywords.length > 0 ? keywords : undefined,
      count: generateForm.count,
      content_length: generateForm.content_length,
    });
    showGenerateModal.value = false;
    fetchContents(selectedTemplate.value?.id);
    message.success('文案生成成功');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to generate content:', e);
    message.error('生成失败');
  }
}

function previewContent(record: any) {
  previewContentData.value = record;
  showPreviewModal.value = true;
}

function editContent(record: any) {
  editingContent.value = record;
  editContentForm.title = record?.title ?? '';
  editContentForm.content = record?.content ?? '';
  showEditContentModal.value = true;
}

function saveContentEdit() {
  if (!editingContent.value) return;
  editingContent.value.title = editContentForm.title.trim();
  editingContent.value.content = editContentForm.content;
  showEditContentModal.value = false;
  message.success('文案已更新');
}

async function publishContent(record: any) {
  try {
    await seoMatrixAPI.publishContent(record.id);
    fetchContents(selectedTemplate.value?.id);
    message.success('发布成功');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to publish:', e);
    message.error('发布失败');
  }
}

async function deleteContent(record: any) {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这篇文案吗？此操作不可撤销。',
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        await seoMatrixAPI.deleteContent(record.id);
        fetchContents(selectedTemplate.value?.id);
        message.success('删除成功');
      } catch (e) {
        if (import.meta.env.DEV) console.error('Failed to delete:', e);
        message.error('删除失败');
      }
    },
  });
}

async function saveTemplate() {
  try {
    if (editingTemplate.value) {
      await seoMatrixAPI.updateTemplate(editingTemplate.value.id, templateForm);
    } else {
      await seoMatrixAPI.createTemplate(templateForm);
    }
    showTemplateModal.value = false;
    resetTemplateForm();
    fetchTemplates();
    message.success('保存成功');
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to save template:', e);
    message.error('保存失败');
  }
}

function resetTemplateForm() {
  editingTemplate.value = null;
  templateForm.name = '';
  templateForm.category = 'article';
  templateForm.content = '';
  templateForm.remark = '';
}

function refreshData() {
  fetchTemplates();
}

onActivated(() => {
  refreshData();
});
</script>
