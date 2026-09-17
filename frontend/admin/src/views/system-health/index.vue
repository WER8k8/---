/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="system-health-layout min-h-screen bg-gray-50">
    <div class="px-6 pt-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 m-0">系统健康压测</h1>
          <p class="text-sm text-gray-500 mt-1 mb-0">实时监控系统资源、执行压力测试与管理备份回滚</p>
        </div>
      </div>

      <a-tabs
        :active-key="activeTab"
        size="large"
        @change="handleTabChange"
        class="system-health-tabs"
      >
        <a-tab-pane key="dashboard" tab="健康看板" />
        <a-tab-pane key="resource-monitor" tab="资源监控" />
        <a-tab-pane key="stress-test" tab="压测管理" />
        <a-tab-pane key="backup" tab="备份回滚" />
      </a-tabs>
    </div>

    <div class="px-6 pb-6">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Tabs, TabPane, message } from 'ant-design-vue';
import { getAuthToken } from '@/utils/api';

const router = useRouter();
const route = useRoute();

const activeTab = computed(() => {
  const name = (route.name as string) || '';
  if (name.includes('dashboard')) return 'dashboard';
  if (name.includes('resource-monitor')) return 'resource-monitor';
  if (name.includes('stress-test')) return 'stress-test';
  if (name.includes('backup')) return 'backup';
  return 'dashboard';
});

const tabRouteMap: Record<string, string> = {
  dashboard: 'system-health-dashboard',
  'resource-monitor': 'system-health-resource-monitor',
  'stress-test': 'system-health-stress-test',
  backup: 'system-health-backup',
};

function handleTabChange(key: string | number) {
  router.push({ name: tabRouteMap[String(key)] });
}

onMounted(async () => {
  try {
    const tk = getAuthToken() || ''
    await fetch('/api/v1/system-health/', { headers: { Authorization: `Bearer ${tk}` } })
  } catch { /* API unavailable, use local data */ }
})
</script>

<style scoped>
.system-health-layout {
  background: #f0f2f5;
}

.system-health-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 0;
}

.system-health-tabs :deep(.ant-tabs-tab) {
  font-size: 15px;
  padding: 12px 24px;
}
</style>
