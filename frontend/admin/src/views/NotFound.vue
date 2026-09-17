/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="nf-wrap" aria-label="页面未找到">
    <a-result
      status="404"
      title="404"
      sub-title="抱歉，您访问的页面不存在或已调整路径。"
    >
      <template #extra>
        <a-space>
          <a-button
            type="primary"
            @click="router.push('/dashboard')"
          >
            数据概览
          </a-button>
          <a-button @click="router.push('/admin')">
            超级管理员
          </a-button>
        </a-space>
      </template>
    </a-result>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const router = useRouter();
</script>

<style scoped lang="scss">
.nf-wrap {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}
</style>
