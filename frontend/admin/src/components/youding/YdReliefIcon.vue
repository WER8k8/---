/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <span
    class="yd-relief-icon"
    :class="[`yd-relief-icon--${size}`, { 'yd-relief-icon--active': active }]"
    aria-hidden="true"
  >
    <component :is="icon" :component="icon" />
  </span>
</template>

<script setup lang="ts">
import type { Component } from 'vue';

withDefaults(
  defineProps<{
    icon: Component;
    size?: 'sm' | 'md' | 'lg';
    active?: boolean;
  }>(),
  { size: 'md', active: false },
);
</script>

<style scoped lang="scss">
.yd-relief-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 10px;
  color: var(--uj-brand-deep, #2a6b60);
  background: linear-gradient(
    155deg,
    rgb(255 255 255 / 0.95) 0%,
    rgb(232 250 244 / 0.9) 38%,
    rgb(196 230 216 / 0.85) 100%
  );
  box-shadow:
    0 1px 0 rgb(255 255 255 / 0.95) inset,
    0 -1px 0 rgb(42 107 96 / 0.08) inset,
    0 4px 10px rgb(74 155 140 / 0.2),
    0 1px 2px rgb(45 107 96 / 0.1);
  transition:
    transform 300ms ease-out,
    box-shadow 300ms ease-out,
    color 300ms ease-out;
}

.yd-relief-icon--sm {
  width: 26px;
  height: 26px;
  font-size: 14px;
  border-radius: 8px;
}

.yd-relief-icon--md {
  width: 30px;
  height: 30px;
  font-size: 16px;
}

.yd-relief-icon--lg {
  width: 36px;
  height: 36px;
  font-size: 18px;
  border-radius: 12px;
}

.yd-relief-icon--active {
  color: #fff;
  background: linear-gradient(
    155deg,
    #7ecdb8 0%,
    var(--uj-brand, #4a9b8c) 45%,
    var(--uj-brand-deep, #2a6b60) 100%
  );
  box-shadow:
    0 1px 0 rgb(255 255 255 / 0.35) inset,
    0 4px 12px rgb(42 107 96 / 0.28);
}
</style>

<style lang="scss">
/* 深色：图标用 Slate 底 + 亮字，避免浅色浮雕吞图标 */
:root[data-uj-theme='dark'] .yd-relief-icon:not(.yd-relief-icon--active) {
  color: var(--uj-icon-tile-color, #eaf2f4);
  background: var(--uj-icon-tile-bg, linear-gradient(155deg, #4a5362 0%, #3f4854 100%));
  box-shadow: var(--uj-icon-tile-shadow, 0 1px 0 rgb(255 255 255 / 0.12) inset, 0 2px 8px rgb(0 0 0 / 0.16));
}

:root[data-uj-theme='dark'] .yd-relief-icon--active {
  color: #fff;
  background: linear-gradient(155deg, #6ec4b4 0%, var(--uj-brand, #5eb8a8) 50%, #3a8f82 100%);
  box-shadow:
    0 1px 0 rgb(255 255 255 / 0.2) inset,
    0 4px 12px rgb(0 0 0 / 0.28);
}
</style>
