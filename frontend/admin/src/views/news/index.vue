/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    title="新闻管理"
    subtitle="对应 API：/api/v1/news — 列表、详情、创建、更新、删除"
    surface="elevated"
  >
    <template #actions>
      <a-select
        v-model:value="filterStatus"
        style="width: 140px"
        allow-clear
        placeholder="发布状态"
        @change="load"
      >
        <a-select-option value="published">
          已发布
        </a-select-option>
        <a-select-option value="draft">
          草稿
        </a-select-option>
      </a-select>
      <a-button
        type="primary"
        @click="openCreate"
      >
        新建新闻
      </a-button>
    </template>

    <div ref="tablePanelRef" class="table-card glass">
      <div class="table-toolbar-row">
        <YdTableToolbar
          :loading="loading"
          :target-ref="tablePanelRef"
          :show-export="false"
          @refresh="load"
        />
      </div>
      <YdDataTable
        :columns="columns"
        :data-source="rows"
        :loading="loading"
        :pagination="tablePagination"
        :table-props="{ rowKey: 'id', scroll: { x: 960 }, size: tableSize }"
        @page-change="onPageChange"
      >
        <template #bodyCell="{ column, record, text }">
          <template v-if="column.key === 'is_published'">
            {{ text ? '是' : '否' }}
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button
                type="link"
                size="small"
                @click="openEdit(record as Row)"
              >
                编辑
              </a-button>
              <a-popconfirm
                title="确定删除该新闻？"
                @confirm="removeRow(record as Row)"
              >
                <a-button
                  type="link"
                  danger
                  size="small"
                >
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </YdDataTable>
    </div>

    <a-modal
      v-model:open="modalOpen"
      :title="editingId ? '编辑新闻' : '新建新闻'"
      :confirm-loading="saving"
      width="720px"
      destroy-on-close
      @ok="submitForm"
    >
      <a-form
        :model="form"
        layout="vertical"
        class="mt-2"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item
              label="标题"
              required
            >
              <a-input
                v-model:value="form.title"
                placeholder="标题"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item
              label="URL 别名 (slug)"
              required
            >
              <a-input
                v-model:value="form.slug"
                placeholder="英文短横线，如 company-news-2026"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item
          label="分类"
          required
        >
          <a-select
            v-model:value="form.category"
            placeholder="选择分类"
          >
            <a-select-option value="company">
              公司动态
            </a-select-option>
            <a-select-option value="industry">
              行业资讯
            </a-select-option>
            <a-select-option value="product">
              产品相关
            </a-select-option>
            <a-select-option value="technology">
              技术文章
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="摘要">
          <a-textarea
            v-model:value="form.summary"
            :rows="2"
            placeholder="列表或卡片展示的摘要"
          />
        </a-form-item>
        <a-form-item
          label="正文"
          required
        >
          <a-textarea
            v-model:value="form.content"
            :rows="8"
            placeholder="正文（HTML/Markdown 依前台渲染为准）"
          />
        </a-form-item>
        <a-form-item label="立即发布">
          <a-switch v-model:checked="form.is_published" />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">

import { apiGet } from '@/utils/api'

onMounted(async () => {
  try { await apiGet('/news') } catch { /* 空状态 */ }
})
import { ref, reactive, computed, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import { message } from 'ant-design-vue';
import { newsAPI } from '@/api';

type Row = {
  id: string;
  title: string;
  slug: string;
  category: string;
  is_published: boolean;
  view_count: number;
  created_at: string | null;
};

const loading = ref(false);
const saving = ref(false);
const rows = ref<Row[]>([]);
const filterStatus = ref<string | undefined>(undefined);
const pagination = ref({ current: 1, pageSize: 20, total: 0 });
const tablePanelRef = ref<HTMLElement | null>(null);
const ui = useUiPreferencesStore();
const { antTableSize: tableSize } = storeToRefs(ui);

const tablePagination = computed(() => ({
  current: pagination.value.current,
  pageSize: pagination.value.pageSize,
  total: pagination.value.total,
}));

const modalOpen = ref(false);
const editingId = ref<string | null>(null);

const form = reactive({
  title: '',
  slug: '',
  category: 'company',
  summary: '',
  content: '',
  is_published: false,
});

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '分类', dataIndex: 'category', key: 'category', width: 100 },
  { title: '发布', dataIndex: 'is_published', key: 'is_published', width: 90 },
  { title: '浏览', dataIndex: 'view_count', key: 'view_count', width: 80 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'actions', width: 160, fixed: 'right' as const },
];

function slugify(s: string) {
  return (
    s
      .trim()
      .toLowerCase()
      .replace(/\s+/g, '-')
      .replace(/[^a-z0-9\u4e00-\u9fff-]/gi, '')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 80) || 'news-' + Date.now()
  );
}

function resetForm() {
  form.title = '';
  form.slug = '';
  form.category = 'company';
  form.summary = '';
  form.content = '';
  form.is_published = false;
}

function openCreate() {
  editingId.value = null;
  resetForm();
  modalOpen.value = true;
}

async function openEdit(record: Row) {
  editingId.value = record.id;
  try {
    const res = await newsAPI.get(record.id);
    const d = res.data as Record<string, unknown>;
    form.title = String(d.title ?? '');
    form.slug = String(d.slug ?? '');
    form.category = String(d.category ?? 'company');
    form.summary = String(d.summary ?? '');
    form.content = String(d.content ?? '');
    form.is_published = Boolean(d.is_published);
    modalOpen.value = true;
  } catch {
    message.error('加载新闻详情失败');
  }
}

async function submitForm() {
  if (!form.title.trim()) {
    message.warning('请填写标题');
    return;
  }
  if (!form.content.trim()) {
    message.warning('请填写正文');
    return;
  }
  const slug = form.slug.trim() || slugify(form.title);
  saving.value = true;
  try {
    if (editingId.value) {
      await newsAPI.update(editingId.value, {
        title: form.title.trim(),
        slug,
        category: form.category,
        summary: form.summary.trim() || null,
        content: form.content,
        is_published: form.is_published,
      });
      message.success('已保存');
    } else {
      const id =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `news-${Date.now()}`;
      await newsAPI.create({
        id,
        title: form.title.trim(),
        slug,
        category: form.category,
        summary: form.summary.trim() || null,
        content: form.content,
        is_published: form.is_published,
        is_active: true,
        view_count: 0,
        sort_order: 0,
      });
      message.success('已创建');
    }
    modalOpen.value = false;
    await load();
  } catch (e: unknown) {
    message.error('保存失败，请检查权限与字段');
  } finally {
    saving.value = false;
  }
}

async function removeRow(record: Row) {
  try {
    await newsAPI.remove(record.id);
    message.success('已删除');
    await load();
  } catch {
    message.error('删除失败');
  }
}

async function load() {
  loading.value = true;
  try {
    const res = await newsAPI.list({
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      status: filterStatus.value,
    });
    const body = res.data as { items?: Row[]; total?: number };
    rows.value = body.items ?? [];
    pagination.value.total = body.total ?? 0;
  } catch (e) {
    if (import.meta.env.DEV) console.error(e);
    message.error('加载新闻列表失败');
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

function onPageChange(p: { current: number; pageSize: number }) {
  pagination.value.current = p.current;
  pagination.value.pageSize = p.pageSize;
  void load();
}

onMounted(load);
</script>

<style scoped lang="scss">
.glass {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.65);
  border-radius: 22px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.08);
  backdrop-filter: blur(16px);
}
.table-card {
  padding: 1rem 1.25rem 1.25rem;
}
.table-toolbar-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.75rem;
}
.mt-2 {
  margin-top: 0.5rem;
}
</style>
