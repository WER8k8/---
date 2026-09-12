<template>
  <YdPage
    class="founder-diag max-w-3xl"
    title="创始人诊断"
    subtitle="国密自检与生产就绪检查。仅需浏览器，无需登录服务器。门禁：超管账号 + 创始人微信已绑定。"
    surface="elevated"
  >
    <template v-if="loading">
      <SkeletonCard variant="card" />
    </template>
    <template v-else>
      <a-alert
        v-if="preflight"
        :type="alertType"
        show-icon
        class="mb-4"
        :message="alertTitle"
        :description="alertDesc"
      />

      <a-card
        title="第一步：创始人微信（已绑死）"
        class="mb-4"
      >
        <a-tag
          v-if="preflight?.founder_wechat_locked"
          color="blue"
          class="mb-3"
        >
          锁定微信号：{{ preflight.founder_wechat_locked }}
        </a-tag>
        <p class="text-sm text-slate-600 mb-3">
          仅 <strong>{{ preflight?.founder_wechat_locked || '创始人' }}</strong> 可进诊断。
          超管登录名与微信号一致时可直接诊断；否则请用本人微信扫码绑定。
        </p>
        <p
          v-if="preflight?.username_is_founder"
          class="text-sm text-green-700 mb-2"
        >
          当前登录名已识别为创始人，可先运行诊断（建议仍绑定微信）。
        </p>
        <a-space wrap>
          <a-button
            type="primary"
            :disabled="!preflight?.oauth_wechat_enabled"
            @click="goBindWechat"
          >
            去绑定微信
          </a-button>
          <router-link to="/admin/system/account-bindings">
            <a-button>账号绑定页</a-button>
          </router-link>
        </a-space>
        <div
          v-if="preflight?.env_line"
          class="mt-4 p-3 bg-slate-50 rounded text-sm font-mono break-all"
        >
          {{ preflight.env_line }}
          <a-button
            size="small"
            class="ml-2"
            @click="copyEnv"
          >
            复制
          </a-button>
        </div>
      </a-card>

      <a-card
        title="第二步：成果保护（鉴定用）"
        class="mb-4"
      >
        <p class="text-sm text-slate-600 mb-3">
          全平台 CSV 导出仅创始人；每次导出与越权尝试会写入安全留痕，供第三方鉴定截图。
        </p>
        <a-space wrap class="mb-3">
          <a-button
            :loading="summaryLoading"
            :disabled="!canRunDiagnostics"
            @click="loadProtectionSummary"
          >
            鉴定摘要
          </a-button>
          <a-button
            :loading="eventsLoading"
            :disabled="!canRunDiagnostics"
            @click="loadSecurityEvents"
          >
            安全事件
          </a-button>
        </a-space>
        <div
          v-if="protectionSummary"
          class="text-sm bg-slate-50 p-3 rounded mb-3"
        >
          <p>环境：{{ protectionSummary.environment }} · 平台导出仅创始人：{{ protectionSummary.export_platform_founder_only ? '是' : '否' }}</p>
          <p>已记录导出 {{ protectionSummary.stats.data_exports_logged }} 次 · 拒绝 {{ protectionSummary.stats.access_denied_logged }} 次</p>
          <ul class="list-disc pl-5 mt-2">
            <li
              v-for="(c, i) in protectionSummary.claims"
              :key="i"
            >
              {{ c }}
            </li>
          </ul>
        </div>
        <a-table
          v-if="securityEvents.length"
          size="small"
          :pagination="{ pageSize: 8 }"
          :data-source="securityEvents"
          :columns="eventColumns"
          row-key="id"
        />
      </a-card>

      <a-card
        title="第三步：系统诊断"
        class="mb-4"
      >
        <a-space wrap>
          <a-button
            type="primary"
            :loading="diagLoading"
            :disabled="!canRunDiagnostics"
            @click="runDiagnostics"
          >
            运行诊断
          </a-button>
          <a-button
            :loading="cryptoLoading"
            :disabled="!canRunDiagnostics"
            @click="runCryptoTest"
          >
            国密自检
          </a-button>
        </a-space>

        <div
          v-if="status"
          class="mt-4"
        >
          <a-tag :color="status.readiness.ready ? 'success' : 'warning'">
            就绪 {{ status.readiness.ready ? '通过' : '未通过' }}
          </a-tag>
          <a-tag class="ml-2">
            环境 {{ status.environment }}
          </a-tag>
          <a-tag
            class="ml-2"
            :color="status.gmssl_installed ? 'success' : 'default'"
          >
            gmssl {{ status.gmssl_installed ? '已安装' : '未安装' }}
          </a-tag>
          <ul class="mt-3 space-y-1 text-sm">
            <li
              v-for="c in failedChecks"
              :key="c.id"
            >
              <span class="text-red-600">{{ c.title }}</span>：{{ c.message }}
            </li>
          </ul>
        </div>

        <div
          v-if="cryptoResult"
          class="mt-4 text-sm"
        >
          <p>SM4 往返：{{ cryptoResult.sm4_roundtrip_ok ? '正常' : '异常' }}</p>
          <p v-if="cryptoResult.error">
            {{ cryptoResult.error }}
          </p>
        </div>
      </a-card>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { apiGet } from '@/utils/api'
import {
  fetchFounderCryptoSelfTest,
  fetchFounderPreflight,
  fetchFounderStatus,
  fetchProtectionSummary,
  fetchSecurityEvents,
  type CryptoSelfTest,
  type FounderPreflight,
  type FounderStatus,
  type ProtectionSummary,
  type SecurityEventRow,
} from '@/api/founderOps'
import { fetchOAuthAuthorizeUrl } from '@/api/oauth'

const router = useRouter()
const loading = ref(false)
const diagLoading = ref(false)
const cryptoLoading = ref(false)
const preflight = ref<FounderPreflight | null>(null)
const status = ref<FounderStatus | null>(null)
const cryptoResult = ref<CryptoSelfTest | null>(null)
const summaryLoading = ref(false)
const eventsLoading = ref(false)
const protectionSummary = ref<ProtectionSummary | null>(null)
const securityEvents = ref<SecurityEventRow[]>([])

const eventColumns = [
  { title: '时间', dataIndex: 'created_at', width: 170 },
  { title: '动作', dataIndex: 'action', width: 140 },
  { title: 'IP', dataIndex: 'ip_address', width: 120 },
  { title: '说明', key: 'detail', customRender: ({ record }: { record: SecurityEventRow }) => (record.detail?.export_kind as string) || record.resource_id || '—' },
]

const canRunDiagnostics = computed(() => {
  if (!preflight.value) return false
  if (preflight.value.gate_mode === 'wechat') {
    return (
      preflight.value.wechat_is_founder === true
      || preflight.value.username_is_founder === true
    )
  }
  return preflight.value.founder_debug_enabled
})

const alertType = computed(() => {
  if (!preflight.value) return 'info'
  if (preflight.value.gate_mode === 'wechat' && preflight.value.wechat_is_founder) {
    return 'success'
  }
  if (!preflight.value.wechat_bound) return 'warning'
  if (!preflight.value.founder_wechat_configured) return 'warning'
  return 'info'
})

const alertTitle = computed(() => {
  const p = preflight.value
  if (!p) return '加载中…'
  if (p.gate_mode === 'wechat' && p.wechat_is_founder) return '创始人微信已验证，可运行诊断'
  if (!p.wechat_bound) return '请先绑定微信'
  if (!p.founder_wechat_configured) return '等待服务器配置 FOUNDER_WECHAT_OPENID'
  if (p.gate_mode === 'token') return '当前为开发令牌模式（建议生产改用微信）'
  return '创始人门禁未配置'
})

const alertDesc = computed(() => {
  const p = preflight.value
  if (!p) return ''
  if (p.wechat_id_masked) return `已绑定：${p.wechat_id_masked}`
  return p.steps?.join(' ') || ''
})

const failedChecks = computed(() => {
  const checks = status.value?.readiness?.checks || []
  return checks.filter((c) => c.status === 'fail')
})

async function loadPreflight() {
  loading.value = true
  try {
    preflight.value = await fetchFounderPreflight()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    loading.value = false
  }
}

async function goBindWechat() {
  try {
    const state = btoa(
      JSON.stringify({
        redirect: '/admin/founder-diagnostics',
        ts: Date.now(),
        provider: 'wechat',
        mode: 'bind',
      })
    )
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
    sessionStorage.setItem('oauth_state_wechat', state)
    const { authorize_url } = await fetchOAuthAuthorizeUrl('wechat', state)
    window.location.assign(authorize_url)
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '无法发起微信绑定')
  }
}

function copyEnv() {
  const line = preflight.value?.env_line
  if (!line) return
  navigator.clipboard?.writeText(line).then(
    () => message.success('已复制到剪贴板，请写入服务器 .env.prod'),
    () => message.warning(`复制失败，请手动复制: ${line}`)
  )
}

async function runDiagnostics() {
  diagLoading.value = true
  status.value = null
  try {
    status.value = await fetchFounderStatus()
    message.success(status.value.readiness.ready ? '诊断完成：就绪' : '诊断完成：存在未通过项')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '诊断失败')
  } finally {
    diagLoading.value = false
  }
}

async function loadProtectionSummary() {
  summaryLoading.value = true
  try {
    protectionSummary.value = await fetchProtectionSummary()
    message.success('已加载鉴定摘要')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    summaryLoading.value = false
  }
}

async function loadSecurityEvents() {
  eventsLoading.value = true
  try {
    securityEvents.value = await fetchSecurityEvents(30)
    message.success(`已加载 ${securityEvents.value.length} 条安全事件`)
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载失败')
  } finally {
    eventsLoading.value = false
  }
}

async function runCryptoTest() {
  cryptoLoading.value = true
  cryptoResult.value = null
  try {
    cryptoResult.value = await fetchFounderCryptoSelfTest()
    if (cryptoResult.value.sm4_roundtrip_ok) {
      message.success('国密 SM4 往返正常')
    } else {
      message.warning('国密未完全就绪，请在后端安装 gmssl')
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '国密自检失败')
  } finally {
    cryptoLoading.value = false
  }
}

onMounted(async () => {
  try { await apiGet('/founder-ops') } catch { /* 空状态 */ }
  loadPreflight()
  if (router.currentRoute.value.query.bound === '1') {
    message.success('微信绑定成功，请复制下方配置到服务器')
  }
})
</script>

<style scoped>
.founder-diag {
  min-height: 320px;
}
</style>
