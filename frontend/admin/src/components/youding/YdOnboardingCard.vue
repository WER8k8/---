<template>
  <div class="yd-onboarding-card uj-kpi-card">
    <h3 class="yd-onboarding-card__title">{{ title }}</h3>
    <a-steps :current="currentStep" size="small" direction="vertical">
      <a-step
        v-for="step in steps"
        :key="step.id"
        :title="step.title"
        :status="step.done ? 'finish' : step.id === activeId ? 'process' : 'wait'"
      />
    </a-steps>
    <a-button v-if="ctaRoute" type="link" class="yd-onboarding-card__cta" @click="goCta">
      {{ ctaLabel }}
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';

import type { OnboardingStep } from './types';

export type { OnboardingStep };

const props = withDefaults(
  defineProps<{
    title?: string;
    steps: OnboardingStep[];
    ctaLabel?: string;
  }>(),
  {
    title: '开户进度',
    ctaLabel: '继续下一步 →',
  },
);

const router = useRouter();

const currentStep = computed(() => {
  const idx = props.steps.findIndex((s) => !s.done);
  return idx === -1 ? props.steps.length - 1 : idx;
});

const activeId = computed(() => props.steps[currentStep.value]?.id);

const ctaRoute = computed(() => props.steps.find((s) => !s.done)?.route);

function goCta() {
  if (ctaRoute.value) router.push(ctaRoute.value);
}
</script>

<style scoped lang="scss">
@use '@/styles/design-tokens-v2.scss';

.yd-onboarding-card {
  padding: var(--uj-space-card);
  &__title {
    font-size: var(--uj-text-title);
    font-weight: 600;
    margin-bottom: 12px;
  }
  &__cta {
    padding-left: 0;
    margin-top: 8px;
  }
}
</style>
