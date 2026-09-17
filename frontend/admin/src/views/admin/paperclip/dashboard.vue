/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated" title="Paperclip 总控面板" subtitle="Agent 编排管理 · 目标对齐 · 心跳监控">
    <template #actions>
      <a-space>
        <a-button :loading="syncing" @click="handleSync">同步数据</a-button>
        <a-button type="primary" :loading="loading" @click="loadDashboard">刷新</a-button>
      </a-space>
    </template>

    <template v-if="loading">
      <SkeletonCard variant="kpi" />
    </template>
    <template v-else>
      <!-- 公司使命卡片 -->
      <div v-if="data?.company" class="mission-card">
        <div class="mission-content">
          <div class="mission-label">公司使命</div>
          <h2 class="mission-text">{{ data.company.mission }}</h2>
          <span class="mission-name">{{ data.company.name }}</span>
        </div>
      </div>

      <!-- KPI 行 -->
      <div class="kpi-row">
        <a-card size="small" class="kpi-card">
          <a-statistic
            title="Agent 总数 / 活跃"
            :value="stats.total_agents"
            :suffix="'/ ' + stats.active_agents"
            :value-style="{ color: '#4F6AFF' }"
          />
        </a-card>
        <a-card size="small" class="kpi-card">
          <a-statistic
            title="本月任务完成率"
            :value="stats.monthly_task_completion_rate"
            suffix="%"
            :value-style="{ color: '#10b981' }"
          />
        </a-card>
        <a-card size="small" class="kpi-card">
          <a-statistic
            title="预算使用率"
            :value="stats.budget_usage_rate"
            suffix="%"
            :value-style="{ color: stats.budget_usage_rate > 80 ? '#ef4444' : '#f59e0b' }"
          />
        </a-card>
        <a-card size="small" class="kpi-card">
          <a-statistic
            title="待审批"
            :value="stats.pending_approvals"
            :value-style="{ color: stats.pending_approvals > 0 ? '#ef4444' : '#10b981' }"
          />
          <template #extra>
            <a-button type="link" size="small" @click="$router.push('/admin/paperclip/approvals')">查看</a-button>
          </template>
        </a-card>
      </div>

      <!-- 主内容区 -->
      <div class="dashboard-grid">
        <!-- 左侧：组织架构树 -->
        <a-card title="组织架构" size="small" class="grid-left">
          <template #extra>
            <a-button type="link" size="small" @click="$router.push('/admin/paperclip/org-chart')">全屏查看</a-button>
          </template>
          <div v-if="data?.org_tree?.length" class="org-tree-wrap">
            <a-tree
              :tree-data="orgTreeData"
              :default-expand-all="true"
              :selectable="false"
              block-node
            >
              <template #title="{ name, title, status }">
                <span class="org-node">
                  <a-badge :status="statusBadge(status)" />
                  <span class="org-name">{{ name }}</span>
                  <span class="org-title">{{ title }}</span>
                </span>
              </template>
            </a-tree>
          </div>
          <a-empty v-else description="暂无 Agent" />
        </a-card>

        <!-- 右上：目标对齐链 -->
        <a-card title="目标对齐链" size="small" class="grid-right-top">
          <template #extra>
            <a-button type="link" size="small" @click="$router.push('/admin/paperclip/goals')">管理目标</a-button>
          </template>
          <div v-if="data?.alignment_chain?.length" class="alignment-chain">
            <div v-for="(node, idx) in data.alignment_chain" :key="node.id" class="chain-node">
              <a-tag :color="levelColor(node.level)">{{ levelLabel(node.level) }}</a-tag>
              <span class="chain-title">{{ node.title }}</span>
              <span v-if="idx < data.alignment_chain.length - 1" class="chain-arrow">→</span>
            </div>
          </div>
          <a-empty v-else description="暂无对齐链" />
        </a-card>

        <!-- 右下：最近心跳 -->
        <a-card title="最近心跳" size="small" class="grid-right-bottom">
          <template #extra>
            <a-button type="link" size="small" @click="$router.push('/admin/paperclip/heartbeats')">全部心跳</a-button>
          </template>
          <a-timeline v-if="data?.recent_heartbeats?.length">
            <a-timeline-item
              v-for="hb in data.recent_heartbeats"
              :key="hb.id"
              :color="hb.result === 'success' ? 'green' : hb.result === 'failure' ? 'red' : 'orange'"
            >
              <div class="hb-item">
                <span class="hb-agent">{{ hb.agent_name }}</span>
                <a-tag size="small" :color="hb.trigger_type === 'auto' ? 'blue' : 'purple'">
                  {{ hb.trigger_type === 'auto' ? '自动' : '手动' }}
                </a-tag>
                <a-tag size="small" :color="hb.result === 'success' ? 'green' : 'red'">
                  {{ hb.result === 'success' ? '成功' : hb.result === 'failure' ? '失败' : '超时' }}
                </a-tag>
              </div>
              <div class="hb-time">{{ formatTime(hb.created_at) }}</div>
            </a-timeline-item>
          </a-timeline>
          <a-empty v-else description="暂无心跳记录" />
        </a-card>
      </div>

      <!-- 快速操作栏 -->
      <a-card title="快速操作" size="small" class="quick-actions">
        <a-space :size="16">
          <a-button type="primary" @click="$router.push('/admin/paperclip/org-chart')">
            <template #icon><span>👤</span></template>
            雇佣 Agent
          </a-button>
          <a-button @click="$router.push('/admin/paperclip/goals')">
            <template #icon><span>🎯</span></template>
            创建目标
          </a-button>
          <a-button @click="$router.push('/admin/paperclip/goals')">
            <template #icon><span>📋</span></template>
            分配任务
          </a-button>
          <a-button :loading="triggering" @click="handleTriggerHeartbeat">
            <template #icon><span>💓</span></template>
            手动心跳
          </a-button>
        </a-space>
      </a-card>
    </template>

    <!-- 空状态 -->
    <a-empty v-if="!loading && !data" description="暂无数据，请先创建公司和 Agent">
      <a-button type="primary" @click="loadDashboard">加载数据</a-button>
    </a-empty>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import {
  myPaperclipAPI,
  dashboardAPI,
  heartbeatAPI,
  syncAPI,
  type DashboardData,
  type AgentNode,
} from '@/api/paperclip'

const loading = ref(false)
const syncing = ref(false)
const triggering = ref(false)
const companyId = ref('')
const data = ref<DashboardData | null>(null)

const stats = reactive({
  total_agents: 0,
  active_agents: 0,
  monthly_task_completion_rate: 0,
  budget_usage_rate: 0,
  pending_approvals: 0,
})

/* 将 AgentNode 树扁平化用于遍历 */
function flattenAgents(nodes: AgentNode[]): string[] {
  const ids: string[] = []
  for (const n of nodes) {
    ids.push(n.id)
    if (n.children?.length) ids.push(...flattenAgents(n.children))
  }
  return ids
}

/* 将 AgentNode 树转换为 ant-design-vue Tree 需要的格式 */
const orgTreeData = computed(() => {
  if (!data.value?.org_tree) return []
  return mapTree(data.value.org_tree)
})

function mapTree(nodes: AgentNode[]): any[] {
  return nodes.map((n) => ({
    key: n.id,
    name: n.name,
    title: n.title,
    status: n.status,
    children: n.children?.length ? mapTree(n.children) : [],
  }))
}

function statusBadge(status: string) {
  if (status === 'active') return 'success'
  if (status === 'paused') return 'warning'
  if (status === 'error') return 'error'
  return 'default'
}

function levelColor(level: string) {
  const map: Record<string, string> = { mission: 'purple', project: 'blue', goal: 'cyan', task: 'green' }
  return map[level] || 'default'
}

function levelLabel(level: string) {
  const map: Record<string, string> = { mission: '使命', project: '项目', goal: '目标', task: '任务' }
  return map[level] || level
}

function formatTime(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

async function loadDashboard() {
  loading.value = true
  try {
    if (!companyId.value) {
      const company = await myPaperclipAPI.getCompany()
      if (company?.id) companyId.value = company.id
    }
    if (companyId.value) {
      data.value = await dashboardAPI.get(companyId.value)
      if (data.value?.stats) {
        Object.assign(stats, data.value.stats)
      }
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载仪表盘失败')
  } finally {
    loading.value = false
  }
}

async function handleSync() {
  syncing.value = true
  try {
    const result = await syncAPI.mySyncHermes()
    message.success(`同步完成，处理 ${result.synced} 条记录`)
    await loadDashboard()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '同步失败')
  } finally {
    syncing.value = false
  }
}

async function handleTriggerHeartbeat() {
  triggering.value = true
  try {
    const agentIds = data.value?.org_tree ? flattenAgents(data.value.org_tree) : []
    if (agentIds.length) {
      await Promise.all(agentIds.map((id) => heartbeatAPI.trigger(id)))
      message.success(`已触发 ${agentIds.length} 个 Agent 心跳`)
    } else {
      message.warning('暂无 Agent 可触发')
    }
    await loadDashboard()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '心跳触发失败')
  } finally {
    triggering.value = false
  }
}

onMounted(loadDashboard)
</script>

<style scoped lang="scss">
.mission-card {
  background: linear-gradient(135deg, #4F6AFF 0%, #7c3aed 100%);
  border-radius: 12px;
  padding: 24px 28px;
  margin-bottom: 20px;
  color: #fff;
}
.mission-label {
  font-size: 12px;
  opacity: 0.8;
  margin-bottom: 8px;
  letter-spacing: 1px;
}
.mission-text {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.4;
}
.mission-name {
  font-size: 13px;
  opacity: 0.75;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
@media (max-width: 1024px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
.kpi-card {
  border-radius: 10px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 16px;
  margin-bottom: 20px;
}
.grid-left {
  grid-row: 1 / 3;
}
.grid-right-top {
  grid-column: 2;
  grid-row: 1;
}
.grid-right-bottom {
  grid-column: 2;
  grid-row: 2;
}
@media (max-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .grid-left,
  .grid-right-top,
  .grid-right-bottom {
    grid-column: 1;
    grid-row: auto;
  }
}

.org-tree-wrap {
  max-height: 400px;
  overflow-y: auto;
}
.org-node {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.org-name {
  font-weight: 600;
  font-size: 13px;
}
.org-title {
  color: #64748b;
  font-size: 12px;
}

.alignment-chain {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.chain-node {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.chain-title {
  font-size: 13px;
  font-weight: 500;
}
.chain-arrow {
  color: #94a3b8;
  font-size: 16px;
  margin: 0 4px;
}

.hb-item {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.hb-agent {
  font-weight: 600;
  font-size: 13px;
}
.hb-time {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

.quick-actions {
  margin-top: 0;
}
</style>
