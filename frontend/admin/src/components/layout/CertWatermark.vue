/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <a-watermark
    v-if="enabled"
    :content="watermarkLines"
    :gap="[200, 160]"
    :offset="[48, 48]"
    :rotate="-22"
    :z-index="0"
    :inherit="false"
    :font="{ color: 'rgba(148, 163, 184, 0.045)', fontSize: 13 }"
    class="cert-watermark-wrap"
  >
    <slot />
  </a-watermark>
  <slot v-else />
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { isCertInspectionMode } from '@/constants/stubVisibility';
import { useAuthStore } from '@/stores/auth';

const auth = useAuthStore();
const enabled = computed(() => isCertInspectionMode());

const watermarkLines = computed(() => {
  const user = auth.username || 'Demo';
  return ['优丁出海 · 送检演示', user];
});
</script>

<style scoped>
.cert-watermark-wrap {
  min-height: 100vh;
}

/* 正文叠在水印之上，且不参与 backdrop 采样 */
.cert-watermark-wrap :deep(.ant-watermark) {
  z-index: 0;
  pointer-events: none;
}

.cert-watermark-wrap > :not(.ant-watermark) {
  position: relative;
  z-index: 1;
}
</style>
