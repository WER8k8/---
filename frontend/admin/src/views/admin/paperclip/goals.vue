<template>
  <YdPage surface="elevated" title="目标管理" subtitle="使命 → 项目 → 目标 → 任务 · 层级对齐链">
    <template #actions>
      <a-space>
        <a-button type="primary" @click="openCreateModal()">创建目标</a-button>
        <a-button :loading="loading" @click="loadGoals">刷新</a-button>
      </a-space>
    </template>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <a-select
        v-model:value="filterLevel"
        allow-clear
        placeholder="按级别筛选"
        style="width: 140px"
        @change="loadGoals"
      >
        <a-select-option value="mission">使命</a-select-option>
        <a-select-option value="project">项目</a-select-option>
        <a-select-option value="goal">目标</a-select-option>
        <a-select-option value="task">任务</a-select-option>
      </a-select>
      <a-select
        v-model:value="filterStatus"
        allow-clear
        placeholder="按状态筛选"
        style="width: 140px"
        @change="loadGoals"
      >
        <a-select-option value="pending">待开始</a-select-option>
        <a-select-option value="in_progress">进行中</a-select-option>
        <a-select-option value="completed">已完成</a-select-option>
        <a-select-option value="blocked">已阻塞</a-select-option>
      </a-select>
    </div>

    <!-- 目标树形表格 -->
    <a-table
      :columns="columns"
      :data-source="goalTree"
      :loading="loading"
      :pagination="false"
      row-key="id"
      :default-expand-all-rows="true"
      size="middle"
      :locale="{ emptyText: '暂无目标，点击右上角创建' }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'level'">
          <a-tag :color="levelColor(record.level)">{{ levelLabel(record.level) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'progress'">
          <a-progress
            :percent="record.progress"
            :status="record.progress >= 100 ? 'success' : 'active'"
            size="small"
            :stroke-color="record.progress >= 100 ? '#10b981' : '#4F6AFF'"
          />
        </template>
        <template v-else-if="column.key === 'priority'">
          <a-tag :color="priorityColor(record.priority)">{{ priorityLabel(record.priority) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="openCreateModal(record.id, record.level)">创建子目标</a-button>
            <a-button type="link" size="small" @click="openEditModal(record as Goal)">编辑</a-button>
            <a-button type="link" size="small" @click="showAlignmentChain(record.id)">对齐链</a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 创建/编辑目标弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingGoal ? '编辑目标' : '创建目标'"
      :confirm-loading="saving"
      @ok="handleSave"
      @cancel="resetModal"
      :width="560"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="标题" required>
          <a-input v-model:value="form.title" placeholder="目标标题" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" placeholder="目标描述" :rows="3" />
        </a-form-item>
        <a-form-item label="级别" required>
          <a-select v-model:value="form.level" placeholder="选择级别">
            <a-select-option value="mission">使命</a-select-option>
            <a-select-option value="project">项目</a-select-option>
            <a-select-option value="goal">目标</a-select-option>
            <a-select-option value="task">任务</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="上级目标">
          <a-select
            v-model:value="form.parent_id"
            placeholder="无（顶级目标）"
            allow-clear
          >
            <a-select-option v-for="g in flatGoals" :key="g.id" :value="g.id">
              [{{ levelLabel(g.level) }}] {{ g.title }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="负责 Agent">
          <a-select
            v-model:value="form.assigned_agent_id"
            placeholder="选择 Agent"
            allow-clear
          >
            <a-select-option v-for="a in agentList" :key="a.id" :value="a.id">
              {{ a.name }} - {{ a.title }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="优先级">
          <a-select v-model:value="form.priority" placeholder="选择优先级">
            <a-select-option value="low">低</a-select-option>
            <a-select-option value="medium">中</a-select-option>
            <a-select-option value="high">高</a-select-option>
            <a-select-option value="critical">紧急</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 对齐链弹窗 -->
    <a-modal
      v-model:open="chainVisible"
      title="目标对齐链"
      :footer="null"
      :width="500"
    >
      <template v-if="chainLoading">
        <SkeletonCard variant="text" />
      </template>
      <template v-else>
        <div v-if="alignmentChain.length" class="alignment-chain-modal">
          <div v-for="(node, idx) in alignmentChain" :key="node.id" class="chain-item">
            <div class="chain-dot-line">
              <span class="chain-dot" :class="{ 'chain-dot-current': idx === alignmentChain.length - 1 }" />
              <span v-if="idx < alignmentChain.length - 1" class="chain-line" />
            </div>
            <div class="chain-info">
              <a-tag :color="levelColor(node.level)" size="small">{{ levelLabel(node.level) }}</a-tag>
              <span class="chain-title">{{ node.title }}</span>
            </div>
          </div>
        </div>
        <a-empty v-else description="暂无对齐链数据" />
      </template>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { goalAPI, agentAPI, myPaperclipAPI, type Goal, type Agent, type AlignmentNode } from '@/api/paperclip'

const loading = ref(false)
const saving = ref(false)
const companyId = ref('')
const goals = ref<Goal[]>([])
const flatGoals = ref<Goal[]>([])
const agentList = ref<Agent[]>([])
const filterLevel = ref<string | undefined>()
const filterStatus = ref<string | undefined>()

const modalVisible = ref(false)
const editingGoal = ref<Goal | null>(null)
const chainVisible = ref(false)
const chainLoading = ref(false)
const alignmentChain = ref<AlignmentNode[]>([])

const form = reactive({
  title: '',
  description: '',
  level: 'goal' as string,
  parent_id: undefined as string | undefined,
  assigned_agent_id: undefined as string | undefined,
  priority: 'medium' as string,
})

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '级别', key: 'level', width: 80 },
  { title: '负责 Agent', dataIndex: 'assigned_agent_name', key: 'assigned_agent_name', width: 120 },
  { title: '状态', key: 'status', width: 80 },
  { title: '进度', key: 'progress', width: 160 },
  { title: '优先级', key: 'priority', width: 80 },
  { title: '操作', key: 'action', width: 220 },
]

/* 将扁平列表构建为树 */
const goalTree = computed(() => {
  const map = new Map<string, any>()
  const roots: any[] = []
  for (const g of goals.value) {
    map.set(g.id, { ...g, children: [] })
  }
  for (const g of goals.value) {
    const node = map.get(g.id)!
    if (g.parent_id && map.has(g.parent_id)) {
      map.get(g.parent_id)!.children.push(node)
    } else {
      roots.push(node)
    }
  }
  return roots
})

/* 工具函数 */
function levelColor(level: string) {
  const map: Record<string, string> = { mission: 'purple', project: 'blue', goal: 'cyan', task: 'green' }
  return map[level] || 'default'
}
function levelLabel(level: string) {
  const map: Record<string, string> = { mission: '使命', project: '项目', goal: '目标', task: '任务' }
  return map[level] || level
}
function statusColor(status: string) {
  const map: Record<string, string> = { pending: 'default', in_progress: 'processing', completed: 'success', blocked: 'error' }
  return map[status] || 'default'
}
function statusLabel(status: string) {
  const map: Record<string, string> = { pending: '待开始', in_progress: '进行中', completed: '已完成', blocked: '已阻塞' }
  return map[status] || status
}
function priorityColor(p: string) {
  const map: Record<string, string> = { low: 'default', medium: 'blue', high: 'orange', critical: 'red' }
  return map[p] || 'default'
}
function priorityLabel(p: string) {
  const map: Record<string, string> = { low: '低', medium: '中', high: '高', critical: '紧急' }
  return map[p] || p
}

/* 数据加载 */
async function loadGoals() {
  loading.value = true
  try {
    if (!companyId.value) {
      const company = await myPaperclipAPI.getCompany()
      if (company?.id) companyId.value = company.id
    }
    if (!companyId.value) return
    const params: Record<string, string> = {}
    if (filterLevel.value) params.level = filterLevel.value
    if (filterStatus.value) params.status = filterStatus.value
    goals.value = (await goalAPI.list(companyId.value, params)) || []
    flatGoals.value = goals.value
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载目标失败')
  } finally {
    loading.value = false
  }
}

async function loadAgents() {
  try {
    if (companyId.value) {
      agentList.value = (await agentAPI.list(companyId.value)) || []
    }
  } catch { /* 静默 */ }
}

/* 弹窗操作 */
function openCreateModal(parentId?: string, parentLevel?: string) {
  editingGoal.value = null
  resetForm()
  if (parentId) {
    form.parent_id = parentId
    // 自动推断子级别
    const childLevel = nextLevel(parentLevel)
    if (childLevel) form.level = childLevel
  }
  modalVisible.value = true
}

function openEditModal(goal: Goal) {
  editingGoal.value = goal
  form.title = goal.title
  form.description = goal.description
  form.level = goal.level
  form.parent_id = goal.parent_id || undefined
  form.assigned_agent_id = goal.assigned_agent_id || undefined
  form.priority = goal.priority
  modalVisible.value = true
}

function nextLevel(level?: string): string | undefined {
  const order = ['mission', 'project', 'goal', 'task']
  const idx = order.indexOf(level || '')
  return idx >= 0 && idx < order.length - 1 ? order[idx + 1] : undefined
}

function resetForm() {
  form.title = ''
  form.description = ''
  form.level = 'goal'
  form.parent_id = undefined
  form.assigned_agent_id = undefined
  form.priority = 'medium'
}

function resetModal() {
  modalVisible.value = false
  editingGoal.value = null
  resetForm()
}

async function handleSave() {
  if (!form.title) {
    message.warning('请填写目标标题')
    return
  }
  saving.value = true
  try {
    if (editingGoal.value) {
      await goalAPI.update(editingGoal.value.id, { ...form } as Partial<Goal>)
      message.success('目标已更新')
    } else {
      await goalAPI.create(companyId.value, { ...form } as Partial<Goal>)
      message.success('目标已创建')
    }
    modalVisible.value = false
    await loadGoals()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

async function showAlignmentChain(goalId: string) {
  chainVisible.value = true
  chainLoading.value = true
  alignmentChain.value = []
  try {
    alignmentChain.value = (await goalAPI.alignmentChain(goalId)) || []
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载对齐链失败')
  } finally {
    chainLoading.value = false
  }
}

onMounted(async () => {
  await loadGoals()
  await loadAgents()
})
</script>

<style scoped lang="scss">
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.alignment-chain-modal {
  padding: 8px 0;
}
.chain-item {
  display: flex;
  gap: 12px;
  min-height: 48px;
}
.chain-dot-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
  flex-shrink: 0;
}
.chain-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #cbd5e1;
  flex-shrink: 0;
  margin-top: 4px;
}
.chain-dot-current {
  background: #4F6AFF;
  box-shadow: 0 0 0 3px rgba(79, 106, 255, 0.2);
}
.chain-line {
  width: 2px;
  flex: 1;
  background: #e2e8f0;
  margin: 2px 0;
}
.chain-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 12px;
}
.chain-title {
  font-weight: 500;
  font-size: 13px;
}
</style>
