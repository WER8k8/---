/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<script setup lang="ts">
interface Props {
  htmlFor?: string;
}

defineProps<Props>();
</script>

<template>
  <label
    v-if="$slots.default"
    :for="htmlFor"
    class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
  >
    <slot />
  </label>
</template>
