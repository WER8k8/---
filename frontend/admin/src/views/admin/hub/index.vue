<template>
  <div class="hub-admin p-4">
    <h2 class="text-lg font-semibold mb-4">总站枢纽 / GSC</h2>
    <template v-if="loading">
      <SkeletonCard variant="card" />
    </template>
    <template v-else>
      <a-card size="small" class="mb-4">
        <p class="text-sm text-gray-600 mb-2">枢纽收录页数量：<strong>{{ checklist.url_count ?? 0 }}</strong></p>
        <p class="text-xs break-all text-gray-500">Sitemap：{{ checklist.sitemap_url }}</p>
        <a-button type="link" size="small" class="px-0 mt-2" @click="copySitemap">复制 Sitemap URL</a-button>
      </a-card>
      <a-card title="GSC 检查步骤" size="small">
        <ol class="list-decimal pl-5 text-sm text-gray-700 space-y-1">
          <li v-for="(s, i) in checklist.steps || []" :key="i">{{ s }}</li>
        </ol>
        <a-tag class="mt-3" :color="checklist.gsc_api_enabled ? 'green' : 'default'">
          GSC API {{ checklist.gsc_api_enabled ? '已配置' : '未配置（仅清单）' }}
        </a-tag>
      </a-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { apiGet } from '@/utils/api'
import SkeletonCard from '@/components/common/SkeletonCard.vue'

const loading = ref(false)
const checklist = ref<Record<string, unknown>>({})

async function load() {
  loading.value = true
  try {
    checklist.value = (await apiGet('/hub/search-console/checklist')) || {}
  } catch (e: unknown) {
    message.error((e as Error)?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function copySitemap() {
  const url = String(checklist.value.sitemap_url || '')
  if (!url) return
  navigator.clipboard.writeText(url).then(() => message.success('已复制'))
}

onMounted(load)
</script>
