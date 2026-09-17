/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="案例管理" subtitle="管理成功案例和项目展示" surface="elevated">
    <template #actions>
      <router-link
        to="/cases/edit/new"
        class="px-5 py-2.5 gradient-primary text-white rounded-xl hover:shadow-lg hover:shadow-primary-500/30 text-sm font-medium transition-all duration-200 flex items-center shadow-md"
      >
        <PlusOutlined class="w-4 h-4 mr-2" />
        添加案例
      </router-link>
    </template>

  <div class="space-y-6 animate-fade-in">
    <div class="bg-white rounded-2xl shadow-card p-6">
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex-1 min-w-[240px]">
          <a-input
            v-model="search"
            placeholder="搜索案例标题..."
            class="input-field"
            @keyup.enter="() => fetchCases()"
          >
            <template #prefix>
              <SearchOutlined class="text-gray-400" />
            </template>
          </a-input>
        </div>
        <a-select
          v-model="filterStatus"
          placeholder="全部状态"
          class="min-w-[120px]"
          @change="() => fetchCases()"
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
          @click="() => fetchCases()"
        >
          搜索
        </a-button>
        <YdTableToolbar
          :loading="loading"
          :target-ref="tablePanelRef"
          :show-export="false"
          @refresh="() => fetchCases()"
        />
      </div>
    </div>

    <div ref="tablePanelRef" class="bg-white rounded-2xl shadow-card overflow-hidden cases-table">
      <YdDataTable
        :columns="columns"
        :data-source="cases"
        :pagination="tablePagination"
        :loading="loading"
        :table-props="{ rowKey: 'id', size: tableSize }"
        @page-change="onPageChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <div class="flex items-center space-x-3">
              <div
                class="w-10 h-10 bg-gradient-to-br from-secondary-100 to-secondary-200 rounded-xl flex items-center justify-center"
              >
                <PictureOutlined class="w-5 h-5 text-secondary-600" />
              </div>
              <div>
                <p class="font-semibold text-gray-900">
                  {{ record.title }}
                </p>
                <p class="text-xs text-gray-400">
                  {{ record.location || '-' }}
                </p>
              </div>
            </div>
          </template>
          <template v-else-if="column.key === 'project_type'">
            <span
              class="px-3 py-1 rounded-full text-sm font-medium"
              :class="getProjectTypeClass(record.project_type)"
            >
              {{ getProjectTypeText(record.project_type) }}
            </span>
          </template>
          <template v-else-if="column.key === 'is_published'">
            <span
              class="px-3 py-1 rounded-full text-sm font-medium"
              :class="
                record.is_published ? 'bg-success-50 text-success-600' : 'bg-gray-100 text-gray-500'
              "
            >
              {{ record.is_published ? '已发布' : '草稿' }}
            </span>
          </template>
          <template v-else-if="column.key === 'updated_at'">
            <span class="text-gray-500">{{
              record.updated_at ? formatDate(record.updated_at) : '-'
            }}</span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <div class="flex items-center space-x-2">
              <router-link
                :to="`/cases/edit/${record.id}`"
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
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">

import { apiGet } from '@/utils/api'

onMounted(async () => {
  try { await apiGet('/content') } catch { /* 空状态 */ }
})
import { ref, computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  DeleteOutlined,
  PictureOutlined,
} from '@ant-design/icons-vue';
import {
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Button as AButton,
  Modal,
} from 'ant-design-vue';
import { ydConfirm } from '@/utils/ydModal';
import { casesAPI } from '@/api';

const cases = ref<any[]>([]);
const loading = ref(false);
const tablePanelRef = ref<HTMLElement | null>(null);
const ui = useUiPreferencesStore();
const { antTableSize: tableSize } = storeToRefs(ui);
const search = ref('');
const filterStatus = ref('');

const tablePagination = computed(() => ({
  current: pagination.value.current,
  pageSize: pagination.value.pageSize,
  total: pagination.value.total,
}));

function onPageChange(p: { current: number; pageSize: number }) {
  pagination.value.pageSize = p.pageSize;
  void fetchCases(p.current);
}

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

const columns = [
  { title: '案例标题', key: 'title', width: 300 },
  { title: '项目类型', key: 'project_type', width: 120 },
  { title: '状态', key: 'is_published', width: 100 },
  { title: '更新时间', key: 'updated_at', width: 150 },
  { title: '操作', key: 'actions', width: 100 },
];

function getProjectTypeClass(type: string) {
  if (type === 'residential') return 'bg-blue-50 text-blue-600';
  if (type === 'commercial') return 'bg-purple-50 text-purple-600';
  if (type === 'industrial') return 'bg-accent-50 text-accent-600';
  return 'bg-gray-100 text-gray-600';
}

function getProjectTypeText(type: string) {
  if (type === 'residential') return '住宅项目';
  if (type === 'commercial') return '商业项目';
  if (type === 'industrial') return '工业项目';
  return type;
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN');
}

async function fetchCases(page = 1) {
  loading.value = true;
  pagination.value.current = page;
  try {
    const params: Record<string, any> = {
      page,
      page_size: pagination.value.pageSize,
    };
    if (search.value) params.search = search.value;
    if (filterStatus.value) params.is_published = filterStatus.value;

    const res = await casesAPI.list(params);
    cases.value = res.data.items || [];
    pagination.value.total = res.data.total || 0;
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch cases:', e);
  } finally {
    loading.value = false;
  }
}

function handleDelete(record: any) {
  ydConfirm({
    title: '确认删除',
    content: `确定要删除案例 "${record.title}" 吗？此操作不可撤销。`,
    okType: 'danger',
    onOk() {
      return (async () => {
        try {
          await casesAPI.delete(record.id);
          await fetchCases();
          Modal.success({ title: '删除成功' });
        } catch (e: any) {
          Modal.error({ title: '删除失败', content: e.message });
        }
      })();
    },
  });
}

onMounted(() => {
  fetchCases();
});
</script>

<style scoped>
.cases-table :deep(.ant-table-thead > tr > th) {
  background: #f8fafc;
  font-weight: 600;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
}

.cases-table :deep(.ant-table-tbody > tr:hover > td) {
  background: #f8fafc;
}

.cases-table :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f1f5f9;
  padding: 16px;
}
</style>
