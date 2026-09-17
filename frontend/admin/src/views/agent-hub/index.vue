/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="agent-hub-layout">
    <a-tabs :active-key="tab" @change="onTab">
      <a-tab-pane key="dashboard" tab="协同看板" />
      <a-tab-pane key="mcp-bridge" tab="MCP桥接" />
      <a-tab-pane key="task-orchestrator" tab="任务调度" />
      <a-tab-pane key="execution-review" tab="执行复盘" />
    </a-tabs>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useModuleTabSync } from '@/composables/useModuleTabSync'

const { tab, onTab } = useModuleTabSync('/agent-hub', [
  'dashboard',
  'mcp-bridge',
  'task-orchestrator',
  'execution-review',
])
</script>

<style scoped>
.agent-hub-layout {
  padding: 0 4px;
}
</style>
