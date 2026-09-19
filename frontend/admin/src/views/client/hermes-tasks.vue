<template>
  <YdPage title="Hermes 任务" subtitle="功能域任务中心 · 计划与节点由爱马仕编排驱动" surface="elevated">
    <YdSearchBar @search="reload" @reset="onReset">
      <a-input v-model:value="planFilter" placeholder="按 plan_id 过滤（可选）" allow-clear style="width: 220px" />
      <a-select v-model:value="statusFilter" placeholder="状态" allow-clear style="width: 140px">
        <a-select-option value="created">created</a-select-option>
        <a-select-option value="executing">executing</a-select-option>
        <a-select-option value="done">done</a-select-option>
        <a-select-option value="failed">failed</a-select-option>
        <a-select-option value="wait_human">wait_human</a-select-option>
      </a-select>
      <template #extra>
        <a-button type="default" :loading="loading" @click="reload">刷新</a-button>
        <a-button type="link" @click="goFulfillment">去履约队列</a-button>
      </template>
    </YdSearchBar>

    <YdEmptyState
      v-if="!loading && !filtered.length"
      variant="inquiry"
      title="暂无 Hermes 任务"
      description="在履约队列点「一键履约 · Hermes」或提交社媒拓客后，任务会出现在这里"
      @action="goFulfillment"
    />

    <div v-else class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="columns"
        :data-source="filtered"
        :loading="loading"
        :pagination="{ current: 1, pageSize: 20, total: filtered.length }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'golden_path'">
            <a-tag v-if="record.golden_path" color="geekblue">{{ record.golden_path }}</a-tag>
            <span v-else>--</span>
          </template>
          <template v-else-if="column.key === 'plan_id'">
            <span class="font-mono text-xs">{{ shortId(record.plan_id) }}</span>
          </template>
          <template v-else-if="column.key === 'node_summary'">
            <span>{{ nodeSummary(record) }}</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" size="small" @click="openDetail(record)">查看节点</a-button>
          </template>
        </template>
      </YdDataTable>
    </div>

    <a-drawer v-model:open="drawerOpen" :width="520" title="Hermes 计划节点">
      <a-spin v-if="detailLoading" />
      <template v-else-if="detail">
        <a-descriptions :column="1" size="small" bordered class="mb-4">
          <a-descriptions-item label="plan_id">{{ detail.plan?.plan_id }}</a-descriptions-item>
          <a-descriptions-item label="状态">{{ detail.plan?.status }}</a-descriptions-item>
          <a-descriptions-item label="黄金路径">{{ detail.plan?.golden_path || '--' }}</a-descriptions-item>
          <a-descriptions-item label="意图">{{ detail.plan?.intent || '--' }}</a-descriptions-item>
          <a-descriptions-item label="图来源">{{ detail.plan?.graph_source || '--' }}</a-descriptions-item>
        </a-descriptions>
        <a-table
          size="small"
          :data-source="detail.nodes || []"
          :pagination="false"
          :columns="nodeColumns"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="statusColor(record.status)">{{ record.status }}</a-tag>
            </template>
            <template v-else-if="column.key === 'executor'">
              <span>{{ record.executor || record.task_type || '--' }}</span>
            </template>
          </template>
        </a-table>
      </template>
    </a-drawer>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { YdDataTable, YdEmptyState, YdPage, YdSearchBar } from '@/components/youding';
import { getHermesTaskDetail, listHermesTasks, type HermesPlanItem, type HermesTaskDetail } from '@/api/orchestration';

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const items = ref<HermesPlanItem[]>([]);
const planFilter = ref('');
const statusFilter = ref<string | undefined>(undefined);
const drawerOpen = ref(false);
const detailLoading = ref(false);
const detail = ref<HermesTaskDetail | null>(null);

const columns = [
  { key: 'plan_id', title: '计划 ID', align: 'center' as const },
  { key: 'status', title: '状态', align: 'center' as const },
  { key: 'golden_path', title: '黄金路径', align: 'center' as const },
  { key: 'node_summary', title: '节点', align: 'center' as const },
  { key: 'intent', title: '意图', align: 'left' as const },
  { key: 'created_at', title: '创建时间', align: 'center' as const },
  { key: 'action', title: '操作', align: 'center' as const, width: 100 },
];

const nodeColumns = [
  { key: 'executor', title: '执行器' },
  { key: 'status', title: '状态' },
  { key: 'capability', title: '能力' },
  { key: 'error_message', title: '错误' },
];

const filtered = computed(() => {
  if (!planFilter.value) return items.value;
  const key = planFilter.value.trim().toLowerCase();
  return items.value.filter((x) => String(x.plan_id || '').toLowerCase().includes(key));
});

function shortId(id: unknown): string {
  const s = String(id || '');
  return s.length > 12 ? `${s.slice(0, 8)}…` : s || '--';
}

function nodeSummary(r: HermesPlanItem): string {
  const list = (r.node_statuses || []) as string[];
  if (!list.length) return `${r.child_count || 0} 节点`;
  const done = list.filter((s) => s === 'done').length;
  return `${done}/${list.length} done · ${r.child_count || list.length} 节点`;
}

function statusColor(s: unknown): string {
  const v = String(s || '');
  if (v === 'done') return 'green';
  if (v === 'failed' || v === 'timeout') return 'red';
  if (v === 'wait_human' || v === 'review') return 'orange';
  if (v === 'executing' || v === 'planning') return 'blue';
  return 'default';
}

function onReset() {
  planFilter.value = '';
  statusFilter.value = undefined;
  void reload();
}

async function reload() {
  loading.value = true;
  try {
    const page = await listHermesTasks({ status: statusFilter.value, limit: 50 });
    items.value = page?.items || [];
  } catch {
    items.value = [];
  } finally {
    loading.value = false;
  }
}

async function openDetail(record: HermesPlanItem) {
  drawerOpen.value = true;
  detailLoading.value = true;
  detail.value = null;
  try {
    detail.value = await getHermesTaskDetail(String(record.plan_id));
  } catch {
    detail.value = null;
  } finally {
    detailLoading.value = false;
  }
}

function goFulfillment() {
  router.push('/client/queues/fulfillment');
}

onMounted(async () => {
  const q = route.query.plan;
  if (q) planFilter.value = String(q);
  await reload();
  if (planFilter.value) {
    const hit = items.value.find((x) => String(x.plan_id) === planFilter.value);
    if (hit) void openDetail(hit);
  }
});
</script>
