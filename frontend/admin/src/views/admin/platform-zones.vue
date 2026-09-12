<template>
  <YdPage title="Platform 三区治理" subtitle="运营 · 商业 · 治理 · 送检开关" surface="elevated">
  <div class="platform-zones">
    <div class="flex flex-wrap gap-4 mb-6 p-4 rounded-xl border bg-slate-50 text-sm">
      <label class="flex items-center gap-2 cursor-pointer">
        <input v-model="certMode" type="checkbox" @change="onCertToggle" />
        <span><strong>送检模式</strong>（侧栏仅鉴定面，默认关 · 录屏送检时再开）</span>
      </label>
      <label class="flex items-center gap-2 cursor-pointer">
        <input v-model="labOpen" type="checkbox" @change="onLabToggle" />
        <span>实验室模块（非送检范围）</span>
      </label>
    </div>

    <p v-if="activeTab === 'lab' && labOpen" class="text-xs text-amber-700 mb-3 px-2 py-1 bg-amber-50 border border-amber-200 rounded-lg">
      非送检范围 · 评测现场请勿演示
    </p>

    <div class="tabs flex gap-2 mb-6 flex-wrap">
      <button
        v-for="t in tabs"
        :key="t.id"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === t.id }"
        @click="activeTab = t.id"
      >
        {{ t.label }}
      </button>
      <button
        type="button"
        class="tab-btn lab"
        :class="{ active: activeTab === 'lab' }"
        @click="toggleLab"
      >
        实验室 {{ labOpen ? '▾' : '▸' }}
      </button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
      <router-link
        v-for="card in visibleCards"
        :key="card.path"
        :to="card.path"
        class="card-link"
      >
        <YdReliefIcon :icon="resolveAntIcon(card.iconKey)" size="md" />
        <div>
          <p class="font-medium text-gray-900">{{ card.title }}</p>
          <p class="text-xs text-gray-500">{{ card.desc }}</p>
        </div>
      </router-link>
    </div>

    <section v-if="readiness" class="mt-8 p-4 rounded-xl border bg-white">
      <h2 class="font-bold text-sm mb-2">P0 彩排就绪度</h2>
      <p class="text-sm" :class="readiness.ready ? 'text-green-600' : 'text-amber-600'">
        {{ readiness.ready ? '关键项已通过' : '存在 fail 项，请先在治理区处理' }}
        （pass {{ readiness.score?.pass }} / warn {{ readiness.score?.warn }} / fail {{ readiness.score?.fail }}）
      </p>
      <button type="button" class="mt-2 text-xs text-primary-600 underline" @click="loadReadiness">刷新</button>
    </section>

    <section v-if="platformAlign" class="mt-4 p-4 rounded-xl border bg-white">
      <div class="flex items-center justify-between gap-2 mb-2">
        <h2 class="font-bold text-sm">40 平台 catalog 对齐（MOD-03 / P2-08）</h2>
        <a-tag :color="platformAlign.aligned ? 'success' : 'warning'">
          {{ platformAlign.aligned ? '已对齐' : '待 seed' }}
        </a-tag>
      </div>
      <p class="text-sm text-gray-600">
        catalog {{ platformAlign.catalog_total }} · DB {{ platformAlign.db_total }}
        · 缺失 {{ platformAlign.missing_count ?? 0 }}
      </p>
      <p v-if="pilotSummary" class="text-xs text-gray-500 mt-1">{{ pilotSummary }}</p>
      <button type="button" class="mt-2 text-xs text-primary-600 underline" @click="loadPlatformAlign">刷新对齐</button>
    </section>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { YdPage, YdReliefIcon } from '@/components/youding'
import { iconNameForPath, resolveAntIcon } from '@/constants/antIconMap'
import { getAuthToken } from '@/utils/api'
import {
  isCertInspectionMode,
  setCertInspectionMode,
  setPlatformLabEnabled,
  isPlatformLabEnabled,
} from '@/constants/stubVisibility'

const activeTab = ref<'ops' | 'biz' | 'gov' | 'lab'>('ops')
const certMode = ref(isCertInspectionMode())
const labOpen = ref(isPlatformLabEnabled())
const readiness = ref<any>(null)
const platformAlign = ref<{
  aligned?: boolean
  catalog_total?: number
  db_total?: number
  missing_count?: number
} | null>(null)
const pilotSummary = ref('')

const tabs = [
  { id: 'ops' as const, label: 'Tab A · 运营' },
  { id: 'biz' as const, label: 'Tab B · 商业' },
  { id: 'gov' as const, label: 'Tab C · 治理' },
]

type ZoneCard = { path: string; title: string; desc: string; iconKey: string }

function zone(path: string, title: string, desc: string): ZoneCard {
  return { path, title, desc, iconKey: iconNameForPath(path) }
}

const cards = {
  ops: [
    zone('/admin/dashboard', '运营看板', '租户与业务大盘'),
    zone('/client/traffic', '流量看板', '访客·点击·询盘归因'),
    zone('/admin/traffic-board', '全平台流量', '租户与代理汇总'),
    zone('/admin/tenants', '租户列表', '套餐与冻结'),
    zone('/admin/file-manager', '产品图片空间', '产品白底图 · 建站复用 · 复制链接'),
    zone('/client/video-space', '租户视频空间', '与图片共用七牛/R2 · tenants/{id}/videos'),
    zone('/inquiries', '询盘大盘', '全站线索'),
    zone('/admin/scheduler-hub', '发布队列', 'Worker / cron'),
  ],
  biz: [
    zone('/admin/finance', '财务概览', '营收与成本'),
    zone('/admin/finance/payment-ops', '支付码与接口', '微信/支付宝探针与回调'),
    zone('/admin/finance/invoices', '开票审核', '租户开票申请'),
    zone('/admin/aggregation', '数据中心', '聚合报表'),
    zone('/referral', '裂变邀请', 'Token / 奖励'),
  ],
  gov: [
    zone('/admin/system', '系统管理', '用户 / 日志 / 配置'),
    zone('/admin/ai-engine/trade-intel', '出海参谋', '规则矩阵种子'),
    zone('/admin/ai-engine', 'AI 引擎', '模型与任务'),
    zone('/admin/demo-rehearsal', '七步彩排', 'P0 演示清单'),
    zone('/system-health', '系统健康', '压测与探针'),
  ],
  lab: [
    zone('/admin/geo-engine', 'GEO 引擎', '实验室'),
    zone('/admin/v2ray', 'V2Ray', '实验室'),
    zone('/agent-hub', '智能体协同', '实验室'),
    zone('/media-factory', '媒体工厂', '实验室'),
  ],
}

const visibleCards = computed(() => {
  if (activeTab.value === 'lab' && labOpen.value) return cards.lab
  if (activeTab.value === 'lab') return []
  return cards[activeTab.value]
})

function toggleLab() {
  if (activeTab.value !== 'lab') {
    activeTab.value = 'lab'
    return
  }
  labOpen.value = !labOpen.value
  onLabToggle()
}

function onCertToggle() {
  setCertInspectionMode(certMode.value)
  window.location.reload()
}

function onLabToggle() {
  setPlatformLabEnabled(labOpen.value)
}

async function loadReadiness() {
  const tk = getAuthToken()
  if (!tk) return
  try {
    const res = await fetch('/api/v1/ops/readiness', {
      headers: { Authorization: `Bearer ${tk}` },
    })
    const body = await res.json()
    readiness.value = body.data || body
  } catch {}
}

async function loadPlatformAlign() {
  const tk = getAuthToken()
  if (!tk) return
  try {
    const [alignRes, pilotRes] = await Promise.all([
      fetch('/api/v1/platforms/catalog/alignment', { headers: { Authorization: `Bearer ${tk}` } }),
      fetch('/api/v1/platforms/pilot', { headers: { Authorization: `Bearer ${tk}` } }),
    ])
    if (alignRes.ok) {
      const body = await alignRes.json()
      platformAlign.value = body.data || body
    }
    if (pilotRes.ok) {
      const body = await pilotRes.json()
      const data = body.data || body
      const gl = data.global?.length ?? 0
      const cn = data.cn?.length ?? 0
      const target = data.target_total ?? 15
      pilotSummary.value = `试点已入库 ${data.total ?? 0}/${target}（国内 ${cn}/5 · 海外十大 ${gl}/10）`
    }
  } catch {
    platformAlign.value = null
    pilotSummary.value = ''
  }
}

onMounted(() => {
  void loadReadiness()
  void loadPlatformAlign()
})
</script>

<style scoped>
.tab-btn {
  padding: 8px 14px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  font-size: 13px;
  color: #475569;
}
.tab-btn.active {
  background: var(--uj-brand, #4a9b8c);
  color: #fff;
  border-color: var(--uj-brand, #4a9b8c);
}
.tab-btn.lab.active {
  background: var(--uj-brand-deep, #2a6b60);
  border-color: var(--uj-brand-deep, #2a6b60);
  color: #fff;
}
.card-link {
  display: flex;
  gap: 12px;
  padding: 14px;
  align-items: center;
  border: 1px solid var(--uj-border-soft, #e2e8f0);
  border-radius: 14px;
  background: var(--uj-glass-bg-strong, rgb(255 255 255 / 0.96));
  transition: border-color 0.15s, box-shadow 0.15s;
}
.card-link:hover {
  border-color: var(--uj-brand, #4a9b8c);
  box-shadow: var(--uj-glass-shadow-hover, 0 8px 24px rgb(45 107 96 / 0.1));
}
</style>
