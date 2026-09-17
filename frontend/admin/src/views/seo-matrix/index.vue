/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="seo-matrix-layout">
    <a-tabs
      :active-key="tab"
      class="seo-matrix-tabs"
      :class="{ 'seo-matrix-tabs--navigating': navigating }"
      @change="onTab"
    >
      <a-tab-pane key="dashboard" tab="数据看板" />
      <a-tab-pane key="settings" tab="系统设置" />
      <a-tab-pane key="regions" tab="地域词库" />
      <a-tab-pane key="keywords" tab="关键词管理" />
      <a-tab-pane key="content" tab="文案生成" />
      <a-tab-pane key="publish" tab="多平台分发" />
      <a-tab-pane key="inclusion" tab="收录监控" />
      <a-tab-pane key="growth-tools" tab="增长工具" />
    </a-tabs>

    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab, navigating } = useModuleTabSync('/seo-matrix', [
  'dashboard',
  'settings',
  'regions',
  'keywords',
  'content',
  'publish',
  'inclusion',
  'growth-tools',
])
</script>

<style scoped>
.seo-matrix-layout {
  padding: 0 4px;
}
.seo-matrix-tabs--navigating :deep(.ant-tabs-tab-active) {
  opacity: 0.85;
}
</style>
