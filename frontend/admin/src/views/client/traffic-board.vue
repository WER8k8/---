<template>
  <YdPage surface="elevated">
    <TrafficBoardPanel
      api-path="/analytics/traffic-board"
      title="流量看板"
      subtitle="您的官网每天多少人访问、点了哪里、哪条内容带来询盘和电话"
    />
  </YdPage>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { apiGet } from '@/utils/api';
import { YdPage } from '@/components/youding';
import TrafficBoardPanel from '@/components/traffic/TrafficBoardPanel.vue';

onMounted(async () => {
  try { await apiGet('/analytics/traffic-board'); } catch { /* 空状态 */ }
});
</script>
