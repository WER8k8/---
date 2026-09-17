/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <section class="readiness-bar">
    <template v-if="loading">
      <SkeletonCard variant="kpi" />
    </template>
    <template v-else>
      <div class="rb-grid">
        <div class="rb-item" :class="{ ok: data?.site_built }">
          <span class="rb-label">官网建站</span>
          <strong>{{ data?.site_built ? '已完成' : '待建站' }}</strong>
        </div>
        <div class="rb-item" :class="{ ok: egressOk }">
          <span class="rb-label">静态 IP 槽位</span>
          <strong>
            {{ data?.egress?.assigned_count ?? 0 }}/{{ data?.egress?.quota ?? 0 }}
            <span v-if="(data?.egress?.remaining ?? 0) > 0" class="rb-hint">可再申请</span>
          </strong>
        </div>
        <div class="rb-item" :class="{ ok: bindOk }">
          <span class="rb-label">平台绑号</span>
          <strong>
            文章 {{ data?.platform_accounts_bound ?? 0 }}
            · 视频 {{ data?.video_bind?.bound_local ?? 0 }}/{{ data?.video_bind?.video_platforms ?? 0 }}
          </strong>
        </div>
        <div class="rb-item" :class="{ ok: data?.ready_to_publish }">
          <span class="rb-label">可外发</span>
          <strong>{{ data?.ready_to_publish ? '就绪' : '先完成绑号' }}</strong>
        </div>
      </div>

      <a-alert
        v-if="data?.bind_disclaimer && !data?.ready_to_publish"
        type="info"
        show-icon
        class="rb-alert"
        :message="data.bind_disclaimer"
      />

      <div v-if="data?.next_actions?.length" class="rb-actions">
        <span class="rb-next-label">建议下一步：</span>
        <a-space wrap>
          <a-button
            v-for="a in data.next_actions"
            :key="a.id"
            size="small"
            :type="a.id === 'bind' || a.id === 'bind_more' ? 'primary' : 'default'"
            @click="emit('action', a)"
          >
            {{ a.label }}
          </a-button>
        </a-space>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { apiGet } from '@/utils/api'

export type ReadinessAction = { id: string; label: string; path: string }

export type PublishReadiness = {
  site_built?: boolean
  ready_to_publish?: boolean
  bind_disclaimer?: string
  platform_accounts_bound?: number
  egress?: { quota?: number; assigned_count?: number; remaining?: number }
  video_bind?: { bound_local?: number; video_platforms?: number }
  next_actions?: ReadinessAction[]
}

const emit = defineEmits<{
  (e: 'action', action: ReadinessAction): void
  (e: 'loaded', data: PublishReadiness | null): void
}>()

const loading = ref(false)
const data = ref<PublishReadiness | null>(null)

const egressOk = computed(() => {
  const q = data.value?.egress?.quota ?? 0
  const a = data.value?.egress?.assigned_count ?? 0
  return q === 0 || a > 0
})

const bindOk = computed(() => {
  const article = data.value?.platform_accounts_bound ?? 0
  const video = data.value?.video_bind?.bound_local ?? 0
  return article > 0 || video > 0
})

async function load() {
  loading.value = true
  try {
    data.value = await apiGet<PublishReadiness>('/client/publish-readiness')
    emit('loaded', data.value)
  } catch {
    data.value = null
    emit('loaded', null)
  } finally {
    loading.value = false
  }
}

onMounted(load)
defineExpose({ reload: load })
</script>

<style scoped>
.readiness-bar {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
}
.rb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}
.rb-item {
  padding: 8px 10px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  font-size: 13px;
}
.rb-item.ok {
  border-color: #86efac;
  background: #f0fdf4;
}
.rb-label {
  display: block;
  font-size: 11px;
  color: #64748b;
  margin-bottom: 2px;
}
.rb-hint {
  font-size: 11px;
  color: #16a34a;
  font-weight: normal;
}
.rb-alert {
  margin-top: 12px;
}
.rb-actions {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.rb-next-label {
  font-size: 12px;
  color: #64748b;
}
</style>
