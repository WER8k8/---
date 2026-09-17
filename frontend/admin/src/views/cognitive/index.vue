/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="cognitive-layout">
    <a-tabs :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="知识图谱" />
      <a-tab-pane key="qa-engine" tab="智能问答" />
      <a-tab-pane key="expert-system" tab="专家系统" />
      <a-tab-pane key="semantic-index" tab="语义索引" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/cognitive', [
  'dashboard',
  'qa-engine',
  'expert-system',
  'semantic-index',
])
</script>

<style scoped>
.cognitive-layout {
  padding: 0 4px;
}
</style>
