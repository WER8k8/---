/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <header class="yd-workspace-header">
    <div class="yd-workspace-header__brand">
      <div class="yd-workspace-header__logo">{{ logoText }}</div>
      <span class="yd-workspace-header__name">{{ tenantName }}</span>
    </div>
    <div class="yd-workspace-header__actions">
      <a-tag :color="planColor">{{ planLabel }}</a-tag>
      <YdUsageMeter class="yd-workspace-header__meter" :used="usageUsed" :max="usageMax" />
      <slot name="extra" />
    </div>
  </header>
</template>

<script setup lang="ts">
import YdUsageMeter from './YdUsageMeter.vue';

withDefaults(
  defineProps<{
    tenantName?: string;
    logoText?: string;
    planLabel?: string;
    planColor?: string;
    usageUsed?: number;
    usageMax?: number;
  }>(),
  {
    tenantName: '工作台',
    logoText: '优',
    planLabel: '体验版',
    planColor: 'default',
    usageUsed: 0,
    usageMax: 100,
  },
);
</script>

<style scoped lang="scss">
.yd-workspace-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 56px;
  padding: 0 var(--uj-space-page);
  background: var(--uj-bg-card);
  border-bottom: 1px solid var(--uj-border);
  &__brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  &__logo {
    width: 40px;
    height: 40px;
    border-radius: var(--uj-radius-sm);
    background: linear-gradient(135deg, var(--uj-brand), var(--uj-brand-deep));
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    box-shadow: 0 4px 12px rgb(37 99 235 / 0.3);
  }
  &__name {
    font-size: 16px;
    font-weight: 600;
    letter-spacing: -0.01em;
  }
  &__actions {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  &__meter {
    width: 120px;
  }
}
</style>
