/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="yd-today-queue uj-kpi-card">
    <div class="yd-today-queue__head">
      <h3 class="yd-today-queue__title">{{ title }}</h3>
      <span v-if="items.length" class="yd-today-queue__count">{{ items.length }}</span>
    </div>
    <ul v-if="items.length" class="yd-today-queue__list">
      <li
        v-for="item in displayItems"
        :key="item.id"
        class="yd-today-queue__row"
        :class="{ 'yd-today-queue__row--link': Boolean(item.route) }"
        :role="item.route ? 'button' : undefined"
        :tabindex="item.route ? 0 : undefined"
        @click="onRowClick(item)"
        @keydown.enter.prevent="onRowClick(item)"
      >
        <span class="yd-today-queue__label">{{ item.label }}</span>
        <span class="yd-today-queue__meta">
          <a-tag :color="item.priority === 'high' ? 'red' : 'default'" size="small">
            {{ item.priority === 'high' ? '优先' : '待办' }}
          </a-tag>
          <span v-if="item.route" class="yd-today-queue__chevron" aria-hidden="true">→</span>
        </span>
      </li>
    </ul>
    <a-empty v-else :description="emptyText">
      <a-button v-if="emptyActionRoute" type="link" size="small" @click="emit('navigate', emptyActionRoute)">
        {{ emptyActionLabel }}
      </a-button>
    </a-empty>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import type { QueueItem } from './types';

export type { QueueItem };

const props = withDefaults(
  defineProps<{
    title?: string;
    items: QueueItem[];
    max?: number;
    emptyText?: string;
    emptyActionRoute?: string;
    emptyActionLabel?: string;
  }>(),
  {
    title: '今日待办',
    max: 5,
    emptyText: '今日暂无待办',
    emptyActionRoute: '',
    emptyActionLabel: '打开今日三步 →',
  },
);

const emit = defineEmits<{
  navigate: [path: string];
}>();

const displayItems = computed(() => props.items.slice(0, props.max));

function onRowClick(item: QueueItem) {
  if (!item.route) return;
  emit('navigate', item.route);
}
</script>

<style scoped lang="scss">
.yd-today-queue {
  padding: var(--uj-space-card);
  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }
  &__title {
    font-size: var(--uj-text-title);
    font-weight: 600;
    margin: 0;
  }
  &__count {
    font-size: 12px;
    color: var(--uj-text-muted);
  }
  &__list {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  &__row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid var(--uj-border);
    &:last-child {
      border-bottom: none;
    }
  }
  &__row--link {
    cursor: pointer;
    border-radius: 8px;
    margin: 0 -6px;
    padding: 8px 6px;
    transition: background 0.15s ease;
    &:hover {
      background: #f8fafc;
    }
    &:focus-visible {
      outline: 2px solid var(--uj-brand, #4a9b8c);
      outline-offset: 2px;
    }
  }
  &__label {
    font-size: var(--uj-text-body);
    color: #111827;
    flex: 1;
    min-width: 0;
  }
  &__meta {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
  }
  &__chevron {
    font-size: 12px;
    color: var(--uj-brand, #4a9b8c);
    font-weight: 600;
  }
}
</style>
