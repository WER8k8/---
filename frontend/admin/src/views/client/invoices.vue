<template>
  <YdPage title="开票申请" subtitle="针对已支付订单申请增值税发票，须财务审核后开具" surface="elevated">
  <div class="coachpro-tertiary coachpro-tertiary--client p-4 max-w-4xl mx-auto space-y-4">
    <a-alert
      v-if="meta.disclaimer"
      type="warning"
      show-icon
      :message="'合规提示'"
      :description="meta.disclaimer"
    />
    <a-alert
      v-if="!meta.platform_ready"
      type="error"
      show-icon
      message="平台开票主体尚未配置"
      description="暂无法提交申请，请联系平台客服或稍后再试。"
    />

    <a-card title="提交申请" size="small">
      <a-form layout="vertical" :model="form" @finish="submit">
        <a-form-item label="关联已支付订单" required>
          <a-select
            v-model:value="form.payment_order_id"
            placeholder="选择订单"
            :options="orderOptions"
            :disabled="!eligibleOrders.length"
          />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="购方类型" required>
              <a-select v-model:value="form.buyer_type" :options="buyerTypeOptions" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="发票类型" required>
              <a-select v-model:value="form.invoice_type" :options="invoiceTypeOptions" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="发票抬头" required>
          <a-input v-model:value="form.title" placeholder="企业全称或个人姓名" :maxlength="200" />
        </a-form-item>
        <a-form-item
          v-if="form.buyer_type === 'enterprise' || form.invoice_type === 'vat_special'"
          label="纳税人识别号 / 统一社会信用代码"
          :required="form.invoice_type === 'vat_special'"
        >
          <a-input v-model:value="form.tax_id" placeholder="18位统一社会信用代码" :maxlength="20" />
        </a-form-item>
        <template v-if="form.invoice_type === 'vat_special'">
          <a-form-item label="注册地址" required>
            <a-input v-model:value="form.company_address" :maxlength="300" />
          </a-form-item>
          <a-form-item label="注册电话" required>
            <a-input v-model:value="form.company_phone" :maxlength="50" />
          </a-form-item>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="开户银行" required>
                <a-input v-model:value="form.bank_name" :maxlength="200" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="银行账号" required>
                <a-input v-model:value="form.bank_account" :maxlength="64" />
              </a-form-item>
            </a-col>
          </a-row>
        </template>
        <a-form-item label="收票邮箱" required>
          <a-input v-model:value="form.recipient_email" type="email" :maxlength="200" />
        </a-form-item>
        <a-form-item label="备注（选填）">
          <a-textarea v-model:value="form.customer_note" :rows="2" :maxlength="500" />
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model:checked="form.disclaimer_ack">
            我已阅读并理解：本提交为开票申请，不代表已开具增值税发票；销售方为平台运营主体。
          </a-checkbox>
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model:checked="form.save_profile">保存为常用开票信息</a-checkbox>
        </a-form-item>
        <a-button
          type="primary"
          html-type="submit"
          :loading="submitting"
          :disabled="!meta.platform_ready"
        >
          提交申请
        </a-button>
      </a-form>
    </a-card>

    <a-card title="我的申请记录" size="small">
      <a-table
        :columns="columns"
        :data-source="applications"
        :loading="loading"
        row-key="id"
        size="small"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'amount'">
            ¥{{ (record.amount_cents / 100).toFixed(2) }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button type="link" size="small" @click="downloadReceipt(record.id)">下载回执</a-button>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import api from '@/api';
import { getAuthToken } from '@/utils/api'

type Meta = {
  disclaimer: string
  platform_ready: boolean
  seller_name?: string
}

type OrderRow = {
  id: string
  order_no: string
  amount_cents: number
  subject: string
  invoice_applied: boolean
}

type AppRow = {
  id: string
  order_no: string
  amount_cents: number
  invoice_type: string
  title: string
  status: string
  reject_reason?: string
  invoice_code?: string
  invoice_number?: string
  created_at: string
}

const meta = ref<Meta>({ disclaimer: '', platform_ready: false })
const eligibleOrders = ref<OrderRow[]>([])
const applications = ref<AppRow[]>([])
const loading = ref(false)
const submitting = ref(false)

const form = reactive({
  payment_order_id: undefined as string | undefined,
  buyer_type: 'enterprise',
  invoice_type: 'vat_general',
  title: '',
  tax_id: '',
  company_address: '',
  company_phone: '',
  bank_name: '',
  bank_account: '',
  recipient_email: '',
  customer_note: '',
  disclaimer_ack: false,
  save_profile: true,
})

const buyerTypeOptions = [
  { value: 'enterprise', label: '企业' },
  { value: 'individual', label: '个人' },
]
const invoiceTypeOptions = [
  { value: 'vat_general', label: '增值税普通发票' },
  { value: 'vat_special', label: '增值税专用发票' },
]

const orderOptions = computed(() =>
  eligibleOrders.value
    .filter((o) => !o.invoice_applied)
    .map((o) => ({
      value: o.id,
      label: `${o.order_no} · ¥${(o.amount_cents / 100).toFixed(2)} · ${o.subject || ''}`,
    }))
)

const columns = [
  { title: '订单号', dataIndex: 'order_no', key: 'order_no', ellipsis: true },
  { title: '抬头', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '金额', key: 'amount' },
  { title: '状态', key: 'status' },
  { title: '申请时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'actions', width: 100 },
]

function statusLabel(s: string) {
  const map: Record<string, string> = {
    pending_review: '待审核',
    approved: '已通过',
    rejected: '已驳回',
    issuing: '开具中',
    issued: '已开票',
    cancelled: '已取消',
  }
  return map[s] || s
}

function statusColor(s: string) {
  if (s === 'issued') return 'green'
  if (s === 'rejected') return 'red'
  if (s === 'pending_review') return 'orange'
  return 'blue'
}

async function loadMeta() {
  const res = (await api.get('/client/invoice-applications/meta')) as unknown
  meta.value = res as Meta
}

async function loadOrders() {
  const res = (await api.get('/client/invoice-applications/eligible-orders')) as OrderRow[]
  eligibleOrders.value = Array.isArray(res) ? res : []
}

async function loadApplications() {
  loading.value = true
  try {
    const res = (await api.get('/client/invoice-applications')) as { items?: AppRow[] }
    applications.value = res?.items ?? (Array.isArray(res) ? (res as unknown as AppRow[]) : [])
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!form.disclaimer_ack) {
    message.warning('请确认免责声明')
    return
  }
  submitting.value = true
  try {
    await api.post('/client/invoice-applications', { ...form })
    message.success('开票申请已提交')
    form.payment_order_id = undefined
    form.disclaimer_ack = false
    await Promise.all([loadOrders(), loadApplications()])
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.error(err.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

async function downloadReceipt(id: string) {
  const tk = getAuthToken()
  const res = await fetch(`/api/v1/client/invoice-applications/${id}/receipt.pdf`, {
    headers: { Authorization: `Bearer ${tk}` },
  })
  if (!res.ok) {
    message.error('下载失败')
    return
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `invoice-application-${id.slice(0, 8)}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  await loadMeta()
  await Promise.all([loadOrders(), loadApplications()])
})
</script>
