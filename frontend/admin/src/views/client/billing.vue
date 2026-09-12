<template>
  <YdPage title="套餐续费" subtitle="选择套餐并完成支付" surface="elevated">
    <template #actions>
      <a-button type="primary" ghost @click="router.push('/client/tokens')">去充值 AI 流量 →</a-button>
    </template>
  <div class="client-billing coachpro-tertiary coachpro-tertiary--client space-y-4 max-w-5xl mx-auto">
    <a-alert
      v-if="currentPlanName"
      type="info"
      show-icon
      :message="`当前套餐：${currentPlanName}`"
      :description="planExpiry ? `到期：${planExpiry}` : undefined"
    />

    <a-card title="选购套餐">
      <template #extra>
        <a-radio-group v-model:value="billingCycle" button-style="solid" size="small">
          <a-radio-button value="monthly">月付</a-radio-button>
          <a-radio-button value="yearly">年付</a-radio-button>
        </a-radio-group>
      </template>

      <div v-if="plansLoading" class="text-center py-10">
        <a-spin />
      </div>
      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="plan in plans"
          :key="plan.id"
          class="rounded-xl border p-4 cursor-pointer transition-all"
          :class="
            selectedPlanId === plan.id
              ? 'border-primary-500 ring-2 ring-primary-100'
              : 'border-gray-200 hover:border-primary-300'
          "
          @click="selectedPlanId = plan.id"
        >
          <div class="font-semibold text-gray-900">{{ plan.name }}</div>
          <div class="text-2xl font-bold text-amber-600 my-2">
            ¥{{ displayPlanPrice(plan, billingCycle) }}
            <span class="text-sm font-normal text-gray-400">
              /{{ billingCycle === 'monthly' ? '月' : '年' }}
            </span>
          </div>
          <ul class="text-xs text-gray-600 space-y-1 mb-4 min-h-[4rem]">
            <li v-for="f in featureList(plan)" :key="f"><CheckOutlined class="feat-check" /> {{ f }}</li>
          </ul>
          <a-button type="primary" block @click.stop="handlePay(plan)">立即支付</a-button>
        </div>
      </div>
    </a-card>

    <a-card v-if="orders.length" title="我的支付记录" size="small">
      <a-table :data-source="orders" :columns="orderCols" row-key="id" size="small" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'pdf'">
            <a-button type="link" size="small" @click="() => downloadInvoicePdf(record)">下载 PDF</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="qrVisible" title="扫码支付" :footer="null" width="380px" centered>
      <div class="text-center py-4">
        <a-spin v-if="paying" tip="正在生成支付二维码..." />
        <template v-else>
          <img
            v-if="currentCodeUrl && !currentMock"
            :src="`https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(currentCodeUrl)}`"
            alt="支付二维码"
            class="mx-auto"
          />
          <div
            v-else-if="currentMock"
            class="mx-auto w-60 h-60 flex flex-col items-center justify-center border-2 border-dashed border-blue-300 rounded-xl text-blue-600"
          >
            <YdIllustration icon="CreditCardOutlined" size="lg" />
            <span class="mt-2 font-medium">演示环境 · 模拟支付</span>
          </div>
          <p class="mt-3 font-medium">{{ currentSubject }}</p>
          <p class="text-gray-500">
            ¥{{ currentAmount ? (currentAmount / 100).toFixed(2) : '0.00' }}
          </p>
          <p class="text-xs text-gray-400 mt-1">订单号 {{ currentOrderNo }}</p>
          <a-button
            v-if="currentMock && currentOrderId"
            type="primary"
            block
            class="mt-4"
            :loading="mockPaying"
            @click="onMockPay"
          >
            模拟支付成功
          </a-button>
        </template>
      </div>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { YdIllustration, YdPage } from '@/components/youding';
import { CheckOutlined } from '@ant-design/icons-vue';

const router = useRouter();
import { apiGet, getAuthToken } from '@/utils/api'
import {
  displayPlanPrice,
  featureList,
  usePlanPayment,
} from '@/composables/usePlanPayment'

const {
  plans,
  plansLoading,
  selectedPlanId,
  billingCycle,
  qrVisible,
  paying,
  currentCodeUrl,
  currentMock,
  currentOrderId,
  currentOrderNo,
  currentSubject,
  currentAmount,
  mockPaying,
  resolveTenantId,
  loadPlans,
  handlePay,
  mockPayOrder,
} = usePlanPayment()

const currentPlanName = ref('')
const planExpiry = ref('')
const tenantId = ref('')
const orders = ref<
  { id: string; amount: number; status: string; period: string; date: string }[]
>([])

const orderCols = [
  { title: '账单号', dataIndex: 'id', width: 140 },
  { title: '金额', dataIndex: 'amount', width: 90 },
  { title: '周期', dataIndex: 'period', width: 100 },
  { title: '状态', dataIndex: 'status', width: 90 },
  { title: '日期', dataIndex: 'date', width: 110 },
  { title: 'PDF', key: 'pdf', width: 90 },
]

async function loadTenantMeta() {
  try {
    const dash = await apiGet<{
      plan?: { name?: string }
      plan_expiry?: string
      subscription?: { plan_name?: string; expires_at?: string }
    }>('/client/dashboard')
    currentPlanName.value =
      dash?.plan?.name || dash?.subscription?.plan_name || ''
    planExpiry.value = dash?.plan_expiry || dash?.subscription?.expires_at || ''
  } catch {
    /* ignore */
  }
}

async function loadMyOrders() {
  const tid = await resolveTenantId()
  if (!tid) return
  tenantId.value = tid
  try {
    const r = await fetch(`/api/v1/tenants/invoices?tenant_id=${encodeURIComponent(tid)}`, {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    })
    if (!r.ok) return
    const d = await r.json()
    const items = d.data?.items || d.items || d.data || []
    orders.value = Array.isArray(items) ? items : []
  } catch {
    orders.value = []
  }
}

async function downloadInvoicePdf(record: Record<string, unknown>) {
  const orderId = String(record.id ?? '')
  if (!orderId) return
  const tid = tenantId.value || (await resolveTenantId())
  if (!tid) return
  const res = await fetch(`/api/v1/tenants/${tid}/invoices/${orderId}/pdf`, {
    headers: { Authorization: `Bearer ${getAuthToken()}` },
  })
  if (!res.ok) return
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `invoice-${orderId.slice(0, 8)}.pdf`
  a.click()
  URL.revokeObjectURL(a.href)
}

function onMockPay() {
  mockPayOrder(() => {
    loadMyOrders()
    loadTenantMeta()
  })
}

onMounted(async () => {
  await resolveTenantId()
  await Promise.all([loadPlans(), loadTenantMeta(), loadMyOrders()])
})
</script>
