/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="AI 场景模型" subtitle="为各业务场景指定具体模型，留空则使用平台默认" surface="elevated">
    <template #actions>
      <a-button @click="loadData" :loading="loading">刷新</a-button>
      <a-button type="primary" :loading="saving" :disabled="!dirty" @click="saveAll">保存</a-button>
    </template>
  <div class="p-4 max-w-4xl mx-auto space-y-4">
    <a-alert
      v-if="tenantName"
      type="info"
      show-icon
      :message="`租户：${tenantName}`"
      description="留空表示使用平台默认；保存后立即对本租户 AI 调用生效。"
    />

    <template v-if="loading">
      <SkeletonCard variant="card" />
    </template>
    <template v-else>
      <div class="grid gap-3 sm:grid-cols-2">
        <a-card v-for="sc in scenarios" :key="sc.id" size="small" class="scenario-card">
          <div class="font-medium text-gray-900">{{ sc.label }}</div>
          <div class="text-xs text-gray-400 mt-1 mb-3">{{ sc.description }}</div>

          <div class="text-xs text-gray-500 mb-1">
            平台默认：<span class="font-mono">{{ sc.platform_model || '—' }}</span>
          </div>
          <div v-if="sc.override_model" class="text-xs text-primary-600 mb-2">
            当前覆盖：<span class="font-mono">{{ sc.override_model }}</span>
          </div>

          <a-select
            v-model:value="localOverrides[sc.id]"
            allow-clear
            show-search
            placeholder="使用平台默认"
            style="width: 100%"
            :filter-option="filterOption"
          >
            <a-select-option v-for="m in sc.candidates" :key="m.id" :value="m.id">
              {{ m.id }}
            </a-select-option>
          </a-select>

          <div class="text-xs text-gray-400 mt-2">
            生效模型：<span class="font-mono text-gray-600">{{ effectivePreview(sc) }}</span>
          </div>
        </a-card>
      </div>
    </template>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import SkeletonCard from '@/components/common/SkeletonCard.vue';
import { apiGet, apiPut } from '@/utils/api';

const router = useRouter();

interface Candidate {
  id: string
}

interface ScenarioRow {
  id: string
  label: string
  description?: string
  platform_model?: string
  override_model?: string
  effective_model?: string
  candidates: Candidate[]
}

const loading = ref(false)
const saving = ref(false)
const tenantName = ref('')
const scenarios = ref<ScenarioRow[]>([])
const localOverrides = reactive<Record<string, string | undefined>>({})
const originalOverrides = reactive<Record<string, string | undefined>>({})

const dirty = computed(() =>
  Object.keys({ ...localOverrides, ...originalOverrides }).some(
    k => (localOverrides[k] || '') !== (originalOverrides[k] || ''),
  ),
)

function filterOption(input: string, option: any) {
  return String(option?.value || '').toLowerCase().includes(input.toLowerCase())
}

function effectivePreview(sc: ScenarioRow) {
  const picked = (localOverrides[sc.id] || '').trim()
  if (picked) return picked
  return sc.platform_model || sc.effective_model || '—'
}

async function loadData() {
  loading.value = true
  try {
    const data = await apiGet<{
      tenant_name?: string
      scenarios?: ScenarioRow[]
      overrides?: Record<string, string>
    }>('/tenants/self/ai-scenarios')

    tenantName.value = data?.tenant_name || ''
    scenarios.value = data?.scenarios || []

    Object.keys(localOverrides).forEach(k => delete localOverrides[k])
    Object.keys(originalOverrides).forEach(k => delete originalOverrides[k])

    for (const sc of scenarios.value) {
      const val = sc.override_model || undefined
      localOverrides[sc.id] = val
      originalOverrides[sc.id] = val
    }
  } catch (err: any) {
    message.error(err?.message || '加载失败，请确认已登录租户账号')
  } finally {
    loading.value = false
  }
}

async function saveAll() {
  saving.value = true
  try {
    const overrides: Record<string, string> = {}
    for (const sc of scenarios.value) {
      const val = (localOverrides[sc.id] || '').trim()
      if (val) overrides[sc.id] = val
      else overrides[sc.id] = ''
    }
    await apiPut('/tenants/self/ai-scenarios', { overrides })
    message.success('租户场景模型已保存')
    await loadData()
  } catch (err: any) {
    message.error(err?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.scenario-card {
  border-radius: 12px;
}
</style>
