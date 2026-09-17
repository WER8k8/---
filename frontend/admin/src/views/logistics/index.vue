/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="lg-layout">
    <a-tabs :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="物流看板" />
      <a-tab-pane key="lbs-routing" tab="LBS测距" />
      <a-tab-pane key="freight-calc" tab="运费精算" />
      <a-tab-pane key="quotation" tab="报价单生成" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/logistics', [
  'dashboard',
  'lbs-routing',
  'freight-calc',
  'quotation',
])
</script>

<style scoped>
.lg-layout {
  padding: 0 4px;
}
</style>
