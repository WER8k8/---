/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="dev-layout">
    <a-tabs :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="API网关" />
      <a-tab-pane key="sdk" tab="SDK管理" />
      <a-tab-pane key="low-code" tab="低代码平台" />
      <a-tab-pane key="plugins" tab="插件市场" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/developer', [
  'dashboard',
  'sdk',
  'low-code',
  'plugins',
])
</script>

<style scoped>
.dev-layout {
  padding: 0 4px;
}
</style>
