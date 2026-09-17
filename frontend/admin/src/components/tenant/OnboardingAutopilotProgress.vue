/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="autopilot-progress">
    <div v-for="step in displaySteps" :key="step.id" class="autopilot-progress__row">
      <span class="autopilot-progress__icon">{{ stepIcon(step) }}</span>
      <div class="autopilot-progress__body">
        <p class="autopilot-progress__label">{{ step.label || step.id }}</p>
        <p v-if="step.detail || stepDetail(step)" class="autopilot-progress__detail">
          {{ step.detail || stepDetail(step) }}
        </p>
      </div>
      <a-tag :color="stepColor(step)">{{ stepStatus(step) }}</a-tag>
    </div>
    <a-progress
      v-if="running"
      :percent="percent"
      status="active"
      :show-info="false"
      class="mt-4"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { AutopilotStep } from '@/utils/onboardingAutopilot';

const props = defineProps<{
  steps: AutopilotStep[];
  running?: boolean;
  activeId?: string;
}>();

const displaySteps = computed(() =>
  props.steps.length
    ? props.steps
    : [
        { id: 'hermes', label: 'Hermes 智能建站' },
        { id: 'wangcai', label: '旺财 · 蓝海雷达' },
        { id: 'publish', label: '首篇引流稿' },
      ],
);

const percent = computed(() => {
  const done = props.steps.filter((s) => s.ok || s.skipped).length;
  const total = Math.max(displaySteps.value.length, 1);
  if (props.running && done >= total) return 95;
  return Math.round((done / total) * 100);
});

function stepIcon(step: AutopilotStep) {
  if (step.ok || step.skipped) return '✓';
  if (step.error) return '!';
  if (props.running && props.activeId === step.id) return '…';
  return '○';
}

function stepColor(step: AutopilotStep) {
  if (step.ok || step.skipped) return 'success';
  if (step.error) return 'error';
  if (props.running && props.activeId === step.id) return 'processing';
  return 'default';
}

function stepStatus(step: AutopilotStep) {
  if (step.skipped) return '已有';
  if (step.ok) return '完成';
  if (step.error) return '待补';
  if (props.running && props.activeId === step.id) return '进行中';
  return '等待';
}

function stepDetail(step: AutopilotStep): string {
  if (step.id === 'wangcai' && step.top_market?.country_label) {
    return `首选 ${step.top_market.country_label}`;
  }
  if (step.home_title) return step.home_title;
  if (step.preview) return step.preview.slice(0, 80);
  return '';
}
</script>

<style scoped lang="scss">
.autopilot-progress {
  &__row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #e2e8f0;
    &:last-child {
      border-bottom: none;
    }
  }
  &__icon {
    width: 24px;
    text-align: center;
    font-weight: 700;
    color: #0f766e;
  }
  &__body {
    flex: 1;
    min-width: 0;
  }
  &__label {
    margin: 0;
    font-weight: 600;
    font-size: 14px;
    color: #0f172a;
  }
  &__detail {
    margin: 4px 0 0;
    font-size: 12px;
    color: #64748b;
    line-height: 1.45;
  }
}
</style>
