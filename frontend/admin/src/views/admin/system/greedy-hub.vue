<template>
  <YdPage title="摸金校尉总控" subtitle="全球累计 · 大赛 · 耐力赛 · 搞钱闭环 · Survival 真钱" surface="elevated">
    <template #actions>
      <a-space wrap>
        <a-button type="primary" :loading="runningLoop" @click="runLoop">跑一轮闭环</a-button>
        <a-button :loading="sendingDigest" @click="pushDigest">飞书周报</a-button>
        <a-button :loading="loading" @click="load">刷新</a-button>
      </a-space>
    </template>

    <a-alert v-if="gateError" type="warning" show-icon :message="gateError" class="mb-3" />

    <template v-else-if="hub">
      <div class="stat-row">
        <a-statistic title="本周全球" :value="weekCny" prefix="¥" :precision="2" />
        <a-statistic title="本月" :value="monthCny" prefix="¥" :precision="2" />
        <a-statistic title="今日实收" :value="todayCny" prefix="¥" :precision="2" />
        <a-statistic title="runway" :value="runwayDays" suffix="天" />
        <a-statistic title="L4 队列" :value="queueDepth" />
        <a-statistic title="protected" :value="protectedCount" />
      </div>

      <a-row :gutter="12" class="mb-3">
        <a-col :xs="24" :md="8">
          <a-card size="small" title="打江山人格">
            <a-tag :color="moodColor(personality.mood)">{{ moodLabel(personality.mood) }}</a-tag>
            <div class="meta">{{ personality.line || '—' }}</div>
            <router-link to="/admin/system/greedy-cumulative">累计看板 →</router-link>
          </a-card>
        </a-col>
        <a-col :xs="24" :md="8">
          <a-card size="small" title="7×24 耐力赛">
            <div class="meta">{{ arenaLabel }}</div>
            <div class="meta">距轮转 {{ daysUntilRollover }} 天</div>
            <router-link to="/admin/system/greedy-contest-leaderboard">挣钱大赛 →</router-link>
          </a-card>
        </a-col>
        <a-col :xs="24" :md="8">
          <a-card size="small" title="搞钱闭环">
            <div class="meta">队列深度 {{ queueDepth }}</div>
            <div class="meta">调度 {{ loopSchedulerOn ? 'ON' : 'OFF' }}</div>
            <router-link to="/admin/system/greedy-publish-queue">L4 发布队列 →</router-link>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="12" class="mb-3">
        <a-col :xs="24" :lg="12">
          <a-card size="small" title="生产就绪">
            <a-alert
              :type="readinessReady ? 'success' : 'warning'"
              show-icon
              :message="readinessReady ? 'required 项已通过' : '存在未满足项，上线前请核对'"
              class="mb-2"
            />
            <div v-if="readiness?.publish_tenant_id" class="meta">
              发布租户 {{ readiness.publish_tenant_domain }} · {{ readiness.publish_tenant_id }}
            </div>
            <a-list size="small" :data-source="readinessChecks" bordered class="mb-2">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-tag :color="item.ok ? 'success' : severityColor(item.severity)">
                    {{ item.ok ? 'OK' : '—' }}
                  </a-tag>
                  <span class="check-msg">{{ item.message }}</span>
                </a-list-item>
              </template>
            </a-list>
            <a-space wrap>
              <a-button size="small" :loading="bootstrapping" @click="runBootstrap">Bootstrap 自营租户</a-button>
              <a-button size="small" :loading="loadingReadiness" @click="loadReadiness">刷新清单</a-button>
            </a-space>
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="12">
          <a-card size="small" title="快捷入口">
            <a-space wrap>
              <router-link to="/admin/system/survival-dashboard"><a-button>Survival 台账</a-button></router-link>
              <router-link to="/admin/system/greedy-expert-memory"><a-button>专家记忆</a-button></router-link>
              <router-link to="/admin/system/greedy-contest-leaderboard"><a-button>大赛榜</a-button></router-link>
              <router-link to="/admin/system/publish-history"><a-button>发布历史</a-button></router-link>
            </a-space>
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="12">
          <a-card size="small" title="大赛 Top3">
            <a-list size="small" :data-source="top3" bordered>
              <template #renderItem="{ item, index }">
                <a-list-item>{{ index + 1 }}. {{ item.name || item.role_id }} · {{ item.score_arena || item.total_score || 0 }}</a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>
      </a-row>

      <a-card size="small" title="摸金 PublishTask（L4 审核后）" class="mb-3">
        <a-table
          :data-source="publishTasks"
          :columns="taskCols"
          row-key="id"
          size="small"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag>{{ record.status }}</a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-button v-if="record.status === 'failed'" size="small" @click="retryTask(record.id)">重试</a-button>
            </template>
          </template>
        </a-table>
      </a-card>

      <a-card size="small" title="最近 survival 入账">
        <a-table :data-source="recentEntries" :columns="entryCols" row-key="id" size="small" :pagination="false" />
      </a-card>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import {
  bootstrapGreedyTenant,
  fetchGreedyHub,
  fetchGreedyReadiness,
  moodColor,
  moodLabel,
  retryPublishTask,
  runGreedyRevenueLoop,
  sendGreedyDigest,
  type GreedyReadiness,
} from '@/api/hermesGreedy'

const loading = ref(false)
const loadingReadiness = ref(false)
const bootstrapping = ref(false)
const runningLoop = ref(false)
const sendingDigest = ref(false)
const gateError = ref('')
const hub = ref<Record<string, unknown> | null>(null)
const readiness = ref<GreedyReadiness | null>(null)

const cumulative = computed(() => (hub.value?.cumulative as Record<string, unknown>) || {})
const display = computed(() => (cumulative.value.display as Record<string, number>) || {})
const personality = computed(() => (cumulative.value.personality as Record<string, string>) || {})
const contest = computed(() => (hub.value?.contest as Record<string, unknown>) || {})
const endurance = computed(() => (hub.value?.endurance as Record<string, unknown>) || {})
const survival = computed(() => (hub.value?.survival as Record<string, unknown>) || {})
const pulse = computed(() => (survival.value.pulse as Record<string, unknown>) || {})
const publishQueue = computed(() => (hub.value?.publish_queue as Record<string, unknown>) || {})
const survivalTasks = computed(() => (hub.value?.survival_publish_tasks as Record<string, unknown>) || {})
const revenueLoop = computed(() => (hub.value?.revenue_loop as Record<string, unknown>) || {})

const weekCny = computed(() => Number(display.value.week_cny ?? 0))
const monthCny = computed(() => Number(display.value.month_cny ?? 0))
const todayCny = computed(() => Number(pulse.value.settled_today_display_cny ?? 0))
const runwayDays = computed(() => Number(pulse.value.runway_days ?? 0))
const queueDepth = computed(() => Number(publishQueue.value.depth ?? 0))
const protectedCount = computed(() => Number(contest.value.protected_count ?? 0))
const top3 = computed(() => ((contest.value.top5 as Record<string, unknown>[]) || []).slice(0, 3))
const publishTasks = computed(() => (survivalTasks.value.items as Record<string, unknown>[]) || [])
const recentEntries = computed(() => (survival.value.recent_entries as Record<string, unknown>[]) || [])
const arenaLabel = computed(() => {
  const a = (endurance.value.current_arena as Record<string, unknown>) || {}
  return String(a.label || a.arena_id || '当前擂台')
})
const daysUntilRollover = computed(() => Number(endurance.value.days_until_rollover ?? 0))
const loopSchedulerOn = computed(() => {
  const s = (revenueLoop.value.scheduler as Record<string, unknown>) || {}
  return Boolean(s.running)
})

const hubReadiness = computed(() => (hub.value?.production_readiness as GreedyReadiness) || null)
const readinessReady = computed(() => Boolean(readiness.value?.ready ?? hubReadiness.value?.ready))
const readinessChecks = computed(() => {
  const checks = readiness.value?.checks ?? hubReadiness.value?.checks ?? []
  return [...checks].sort((a, b) => severityRank(a.severity) - severityRank(b.severity))
})

function severityRank(severity?: string): number {
  if (severity === 'required') return 0
  if (severity === 'recommended') return 1
  return 2
}

function severityColor(severity?: string): string {
  if (severity === 'required') return 'error'
  if (severity === 'recommended') return 'warning'
  return 'default'
}

const taskCols = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '平台', dataIndex: 'platform_name', key: 'platform_name', width: 100 },
  { title: '状态', key: 'status', width: 90 },
  { title: '更新', dataIndex: 'updated_at', key: 'updated_at', width: 170 },
  { title: '操作', key: 'actions', width: 80 },
]

const entryCols = [
  { title: '渠道', dataIndex: 'channel', key: 'channel', width: 120 },
  { title: '金额(分)', dataIndex: 'amount_base_minor', key: 'amount_base_minor', width: 100 },
  { title: '币种', dataIndex: 'currency', key: 'currency', width: 60 },
  { title: '时间', dataIndex: 'recorded_at', key: 'recorded_at', width: 170 },
]

async function load() {
  loading.value = true
  gateError.value = ''
  try {
    hub.value = await fetchGreedyHub()
    readiness.value = (hub.value?.production_readiness as GreedyReadiness) || readiness.value
  } catch (e: unknown) {
    const msg = (e as Error).message || '加载失败'
    const isRouteMissing = /not found|404/i.test(msg)
    gateError.value =
      isRouteMissing
        ? '摸金总控接口未就绪，请重启本地 API（scripts/start-dev-admin.ps1）后刷新'
        : msg.includes('503') || msg.includes('greedy')
          ? msg
          : ''
    if (!gateError.value) message.error(msg)
  } finally {
    loading.value = false
  }
}

async function loadReadiness() {
  loadingReadiness.value = true
  try {
    readiness.value = await fetchGreedyReadiness()
  } catch (e: unknown) {
    message.error((e as Error).message || '就绪清单加载失败')
  } finally {
    loadingReadiness.value = false
  }
}

async function runBootstrap() {
  bootstrapping.value = true
  try {
    const out = await bootstrapGreedyTenant(true)
    const tid = out.tenant?.tenant_id
    message.success(tid ? `已 bootstrap 租户 ${tid}` : 'Bootstrap 完成')
    await load()
    await loadReadiness()
  } catch (e: unknown) {
    message.error((e as Error).message || 'Bootstrap 失败')
  } finally {
    bootstrapping.value = false
  }
}

async function runLoop() {
  runningLoop.value = true
  try {
    await runGreedyRevenueLoop({ locale: 'global', survival_goal_cny: 1000 })
    message.success('搞钱闭环已在后台启动')
  } catch (e: unknown) {
    message.error((e as Error).message || '启动失败')
  } finally {
    runningLoop.value = false
  }
}

async function pushDigest() {
  sendingDigest.value = true
  try {
    await sendGreedyDigest()
    message.success('飞书周报已推送')
  } catch (e: unknown) {
    message.error((e as Error).message || '推送失败')
  } finally {
    sendingDigest.value = false
  }
}

async function retryTask(id: string) {
  try {
    await retryPublishTask(id)
    message.success('已重试')
    await load()
  } catch (e: unknown) {
    message.error((e as Error).message || '重试失败')
  }
}

onMounted(load)
</script>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}
.mb-3 {
  margin-bottom: 12px;
}
.meta {
  color: rgba(0, 0, 0, 0.65);
  margin: 8px 0;
  font-size: 13px;
}
.check-msg {
  margin-left: 8px;
  font-size: 12px;
}
</style>
