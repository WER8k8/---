<template>
  <YdPage title="开票审核" subtitle="审核租户开票申请，线下/税控开具后登记发票号码" surface="elevated">
    <template #actions>
      <YdTableToolbar
        :loading="loading"
        :target-ref="tablePanelRef"
        show-export
        @refresh="load"
        @export="exportCsv"
      />
      <a-button type="primary" @click="configOpen = true">平台开票主体</a-button>
    </template>

    <YdFinanceNav />

    <a-alert
      class="mb-4"
      type="info"
      show-icon
      message="合规说明"
      description="审核通过仅代表业务同意开票；须在税控/全电票系统实际开具后，再标记「已开票」并填写发票代码与号码。销售方为平台主体，与代理分润无关。"
    />

    <a-tabs v-model:activeKey="statusFilter" @change="load">
      <a-tab-pane key="" tab="全部" />
      <a-tab-pane key="pending_review" tab="待审核" />
      <a-tab-pane key="approved" tab="已通过" />
      <a-tab-pane key="issued" tab="已开票" />
      <a-tab-pane key="rejected" tab="已驳回" />
    </a-tabs>

    <div ref="tablePanelRef" class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="{ current: 1, pageSize: 20, total }"
        :table-props="{ rowKey: 'id' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'amount'">
            ¥{{ (record.amount_cents / 100).toFixed(2) }}
          </template>
          <template v-else-if="column.key === 'invoice_type'">
            {{ record.invoice_type === 'vat_special' ? '专票' : '普票' }}
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag>{{ statusLabel(record.status) }}</a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button
                v-if="record.status === 'pending_review'"
                type="link"
                size="small"
                @click="openReview(record, 'approve')"
              >
                通过
              </a-button>
              <a-button
                v-if="record.status === 'pending_review'"
                type="link"
                danger
                size="small"
                @click="openReview(record, 'reject')"
              >
                驳回
              </a-button>
              <a-button
                v-if="record.status === 'approved'"
                type="link"
                size="small"
                @click="issueViaProvider(record)"
              >
                电子开票
              </a-button>
              <a-button
                v-if="record.status === 'approved'"
                type="link"
                size="small"
                @click="openIssue(record)"
              >
                手工登记
              </a-button>
            </a-space>
          </template>
        </template>
      </YdDataTable>
    </div>

    <a-modal
      v-model:open="reviewOpen"
      :title="reviewAction === 'approve' ? '审核通过' : '驳回申请'"
      @ok="submitReview"
      :confirm-loading="reviewLoading"
    >
      <p v-if="reviewAction === 'approve'">确认通过该开票申请？通过后请在税控系统开具发票。</p>
      <a-form v-else layout="vertical">
        <a-form-item label="驳回原因" required>
          <a-textarea v-model:value="rejectReason" :rows="3" :maxlength="500" />
        </a-form-item>
      </a-form>
      <a-form-item v-if="reviewAction === 'approve'" label="内部备注">
        <a-textarea v-model:value="adminNote" :rows="2" :maxlength="500" />
      </a-form-item>
    </a-modal>

    <a-modal
      v-model:open="issueOpen"
      title="登记已开票信息"
      @ok="submitIssue"
      :confirm-loading="issueLoading"
    >
      <a-form layout="vertical">
        <a-form-item label="发票代码" required>
          <a-input v-model:value="issueForm.invoice_code" :maxlength="32" />
        </a-form-item>
        <a-form-item label="发票号码" required>
          <a-input v-model:value="issueForm.invoice_number" :maxlength="32" />
        </a-form-item>
        <a-form-item label="交付说明（如邮箱已发送）">
          <a-input v-model:value="issueForm.invoice_file_note" :maxlength="500" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="configOpen"
      title="平台开票主体（销售方）"
      width="640px"
      @ok="saveConfig"
      :confirm-loading="configLoading"
    >
      <a-alert
        class="mb-3"
        type="warning"
        show-icon
        message="须完成公司注册及全电票资质后方可对外开票；此处为系统内销售方信息配置。"
      />
      <a-form layout="vertical">
        <a-form-item label="销售方名称" required>
          <a-input v-model:value="configForm.seller_name" :maxlength="200" />
        </a-form-item>
        <a-form-item label="统一社会信用代码 / 税号" required>
          <a-input v-model:value="configForm.seller_tax_id" :maxlength="20" />
        </a-form-item>
        <a-form-item label="地址">
          <a-input v-model:value="configForm.seller_address" :maxlength="300" />
        </a-form-item>
        <a-form-item label="电话">
          <a-input v-model:value="configForm.seller_phone" :maxlength="50" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="开户银行">
              <a-input v-model:value="configForm.seller_bank_name" :maxlength="200" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="银行账号">
              <a-input v-model:value="configForm.seller_bank_account" :maxlength="64" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="商品/服务类目">
          <a-input v-model:value="configForm.service_category" placeholder="如：信息技术服务*软件服务费" />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

import { YdDataTable, YdFinanceNav, YdPage, YdTableToolbar } from '@/components/youding'
import api from '@/api'
import { downloadTableCsv } from '@/utils/exportCsv'

type Row = {
  id: string
  tenant_id: string
  order_no: string
  amount_cents: number
  title: string
  tax_id?: string
  invoice_type: string
  recipient_email: string
  status: string
  created_at: string
}

const tablePanelRef = ref<HTMLElement | null>(null)
const loading = ref(false)
const items = ref<Row[]>([])
const total = ref(0)
const statusFilter = ref('')

const reviewOpen = ref(false)
const reviewLoading = ref(false)
const reviewAction = ref<'approve' | 'reject'>('approve')
const rejectReason = ref('')
const adminNote = ref('')
const currentRow = ref<Row | null>(null)

const issueOpen = ref(false)
const issueLoading = ref(false)
const issueForm = reactive({
  invoice_code: '',
  invoice_number: '',
  invoice_file_note: '',
})

const configOpen = ref(false)
const configLoading = ref(false)
const configForm = reactive({
  seller_name: '',
  seller_tax_id: '',
  seller_address: '',
  seller_phone: '',
  seller_bank_name: '',
  seller_bank_account: '',
  service_category: '信息技术服务*软件服务费',
})

const columns = [
  { title: '租户', dataIndex: 'tenant_id', key: 'tenant_id', ellipsis: true, width: 120 },
  { title: '订单号', dataIndex: 'order_no', key: 'order_no', ellipsis: true },
  { title: '抬头', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '类型', key: 'invoice_type', width: 70 },
  { title: '金额', key: 'amount', width: 100 },
  { title: '邮箱', dataIndex: 'recipient_email', key: 'recipient_email', ellipsis: true },
  { title: '状态', key: 'status', width: 90 },
  { title: '申请时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'actions', width: 240 },
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

async function load() {
  loading.value = true
  try {
    const params = statusFilter.value ? { status: statusFilter.value } : {}
    const res = (await api.get('/finance/invoice-applications', { params })) as {
      items?: Row[]
      total?: number
    }
    items.value = res?.items ?? []
    total.value = res?.total ?? items.value.length
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  downloadTableCsv(
    'invoice-applications.csv',
    ['租户', '订单号', '抬头', '类型', '金额', '邮箱', '状态', '申请时间'],
    items.value.map((r) => [
      r.tenant_id,
      r.order_no,
      r.title,
      r.invoice_type === 'vat_special' ? '专票' : '普票',
      (r.amount_cents / 100).toFixed(2),
      r.recipient_email,
      statusLabel(r.status),
      r.created_at,
    ]),
  )
}

async function loadConfig() {
  const res = (await api.get('/finance/invoice-applications/platform-config')) as Record<string, unknown>
  if (res?.configured) {
    Object.assign(configForm, {
      seller_name: res.seller_name || '',
      seller_tax_id: res.seller_tax_id || '',
      seller_address: res.seller_address || '',
      seller_phone: res.seller_phone || '',
      seller_bank_name: res.seller_bank_name || '',
      seller_bank_account: res.seller_bank_account || '',
      service_category: res.service_category || configForm.service_category,
    })
  }
}

function openReview(row: Record<string, unknown>, action: 'approve' | 'reject') {
  currentRow.value = row as Row
  reviewAction.value = action
  rejectReason.value = ''
  adminNote.value = ''
  reviewOpen.value = true
}

async function submitReview() {
  if (!currentRow.value) return
  reviewLoading.value = true
  try {
    await api.post(`/finance/invoice-applications/${currentRow.value.id}/review`, {
      action: reviewAction.value,
      reject_reason: reviewAction.value === 'reject' ? rejectReason.value : undefined,
      admin_note: adminNote.value || undefined,
    })
    message.success('审核完成')
    reviewOpen.value = false
    await load()
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.error(err.message || '操作失败')
  } finally {
    reviewLoading.value = false
  }
}

function openIssue(row: Record<string, unknown>) {
  currentRow.value = row as Row
  issueForm.invoice_code = ''
  issueForm.invoice_number = ''
  issueForm.invoice_file_note = ''
  issueOpen.value = true
}

async function issueViaProvider(row: Record<string, unknown>) {
  const id = String(row.id ?? '')
  if (!id) return
  try {
    const res = (await api.post(
      `/finance/invoice-applications/${id}/issue-via-provider`,
    )) as { provider_result?: { message?: string } }
    message.success(res?.provider_result?.message || '电子开票已处理')
    await load()
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.error(err.message || '电子开票失败')
  }
}

async function submitIssue() {
  if (!currentRow.value) return
  issueLoading.value = true
  try {
    await api.post(`/finance/invoice-applications/${currentRow.value.id}/mark-issued`, {
      ...issueForm,
    })
    message.success('已登记开票信息')
    issueOpen.value = false
    await load()
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.error(err.message || '操作失败')
  } finally {
    issueLoading.value = false
  }
}

async function saveConfig() {
  configLoading.value = true
  try {
    await api.put('/finance/invoice-applications/platform-config', { ...configForm })
    message.success('平台开票主体已保存')
    configOpen.value = false
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.error(err.message || '保存失败')
  } finally {
    configLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([load(), loadConfig()])
})
</script>
