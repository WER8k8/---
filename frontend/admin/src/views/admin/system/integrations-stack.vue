/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="集成栈状态" subtitle="FastAPI 主栈与可选 Node seo-backend 健康一览" surface="elevated">
    <template #actions>
      <a-button type="primary" :loading="loading" @click="load">刷新</a-button>
    </template>
    <template v-if="loading">
      <SkeletonCard variant="card" />
    </template>
    <template v-else>
      <a-descriptions v-if="status" bordered size="small" :column="1">
        <a-descriptions-item label="主栈">{{ status.primary }}</a-descriptions-item>
        <a-descriptions-item label="SEO 矩阵路由数">
          {{ status.fastapi_routes?.seo_matrix }}
        </a-descriptions-item>
        <a-descriptions-item label="高级 SEO 路由数">
          {{ status.fastapi_routes?.seo_advanced }}
        </a-descriptions-item>
        <a-descriptions-item label="seo-backend URL">
          {{ status.seo_backend?.url }}
        </a-descriptions-item>
        <a-descriptions-item label="seo-backend 状态">
          <a-tag :color="nodeColor">{{ status.seo_backend?.status }}</a-tag>
          <span v-if="status.seo_backend?.detail" class="ml-2 text-gray-500 text-xs">
            {{ status.seo_backend.detail }}
          </span>
        </a-descriptions-item>
        <a-descriptions-item label="代理路径">{{ status.seo_backend?.proxy_path }}</a-descriptions-item>
      </a-descriptions>

      <a-card v-if="status?.acquisition_panel" class="mt-4" size="small">
        <template #title>
          <div class="flex items-center justify-between">
            <span>{{ status.acquisition_panel.name }}</span>
            <a-tag :color="acquisitionStatusColor">
              {{ status.acquisition_panel.status_label }}
              （{{ status.acquisition_panel.configured }}/{{ status.acquisition_panel.total }}）
            </a-tag>
          </div>
        </template>
        <a-alert type="info" show-icon class="mb-3" :message="status.acquisition_panel.overall_hint" />
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div
            v-for="m in status.acquisition_panel.modules"
            :key="m.id"
            class="p-3 rounded-lg border bg-white hover:shadow-sm transition-shadow"
            :class="m.status === 'configured' ? 'border-green-200 bg-green-50/30' : 'border-amber-200 bg-amber-50/30'"
          >
            <div class="flex items-center justify-between gap-2 mb-2">
              <span class="font-medium text-sm text-slate-800">{{ m.name }}</span>
              <a-tag
                size="small"
                :color="m.status === 'configured' ? 'success' : 'warning'"
              >
                {{ m.status === 'configured' ? '已配置' : '待配置' }}
              </a-tag>
            </div>
            <p class="text-xs text-slate-500 mb-2">{{ m.hint }}</p>
            <div class="text-xs text-slate-400 mb-2">
              <span class="font-mono bg-slate-100 px-1.5 py-0.5 rounded">{{ m.env_key }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-slate-400">{{ m.category }}</span>
              <a
                :href="m.doc_link"
                target="_blank"
                class="text-xs text-teal-600 hover:text-teal-700"
              >
                获取 Key →
              </a>
            </div>
          </div>
        </div>
        <ul v-if="status.acquisition_panel.usage_tips?.length" class="list-disc pl-5 text-xs text-slate-500 mt-4 mb-0 space-y-1">
          <li v-for="(tip, i) in status.acquisition_panel.usage_tips" :key="i">{{ tip }}</li>
        </ul>
      </a-card>

      <a-card v-if="crawlPanel" title="数据采集旁路" class="mt-4" size="small">
        <a-alert type="info" show-icon class="mb-3" :message="crawlPanel.overall_hint" />
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div
            v-for="m in crawlPanel.modules || []"
            :key="m.id"
            class="p-3 rounded-lg border border-gray-100 bg-gray-50"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="font-medium text-sm">{{ m.name }}</span>
              <a-tag size="small">{{ m.status }}</a-tag>
            </div>
            <p class="text-xs text-gray-500 mt-2">{{ m.hint }}</p>
          </div>
        </div>
        <ul v-if="crawlPanel.usage_tips?.length" class="list-disc pl-5 text-xs text-gray-500 mt-3 mb-0">
          <li v-for="(tip, i) in crawlPanel.usage_tips" :key="i">{{ tip }}</li>
        </ul>
      </a-card>

      <a-card v-if="status?.guidance?.length" title="集成指引" class="mt-4" size="small">
        <ul class="list-disc pl-5 text-sm text-gray-600">
          <li v-for="(g, i) in status.guidance" :key="i">{{ g }}</li>
        </ul>
      </a-card>
    </template>
  </YdPage>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import SkeletonCard from '@/components/common/SkeletonCard.vue'
import { apiGet } from '@/utils/api'

const loading = ref(false)
const status = ref<any>(null)
const crawlPanel = ref<any>(null)

const nodeColor = computed(() => {
  const s = status.value?.seo_backend?.status
  if (s === 'connected') return 'green'
  if (s === 'degraded') return 'orange'
  if (s === 'unreachable' || s === 'failed') return 'red'
  return 'default'
})

const acquisitionStatusColor = computed(() => {
  const panel = status.value?.acquisition_panel
  if (!panel) return 'default'
  if (panel.configured === panel.total) return 'success'
  if (panel.configured > 0) return 'warning'
  return 'error'
})

async function load() {
  loading.value = true
  try {
    const [res, panelRes] = await Promise.all([
      apiGet('/integrations/status'),
      apiGet('/foreign-trade/integrations/ecommerce-crawlers/panel').catch(() => null),
    ])
    status.value = res?.data ?? res
    const panelData = panelRes?.data ?? panelRes
    crawlPanel.value = panelData?.data ?? panelData ?? null
  } catch (e: any) {
    message.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
