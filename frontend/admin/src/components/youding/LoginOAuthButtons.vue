/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="login-oauth-block">
    <div class="login-oauth-block__divider">
      <span>或使用以下方式登录</span>
    </div>
    <div class="login-oauth-block__grid">
      <button
        v-for="item in providers"
        :key="item.id"
        type="button"
        class="login-oauth-block__btn"
        :class="[
          `login-oauth-block__btn--${item.id}`,
          { 'login-oauth-block__btn--loading': loading === item.id },
        ]"
        :disabled="loading === item.id || !isAvailable(item.id)"
        :title="buttonTitle(item.id)"
        @click="emit('start', item.id)"
      >
        <span class="login-oauth-block__icon" aria-hidden="true">
          <svg v-if="item.id === 'wechat'" viewBox="0 0 24 24" width="22" height="22">
            <circle cx="12" cy="12" r="12" fill="currentColor" />
            <path
              fill="#fff"
              d="M8.5 7.5c-2.5 0-4.5 1.6-4.5 3.6 0 1.1.6 2.1 1.6 2.8l-.4 1.8 1.9-.9c.6.2 1.3.3 2 .3.1 0 .3 0 .4 0-.1-.4-.2-.8-.2-1.2 0-2.4 2.2-4.4 5-4.4.3 0 .6 0 .9.1C14.2 8.5 11.5 7.5 8.5 7.5zm-1.3 3a.9.9 0 1 1 0-1.8.9.9 0 0 1 0 1.8zm2.6 0a.9.9 0 1 1 0-1.8.9.9 0 0 1 0 1.8zm5.2 1.2c-2.2 0-4 1.4-4 3.1 0 .9.5 1.7 1.3 2.3l-.3 1.3 1.4-.7c.5.1 1 .2 1.5.2 2.2 0 4-1.4 4-3.1s-1.8-3.1-4-3.1zm-1.1 2.2a.7.7 0 1 1 0-1.4.7.7 0 0 1 0 1.4zm2.2 0a.7.7 0 1 1 0-1.4.7.7 0 0 1 0 1.4z"
            />
          </svg>
          <svg v-else-if="item.id === 'qq'" viewBox="0 0 24 24" width="22" height="22">
            <circle cx="12" cy="12" r="12" fill="currentColor" />
            <path
              fill="#fff"
              d="M12 6c-3.3 0-6 2.4-6 5.4v2.2c0 .8.2 1.5.6 2.1L6 17l1.8-.5c1 .3 2.1.5 3.2.5h.5c1.1 0 2.2-.2 3.2-.5L17 17l-.6-1.3c.4-.6.6-1.3.6-2.1v-2.2C17 8.4 15.3 6 12 6zm-2.2 4.2a1 1 0 1 1 0-2 1 1 0 0 1 0 2zm4.4 0a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"
            />
          </svg>
          <svg v-else-if="item.id === 'feishu'" viewBox="0 0 24 24" width="22" height="22">
            <rect width="24" height="24" rx="6" fill="currentColor" />
            <path
              fill="#fff"
              d="M6 8.5 10.5 6v4.5L6 13V8.5zm12 0L13.5 6v4.5L18 13V8.5zM6 15.5 10.5 18v-4.5L6 11v4.5zm12 0L13.5 18v-4.5L18 11v4.5z"
            />
          </svg>
          <svg v-else-if="item.id === 'dingtalk'" viewBox="0 0 24 24" width="22" height="22">
            <rect width="24" height="24" rx="6" fill="currentColor" />
            <path fill="#fff" d="M12 5.5 7 18.5h2.1l.9-2.4h3.8l.9 2.4H17L12 5.5zm-.2 8.2-.9-2.4h1.8l-.9 2.4z" />
          </svg>
        </span>
        <span class="login-oauth-block__label">{{ item.label }}登录</span>
      </button>
    </div>
    <p v-if="hint && !devBypass" class="login-oauth-block__hint">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { oauthProviderLabel, type OAuthProvider } from '@/api/oauth';

const props = withDefaults(
  defineProps<{
    ready: Record<OAuthProvider, boolean>;
    devBypass?: boolean;
    loading?: OAuthProvider | '';
    hint?: string;
  }>(),
  {
    devBypass: false,
    loading: '',
    hint: '',
  },
);

const emit = defineEmits<{ start: [provider: OAuthProvider] }>();

const providers: { id: OAuthProvider; label: string }[] = [
  { id: 'wechat', label: '微信' },
  { id: 'qq', label: 'QQ' },
  { id: 'feishu', label: '飞书' },
  { id: 'dingtalk', label: '钉钉' },
];

function isAvailable(provider: OAuthProvider): boolean {
  return props.devBypass || props.ready[provider];
}

function buttonTitle(provider: OAuthProvider): string {
  if (isAvailable(provider)) return `使用${oauthProviderLabel(provider)}登录`;
  return `${oauthProviderLabel(provider)} 未配置（需在 backend/.env 填写 AppId/Secret）`;
}
</script>

<style scoped lang="scss">
.login-oauth-block__divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 28px 0 16px;
  color: var(--login-text-muted);
  font-size: 12px;
}
.login-oauth-block__divider::before,
.login-oauth-block__divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--login-border);
}
.login-oauth-block__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.login-oauth-block__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 12px;
  border: 1px solid var(--login-border);
  border-radius: 10px;
  background: #fff;
  color: var(--login-text-on-light);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease,
    transform 0.12s ease;
}
.login-oauth-block__btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgb(15 23 42 / 0.06);
}
.login-oauth-block__btn:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}
.login-oauth-block__btn--wechat {
  color: #07c160;
}
.login-oauth-block__btn--qq {
  color: #12b7f5;
}
.login-oauth-block__btn--feishu {
  color: #3370ff;
}
.login-oauth-block__btn--dingtalk {
  color: #0089ff;
}
.login-oauth-block__icon {
  display: flex;
  flex-shrink: 0;
}
.login-oauth-block__label {
  white-space: nowrap;
}
.login-oauth-block__hint {
  margin: 10px 0 0;
  font-size: 11px;
  color: var(--login-text-muted);
  text-align: center;
  line-height: 1.5;
}
</style>
