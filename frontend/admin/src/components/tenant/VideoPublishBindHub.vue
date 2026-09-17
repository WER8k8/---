/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <section v-if="hub" class="video-bind-hub panel">
    <div class="vbh-head">
      <div>
        <h3 class="vbh-title">视频发布渠道</h3>
        <p class="vbh-sub">
          平台代发矩阵（AiToEarn）与本机 SAU 自带号（抖音/快手/B站等）可并存；发布前请确保对应渠道 Cookie 有效。
        </p>
      </div>
      <a-space wrap>
        <a-tag :color="slotAssigned ? 'success' : 'warning'">
          {{ slotAssigned ? `矩阵号 ${slotCount} 个` : '矩阵待分配' }}
        </a-tag>
        <a-tag :color="sauOkCount > 0 ? 'success' : 'default'">
          SAU {{ sauOkCount }}/{{ sauPlatforms.length }} 已登录
        </a-tag>
        <a-button size="small" :loading="loading" @click="load">刷新</a-button>
        <a-button size="small" :loading="sauChecking" @click="checkSauAll">检测 SAU Cookie</a-button>
      </a-space>
    </div>

    <a-alert
      type="info"
      show-icon
      class="mb-3"
      :message="hub.aitoearn.hint || '平台代发模式'"
      :description="slotAssigned ? '矩阵号由运营分配；也可在下方使用 SAU 自带号。' : '开户后运营可分配矩阵号；国内短视频可先配置 SAU 自带号。'"
    >
      <template v-if="slotAssigned" #action>
        <a-button size="small" type="primary" ghost :loading="syncing" @click="syncSlot">
          刷新代发渠道
        </a-button>
      </template>
    </a-alert>

    <div class="vbh-grid">
      <div
        v-for="p in hub.platforms"
        :key="p.platform_id"
        class="vbh-card"
        :class="cardClass(p)"
      >
        <div class="vbh-card-top">
          <strong>{{ p.platform_name }}</strong>
          <a-tag v-if="p.sau_cookie_ok" color="success" size="small">SAU 有效</a-tag>
          <a-tag v-else-if="p.sau_bind" color="orange" size="small">待扫码</a-tag>
          <a-tag v-else-if="p.account?.bound" color="success" size="small">已就绪</a-tag>
          <a-tag v-else-if="p.aitoearn_synced" color="processing" size="small">矩阵已配</a-tag>
          <a-tag v-else color="default" size="small">未开通</a-tag>
        </div>
        <p class="vbh-cap">{{ p.video_publish?.label || '视频代发' }}</p>

        <div v-if="p.sau_bind" class="vbh-sau">
          <p class="vbh-sau-account">账号 {{ p.sau_bind.account }}</p>
          <a-typography-paragraph
            :copyable="{ text: p.sau_bind.login_command }"
            class="vbh-cmd"
          >
            {{ p.sau_bind.login_command }}
          </a-typography-paragraph>
          <a-button size="small" type="link" @click="checkSauOne(p.platform_name)">检测 Cookie</a-button>
        </div>

        <a-button
          v-else-if="!p.aitoearn_synced && p.bind_via !== 'aitoearn_dedicated'"
          size="small"
          type="link"
          @click="emitConnect(p)"
        >
          自带号连接
        </a-button>
      </div>
    </div>

    <div class="vbh-foot">
      <router-link to="/client/article-to-video" class="text-primary-600 text-sm">文章转视频 →</router-link>
      <router-link to="/client/queues/publish" class="text-primary-600 text-sm ml-4">发布队列 →</router-link>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { apiGet, apiPost } from '@/utils/api'

type SauBind = {
  account: string
  login_command: string
  check_command: string
  execution?: string
}

type HubPlatform = {
  platform_id: string
  platform_name: string
  account?: { bound?: boolean }
  aitoearn_synced?: boolean
  bind_via?: string
  video_publish?: { label?: string }
  sau_bind?: SauBind
  sau_cookie_ok?: boolean
}

type BindHub = {
  summary: { bound_local: number; video_platforms: number }
  tenant_aitoearn_slot?: { assigned?: boolean; account_count?: number }
  aitoearn: { enabled: boolean; hint: string }
  platforms: HubPlatform[]
}

const emit = defineEmits<{
  (e: 'connect', platform: { id: string; name: string }): void
}>()

const hub = ref<BindHub | null>(null)
const loading = ref(false)
const syncing = ref(false)
const sauChecking = ref(false)

const slotAssigned = computed(
  () => hub.value?.tenant_aitoearn_slot?.assigned || (hub.value?.aitoearn as { tenant_account_ids?: string[] })?.tenant_account_ids?.length,
)
const slotCount = computed(() => hub.value?.tenant_aitoearn_slot?.account_count ?? 0)
const sauPlatforms = computed(() => (hub.value?.platforms || []).filter((p) => p.sau_bind))
const sauOkCount = computed(() => sauPlatforms.value.filter((p) => p.sau_cookie_ok).length)

function cardClass(p: HubPlatform) {
  return {
    bound: p.account?.bound || p.sau_cookie_ok,
    aito: p.aitoearn_synced,
    'sau-pending': p.sau_bind && !p.sau_cookie_ok,
  }
}

async function load() {
  loading.value = true
  try {
    hub.value = await apiGet<BindHub>('/publish/video/bind-hub')
    await mergeSauChecks()
  } catch {
    hub.value = null
  } finally {
    loading.value = false
  }
}

async function mergeSauChecks() {
  if (!hub.value?.platforms?.some((p) => p.sau_bind)) return
  try {
    const data = await apiGet<{ platforms?: { platform_name: string; cookie_ok: boolean }[] }>(
      '/publish/video/sau-check',
    )
    const map = new Map((data.platforms || []).map((r) => [r.platform_name, r.cookie_ok]))
    hub.value.platforms = hub.value.platforms.map((p) => ({
      ...p,
      sau_cookie_ok: map.get(p.platform_name) ?? p.sau_cookie_ok,
    }))
  } catch {
    /* sidecar/cli 未配置时忽略 */
  }
}

async function checkSauAll() {
  sauChecking.value = true
  try {
    const data = await apiGet<{ cookie_ok: number; checked: number }>('/publish/video/sau-check')
    await mergeSauChecks()
    message.success(`SAU Cookie 有效 ${data.cookie_ok}/${data.checked}`)
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : 'SAU 检测失败，请配置 Worker')
  } finally {
    sauChecking.value = false
  }
}

async function checkSauOne(name: string) {
  try {
    const data = await apiGet<{ platforms?: { platform_name: string; cookie_ok: boolean }[] }>(
      `/publish/video/sau-check?platform_name=${encodeURIComponent(name)}`,
    )
    const row = (data.platforms || [])[0]
    if (row?.cookie_ok) {
      message.success(`${name} Cookie 有效`)
    } else {
      message.warning(`${name} 未登录，请在 Worker 机执行扫码命令`)
    }
    await mergeSauChecks()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '检测失败')
  }
}

async function syncSlot() {
  syncing.value = true
  try {
    const data = await apiPost<{ synced?: string[]; message?: string }>('/publish/video/sync-aitoearn', {})
    message.success(data?.message || `已刷新 ${data?.synced?.length ?? 0} 个代发渠道`)
    await load()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '刷新失败')
  } finally {
    syncing.value = false
  }
}

function emitConnect(p: HubPlatform) {
  emit('connect', { id: p.platform_id, name: p.platform_name })
}

onMounted(load)

defineExpose({ reload: load })
</script>

<style scoped>
.video-bind-hub {
  margin-bottom: 16px;
  padding: 16px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: linear-gradient(135deg, rgb(37 99 235 / 0.04), rgb(14 165 233 / 0.03));
}
.vbh-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.vbh-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}
.vbh-sub {
  margin: 4px 0 0;
  font-size: 13px;
  color: #64748b;
}
.vbh-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}
.vbh-card {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
}
.vbh-card.bound {
  border-color: #86efac;
}
.vbh-card.aito:not(.bound) {
  border-color: #93c5fd;
}
.vbh-card.sau-pending {
  border-color: #fdba74;
}
.vbh-card-top {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  font-size: 13px;
}
.vbh-cap {
  margin: 4px 0 0;
  font-size: 11px;
  color: #94a3b8;
}
.vbh-sau {
  margin-top: 6px;
}
.vbh-sau-account {
  margin: 0;
  font-size: 11px;
  color: #64748b;
}
.vbh-cmd {
  margin: 2px 0 0 !important;
  font-size: 10px;
  word-break: break-all;
}
.vbh-foot {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed #e2e8f0;
}
.mb-3 {
  margin-bottom: 12px;
}
.ml-4 {
  margin-left: 16px;
}
</style>
