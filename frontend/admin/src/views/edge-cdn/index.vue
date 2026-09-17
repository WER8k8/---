/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="ecdn-layout">
    <a-tabs :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="CDN管理" />
      <a-tab-pane key="nodes" tab="边缘节点" />
      <a-tab-pane key="preheat" tab="内容预热" />
      <a-tab-pane key="protocol" tab="协议优化" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/edge-cdn', [
  'dashboard',
  'nodes',
  'preheat',
  'protocol',
])
</script>

<style scoped>
.ecdn-layout {
  padding: 0 4px;
}
</style>
