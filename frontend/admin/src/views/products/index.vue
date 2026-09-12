<template>
  <YdPage title="产品管理" subtitle="管理产品信息和分类" surface="elevated">
    <template #actions>
      <input
        ref="importInputRef"
        type="file"
        accept=".csv"
        class="hidden"
        @change="onImportFile"
      >
      <a-button @click="triggerImport">
        <UploadOutlined class="w-4 h-4 mr-2" />
        导入 CSV
      </a-button>
      <a-button :loading="exporting" @click="handleExportCsv">
        <DownloadOutlined class="w-4 h-4 mr-2" />
        导出 CSV
      </a-button>
      <router-link
        :to="`${productBase}/products/categories`"
        class="px-5 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 text-sm font-medium transition-all duration-200 shadow-sm flex items-center"
      >
        <FolderOpenOutlined class="w-4 h-4 mr-2" />
        分类管理
      </router-link>
      <router-link
        :to="`${productBase}/products/edit/new`"
        class="px-5 py-2.5 gradient-primary text-white rounded-xl hover:shadow-lg hover:shadow-primary-500/30 text-sm font-medium transition-all duration-200 flex items-center shadow-md"
      >
        <PlusOutlined class="w-4 h-4 mr-2" />
        新增产品
      </router-link>
    </template>
  <div class="space-y-6 animate-fade-in">

    <a-alert
      v-if="listError"
      type="warning"
      show-icon
      class="rounded-xl"
      :message="listError"
    />

    <div class="bg-white rounded-2xl shadow-card p-6">
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex-1 min-w-[240px]">
          <a-input
            v-model:value="search"
            placeholder="搜索产品名称..."
            class="input-field"
            @keyup.enter="() => fetchProducts()"
          >
            <template #prefix>
              <SearchOutlined class="text-gray-400" />
            </template>
          </a-input>
        </div>
        <a-select
          v-model:value="filterCategory"
          placeholder="全部分类"
          class="min-w-[160px]"
          @change="() => fetchProducts()"
        >
          <a-select-option value="">
            全部分类
          </a-select-option>
          <a-select-option
            v-for="cat in categories"
            :key="cat.id"
            :value="cat.id"
          >
            {{ cat.name }}
          </a-select-option>
        </a-select>
        <a-select
          v-model:value="filterStatus"
          placeholder="全部状态"
          class="min-w-[120px]"
          @change="() => fetchProducts()"
        >
          <a-select-option value="">
            全部状态
          </a-select-option>
          <a-select-option value="true">
            上架
          </a-select-option>
          <a-select-option value="false">
            下架
          </a-select-option>
        </a-select>
        <a-button
          type="primary"
          class="gradient-primary shadow-md"
          @click="() => fetchProducts()"
        >
          搜索
        </a-button>
        <YdTableToolbar
          :loading="loading"
          :target-ref="tablePanelRef"
          :show-export="true"
          @refresh="() => fetchProducts()"
          @export="handleExportCsv"
        />
      </div>
    </div>

    <div ref="tablePanelRef" class="bg-white rounded-2xl shadow-card overflow-hidden product-table">
      <template v-if="initialLoading">
        <SkeletonCard variant="table" :rows="6" />
      </template>
      <template v-else>
      <YdDataTable
        :columns="columns"
        :data-source="products"
        :pagination="tablePagination"
        :loading="loading"
        :table-props="{ rowKey: 'id', size: tableSize }"
        @page-change="onPageChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="flex items-center space-x-3">
              <div
                class="w-12 h-12 bg-gradient-to-br from-gray-100 to-gray-200 rounded-xl flex items-center justify-center"
              >
                <PauseOutlined class="w-6 h-6 text-gray-500" />
              </div>
              <div>
                <p class="font-semibold text-gray-900">
                  {{ record.name }}
                </p>
                <p class="text-xs text-gray-400">
                  /{{ record.slug }}
                </p>
              </div>
            </div>
          </template>
          <template v-else-if="column.key === 'category'">
            <span class="px-3 py-1 bg-primary-50 text-primary-600 rounded-full text-sm">
              {{ record.category_name || '-' }}
            </span>
          </template>
          <template v-else-if="column.key === 'fire_rating'">
            <span
              class="px-3 py-1 rounded-full text-sm font-medium"
              :class="getFireRatingClass(record.fire_rating)"
            >
              {{ record.fire_rating || '-' }}
            </span>
          </template>
          <template v-else-if="column.key === 'is_active'">
            <span
              class="px-3 py-1 rounded-full text-sm font-medium"
              :class="
                record.is_active ? 'bg-success-50 text-success-600' : 'bg-gray-100 text-gray-500'
              "
            >
              {{ record.is_active ? '上架' : '下架' }}
            </span>
          </template>
          <template v-else-if="column.key === 'view_count'">
            <span class="text-gray-600 font-medium">{{ record.view_count || 0 }}</span>
          </template>
          <template v-else-if="column.key === 'updated_at'">
            <span class="text-gray-500">{{
              record.updated_at ? formatDate(record.updated_at) : '-'
            }}</span>
          </template>
          <template v-else-if="column.key === 'actions'">
            <div class="flex items-center space-x-2">
              <router-link
                :to="`${productBase}/products/edit/${record.id}`"
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
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
const route = useRoute();
// 同一组件渲染于 /client（租户壳）与 /products（平台壳）两种 shell：链接前缀随当前路由
const productBase = computed(() => (route.path.startsWith('/client') ? '/client' : ''));
import { storeToRefs } from 'pinia';
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import {
  SearchOutlined,
  FolderOpenOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PauseOutlined,
  UploadOutlined,
  DownloadOutlined,
} from '@ant-design/icons-vue';
import {
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Button as AButton,
  Modal,
  message,
} from 'ant-design-vue';
import { ydConfirm } from '@/utils/ydModal';
import { productsAPI, unwrapApiData } from '@/api';

const products = ref<any[]>([]);
const categories = ref<any[]>([]);
const loading = ref(false);
const initialLoading = ref(true);
const exporting = ref(false);
const listError = ref('');
const importInputRef = ref<HTMLInputElement | null>(null);
const tablePanelRef = ref<HTMLElement | null>(null);
const ui = useUiPreferencesStore();
const { antTableSize: tableSize } = storeToRefs(ui);
const search = ref('');
const filterCategory = ref('');
const filterStatus = ref('');

const tablePagination = computed(() => ({
  current: pagination.value.current,
  pageSize: pagination.value.pageSize,
  total: pagination.value.total,
}));

function onPageChange(p: { current: number; pageSize: number }) {
  pagination.value.pageSize = p.pageSize;
  void fetchProducts(p.current);
}

const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
});

const columns = [
  { title: '产品名称', key: 'name', width: 280 },
  { title: '分类', key: 'category', width: 120 },
  { title: '防火等级', key: 'fire_rating', width: 100 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '浏览量', key: 'view_count', width: 80 },
  { title: '更新时间', key: 'updated_at', width: 120 },
  { title: '操作', key: 'actions', width: 100 },
];

function getFireRatingClass(rating: string) {
  if (rating === 'A级') return 'bg-success-50 text-success-600';
  if (rating === 'B1级') return 'bg-warning-50 text-warning-600';
  if (rating === 'B2级') return 'bg-accent-50 text-accent-600';
  return 'bg-gray-100 text-gray-500';
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN');
}

async function fetchCategories() {
  try {
    const res = await productsAPI.categories();
    const raw = unwrapApiData<unknown>(res);
    if (Array.isArray(raw)) {
      categories.value = raw;
      return;
    }
    if (
      raw &&
      typeof raw === 'object' &&
      Array.isArray((raw as { categories?: unknown }).categories)
    )
      categories.value = (raw as { categories: any[] }).categories;
    else categories.value = [];
  } catch (e) {
    if (import.meta.env.DEV) console.error('Failed to fetch categories:', e);
    categories.value = [];
  }
}

function listQueryParams(page: number) {
  const params: Record<string, unknown> = {
    page,
    page_size: pagination.value.pageSize,
  };
  if (search.value) params.search = search.value;
  if (filterCategory.value) params.category_id = filterCategory.value;
  if (filterStatus.value === 'true' || filterStatus.value === 'false')
    params.is_active = filterStatus.value === 'true';
  return params;
}

async function fetchProducts(page = 1) {
  loading.value = true;
  listError.value = '';
  pagination.value.current = page;
  try {
    const params = listQueryParams(page);

    const res = await productsAPI.list(params as Record<string, any>);
    const data = unwrapApiData<Record<string, unknown>>(res) as
      | Record<string, unknown>
      | null
      | undefined;
    const items = Array.isArray(data?.items)
      ? (data!.items as any[])
      : Array.isArray(data)
        ? (data as unknown as any[])
        : [];
    const catMap = new Map(
      Array.isArray(categories.value) ? categories.value.map((c: any) => [c.id, c.name]) : []
    );
    products.value = items.map((p: any) => ({
      ...p,
      category_name: catMap.get(p.category_id) || p.category_name || '-',
    }));
    const total = typeof data?.total === 'number' ? data.total : items.length;
    pagination.value.total = total;
  } catch (e: unknown) {
    if (import.meta.env.DEV) console.error('Failed to fetch products:', e);
    products.value = [];
    pagination.value.total = 0;
    listError.value = '产品列表加载失败（请确认已登录且后端 /api/v1/products 可用）。';
    message.error(listError.value);
  } finally {
    loading.value = false;
    initialLoading.value = false;
  }
}

function triggerImport() {
  importInputRef.value?.click();
}

async function onImportFile(ev: Event) {
  const input = ev.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  try {
    const fd = new FormData();
    fd.append('file', file);
    const res = await productsAPI.importCsv(fd);
    const body = unwrapApiData<Record<string, unknown>>(res) as Record<string, unknown> | undefined;
    const n = Number(body?.imported_count ?? 0);
    const errs = body?.errors as string[] | undefined;
    if (errs?.length) message.warning(`已导入 ${n} 条，部分行失败：${errs.slice(0, 3).join('；')}`);
    else message.success(`导入完成，共 ${n} 条`);
    await fetchProducts(1);
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '导入失败');
  } finally {
    input.value = '';
  }
}

async function handleExportCsv() {
  exporting.value = true;
  try {
    const params = listQueryParams(pagination.value.current);
    delete params.page;
    delete params.page_size;
    const res = await productsAPI.exportCsv(params);
    const blob = res.data as Blob;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `products-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    message.success('已开始下载导出文件');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '导出失败（需管理员登录）');
  } finally {
    exporting.value = false;
  }
}

function handleDelete(record: any) {
  ydConfirm({
    title: '确认删除',
    content: `确定要删除产品 "${record.name}" 吗？此操作不可撤销。`,
    okType: 'danger',
    onOk() {
      return (async () => {
        try {
          await productsAPI.delete(record.id);
          await fetchProducts(pagination.value.current);
          message.success('已删除');
        } catch (e: any) {
          Modal.error({ title: '删除失败', content: e.message });
        }
      })();
    },
  });
}

onMounted(async () => {
  await fetchCategories();
  await fetchProducts();
});
</script>

<style scoped>
.product-table :deep(.ant-table-thead > tr > th) {
  background: #f8fafc;
  font-weight: 600;
  color: #64748b;
  border-bottom: 1px solid #e2e8f0;
}

.product-table :deep(.ant-table-tbody > tr:hover > td) {
  background: #f8fafc;
}

.product-table :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f1f5f9;
  padding: 16px;
}
</style>
