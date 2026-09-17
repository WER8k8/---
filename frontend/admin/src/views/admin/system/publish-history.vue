/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="统一发布历史" subtitle="SEO 图文矩阵 + 视频矩阵" surface="elevated">
    <template #actions>
      <a-button :loading="loading" @click="load">刷新</a-button>
    </template>
    <a-table :loading="loading" :data-source="items" :columns="cols" row-key="id" size="small" :pagination="false" />
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { YdPage } from '@/components/youding'
import { apiGet } from '@/utils/api'

const loading = ref(false)
const items = ref<Record<string, unknown>[]>([])

const cols = [
  { title: '渠道', dataIndex: 'channel', key: 'channel', width: 110 },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: 'URL', dataIndex: 'url', key: 'url', ellipsis: true },
  { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 170 },
]

async function load() {
  loading.value = true
  try {
    const data = await apiGet<{ items: Record<string, unknown>[] }>('/hermes/ops/publish-history', {
      limit: 50,
    })
    items.value = data.items || []
  } catch (e: unknown) {
    message.error((e as Error)?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
