<template>
  <YdPage :surface="surface" :title="pageTitle" :subtitle="pageSubtitle">
    <template v-if="$slots.actions" #actions>
      <slot name="actions" />
    </template>
    <div class="coachpro-tertiary" :class="variantClass">
      <section
        v-if="showTopbar"
        class="coachpro-topbar uj-glass-panel"
      >
        <div class="coachpro-topbar__main">
          <p v-if="kicker" class="coachpro-kicker">{{ kicker }}</p>
          <h1 v-if="title" class="coachpro-title">{{ title }}</h1>
          <p v-if="subtitle" class="coachpro-desc">{{ subtitle }}</p>
        </div>
        <div v-if="$slots.topActions" class="coachpro-topbar__actions">
          <slot name="topActions" />
        </div>
      </section>
      <slot />
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import YdPage from './YdPage.vue';

const props = withDefaults(
  defineProps<{
    /** 不传 title 时仍可用 slot 自定义顶栏 */
    title?: string;
    subtitle?: string;
    kicker?: string;
    /** 与 YdPage 重复时优先用 shell 顶栏，隐藏 YdPageHeader */
    pageTitle?: string;
    pageSubtitle?: string;
    surface?: 'default' | 'elevated' | 'brand-hero';
    variant?: 'platform' | 'agent' | 'partner' | 'client';
    hideTopbar?: boolean;
  }>(),
  {
    surface: 'elevated',
    variant: 'platform',
    hideTopbar: false,
  },
);

const showTopbar = computed(
  () => !props.hideTopbar && !!(props.title || props.kicker || props.subtitle),
);

const variantClass = computed(() => `coachpro-tertiary--${props.variant}`);
</script>

<style scoped lang="scss">
.coachpro-topbar__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 8px;
}
</style>
