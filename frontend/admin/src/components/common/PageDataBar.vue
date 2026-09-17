/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div v-if="visible" class="page-data-bar mb-4">
    <a-alert
      v-if="mode === 'loading'"
      type="info"
      show-icon
      message="正在加载数据…"
    />
    <a-alert
      v-else-if="mode === 'demo'"
      type="warning"
      show-icon
      :message="demoMessage"
      :description="demoDescription"
    />
    <a-alert
      v-else-if="mode === 'empty'"
      type="info"
      show-icon
      :message="emptyMessage"
      :description="emptyDescription"
    >
      <template v-if="showRetry" #action>
        <a-button size="small" @click="$emit('retry')">重试</a-button>
      </template>
    </a-alert>
    <a-alert
      v-else-if="mode === 'error'"
      type="error"
      show-icon
      :message="errorMessage || '加载失败'"
      :description="errorDetail"
    >
      <template v-if="showRetry" #action>
        <a-button size="small" type="primary" @click="$emit('retry')">重试</a-button>
      </template>
    </a-alert>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PageDataMode } from '@/composables/usePageData'

const props = withDefaults(
  defineProps<{
    mode: PageDataMode | 'loading'
    errorMessage?: string
    errorDetail?: string
    demoMessage?: string
    demoDescription?: string
    emptyMessage?: string
    emptyDescription?: string
    showRetry?: boolean
  }>(),
  {
    demoMessage: '当前为演示数据',
    demoDescription: '后端接口未返回数据或暂不可用，所示数字仅供界面预览，不可作为经营依据。',
    emptyMessage: '暂无数据',
    emptyDescription: '请确认后端服务已启动，或稍后在页面内创建第一条记录。',
    showRetry: true,
  },
)

defineEmits<{ retry: [] }>()

const visible = computed(() => props.mode !== 'live')
</script>

<style scoped>
.page-data-bar :deep(.ant-alert) {
  border-radius: 10px;
}
</style>
