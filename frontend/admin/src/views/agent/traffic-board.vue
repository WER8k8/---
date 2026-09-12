<template>
  <YdPage surface="elevated">
  <div class="agent-traffic-page coachpro-tertiary coachpro-tertiary--agent">
    <TrafficBoardPanel
      api-path="/agent/traffic-board"
      title="辖区流量看板"
      subtitle="您及下级代理辖区的访客、点击与转化归因"
    />

    <section class="agent-client-inbox uj-glass-panel coachpro-panel">
      <div class="agent-client-inbox__head">
        <h2>辖区客户 inbox</h2>
        <a-button size="small" :loading="clientsLoading" @click="() => loadClients()">刷新</a-button>
      </div>
      <YdEmptyState
        v-if="!clientsLoading && !clientRows.length"
        variant="inquiry"
        title="暂无辖区客户"
        description="开户成功后客户将出现在此列表"
        @action="router.push('/agent/account-opening')"
      />
      <YdDataTable
        v-else
        :columns="clientColumns"
        :data-source="clientRows"
        :loading="clientsLoading"
        :pagination="clientPagination"
        @page-change="onClientPageChange"
      />
    </section>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import { YdDataTable, YdEmptyState, YdPage } from '@/components/youding';
import TrafficBoardPanel from '@/components/traffic/TrafficBoardPanel.vue';
import { apiGet } from '@/utils/api';

const router = useRouter();
const clientsLoading = ref(false);
const clientRows = ref<Record<string, unknown>[]>([]);
const clientPagination = ref({ current: 1, pageSize: 10, total: 0 });

const clientColumns = [
  { title: '客户', dataIndex: 'name', key: 'name' },
  { title: '域名', dataIndex: 'domain', key: 'domain' },
  { title: '套餐', dataIndex: 'plan_name', key: 'plan_name' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '到期', dataIndex: 'expires_at', key: 'expires_at' },
];

async function loadClients(page = 1) {
  clientsLoading.value = true;
  try {
    const data = (await apiGet('/agent/clients', {
      page,
      page_size: clientPagination.value.pageSize,
    })) as {
      items?: Record<string, unknown>[];
      total?: number;
      page?: number;
    };
    clientRows.value = data.items ?? [];
    clientPagination.value = {
      ...clientPagination.value,
      current: data.page ?? page,
      total: data.total ?? clientRows.value.length,
    };
  } catch {
    clientRows.value = [];
  } finally {
    clientsLoading.value = false;
  }
}

function onClientPageChange(pag: { current: number; pageSize: number }) {
  void loadClients(pag.current);
}

onMounted(async () => {
  try {
    await apiGet('/agent/traffic-board');
  } catch {
    /* 空状态 */
  }
  await loadClients();
});
</script>

<style scoped>
.agent-traffic-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.agent-client-inbox {
  padding: 20px;
}
.agent-client-inbox__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.agent-client-inbox__head h2 {
  font-size: 1rem;
  font-weight: 700;
  margin: 0;
}
</style>
