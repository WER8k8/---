<template>
  <a-alert
    v-if="loaded"
    :type="alertType"
    show-icon
    class="aitoearn-capability-bar mb-4"
    :message="headline"
  >
    <template #description>
      <p class="aitoearn-capability-bar__desc">{{ description }}</p>
      <div v-if="platforms.length" class="aitoearn-capability-bar__tags">
        <a-tag v-for="p in platforms.slice(0, 8)" :key="p">{{ p }}</a-tag>
        <a-tag v-if="platforms.length > 8">+{{ platforms.length - 8 }}</a-tag>
      </div>
      <a-space v-if="showActions" class="mt-2" wrap>
        <router-link to="/client/cross-platform">跨平台数据 →</router-link>
        <router-link to="/client/engage">评论互动 →</router-link>
      </a-space>
    </template>
  </a-alert>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { apiGet } from '@/utils/api'

type CapModules = {
  publish?: { available?: boolean }
  engage?: { available?: boolean }
  create?: { available?: boolean }
  analytics?: { available?: boolean }
}

const loaded = ref(false)
const enabled = ref(false)
const platforms = ref<string[]>([])
const modules = ref<CapModules>({})
const slotAssigned = ref(false)

const alertType = computed(() => {
  if (!enabled.value) return 'info'
  if (modules.value.publish?.available) return 'success'
  return 'warning'
})

const headline = computed(() => {
  if (!enabled.value) return 'AiToEarn 未配置 — 视频真发与自动回评需运维配置 Key'
  if (modules.value.publish?.available) return `AiToEarn 已连通 · ${platforms.value.length} 平台矩阵`
  if (!slotAssigned.value) return 'AiToEarn 已连通 — 待超管分配租户矩阵号'
  return 'AiToEarn 已连通 — 请完成平台绑号'
})

const description = computed(() => {
  const parts: string[] = []
  if (modules.value.create?.available) parts.push('Create：AI 生成 + 素材库')
  if (modules.value.publish?.available) parts.push('Publish：多平台真发 + 定时排期')
  else parts.push('Publish：需 Key + 矩阵槽位')
  if (modules.value.engage?.available) parts.push('Engage：评论拉取 + 真回复')
  else parts.push('Engage：需矩阵槽位')
  if (modules.value.analytics?.available) parts.push('Analytics：跨平台看板')
  return parts.join(' · ')
})

const showActions = computed(() => enabled.value)

async function load() {
  try {
    const data = await apiGet<{
      aitoearn_enabled?: boolean
      platforms?: string[]
      modules?: CapModules
      tenant_slot?: { assigned?: boolean }
    }>('/aitoearn/hub/capabilities')
    enabled.value = Boolean(data?.aitoearn_enabled)
    platforms.value = Array.isArray(data?.platforms) ? data.platforms : []
    modules.value = data?.modules || {}
    slotAssigned.value = Boolean(data?.tenant_slot?.assigned)
  } catch {
    enabled.value = false
  } finally {
    loaded.value = true
  }
}

onMounted(() => {
  void load()
})

defineExpose({ reload: load })
</script>

<style scoped>
.mb-4 { margin-bottom: 16px; }
.mt-2 { margin-top: 8px; }
.aitoearn-capability-bar__desc { margin: 0 0 8px; color: var(--uj-text-secondary, #64748b); }
.aitoearn-capability-bar__tags { display: flex; flex-wrap: wrap; gap: 4px; }
</style>
