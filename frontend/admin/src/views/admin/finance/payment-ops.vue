/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="支付码与接口" subtitle="微信/支付宝收款配置、回调地址、探针二维码与证书缓存" surface="elevated">
    <template #actions>
      <YdTableToolbar
        :loading="loading"
        :show-density="false"
        :show-fullscreen="false"
        @refresh="load"
      />
    </template>

    <YdFinanceNav />

    <section class="payment-ops-toolbar uj-glass-panel">
      <div class="payment-ops-toolbar__head">
        <strong>支付探针与验收</strong>
        <span v-if="!canRunPaymentOps" class="payment-ops-toolbar__hint">需平台管理员权限方可操作</span>
      </div>
      <div class="payment-ops-toolbar__actions">
        <a-button
          type="primary"
          :loading="refreshing"
          :disabled="!canRunPaymentOps"
          @click="refreshCerts"
        >
          刷新微信证书缓存
        </a-button>
        <a-button
          :loading="probing"
          :disabled="!canRunPaymentOps"
          @click="probeAlipay"
        >
          支付宝沙箱探针
        </a-button>
        <a-button
          :loading="wxProbing"
          :disabled="!canRunPaymentOps"
          @click="probeWechat"
        >
          微信 Native 探针
        </a-button>
        <a-button
          :loading="stagingChecking"
          :disabled="!canRunPaymentOps"
          @click="runStagingCheck"
        >
          Staging 自检
        </a-button>
        <a-button
          :loading="reachabilityChecking"
          :disabled="!canRunPaymentOps"
          @click="checkPublicReachability"
        >
          公网/ngrok 探测
        </a-button>
        <a-button
          :loading="publicNotifyChecking"
          :disabled="!canRunPaymentOps"
          @click="checkPublicNotify"
        >
          公网 notify 验收
        </a-button>
      </div>
    </section>

    <a-alert
      type="info"
      show-icon
      class="mb-4"
      message="商户号与密钥在服务器 .env 配置"
      description="本页用于查看回调地址、刷新微信证书、生成支付宝/微信探针收款码（测试下单）。更换商户请在 deploy/production 环境变量中修改 WECHAT_PAY_* / ALIPAY_* 后重启 API。"
    />

    <template v-if="loading">
      <SkeletonCard variant="card" />
    </template>
    <template v-else>
      <a-row
        :gutter="[16, 16]"
        class="mb-4"
      >
        <a-col
          v-for="card in envCards"
          :key="card.key"
          :xs="24"
          :sm="12"
          :lg="6"
        >
          <a-card size="small">
            <div class="text-xs text-slate-500">
              {{ card.label }}
            </div>
            <div class="text-base font-medium mt-1">
              {{ card.value }}
            </div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="[16, 16]">
        <a-col
          :xs="24"
          :lg="12"
        >
          <a-card
            title="微信支付"
            size="small"
          >
            <a-descriptions
              :column="1"
              size="small"
              bordered
            >
              <a-descriptions-item label="V3 已配置">
                {{ wechat?.v3_live ? '是' : '否' }}
              </a-descriptions-item>
              <a-descriptions-item label="Notify URL">
                {{ wechat?.notify_url || '—' }}
              </a-descriptions-item>
              <a-descriptions-item label="商户证书 Serial">
                {{ wechat?.merchant_serial || '—' }}
              </a-descriptions-item>
              <a-descriptions-item label="环境平台 Serial">
                {{ wechat?.env_platform_serial || '—' }}
              </a-descriptions-item>
              <a-descriptions-item label="环境平台公钥">
                {{ wechat?.env_platform_pem_configured ? '已配置' : '未配置' }}
              </a-descriptions-item>
              <a-descriptions-item label="缓存 TTL（秒）">
                {{ wechat?.cert_cache_ttl_seconds ?? '—' }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
        <a-col
          :xs="24"
          :lg="12"
        >
          <a-card
            title="支付宝"
            size="small"
          >
            <a-descriptions
              :column="1"
              size="small"
              bordered
            >
              <a-descriptions-item label="已配置">
                {{ alipay?.configured ? '是' : '否' }}
              </a-descriptions-item>
              <a-descriptions-item label="Gateway">
                {{ alipay?.gateway || '—' }}
              </a-descriptions-item>
              <a-descriptions-item label="Notify URL">
                {{ alipay?.notify_url || '—' }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
      </a-row>

      <a-card
        title="运维操作历史"
        size="small"
        class="mt-4"
        v-if="canRunPaymentOps"
      >
        <a-space class="mb-3" wrap>
          <a-select
            v-model:value="opsAuditAction"
            allow-clear
            placeholder="操作类型"
            style="width: 180px"
            @change="() => loadOpsAudit(1)"
          >
            <a-select-option v-for="a in opsAuditActions" :key="a.value" :value="a.value">
              {{ a.label }}
            </a-select-option>
          </a-select>
          <a-range-picker
            v-model:value="opsAuditDateRange"
            value-format="YYYY-MM-DD"
            :placeholder="['起始', '结束']"
            @change="() => loadOpsAudit(1)"
          />
          <a-button @click="exportOpsAudit">
            导出 CSV
          </a-button>
        </a-space>
        <div ref="opsAuditPanelRef" class="yd-panel yd-table-panel">
          <div class="panel-head mb-3">
            <YdTableToolbar
              :loading="opsAuditLoading"
              :target-ref="opsAuditPanelRef"
              :show-export="true"
              @refresh="() => loadOpsAudit(1)"
              @export="exportOpsAudit"
            />
          </div>
          <YdDataTable
            :columns="opsAuditCols"
            :data-source="opsAuditRows"
            :loading="opsAuditLoading"
            :pagination="opsAuditPagination"
            :table-props="{ size: tableSize, rowKey: 'id', customRow: opsAuditRowProps }"
            @page-change="onOpsAuditPageChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'ok'">
                {{ record.ok ? '成功' : '失败' }}
              </template>
            </template>
          </YdDataTable>
        </div>
      </a-card>

      <a-drawer
        v-model:open="opsAuditDrawerOpen"
        title="运维操作详情"
        width="560"
      >
        <template v-if="opsAuditDetail">
          <a-descriptions :column="1" size="small" bordered class="mb-3">
            <a-descriptions-item label="时间">{{ opsAuditDetail.created_at }}</a-descriptions-item>
            <a-descriptions-item label="操作">{{ opsAuditDetail.action_label || opsAuditDetail.action }}</a-descriptions-item>
            <a-descriptions-item label="操作人">{{ opsAuditDetail.actor_user_name || '—' }}</a-descriptions-item>
            <a-descriptions-item label="结果">{{ opsAuditDetail.ok ? '成功' : '失败' }}</a-descriptions-item>
            <a-descriptions-item label="摘要">{{ opsAuditDetail.summary || '—' }}</a-descriptions-item>
          </a-descriptions>
          <pre class="text-xs bg-slate-50 p-3 rounded overflow-auto">{{ JSON.stringify(opsAuditDetail.detail, null, 2) }}</pre>
        </template>
      </a-drawer>

      <a-card
        title="运维操作结果"
        size="small"
        class="mt-4"
        v-if="probeResult || wxProbeResult || stagingResult || reachabilityResult || publicNotifyResult"
      >
        <div v-if="alipayCodeUrl" class="text-center mb-3">
          <p class="text-xs text-slate-500 mb-1">支付宝探针二维码</p>
          <img :src="qrImg(alipayCodeUrl)" alt="alipay qr" class="mx-auto border rounded" />
        </div>
        <div v-if="wxCodeUrl" class="text-center mb-3">
          <p class="text-xs text-slate-500 mb-1">微信探针二维码</p>
          <img :src="qrImg(wxCodeUrl)" alt="wechat qr" class="mx-auto border rounded" />
        </div>
        <pre v-if="probeResult" class="text-xs bg-slate-50 p-3 rounded overflow-auto">支付宝:\n{{ probeResult }}</pre>
        <pre v-if="wxProbeResult" class="text-xs bg-slate-50 p-3 rounded overflow-auto mt-2">微信:\n{{ wxProbeResult }}</pre>
        <pre v-if="stagingResult" class="text-xs bg-slate-50 p-3 rounded overflow-auto mt-2">Staging:\n{{ stagingResult }}</pre>
        <pre v-if="reachabilityResult" class="text-xs bg-slate-50 p-3 rounded overflow-auto mt-2">公网:\n{{ reachabilityResult }}</pre>
        <pre v-if="publicNotifyResult" class="text-xs bg-slate-50 p-3 rounded overflow-auto mt-2">公网 notify:\n{{ publicNotifyResult }}</pre>
      </a-card>

      <a-card
        title="微信平台证书缓存"
        size="small"
        class="mt-4"
      >
        <a-empty
          v-if="!certCache.length"
          description="暂无缓存条目（验签时将按需拉取或使用环境变量公钥）"
        />
        <div v-else ref="certPanelRef" class="yd-panel yd-table-panel">
          <div class="panel-head mb-3">
            <YdTableToolbar
              :loading="loading"
              :target-ref="certPanelRef"
              :show-export="false"
              @refresh="load"
            />
          </div>
          <YdDataTable
            :columns="certCols"
            :data-source="certCache"
            :pagination="false"
            :table-props="{ size: tableSize, rowKey: 'serial' }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'expired'">
                {{ record.expired ? '已过期' : '有效' }}
              </template>
            </template>
          </YdDataTable>
        </div>
      </a-card>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import { message } from 'ant-design-vue'

import { YdDataTable, YdFinanceNav, YdPage, YdTableToolbar } from '@/components/youding'
import { getAuthToken } from '@/utils/api'
import { isPlatformAdminFromToken } from '@/utils/sessionAuth'
import SkeletonCard from '@/components/common/SkeletonCard.vue'

type CertRow = {
  serial: string
  expires_at: string
  expired: boolean
}

type OpsStatus = {
  environment?: string
  strict_verify?: boolean
  mock_allowed?: boolean
  wechat?: {
    v3_live?: boolean
    notify_url?: string
    merchant_serial?: string
    env_platform_serial?: string
    env_platform_pem_configured?: boolean
    cert_cache_ttl_seconds?: number
    cert_cache?: CertRow[]
  }
  alipay?: {
    configured?: boolean
    gateway?: string
    notify_url?: string
  }
}

const loading = ref(false)
const opsAuditPanelRef = ref<HTMLElement | null>(null)
const certPanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)
const refreshing = ref(false)
const probing = ref(false)
const wxProbing = ref(false)
const stagingChecking = ref(false)
const reachabilityChecking = ref(false)
const publicNotifyChecking = ref(false)
const probeResult = ref('')
const wxProbeResult = ref('')
const stagingResult = ref('')
const reachabilityResult = ref('')
const publicNotifyResult = ref('')
const opsAuditLoading = ref(false)
const opsAuditRows = ref<Record<string, unknown>[]>([])
const opsAuditPage = ref(1)
const opsAuditPageSize = ref(10)
const opsAuditTotal = ref(0)
const opsAuditAction = ref<string | undefined>()
const opsAuditDateRange = ref<[string, string] | undefined>(undefined)
const opsAuditActions = ref<{ value: string; label: string }[]>([])
const opsAuditDrawerOpen = ref(false)
const opsAuditDetail = ref<Record<string, unknown> | null>(null)
const alipayCodeUrl = ref('')
const wxCodeUrl = ref('')
const status = ref<OpsStatus | null>(null)

const wechat = computed(() => status.value?.wechat)
const alipay = computed(() => status.value?.alipay)
const certCache = computed(() => status.value?.wechat?.cert_cache || [])
const canRunPaymentOps = computed(() => isPlatformAdminFromToken(getAuthToken()))

const certCols = [
  { title: 'Serial', dataIndex: 'serial', key: 'serial', ellipsis: true },
  { title: '过期时间', dataIndex: 'expires_at', key: 'expires_at', width: 200 },
  { title: '状态', key: 'expired', width: 90 },
]

const opsAuditCols = [
  { title: '时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', dataIndex: 'action_label', key: 'action_label', width: 140 },
  { title: '操作人', dataIndex: 'actor_user_name', key: 'actor_user_name', width: 100 },
  { title: '结果', key: 'ok', width: 70 },
  { title: '摘要', dataIndex: 'summary', key: 'summary', ellipsis: true },
]

const opsAuditPagination = computed(() => ({
  current: opsAuditPage.value,
  pageSize: opsAuditPageSize.value,
  total: opsAuditTotal.value,
}))

function onOpsAuditPageChange(p: { current: number; pageSize: number }) {
  void loadOpsAudit(p.current)
}

const envCards = computed(() => {
  const s = status.value
  return [
    { key: 'env', label: '环境', value: s?.environment || '—' },
    { key: 'strict', label: '严验签', value: s?.strict_verify ? '开启' : '关闭' },
    { key: 'mock', label: 'Mock 支付', value: s?.mock_allowed ? '允许' : '禁止' },
    { key: 'wx', label: '微信 V3', value: s?.wechat?.v3_live ? 'Live' : '未配置' },
  ]
})

function authHeaders() {
  return { Authorization: `Bearer ${getAuthToken()}` }
}

function qrImg(codeUrl: string) {
  return `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(codeUrl)}`
}

async function load() {
  loading.value = true
  try {
    const r = await fetch('/api/v1/payment/ops/status', { headers: authHeaders() })
    const d = await r.json()
    if (d.code !== 0) {
      message.error(d.message || '加载失败')
      return
    }
    status.value = d.data
  } catch (e) {
    message.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

async function refreshCerts() {
  refreshing.value = true
  try {
    const r = await fetch('/api/v1/payment/ops/wechat/refresh-certs', {
      method: 'POST',
      headers: authHeaders(),
    })
    const d = await r.json()
    if (d.code !== 0) {
      message.error(d.message || '刷新失败')
      return
    }
    const payload = d.data || {}
    if (payload.refreshed) {
      message.success(`已刷新 ${(payload.serials || []).length} 张证书`)
    } else {
      message.warning(payload.reason || '未刷新（微信 V3 未配置 live）')
    }
    await load()
    await loadOpsAudit(1)
  } catch (e) {
    message.error(e instanceof Error ? e.message : '刷新失败')
  } finally {
    refreshing.value = false
  }
}

async function probeAlipay() {
  probing.value = true
  probeResult.value = ''
  alipayCodeUrl.value = ''
  try {
    const r = await fetch('/api/v1/payment/ops/alipay/probe', {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_yuan: 0.01, subject: '运维探针', run_precreate: true }),
    })
    const d = await r.json()
    if (d.code !== 0) {
      message.error(d.message || '探针失败')
      return
    }
    probeResult.value = JSON.stringify(d.data, null, 2)
    alipayCodeUrl.value = d.data?.precreate?.code_url || d.data?.precreate?.qr_code || ''
    if (d.data?.precreate?.code_url) {
      message.success('探针完成，见下方 code_url / 可扫码')
    } else if (d.data?.configured) {
      message.success('配置齐全，precreate 已执行')
    } else {
      message.warning(d.data?.reason || '支付宝未配置 live')
    }
    await loadOpsAudit(1)
  } catch (e) {
    message.error(e instanceof Error ? e.message : '探针失败')
  } finally {
    probing.value = false
  }
}

async function probeWechat() {
  wxProbing.value = true
  wxProbeResult.value = ''
  wxCodeUrl.value = ''
  try {
    const r = await fetch('/api/v1/payment/ops/wechat/probe', {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_yuan: 0.01, subject: '微信运维探针', run_precreate: true }),
    })
    const d = await r.json()
    if (d.code !== 0) {
      message.error(d.message || '探针失败')
      return
    }
    wxProbeResult.value = JSON.stringify(d.data, null, 2)
    wxCodeUrl.value = d.data?.precreate?.code_url || ''
    if (d.data?.precreate?.code_url) {
      message.success('微信探针完成')
    } else {
      message.warning(d.data?.reason || '微信未配置 live')
    }
    await loadOpsAudit(1)
  } catch (e) {
    message.error(e instanceof Error ? e.message : '探针失败')
  } finally {
    wxProbing.value = false
  }
}

async function runStagingCheck() {
  stagingChecking.value = true
  stagingResult.value = ''
  try {
    const r = await fetch('/api/v1/payment/ops/staging/self-check', {
      method: 'POST',
      headers: authHeaders(),
    })
    const d = await r.json()
    if (d.code !== 0) {
      message.error(d.message || '自检失败')
      return
    }
    stagingResult.value = JSON.stringify(d.data, null, 2)
    if (d.data?.ok) {
      message.success('Staging 自检通过（进程内 notify）')
    } else {
      message.warning('部分检查未通过，见下方详情')
    }
    await loadOpsAudit(1)
  } catch (e) {
    message.error(e instanceof Error ? e.message : '自检失败')
  } finally {
    stagingChecking.value = false
  }
}

async function checkPublicReachability() {
  reachabilityChecking.value = true
  reachabilityResult.value = ''
  try {
    const r = await fetch('/api/v1/payment/ops/staging/public-reachability', {
      headers: authHeaders(),
    })
    const d = await r.json()
    if (d.code !== 0) {
      message.error(d.message || '探测失败')
      return
    }
    reachabilityResult.value = JSON.stringify(d.data, null, 2)
    if (d.data?.ok) {
      message.success(`公网可达: ${d.data.public_url}`)
    } else {
      message.warning(d.data?.reason || d.data?.health?.error || '公网不可达')
    }
    await loadOpsAudit(1)
  } catch (e) {
    message.error(e instanceof Error ? e.message : '探测失败')
  } finally {
    reachabilityChecking.value = false
  }
}

async function checkPublicNotify() {
  publicNotifyChecking.value = true
  publicNotifyResult.value = ''
  try {
    const r = await fetch('/api/v1/payment/ops/staging/public-notify-check?discover_ngrok=true&try_signed=true', {
      method: 'POST',
      headers: authHeaders(),
    })
    const d = await r.json()
    if (d.code !== 0) {
      message.error(d.message || '公网 notify 验收失败')
      return
    }
    publicNotifyResult.value = JSON.stringify(d.data, null, 2)
    if (d.data?.ok) {
      const mode = d.data?.verify_mode === 'strict_unsigned_reject' ? '（严验签：未签名回调已正确拒绝）' : ''
      message.success(`公网 notify 端到端验收通过${mode}`)
    } else if (d.data?.strict_verify) {
      message.warning(d.data?.reason || '严验签模式下未签名回调应被拒绝；请检查配置')
    } else {
      message.warning(d.data?.reason || '公网 notify 未全部通过')
    }
    await loadOpsAudit(1)
  } catch (e) {
    message.error(e instanceof Error ? e.message : '公网 notify 验收失败')
  } finally {
    publicNotifyChecking.value = false
  }
}

async function exportOpsAudit() {
  if (!canRunPaymentOps.value) {
    message.warning('需平台管理员权限方可导出')
    return
  }
  try {
    const params = new URLSearchParams()
    if (opsAuditAction.value) params.set('action', opsAuditAction.value)
    if (opsAuditDateRange.value?.[0]) params.set('start_at', opsAuditDateRange.value[0])
    if (opsAuditDateRange.value?.[1]) params.set('end_at', opsAuditDateRange.value[1])
    const qs = params.toString()
    const r = await fetch(`/api/v1/payment/ops/audit/export${qs ? `?${qs}` : ''}`, {
      headers: authHeaders(),
    })
    if (!r.ok) {
      message.error('导出失败')
      return
    }
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `payment_ops_audit_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    message.success('运维审计 CSV 已下载')
  } catch (e) {
    message.error(e instanceof Error ? e.message : '导出失败')
  }
}

async function loadOpsAuditActions() {
  if (!canRunPaymentOps.value) return
  try {
    const r = await fetch('/api/v1/payment/ops/audit/actions', { headers: authHeaders() })
    const d = await r.json()
    if (d.code === 0) opsAuditActions.value = d.data || []
  } catch {
    opsAuditActions.value = []
  }
}

function opsAuditRowProps(record: Record<string, unknown>) {
  return {
    style: { cursor: 'pointer' },
    onClick: () => openOpsAuditDetail(record),
  }
}

function openOpsAuditDetail(record: Record<string, unknown>) {
  opsAuditDetail.value = record
  opsAuditDrawerOpen.value = true
}

async function loadOpsAudit(page = 1) {
  if (!canRunPaymentOps.value) return
  opsAuditLoading.value = true
  opsAuditPage.value = page
  try {
    const params = new URLSearchParams()
    params.set('page', String(page))
    params.set('page_size', String(opsAuditPageSize.value))
    if (opsAuditAction.value) params.set('action', opsAuditAction.value)
    if (opsAuditDateRange.value?.[0]) params.set('start_at', opsAuditDateRange.value[0])
    if (opsAuditDateRange.value?.[1]) params.set('end_at', opsAuditDateRange.value[1])
    const r = await fetch(`/api/v1/payment/ops/audit?${params}`, { headers: authHeaders() })
    const d = await r.json()
    if (d.code !== 0) return
    opsAuditRows.value = d.data?.items || []
    opsAuditTotal.value = d.data?.total || 0
  } finally {
    opsAuditLoading.value = false
  }
}

onMounted(async () => {
  await load()
  await loadOpsAuditActions()
  await loadOpsAudit(1)
})
</script>

<style scoped lang="scss">
.payment-ops-toolbar {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 16px;
}

.payment-ops-toolbar__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #1e293b;
}

.payment-ops-toolbar__hint {
  font-size: 12px;
  font-weight: 500;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fde68a;
  padding: 2px 8px;
  border-radius: 999px;
}

.payment-ops-toolbar__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
