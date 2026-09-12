<template>
  <div class="ai-learning-layout">
    <a-tabs :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="学习看板" />
      <a-tab-pane key="behavior" tab="行为分析" />
      <a-tab-pane key="conversion-funnel" tab="转化漏斗" />
      <a-tab-pane key="auto-ab-test" tab="A/B自动化" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/ai-learning', [
  'dashboard',
  'behavior',
  'conversion-funnel',
  'auto-ab-test',
])
</script>

<style scoped>
.ai-learning-layout {
  padding: 0 4px;
}
</style>
