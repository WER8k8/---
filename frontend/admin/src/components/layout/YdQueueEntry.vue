/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <a-dropdown :trigger="['click']">
    <a-badge :count="totalBadge" :offset="[-2, 2]" :number-style="{ fontSize: '10px' }">
      <a-button size="small" :loading="badges.loading">
        <UnorderedListOutlined />
        <span class="hidden sm:inline ml-1">今日队列</span>
      </a-button>
    </a-badge>
    <template #overlay>
      <a-menu @click="onMenuClick">
        <a-menu-item key="inquiries">
          <div class="yd-queue-item">
            <span>询盘队列</span>
            <a-badge :count="badges.inquiries" :show-zero="false" />
          </div>
        </a-menu-item>
        <a-menu-item key="publish">
          <div class="yd-queue-item">
            <span>发布队列</span>
            <a-badge :count="badges.publish" :show-zero="false" />
          </div>
        </a-menu-item>
        <a-menu-item key="fulfillment">
          <div class="yd-queue-item">
            <span>履约队列</span>
            <a-badge :count="badges.fulfillment" :show-zero="false" />
          </div>
        </a-menu-item>
      </a-menu>
    </template>
  </a-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { UnorderedListOutlined } from '@ant-design/icons-vue';
import type { MenuProps } from 'ant-design-vue';

import { useQueueBadges } from '@/composables/useQueueBadges';
import { resolveShellMode } from '@/constants/proShellMenus';

const router = useRouter();
const { badges } = useQueueBadges();

const totalBadge = computed(
  () => badges.inquiries + badges.publish + badges.fulfillment,
);

function queuePaths() {
  const mode = resolveShellMode(router.currentRoute.value.path);
  if (mode === 'client') {
    return {
      inquiries: '/client/queues/inquiries',
      publish: '/client/queues/publish',
      fulfillment: '/client/queues/fulfillment',
    };
  }
  return {
    inquiries: '/inquiries',
    publish: '/client/queues/publish',
    fulfillment: '/client/queues/fulfillment',
  };
}

const onMenuClick: MenuProps['onClick'] = ({ key }) => {
  const paths = queuePaths();
  const path = paths[key as keyof typeof paths];
  if (path) void router.push(path);
};
</script>

<style scoped>
.yd-queue-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-width: 160px;
}
</style>
