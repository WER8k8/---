<template>
  <YdPage title="计费结算" subtitle="套餐选购 / 账单管理 / 支付记录" surface="elevated">
    <template #actions>
      <a-space>
        <!-- 租户选择器 -->
        <a-select
          v-model:value="selectedTenantId"
          placeholder="选择租户"
          style="width: 200px"
          show-search
          :filter-option="filterTenantOption"
          @change="(v) => onTenantChange(v as string)"
        >
          <a-select-option v-for="t in tenantList" :key="t.id" :value="t.id">
            {{ t.name }} ({{ t.domain || '无域名' }})
          </a-select-option>
        </a-select>
        <a-button type="primary" @click="genBill" :disabled="!selectedTenantId">生成月度账单</a-button>
        <a-button @click="exportBills" :disabled="!selectedTenantId">导出账单</a-button>
      </a-space>
    </template>

    <a-alert
      v-if="!selectedTenantId && tenantList.length > 0"
      type="info"
      show-icon
      class="mb-4"
      message="请先从右上角选择要管理的租户"
    />
    <a-alert
      v-if="plansLoadError"
      type="warning"
      show-icon
      class="mb-4"
      :message="plansLoadError"
      closable
      @close="plansLoadError = ''"
    />

    <!-- ================================================================ -->
    <!-- 统计卡片 -->
    <!-- ================================================================ -->
    <div class="stats-row">
      <a-card size="small"><a-statistic title="本月实收" :value="formatYuan(monthlyIncome)" prefix="¥" /></a-card>
      <a-card size="small"><a-statistic title="待付款" :value="formatYuan(pendingAmount)" prefix="¥" :value-style="{ color: '#f59e0b' }" /></a-card>
      <a-card size="small"><a-statistic title="已收款" :value="formatYuan(paidAmount)" prefix="¥" :value-style="{ color: '#22c55e' }" /></a-card>
    </div>

    <!-- ================================================================ -->
    <!-- 套餐选购区域 -->
    <!-- ================================================================ -->
    <a-card title="套餐选购 / 续费" class="plan-section">
      <template #extra>
        <a-radio-group v-model:value="billingCycle" button-style="solid" size="small">
          <a-radio-button value="monthly">月付</a-radio-button>
          <a-radio-button value="yearly">年付 <span style="color:#22c55e;font-weight:600">省 2 个月</span></a-radio-button>
        </a-radio-group>
      </template>

      <div v-if="plansLoading" style="text-align:center;padding:32px">
        <a-spin />
      </div>

      <div v-else class="plan-grid">
        <div
          v-for="plan in plans"
          :key="plan.id"
          class="plan-card"
          :class="{ 'plan-active': selectedPlanId === plan.id }"
          @click="selectedPlanId = plan.id"
        >
          <div class="plan-name">{{ plan.name }}</div>
          <div class="plan-price">
            <span class="price-symbol">¥</span>
            <span class="price-value">{{ displayPrice(plan) }}</span>
            <span class="price-unit">/{{ billingCycle === 'monthly' ? '月' : '年' }}</span>
          </div>
          <div v-if="billingCycle === 'yearly' && plan.price_yearly > 0" class="plan-saving">
            比月付省 ¥{{ Math.round(plan.price_monthly * 12 - plan.price_yearly) / 100 }}
          </div>
          <ul class="plan-features">
            <li v-for="f in featureList(plan)" :key="f">{{ f }}</li>
          </ul>
          <div class="plan-footer">
            <div class="plan-quota">用户 {{ plan.max_users }} 人 · 站点 {{ plan.max_sites }} 个</div>
            <a-button
              type="primary"
              :disabled="!selectedTenantId"
              @click.stop="handlePay(plan)"
            >
              立即支付
            </a-button>
          </div>
        </div>
      </div>
    </a-card>

    <!-- ================================================================ -->
    <!-- 账单表格 -->
    <!-- ================================================================ -->
    <a-card size="small" title="账单记录" style="margin-top:16px">
      <template #extra>
        <a-radio-group v-model:value="statusFilter" button-style="solid" size="small">
          <a-radio-button value="">全部</a-radio-button>
          <a-radio-button value="paid">已付</a-radio-button>
          <a-radio-button value="unpaid">待付</a-radio-button>
          <a-radio-button value="overdue">逾期</a-radio-button>
        </a-radio-group>
      </template>

      <a-table :columns="cols" :data-source="filteredBills" row-key="id" size="small"
        :pagination="{ pageSize: 20, showSizeChanger: true, showTotal: (t:number) => `共 ${t} 条` }">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status==='paid'?'green':record.status==='overdue'?'red':'orange'">
              {{ record.status==='paid'?'已付':record.status==='overdue'?'逾期':'待付' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button size="small" type="primary" ghost :disabled="record.status==='paid'" @click="markPaid(record as Bill)">标记已付</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- ================================================================ -->
    <!-- 支付二维码弹窗 -->
    <!-- ================================================================ -->
    <a-modal
      v-model:open="qrVisible"
      title="微信扫码支付"
      :footer="null"
      width="380px"
      :centered="true"
    >
      <div style="text-align:center;padding:16px 0">
        <div v-if="paying" style="padding:40px 0">
          <a-spin tip="正在生成支付二维码..." />
        </div>
        <template v-else>
          <!-- 真实二维码 -->
          <div v-if="currentCodeUrl && !currentMock" style="margin-bottom:12px">
            <img
              :src="`https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(currentCodeUrl)}`"
              alt="支付二维码"
              style="width:250px;height:250px;margin:0 auto;display:block"
            />
          </div>
          <!-- 占位二维码（mock 模式） -->
          <div v-else-if="currentMock" style="margin-bottom:12px">
            <div style="width:250px;height:250px;margin:0 auto;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#f0f5ff;border:2px dashed #1890ff;border-radius:12px;color:#1890ff">
              <div style="font-size:64px;line-height:1">&#128179;</div>
              <div style="font-size:16px;font-weight:600;margin-top:8px">模拟支付</div>
              <div style="font-size:12px;margin-top:4px">(占位环境 · 无需真实扫码)</div>
            </div>
          </div>
          <div v-else style="padding:40px 0;color:#999">二维码加载失败</div>

          <div style="margin-top:12px">
            <div style="font-size:16px;font-weight:600">{{ currentSubject }}</div>
            <div style="font-size:14px;color:#666;margin-top:4px">
              ¥{{ currentAmount ? (currentAmount / 100).toFixed(2) : '0.00' }}
            </div>
            <div style="font-size:12px;color:#999;margin-top:4px">
              订单号: {{ currentOrderNo }}
            </div>
          </div>

          <!-- 占位环境：模拟支付按钮 -->
          <div v-if="currentMock && currentOrderId" style="margin-top:20px;border-top:1px solid #eee;padding-top:16px">
            <a-button type="primary" size="large" block @click="mockPayOrder" :loading="mockPaying">
              模拟支付成功（演示用）
            </a-button>
          </div>

          <div style="margin-top:12px;color:#999;font-size:12px">
            打开微信「扫一扫」扫码支付
          </div>
        </template>
      </div>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet, apiPost, apiPut } from '@/utils/api'

// ============================================================================
// 状态
// ============================================================================
const statusFilter = ref('')
const loading = ref(false)

// 套餐
const plans = ref<any[]>([])
const plansLoading = ref(false)
const plansLoadError = ref('')
const selectedPlanId = ref('')
const billingCycle = ref<'monthly' | 'yearly'>('monthly')

// 支付二维码弹窗
const qrVisible = ref(false)
const paying = ref(false)
const currentCodeUrl = ref('')
const currentMock = ref(false)
const currentOrderId = ref('')
const currentOrderNo = ref('')
const currentSubject = ref('')
const currentAmount = ref(0)
const mockPaying = ref(false)

// ============================================================================
// 租户选择器
// ============================================================================
interface TenantOption {
  id: string
  name: string
  domain: string
  status: string
}

const tenantList = ref<TenantOption[]>([])
const selectedTenantId = ref('')
const selectedTenantName = ref('')

async function loadTenantList() {
  try {
    const data = await apiGet<{ items?: TenantOption[]; recent_tenants?: TenantOption[] }>('/tenants/', {
      page: 1,
      page_size: 100,
    })
    const items = data?.items || data?.recent_tenants || []
    tenantList.value = items.map((t: any) => ({
      id: String(t.id ?? ''),
      name: String(t.name ?? ''),
      domain: String(t.domain ?? ''),
      status: String(t.status ?? ''),
    }))
  } catch {
    tenantList.value = []
  }
}

function filterTenantOption(input: string, option: any) {
  const text = option.children?.()?.toString()?.toLowerCase() || ''
  return text.toLowerCase().includes(input.toLowerCase())
}

async function onTenantChange(tenantId: string) {
  const tenant = tenantList.value.find((t) => t.id === tenantId)
  selectedTenantName.value = tenant?.name || ''
  selectedTenantId.value = tenantId
  // 切换租户后刷新账单
  await loadBills()
}

// ============================================================================
// 账单数据
// ============================================================================
interface Bill {
  id: string
  tenant: string
  amount: number
  period: string
  status: string
  date: string
}

const bills = ref<Bill[]>([])

const filteredBills = computed(() => {
  if (!statusFilter.value) return bills.value
  return bills.value.filter(b => b.status === statusFilter.value)
})

const monthlyIncome = computed(() => {
  const m = new Date().toISOString().slice(0, 7)
  return bills.value
    .filter(b => b.period === m && b.status === 'paid')
    .reduce((s, b) => s + b.amount, 0)
})
const paidAmount = computed(() => bills.value.filter(b => b.status === 'paid').reduce((s, b) => s + b.amount, 0))
const pendingAmount = computed(() => bills.value.filter(b => b.status === 'unpaid' || b.status === 'overdue').reduce((s, b) => s + b.amount, 0))

const cols = [
  { title: '账单编号', dataIndex: 'id', width: 140 },
  { title: '租户名称', dataIndex: 'tenant', width: 140 },
  { title: '金额(元)', dataIndex: 'amount', width: 100, customRender: ({ text }: { text: number }) => formatYuan(text) },
  { title: '周期', dataIndex: 'period', width: 100 },
  { title: '状态', key: 'status', width: 90 },
  { title: '生成日期', dataIndex: 'date', width: 110 },
  { title: '操作', key: 'actions', width: 100 },
]

// ============================================================================
// 套餐辅助
// ============================================================================
const FEATURE_LABELS: Record<string, string> = {
  seo: 'SEO 优化',
  analytics: '数据分析',
  globalization: '多语言',
  international: '国际询盘',
  content: '内容管理',
  ai: 'AI 写作',
  white_label: '品牌定制',
  api: 'API 接口',
}

function featureList(plan: any): string[] {
  try {
    const raw = typeof plan.features === 'string' ? JSON.parse(plan.features) : plan.features
    return (raw as string[]).map((k: string) => FEATURE_LABELS[k] || k)
  } catch {
    return []
  }
}

function displayPrice(plan: any): string {
  const amount = billingCycle.value === 'yearly' ? plan.price_yearly : plan.price_monthly
  return (amount / 100).toFixed(2)
}

// ============================================================================
// 加载套餐
// ============================================================================
async function loadPlans() {
  plansLoading.value = true
  plansLoadError.value = ''
  try {
    const data = await apiGet('/payment/plans')
    plans.value = data || []
    if (plans.value.length > 0) {
      selectedPlanId.value = plans.value[0].id
    }
  } catch (e: unknown) {
    if (import.meta.env.DEV) console.error(e)
    plansLoadError.value = e instanceof Error ? e.message : '加载套餐失败'
  } finally {
    plansLoading.value = false
  }
}

// ============================================================================
// 支付流程
// ============================================================================
async function handlePay(plan: any) {
  if (!selectedTenantId.value) {
    message.warning('请先选择租户')
    return
  }

  paying.value = true
  qrVisible.value = true
  currentCodeUrl.value = ''
  currentMock.value = false
  currentOrderId.value = ''
  currentOrderNo.value = ''
  currentSubject.value = `${plan.name} - ${billingCycle.value === 'monthly' ? '月付' : '年付'}`
  currentAmount.value = billingCycle.value === 'yearly' ? plan.price_yearly : plan.price_monthly

  try {
    const data = await apiPost('/payment/create-native', {
      tenant_id: selectedTenantId.value,
      plan_id: plan.id,
      billing_cycle: billingCycle.value,
    })
    currentCodeUrl.value = data.code_url || ''
    currentMock.value = data.mock || false
    currentOrderId.value = data.id || ''
    currentOrderNo.value = data.order_no || ''
    currentAmount.value = data.amount || currentAmount.value
    currentSubject.value = data.subject || currentSubject.value
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '创建支付订单失败')
    qrVisible.value = false
  } finally {
    paying.value = false
  }
}

async function mockPayOrder() {
  // 安全检查：仅允许在开发环境使用模拟支付
  if (!import.meta.env.DEV) {
    message.error('模拟支付仅在开发环境可用');
    return;
  }
  if (!currentOrderId.value) return;
  mockPaying.value = true;
  try {
    const data = await apiPost('/payment/mock-pay', {
      order_id: currentOrderId.value,
    });
    message.success(`订单 ${data.order_no} 支付成功！`);
    qrVisible.value = false;
    // 刷新账单
    await loadBills();
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '模拟支付失败');
  } finally {
    mockPaying.value = false;
  }
}

// ============================================================================
// 账单操作
// ============================================================================
async function loadBills() {
  if (!selectedTenantId.value) {
    bills.value = []
    return
  }
  loading.value = true
  try {
    const params: Record<string, string | number> = { page: 1, page_size: 100, tenant_id: selectedTenantId.value }
    const data = await apiGet<{ items: Array<{ id: string; tenant?: string; amount: number; period?: string; status: string; created_at?: string }> }>('/tenants/invoices', params)
    const items = data?.items || []
    bills.value = items.map((inv) => ({
      id: inv.id,
      tenant: inv.tenant || selectedTenantName.value || '--',
      amount: inv.amount || 0,
      period: inv.period || '--',
      status: inv.status,
      date: inv.created_at ? new Date(inv.created_at).toISOString().slice(0, 10) : '--',
    }))
  } catch (e: unknown) {
    if (import.meta.env.DEV) console.error(e)
  } finally { loading.value = false }
}

async function genBill() {
  if (!selectedTenantId.value) {
    message.warning('请先从右上角选择租户')
    return
  }
  const period = new Date().toISOString().slice(0, 7)
  try {
    const payload: Record<string, string> = { period, tenant_id: selectedTenantId.value }
    await apiPost('/tenants/invoices/generate', payload)
    message.success(`已生成 ${period} 月度账单`)
    await loadBills()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '生成失败')
  }
}

async function markPaid(record: Bill) {
  if (!selectedTenantId.value) {
    message.warning('请先指定租户')
    return
  }
  try {
    const payload: Record<string, string> = { status: 'paid', tenant_id: selectedTenantId.value }
    await apiPut(`/tenants/invoices/${record.id}`, payload)
    message.success(`账单 ${record.id.slice(0, 8)} 已标记为已付`)
    await loadBills()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '操作失败')
  }
}

function exportBills() {
  const csv = ['账单编号,租户名称,金额,周期,状态,生成日期']
  bills.value.forEach(b => csv.push(`${b.id},${b.tenant},${b.amount},${b.period},${b.status},${b.date}`))
  const blob = new Blob(['\uFEFF' + csv.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `账单导出_${new Date().toISOString().slice(0, 10)}.csv`
  a.click(); URL.revokeObjectURL(url)
  message.success('账单已导出')
}

// ============================================================================
// 工具函数
// ============================================================================
/** 分转元，保留2位小数 */
function formatYuan(fen: number): string {
  return (fen / 100).toFixed(2)
}

// ============================================================================
// 初始化
// ============================================================================
onMounted(async () => {
  await loadTenantList()
  loadPlans()
  // 优先从 URL 参数读取租户 ID
  const params = new URLSearchParams(window.location.search)
  const tid = params.get('tenant_id')
  if (tid) {
    selectedTenantId.value = tid
    await loadBills()
  }
})
</script>

<style scoped>
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }

/* 套餐选购网格 */
.plan-section { margin-top: 16px; }
.plan-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.plan-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
}
.plan-card:hover { border-color: #1890ff; box-shadow: 0 2px 8px rgba(24,144,255,0.12); }
.plan-active { border-color: #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.25); }
.plan-name { font-size: 18px; font-weight: 700; color: #1f2937; }
.plan-price { margin: 10px 0 4px; display: flex; align-items: baseline; gap: 2px; }
.price-symbol { font-size: 16px; color: #f59e0b; font-weight: 600; }
.price-value { font-size: 28px; font-weight: 700; color: #f59e0b; line-height: 1; }
.price-unit { font-size: 13px; color: #9ca3af; }
.plan-saving { font-size: 12px; color: #22c55e; font-weight: 500; margin-bottom: 8px; }
.plan-features { list-style: none; padding: 0; margin: 10px 0; flex: 1; }
.plan-features li { font-size: 13px; color: #6b7280; padding: 3px 0; }
.plan-features li::before { content: ''; display: inline-block; width: 6px; height: 6px; margin-right: 8px; border-radius: 50%; background: #22c55e; vertical-align: middle; }
.plan-footer { display: flex; flex-direction: column; gap: 10px; }
.plan-quota { font-size: 12px; color: #9ca3af; }
</style>
