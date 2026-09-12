<template>
  <YdPage surface="elevated" title="心跳监控" subtitle="心跳引擎控制 · Agent 健康状态 · 历史日志">
    <template #actions>
      <a-space>
        <a-button
          :type="engineStatus.running ? 'default' : 'primary'"
          :loading="engineLoading"
          @click="toggleEngine"
        >
          {{ engineStatus.running ? '停止引擎' : '启动引擎' }}
        </a-button>
        <a-button :loading="triggering" @click="handleManualTrigger">手动触发心跳</a-button>
        <a-button :loading="loading" @click="loadAll">刷新</a-button>
      </a-space>
    </template>

    <!-- 引擎状态卡片 -->
    <a-card size="small" class="engine-card">
      <div class="engine-row">
        <div class="engine-item">
          <span class="engine-label">引擎状态</span>
          <a-badge
            :status="engineStatus.running ? 'success' : 'default'"
            :text="engineStatus.running ? '运行中' : '已停止'"
          />
        </div>
        <div class="engine-item">
          <span class="engine-label">下次心跳</span>
          <span class="engine-value">
            {{ engineStatus.next_heartbeat ? formatTime(engineStatus.next_heartbeat) : '--' }}
          </span>
        </div>
        <div class="engine-item">
          <span class="engine-label">活跃 Agent</span>
          <a-statistic :value="engineStatus.active_agents" :value-style="{ fontSize: '20px' }" />
        </div>
      </div>
    </a-card>

    <!-- Agent 心跳状态表格 -->
    <a-card title="Agent 心跳状态" size="small" class="mt-4">
      <a-table
        :columns="agentColumns"
        :data-source="agentStatuses"
        :loading="loading"
        :pagination="false"
        row-key="id"
        size="middle"
        :locale="{ emptyText: '暂无 Agent' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-badge
              :status="record.status === 'active' ? 'success' : record.status === 'error' ? 'error' : 'warning'"
              :text="agentStatusLabel(record.status)"
            />
          </template>
          <template v-else-if="column.key === 'last_heartbeat'">
            {{ record.last_heartbeat ? formatTime(record.last_heartbeat) : '从未' }}
          </template>
          <template v-else-if="column.key === 'success_rate'">
            <a-progress
              :percent="record.success_rate || 0"
              :status="(record.success_rate || 0) >= 80 ? 'success' : 'exception'"
              size="small"
              :stroke-color="(record.success_rate || 0) >= 80 ? '#10b981' : '#ef4444'"
            />
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" size="small" @click="triggerSingle(record.id)">触发心跳</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 心跳历史日志 -->
    <a-card title="心跳历史日志" size="small" class="mt-4">
      <template #extra>
        <a-select
          v-model:value="logFilterAgent"
          allow-clear
          placeholder="按 Agent 筛选"
          style="width: 200px"
          @change="loadLogs"
        >
          <a-select-option v-for="a in agentStatuses" :key="a.id" :value="a.id">
            {{ a.name }}
          </a-select-option>
        </a-select>
      </template>
      <a-table
        :columns="logColumns"
        :data-source="logs"
        :loading="logsLoading"
        :pagination="{ pageSize: 20, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }"
        row-key="id"
        size="middle"
        :locale="{ emptyText: '暂无心跳日志' }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'trigger_type'">
            <a-tag :color="record.trigger_type === 'auto' ? 'blue' : 'purple'">
              {{ record.trigger_type === 'auto' ? '自动' : '手动' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'result'">
            <a-tag :color="record.result === 'success' ? 'green' : record.result === 'failure' ? 'red' : 'orange'">
              {{ record.result === 'success' ? '成功' : record.result === 'failure' ? '失败' : '超时' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ formatTime(record.created_at) }}
          </template>
        </template>
      </a-table>
    </a-card>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import {
  myPaperclipAPI,
  agentAPI,
  heartbeatAPI,
  type Agent,
  type HeartbeatLog,
  type HeartbeatEngineStatus,
} from '@/api/paperclip'

const loading = ref(false)
const logsLoading = ref(false)
const engineLoading = ref(false)
const triggering = ref(false)
const companyId = ref('')
const logFilterAgent = ref<string | undefined>()

const engineStatus = reactive<HeartbeatEngineStatus>({
  running: false,
  next_heartbeat: null,
  active_agents: 0,
})

const agentStatuses = ref<(Agent & { success_rate?: number })[]>([])
const logs = ref<HeartbeatLog[]>([])

const agentColumns = [
  { title: 'Agent', dataIndex: 'name', key: 'name', width: 140 },
  { title: '头衔', dataIndex: 'title', key: 'title', width: 140 },
  { title: '状态', key: 'status', width: 100 },
  { title: '上次心跳', key: 'last_heartbeat', width: 160 },
  { title: '成功率', key: 'success_rate', width: 140 },
  { title: '操作', key: 'action', width: 100 },
]

const logColumns = [
  { title: 'Agent', dataIndex: 'agent_name', key: 'agent_name', width: 120 },
  { title: '触发方式', key: 'trigger_type', width: 100 },
  { title: '结果', key: 'result', width: 80 },
  { title: '信息', dataIndex: 'message', key: 'message', ellipsis: true },
  { title: '时间', key: 'created_at', width: 160 },
]

function agentStatusLabel(status: string) {
  const map: Record<string, string> = { active: '活跃', paused: '已暂停', offline: '离线', error: '异常' }
  return map[status] || status
}

function formatTime(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleString('zh-CN', {
      month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
    })
  } catch {
    return dateStr
  }
}

async function loadEngineStatus() {
  try {
    const status = await heartbeatAPI.status()
    Object.assign(engineStatus, status)
  } catch { /* 静默 */ }
}

async function loadAgents() {
  loading.value = true
  try {
    if (!companyId.value) {
      const company = await myPaperclipAPI.getCompany()
      if (company?.id) companyId.value = company.id
    }
    if (companyId.value) {
      agentStatuses.value = (await agentAPI.list(companyId.value)) || []
    }
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载 Agent 列表失败')
  } finally {
    loading.value = false
  }
}

async function loadLogs() {
  logsLoading.value = true
  try {
    if (!companyId.value) return
    const params: Record<string, string | number> = { limit: 100 }
    if (logFilterAgent.value) params.agent_id = logFilterAgent.value
    logs.value = (await heartbeatAPI.logs(companyId.value, params)) || []
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '加载日志失败')
  } finally {
    logsLoading.value = false
  }
}

async function loadAll() {
  await loadAgents()
  await Promise.all([loadEngineStatus(), loadLogs()])
}

async function toggleEngine() {
  engineLoading.value = true
  try {
    if (engineStatus.running) {
      await heartbeatAPI.stopEngine()
      message.success('引擎已停止')
    } else {
      await heartbeatAPI.startEngine()
      message.success('引擎已启动')
    }
    await loadEngineStatus()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '操作失败')
  } finally {
    engineLoading.value = false
  }
}

async function handleManualTrigger() {
  triggering.value = true
  try {
    const agents = agentStatuses.value.filter((a) => a.status === 'active')
    if (agents.length) {
      await Promise.all(agents.map((a) => heartbeatAPI.trigger(a.id)))
      message.success(`已触发 ${agents.length} 个 Agent 心跳`)
    } else {
      message.warning('暂无活跃 Agent 可触发')
    }
    await loadAll()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '触发失败')
  } finally {
    triggering.value = false
  }
}

async function triggerSingle(agentId: string) {
  try {
    await heartbeatAPI.trigger(agentId)
    message.success('心跳触发成功')
    await loadLogs()
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '触发失败')
  }
}

onMounted(loadAll)
</script>

<style scoped lang="scss">
.engine-card {
  margin-bottom: 0;
}
.engine-row {
  display: flex;
  gap: 48px;
  flex-wrap: wrap;
}
.engine-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.engine-label {
  font-size: 12px;
  color: #64748b;
}
.engine-value {
  font-size: 14px;
  font-weight: 500;
}
.mt-4 {
  margin-top: 16px;
}
</style>
