<template>

  <YdPage title="订单运单回填" subtitle="填写运单号并同步轨迹至订单状态" surface="elevated">

    <div ref="tablePanelRef" class="yd-panel yd-table-panel">

      <div class="panel-head mb-3">

        <YdTableToolbar

          :loading="loading"

          :target-ref="tablePanelRef"

          :show-export="false"

          @refresh="load"

        />

      </div>

      <YdDataTable

        :columns="cols"

        :data-source="rows"

        :loading="loading"

        :pagination="false"

        :table-props="{ size: tableSize, rowKey: 'id' }"

      >

        <template #bodyCell="{ column, record }">

          <template v-if="column.key === 'tracking'">

            <a-input

              v-model:value="record._tracking"

              size="small"

              placeholder="运单号"

              style="width: 140px"

            />

          </template>

          <template v-if="column.key === 'actions'">

            <a-space>

              <a-button size="small" type="primary" @click="saveTracking(record)">保存</a-button>

              <a-button

                size="small"

                :disabled="!record.tracking_number && !record._tracking"

                @click="syncTracking(record)"

              >

                同步轨迹

              </a-button>

            </a-space>

          </template>

        </template>

      </YdDataTable>

    </div>

  </YdPage>

</template>



<script setup lang="ts">

import { onMounted, ref } from 'vue'

import { storeToRefs } from 'pinia'

import { message } from 'ant-design-vue'

import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'

import { useUiPreferencesStore } from '@/stores/uiPreferences'

import { apiGet, apiPost, authHeaders } from '@/utils/api'



type Row = {

  id: string

  order_number: string

  status: string

  tracking_number?: string

  _tracking?: string

}



const loading = ref(false)

const rows = ref<Row[]>([])

const tablePanelRef = ref<HTMLElement | null>(null)

const ui = useUiPreferencesStore()

const { antTableSize: tableSize } = storeToRefs(ui)



const cols = [

  { title: '订单号', dataIndex: 'order_number', key: 'order_number', width: 140 },

  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },

  { title: '运单号', key: 'tracking', width: 160 },

  { title: '操作', key: 'actions', width: 180 },

]



async function load() {

  loading.value = true

  try {

    const list = (await apiGet('/orders/?limit=50')) as Row[]

    rows.value = (Array.isArray(list) ? list : []).map((r) => ({

      ...r,

      _tracking: r.tracking_number || '',

    }))

  } catch (e: unknown) {

    message.error((e as Error)?.message || '加载失败')

  } finally {

    loading.value = false

  }

}



async function saveTracking(record: Row) {

  const num = (record._tracking || '').trim()

  if (!num) {

    message.warning('请填写运单号')

    return

  }

  try {

    const res = await fetch(`/api/v1/orders/${record.id}/tracking`, {

      method: 'PATCH',

      headers: authHeaders(),

      body: JSON.stringify({ tracking_number: num }),

    })

    if (!res.ok) throw new Error('patch failed')

    message.success('运单号已保存')

    await load()

  } catch {

    message.error('保存失败')

  }

}



async function syncTracking(record: Row) {

  const num = (record._tracking || record.tracking_number || '').trim()

  if (!num) {

    message.warning('请先填写运单号')

    return

  }

  try {

    await apiPost(`/logistics/orders/${record.id}/sync-tracking`, {})

    message.success('轨迹已同步')

    await load()

  } catch (e: unknown) {

    message.error((e as Error)?.message || '同步失败')

  }

}



onMounted(load)

</script>



<style scoped>

.panel-head {

  display: flex;

  justify-content: flex-end;

  margin-bottom: 8px;

}

</style>

