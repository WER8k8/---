/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <TrafficBoardPanel
      api-path="/super-admin/traffic-board"
      title="全平台流量看板"
      subtitle="各租户与各代理层级流量汇总，掌握全站获客链路"
    />
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import TrafficBoardPanel from '@/components/traffic/TrafficBoardPanel.vue';

onMounted(async () => {
  try { await apiGet('/analytics/traffic-board') } catch { /* 空状态 */ }
});
</script>
