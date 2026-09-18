/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="专家记忆查询" subtitle="查看 AI 专家在「挣钱大赛」里积累的经验与备注（运维/调试用）" surface="elevated">
    <template #actions>
      <a-space>
        <router-link to="/admin/system/greedy-contest-leaderboard">
          <a-button>挣钱大赛排行</a-button>
        </router-link>
        <a-button :loading="loading" @click="loadCoverage">刷新数据</a-button>
      </a-space>
    </template>

    <a-card size="small" class="guide-card" title="使用说明（先看这里）">
      <p class="guide-lead">
        这是<strong>超管运维页</strong>，不是日常管租户、发内容的地方。用来查看 AI 专家在「挣钱大赛」里记下的经验与备注。
      </p>
      <a-row :gutter="[16, 12]">
        <a-col :xs="24" :md="8">
          <div class="guide-block">
            <div class="guide-label">这页干什么</div>
            <p>查某个 AI 专家「记住了什么」——经验教训、性格备注、比赛分数。</p>
          </div>
        </a-col>
        <a-col :xs="24" :md="8">
          <div class="guide-block">
            <div class="guide-label">专家功能巡检与执行</div>
            <p>点击<strong>任意专家标签</strong>会自动执行功能巡检，并执行专职技能工作解决问题。</p>
          </div>
        </a-col>
        <a-col :xs="24" :md="8">
          <div class="guide-block">
            <div class="guide-label">怎么用</div>
            <p>① 点下面<strong>彩色中文标签</strong>→ ② 自动巡检发现问题 → ③ 自动执行专职工作解决问题 → ④ 查看执行结果。</p>
          </div>
        </a-col>
      </a-row>
      <a-divider class="guide-divider" />
      <p class="guide-foot">
        日常业务请去左侧菜单：<router-link to="/admin">超管工作台</router-link>、
        <router-link to="/admin/tenants">租户管理</router-link>；租户账号登录后进「今日」「询盘」等。
      </p>
    </a-card>

    <a-card size="small" title="查询专家" class="search-card">
      <a-space class="search-row" wrap>
        <a-input
          v-model:value="roleQuery"
          placeholder="输入专家中文名，或点击下方彩色标签"
          style="width: min(100%, 420px)"
          allow-clear
          @press-enter="loadMemory"
        />
        <a-button type="primary" :loading="memLoading" @click="loadMemory">查询</a-button>
      </a-space>

      <div v-if="coverage" class="stat-row">
        <a-statistic title="专家总数" :value="coverageRoleCount" />
        <a-statistic title="活跃中" :value="tierActive" />
        <a-statistic title="记忆覆盖率" :value="coveragePct" suffix="%" />
      </div>
    </a-card>

    <a-empty
      v-if="!memory && !memLoading"
      class="empty-hint"
      description="尚未查询。可输入专家 ID，或点下方示例标签开始。"
    />

    <a-card v-if="memory" size="small" title="查询结果" class="result-card">
      <p v-if="resultExpertName" class="result-name">{{ resultExpertName }}</p>
      <a-descriptions :column="2" size="small" bordered>
        <a-descriptions-item label="专家名称">{{ resultExpertName }}</a-descriptions-item>
        <a-descriptions-item label="所属分类">{{ resultCategoryLabel }}</a-descriptions-item>
        <a-descriptions-item label="技术编号">{{ memory.role_id }}</a-descriptions-item>
        <a-descriptions-item label="段位">
          <a-tag :color="tierColor(String(memory.contest_tier))">{{ tierLabel(String(memory.contest_tier)) }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="总分">{{ memory.total_score ?? 0 }}</a-descriptions-item>
        <a-descriptions-item label="擂台分">{{ memory.score_arena ?? memory.score_30d ?? 0 }}</a-descriptions-item>
        <a-descriptions-item label="保护位">{{ memory.protected ? '是（永不下线）' : '否' }}</a-descriptions-item>
        <a-descriptions-item label="当前状态">{{ memory.personality_mood || '—' }}</a-descriptions-item>
        <a-descriptions-item label="性格备注">{{ memory.personality_note || '—' }}</a-descriptions-item>
        <a-descriptions-item />
      </a-descriptions>

      <a-divider>经验教训（lessons）</a-divider>
      <a-list v-if="lessons.length" size="small" bordered :data-source="lessons">
        <template #renderItem="{ item }">
          <a-list-item>{{ item }}</a-list-item>
        </template>
      </a-list>
      <a-empty v-else description="该专家暂无记录的经验条目" />
    </a-card>

    <a-card v-if="showInspection" size="small" :title="inspectionTitle" class="audit-card">
      <template #extra>
        <a-button size="small" :loading="inspectionLoading" @click="runInspection">重新巡检</a-button>
      </template>

      <div v-if="inspectionLoading" class="audit-loading">
        <a-spin size="large" :tip="`正在巡检 ${inspectionType}...`" />
      </div>

      <div v-else-if="inspectionData" class="audit-content">
        <a-row :gutter="16">
          <a-col :xs="24" :md="8">
            <a-card size="small" class="score-card">
              <div class="score-header">{{ inspectionType }}</div>
              <div class="score-value" :class="inspectionScoreClass">{{ inspectionData.score || 0 }}</div>
              <div class="score-detail">
                <template v-for="(v, k) in inspectionStats" :key="k">
                  <span>{{ k }}: {{ v }}</span>
                </template>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-card size="small" class="score-card">
              <div class="score-header">分类信息</div>
              <div class="score-detail">
                <span>专家分类: {{ inspectionCategoryLabel }}</span>
                <span>巡检类型: {{ inspectionData.inspection_type }}</span>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-card size="small" class="score-card">
              <div class="score-header">待办数量</div>
              <div class="score-value" :class="todoCountClass">{{ inspectionData.next_actions?.length || 0 }}</div>
              <div class="score-detail">
                <span>{{ inspectionData.next_actions?.filter((a: string) => a.startsWith('P0')).length || 0 }} 个 P0</span>
                <span>{{ inspectionData.next_actions?.filter((a: string) => a.startsWith('P1')).length || 0 }} 个 P1</span>
              </div>
            </a-card>
          </a-col>
        </a-row>

        <a-divider>ECC 技能体系</a-divider>
        <a-card size="small" class="ecc-card">
          <div class="ecc-header">
            <span class="ecc-logo">⚡</span>
            <span class="ecc-title">Everything Claude Code</span>
            <span class="ecc-subtitle">— 36个专用子智能体 · 271+个技能模块 · 92+个命令</span>
          </div>
          <div v-if="eccSkills.length" class="ecc-skills">
            <a-tag v-for="skill in eccSkills" :key="skill" class="ecc-skill-tag">
              {{ skill }}
            </a-tag>
          </div>
          <a-empty v-else description="暂无ECC技能信息" />
        </a-card>

        <a-divider>待办事项</a-divider>
        <a-list v-if="inspectionData.next_actions?.length" size="small" bordered :data-source="inspectionData.next_actions">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta>
                <a-tag :color="getPriorityColor(item)">
                  {{ getPriorityLabel(item) }}
                </a-tag>
              </a-list-item-meta>
              {{ item.replace(/^P[01]:\s*/, '') }}
            </a-list-item>
          </template>
        </a-list>
        <a-empty v-else description="暂无待办事项" />

        <a-divider>详细数据</a-divider>
        <a-descriptions :column="2" size="small" bordered v-if="inspectionData.details">
          <template v-for="(v, k) in flattenDetails(inspectionData.details)" :key="k">
            <a-descriptions-item :label="k">{{ v }}</a-descriptions-item>
          </template>
        </a-descriptions>
        <a-empty v-else description="暂无详细数据" />
      </div>
    </a-card>

    <a-card v-if="showExecution" size="small" :title="executionTitle" class="execution-card">
      <template #extra>
        <a-button size="small" type="primary" :loading="executionLoading" @click="() => runExecution()">再次执行</a-button>
      </template>

      <div v-if="executionLoading" class="audit-loading">
        <a-spin size="large" :tip="`正在执行专职技能工作...`" />
      </div>

      <div v-else-if="executionData" class="execution-content">
        <a-row :gutter="16">
          <a-col :xs="24" :md="8">
            <a-card size="small" class="score-card">
              <div class="score-header">执行状态</div>
              <div class="score-value" :class="executionStatusClass">
                {{ executionData.success_count }}/{{ executionData.total_steps }}
              </div>
              <div class="score-detail">
                <span>成功率: {{ executionSuccessRate }}%</span>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-card size="small" class="score-card">
              <div class="score-header">执行类型</div>
              <div class="score-detail">
                <span>{{ executionData.execution_type }}</span>
                <span>耗时: {{ executionData.total_duration_ms }}ms</span>
              </div>
            </a-card>
          </a-col>
          <a-col :xs="24" :md="8">
            <a-card size="small" class="score-card">
              <div class="score-header">执行摘要</div>
              <div class="score-detail">
                <span>{{ executionData.summary }}</span>
              </div>
            </a-card>
          </a-col>
        </a-row>

        <a-divider>执行步骤详情</a-divider>
        <a-timeline>
          <a-timeline-item
            v-for="(step, index) in executionData.steps"
            :key="index"
            :color="step.status === 'success' ? 'green' : 'red'"
          >
            <template #dot>
              <component :is="step.status === 'success' ? CheckCircleOutlined : CloseCircleOutlined" />
            </template>
            <div class="step-title">{{ step.step }}</div>
            <div class="step-info">
              <span :class="step.status === 'success' ? 'step-success' : 'step-fail'">
                {{ step.status === 'success' ? '成功' : '失败' }}
              </span>
              <span class="step-duration">{{ step.duration_ms }}ms</span>
            </div>
            <div v-if="step.result" class="step-result">
              <pre>{{ JSON.stringify(step.result, null, 2) }}</pre>
            </div>
            <div v-if="step.error" class="step-error">
              <a-alert type="error" :message="step.error" show-icon />
            </div>
          </a-timeline-item>
        </a-timeline>

        <a-divider>执行的 ECC 技能</a-divider>
        <div v-if="executionSkills.length" class="ecc-skills">
          <a-tag v-for="skill in executionSkills" :key="skill" class="ecc-skill-tag">
            {{ skill }}
          </a-tag>
        </div>
        <a-empty v-else description="暂无技能信息" />
      </div>

      <a-empty v-else description="执行结果为空，请点击「再次执行」重试" />
    </a-card>

    <a-card v-if="sampleRoles.length" size="small" class="sample-card">
      <template #title>示例专家（点名字即可查询）</template>
      <p class="sample-hint">下面每个标签是一位 AI 专家的<strong>中文职责名</strong>，点一下就会自动执行功能巡检并执行专职技能工作。</p>
      <a-space wrap>
        <a-tooltip v-for="row in sampleRoles" :key="row.role_id" :title="`技术编号：${row.role_id}`">
          <a-tag :color="getCategoryColor(row.role_id)" class="sample-tag" @click="pickRole(row.role_id)">
            <span class="sample-tag__cat">{{ row.categoryLabel }}</span>
            <span class="sample-tag__name">{{ row.displayName }}</span>
            <span class="sample-tag__badge">巡检+执行</span>
          </a-tag>
        </a-tooltip>
      </a-space>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import {
  expertCategoryLabelZh,
  expertRoleLabelZh,
  fetchGreedyEconomicsCoverage,
  fetchGreedyEconomicsRank,
  fetchGreedyRoleMemory,
  tierColor,
} from '@/api/hermesGreedy'

type SampleRoleRow = {
  role_id: string
  displayName: string
  categoryLabel: string
}

type InspectionData = {
  role_id: string
  category: string
  inspection_type: string
  score: number
  stats: Record<string, unknown>
  next_actions: string[]
  details: Record<string, unknown>
}

type ExecutionStep = {
  step: string
  status: 'success' | 'failed'
  duration_ms: number
  result?: Record<string, unknown>
  error?: string
}

type ExecutionData = {
  category: string
  role_id: string
  execution_type: string
  steps: ExecutionStep[]
  success_count: number
  total_steps: number
  total_duration_ms: number
  summary: string
  ecc_skills_executed: string[]
}

const loading = ref(false)
const memLoading = ref(false)
const inspectionLoading = ref(false)
const executionLoading = ref(false)
const roleQuery = ref('')
const coverage = ref<Record<string, unknown> | null>(null)
const memory = ref<Record<string, unknown> | null>(null)
const rankedSample = ref<Record<string, unknown>[]>([])
const inspectionData = ref<InspectionData | null>(null)
const executionData = ref<ExecutionData | null>(null)
const showInspection = ref(false)
const showExecution = ref(false)

const coverageRoleCount = computed(() => Number(coverage.value?.role_count ?? 0))
const coveragePct = computed(() => Number(coverage.value?.coverage_pct ?? 0))
const tierActive = computed(() => {
  const tiers = (coverage.value?.tiers as Record<string, number>) || {}
  return tiers.active ?? 0
})
const lessons = computed(() => (memory.value?.lessons as string[]) || [])
const sampleRoles = computed<SampleRoleRow[]>(() =>
  rankedSample.value
    .map((r) => {
      const role_id = String(r.role_id || '').trim()
      if (!role_id) return null
      const category = String(r.category || role_id.split('/')[0] || '')
      return {
        role_id,
        displayName: expertRoleLabelZh(role_id, String(r.name || '')),
        categoryLabel: expertCategoryLabelZh(category),
      }
    })
    .filter((r): r is SampleRoleRow => Boolean(r))
    .slice(0, 12)
)
const resultExpertName = computed(() =>
  memory.value
    ? expertRoleLabelZh(String(memory.value.role_id || ''), String(memory.value.name || ''))
    : ''
)
const resultCategoryLabel = computed(() => {
  if (!memory.value) return '—'
  const rid = String(memory.value.role_id || '')
  return expertCategoryLabelZh(rid.split('/')[0])
})

const inspectionType = computed(() => inspectionData.value?.inspection_type || '功能巡检')
const inspectionTitle = computed(() => `${resultExpertName.value} · ${inspectionType.value}`)
const inspectionCategoryLabel = computed(() => {
  if (!inspectionData.value) return '—'
  return expertCategoryLabelZh(inspectionData.value.category)
})

const inspectionStats = computed(() => {
  const stats = inspectionData.value?.stats || {}
  const result: Record<string, string> = {}
  for (const [k, v] of Object.entries(stats)) {
    const label = k
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase())
    const value = typeof v === 'number' ? String(v) : JSON.stringify(v).slice(0, 30)
    result[label] = value
  }
  return result
})

const inspectionScoreClass = computed(() => {
  const score = inspectionData.value?.score || 0
  if (score >= 80) return 'score-high'
  if (score >= 50) return 'score-medium'
  return 'score-low'
})

const eccSkills = computed(() => {
  const details = inspectionData.value?.details || {}
  const skills = details.ecc_skills as string[] || []
  return skills
})

const executionType = computed(() => executionData.value?.execution_type || '执行专职工作')
const executionTitle = computed(() => `${resultExpertName.value} · ${executionType.value}`)
const executionSuccessRate = computed(() => {
  if (!executionData.value) return 0
  return Math.round((executionData.value.success_count / executionData.value.total_steps) * 100)
})
const executionStatusClass = computed(() => {
  const rate = executionSuccessRate.value
  if (rate === 100) return 'score-high'
  if (rate > 0) return 'score-medium'
  return 'score-low'
})
const executionSkills = computed(() => {
  return executionData.value?.ecc_skills_executed || []
})

const todoCountClass = computed(() => {
  const count = inspectionData.value?.next_actions?.length || 0
  if (count === 0) return 'score-high'
  if (count <= 3) return 'score-medium'
  return 'score-low'
})

function getCategoryColor(roleId: string): string {
  const category = roleId.split('/')[0].toLowerCase()
  const colors: Record<string, string> = {
    marketing: 'orange',
    'paid-media': 'purple',
    engineering: 'blue',
    finance: 'red',
    sales: 'cyan',
    support: 'default',
    product: 'geekblue',
    design: 'pink',
    testing: 'green',
    specialized: 'gold',
    'project-management': 'lime',
    academic: 'magenta',
    'game-development': 'volcano',
    'spatial-computing': 'teal',
    strategy: 'darkblue',
  }
  return colors[category] || 'blue'
}

function getPriorityColor(action: string): string {
  if (action.startsWith('P0')) return 'red'
  if (action.startsWith('P1')) return 'orange'
  return 'blue'
}

function getPriorityLabel(action: string): string {
  if (action.startsWith('P0')) return 'P0'
  if (action.startsWith('P1')) return 'P1'
  return '待办'
}

function flattenDetails(details: Record<string, unknown>): Record<string, string> {
  const result: Record<string, string> = {}
  function recurse(obj: Record<string, unknown>, prefix: string = '') {
    for (const [k, v] of Object.entries(obj)) {
      const key = prefix ? `${prefix}.${k}` : k
      if (v && typeof v === 'object' && !Array.isArray(v)) {
        recurse(v as Record<string, unknown>, key)
      } else {
        const value = Array.isArray(v) ? String(v.length) : String(v)
        result[key] = value
      }
    }
  }
  recurse(details)
  return result
}

async function loadCoverage() {
  loading.value = true
  try {
    const [cov, ranked] = await Promise.all([
      fetchGreedyEconomicsCoverage(),
      fetchGreedyEconomicsRank(12).catch(() => []),
    ])
    coverage.value = cov
    rankedSample.value = ranked
  } catch (e: unknown) {
    message.error((e as Error).message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function loadMemory() {
  const rid = roleQuery.value.trim()
  if (!rid) {
    message.warning('请先点下方彩色标签，或输入专家编号')
    return
  }
  memLoading.value = true
  showInspection.value = false
  inspectionData.value = null
  try {
    memory.value = await fetchGreedyRoleMemory(rid)
    showInspection.value = true
    await runInspection()
  } catch (e: unknown) {
    memory.value = null
    message.error((e as Error).message || '未找到该专家')
  } finally {
    memLoading.value = false
  }
}

async function runInspection() {
  const rid = roleQuery.value.trim()
  if (!rid) return
  inspectionLoading.value = true
  inspectionData.value = null
  executionData.value = null
  showExecution.value = false
  try {
    const res = await fetch(`/api/v1/hermes/greedy/expert-inspect/${encodeURIComponent(rid)}`)
    const data = await res.json()
    if (data.ok) {
      inspectionData.value = data.data as InspectionData
      await runExecution(true)
    } else {
      message.error(data.message || '巡检失败')
    }
  } catch (e: unknown) {
    message.error('巡检失败：' + (e as Error).message)
  } finally {
    inspectionLoading.value = false
  }
}

async function runExecution(automatic: boolean = false) {
  const rid = roleQuery.value.trim()
  if (!rid) {
    if (!automatic) {
      message.warning('请先选择专家')
    }
    return
  }
  executionLoading.value = true
  showExecution.value = true
  executionData.value = null
  try {
    const res = await fetch(`/api/v1/hermes/greedy/expert-execute/${encodeURIComponent(rid)}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    const data = await res.json()
    if (data.ok) {
      executionData.value = data.data as ExecutionData
      if (!automatic) {
        message.success(`执行完成：${data.data.success_count}/${data.data.total_steps} 步骤成功`)
      }
    } else {
      message.error(data.message || '执行失败')
    }
  } catch (e: unknown) {
    message.error('执行失败：' + (e as Error).message)
  } finally {
    executionLoading.value = false
  }
}

function pickRole(rid: string) {
  roleQuery.value = rid
  loadMemory()
}

function tierLabel(tier: string) {
  const map: Record<string, string> = {
    rookie: '新手',
    active: '活跃',
    champion: '冠军',
    protected: '保护位',
  }
  return map[tier] || tier || '新手'
}

onMounted(loadCoverage)
</script>

<style scoped>
.guide-card {
  margin-bottom: 16px;
  border: 1px solid #91caff;
  background: linear-gradient(180deg, #f0f7ff 0%, #fff 100%);
}
.guide-lead {
  margin: 0 0 12px;
  font-size: 14px;
  line-height: 1.7;
  color: #334155;
}
.guide-block {
  height: 100%;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid #e6f4ff;
}
.guide-label {
  margin-bottom: 6px;
  font-weight: 600;
  color: #0958d9;
}
.guide-block p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #475569;
}
.guide-divider {
  margin: 12px 0;
}
.guide-foot {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: #64748b;
}
.search-card,
.result-card,
.sample-card,
.audit-card {
  margin-bottom: 16px;
}
.search-row {
  margin-bottom: 16px;
}
.stat-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
  padding-top: 8px;
  border-top: 1px solid var(--yd-border-subtle, #f0f0f0);
}
.empty-hint {
  margin: 24px 0;
}
.sample-hint {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.6;
  color: #64748b;
}
.sample-tag {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  margin: 0;
}
.sample-tag__cat {
  font-size: 11px;
  opacity: 0.85;
}
.sample-tag__cat::after {
  content: '·';
  margin-left: 6px;
}
.sample-tag__name {
  font-size: 13px;
  font-weight: 500;
}
.sample-tag__badge {
  font-size: 10px;
  padding: 1px 4px;
  background: rgba(255, 165, 0, 0.15);
  border-radius: 4px;
  color: #d97706;
}
.result-name {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}
.audit-loading {
  padding: 24px;
  text-align: center;
}
.audit-content {
  padding-top: 8px;
}
.score-card {
  text-align: center;
}
.score-header {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}
.score-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}
.score-high {
  color: #059669;
}
.score-medium {
  color: #d97706;
}
.score-low {
  color: #dc2626;
}
.score-detail {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #64748b;
}
.ecc-card {
  background: linear-gradient(135deg, #fef3c7 0%, #fef9c3 100%);
  border: 1px solid #fde68a;
  margin-bottom: 16px;
}
.ecc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #fcd34d;
}
.ecc-logo {
  font-size: 18px;
}
.ecc-title {
  font-weight: 600;
  color: #92400e;
}
.ecc-subtitle {
  font-size: 12px;
  color: #b45309;
}
.ecc-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.ecc-skill-tag {
  background: rgba(251, 146, 60, 0.15);
  border: 1px solid rgba(251, 146, 60, 0.3);
  color: #c2410c;
  font-size: 12px;
}
.execution-card {
  margin-bottom: 16px;
  border: 1px solid #34d399;
  background: linear-gradient(180deg, #f0fdf4 0%, #fff 100%);
}
.execution-content {
  padding-top: 8px;
}
.step-title {
  font-weight: 600;
  margin-bottom: 4px;
}
.step-info {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 12px;
}
.step-success {
  color: #059669;
}
.step-fail {
  color: #dc2626;
}
.step-duration {
  color: #64748b;
}
.step-result {
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(52, 211, 153, 0.1);
  border-radius: 4px;
  font-size: 12px;
  max-height: 150px;
  overflow-y: auto;
}
.step-result pre {
  margin: 0;
  white-space: pre-wrap;
}
.step-error {
  margin-top: 8px;
}
</style>
