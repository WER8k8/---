<template>
  <YdPage title="客户开户" subtitle="提交开户并生成收款二维码" surface="elevated">
  <div class="agent-account-opening coachpro-tertiary coachpro-tertiary--agent">

    <div class="coachpro-panel p-6 mb-4">

      <h3 class="text-lg font-semibold text-gray-900 mb-2">提交开户并收款</h3>

      <p class="text-sm text-gray-500 mb-6">开户成功后可在本页生成微信/支付宝收款二维码，客户扫码付款后自动开通并多级分润。</p>

      <a-form :model="form" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }" @finish="handleSubmit">

        <a-form-item label="客户公司名称" name="companyName" :rules="[{ required: true, message: '请输入公司名称' }]">

          <a-input v-model:value="form.companyName" placeholder="请输入客户公司全称" />

        </a-form-item>

        <a-form-item label="联系人姓名" name="contactName" :rules="[{ required: true, message: '请输入联系人姓名' }]">

          <a-input v-model:value="form.contactName" placeholder="请输入联系人姓名" />

        </a-form-item>

        <a-form-item label="联系电话" name="phone" :rules="[{ required: true, message: '请输入联系电话' }]">

          <a-input v-model:value="form.phone" placeholder="请输入联系电话" />

        </a-form-item>

        <a-form-item label="联系邮箱" name="email">

          <a-input v-model:value="form.email" placeholder="请输入联系邮箱（选填）" />

        </a-form-item>

        <a-form-item label="选择套餐" name="package" :rules="[{ required: true, message: '请选择套餐' }]">

          <a-select v-model:value="form.package" placeholder="请选择客户套餐" style="width: 100%">

            <a-select-option v-for="pkg in packages" :key="pkg.value" :value="pkg.value">

              {{ pkg.label }} — ¥{{ pkg.price }}/年

            </a-select-option>

          </a-select>

        </a-form-item>

        <a-form-item label="计费周期">

          <a-radio-group v-model:value="billingCycle" button-style="solid">

            <a-radio-button value="yearly">年付</a-radio-button>

            <a-radio-button value="monthly">月付</a-radio-button>

          </a-radio-group>

        </a-form-item>

        <a-form-item label="备注" name="remark">

          <a-textarea v-model:value="form.remark" placeholder="备注信息（选填）" :rows="3" />

        </a-form-item>

        <a-form-item :wrapper-col="{ offset: 4, span: 16 }">

          <a-space>

            <a-button type="primary" html-type="submit" :loading="submitting">提交开户</a-button>

            <a-button :disabled="!lastTenantId" @click="openCollectQr(lastTenantId)">生成收款码</a-button>

          </a-space>

        </a-form-item>

      </a-form>

    </div>



    <div class="coachpro-panel p-6">

      <h3 class="text-lg font-semibold text-gray-900 mb-4">开户记录</h3>

      <a-table :data-source="records" :columns="columns" :pagination="{ pageSize: 8 }" size="small" row-key="id">

        <template #bodyCell="{ column, record }">

          <template v-if="column.key === 'status'">

            <a-tag :color="statusTagColor(record.status)">{{ record.status }}</a-tag>

          </template>

          <template v-if="column.key === 'action'">

            <a-button type="link" size="small" :disabled="!record.tenantId" @click="openCollectQr(record.tenantId, record.package)">

              收款二维码

            </a-button>

          </template>

        </template>

      </a-table>

    </div>



    <a-modal v-model:open="qrVisible" title="客户扫码支付" :footer="null" width="400px" centered>

      <div class="text-center py-4">

        <a-spin v-if="paying" tip="正在生成支付二维码..." />

        <template v-else>

          <div v-if="currentCodeUrl && !currentMock" class="mb-3">

            <img

              :src="`https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(currentCodeUrl)}`"

              alt="支付二维码"

              class="mx-auto w-60 h-60"

            />

          </div>

          <div v-else-if="currentMock" class="mx-auto mb-3 w-60 h-60 flex flex-col items-center justify-center bg-blue-50 border-2 border-dashed border-blue-400 rounded-xl text-blue-600">

            <YdIllustration icon="CreditCardOutlined" size="lg" />

            <div class="font-semibold mt-2">演示环境 · 模拟支付</div>

          </div>

          <div class="font-semibold">{{ currentSubject }}</div>

          <div class="text-gray-500 mt-1">¥{{ formatYuan(currentAmount) }}</div>

          <div class="text-xs text-gray-400 mt-1">订单号 {{ currentOrderNo }}</div>

          <a-button v-if="currentMock && currentOrderId" type="primary" block class="mt-4" :loading="mockPaying" @click="mockPay">

            模拟支付成功（自动开通+分润）

          </a-button>

          <p class="text-xs text-gray-400 mt-3">请客户使用微信扫一扫；支付成功后自动开通服务并按代理链分润</p>

        </template>

      </div>

    </a-modal>

  </div>
  </YdPage>
</template>



<script setup lang="ts">

import { ref, reactive, onMounted } from 'vue'
import { YdIllustration, YdPage } from '@/components/youding'

import { message } from 'ant-design-vue'

import { apiGet, apiPost } from '@/utils/api'



interface PlanOption { value: string; label: string; price: string; planId?: string }

interface OpeningRecord {

  id: number | string

  applyTime: string

  clientName: string

  package: string

  status: string

  tenantId?: string

}



const packages = ref<PlanOption[]>([

  { value: 'basic', label: '基础版', price: '6,000' },

  { value: 'standard', label: '标准版', price: '12,000' },

  { value: 'pro', label: '高级版', price: '24,000' },

])

const billingCycle = ref<'monthly' | 'yearly'>('yearly')

const form = reactive({

  companyName: '',

  contactName: '',

  phone: '',

  email: '',

  package: undefined as string | undefined,

  remark: '',

})

const submitting = ref(false)

const lastTenantId = ref('')



const qrVisible = ref(false)

const paying = ref(false)

const mockPaying = ref(false)

const currentCodeUrl = ref('')

const currentMock = ref(false)

const currentOrderId = ref('')

const currentOrderNo = ref('')

const currentSubject = ref('')

const currentAmount = ref(0)



const records = ref<OpeningRecord[]>([])

const columns = [

  { title: '申请时间', dataIndex: 'applyTime', key: 'applyTime' },

  { title: '客户名称', dataIndex: 'clientName', key: 'clientName' },

  { title: '套餐', dataIndex: 'package', key: 'package' },

  { title: '状态', dataIndex: 'status', key: 'status' },

  { title: '操作', key: 'action' },

]



function formatYuan(cents: number) {

  return (cents / 100).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

}



async function loadPlans() {

  try {

    const data = await apiGet<Array<{ id: string; code: string; name: string; price_yearly: number }>>('/agent/plans')

    if (data?.length) {

      packages.value = data.map((p) => ({

        value: p.code,

        label: p.name,

        price: (p.price_yearly / 100).toLocaleString('zh-CN'),

        planId: p.id,

      }))

    }

  } catch { /* 保留默认 */ }

}



async function handleSubmit() {

  submitting.value = true

  try {

    const data = await apiPost<{ tenant_id: string; name: string; plan: string; package_code: string }>('/agent/account-opening', {

      company_name: form.companyName,

      contact_name: form.contactName,

      phone: form.phone,

      email: form.email || undefined,

      package: form.package,

      remark: form.remark || undefined,

    })

    const pkg = packages.value.find((p) => p.value === form.package)

    lastTenantId.value = data.tenant_id

    records.value.unshift({

      id: data.tenant_id,

      applyTime: new Date().toLocaleString('zh-CN'),

      clientName: data.name || form.companyName,

      package: pkg?.label || data.plan || '',

      status: '待收款',

      tenantId: data.tenant_id,

    })

    message.success('开户成功，请生成收款二维码')

    form.companyName = ''

    form.contactName = ''

    form.phone = ''

    form.email = ''

    form.package = undefined

    form.remark = ''

    await openCollectQr(data.tenant_id, pkg?.value || data.package_code)

  } catch {

    message.error('提交失败，请稍后重试')

  } finally {

    submitting.value = false

  }

}



async function openCollectQr(tenantId?: string, packageCode?: string) {

  if (!tenantId) return

  qrVisible.value = true

  paying.value = true

  currentCodeUrl.value = ''

  currentMock.value = false

  try {

    const data = await apiPost<{

      id: string

      order_no: string

      amount: number

      subject: string

      code_url: string

      mock: boolean

    }>('/agent/collect-payment', {

      tenant_id: tenantId,

      package: packageCode,

      billing_cycle: billingCycle.value,

      channel: 'wechat',

    })

    currentOrderId.value = data.id

    currentOrderNo.value = data.order_no

    currentSubject.value = data.subject

    currentAmount.value = data.amount

    currentCodeUrl.value = data.code_url || ''

    currentMock.value = !!data.mock

  } catch {

    message.error('生成收款码失败')

    qrVisible.value = false

  } finally {

    paying.value = false

  }

}



async function mockPay() {

  if (!currentOrderId.value) return

  mockPaying.value = true

  try {

    await apiPost('/payment/mock-pay', { order_id: currentOrderId.value })

    message.success('支付成功：已自动开通并按代理链分润')

    qrVisible.value = false

    const rec = records.value.find((r) => r.tenantId === lastTenantId.value)

    if (rec) rec.status = '已开通'

  } catch {

    message.error('模拟支付失败')

  } finally {

    mockPaying.value = false

  }

}



function statusTagColor(status: string) {

  const map: Record<string, string> = { 待收款: 'orange', 已开通: 'green', 已提交: 'blue' }

  return map[status] || 'default'

}



onMounted(loadPlans)

</script>



<style scoped>

.agent-account-opening { animation: pageIn 0.35s ease; }

@keyframes pageIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

</style>

