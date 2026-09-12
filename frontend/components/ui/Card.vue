<script setup lang="ts">
interface Props {
  variant?: 'default' | 'outline';
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
});
</script>

<template>
  <div
    :class="[
      'rounded-lg border bg-card text-card-foreground shadow-sm',
      variant === 'default' ? 'border-border' : 'border-input',
    ]"
  >
    <slot />
  </div>
</template>
