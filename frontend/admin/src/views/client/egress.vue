<template>
  <YdPage title="出口代理槽位" :subtitle="pageSubtitle" surface="elevated">
  <div class="client-egress coachpro-tertiary coachpro-tertiary--client p-4 max-w-3xl mx-auto">
    <a-alert
      v-if="(summary.pending_manual_count ?? 0) > 0"
      type="info"
      show-icon
      class="mb-4"
      message="等待运营配置"
      description="已占用配额，运营将在工作台为您录入代理地址与账密。"
    />
    <a-alert
      v-else-if="(summary.provisioning_count ?? 0) > 0 && summary.provision_mode === 'asocks'"
      type="info"
      show-icon
      class="mb-4"
      message="ASocks 开通中"
      description="已向 ASocks 提交采购，通常 1～3 分钟完成，请稍候自动刷新。"
    />
    <template v-if="loading">
      <SkeletonCard variant="kpi" />
      <div class="mt-4">
        <SkeletonCard variant="table" :rows="4" />
      </div>
    </template>
    <template v-else>
      <a-row :gutter="[16, 16]" class="mb-4">
        <a-col :span="8">
          <a-card size="small">
            <a-statistic title="套餐配额" :value="summary.quota ?? 0" />
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small">
            <a-statistic title="已开通" :value="summary.assigned_count ?? 0" />
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small">
            <a-statistic title="可再申请" :value="summary.remaining ?? 0" :value-style="{ color: '#16a34a' }" />
          </a-card>
        </a-col>
      </a-row>

      <a-card title="我的 IP 槽位" size="small" class="mb-4">
        <a-table
          :columns="cols"
          :data-source="summary.slots || []"
          :pagination="false"
          row-key="id"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'slot_status'">
              <a-tag :color="statusColor(record.slot_status)">{{ statusLabel(record.slot_status) }}</a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'host'">
              <span v-if="record.slot_status === 'assigned'">{{ record.host }}:{{ record.port }}</span>
              <span v-else class="text-gray-500">—</span>
            </template>
            <template v-else-if="column.key === 'action'">
              <a-button
                v-if="record.slot_status === 'failed'"
                type="link"
                size="small"
                :loading="retryingId === record.id"
                @click="retrySlot(record.id)"
              >
                重新申请
              </a-button>
            </template>
          </template>
        </a-table>
        <p v-if="failedHint" class="text-xs text-red-600 mt-2">{{ failedHint }}</p>
        <a-space class="mt-4">
          <a-button type="primary" :loading="requesting" :disabled="!((summary.remaining ?? 0) > 0)" @click="requestSlot">
            申请 1 个槽位
          </a-button>
        </a-space>
      </a-card>

      <a-card title="加购 IP 槽位" size="small">
        <a-form layout="inline">
          <a-form-item label="数量">
            <a-input-number v-model:value="buySlots" :min="1" :max="10" />
          </a-form-item>
          <a-form-item label="支付">
            <a-select v-model:value="channel" style="width: 120px">
              <a-select-option value="wechat">微信</a-select-option>
              <a-select-option value="alipay">支付宝</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item>
            <a-button type="primary" :loading="buying" @click="buyAddon">
              下单加购（约 ¥{{ (buySlots * 99).toFixed(0) }}）
            </a-button>
          </a-form-item>
        </a-form>
        <p class="text-xs text-gray-500 mt-2">
          支付成功后增加配额；
          <template v-if="summary.provision_mode === 'asocks'">申请槽位后将自动向 ASocks 开通。</template>
          <template v-else>线路由运营采购并录入。</template>
        </p>
      </a-card>
    </template>

    <a-modal v-model:open="qrOpen" title="扫码支付 IP 槽位" :footer="null">
      <p class="text-sm text-gray-600 mb-2">{{ currentSubject }}</p>
      <p class="font-semibold">¥{{ (currentAmount / 100).toFixed(2) }}</p>
      <div v-if="currentCodeUrl" class="mt-3 text-center">
        <img
          :src="`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(currentCodeUrl)}`"
          alt="支付二维码"
          class="mx-auto border rounded"
        />
      </div>
      <a-button
        v-if="currentMock && currentOrderId"
        type="primary"
        block
        class="mt-4"
        :loading="mockPaying"
        @click="mockPay"
      >
        演示环境：模拟支付成功
      </a-button>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { apiGet, apiPost } from '@/utils/api';

const loading = ref(false)
const requesting = ref(false)
const buying = ref(false)
const tenantId = ref('')
const pollTimer = ref<ReturnType<typeof setInterval> | null>(null)
const retryingId = ref<string | number | null>(null)

interface EgressSlot {
  id: string | number
  region?: string
  host?: string | null
  port?: number
  slot_status?: string
  provision_error?: string
}
interface EgressSummary {
  quota?: number
  assigned_count?: number
  pending_manual_count?: number
  provisioning_count?: number
  provision_mode?: string
  remaining?: number
  slots?: EgressSlot[]
}
const summary = ref<EgressSummary>({ quota: 0, assigned_count: 0, remaining: 0, slots: [] })
const buySlots = ref(1)
const channel = ref('wechat')
const qrOpen = ref(false)
const currentOrderId = ref('')
const currentMock = ref(false)
const currentAmount = ref(0)
const currentSubject = ref('')
const currentCodeUrl = ref('')
const mockPaying = ref(false)

const failedHint = computed(() => {
  const failed = (summary.value.slots || []).find((s) => s.slot_status === 'failed')
  return failed?.provision_error || ''
})

const pageSubtitle = computed(() => {
  if (summary.value.provision_mode === 'asocks') {
    return '租户申请后自动向 ASocks 采购美国住宅代理，无预库存'
  }
  if (summary.value.provision_mode === 'mock') {
    return '演示环境：模拟自动开通'
  }
  return '由运营配置独享线路'
})

const cols = [
  { title: '区域', dataIndex: 'region', width: 80 },
  { title: '地址', dataIndex: 'host', ellipsis: true },
  { title: '状态', dataIndex: 'slot_status', width: 120 },
  { title: '操作', key: 'action', width: 100 },
]

function statusLabel(st?: string) {
  const m: Record<string, string> = {
    provisioning: '开通中',
    pending_manual: '待运营配置',
    assigned: '已开通',
    failed: '失败',
    disabled: '已停用',
  }
  return m[st || ''] || st || '—'
}

function statusColor(st?: string) {
  const m: Record<string, string> = {
    provisioning: 'processing',
    pending_manual: 'warning',
    assigned: 'success',
    failed: 'error',
  }
  return m[st || ''] || 'default'
}

function startPollIfNeeded() {
  if (pollTimer.value) clearInterval(pollTimer.value)
  const need = (summary.value.slots || []).some((s) => s.slot_status === 'provisioning')
  if (!need) {
    pollTimer.value = null
    return
  }
  pollTimer.value = setInterval(() => loadSummary(true), 4000)
}

async function loadTenantId() {
  try {
    const dash = await apiGet('/client/dashboard')
    tenantId.value = dash.tenant_id || ''
  } catch {
    tenantId.value = ''
  }
}

async function loadSummary(silent = false) {
  if (!silent) loading.value = true
  try {
    summary.value = (await apiGet('/egress/my')) || {}
    startPollIfNeeded()
  } catch (e: unknown) {
    if (!silent) message.error((e as Error)?.message || '加载失败')
  } finally {
    if (!silent) loading.value = false
  }
}

async function requestSlot() {
  requesting.value = true
  try {
    const res = await apiPost('/egress/request-slot', {})
    message.success(res?.message || '申请已提交')
    await loadSummary()
  } catch (e: unknown) {
    message.error((e as Error)?.message || '申请失败')
  } finally {
    requesting.value = false
  }
}

async function retrySlot(endpointId: string | number) {
  retryingId.value = endpointId
  try {
    await apiPost(`/egress/slots/${endpointId}/retry`, {})
    message.success('已重新提交')
    await loadSummary()
  } catch (e: unknown) {
    message.error((e as Error)?.message || '操作失败')
  } finally {
    retryingId.value = null
  }
}

async function buyAddon() {
  if (!tenantId.value) {
    message.warning('无法获取租户 ID，请刷新工作台')
    return
  }
  buying.value = true
  try {
    const res = await apiPost('/payment/addon/egress-ip', {
      tenant_id: tenantId.value,
      slots: buySlots.value,
      channel: channel.value,
    })
    currentOrderId.value = res.id
    currentMock.value = !!res.mock
    currentAmount.value = res.amount
    currentSubject.value = res.subject
    currentCodeUrl.value = res.code_url || ''
    qrOpen.value = true
  } catch (e: unknown) {
    message.error((e as Error)?.message || '下单失败')
  } finally {
    buying.value = false
  }
}

async function mockPay() {
  mockPaying.value = true
  try {
    await apiPost('/payment/mock-pay', { order_id: currentOrderId.value })
    message.success('加购成功，请申请槽位后等待运营配置')
    qrOpen.value = false
    await loadSummary()
  } catch (e: unknown) {
    message.error((e as Error)?.message || '支付失败')
  } finally {
    mockPaying.value = false
  }
}

onMounted(async () => {
  await loadTenantId()
  await loadSummary()
})

onUnmounted(() => {
  if (pollTimer.value) clearInterval(pollTimer.value)
})
</script>
