<template>
  <div class="gl-layout">
    <a-tabs :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="多语言管理" />
      <a-tab-pane key="glossary" tab="术语库" />
      <a-tab-pane key="translator" tab="翻译引擎" />
      <a-tab-pane key="culture-adapt" tab="文化适配" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/globalization', [
  'dashboard',
  'glossary',
  'translator',
  'culture-adapt',
])
</script>

<style scoped>
.gl-layout {
  padding: 0 4px;
}
</style>
