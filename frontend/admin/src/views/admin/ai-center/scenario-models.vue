<template>
  <YdPage title="场景模型切换" subtitle="不同功能使用不同模型：文章、视频、对话等场景独立配置，保存后立即生效。" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="checkHealth" :loading="healthLoading">健康检查</a-button>
        <a-button @click="loadData" :loading="loading">刷新</a-button>
        <a-button type="primary" :loading="saving" :disabled="!dirty" @click="saveAll">
          <SaveOutlined /> 保存全部
        </a-button>
      </a-space>
    </template>
  <div class="scenario-models-page">

    <a-alert
      v-if="healthSummary"
      :type="healthSummary.unhealthy_count === 0 ? 'success' : 'warning'"
      show-icon
      style="margin-bottom: 16px"
      :message="healthAlertMessage"
    />

    <a-alert
      v-if="note"
      type="info"
      show-icon
      :message="note"
      style="margin-bottom: 20px"
    />

    <template v-if="loading">
      <SkeletonCard variant="card" />
    </template>
    <template v-else>
      <div v-for="group in groups" :key="group.id" class="scenario-group">
        <h2 class="group-title">{{ group.label }}</h2>
        <div class="scenario-grid">
          <a-card
            v-for="sc in group.scenarios"
            :key="sc.id"
            class="scenario-card"
            :class="{ active: localMappings[sc.id] !== originalMappings[sc.id] }"
          >
            <div class="sc-head">
              <div>
                <div class="sc-label">{{ sc.label }}</div>
                <div class="sc-desc">{{ sc.description }}</div>
              </div>
              <a-tag :color="endpointColor(sc.endpoint)">{{ endpointLabel(sc.endpoint) }}</a-tag>
            </div>

            <a-select
              v-model:value="localMappings[sc.id]"
              show-search
              style="width: 100%; margin-top: 12px"
              :filter-option="filterOption"
              placeholder="选择模型"
            >
              <a-select-option
                v-for="m in sc.candidates"
                :key="m.id"
                :value="m.id"
              >
                {{ m.id }}
              </a-select-option>
            </a-select>

            <div class="sc-foot">
              <span class="sc-current">当前：{{ localMappings[sc.id] || sc.current_model || '未设置' }}</span>
              <a-tag v-if="healthMap[sc.id]" :color="healthMap[sc.id].healthy ? 'success' : 'error'" size="small">
                {{ healthMap[sc.id].healthy ? `${healthMap[sc.id].latency_ms}ms` : '异常' }}
              </a-tag>
              <a-button type="link" size="small" @click="resetOne(sc.id, sc.current_model)">恢复默认</a-button>
            </div>
          </a-card>
        </div>
      </div>
    </template>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { SaveOutlined } from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { apiGet, apiPut } from '@/utils/api'

interface Candidate {
  id: string
  endpoint?: string
  description?: string
}

interface ScenarioRow {
  id: string
  label: string
  description: string
  group: string
  current_model: string
  endpoint: string
  candidates: Candidate[]
}

interface ScenarioGroup {
  id: string
  label: string
  scenarios: ScenarioRow[]
}

const loading = ref(false)
const saving = ref(false)
const healthLoading = ref(false)
const note = ref('')
const healthSummary = ref<{ healthy_count: number; unhealthy_count: number; total: number } | null>(null)
const healthSavedAt = ref('')
const healthMap = reactive<Record<string, { healthy: boolean; latency_ms?: number }>>({})
const groups = ref<ScenarioGroup[]>([])
const localMappings = reactive<Record<string, string>>({})
const originalMappings = reactive<Record<string, string>>({})

const dirty = computed(() =>
  Object.keys(localMappings).some(k => localMappings[k] !== originalMappings[k]),
)

const healthAlertMessage = computed(() => {
  if (!healthSummary.value) return ''
  const base = `健康 ${healthSummary.value.healthy_count}/${healthSummary.value.total} · 异常 ${healthSummary.value.unhealthy_count}`
  return healthSavedAt.value ? `${base} · 快照 ${formatSavedAt(healthSavedAt.value)}` : base
})

function formatSavedAt(iso: string) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function applyHealthReport(data: {
  healthy_count?: number
  unhealthy_count?: number
  total?: number
  saved_at?: string
  scenarios?: Array<{ scenario: string; healthy: boolean; latency_ms?: number }>
} | null | undefined) {
  if (!data) return
  healthSummary.value = {
    healthy_count: data.healthy_count || 0,
    unhealthy_count: data.unhealthy_count || 0,
    total: data.total || 0,
  }
  healthSavedAt.value = data.saved_at || ''
  Object.keys(healthMap).forEach(k => delete healthMap[k])
  for (const row of data.scenarios || []) {
    healthMap[row.scenario] = { healthy: row.healthy, latency_ms: row.latency_ms }
  }
}

function filterOption(input: string, option: any) {
  return String(option?.value || '').toLowerCase().includes(input.toLowerCase())
}

function endpointLabel(endpoint?: string) {
  return endpoint === '/v1/infer' ? '视频 infer' : '对话 chat'
}

function endpointColor(endpoint?: string) {
  return endpoint === '/v1/infer' ? 'purple' : 'green'
}

function resetOne(id: string, fallback?: string) {
  localMappings[id] = originalMappings[id] || fallback || ''
}

async function loadData() {
  loading.value = true
  try {
    const data = await apiGet<{
      groups: ScenarioGroup[]
      note?: string
      mappings?: Record<string, string>
    }>('/super-admin/ai-config/nvidia/scenarios')

    groups.value = data?.groups || []
    note.value = data?.note || ''
    Object.keys(localMappings).forEach(k => delete localMappings[k])
    Object.keys(originalMappings).forEach(k => delete originalMappings[k])

    const mappings = data?.mappings || {}
    for (const g of groups.value) {
      for (const sc of g.scenarios) {
        const val = mappings[sc.id] || sc.current_model || ''
        localMappings[sc.id] = val
        originalMappings[sc.id] = val
      }
    }
  } catch {
    message.error('加载场景配置失败，请先完成 NVIDIA API 接入')
  } finally {
    loading.value = false
  }
}

async function checkHealth() {
  healthLoading.value = true
  try {
    const data = await apiGet<{
      healthy_count: number
      unhealthy_count: number
      total: number
      saved_at?: string
      scenarios: Array<{ scenario: string; healthy: boolean; latency_ms?: number }>
    }>('/super-admin/ai-config/nvidia/scenarios/health')
    applyHealthReport(data)
    message.success('场景健康检查完成')
  } catch (err: any) {
    message.error(err?.message || '健康检查失败')
  } finally {
    healthLoading.value = false
  }
}

async function loadLatestHealthSnapshot() {
  try {
    const data = await apiGet<{
      healthy_count: number
      unhealthy_count: number
      total: number
      saved_at?: string
      scenarios: Array<{ scenario: string; healthy: boolean; latency_ms?: number }>
    } | null>('/super-admin/ai-config/nvidia/scenarios/health/latest')
    applyHealthReport(data)
  } catch {
    /* 无快照时忽略 */
  }
}

async function saveAll() {
  saving.value = true
  try {
    const res = await apiPut<{ mappings: Record<string, string> }>(
      '/super-admin/ai-config/nvidia/scenarios',
      { mappings: { ...localMappings } },
    )
    const saved = res?.mappings || { ...localMappings }
    Object.assign(originalMappings, saved)
    Object.assign(localMappings, saved)
    message.success('场景模型已保存，各功能将使用对应模型')
  } catch (err: any) {
    message.error(err?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadData()
  await loadLatestHealthSnapshot()
})
</script>

<style scoped>
.scenario-models-page {
  max-width: 1100px;
  margin: 0 auto;
}
.scenario-group {
  margin-bottom: 28px;
}
.group-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0 0 12px;
  color: #374151;
}
.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}
.scenario-card {
  border-radius: 12px;
  transition: box-shadow 0.2s, border-color 0.2s;
}
.scenario-card.active {
  border-color: #722ed1;
  box-shadow: 0 0 0 1px rgba(114, 46, 209, 0.15);
}
.sc-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;
}
.sc-label {
  font-weight: 600;
  color: #111827;
}
.sc-desc {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
  line-height: 1.4;
}
.sc-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  font-size: 11px;
  color: #6b7280;
}
.sc-current {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}
</style>
