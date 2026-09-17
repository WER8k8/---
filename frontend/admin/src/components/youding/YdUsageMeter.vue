/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="yd-usage-meter">
    <div class="yd-usage-meter__label">
      <span>{{ label }}</span>
      <span class="yd-usage-meter__pct" :class="tone">{{ pctDisplay }}%</span>
    </div>
    <div class="yd-usage-meter__track">
      <div class="yd-usage-meter__bar" :class="tone" :style="{ width: `${clampedPct}%` }" />
    </div>
    <p v-if="hint" class="yd-usage-meter__hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    label?: string;
    used: number;
    max: number;
    hint?: string;
  }>(),
  {
    label: '本月额度',
  },
);

const clampedPct = computed(() => {
  if (!props.max) return 0;
  return Math.min(100, Math.round((props.used / props.max) * 100));
});

const pctDisplay = computed(() => clampedPct.value);

const tone = computed(() => {
  if (clampedPct.value >= 100) return 'danger';
  if (clampedPct.value >= 80) return 'warning';
  return 'normal';
});
</script>

<style scoped lang="scss">
.yd-usage-meter {
  &__label {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--uj-text-muted);
    margin-bottom: 6px;
  }
  &__track {
    height: 6px;
    border-radius: 999px;
    background: #e5e7eb;
    overflow: hidden;
  }
  &__bar {
    height: 100%;
    border-radius: 999px;
    transition: width 0.2s ease;
    &.normal {
      background: var(--uj-brand);
    }
    &.warning {
      background: var(--uj-warning);
    }
    &.danger {
      background: var(--uj-danger);
    }
  }
  &__pct.warning {
    color: var(--uj-warning);
  }
  &__pct.danger {
    color: var(--uj-danger);
  }
  &__hint {
    margin: 6px 0 0;
    font-size: 12px;
    color: var(--uj-text-muted);
  }
}
</style>
