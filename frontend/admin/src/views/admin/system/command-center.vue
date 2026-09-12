<template>
  <YdPage title="超管司令部" subtitle="L0 作战态势 · Hermes 巡站 · DeerFlow 研究 · SEO · 视频矩阵" surface="elevated">
    <template #actions>
      <a-space wrap>
        <a-button :loading="loading" @click="() => loadSnapshot({ force: true })">刷新</a-button>
        <a-button type="primary" :loading="runningOps" @click="runHermesOps">Hermes 运维循环</a-button>
        <a-button :loading="runningDeerflow" @click="runDeerflow">DeerFlow 研究+队列</a-button>
        <a-button :loading="runningRankGuard" @click="runRankGuard">Rank Guard</a-button>
        <a-button :loading="runningInclusion" @click="runInclusionRecheck">收录复检</a-button>
        <router-link to="/admin/system/ecc-hangar">
          <a-button>ECC 机库</a-button>
        </router-link>
        <router-link to="/admin/system/deerflow-monitor">
          <a-button>DeerFlow 队列</a-button>
        </router-link>
        <router-link to="/admin/system/publish-history">
          <a-button>发布历史</a-button>
        </router-link>
        <router-link to="/admin/system/rank-scheduler">
          <a-button>Rank Scheduler</a-button>
        </router-link>
        <router-link to="/admin/system/greedy-hub">
          <a-button>摸金总控</a-button>
        </router-link>
        <router-link to="/admin/system/greedy-cumulative">
          <a-button>摸金累计</a-button>
        </router-link>
        <router-link to="/admin/system/greedy-contest-leaderboard">
          <a-button>挣钱大赛</a-button>
        </router-link>
        <router-link to="/admin/system/greedy-publish-queue">
          <a-button>L4 发布队列</a-button>
        </router-link>
        <router-link to="/admin/system/survival-dashboard">
          <a-button>Survival 台账</a-button>
        </router-link>
        <router-link to="/admin/system/greedy-expert-memory">
          <a-button>专家记忆</a-button>
        </router-link>
      </a-space>
    </template>

    <a-alert
      v-if="loading && !snap"
      type="info"
      show-icon
      class="cc-tip"
      message="正在加载司令部"
      description="云端通常 1 秒内（Redis 预热缓存）；首次或点「刷新」强制更新时约 10–15 秒，请稍候。"
    />

    <a-alert
      v-if="loadError"
      type="error"
      show-icon
      class="cc-tip"
      :message="loadError"
      description="若刚启动后端，请等 30 秒后点「刷新」。仍失败再运行 scripts/start-dev-admin.ps1 -ForceRestart。"
    />

    <a-alert
      type="info"
      show-icon
      class="cc-tip"
      message="绿色/蓝色按钮说明"
      description="「Hermes 运维循环」「DeerFlow 研究+队列」为重型任务，已在后台执行（约 1–3 分钟），点一次即可，完成后点「刷新」。Rank Guard / 收录复检 通常几秒内完成。"
    />

    <div v-if="snap" class="cc-grid">
      <a-card size="small" title="作战态势">
        <a-tag :color="statusColor(snap.overall_status)">{{ snap.overall_status }}</a-tag>
        <div class="cc-meta">定位：{{ snap.positioning }}</div>
        <div v-if="opsSavedAt" class="cc-meta">最近运维：{{ opsSavedAt }}</div>
      </a-card>

      <a-card size="small" title="服务器配置状态">
        <div class="cc-meta cc-readonly-hint">只读展示 · 需在服务器 <code>.env</code> 修改后重启 backend，此处不可点击切换</div>
        <a-descriptions :column="1" size="small" class="mt-2">
          <a-descriptions-item v-for="row in configFlagRows" :key="row.key" :label="row.label">
            <a-tag :color="row.tagColor">{{ row.display }}</a-tag>
            <span v-if="row.hint" class="cc-flag-hint">{{ row.hint }}</span>
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <a-card size="small" title="Hermes 巡站">
        <div class="cc-stat-row">
          <span>通过 {{ patrolPass }}</span>
          <span>警告 {{ patrolWarn }}</span>
          <span>失败 {{ patrolFail }}</span>
        </div>
        <a-list size="small" :data-source="patrolProbes" bordered>
          <template #renderItem="{ item }">
            <a-list-item>
              <a-tag :color="probeColor(item.status)">{{ item.status }}</a-tag>
              {{ item.title }}
            </a-list-item>
          </template>
        </a-list>
      </a-card>

      <a-card size="small" title="DeerFlow 队列">
        <a-descriptions :column="2" size="small">
          <a-descriptions-item v-for="(v, k) in deerflowCounts" :key="k" :label="k">{{ v }}</a-descriptions-item>
        </a-descriptions>
        <div class="cc-meta">调度：{{ deerflowSchedulerEnabled ? '启用' : '关闭' }}</div>
      </a-card>

      <a-card size="small" title="SEO 雷达">
        <div class="cc-meta">排名调度：{{ snap.seo?.rank_scheduler_enabled ? '已配置' : '未开' }}</div>
        <div v-if="snap.seo?.rank_scheduler_ops" class="cc-stat-row">
          <span>DB 词 {{ snap.seo.rank_scheduler_ops.db_keyword_count ?? 0 }}</span>
          <span>追踪 {{ snap.seo.rank_scheduler_ops.scheduler?.tracked_count ?? 0 }}</span>
        </div>
        <div v-if="snap.seo?.seo_matrix_db" class="cc-meta mt-2">
          <a-tag :color="snap.seo.seo_matrix_db.reachable ? 'green' : 'default'">
            SEO 矩阵库 · {{ snap.seo.seo_matrix_db.mode || 'none' }}
            · {{ snap.seo.seo_matrix_db.reachable ? '可达' : '未配/不可达' }}
          </a-tag>
        </div>
        <div v-if="snap.seo?.inclusion" class="cc-stat-row">
          <span>收录 {{ snap.seo.inclusion.included }}/{{ snap.seo.inclusion.total }}</span>
          <span>失败 {{ snap.seo.inclusion.failed }}</span>
          <span>率 {{ snap.seo.inclusion.inclusion_rate }}%</span>
        </div>
        <div v-if="rankGuard" class="cc-meta mt-2">
          <a-tag :color="rankGuard.passed ? 'green' : 'red'">
            Rank Guard · {{ rankGuard.passed ? '通过' : '拦截' }}
          </a-tag>
          <span v-if="rankGuard.checked_at"> · {{ rankGuard.checked_at.slice(0, 16) }}</span>
        </div>
        <ul v-if="rankGuard?.blocked_reasons?.length" class="cc-reasons">
          <li v-for="r in rankGuard.blocked_reasons" :key="r">{{ r }}</li>
        </ul>
        <router-link to="/seo-matrix/dashboard">进入 SEO 矩阵 →</router-link>
      </a-card>

      <a-card size="small" title="AI 机库">
        <a-tag :color="aiReady ? 'green' : 'orange'">{{ aiReady ? 'Key 就绪' : '未配置 Key' }}</a-tag>
        <div class="cc-meta">提供商：{{ (snap.ai_hangar?.providers || []).join('、') || '—' }}</div>
        <div class="cc-stat-row">
          <span>场景健康 {{ aiHealth.healthy }}/{{ aiHealth.total }}</span>
          <span v-if="aiHealth.unhealthy">异常 {{ aiHealth.unhealthy }}</span>
        </div>
        <router-link to="/admin/ai-center">AI 中心 →</router-link>
      </a-card>

      <a-card size="small" title="AI 场景分流 (RADAR-07)">
        <div class="cc-meta">
          雷达 LLM：{{ aiLane.radar_07?.ecc_llm_scenario }} → {{ aiLane.radar_07?.resolved_ops_scenario }}
        </div>
        <div class="cc-meta">
          Ops 默认 {{ aiLane.lanes?.ops?.default }} · Customer 默认 {{ aiLane.lanes?.customer?.default }}
        </div>
      </a-card>

      <a-card size="small" title="飞轮管线">
        <div class="cc-stat-row">
          <span>洞察 {{ flywheelStats.insight_total }}</span>
          <span>编排 {{ flywheelStats.pipeline_total }}</span>
        </div>
        <a-list v-if="flywheelRecent.length" size="small" :data-source="flywheelRecent" bordered>
          <template #renderItem="{ item }">
            <a-list-item>
              <a-tag>{{ item.status }}</a-tag>
              {{ String(item.tenant_id).slice(0, 8) }}…
            </a-list-item>
          </template>
        </a-list>
      </a-card>

      <a-card size="small" title="租户套餐 · DeerFlow">
        <div class="cc-stat-row">
          <span>合格 {{ tenantPlans.eligible_count }}</span>
          <span>跳过 {{ tenantPlans.skipped_count }}</span>
        </div>
        <div class="cc-meta">套餐：{{ (tenantPlans.schedule_plan_codes || []).join(', ') }}</div>
        <div class="cc-meta">月配额 {{ tenantPlans.monthly_limit_per_tenant }}/租户</div>
        <div class="cc-meta">自动入队：{{ tenantPlans.auto_enqueue ? '开' : '关' }}</div>
      </a-card>

      <a-card size="small" title="集成栈 (n8n/Mem0)">
        <a-descriptions :column="1" size="small">
          <a-descriptions-item label="n8n">
            {{ integrations.n8n?.configured ? '已配置 Secret' : '未配置' }}
          </a-descriptions-item>
          <a-descriptions-item label="Mem0">
            {{ integrations.mem0?.configured ? '已配置' : '未配置' }}
          </a-descriptions-item>
          <a-descriptions-item label="PostHog">
            {{ integrations.posthog?.configured ? '已配置' : '未配置' }}
          </a-descriptions-item>
          <a-descriptions-item label="DeerFlow 旁路">
            <a-tag :color="sidecarHealthy ? 'green' : 'default'">
              {{ sidecarConfigured ? (sidecarHealthy ? '健康' : '不可达') : '未配置' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
        <a-button size="small" class="mt-2" :loading="runningMem0" @click="runMem0Sync">Mem0 双写最近洞察</a-button>
      </a-card>

      <a-card size="small" title="DeerFlow SLO">
        <div class="cc-stat-row">
          <span>失败率 {{ ((deerflowSlo.failure_rate || 0) * 100).toFixed(1) }}%</span>
          <span>排队 {{ deerflowSlo.avg_queue_seconds ?? '—' }}s</span>
        </div>
        <router-link to="/admin/system/deerflow-monitor">队列明细 →</router-link>
      </a-card>

      <a-card size="small" title="RUM 性能">
        <div class="cc-meta">样本 {{ rum.sample_count ?? 0 }} · {{ rum.source || '—' }}</div>
        <div class="cc-stat-row">
          <span>LCP {{ rum.lcp_ms ?? '—' }}ms</span>
          <span>INP {{ rum.inp_ms ?? '—' }}ms</span>
        </div>
      </a-card>

      <a-card size="small" title="最近发布" class="cc-wide">
        <a-list v-if="recentPublish.length" size="small" :data-source="recentPublish" bordered>
          <template #renderItem="{ item }">
            <a-list-item>
              <a-tag>{{ item.channel }}</a-tag>
              {{ item.title }} · {{ item.status }}
            </a-list-item>
          </template>
        </a-list>
        <router-link to="/admin/system/publish-history">全部历史 →</router-link>
      </a-card>

      <a-card size="small" title="巡站 7 日趋势" class="cc-wide">
        <div v-for="t in patrolTrend" :key="t.at" class="cc-meta">
          {{ String(t.at).slice(0, 16) }} · pass {{ t.pass }} / warn {{ t.warn }} / fail {{ t.fail }}
        </div>
      </a-card>

      <a-card size="small" title="视频 Worker">
        <a-tag :color="videoReady ? 'green' : 'orange'">{{ videoReady ? '就绪' : '未就绪' }}</a-tag>
        <a-list size="small" :data-source="videoWorkerRows" bordered class="mt-2">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-tag :color="item.enabled ? 'green' : 'default'">{{ item.enabled ? 'ON' : 'OFF' }}</a-tag>
              {{ item.name }}
            </a-list-item>
          </template>
        </a-list>
        <router-link to="/media-factory/render-queue">渲染队列 →</router-link>
      </a-card>

      <a-card size="small" title="技术雷达（最近）" class="cc-wide">
        <div class="cc-meta">高影响 {{ techHighImpact }} · 专家否决 {{ techExpertFail }}</div>
        <a-list v-if="techCandidates.length" size="small" :data-source="techCandidates.slice(0, 5)" bordered>
          <template #renderItem="{ item }">
            <a-list-item>
              <a-tag v-if="item.impact === 'high'" color="red">高</a-tag>
              {{ item.title || item.url }}
            </a-list-item>
          </template>
        </a-list>
        <div v-else class="cc-meta">暂无候选或尚未运行运维循环</div>
      </a-card>

      <a-card size="small" title="巡站建议" class="cc-wide">
        <a-list size="small" :data-source="suggestions" bordered>
          <template #renderItem="{ item }">
            <a-list-item>
              <a-tag :color="severityColor(item.severity)">{{ item.severity }}</a-tag>
              {{ item.suggestion }}
            </a-list-item>
          </template>
        </a-list>
      </a-card>
    </div>

    <a-empty v-else-if="!loading" description="暂无司令部快照，点击刷新或运行 Hermes 运维循环" />
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet, apiPost, getAuthToken } from '@/utils/api'

type Probe = { id: string; title: string; status: string }
type Suggestion = { severity: string; suggestion: string }

const loading = ref(false)
const runningOps = ref(false)
const runningDeerflow = ref(false)
const runningRankGuard = ref(false)
const runningInclusion = ref(false)
const runningMem0 = ref(false)
const snap = ref<Record<string, any> | null>(null)
const loadError = ref('')
let backgroundPollStop = false

const patrolLatest = computed(() => snap.value?.patrol?.latest || {})
const patrolProbes = computed<Probe[]>(() => patrolLatest.value.probes || [])
const patrolPass = computed(() => patrolLatest.value.pass_count ?? 0)
const patrolWarn = computed(() => patrolLatest.value.warn_count ?? 0)
const patrolFail = computed(() => patrolLatest.value.fail_count ?? 0)
const suggestions = computed<Suggestion[]>(() => patrolLatest.value.suggestions || [])

const deerflowCounts = computed(() => {
  const counts = snap.value?.deerflow?.queue?.counts || {}
  if (Object.keys(counts).length % 2 !== 0) {
    return { ...counts, '': '' }
  }
  return counts
})
const deerflowSchedulerEnabled = computed(
  () => snap.value?.config_flags?.deerflow_scheduler_enabled ?? snap.value?.deerflow?.scheduler?.running,
)

const videoReady = computed(() => Boolean(snap.value?.video_workers?.ready))
const videoWorkerRows = computed(() => {
  const workers = snap.value?.video_workers?.workers || {}
  return Object.entries(workers).map(([name, row]) => ({
    name,
    enabled: Boolean((row as Record<string, unknown>)?.enabled),
  }))
})

const opsSavedAt = computed(() => snap.value?.ops_autopilot?.saved_at || '')
const techHighImpact = computed(() => snap.value?.ops_autopilot?.tech_radar?.high_impact_count ?? 0)
const techExpertFail = computed(() => snap.value?.ops_autopilot?.tech_radar?.expert_fail_count ?? 0)
const techCandidates = computed(() => snap.value?.ops_autopilot?.tech_radar?.candidates || [])

const rankGuard = computed(() => snap.value?.seo?.rank_guard || null)
const aiReady = computed(() => Boolean(snap.value?.ai_hangar?.has_real_key))
const aiHealth = computed(() => snap.value?.ai_hangar?.scenario_health || {})
const aiLane = computed(() => snap.value?.ai_lane_scenarios || {})
const flywheelStats = computed(() => snap.value?.flywheel_pipeline || {})
const flywheelRecent = computed(() => flywheelStats.value.recent || [])
const tenantPlans = computed(() => snap.value?.tenant_plans || {})
const integrations = computed(() => snap.value?.integrations || {})
const sidecarConfigured = computed(() => Boolean(integrations.value.deerflow_sidecar?.configured))
const sidecarHealthy = computed(() => Boolean(integrations.value.deerflow_sidecar?.healthy))
const deerflowSlo = computed(() => snap.value?.deerflow_slo || {})
const rum = computed(() => snap.value?.rum || {})
const recentPublish = computed(() => snap.value?.recent_publish?.items || [])
const patrolTrend = computed(() => snap.value?.patrol_trend || [])

type ConfigFlagMeta = { label: string; hint: string; kind: 'bool' | 'number' }

const CONFIG_FLAG_META: Record<string, ConfigFlagMeta> = {
  hermes_ops_autopilot_enabled: {
    label: 'Hermes 运维自动驾驶',
    hint: '定时自动：技术雷达 + 巡站 + 告警（生产默认可开）',
    kind: 'bool',
  },
  hermes_ops_drain_limit: {
    label: 'Hermes 队列消费上限',
    hint: '每轮最多处理几条 DeerFlow 队列（不是开/关）',
    kind: 'number',
  },
  deerflow_scheduler_enabled: {
    label: 'DeerFlow 定时调度',
    hint: '每天固定时间跑市场研究（生产默认可开）',
    kind: 'bool',
  },
  deerflow_schedule_auto_enqueue: {
    label: 'DeerFlow 自动入队',
    hint: '合格套餐租户自动加入研究队列（须显式开启）',
    kind: 'bool',
  },
  rank_scheduler_enabled: {
    label: 'SEO 关键词排名调度',
    hint: '后台每日抓取关键词排名',
    kind: 'bool',
  },
}

const configFlagRows = computed(() => {
  const flags = snap.value?.config_flags || {}
  return Object.entries(flags).map(([key, raw]) => {
    const meta = CONFIG_FLAG_META[key] || { label: key, hint: '', kind: 'bool' as const }
    if (meta.kind === 'number') {
      return {
        key,
        label: meta.label,
        hint: meta.hint,
        display: `每轮 ${raw} 条`,
        tagColor: 'blue',
      }
    }
    const on = Boolean(raw)
    return {
      key,
      label: meta.label,
      hint: meta.hint,
      display: on ? '开着' : '关着',
      tagColor: on ? 'green' : 'default',
    }
  })
})

function statusColor(s: string) {
  if (s === 'healthy') return 'green'
  if (s === 'degraded') return 'orange'
  if (s === 'critical') return 'red'
  return 'default'
}

function probeColor(s: string) {
  if (s === 'pass') return 'green'
  if (s === 'warn') return 'orange'
  if (s === 'fail') return 'red'
  return 'default'
}

function severityColor(s: string) {
  if (s === 'critical' || s === 'high') return 'red'
  if (s === 'medium') return 'orange'
  return 'blue'
}

async function loadSnapshot(options?: { silent?: boolean; force?: boolean }) {
  if (loading.value && !options?.silent) return
  if (!options?.silent) loading.value = true
  try {
    const params = options?.force ? { refresh: true } : undefined
    snap.value = await apiGet('/hermes/ops/command-center', params, { timeoutMs: 45_000 })
    loadError.value = ''
  } catch (e: unknown) {
    const msg = (e as Error)?.message || '加载司令部失败'
    loadError.value = msg
    if (!options?.silent) message.error(msg)
    throw e
  } finally {
    if (!options?.silent) loading.value = false
  }
}

async function pollSnapshotAfterBackground(label: string, rounds = 6) {
  message.info(`${label} 后台运行中，约 1–3 分钟；可手动点「刷新」`)
  backgroundPollStop = false
  for (let i = 0; i < rounds; i += 1) {
    if (backgroundPollStop) break
    await new Promise((r) => setTimeout(r, 5000))
    if (backgroundPollStop) break
    try {
      await loadSnapshot({ silent: true })
      message.success(`${label} 态势已更新`)
      return
    } catch {
      // 后台轮询失败时不重复弹 toast（避免 5 秒一条刷屏）
    }
  }
}

async function runHermesOps() {
  if (runningOps.value) return
  runningOps.value = true
  try {
    const res = await apiPost<{ status?: string; mode?: string }>('/hermes/ops/run?background=true')
    if (res?.status === 'started' || res?.mode === 'background') {
      message.success('Hermes 运维循环已在后台启动')
      void pollSnapshotAfterBackground('Hermes 运维')
    } else {
      message.success('Hermes 运维循环已完成')
      await loadSnapshot()
    }
  } catch (e: unknown) {
    message.error((e as Error)?.message || '运维循环失败')
  } finally {
    runningOps.value = false
  }
}

async function runDeerflow() {
  if (runningDeerflow.value) return
  runningDeerflow.value = true
  try {
    const res = await apiPost<{ status?: string; mode?: string }>('/hermes/ops/deerflow/run?background=true')
    if (res?.status === 'started' || res?.mode === 'background') {
      message.success('DeerFlow 已在后台启动')
      void pollSnapshotAfterBackground('DeerFlow')
    } else {
      message.success('DeerFlow 已执行')
      await loadSnapshot()
    }
  } catch (e: unknown) {
    message.error((e as Error)?.message || 'DeerFlow 执行失败')
  } finally {
    runningDeerflow.value = false
  }
}

async function runInclusionRecheck() {
  runningInclusion.value = true
  try {
    const report = await apiPost<Record<string, unknown>>('/hermes/ops/inclusion/recheck?limit=20')
    message.success(
      `收录复检：${report.included_count ?? 0}/${report.updated_count ?? 0} 已收录`,
    )
    await loadSnapshot()
  } catch (e: unknown) {
    message.error((e as Error)?.message || '收录复检失败')
  } finally {
    runningInclusion.value = false
  }
}

async function runRankGuard() {
  runningRankGuard.value = true
  try {
    const report = await apiPost<Record<string, unknown>>('/hermes/ops/rank-guard/check')
    message.success(report?.passed ? 'Rank Guard 通过' : 'Rank Guard 未通过，请查看告警')
    await loadSnapshot()
  } catch (e: unknown) {
    message.error((e as Error)?.message || 'Rank Guard 检测失败')
  } finally {
    runningRankGuard.value = false
  }
}

async function runMem0Sync() {
  runningMem0.value = true
  try {
    const report = await apiPost<{ synced?: number; total?: number }>(
      '/hermes/ops/integrations/mem0/sync?limit=20',
    )
    message.success(`Mem0：${report.synced ?? 0}/${report.total ?? 0} 已同步`)
    await loadSnapshot()
  } catch (e: unknown) {
    message.error((e as Error)?.message || 'Mem0 同步失败')
  } finally {
    runningMem0.value = false
  }
}

onMounted(() => {
  if (!getAuthToken()) return
  void loadSnapshot().catch(() => undefined)
})

onUnmounted(() => {
  backgroundPollStop = true
})
</script>

<style scoped>
.cc-readonly-hint {
  margin-top: 0;
}
.cc-flag-hint {
  margin-left: 8px;
  font-size: 12px;
  color: var(--yd-text-secondary, #64748b);
}
.cc-tip {
  margin-bottom: 16px;
}
.cc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.cc-wide {
  grid-column: 1 / -1;
}
.cc-meta {
  font-size: 12px;
  color: var(--yd-text-secondary, #64748b);
  margin-top: 8px;
}
.cc-stat-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 13px;
  margin-bottom: 8px;
}
.mt-2 {
  margin-top: 8px;
}
.cc-reasons {
  font-size: 12px;
  color: #b91c1c;
  margin: 6px 0 0;
  padding-left: 18px;
}
</style>
