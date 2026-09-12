<template>
  <a-card
    :title="title"
    size="small"
  >
    <a-space
      wrap
      style="margin-bottom: 12px"
    >
      <a-input
        v-model:value="actionFilter"
        placeholder="筛选 action"
        allow-clear
        style="width: 160px"
        @press-enter="() => fetch(1)"
      />
      <a-input
        v-model:value="resourceFilter"
        placeholder="筛选 resource_type"
        allow-clear
        style="width: 180px"
        @press-enter="() => fetch(1)"
      />
      <a-button
        type="primary"
        :loading="loading"
        @click="() => fetch(1)"
      >
        查询
      </a-button>
    </a-space>
    <a-table
      :columns="columns"
      :data-source="rows"
      :loading="loading"
      :pagination="pagination"
      row-key="id"
      size="small"
      :scroll="{ x: 960 }"
      @change="onTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'detail'">
          <span
            class="cell-detail"
            :title="record.detail"
          >{{ record.detail }}</span>
        </template>
      </template>
    </a-table>
  </a-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import type { TableColumnsType } from 'ant-design-vue';
import { systemAPI } from '@/api';

withDefaults(
  defineProps<{
    title?: string;
  }>(),
  { title: '操作审计（后端 OperationLog）' }
);

const loading = ref(false);
const rows = ref<any[]>([]);
const actionFilter = ref('');
const resourceFilter = ref('');
const pagination = ref({ current: 1, pageSize: 15, total: 0, showSizeChanger: true });

const columns: TableColumnsType = [
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '动作', dataIndex: 'action', key: 'action', width: 140 },
  { title: '资源类型', dataIndex: 'resource_type', key: 'resource_type', width: 120 },
  { title: '详情', dataIndex: 'detail', key: 'detail', ellipsis: true },
  { title: 'IP', dataIndex: 'ip_address', key: 'ip_address', width: 130 },
];

async function fetch(page = 1, pageSize?: number) {
  loading.value = true;
  const ps = pageSize ?? pagination.value.pageSize;
  pagination.value.current = page;
  try {
    const res = await systemAPI.auditLogs({
      page,
      page_size: ps,
      ...(actionFilter.value ? { action: actionFilter.value } : {}),
      ...(resourceFilter.value ? { resource_type: resourceFilter.value } : {}),
    });
    const raw = res.data as
      | unknown[]
      | { items?: unknown[]; data?: unknown[]; total?: number }
      | null;
    let list: any[] = [];
    let total = 0;
    if (Array.isArray(raw)) {
      list = raw as any[];
      total = list.length;
    } else if (raw && typeof raw === 'object') {
      const o = raw as { items?: unknown[]; data?: unknown[]; total?: number };
      list = (Array.isArray(o.items) ? o.items : Array.isArray(o.data) ? o.data : []) as any[];
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

onMounted(() => fetch());
</script>

<style scoped>
.cell-detail {
  display: inline-block;
  max-width: 420px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
</style>
