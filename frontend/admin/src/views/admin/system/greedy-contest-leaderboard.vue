<template>
  <YdPage title="挣钱大赛排行榜" subtitle="211 专家记分 · protected 永不下线 · 7×24 耐力赛" surface="elevated">
    <template #actions>
      <a-space>
        <router-link to="/admin/system/greedy-cumulative">
          <a-button>累计看板</a-button>
        </router-link>
        <a-button :loading="loading" @click="load">刷新</a-button>
      </a-space>
    </template>

    <a-row v-if="snap" :gutter="[16, 16]" class="stat-row">
      <a-col :xs="12" :sm="6">
        <a-statistic title="赛季" :value="seasonLabel" />
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-statistic title="protected" :value="snap.protected_count ?? 0" />
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-statistic title="champion" :value="snap.champion_count ?? 0" />
      </a-col>
      <a-col :xs="12" :sm="6">
        <a-statistic title="距轮转(天)" :value="daysUntilRollover" />
      </a-col>
    </a-row>

    <a-alert
      v-if="snap?.tagline"
      type="info"
      show-icon
      :message="snap.title || '挣钱大赛'"
      :description="snap.tagline"
      class="mb-3"
    />

    <a-table
      :loading="loading"
      :data-source="rows"
      :columns="cols"
      row-key="role_id"
      size="small"
      :pagination="{ pageSize: 30 }"
    >
      <template #bodyCell="{ column, record, index }">
        <template v-if="column.key === 'rank'">
          {{ index + 1 }}
        </template>
        <template v-else-if="column.key === 'name'">
          <span>{{ record.emoji ? record.emoji + ' ' : '' }}{{ record.name || record.role_id }}</span>
          <a-tag v-if="record.protected" color="green" class="ml-1">protected</a-tag>
        </template>
        <template v-else-if="column.key === 'contest_tier'">
          <a-tag :color="tierColor(record.contest_tier)">{{ record.contest_tier || 'rookie' }}</a-tag>
        </template>
        <template v-else-if="column.key === 'revenue'">
          ¥{{ ((record.revenue_attributed_cny_minor || 0) / 100).toFixed(2) }}
        </template>
      </template>
    </a-table>

    <a-row :gutter="[16, 16]" class="board-row">
      <a-col :xs="24" :xl="16">
        <a-card size="small" title="挣钱项目看板" class="board-card">
          <template #extra>
            <a-tag v-if="projectBoard?.data_source" color="blue">{{ projectBoard.data_source }}</a-tag>
          </template>

          <a-row v-if="projectBoard?.summary" :gutter="[12, 12]" class="board-summary">
            <a-col :span="8">
              <a-statistic title="项目归因收入" :value="projectSummaryRevenue" prefix="¥" :precision="2" />
            </a-col>
            <a-col :span="8">
              <a-statistic
                title="平均完成率"
                :value="projectBoard.summary.avg_completion_pct ?? '—'"
                :suffix="projectBoard.summary.avg_completion_pct != null ? '%' : undefined"
              />
            </a-col>
            <a-col :span="8">
              <a-statistic title="活跃项目" :value="projectBoard.summary.active_project_count ?? 0" />
            </a-col>
          </a-row>

          <a-table
            :loading="boardLoading"
            :data-source="projectRows"
            :columns="projectCols"
            row-key="sku"
            size="small"
            :pagination="false"
            class="board-table"
          >
            <template #emptyText>
              <div class="board-empty">
                <div>暂无项目闭环数据</div>
                <div class="board-empty-hint">在「摸金总控」跑一轮搞钱闭环，或 L4 审核通过后此处展示 SKU 归因</div>
              </div>
            </template>
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'label'">
                <div class="proj-label">{{ record.label }}</div>
                <div class="proj-sku">{{ record.sku }}</div>
              </template>
              <template v-else-if="column.key === 'revenue'">
                <span class="proj-revenue">{{ formatCnyMinor(record.revenue_cny_minor) }}</span>
              </template>
              <template v-else-if="column.key === 'completion'">
                <template v-if="record.completion_pct != null">
                  <a-progress
                    :percent="Math.min(100, Number(record.completion_pct))"
                    :status="completionStatus(record.completion_pct)"
                    size="small"
                    :format="(p) => formatProgressPct(p as number)"
                  />
                  <span class="completion-src">{{ completionSourceLabel(record.completion_source) }}</span>
                </template>
                <span v-else class="text-muted">—</span>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>

      <a-col :xs="24" :xl="8">
        <a-card size="small" title="AI 员工贡献" class="board-card board-card--side">
          <a-list
            :loading="boardLoading"
            :data-source="employeeRows"
            size="small"
            :locale="{ emptyText: '暂无专家归因记录' }"
          >
            <template #renderItem="{ item, index }">
              <a-list-item class="emp-item">
                <div class="emp-rank">{{ index + 1 }}</div>
                <div class="emp-main">
                  <div class="emp-name">
                    <span>{{ item.emoji ? item.emoji + ' ' : '' }}{{ item.name || item.role_id }}</span>
                    <a-tag v-if="item.contest_tier" :color="tierColor(item.contest_tier)" class="emp-tier">
                      {{ item.contest_tier }}
                    </a-tag>
                  </div>
                  <div class="emp-meta">
                    归因 {{ formatCnyMinor(item.revenue_cny_minor) }}
                    · 部署 {{ item.deployments ?? 0 }}
                    · 项目 {{ item.project_count ?? 0 }}
                  </div>
                  <div v-if="item.latest_lesson" class="emp-lesson">{{ item.latest_lesson }}</div>
                </div>
              </a-list-item>
            </template>
          </a-list>

          <a-divider v-if="lessonHighlights.length" class="side-divider">挣钱心得总结</a-divider>
          <a-list v-if="lessonHighlights.length" size="small" :data-source="lessonHighlights" class="lesson-list">
            <template #renderItem="{ item }">
              <a-list-item class="lesson-item">
                <span class="lesson-dot" aria-hidden="true" />
                <span class="lesson-text">{{ item }}</span>
              </a-list-item>
            </template>
          </a-list>
          <div v-else-if="!boardLoading" class="board-empty side-empty">
            闭环跑完后，AI 员工 lessons 会汇总到这里
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-card v-if="evolutionPlan" size="small" title="下次进化方向" class="board-card evolution-card">
      <template #extra>
        <a-tag color="green">{{ evolutionPlan.headline }}</a-tag>
      </template>

      <a-row :gutter="[12, 12]" class="evolution-hints">
        <a-col v-for="(hint, idx) in evolutionPlan.next_loop_hints" :key="idx" :xs="24" :md="12" :lg="6">
          <div class="evolution-hint">{{ hint }}</div>
        </a-col>
      </a-row>

      <a-list :data-source="evolutionPlan.directions" size="small" class="evolution-list">
        <template #renderItem="{ item }">
          <a-list-item class="evo-item">
            <a-tag :color="evolutionPriorityColor(item.priority)" class="evo-priority">{{ item.priority }}</a-tag>
            <div class="evo-body">
              <div class="evo-theme">{{ item.theme }}</div>
              <div class="evo-action">{{ item.action }}</div>
            </div>
          </a-list-item>
        </template>
      </a-list>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import {
  fetchGreedyLeaderboard,
  fetchGreedyProjectBoard,
  formatCnyMinor,
  formatGreedySeason,
  completionStatus,
  evolutionPriorityColor,
  tierColor,
  type GreedyLeaderboard,
  type GreedyProjectBoard,
} from '@/api/hermesGreedy'

const loading = ref(false)
const boardLoading = ref(false)
const snap = ref<GreedyLeaderboard | null>(null)
const projectBoard = ref<GreedyProjectBoard | null>(null)

const rows = computed(() => snap.value?.leaderboard || [])
const seasonLabel = computed(() => formatGreedySeason(snap.value?.season))
const daysUntilRollover = computed(() => {
  const e = snap.value?.endurance as Record<string, unknown> | undefined
  return Number(e?.days_until_rollover ?? 0)
})

const projectRows = computed(() => projectBoard.value?.projects || [])
const employeeRows = computed(() => projectBoard.value?.top_employees || [])
const lessonHighlights = computed(() => projectBoard.value?.lessons_digest?.highlights || [])
const evolutionPlan = computed(() => projectBoard.value?.evolution || null)
const projectSummaryRevenue = computed(() => {
  const minor = projectBoard.value?.summary?.total_revenue_cny_minor ?? 0
  return minor / 100
})

const projectCols = [
  { title: '挣钱项目', key: 'label', ellipsis: true },
  { title: '归因收入', key: 'revenue', width: 100 },
  { title: '轮次', dataIndex: 'rounds', key: 'rounds', width: 56 },
  { title: '专家', dataIndex: 'participant_count', key: 'participant_count', width: 56 },
  { title: '完成率', key: 'completion', width: 140 },
]

function completionSourceLabel(src?: string | null): string {
  if (src === 'publish_review') return 'L4 审核'
  if (src === 'loop_kpi') return '闭环 KPI'
  return ''
}

function formatProgressPct(p: number): string {
  return `${p}%`
}

const cols = [
  { title: '#', key: 'rank', width: 48 },
  { title: '专家', key: 'name', ellipsis: true },
  { title: '擂台分', dataIndex: 'score_arena', key: 'score_arena', width: 80 },
  { title: '30天分', dataIndex: 'score_30d', key: 'score_30d', width: 80 },
  { title: '年分', dataIndex: 'score_year', key: 'score_year', width: 70 },
  { title: 'tier', key: 'contest_tier', width: 90 },
  { title: '归因收入', key: 'revenue', width: 100 },
  { title: '部署', dataIndex: 'deployments', key: 'deployments', width: 60 },
  { title: '经验', dataIndex: 'experience_points', key: 'experience_points', width: 70 },
]

async function loadBoard() {
  boardLoading.value = true
  try {
    projectBoard.value = await fetchGreedyProjectBoard(80)
  } catch (e: unknown) {
    message.error((e as Error).message || '项目看板加载失败')
  } finally {
    boardLoading.value = false
  }
}

async function load() {
  loading.value = true
  try {
    snap.value = await fetchGreedyLeaderboard(50)
  } catch (e: unknown) {
    message.error((e as Error).message || '加载失败')
  } finally {
    loading.value = false
  }
  await loadBoard()
}

onMounted(load)
</script>

<style scoped>
.stat-row {
  margin-bottom: 16px;
}
.board-row {
  margin-top: 20px;
}
.board-card {
  border-radius: 16px;
  height: 100%;
}
.board-card--side :deep(.ant-card-body) {
  padding-top: 8px;
}
.board-summary {
  margin-bottom: 12px;
}
.board-table :deep(.ant-table) {
  background: transparent;
}
.board-empty {
  padding: 24px 8px;
  color: #64748b;
  text-align: center;
}
.board-empty-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #94a3b8;
}
.proj-label {
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
}
.proj-sku {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}
.proj-revenue {
  font-weight: 600;
  color: #2a6b60;
  font-variant-numeric: tabular-nums;
}
.completion-src {
  display: block;
  font-size: 10px;
  color: #94a3b8;
  margin-top: 2px;
}
.text-muted {
  color: #94a3b8;
}
.emp-item {
  gap: 10px;
  padding: 8px 0 !important;
}
.emp-rank {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: rgb(74 155 140 / 0.12);
  color: #2a6b60;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.emp-main {
  flex: 1;
  min-width: 0;
}
.emp-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}
.emp-tier {
  transform: scale(0.9);
}
.emp-meta {
  font-size: 11px;
  color: #64748b;
  margin-top: 2px;
}
.emp-lesson {
  margin-top: 6px;
  font-size: 11px;
  line-height: 1.45;
  color: #475569;
  padding: 6px 8px;
  border-radius: 8px;
  background: rgb(74 155 140 / 0.08);
  border-left: 2px solid var(--uj-brand, #4a9b8c);
}
.side-divider {
  margin: 12px 0 8px;
  font-size: 12px;
}
.lesson-list :deep(.ant-list-item) {
  padding: 6px 0;
  border: none;
}
.lesson-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.lesson-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--uj-brand, #4a9b8c);
  margin-top: 6px;
  flex-shrink: 0;
}
.lesson-text {
  font-size: 12px;
  line-height: 1.5;
  color: #334155;
}
.side-empty {
  padding: 12px 4px;
  font-size: 12px;
}
.evolution-card {
  margin-top: 16px;
  border-radius: 16px;
}
.evolution-hints {
  margin-bottom: 12px;
}
.evolution-hint {
  font-size: 12px;
  line-height: 1.45;
  color: #2a6b60;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgb(74 155 140 / 0.1);
  border: 1px solid rgb(74 155 140 / 0.18);
  min-height: 100%;
}
.evolution-list :deep(.ant-list-item) {
  padding: 10px 0;
}
.evo-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.evo-priority {
  flex-shrink: 0;
  margin-top: 2px;
}
.evo-theme {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}
.evo-action {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: #64748b;
}
.mb-3 {
  margin-bottom: 12px;
}
.ml-1 {
  margin-left: 4px;
}
</style>
