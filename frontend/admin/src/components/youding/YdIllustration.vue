/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="yd-illustration" :class="`yd-illustration--${size}`">
    <YdReliefIcon :icon="resolveAntIcon(icon)" size="lg" />
  </div>
</template>

<script setup lang="ts">
import { resolveAntIcon } from '@/constants/antIconMap';
import YdReliefIcon from './YdReliefIcon.vue';

withDefaults(
  defineProps<{
    /** Ant Design 图标名，如 CreditCardOutlined */
    icon: string;
    size?: 'md' | 'lg';
  }>(),
  { size: 'lg' },
);
</script>

<style scoped>
.yd-illustration {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}
.yd-illustration--lg :deep(.yd-relief-icon) {
  width: 56px;
  height: 56px;
  font-size: 28px;
  border-radius: 16px;
}
.yd-illustration--md :deep(.yd-relief-icon) {
  width: 44px;
  height: 44px;
  font-size: 22px;
}
</style>
