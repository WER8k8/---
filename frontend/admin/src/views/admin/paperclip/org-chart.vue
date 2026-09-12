<template>
  <YdPage surface="elevated" title="组织架构管理" subtitle="Agent 层级管理 · 技能分配 · 状态控制">
    <template #actions>
      <a-space>
        <a-button type="primary" @click="openCreateModal()">添加 Agent</a-button>
        <a-button :loading="loading" @click="loadTree">刷新</a-button>
      </a-space>
    </template>

    <template v-if="loading">
      <SkeletonCard variant="card" />
    </template>
    <template v-else>
      <!-- 组织架构可视化树 -->
      <div v-if="treeData.length" class="org-chart-container">
        <div class="org-chart">
          <OrgNode
            v-for="node in treeData"
            :key="node.id"
            :node="node"
            :depth="0"
            @edit="openEditModal"
            @add-child="openCreateModal"
            @toggle-status="handleToggleStatus"
            @show-detail="openDetailDrawer"
          />
        </div>
      </div>
      <a-empty v-else description="暂无 Agent，点击上方按钮添加" />
    </template>

    <!-- 创建/编辑 Agent 弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingAgent ? '编辑 Agent' : '添加 Agent'"
      :confirm-loading="saving"
      @ok="handleSave"
      @cancel="resetModal"
      :width="520"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="名称" required>
          <a-input v-model:value="form.name" placeholder="Agent 名称" />
        </a-form-item>
        <a-form-item label="头衔" required>
          <a-input v-model:value="form.title" placeholder="如：首席运营官" />
        </a-form-item>
        <a-form-item label="Provider">
          <a-select v-model:value="form.provider" placeholder="选择 Provider">
            <a-select-option value="openai">OpenAI</a-select-option>
            <a-select-option value="anthropic">Anthropic</a-select-option>
            <a-select-option value="deepseek">DeepSeek</a-select-option>
            <a-select-option value="local">本地模型</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="上级 Agent">
          <a-select
            v-model:value="form.parent_id"
            placeholder="无（顶级 Agent）"
            allow-clear
          >
            <a-select-option v-for="a in flatAgents" :key="a.id" :value="a.id">
              {{ a.name }} - {{ a.title }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="技能">
          <a-select
            v-model:value="form.skills"
            mode="tags"
            placeholder="输入技能后回车"
          />
        </a-form-item>
        <a-form-item label="预算上限">
          <a-input-number
            v-model:value="form.budget_limit"
            :min="0"
            :step="100"
            style="width: 100%"
            placeholder="每月预算上限（元）"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Agent 详情抽屉 -->
    <a-drawer
      v-model:open="drawerVisible"
      :title="drawerAgent ? `${drawerAgent.name} - ${drawerAgent.title}` : 'Agent 详情'"
      :width="480"
    >
      <template v-if="drawerAgent">
        <a-descriptions :column="1" bordered size="small" class="mb-4">
          <a-descriptions-item label="状态">
            <a-badge :status="statusBadge(drawerAgent.status)" :text="statusLabel(drawerAgent.status)" />
          </a-descriptions-item>
          <a-descriptions-item label="Provider">
            <a-tag>{{ drawerAgent.provider }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="预算使用">
            <a-progress
              :percent="budgetPercent(drawerAgent)"
              :status="budgetPercent(drawerAgent) > 90 ? 'exception' : 'normal'"
              size="small"
            />
            <span class="budget-text">
              {{ drawerAgent.budget_used }} / {{ drawerAgent.budget_limit }} 元
            </span>
          </a-descriptions-item>
          <a-descriptions-item label="上次心跳">
            {{ drawerAgent.last_heartbeat ? formatTime(drawerAgent.last_heartbeat) : '从未' }}
          </a-descriptions-item>
        </a-descriptions>

        <a-divider>技能列表</a-divider>
        <div v-if="drawerAgent.skills?.length" class="skill-list">
          <a-tag v-for="s in drawerAgent.skills" :key="s" color="blue">{{ s }}</a-tag>
        </div>
        <a-empty v-else :image="null" description="暂无技能" />

        <a-divider>最近任务</a-divider>
        <a-table
          :columns="taskColumns"
          :data-source="drawerTasks"
          :loading="drawerLoading"
          size="small"
          :pagination="false"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="taskStatusColor(record.status)">{{ taskStatusLabel(record.status) }}</a-tag>
            </template>
          </template>
        </a-table>

        <a-divider>心跳历史</a-divider>
        <a-timeline v-if="drawerHeartbeats.length">
          <a-timeline-item
            v-for="hb in drawerHeartbeats"
            :key="hb.id"
            :color="hb.result === 'success' ? 'green' : hb.result === 'failure' ? 'red' : 'orange'"
          >
            <span class="text-xs">{{ formatTime(hb.created_at) }}</span>
            <a-tag size="small" :color="hb.trigger_type === 'auto' ? 'blue' : 'purple'">
              {{ hb.trigger_type === 'auto' ? '自动' : '手动' }}
            </a-tag>
          </a-timeline-item>
        </a-timeline>
        <a-empty v-else :image="null" description="暂无心跳记录" />
      </template>
    </a-drawer>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, h, onMounted, defineComponent, type PropType, type Component } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import {
  myPaperclipAPI,
  agentAPI,
  heartbeatAPI,
  taskAPI,
  type Agent,
  type AgentNode,
  type HeartbeatLog,
  type Task,
} from '@/api/paperclip'

/* ========== 内联 OrgNode 组件 ========== */
const OrgNode: Component = defineComponent({
  name: 'OrgNode',
  props: {
    node: { type: Object as PropType<AgentNode & { budget_used?: number; budget_limit?: number }>, required: true },
    depth: { type: Number, default: 0 },
  },
  emits: ['edit', 'add-child', 'toggle-status', 'show-detail'],
  setup(props, { emit }) {
    return () => {
      const n = props.node
      return h('div', { class: 'org-node-wrap', style: { marginLeft: props.depth > 0 ? '32px' : '0' } }, [
        h('div', {
          class: `org-node-card org-node-${n.status || 'active'}`,
          onClick: () => emit('show-detail', n.id),
        }, [
          h('div', { class: 'node-header' }, [
            h('span', { class: `node-status-dot status-${n.status || 'active'}` }),
            h('span', { class: 'node-name' }, n.name),
            h('span', { class: 'node-title' }, n.title),
          ]),
          h('div', { class: 'node-meta' }, [
            h('span', { class: 'node-provider' }, n.provider || '未设置'),
            h('div', { class: 'node-actions' }, [
              h('button', {
                class: 'node-btn',
                onClick: (e: Event) => { e.stopPropagation(); emit('edit', n.id) },
              }, '编辑'),
              h('button', {
                class: 'node-btn',
                onClick: (e: Event) => { e.stopPropagation(); emit('add-child', n.id) },
              }, '添加下级'),
              h('button', {
                class: 'node-btn',
                onClick: (e: Event) => { e.stopPropagation(); emit('toggle-status', n.id) },
              }, n.status === 'active' ? '暂停' : '恢复'),
            ]),
          ]),
        ]),
        ...(n.children?.length
          ? n.children.map((child: AgentNode) =>
            h(OrgNode, {
              node: child,
              depth: props.depth + 1,
              onEdit: (id: string) => emit('edit', id),
              onAddChild: (id: string) => emit('add-child', id),
              onToggleStatus: (id: string) => emit('toggle-status', id),
              onShowDetail: (id: string) => emit('show-detail', id),
            })
          )
          : []),
      ])
    }
  },
})

/* ========== 状态 ========== */
const loading = ref(false)
const saving = ref(false)
const companyId = ref('')
const treeData = ref<AgentNode[]>([])
const flatAgents = ref<Agent[]>([])

const modalVisible = ref(false)
const editingAgent = ref<Agent | null>(null)
const form = reactive({
  name: '',
  title: '',
  provider: 'openai',
  parent_id: undefined as string | undefined,
  skills: [] as string[],
  budget_limit: 1000,
})

const drawerVisible = ref(false)
const drawerAgent = ref<Agent | null>(null)
const drawerTasks = ref<Task[]>([])
const drawerHeartbeats = ref<HeartbeatLog[]>([])
const drawerLoading = ref(false)

const taskColumns = [
  { title: '任务', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '状态', key: 'status', width: 80 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 140 },
]

/* ========== 工具函数 ========== */
function statusBadge(status: string) {
  const map: Record<string, string> = { active: 'success', paused: 'warning', offline: 'default', error: 'error' }
  return (map[status] || 'default') as 'success' | 'warning' | 'default' | 'error'
}

function statusLabel(status: string) {
  const map: Record<string, string> = { active: '活跃', paused: '已暂停', offline: '离线', error: '异常' }
  return map[status] || status
}

function budgetPercent(agent: any) {
  if (!agent.budget_limit) return 0
  return Math.round((agent.budget_used / agent.budget_limit) * 100)
}

function formatTime(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return dateStr
  }
}

function taskStatusColor(s: string) {
  const map: Record<string, string> = { pending: 'default', running: 'processing', completed: 'success', failed: 'error' }
  return map[s] || 'default'
}

function taskStatusLabel(s: string) {
  const map: Record<string, string> = { pending: '待执行', running: '执行中', completed: '已完成', failed: '失败' }
  return map[s] || s
}

/* ========== 数据加载 ========== */
async function loadTree() {
  loading.value = true
  try {
    if (!companyId.value) {
      const company = await myPaperclipAPI.getCompany()
      if (company?.id) companyId.value = company.id
    }
    if (companyId.value) {
      const [tree, agents] = await Promise.all([agentAPI.orgTree(companyId.value), agentAPI.list(companyId.value)])
      treeData.value = tree || []
      flatAgents.value = agents || []
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载组织架构失败')
  } finally {
    loading.value = false
  }
}

/* ========== 弹窗操作 ========== */
function openCreateModal(parentId?: string) {
  editingAgent.value = null
  resetForm()
  if (parentId) form.parent_id = parentId
  modalVisible.value = true
}

async function openEditModal(agentId: string) {
  try {
    const agent = await agentAPI.get(agentId)
    editingAgent.value = agent
    form.name = agent.name
    form.title = agent.title
    form.provider = agent.provider
    form.parent_id = agent.parent_id || undefined
    form.skills = [...(agent.skills || [])]
    form.budget_limit = agent.budget_limit
    modalVisible.value = true
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载 Agent 失败')
  }
}

function resetForm() {
  form.name = ''
  form.title = ''
  form.provider = 'openai'
  form.parent_id = undefined
  form.skills = []
  form.budget_limit = 1000
}

function resetModal() {
  modalVisible.value = false
  editingAgent.value = null
  resetForm()
}

async function handleSave() {
  if (!form.name || !form.title) {
    message.warning('请填写名称和头衔')
    return
  }
  saving.value = true
  try {
    if (editingAgent.value) {
      await agentAPI.update(editingAgent.value.id, { ...form } as any)
      message.success('Agent 已更新')
    } else {
      await agentAPI.hire(companyId.value, { ...form } as any)
      message.success('Agent 已创建')
    }
    modalVisible.value = false
    await loadTree()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleToggleStatus(agentId: string) {
  try {
    const agent = flatAgents.value.find((a) => a.id === agentId)
    if (!agent) return
    if (agent.status === 'active') {
      await agentAPI.pause(agentId)
      message.success('已暂停')
    } else {
      await agentAPI.resume(agentId)
      message.success('已恢复')
    }
    await loadTree()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '操作失败')
  }
}

/* ========== 抽屉操作 ========== */
async function openDetailDrawer(agentId: string) {
  drawerVisible.value = true
  drawerLoading.value = true
  try {
    const [agent, tasks, hbs] = await Promise.all([
      agentAPI.get(agentId),
      taskAPI.list(companyId.value, { agent_id: agentId }),
      heartbeatAPI.logs(companyId.value, { agent_id: agentId, limit: 10 }),
    ])
    drawerAgent.value = agent
    drawerTasks.value = (tasks || []).slice(0, 10)
    drawerHeartbeats.value = hbs || []
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载详情失败')
  } finally {
    drawerLoading.value = false
  }
}

onMounted(loadTree)
</script>

<style scoped lang="scss">
.org-chart-container {
  overflow-x: auto;
  padding: 16px 0;
}
.org-chart {
  min-width: 400px;
}

.org-node-wrap {
  position: relative;
  &::before {
    content: '';
    position: absolute;
    left: -16px;
    top: 0;
    bottom: 0;
    width: 1px;
    background: #e2e8f0;
  }
  &:first-child::before {
    display: none;
  }
}

.org-node-card {
  display: inline-block;
  min-width: 260px;
  max-width: 480px;
  padding: 12px 16px;
  margin: 6px 0;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;

  &:hover {
    border-color: #4F6AFF;
    box-shadow: 0 2px 12px rgba(79, 106, 255, 0.1);
  }
}
.org-node-active { border-left: 3px solid #10b981; }
.org-node-paused { border-left: 3px solid #f59e0b; }
.org-node-offline { border-left: 3px solid #94a3b8; }
.org-node-error { border-left: 3px solid #ef4444; }

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.node-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-active { background: #10b981; }
.status-paused { background: #f59e0b; }
.status-offline { background: #94a3b8; }
.status-error { background: #ef4444; }
.node-name {
  font-weight: 600;
  font-size: 14px;
}
.node-title {
  font-size: 12px;
  color: #64748b;
}

.node-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.node-provider {
  font-size: 11px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
}
.node-actions {
  display: flex;
  gap: 4px;
}
.node-btn {
  font-size: 11px;
  color: #4F6AFF;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  &:hover {
    background: #f0f2ff;
  }
}

.skill-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.budget-text {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
  display: block;
}
</style>
