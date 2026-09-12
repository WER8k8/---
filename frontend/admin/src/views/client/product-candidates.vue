<template>
  <YdPage title="产业带产品候选" subtitle="大城+河间 AI 调研 · 勾选导入产品库" surface="elevated">
    <a-alert type="warning" show-icon class="mb-4" :message="honestNote" />

    <a-space class="mb-4" wrap>
      <a-select
        v-model:value="categoryId"
        allow-clear
        placeholder="按品类筛选"
        style="width: 200px"
        @change="reload"
      >
        <a-select-option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</a-select-option>
      </a-select>
      <a-input-search
        v-model:value="search"
        placeholder="搜品名"
        style="width: 220px"
        @search="reload"
      />
      <a-button type="primary" :loading="importing" :disabled="!selected.length" @click="doImport">
        导入选中（{{ selected.length }}）
      </a-button>
      <a-button @click="router.push('/client/products')">去产品库核对 →</a-button>
    </a-space>

    <a-table
      :columns="columns"
      :data-source="items"
      :loading="loading"
      row-key="candidate_id"
      :pagination="{ current: page, pageSize: 30, total, onChange: onPage }"
      :row-selection="{ selectedRowKeys: selected, onChange: onSelect }"
      size="small"
    />
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';

import { YdPage } from '@/components/youding';
import {
  fetchProductCandidates,
  importProductCandidates,
  type ProductCandidate,
} from '@/api/cross-border';

const router = useRouter();
const loading = ref(false);
const importing = ref(false);
const items = ref<ProductCandidate[]>([]);
const categories = ref<Array<{ id: string; name: string }>>([]);
const total = ref(0);
const page = ref(1);
const categoryId = ref<string | undefined>();
const search = ref('');
const selected = ref<string[]>([]);
const honestNote = ref('AI 调研候选，导入后默认未上架，请核对后再启用。');

const columns = [
  { title: '品名', dataIndex: 'name', key: 'name' },
  { title: '品类', dataIndex: 'category_name_zh', key: 'cat' },
  { title: '集群', dataIndex: 'town_cluster', key: 'town' },
  { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
];

async function reload() {
  loading.value = true;
  try {
    const res = await fetchProductCandidates({
      category_id: categoryId.value,
      search: search.value || undefined,
      page: page.value,
    });
    items.value = res.items || [];
    categories.value = res.categories || [];
    total.value = res.total || 0;
    if (res.honest_note) honestNote.value = res.honest_note;
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载失败');
  } finally {
    loading.value = false;
  }
}

function onPage(p: number) {
  page.value = p;
  reload();
}

function onSelect(keys: (string | number)[]) {
  selected.value = keys as string[];
}

async function doImport() {
  importing.value = true;
  try {
    const res = await importProductCandidates(selected.value);
    message.success(`已导入 ${res.imported_count} 条，跳过 ${res.skipped_count} 条`);
    selected.value = [];
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '导入失败');
  } finally {
    importing.value = false;
  }
}

onMounted(reload);
</script>
