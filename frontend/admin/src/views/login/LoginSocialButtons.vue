<template>
  <div class="social-btns">
    <button type="button" class="social-btn" @click="$emit('start-oauth', 'wechat')">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M10.5 2C5.26 2 1 5.58 1 10c0 2.5 1.35 4.74 3.5 6.24V22l4.5-2.5c.63.17 1.29.26 2 .26.34 0 .68-.02 1-.05A7.48 7.48 0 0 1 10.5 16.5c0-3.87 3.58-7 8-7 .34 0 .68.02 1 .06C18.44 5.72 14.84 2 10.5 2zM7 7.5c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm7 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/><path d="M22.5 16.5c0-3.31-3.13-6-7-6s-7 2.69-7 6 3.13 6 7 6c.82 0 1.61-.11 2.35-.32l2.65 1.32-.68-2.05C21.3 20.44 22.5 18.6 22.5 16.5zm-9.5-1c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm5 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z"/></svg>
      <span>微信扫码登录</span>
    </button>
    <button type="button" class="social-btn" @click="$emit('start-oauth', 'feishu')">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z" /><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2" /><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2" /><path d="M10 6h4" /><path d="M10 10h4" /><path d="M10 14h4" /><path d="M10 18h4" /></svg>
      <span>企业微信登录</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { type OAuthProvider } from '@/api/oauth'

defineEmits<{
  'start-oauth': [provider: OAuthProvider]
}>()
</script>

<style scoped>
.social-btns {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

.social-btn {
  width: 100%;
  padding: 0.625rem;
  border-radius: var(--uj-radius-md);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background-color: #fafafa;
  border: 1px solid #d9d9d9;
  color: #595959;
  transition: border-color var(--uj-duration) var(--uj-ease), background-color var(--uj-duration) var(--uj-ease);
}
.social-btn:hover {
  border-color: var(--uj-brand);
  background-color: rgba(74, 155, 140, 0.06);
}
:root[data-uj-theme='dark'] .social-btn {
  background-color: #262626;
  border-color: #424242;
  color: #bfbfbf;
}
:root[data-uj-theme='dark'] .social-btn:hover {
  border-color: var(--uj-brand);
  background-color: rgba(74, 155, 140, 0.12);
}
</style>
