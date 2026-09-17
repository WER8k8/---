/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="sales-layout">
    <a-tabs :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="销售工作台" />
      <a-tab-pane key="customer-finder" tab="客户开发" />
      <a-tab-pane key="auto-negotiator" tab="自动谈单" />
      <a-tab-pane key="email-automation" tab="开发信管理" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/sales', [
  'dashboard',
  'customer-finder',
  'auto-negotiator',
  'email-automation',
])
</script>

<style scoped>
.sales-layout {
  padding: 0 4px;
}
</style>
