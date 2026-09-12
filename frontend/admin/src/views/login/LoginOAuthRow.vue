<template>
  <div>
    <div class="oauth-row">
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        class="oauth-icon-btn"
        :class="{ 'oauth-icon-btn--muted': !item.available }"
        :title="item.title"
        :disabled="loading === item.id"
        @click="$emit('start-oauth', item.id)"
        v-html="item.icon"
      />
    </div>
    <div v-if="hint" class="oauth-hint-wrap">
      <div class="oauth-hint">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" /></svg>
        <span>{{ hint }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { type OAuthProvider } from '@/api/oauth'

interface OAuthItem {
  id: OAuthProvider
  icon: string
  available: boolean
  title: string
}

defineProps<{
  items: OAuthItem[]
  loading: string
  hint: string
  devBypass: boolean
}>()

defineEmits<{
  'start-oauth': [id: OAuthProvider]
}>()
</script>

<style scoped>
.oauth-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 0.25rem 0;
}

.oauth-icon-btn {
  width: 56px;
  height: 56px;
  padding: 0;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: #ffffff;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}
.oauth-icon-btn :deep(svg) {
  width: 32px;
  height: 32px;
  display: block;
  flex-shrink: 0;
}
.oauth-icon-btn:hover:not(:disabled) {
  border-color: rgba(74, 155, 140, 0.45);
  background: #ffffff;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.1), 0 0 0 3px rgba(74, 155, 140, 0.12);
  transform: translateY(-2px);
}
.oauth-icon-btn:focus-visible {
  outline: 2px solid var(--uj-brand, #4a9b8c);
  outline-offset: 2px;
}
:root[data-uj-theme='dark'] .oauth-icon-btn {
  border-color: rgba(255, 255, 255, 0.1);
  background: #1f1f1f;
  box-shadow: none;
}
:root[data-uj-theme='dark'] .oauth-icon-btn:hover:not(:disabled) {
  border-color: rgba(74, 155, 140, 0.45);
  background: #262626;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
}
.oauth-icon-btn--muted {
  opacity: 0.5;
  filter: grayscale(0.25);
}
.oauth-icon-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

.oauth-hint-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}
.oauth-hint {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border-radius: 999px;
  background: rgba(74, 155, 140, 0.08);
  border: 1px solid rgba(74, 155, 140, 0.15);
  font-size: 0.75rem;
  line-height: 1.4;
  color: var(--uj-brand, #4a9b8c);
}
:root[data-uj-theme='dark'] .oauth-hint {
  background: rgba(74, 155, 140, 0.12);
  border-color: rgba(74, 155, 140, 0.25);
  color: #6bb8a8;
}
</style>
