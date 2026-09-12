<template>
  <YdPage title="摸金累计看板" subtitle="全球周/月/年累计 · 打江山人格 · 比上次更强" surface="elevated">
    <template #actions>
      <a-space wrap>
        <router-link to="/admin/system/greedy-contest-leaderboard">
          <a-button>挣钱大赛</a-button>
        </router-link>
        <router-link to="/admin/system/greedy-publish-queue">
          <a-button>L4 发布队列</a-button>
        </router-link>
        <a-button :loading="sendingDigest" @click="pushDigest">推送飞书周报</a-button>
        <a-button type="primary" :loading="runningLoop" @click="runLoop">跑一轮搞钱闭环</a-button>
        <a-button :loading="loading" @click="load">刷新</a-button>
      </a-space>
    </template>

    <a-alert
      v-if="gateError"
      type="warning"
      show-icon
      message="摸金校尉未启用"
      :description="gateError"
      class="mb-3"
    />

    <template v-else-if="data">
      <div class="stat-row">
        <a-statistic title="本周累计" :value="display.week_cny ?? 0" prefix="¥" :precision="2" />
        <a-statistic title="本月累计" :value="display.month_cny ?? 0" prefix="¥" :precision="2" />
        <a-statistic title="今年累计" :value="display.year_cny ?? 0" prefix="¥" :precision="2" />
        <a-statistic title="终身累计" :value="display.lifetime_cny ?? 0" prefix="¥" :precision="2" />
      </div>

      <a-card size="small" title="打江山人格" class="mb-3">
        <a-space direction="vertical" style="width: 100%">
          <div>
            <a-tag :color="moodColor(personality.mood)">{{ moodLabel(personality.mood) }}</a-tag>
            <span class="personality-line">{{ personality.line }}</span>
          </div>
          <a-descriptions :column="2" size="small">
            <a-descriptions-item label="代号">{{ personality.codename || '摸金打江山' }}</a-descriptions-item>
            <a-descriptions-item label="对比上次">{{ vsLastLabel }}</a-descriptions-item>
            <a-descriptions-item label="上次结算">¥{{ display.prev_settlement_cny ?? 0 }}</a-descriptions-item>
            <a-descriptions-item label="本次结算">¥{{ display.last_settlement_cny ?? 0 }}</a-descriptions-item>
            <a-descriptions-item label="周期">{{ data.week_key }} · {{ data.month_key }} · {{ data.year_key }}</a-descriptions-item>
            <a-descriptions-item label="结算次数">{{ data.settlements_count ?? 0 }}</a-descriptions-item>
          </a-descriptions>
        </a-space>
      </a-card>

      <a-row :gutter="12">
        <a-col :xs="24" :lg="12">
          <a-card size="small" title="7×24 耐力赛">
            <template v-if="endurance">
              <div class="meta">擂台：{{ arenaLabel }}</div>
              <div class="meta">距轮转 {{ endurance.days_until_rollover ?? '—' }} 天</div>
              <div class="meta">已完成 {{ endurance.total_arenas_completed ?? 0 }} 轮</div>
            </template>
            <div v-else class="meta">—</div>
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="12">
          <a-card size="small" title="全球收入策略">
            <div class="meta">{{ globalNote }}</div>
            <a-tag color="green">scope: unrestricted</a-tag>
          </a-card>
        </a-col>
      </a-row>

      <a-card v-if="digestPreview" size="small" title="飞书周报预览" class="mt-3">
        <pre class="digest-pre">{{ digestPreview.body_md }}</pre>
      </a-card>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import {
  fetchGreedyCumulative,
  fetchGreedyDigestPreview,
  fetchGreedyEndurance,
  sendGreedyDigest,
  runGreedyRevenueLoop,
  moodColor,
  moodLabel,
  type GreedyCumulative,
  type GreedyDigestPreview,
} from '@/api/hermesGreedy'

const loading = ref(false)
const sendingDigest = ref(false)
const runningLoop = ref(false)
const gateError = ref('')
const data = ref<GreedyCumulative | null>(null)
const endurance = ref<Record<string, unknown> | null>(null)
const digestPreview = ref<GreedyDigestPreview | null>(null)

const display = computed(() => (data.value?.display || {}) as Record<string, number | undefined>)
const personality = computed(
  () =>
    (data.value?.personality || {}) as {
      mood?: string
      line?: string
      codename?: string
      vs_last?: string
    },
)
const vsLastLabel = computed(() => {
  const v = personality.value.vs_last
  if (v === 'stronger') return '比上次更强 ↑'
  if (v === 'weaker') return '比上次更少 ↓'
  if (v === 'same') return '持平'
  return '—'
})
const arenaLabel = computed(() => {
  const arena = (endurance.value?.current_arena as Record<string, unknown>) || {}
  return String(arena.label || arena.arena_id || '当前擂台')
})
const globalNote = computed(
  () => data.value?.global_revenue_policy?.markets_note || 'CNY/USD/EUR 等凡入账 survival 均计 global'
)

async function load() {
  loading.value = true
  gateError.value = ''
  try {
    const [cum, end, digest] = await Promise.all([
      fetchGreedyCumulative(),
      fetchGreedyEndurance().catch(() => null),
      fetchGreedyDigestPreview().catch(() => null),
    ])
    data.value = cum
    endurance.value = end
    digestPreview.value = digest
  } catch (e: unknown) {
    const msg = (e as Error).message || '加载失败'
    if (msg.includes('503') || msg.includes('未启用') || msg.includes('greedy')) {
      gateError.value = msg
    } else {
      message.error(msg)
    }
  } finally {
    loading.value = false
  }
}

async function pushDigest() {
  sendingDigest.value = true
  try {
    await sendGreedyDigest()
    message.success('Survival 周报已推送飞书')
  } catch (e: unknown) {
    message.error((e as Error).message || '推送失败')
  } finally {
    sendingDigest.value = false
  }
}

async function runLoop() {
  runningLoop.value = true
  try {
    await runGreedyRevenueLoop({ locale: 'global', survival_goal_cny: 1000 })
    message.success('搞钱闭环已在后台启动（约 1–3 分钟），完成后点刷新')
  } catch (e: unknown) {
    message.error((e as Error).message || '启动失败')
  } finally {
    runningLoop.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.mb-3 {
  margin-bottom: 12px;
}
.mt-3 {
  margin-top: 12px;
}
.meta {
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 6px;
}
.personality-line {
  margin-left: 8px;
}
.digest-pre {
  white-space: pre-wrap;
  font-size: 12px;
  margin: 0;
  max-height: 280px;
  overflow: auto;
}
</style>
