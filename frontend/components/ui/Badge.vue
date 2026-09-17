/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<script setup lang="ts">
interface Props {
  variant?: 'default' | 'secondary' | 'outline';
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
});

const variantClasses = {
  default: 'bg-primary/10 text-primary',
  secondary: 'bg-secondary text-secondary-foreground',
  outline: 'border border-input text-foreground',
};
</script>

<template>
  <span
    :class="[
      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
      variantClasses[variant],
    ]"
  >
    <slot />
  </span>
</template>
