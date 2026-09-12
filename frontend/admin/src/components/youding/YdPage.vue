<template>
  <div class="yd-page" :class="pageClass">
    <div v-if="$slots.hero" class="yd-page-hero">
      <slot name="hero" />
    </div>
    <YdPageHeader v-if="title" :title="title" :subtitle="subtitle">
      <template v-if="$slots.actions" #actions>
        <slot name="actions" />
      </template>
    </YdPageHeader>
    <div class="yd-page-body coachpro-page-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import YdPageHeader from './YdPageHeader.vue';

const props = withDefaults(
  defineProps<{
    title?: string;
    subtitle?: string;
    surface?: 'default' | 'elevated' | 'brand-hero';
  }>(),
  { surface: 'default' },
);

const pageClass = computed(() => ({
  'yd-page--surface-default': props.surface === 'default',
  'yd-page--surface-elevated': props.surface === 'elevated',
  'yd-page--surface-brand-hero': props.surface === 'brand-hero',
}));
</script>
