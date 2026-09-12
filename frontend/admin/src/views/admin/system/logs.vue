<template>
  <YdPage title="系统日志" subtitle="操作审计流水 · GET /api/v1/system/audit/logs" surface="elevated">
    <template #actions>
      <a-button :disabled="!displayRows.length" @click="exportJson">
        <DownloadOutlined />
        导出当前页 JSON
      </a-button>
    </template>
  <div class="logs-page">
    <a-alert
      type="info"
      show-icon
      style="margin-bottom: 16px"
      message="与旧版日志视图的区别"
      description="筛选条件中「动作 / 资源类型」会传给后端；「关键词」仅过滤表格中已加载的行。"
    />

    <div class="filter-bar">
      <a-input
        v-model:value="action"
        placeholder="动作 action（后端）"
        allow-clear
        class="search-input"
        @press-enter="fetch(1)"
      />
      <a-input
        v-model:value="resourceType"
        placeholder="资源类型 resource_type（后端）"
        allow-clear
        class="search-input"
        @press-enter="fetch(1)"
      />
      <a-range-picker
        v-model:value="dateRange"
        show-time
        format="YYYY-MM-DD HH:mm"
      />
      <a-input
        v-model:value="keyword"
        placeholder="关键词（本地过滤 detail）"
        allow-clear
        class="search-input"
      />
      <a-button
        type="primary"
        :loading="loading"
        @click="fetch(1)"
      >
        <SearchOutlined />
        查询
      </a-button>
    </div>

    <div class="table-container">
      <a-table
        :columns="columns"
        :data-source="displayRows"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        :scroll="{ x: 1100 }"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'detail'">
            <span
              class="log-content"
              :title="record.detail"
            >{{ record.detail }}</span>
          </template>
        </template>
      </a-table>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import type { TableColumnsType } from 'ant-design-vue';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import { FileTextOutlined, DownloadOutlined, SearchOutlined } from '@ant-design/icons-vue';
import { systemAPI } from '@/api';

interface AuditRow {
  id: string;
  user_id?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  detail?: string | null;
  ip_address?: string | null;
  created_at?: string | null;
}

const loading = ref(false);
const rows = ref<AuditRow[]>([]);
const action = ref('');
const resourceType = ref('');
const keyword = ref('');
const dateRange = ref<[Dayjs, Dayjs] | undefined>(undefined);

const pagination = ref({
  current: 1,
  pageSize: 15,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
});

const columns: TableColumnsType<AuditRow> = [
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 190 },
  { title: '动作', dataIndex: 'action', key: 'action', width: 130 },
  { title: '资源类型', dataIndex: 'resource_type', key: 'resource_type', width: 120 },
  { title: '资源 ID', dataIndex: 'resource_id', key: 'resource_id', width: 120, ellipsis: true },
  { title: '详情', dataIndex: 'detail', key: 'detail', ellipsis: true },
  { title: 'IP', dataIndex: 'ip_address', key: 'ip_address', width: 130 },
];

const displayRows = computed(() => {
  const k = keyword.value.trim().toLowerCase();
  if (!k) return rows.value;
  return rows.value.filter((r) => {
    const blob =
      `${r.detail || ''} ${r.action} ${r.resource_type} ${r.resource_id || ''}`.toLowerCase();
    return blob.includes(k);
  });
});

async function fetch(page = 1, pageSize?: number) {
  loading.value = true;
  const ps = pageSize ?? pagination.value.pageSize;
  pagination.value.current = page;
  try {
    const params: Record<string, string | number> = { page, page_size: ps };
    if (action.value.trim()) params.action = action.value.trim();
    if (resourceType.value.trim()) params.resource_type = resourceType.value.trim();
    if (dateRange.value?.[0]) {
      params.start_time = dateRange.value[0].toISOString();
    }
    if (dateRange.value?.[1]) {
      params.end_time = dateRange.value[1].toISOString();
    }
    const res = await systemAPI.auditLogs(params);
    const raw = res.data as
      | unknown[]
      | { items?: unknown[]; data?: unknown[]; total?: number }
      | null;
    let list: AuditRow[] = [];
    let total = 0;
    if (Array.isArray(raw)) {
      list = raw as AuditRow[];
      total = list.length;
    } else if (raw && typeof raw === 'object') {
      const o = raw as { items?: unknown[]; data?: unknown[]; total?: number };
      const arr = Array.isArray(o.items) ? o.items : Array.isArray(o.data) ? o.data : [];
      list = arr as AuditRow[];
      total = typeof o.total === 'number' ? o.total : list.length;
    }
    rows.value = list;
    pagination.value.total = total;
    pagination.value.pageSize = ps;
  } catch (e: any) {
    message.error(e?.response?.data?.message || e?.message || '加载审计日志失败');
    rows.value = [];
  } finally {
    loading.value = false;
  }
}

function onTableChange(pag: { current?: number; pageSize?: number }) {
  fetch(pag.current ?? 1, pag.pageSize);
}

function exportJson() {
  const blob = new Blob([JSON.stringify(displayRows.value, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `audit-logs-page-${pagination.value.current}-${dayjs().format('YYYYMMDDHHmmss')}.json`;
  a.click();
  URL.revokeObjectURL(url);
  message.success('已导出当前表格所显示的行');
}

onMounted(() => fetch());
</script>

<style scoped lang="scss">
.logs-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;

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
      max-width: 720px;
    }
  }

  .export-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;

  .search-input {
    width: 220px;
  }
}

.table-container {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

  .log-content {
    max-width: 420px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: block;
  }
}
</style>
