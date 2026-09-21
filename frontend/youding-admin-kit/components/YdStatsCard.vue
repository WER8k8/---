<template>
  <div
    class="yd-stats-card"
    :class="{ compact }"
  >
    <div class="yd-stats-card__label">
      {{ label }}
    </div>
    <div class="yd-stats-card__value">
      <slot>{{ displayValue }}</slot>
    </div>
    <div
      v-if="hint"
      class="yd-stats-card__hint"
    >
      {{ hint }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    label: string
    value?: string | number
    hint?: string
    compact?: boolean
  }>(),
  { compact: false },
)

const displayValue = computed(() => {
  if (props.value === 0) return '0'
  if (props.value === undefined || props.value === null || props.value === '') return '--'
  return props.value
})
</script>

<style scoped>
.yd-stats-card {
  background: var(--uj-bg-card, #fff);
  border: 1px solid var(--uj-border, #e5e7eb);
  border-radius: var(--uj-radius-lg, 16px);
  padding: 16px 18px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}
.yd-stats-card.compact {
  padding: 12px 14px;
}
.yd-stats-card__label {
  font-size: 12px;
  color: var(--uj-text-muted, #6b7280);
}
.yd-stats-card__value {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}
.yd-stats-card__hint {
  margin-top: 4px;
  font-size: 11px;
  color: var(--uj-text-muted, #6b7280);
}
</style>
