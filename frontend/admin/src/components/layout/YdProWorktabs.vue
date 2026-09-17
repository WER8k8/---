/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="yd-pro-worktabs" :class="[`yd-pro-worktabs--${shellMode}`, { 'yd-pro-worktabs--tabs-only': hideMeta }]">
    <div v-if="!hideMeta" class="yd-pro-worktabs__meta">
      <span class="yd-pro-worktabs__role">{{ roleLabel }}</span>
      <span class="yd-pro-worktabs__dot" aria-hidden="true" />
      <span class="yd-pro-worktabs__user">{{ username }}</span>
      <button
        v-if="ui.worktabEnabled && closableCount > 0"
        type="button"
        class="yd-pro-worktabs__clear"
        @click="closeOthers(activePath)"
      >
        关闭其他
      </button>
    </div>

    <div
      v-if="ui.worktabEnabled && tabs.length"
      ref="tabScroller"
      class="yd-pro-worktabs__strip"
      role="tablist"
      aria-label="已打开页面"
    >
      <button
        v-for="tab in tabs"
        :key="tab.path"
        type="button"
        role="tab"
        class="yd-pro-worktabs__tab"
        :class="{ active: tab.path === activePath }"
        :aria-selected="tab.path === activePath"
        @click="go(tab.path)"
      >
        <span class="yd-pro-worktabs__tab-label">{{ tab.title }}</span>
        <span
          v-if="!tab.affix"
          class="yd-pro-worktabs__tab-close"
          role="button"
          aria-label="关闭标签"
          @click.stop="close(tab.path)"
        >
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import { useWorkTabNavigation } from '@/composables/useWorkTabNavigation'
import type { ShellMode } from '@/constants/proShellMenus'
import { useUiPreferencesStore } from '@/stores/uiPreferences'

withDefaults(
  defineProps<{
    roleLabel?: string
    username?: string
    shellMode?: ShellMode
    hideMeta?: boolean
  }>(),
  {
    roleLabel: '',
    username: '',
    shellMode: 'platform',
    hideMeta: false,
  },
)

const ui = useUiPreferencesStore()
const { tabs, activePath, go, close, closeOthers } = useWorkTabNavigation()
const tabScroller = ref<HTMLElement>()

const closableCount = computed(() => tabs.value.filter((t) => !t.affix).length)

watch(
  activePath,
  () => {
    void nextTick(() => {
      const el = tabScroller.value?.querySelector('.yd-pro-worktabs__tab.active')
      el?.scrollIntoView({ inline: 'nearest', block: 'nearest', behavior: 'smooth' })
    })
  },
  { immediate: true },
)
</script>

<style scoped>
.yd-pro-worktabs {
  display: flex;
  flex-direction: column;
  background: var(--uj-glass-bg-strong, #fff);
  border-bottom: 1px solid var(--uj-border-soft, #e2e8f0);
}

.yd-pro-worktabs__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  padding: 0 16px;
  font-size: var(--uj-font-size-sm, 13px);
  color: var(--uj-text-muted, #64748b);
  border-bottom: 1px solid var(--uj-border-soft, rgb(94 181 162 / 0.15));
}

.yd-pro-worktabs__role {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--uj-brand-deep, #2a6b60);
  background: var(--uj-brand-muted, rgb(74 155 140 / 0.14));
}

.yd-pro-worktabs--client .yd-pro-worktabs__role,
.yd-pro-worktabs--agent .yd-pro-worktabs__role,
.yd-pro-worktabs--partner .yd-pro-worktabs__role {
  color: var(--uj-brand-deep);
  background: var(--uj-brand-muted);
}

.yd-pro-worktabs__dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: var(--uj-border-soft, #cbd5e1);
  flex-shrink: 0;
}

.yd-pro-worktabs__user {
  font-weight: 500;
  color: var(--uj-text-secondary, #475569);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.yd-pro-worktabs__clear {
  margin-left: auto;
  padding: 2px 8px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 12px;
  color: var(--uj-text-muted, #94a3b8);
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease;
  font-family: inherit;
}
.yd-pro-worktabs__clear:hover {
  color: var(--uj-brand-deep, #2a6b60);
  background: var(--uj-brand-muted, rgb(74 155 140 / 0.1));
}

.yd-pro-worktabs__strip {
  display: flex;
  align-items: center;
  gap: 4px;
  height: var(--uj-worktab-height, 40px);
  padding: 0 12px;
  overflow-x: auto;
  scrollbar-width: none;
}
.yd-pro-worktabs__strip::-webkit-scrollbar {
  display: none;
}

.yd-pro-worktabs__tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  max-width: 168px;
  padding: 0 10px 0 12px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: var(--uj-text-muted, #64748b);
  font-size: var(--uj-font-size-sm, 13px);
  font-family: var(--uj-font-sans);
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  position: relative;
  transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
}

.yd-pro-worktabs__tab::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 2px;
  height: 14px;
  border-radius: 0 2px 2px 0;
  background: var(--uj-brand, #4a9b8c);
  transition: transform 0.15s ease;
}

.yd-pro-worktabs__tab:hover {
  background: var(--uj-surface-hover, rgb(255 255 255 / 0.55));
  color: var(--uj-brand-deep, #2a6b60);
  border-color: var(--uj-border-soft, rgb(94 181 162 / 0.22));
}

.yd-pro-worktabs__tab.active {
  color: var(--uj-brand-deep, #2a6b60);
  font-weight: 600;
  background: var(--uj-surface-active, rgb(74 155 140 / 0.14));
  border-color: color-mix(in srgb, var(--uj-brand, #4a9b8c) 25%, transparent);
  box-shadow: inset 0 1px 0 var(--uj-surface-inset, rgb(255 255 255 / 0.65));
}

.yd-pro-worktabs__tab.active::before {
  transform: translateY(-50%) scaleY(1);
  background: var(--uj-brand, #4a9b8c);
}

.yd-pro-worktabs__tab-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.yd-pro-worktabs__tab-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 4px;
  opacity: 0.45;
  flex-shrink: 0;
  transition: opacity 0.15s ease, background 0.15s ease, color 0.15s ease;
}
.yd-pro-worktabs__tab-close:hover {
  opacity: 1;
  background: rgb(239 68 68 / 0.12);
  color: #dc2626;
}

.yd-pro-worktabs--tabs-only .yd-pro-worktabs__strip {
  border-top: none;
}

@media (max-width: 768px) {
  .yd-pro-worktabs__meta {
    padding: 0 12px;
  }
  .yd-pro-worktabs__clear {
    display: none;
  }
  .yd-pro-worktabs__tab {
    max-width: 132px;
  }
}
</style>
