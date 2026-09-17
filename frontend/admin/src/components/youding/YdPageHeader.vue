/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="yd-page-header">
    <div class="yd-page-header__main">
      <h1 class="yd-page-header__title">{{ title }}</h1>
      <p v-if="subtitle" class="yd-page-header__subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="yd-page-header__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  subtitle?: string;
}>();
</script>

<style scoped>
.yd-page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}
.yd-page-header__title {
  margin: 0;
  font-family: var(--uj-font-display);
  font-size: var(--uj-font-size-h1, 24px);
  font-weight: 700;
  color: var(--uj-text-secondary, #0f172a);
  letter-spacing: -0.02em;
}
.yd-page-header__subtitle {
  margin: 4px 0 0;
  font-size: var(--uj-text-body, 15px);
  color: var(--uj-text-muted, #64748b);
}
.yd-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.yd-page-header__actions :deep(.ant-btn-default:not(:disabled)) {
  background: rgb(255 255 255 / 0.96);
  border-color: #cbd5e1;
  color: #334155;
}
</style>
