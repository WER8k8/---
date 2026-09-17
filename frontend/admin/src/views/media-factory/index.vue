/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="mf-layout">
    <a-tabs :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="视频生成" />
      <a-tab-pane key="tts" tab="TTS配音" />
      <a-tab-pane key="charts" tab="动态图表" />
      <a-tab-pane key="render-queue" tab="渲染队列" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/media-factory', [
  'dashboard',
  'tts',
  'charts',
  'render-queue',
])
</script>

<style scoped>
.mf-layout {
  padding: 0 4px;
}
</style>
