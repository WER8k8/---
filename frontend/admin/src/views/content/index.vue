/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="内容管理" subtitle="管理网站页面内容" surface="elevated">
  <template #actions>
  <router-link
  :to="`${contentBase}/content/edit/new`"
  class="px-5 py-2.5 gradient-primary text-white rounded-xl hover:shadow-lg hover:shadow-primary-500/30 text-sm font-medium transition-all duration-200 flex items-center shadow-md"
  >
  <PlusOutlined class="w-4 h-4 mr-2" />
  添加内容
</router-link>
</template>

  <div class="space-y-6 animate-fade-in">
  <div class="bg-white rounded-2xl shadow-card p-6">
  <div class="flex flex-wrap items-center gap-4">
  <div class="flex-1 min-w-[240px]">
  <a-input
  v-model:value="search"
  placeholder="搜索页面标题..."
  class="input-field"
  @keyup.enter="() => fetchContent()"
  >
  <template #prefix>
  <SearchOutlined class="text-gray-400" />
</template>
</a-input>
</div>
  <a-select
  v-model:value="filterType"
  placeholder="全部类型"
  class="min-w-[140px]"
  @change="() => fetchContent()"
  >
  <a-select-option value="">
  全部类型
</a-select-option>
  <a-select-option value="about">
  关于我们
</a-select-option>
  <a-select-option value="news">
  新闻资讯
</a-select-option>
  <a-select-option value="contact">
  联系我们
</a-select-option>
  <a-select-option value="custom">
  自定义页面
</a-select-option>
</a-select>
  <a-select
  v-model:value="filterStatus"
  placeholder="全部状态"
  class="min-w-[120px]"
  @change="() => fetchContent()"
  >
  <a-select-option value="">
  全部状态
</a-select-option>
  <a-select-option value="true">
  已发布
</a-select-option>
  <a-select-option value="false">
  草稿
</a-select-option>
</a-select>
  <a-button
  type="primary"
  class="gradient-primary shadow-md"
  @click="() => fetchContent()"
  >
  搜索
</a-button>
  <YdTableToolbar
  :loading="loading"
  :target-ref="tablePanelRef"
  :show-export="false"
  @refresh="() => fetchContent()"
  />
</div>
</div>

  <div ref="tablePanelRef" class="bg-white rounded-2xl shadow-card overflow-hidden content-table">
  <template v-if="initialLoading">
  <SkeletonCard variant="table" :rows="6" />
</template>
  <template v-else>
  <YdDataTable
  :columns="columns"
  :data-source="contentList"
  :pagination="tablePagination"
  :loading="loading"
  :table-props="{ rowKey: 'id', size: tableSize, customRow: contentRowProps }"
  @page-change="onPageChange"
  >
  <template #bodyCell="{ column, record }">
  <template v-if="column.key === 'title'">
  <div class="flex items-center space-x-3">
  <div
  class="w-10 h-10 bg-gradient-to-br from-primary-100 to-primary-200 rounded-xl flex items-center justify-center"
  >
  <FileTextOutlined class="w-5 h-5 text-primary-600" />
</div>
  <div>
  <p
  class="font-medium text-gray-900 cursor-pointer hover:text-primary-500 transition-colors"
  @click.stop="openDetail(record)"
  >
  {{ record.title }}
</p>
  <p class="text-xs text-gray-400">
  /{{ record.slug }}
</p>
</div>
</div>
</template>
  <template v-else-if="column.key === 'page_type'">
  <span
  class="px-3 py-1 rounded-full text-sm font-medium"
  :class="getTypeClass(record.page_type)"
  >
  {{ getTypeText(record.page_type) }}
</span>
</template>
  <template v-else-if="column.key === 'is_published'">
  <div class="flex items-center gap-1">
  <span
  class="px-3 py-1 rounded-full text-sm font-medium"
  :class="
    isPublished(record)
    ? 'bg-success-50 text-success-600'
    : 'bg-gray-100 text-gray-500'
  "
  >
  {{ isPublished(record) ? '已发布' : '草稿' }}
</span>
  <a-button
  v-if="isPublished(record)"
  type="link"
  size="small"
  class="!p-0 !h-auto text-xs"
  @click.stop="openDetail(record)"
  >
  查看
</a-button>
</div>
</template>
  <template v-else-if="column.key === 'updated_at'">
  <span class="text-gray-500">{{
    record.updated_at ? formatDate(record.updated_at) : '-'
  }}</span>
</template>
  <template v-else-if="column.key === 'actions'">
  <div class="flex items-center space-x-2" @click.stop>
  <a-button
  type="text"
  class="p-2 rounded-lg text-primary-500 hover:bg-primary-50 transition-colors"
  title="查看"
  @click="openDetail(record)"
  >
  <EyeOutlined class="w-4 h-4" />
</a-button>
  <router-link
  :to="`${contentBase}/content/edit/${record.id}`"
  class="p-2 rounded-lg text-primary-500 hover:bg-primary-50 transition-colors"
  >
  <EditOutlined class="w-4 h-4" />
</router-link>
  <a-button
  type="text"
  danger
  class="p-2 rounded-lg hover:bg-danger-50 transition-colors"
  @click="handleDelete(record)"
  >
  <DeleteOutlined class="w-4 h-4" />
</a-button>
</div>
</template>
</template>
</YdDataTable>
</template>
</div>
</div>
  </YdPage>

  <a-drawer
  v-model:open="detailOpen"
  title="内容详情"
  width="560"
  >
  <a-spin :spinning="detailLoading">
  <div v-if="detailData" class="space-y-4">
  <div class="flex items-start justify-between gap-3">
  <div>
  <h3 class="text-lg font-semibold text-gray-900 m-0">
  {{ detailData.title || '未命名页面' }}
</h3>
  <p class="text-sm text-gray-400 mt-1">/{{ detailData.slug || '-' }}</p>
</div>
  <span
  class="px-3 py-1 rounded-full text-sm font-medium shrink-0"
  :class="
    detailIsPublished
    ? 'bg-success-50 text-success-600'
    : 'bg-gray-100 text-gray-500'
  "
  >
  {{ detailIsPublished ? '已发布' : '草稿' }}
</span>
</div>

  <div class="grid grid-cols-2 gap-3 text-sm">
  <div>
  <div class="text-gray-400">类型</div>
  <div class="text-gray-800 mt-0.5">
  {{ getTypeText(detailData.page_type) }}
</div>
</div>
  <div>
  <div class="text-gray-400">更新时间</div>
  <div class="text-gray-800 mt-0.5">
  {{ detailData.updated_at ? formatDate(detailData.updated_at) : '-' }}
</div>
</div>
</div>

  <div>
  <div class="text-gray-400 text-sm mb-1">正文</div>
  <div
  v-if="detailHtml"
  class="prose prose-sm max-w-none text-gray-800 border border-gray-100 rounded-xl p-3 bg-gray-50/50"
  v-html="detailHtml"
  />
  <div v-else class="text-gray-400 text-sm py-3">暂无正文</div>
</div>

  <div v-if="officialUrl" class="pt-2">
  <a
  :href="officialUrl"
  target="_blank"
  rel="noopener noreferrer"
  class="text-primary-500 text-sm font-medium"
  >
  在官网查看 →
</a>
</div>
</div>
  <div v-else class="text-gray-400 text-sm py-8 text-center">暂无详情</div>
  </a-spin>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
const route = useRoute();
// 同一组件渲染于 /client（租户壳）与 /content（平台壳）两种 shell
const contentBase = computed(() => (route.path.startsWith('/client') ? '/client' : ''));
import { storeToRefs } from 'pinia';
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  FileTextOutlined,
  EyeOutlined,
} from '@ant-design/icons-vue';
import {
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Button as AButton,
  Modal,
  Drawer as ADrawer,
  Spin as ASpin,
} from 'ant-design-vue';
import { ydConfirm } from '@/utils/ydModal';
import { contentAPI, unwrapApiData } from '@/api';
import { useTenantBrand } from '@/composables/useTenantBrand';

const contentList = ref<any[]>([]);
const loading = ref(false);
const initialLoading = ref(true);
const tablePanelRef = ref<HTMLElement | null>(null);
const ui = useUiPreferencesStore();
const { antTableSize: tableSize } = storeToRefs(ui);
const search = ref('');
const filterType = ref('');
const filterStatus = ref('');

const tenantBrand = useTenantBrand();
const detailOpen = ref(false);
const detailLoading = ref(false);
const detailData = ref<Record<string, any> | null>(null);

function isPublished(record: Record<string, any> | null | undefined) {
  if (!record) return false;
  return record.status === 'published' || record.is_published === true;
}

const detailIsPublished = computed(() => isPublished(detailData.value));

const detailHtml = computed(() => {
  const raw = detailData.value?.content ?? detailData.value?.body ?? detailData.value?.html ?? '';
  return String(raw).trim();
});

const officialUrl = computed(() => {
  if (!detailIsPublished.value || !detailData.value?.slug) return '';
  const base = String(tenantBrand.siteUrl.value || '').replace(/\/$/, '');
  if (!base || base === '#') return '';
  return `${base}/content/${detailData.value.slug}`;
});

function contentRowProps(record: Record<string, unknown>) {
  return {
    onClick: () => openDetail(record),
    style: { cursor: 'pointer' },
  };
}

async function openDetail(record: Record<string, unknown>) {
  detailOpen.value = true;
  detailLoading.value = true;
  detailData.value = record as Record<string, any>;
  try {
    const res = await contentAPI.get(String(record.id));
    const data = unwrapApiData<Record<string, unknown>>(res) as Record<string, any> | null | undefined;
    if (data && typeof data === 'object') {
      detailData.value = { ...record, ...data };
    }
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to load content detail:', e);
  } finally {
    detailLoading.value = false;
  }
}

const tablePagination = computed(() => ({
  current: pagination.value.current,
  pageSize: pagination.value.pageSize,
  total: pagination.value.total,
}));

function onPageChange(p: { current: number; pageSize: number }) {
  pagination.value.pageSize = p.pageSize;
  void fetchContent(p.current);
}

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

const columns = [
  { title: '页面标题', key: 'title', width: 300 },
  { title: '类型', key: 'page_type', width: 120 },
  { title: '状态', key: 'is_published', width: 110 },
  { title: '更新时间', key: 'updated_at', width: 150 },
  { title: '操作', key: 'actions', width: 130 },
];

function getTypeClass(type: string) {
  if (type === 'about') return 'bg-blue-50 text-blue-600';
  if (type === 'news') return 'bg-purple-50 text-purple-600';
  if (type === 'contact') return 'bg-success-50 text-success-600';
  return 'bg-gray-100 text-gray-600';
}

function getTypeText(type: string) {
  if (type === 'about') return '关于我们';
  if (type === 'news') return '新闻资讯';
  if (type === 'contact') return '联系我们';
  if (type === 'custom') return '自定义页面';
  return type || '-';
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN');
}

async function fetchContent(page = 1) {
  loading.value = true;
  pagination.value.current = page;
  try {
    const params: Record<string, any> = {
      page,
      page_size: pagination.value.pageSize,
    };
    if (search.value) params.search = search.value;
    if (filterType.value) params.page_type = filterType.value;
    if (filterStatus.value) params.is_published = filterStatus.value;

    const res = await contentAPI.list(params);
    const data = unwrapApiData<Record<string, unknown>>(res) as
      | Record<string, unknown>
      | null
      | undefined;
    contentList.value = Array.isArray(data?.items)
      ? (data!.items as any[])
      : Array.isArray((data as any)?.records)
      ? (data as any).records
      : Array.isArray((data as any)?.list)
      ? (data as any).list
      : Array.isArray(data)
      ? (data as unknown as any[])
      : [];
    pagination.value.total =
      typeof data?.total === 'number' ? data.total : contentList.value.length;
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch content:', e);
  } finally {
    loading.value = false;
    initialLoading.value = false;
  }
}

function handleDelete(record: any) {
  ydConfirm({
    title: '确认删除',
    content: `确定要删除页面 "${record.title}" 吗？此操作不可撤销。`,
    okType: 'danger',
    onOk() {
      return (async () => {
        try {
          await contentAPI.delete(record.id);
          await fetchContent();
          Modal.success({ title: '删除成功' });
        } catch (e: any) {
          Modal.error({ title: '删除失败', content: e.message });
        }
      })();
    },
  });
}

onMounted(() => {
  fetchContent();
});
</script>

<style scoped>
.content-table :deep(.ant-table-thead > tr > th) {
  background: #f8fafc;
  font-weight: 500;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
}

.content-table :deep(.ant-table-tbody > tr:hover > td) {
  background: #f8fafc;
}

.content-table :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f1f5f9;
  padding: 16px;
}
</style>
