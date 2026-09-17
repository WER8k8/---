/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage
    title="AI 流量充值"
    subtitle="英伟达目前有免费额度可尝鲜（模型可用性不保证）；要想获得更好的体验，请充值"
    surface="elevated"
  >
    <template #actions>
      <a-button type="link" @click="router.push('/client/billing')">套餐续费 →</a-button>
    </template>
  <div class="client-tokens coachpro-tertiary coachpro-tertiary--client max-w-5xl mx-auto space-y-4 p-1">
    <a-row :gutter="[16, 16]">
      <a-col :xs="24" :sm="8">
        <a-card size="small">
          <a-statistic title="剩余 AI 流量" :value="tokenBalance" suffix="点" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="8">
        <a-card size="small">
          <a-statistic title="本月已用流量" :value="quotaUsed" suffix="点" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="8">
        <a-card size="small">
          <a-statistic title="当前选用平台" :value="currentProviderLabel || '未选择'" />
        </a-card>
      </a-col>
    </a-row>

    <a-alert
      v-if="isSuspended"
      type="warning"
      show-icon
      message="AI 流量不足，部分功能可能已暂停"
      description="请先选择大模型平台，再购买流量包；演示环境可点「模拟支付成功」立即到账。"
    />

    <a-alert
      v-if="showNvidiaFreeBanner"
      type="info"
      show-icon
      :message="aiConnectFreeTier ? aiConnectAlertTitle : nvidiaAlertTitle"
      :description="nvidiaBannerText"
    />

    <a-alert
      v-if="usagePolicyNotice && aiConnectFreeTier"
      type="warning"
      show-icon
      message="英伟达免费通道 · 客户须知"
    >
      <template #description>
        <p>{{ usagePolicyNotice }}</p>
        <p v-if="probeSummaryLine" class="text-xs text-gray-600 mt-2">{{ probeSummaryLine }}</p>
      </template>
    </a-alert>

    <a-alert
      v-else-if="aiConnectNotice && !aiConnectFreeTier"
      type="success"
      show-icon
      message="AI 通道已接通"
      :description="aiConnectNotice"
    />

    <a-card title="第 1 步：选择大模型平台（必选）">
      <p class="text-sm text-gray-500 mb-4">
        不同平台就像不同运营商。未充值时系统会尝试用英伟达免费通道（哪些模型能用以实时为准）；
        充值后自动接通您所选平台，体验更稳定。您也可在
        <a class="text-primary-600" @click.prevent="goScenarios">AI 场景模型</a>
        里为各场景指定具体模型。
      </p>
      <template v-if="loadingPacks">
        <SkeletonCard variant="kpi" />
      </template>
      <template v-else>
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <button
            v-for="p in providers"
            :key="p.provider_id"
            type="button"
            class="text-left rounded-xl border p-4 transition-all"
            :class="
              selectedProviderId === p.provider_id
                ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-100'
                : 'border-gray-200 hover:border-primary-300'
            "
            @click="selectProvider(p.provider_id)"
          >
            <div class="font-semibold text-gray-900">{{ p.label }}</div>
            <div class="text-xs text-gray-500 mt-1">{{ p.tagline }}</div>
            <p v-if="p.experience_hint" class="text-xs text-amber-700 mt-2 leading-snug">
              {{ p.experience_hint }}
            </p>
            <a-tag v-if="currentProviderId === p.provider_id" color="blue" class="mt-2">
              当前已选
            </a-tag>
          </button>
        </div>
      </template>
    </a-card>

    <a-card v-if="selectedProviderId" title="第 2 步：选流量包或自定义金额">
      <a-alert
        type="success"
        show-icon
        class="mb-4"
        :message="`已为「${selectedProviderLabel}」充值 AI 流量`"
        description="支付成功后流量立即到账，并记为您的主用大模型平台。"
      />
      <template v-if="loadingPacks">
        <SkeletonCard variant="card" />
      </template>
      <template v-else>
        <a-empty v-if="!packs.length" description="暂无可购买的流量包">
          <a-button type="primary" @click="reload">重新加载</a-button>
        </a-empty>
        <a-row v-else :gutter="[16, 16]">
          <a-col v-for="pack in packs" :key="pack.pack_id" :xs="24" :sm="8">
            <a-card hoverable class="h-full border-primary-100">
              <div class="text-lg font-semibold text-gray-900">
                {{ selectedProviderLabel }} · {{ displayPackLabel(pack) }}
              </div>
              <div class="text-3xl font-bold text-primary-600 my-3">¥{{ pack.price_yuan }}</div>
              <div class="text-sm text-gray-500 mb-4">
                到账 {{ pack.tokens.toLocaleString() }} 点 AI 流量
              </div>
              <a-button
                type="primary"
                size="large"
                block
                :loading="paying === pack.pack_id"
                :disabled="!selectedProviderId"
                @click="buyPack(pack)"
              >
                立即充值
              </a-button>
            </a-card>
          </a-col>
        </a-row>

        <a-divider v-if="customRecharge?.enabled">或自定义充值金额</a-divider>

        <a-card
          v-if="customRecharge?.enabled"
          class="border-dashed border-primary-200 bg-primary-50/30"
        >
          <p class="text-sm text-gray-600 mb-3">
            {{ customRecharge.rate_description || '按标准档位折算' }}，金额范围
            ¥{{ customRecharge.min_yuan }}～¥{{ customRecharge.max_yuan?.toLocaleString() }}
          </p>
          <div class="flex flex-col sm:flex-row sm:items-end gap-4">
            <div class="flex-1">
              <label class="text-xs text-gray-500 block mb-1">充值金额（元）</label>
              <a-input-number
                v-model:value="customAmountYuan"
                :min="customRecharge.min_yuan"
                :max="customRecharge.max_yuan"
                :precision="2"
                :step="10"
                class="w-full max-w-xs"
                addon-before="¥"
                @change="onCustomAmountChange"
              />
            </div>
            <div class="text-sm text-gray-700 pb-1">
              <a-spin v-if="quotingCustom" size="small" class="mr-2" />
              <template v-if="customQuoteTokens != null">
                预计到账 <strong class="text-primary-600">{{ customQuoteTokens.toLocaleString() }}</strong> 点 AI 流量
              </template>
              <span v-else class="text-gray-400">请输入有效金额查看预估</span>
            </div>
          </div>
          <a-button
            type="primary"
            size="large"
            class="mt-4"
            :loading="paying === 'custom'"
            :disabled="!selectedProviderId || customQuoteTokens == null"
            @click="buyCustom"
          >
            按自定义金额充值
          </a-button>
        </a-card>
      </template>
    </a-card>

    <a-card v-else title="第 2 步：选择流量包">
      <a-empty description="请先在上方选择一个大模型平台" />
    </a-card>

    <a-card title="流量消耗明细（公开透明）" class="mt-4">
      <p class="text-sm text-gray-500 mb-3">
        每次 AI 生成、优化、发布相关操作都会在此记一笔，扣多少、剩多少一目了然。
      </p>
      <a-table
        :columns="ledgerColumns"
        :data-source="ledgerRows"
        :loading="ledgerLoading"
        row-key="id"
        size="small"
        :pagination="{ pageSize: 10, total: ledgerTotal, onChange: onLedgerPage }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'delta'">
            <span :class="record.delta >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ record.delta >= 0 ? '+' : '' }}{{ record.delta }}
            </span>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="qrOpen" title="扫码支付 · AI 流量包" :footer="null" centered width="400px">
      <p class="text-sm text-gray-600 mb-1">{{ currentSubject }}</p>
      <p class="text-xs text-gray-400 mb-2">平台：{{ selectedProviderLabel }}</p>
      <p class="text-xl font-semibold text-center">¥{{ (currentAmount / 100).toFixed(2) }}</p>
      <div v-if="payingOrder" class="text-center py-8">
        <a-spin tip="正在创建订单..." />
      </div>
      <template v-else>
        <div v-if="currentCodeUrl && !currentMock" class="mt-3 text-center">
          <img
            :src="`https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(currentCodeUrl)}`"
            alt="支付二维码"
            class="mx-auto border rounded"
          />
        </div>
        <div
          v-else-if="currentMock"
          class="mx-auto mt-3 w-56 h-56 flex flex-col items-center justify-center border-2 border-dashed border-blue-300 rounded-xl text-blue-600"
        >
          <YdIllustration icon="ThunderboltOutlined" size="lg" />
          <span class="mt-2 font-medium">演示环境</span>
        </div>
        <a-button
          v-if="currentMock && currentOrderId"
          type="primary"
          block
          class="mt-4"
          size="large"
          :loading="mockPaying"
          @click="mockPay"
        >
          模拟支付成功（演示）
        </a-button>
      </template>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { YdIllustration, YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { apiGet, apiPost, apiPut } from '@/utils/api';
import {
  FREE_NVIDIA_ALERT_TITLE,
  FREE_NVIDIA_NOTICE,
  useAiConnect,
} from '@/composables/useAiConnect';

const router = useRouter()
const {
  aiConnect,
  notice: aiConnectNotice,
  freeTier: aiConnectFreeTier,
  alertTitle: aiConnectAlertTitle,
  usagePolicyNotice,
  probeSummaryLine,
  refresh: refreshAiConnect,
} = useAiConnect()

type Provider = {
  provider_id: string
  label: string
  tagline?: string
  experience_hint?: string
}
type Pack = {
  pack_id: string
  tokens: number
  price_cents: number
  price_yuan: number
  label: string
}

type CustomRecharge = {
  enabled?: boolean
  min_yuan?: number
  max_yuan?: number
  rate_description?: string
  tokens_per_yuan?: number
}

const providers = ref<Provider[]>([])
const packs = ref<Pack[]>([])
const customRecharge = ref<CustomRecharge | null>(null)
const customAmountYuan = ref<number>(100)
const customQuoteTokens = ref<number | null>(null)
const quotingCustom = ref(false)
let customQuoteTimer: ReturnType<typeof setTimeout> | null = null
const loadingPacks = ref(false)
const selectedProviderId = ref('')
const currentProviderId = ref<string | null>(null)

const paying = ref('')
const payingOrder = ref(false)
const qrOpen = ref(false)
const currentOrderId = ref('')
const currentMock = ref(false)
const currentAmount = ref(0)
const currentSubject = ref('')
const currentCodeUrl = ref('')
const mockPaying = ref(false)
const tenantId = ref('')

const tokenBalance = ref(0)
const quotaUsed = ref(0)
const isSuspended = ref(false)
const freeNvidiaNotice = ref(FREE_NVIDIA_NOTICE)
const nvidiaAlertTitle = ref(FREE_NVIDIA_ALERT_TITLE)
const rechargeCta = ref('要想获得更好的体验，请充值 AI 流量。')
const nvidiaFreeAvailable = ref(true)

const showNvidiaFreeBanner = computed(() => {
  if (!nvidiaFreeAvailable.value) return false
  if (aiConnectFreeTier.value) return true
  return aiConnect.value?.mode !== 'paid'
})
const nvidiaBannerText = computed(() => {
  if (aiConnectFreeTier.value && aiConnectNotice.value) {
    return aiConnectNotice.value
  }
  const parts = [freeNvidiaNotice.value]
  if (rechargeCta.value && !freeNvidiaNotice.value.includes(rechargeCta.value)) {
    parts.push(rechargeCta.value)
  }
  return parts.filter(Boolean).join(' ')
})

type LedgerRow = {
  id: string
  delta: number
  balance_after: number
  reason: string
  created_at?: string
}
const ledgerRows = ref<LedgerRow[]>([])
const ledgerTotal = ref(0)
const ledgerLoading = ref(false)
const ledgerPage = ref(1)
const ledgerColumns = [
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '变动', key: 'delta', width: 100 },
  { title: '原因', dataIndex: 'reason', key: 'reason' },
  { title: '余额', dataIndex: 'balance_after', key: 'balance_after', width: 100 },
]

const selectedProviderLabel = computed(() => {
  const p = providers.value.find(x => x.provider_id === selectedProviderId.value)
  return p?.label || ''
})

const currentProviderLabel = computed(() => {
  const pid = currentProviderId.value
  if (!pid) return ''
  return providers.value.find(x => x.provider_id === pid)?.label || pid
})

function displayPackLabel(pack: Pack): string {
  return (pack.label || '').replace(/Token/gi, '流量').replace(/token/gi, '流量')
}

async function resolveTenant(): Promise<string> {
  if (tenantId.value) return tenantId.value
  try {
    const dash = await apiGet<{ tenant_id?: string; tenant?: { id?: string } }>('/client/dashboard')
    const tid = dash?.tenant_id || dash?.tenant?.id
    if (tid) {
      tenantId.value = String(tid)
      return tenantId.value
    }
  } catch {
    /* ignore */
  }
  try {
    const cur = await apiGet<{ tenant?: { id?: string } }>('/tenants/current')
    const tid = cur?.tenant?.id
    if (tid) {
      tenantId.value = String(tid)
      return tenantId.value
    }
  } catch {
    /* ignore */
  }
  return ''
}

async function loadQuota() {
  try {
    const q = await apiGet<{
      balance?: number
      quota_used?: number
      is_suspended?: boolean
      ai_traffic_provider_id?: string
      ai_traffic_provider_label?: string
    }>('/token/my-quota')
    tokenBalance.value = q?.balance ?? 0
    quotaUsed.value = q?.quota_used ?? 0
    isSuspended.value = !!q?.is_suspended
    return
  } catch {
    /* fallback below */
  }
  const tid = await resolveTenant()
  if (!tid) return
  try {
    const q = await apiGet<{
      balance?: number
      quota_used?: number
      is_suspended?: boolean
      ai_traffic_provider_id?: string
      ai_traffic_provider_label?: string
    }>(`/token/quota-status/${tid}`)
    tokenBalance.value = q?.balance ?? 0
    quotaUsed.value = q?.quota_used ?? 0
    isSuspended.value = !!q?.is_suspended
    if (q?.ai_traffic_provider_id) {
      currentProviderId.value = q.ai_traffic_provider_id
      if (!selectedProviderId.value) selectedProviderId.value = q.ai_traffic_provider_id
    }
  } catch {
    /* ignore */
  }
}

async function loadLedger(page = 1) {
  ledgerLoading.value = true
  ledgerPage.value = page
  try {
    const data = await apiGet<{ items?: LedgerRow[]; total?: number }>(
      `/token/my-ledger?page=${page}&page_size=10`,
    )
    ledgerRows.value = data?.items || []
    ledgerTotal.value = data?.total ?? ledgerRows.value.length
  } catch {
    ledgerRows.value = []
  } finally {
    ledgerLoading.value = false
  }
}

function onLedgerPage(p: number) {
  void loadLedger(p)
}

type CatalogPayload = {
  providers?: Provider[]
  packs?: Pack[]
  current_provider_id?: string | null
  custom_recharge?: CustomRecharge
  ai_connect?: { user_notice?: string; free_tier?: boolean }
  free_nvidia_notice?: string
  free_nvidia_alert_title?: string
  recharge_cta?: string
  nvidia_free_available?: boolean
}

function applyCatalog(data: CatalogPayload | Pack[] | null | undefined) {
  if (!data) return
  if (Array.isArray(data)) {
    packs.value = data
    return
  }
  providers.value = data.providers || []
  packs.value = data.packs || []
  customRecharge.value = data.custom_recharge || null
  if (data.free_nvidia_notice) freeNvidiaNotice.value = data.free_nvidia_notice
  if (data.free_nvidia_alert_title) nvidiaAlertTitle.value = data.free_nvidia_alert_title
  if (data.recharge_cta) rechargeCta.value = data.recharge_cta
  if (typeof data.nvidia_free_available === 'boolean') {
    nvidiaFreeAvailable.value = data.nvidia_free_available
  }
  if (data.current_provider_id) {
    currentProviderId.value = data.current_provider_id
    if (!selectedProviderId.value) selectedProviderId.value = data.current_provider_id
  }
}

async function loadProvidersFallback() {
  try {
    const prov = await apiGet<{
      providers?: Provider[]
      current_provider_id?: string | null
    }>('/tenants/self/ai-traffic-provider')
    if (prov?.providers?.length) providers.value = prov.providers
    if (prov?.current_provider_id) {
      currentProviderId.value = prov.current_provider_id
      if (!selectedProviderId.value) selectedProviderId.value = prov.current_provider_id
    }
  } catch {
    /* ignore */
  }
}

async function loadCatalog() {
  loadingPacks.value = true
  try {
    let data: CatalogPayload | Pack[] | null = null
    try {
      data = await apiGet<CatalogPayload | Pack[]>('/client/ai-traffic-recharge-catalog')
    } catch {
      data = await apiGet<CatalogPayload | Pack[]>('/payment/addon/token-packs')
    }
    applyCatalog(data)
    if (!providers.value.length) {
      await loadProvidersFallback()
    }
    if (!providers.value.length) {
      message.warning('未加载到大模型平台列表，请确认已登录租户账号并刷新页面')
    }
  } catch (e: unknown) {
    const err = e as { message?: string }
    providers.value = []
    packs.value = []
    await loadProvidersFallback()
    message.error(err.message || '加载失败')
  } finally {
    loadingPacks.value = false
  }
  void refreshCustomQuote()
}

async function refreshCustomQuote() {
  if (!customRecharge.value?.enabled) return
  const yuan = customAmountYuan.value
  if (!yuan || yuan <= 0) {
    customQuoteTokens.value = null
    return
  }
  quotingCustom.value = true
  try {
    const q = await apiGet<{ tokens?: number }>(
      `/payment/addon/token-pack/quote?amount_yuan=${encodeURIComponent(String(yuan))}`,
    )
    customQuoteTokens.value = q?.tokens ?? null
  } catch {
    customQuoteTokens.value = null
  } finally {
    quotingCustom.value = false
  }
}

function onCustomAmountChange() {
  if (customQuoteTimer) clearTimeout(customQuoteTimer)
  customQuoteTimer = setTimeout(() => void refreshCustomQuote(), 300)
}

watch(customAmountYuan, () => onCustomAmountChange())

async function selectProvider(providerId: string) {
  selectedProviderId.value = providerId
  try {
    await apiPut('/tenants/self/ai-traffic-provider', { provider_id: providerId })
    currentProviderId.value = providerId
    message.success(`已选择：${selectedProviderLabel.value}`)
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.warning(err.message || '平台偏好保存失败，支付时仍会按当前选择下单')
  }
}

function goScenarios() {
  router.push('/client/ai-scenarios')
}

async function reload() {
  await Promise.all([loadQuota(), loadCatalog(), loadLedger(), refreshAiConnect()])
}

async function startCheckout(opts: {
  payKey: string
  subject: string
  amountCentsFallback: number
  body: Record<string, unknown>
}) {
  if (!selectedProviderId.value) {
    message.warning('请先选择大模型平台')
    return
  }
  const tid = await resolveTenant()
  if (!tid) {
    message.warning('无法识别当前租户，请重新登录')
    return
  }
  paying.value = opts.payKey
  payingOrder.value = true
  qrOpen.value = true
  currentCodeUrl.value = ''
  currentMock.value = false
  currentOrderId.value = ''
  currentSubject.value = opts.subject
  currentAmount.value = opts.amountCentsFallback

  try {
    const res = await apiPost<{
      id: string
      mock?: boolean
      amount: number
      subject: string
      code_url?: string
    }>('/payment/addon/token-pack', {
      tenant_id: tid,
      provider_id: selectedProviderId.value,
      ...opts.body,
    })
    currentOrderId.value = res.id
    currentMock.value = !!res.mock
    currentAmount.value = res.amount ?? opts.amountCentsFallback
    currentSubject.value = res.subject || opts.subject
    currentCodeUrl.value = res.code_url || ''
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.error(err.message || '下单失败')
    qrOpen.value = false
  } finally {
    paying.value = ''
    payingOrder.value = false
  }
}

function buyPack(pack: Pack) {
  void startCheckout({
    payKey: pack.pack_id,
    subject: `${selectedProviderLabel.value} · ${displayPackLabel(pack)}`,
    amountCentsFallback: pack.price_cents,
    body: { pack_id: pack.pack_id },
  })
}

function buyCustom() {
  const yuan = customAmountYuan.value
  if (!yuan || customQuoteTokens.value == null) {
    message.warning('请输入有效充值金额')
    return
  }
  void startCheckout({
    payKey: 'custom',
    subject: `${selectedProviderLabel.value} · 自定义 ¥${yuan}`,
    amountCentsFallback: Math.round(yuan * 100),
    body: { amount_yuan: yuan },
  })
}

async function mockPay() {
  mockPaying.value = true
  try {
    await apiPost('/payment/mock-pay', { order_id: currentOrderId.value })
    message.success('AI 流量已到账')
    qrOpen.value = false
    await loadQuota()
    await loadCatalog()
  } catch (e: unknown) {
    const err = e as { message?: string }
    message.error(err.message || '支付失败')
  } finally {
    mockPaying.value = false
  }
}

onMounted(reload)
</script>
