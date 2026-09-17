/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdReliefIcon :icon="resolveAntIcon(name)" :size="size" :active="active" />
</template>

<script setup lang="ts">
import { resolveAntIcon } from '@/constants/antIconMap';
import YdReliefIcon from './YdReliefIcon.vue';

withDefaults(
  defineProps<{
    name: string;
    size?: 'sm' | 'md' | 'lg';
    active?: boolean;
  }>(),
  { size: 'md', active: false },
);
</script>
