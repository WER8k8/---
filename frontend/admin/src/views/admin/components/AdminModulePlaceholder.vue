/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="admin-placeholder-wrap">
    <a-card
      :bordered="false"
      class="admin-placeholder-card"
    >
      <template #title>
        <span class="admin-placeholder-title">{{ title }}</span>
      </template>
      <p class="admin-placeholder-desc">
        {{ description }}
      </p>
      <a-divider
        v-if="links.length"
        orientation="left"
      >
        已上线能力
      </a-divider>
      <a-space
        v-if="links.length"
        direction="vertical"
        size="small"
        class="admin-placeholder-links"
      >
        <router-link
          v-for="l in links"
          :key="l.path"
          :to="l.path"
        >
          <a-button type="link">
            {{ l.label }}
          </a-button>
        </router-link>
      </a-space>
      <div class="admin-placeholder-actions">
        <a-button
          type="primary"
          @click="go"
        >
          {{ backLabel }}
        </a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

export interface AdminPlaceholderLink {
  label: string;
  path: string;
}

const props = withDefaults(
  defineProps<{
    title: string;
    description: string;
    links?: AdminPlaceholderLink[];
    backPath?: string;
    backLabel?: string;
  }>(),
  {
    links: () => [],
    backPath: '/admin',
    backLabel: '返回超级管理员首页',
  }
);

const router = useRouter();

function go() {
  router.push(props.backPath);
}
</script>

<style scoped lang="scss">
.admin-placeholder-wrap {
  padding: 24px;
  max-width: 720px;
  margin: 0 auto;
}

.admin-placeholder-card {
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

.admin-placeholder-title {
  font-weight: 600;
  font-size: 18px;
}

.admin-placeholder-desc {
  color: #64748b;
  line-height: 1.7;
  margin: 0;
}

.admin-placeholder-links {
  width: 100%;
}

.admin-placeholder-actions {
  margin-top: 20px;
}
</style>
