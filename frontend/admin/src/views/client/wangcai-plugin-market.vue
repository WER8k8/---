/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <div class="market-page">
      <header class="market-header">
        <div>
          <h1 class="text-xl font-bold text-gray-900">旺财插件市场</h1>
          <p class="text-sm text-gray-500 mt-1">
            云端插件在卖货副驾一句话调用；<strong>浏览器伴侣</strong>需在本机 Chrome/Edge 安装，与云端真发互补。
          </p>
        </div>
        <router-link to="/client/copilot" class="link-back">返回卖货副驾</router-link>
      </header>

      <a-alert
        v-if="usagePolicyNotice && aiConnectFreeTier"
        type="warning"
        show-icon
        class="market-ai-connect"
        message="英伟达免费通道 · 客户须知"
      >
        <template #description>
          <p>{{ usagePolicyNotice }}</p>
          <p v-if="probeSummaryLine" class="text-xs text-gray-600 mt-2">{{ probeSummaryLine }}</p>
        </template>
      </a-alert>
      <a-alert
        v-else-if="aiConnectNotice"
        :type="aiConnectAlertType"
        show-icon
        class="market-ai-connect"
        :message="aiConnectAlertTitle"
        :description="aiConnectNotice"
      />

      <section v-if="meta" class="meta-bar">
        <span>共 {{ meta.plugin_count }} 个插件</span>
        <span>已上架 {{ meta.public_count }} 个</span>
        <span>稳定版 {{ meta.stable_count }} 个</span>
      </section>

      <div class="filter-row">
        <button
          v-for="c in categories"
          :key="c"
          type="button"
          class="filter-chip"
          :class="{ active: category === c }"
          @click="setCategory(c)"
        >
          {{ c }}
        </button>
      </div>

      <div class="plugin-grid">
        <article v-for="p in filtered" :key="p.id" class="plugin-card" :class="{ 'plugin-card--browser': p.install_kind === 'local_browser' }">
          <div class="plugin-head">
            <h2 class="font-semibold text-gray-900">{{ p.name }}</h2>
            <span class="tag" :class="'m-' + (p.maturity || 'stable')">{{ maturityLabel(p.maturity) }}</span>
          </div>
          <p v-if="p.install_kind === 'local_browser'" class="text-xs text-amber-700 mt-1">
            🔒 优丁平台专属 · 须从工作台唤起
          </p>
          <p class="text-xs text-indigo-600">{{ p.tagline }}</p>
          <p class="text-sm text-gray-600 mt-2">{{ p.description }}</p>
          <p v-if="p.companion?.recommended_for" class="text-xs text-gray-500 mt-2">
            适合：{{ p.companion.recommended_for }}
          </p>
          <p class="text-xs text-gray-400 mt-2">{{ p.author }} · v{{ p.version }} · {{ p.plan_tier }}</p>
          <p v-if="p.companion?.disclaimer" class="text-xs text-gray-500 mt-2 border-t pt-2">
            {{ p.companion.disclaimer }}
          </p>
          <div class="plugin-actions">
            <template v-if="p.install_kind === 'local_browser'">
              <button
                type="button"
                class="btn-primary"
                @click="openCompanionWorkbench(p)"
              >
                在优丁工作台使用
              </button>
              <a
                v-if="p.companion?.install?.chrome"
                :href="p.companion.install.chrome"
                target="_blank"
                rel="noopener"
                class="btn-run"
              >首次安装扩展</a>
              <button
                v-if="!p.installed"
                type="button"
                class="btn-run"
                :disabled="busyId === p.id"
                @click="install(p)"
              >
                收藏到市场
              </button>
              <label v-else class="toggle">
                <input
                  type="checkbox"
                  :checked="p.enabled"
                  :disabled="busyId === p.id"
                  @change="toggle(p, ($event.target as HTMLInputElement).checked)"
                />
                已收藏
              </label>
            </template>
            <template v-else>
              <button
                v-if="!p.installed"
                type="button"
                class="btn-primary"
                :disabled="busyId === p.id"
                @click="install(p)"
              >
                安装
              </button>
              <template v-else>
                <label class="toggle">
                  <input
                    type="checkbox"
                    :checked="p.enabled"
                    :disabled="busyId === p.id"
                    @change="toggle(p, ($event.target as HTMLInputElement).checked)"
                  />
                  已启用
                </label>
                <button
                  type="button"
                  class="btn-run"
                  :disabled="busyId === p.id || !p.enabled"
                  @click="runPlugin(p)"
                >
                  试运行
                </button>
              </template>
            </template>
          </div>
        </article>
      </div>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { getAuthToken } from '@/utils/api'
import { useAiConnect } from '@/composables/useAiConnect'

const route = useRoute()
const router = useRouter()

const {
  notice: aiConnectNotice,
  freeTier: aiConnectFreeTier,
  alertType: aiConnectAlertType,
  alertTitle: aiConnectAlertTitle,
  usagePolicyNotice,
  probeSummaryLine,
  refresh: refreshAiConnect,
} = useAiConnect()

type CompanionInstall = {
  chrome?: string
  edge?: string
  website?: string
  github?: string
  guide?: string
}

type PluginItem = {
  id: string
  name: string
  tagline?: string
  description?: string
  category?: string
  version?: string
  author?: string
  maturity?: string
  plan_tier?: string
  installed?: boolean
  enabled?: boolean
  install_kind?: 'local_browser' | 'server'
  platform_exclusive?: boolean
  launch_route?: string
  companion?: {
    content_types?: string[]
    platforms?: string[]
    install?: CompanionInstall
    disclaimer?: string
    recommended_for?: string
    launch_route?: string
  }
}

const items = ref<PluginItem[]>([])
const meta = ref<Record<string, number> | null>(null)
const category = ref('全部')
const busyId = ref('')

const categories = computed(() => {
  const set = new Set<string>(['全部'])
  items.value.forEach((p) => {
    if (p.category) set.add(p.category)
  })
  return [...set]
})

const filtered = computed(() => {
  if (category.value === '全部') return items.value
  return items.value.filter((p) => p.category === category.value)
})

function setCategory(c: string) {
  category.value = c
  const q = c === '全部' ? {} : { category: c }
  router.replace({ query: q })
}

const COMPANION_LAUNCH_KEY = 'youding_companion_launch'

function openCompanionWorkbench(p: PluginItem) {
  sessionStorage.setItem(
    COMPANION_LAUNCH_KEY,
    JSON.stringify({ ts: Date.now(), companion: p.id }),
  )
  const launch = p.launch_route || p.companion?.launch_route || '/admin/ai-center/browser-companion'
  router.push({
    path: launch,
    query: { from: 'youding', companion: p.id },
  })
}

function authHeaders(): Record<string, string> {
  const tk = getAuthToken()
  return tk ? { Authorization: `Bearer ${tk}` } : {}
}

function maturityLabel(m?: string) {
  if (m === 'partial') return '试点'
  if (m === 'beta') return 'Beta'
  return '稳定'
}

async function loadMarket() {
  const q = category.value !== '全部' ? `?category=${encodeURIComponent(category.value)}` : ''
  const res = await fetch(`/api/v1/wangcai/plugins/marketplace${q}`, { headers: authHeaders() })
  const body = await res.json()
  const data = body.data || body
  items.value = data.items || []
  meta.value = data.meta || null
}

async function install(p: PluginItem) {
  busyId.value = p.id
  try {
    const res = await fetch(`/api/v1/wangcai/plugins/${p.id}/install`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ enabled: true }),
    })
    const body = await res.json()
    if (!res.ok) throw new Error(body.message || '安装失败')
    message.success(p.install_kind === 'local_browser' ? `已收藏：${p.name}` : `已安装：${p.name}`)
    await loadMarket()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '安装失败')
  } finally {
    busyId.value = ''
  }
}

async function toggle(p: PluginItem, enabled: boolean) {
  busyId.value = p.id
  try {
    const res = await fetch(`/api/v1/wangcai/plugins/${p.id}/enabled`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ enabled }),
    })
    const body = await res.json()
    if (!res.ok) throw new Error(body.message || '更新失败')
    p.enabled = enabled
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '更新失败')
    await loadMarket()
  } finally {
    busyId.value = ''
  }
}

async function runPlugin(p: PluginItem) {
  busyId.value = p.id
  try {
    const msg =
      p.id === 'sales_flywheel_loop'
        ? '跑一轮市场研究并自动找客'
        : `请使用【${p.name}】能力帮我处理当前租户业务`
    const res = await fetch(`/api/v1/wangcai/plugins/${p.id}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ message: msg }),
    })
    const body = await res.json()
    const data = body.data || body
    if (!res.ok) throw new Error(body.message || '执行失败')
    message.success((data.reply as string)?.slice(0, 120) || '插件已执行，请到卖货副驾查看详情')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '执行失败')
  } finally {
    busyId.value = ''
  }
}

onMounted(() => {
  const qCat = route.query.category
  if (typeof qCat === 'string' && qCat.trim()) {
    category.value = qCat.trim()
  }
  void loadMarket()
  void refreshAiConnect()
})

watch(
  () => route.query.category,
  (v) => {
    if (typeof v === 'string' && v.trim() && v !== category.value) {
      category.value = v.trim()
      void loadMarket()
    }
  },
)
</script>

<style scoped>
.market-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 1rem;
}
.market-ai-connect {
  margin-bottom: 1rem;
}
.market-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}
.link-back {
  font-size: 0.875rem;
  color: #4f46e5;
  white-space: nowrap;
}
.meta-bar {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.75rem;
}
.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.filter-chip {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  border: 1px solid #e5e7eb;
  font-size: 0.75rem;
  background: #fff;
}
.filter-chip.active {
  background: #eef2ff;
  border-color: #818cf8;
  color: #4338ca;
}
.plugin-grid {
  display: grid;
  gap: 1rem;
}
@media (min-width: 768px) {
  .plugin-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
.plugin-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  background: #fff;
}
.plugin-card--browser {
  border-color: #fcd34d;
  background: #fffbeb;
}
.plugin-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}
.tag {
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  background: #ecfdf5;
  color: #047857;
}
.tag.m-partial {
  background: #fffbeb;
  color: #b45309;
}
.plugin-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.75rem;
}
.btn-primary,
.btn-run {
  font-size: 0.8rem;
  padding: 0.35rem 0.85rem;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
}
.btn-primary {
  background: #4f46e5;
  color: #fff;
}
.btn-run {
  background: #f3f4f6;
  color: #111827;
}
.toggle {
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
</style>
