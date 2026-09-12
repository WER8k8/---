<template>
  <YdPage title="现金券线下核销" subtitle="邀请满 5 人发放的现金券，财务线下兑付后在此确认" surface="elevated">
    <template #actions>
      <a-tag color="orange">待核销 {{ items.length }}</a-tag>
    </template>
  <div class="p-4 space-y-4 animate-fade-in">
    <div ref="tablePanelRef" class="yd-table-panel">
      <div class="table-toolbar-row mb-3">
        <YdTableToolbar
          :loading="loading"
          :target-ref="tablePanelRef"
          :show-export="false"
          @refresh="loadPending"
        />
      </div>
      <YdDataTable
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="tablePagination"
        :table-props="{ rowKey: 'id', size: tableSize }"
      >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'amount'">
          <span class="font-semibold text-amber-600">¥{{ (record.reward_amount / 100).toFixed(0) }}</span>
        </template>
        <template v-if="column.key === 'action'">
          <a-popconfirm title="确认已线下兑付？" @confirm="redeem(record.id)">
            <a-button type="link" size="small">确认核销</a-button>
          </a-popconfirm>
        </template>
      </template>
      <template #emptyText>
        <a-empty description="暂无待核销现金券" />
      </template>
      </YdDataTable>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { message } from 'ant-design-vue';
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding';
import { useUiPreferencesStore } from '@/stores/uiPreferences';
import { getAuthToken } from '@/utils/api';

const loading = ref(false)
const items = ref<any[]>([])
const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

const tablePagination = computed(() => ({
  current: 1,
  pageSize: 10,
  total: items.value.length,
}))

const columns = [
  { title: '邀请方', dataIndex: 'inviter_name', key: 'inviter_name' },
  { title: '被邀请方', dataIndex: 'invited_name', key: 'invited_name' },
  { title: '金额', key: 'amount', width: 100 },
  { title: '奖励时间', dataIndex: 'rewarded_at', key: 'rewarded_at', width: 180 },
  { title: '操作', key: 'action', width: 100 },
]

function headers(): Record<string, string> {
  const tk = getAuthToken()
  return tk ? { Authorization: `Bearer ${tk}` } : {}
}

async function loadPending() {
  loading.value = true
  try {
    const res = await fetch('/api/v1/referral/admin/cash-coupons/pending', { headers: headers() })
    const body = await res.json()
    if (!res.ok) {
      message.error(body.message || '加载失败')
      return
    }
    items.value = body.data?.items || []
  } catch {
    message.error('网络错误')
  } finally {
    loading.value = false
  }
}

async function redeem(recordId: string) {
  try {
    const res = await fetch(
      `/api/v1/referral/admin/cash-coupons/${recordId}/redeem`,
      { method: 'POST', headers: headers() },
    )
    const body = await res.json()
    if (!res.ok) {
      message.error(body.message || '核销失败')
      return
    }
    message.success('已核销')
    await loadPending()
  } catch {
    message.error('核销请求失败')
  }
}

onMounted(loadPending)
</script>
