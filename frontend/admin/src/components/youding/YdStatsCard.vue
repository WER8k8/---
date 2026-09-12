<template>
  <div
    class="yd-stats-card uj-kpi-card uj-glass-panel"
    :class="{ compact, clickable: !!to, [`tone-${tone}`]: tone }"
    @click="handleClick"
  >
    <div class="yd-stats-card__label">{{ label }}</div>
    <div class="yd-stats-card__value" :style="valueStyle">
      <slot>{{ shownValue }}</slot>
    </div>
    <div v-if="hint" class="yd-stats-card__hint">{{ hint }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useCountUp, parseMetricValue } from '@/composables/useCountUp';

const props = withDefaults(
  defineProps<{
    label: string;
    value?: string | number;
    hint?: string;
    compact?: boolean;
    tone?: 'blue' | 'green' | 'amber' | 'purple' | 'default';
    /** 载入时数字滚动 */
    animate?: boolean;
    /** 点击后跳转的路由路径 */
    to?: string;
  }>(),
  { compact: false, tone: 'default', animate: true },
);

const router = useRouter();

const handleClick = () => {
  if (props.to) {
    router.push(props.to);
  }
};

const parsed = computed(() => parseMetricValue(props.value));

const countDisplay = useCountUp(
  () => (props.animate ? parsed.value.num : null),
  {
    duration: 900,
    decimals: () => parsed.value.decimals,
    enabled: () => props.animate,
  },
);

const shownValue = computed(() => {
  if (props.value === 0) return '0';
  if (props.value === undefined || props.value === null || props.value === '') return '--';
  if (props.animate && parsed.value.num != null) {
    const formatted =
      parsed.value.decimals > 0
        ? countDisplay.value
        : Number(countDisplay.value).toLocaleString('zh-CN');
    return `${formatted}${parsed.value.suffix}`;
  }
  return props.value;
});

const toneColors: Record<string, string> = {
  blue: '#4a9b8c',
  green: 'var(--uj-brand-deep, #3d8f7a)',
  amber: '#b8954a',
  purple: 'var(--uj-brand-hover, #5eb8a8)',
  default: 'var(--uj-text-secondary, #0f2924)',
};

const valueStyle = computed(() =>
  props.tone && props.tone !== 'default' ? { color: toneColors[props.tone] } : undefined,
);
</script>

<style scoped>
.yd-stats-card {
  padding: 16px 18px;
  border-radius: 18px;
}
.yd-stats-card.compact {
  padding: 12px 14px;
}
.yd-stats-card__label {
  font-size: var(--uj-font-size-sm, 13px);
  font-weight: 600;
  color: var(--uj-text-muted);
}
.yd-stats-card__value {
  margin-top: 8px;
  font-family: var(--uj-font-display);
  font-size: 28px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.15;
  color: var(--uj-text-secondary, #0f2924);
}
.yd-stats-card__hint {
  margin-top: 4px;
  font-size: var(--uj-font-size-xs, 12px);
  color: var(--uj-text-muted);
}
.yd-stats-card.clickable {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease;
}
.yd-stats-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(74, 155, 140, 0.18);
  background-color: var(--uj-bg-hover, rgba(74, 155, 140, 0.04));
}
.yd-stats-card.clickable:active {
  transform: translateY(0);
}
</style>
