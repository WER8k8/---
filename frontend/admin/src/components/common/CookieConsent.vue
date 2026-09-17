/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <transition name="cookie-fade">
    <div
      v-if="visible"
      class="cookie-banner"
      role="region"
      aria-label="Cookie 同意"
    >
      <div class="cookie-banner__inner">
        <div class="cookie-banner__text">
          <h3 class="cookie-banner__title">🍪 我们使用 Cookie</h3>
          <p class="cookie-banner__desc">
            优丁使用 Cookie 提升您的体验(记住登录、个性化设置、流量统计)。
            继续浏览即表示您同意我们的
            <router-link to="/privacy" class="cookie-banner__link">隐私政策</router-link>
            和
            <router-link to="/terms" class="cookie-banner__link">服务条款</router-link>。
          </p>
        </div>
        <div class="cookie-banner__actions">
          <button
            type="button"
            class="cookie-banner__btn cookie-banner__btn--secondary"
            @click="reject"
          >
            仅必要
          </button>
          <button
            type="button"
            class="cookie-banner__btn cookie-banner__btn--primary"
            @click="accept"
            autofocus
          >
            同意全部
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const STORAGE_KEY = 'uj-cookie-consent-v1';
const visible = ref(false);

onMounted(() => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (!stored) {
    // 延迟 1.5s 显示,避免抢首屏注意力
    setTimeout(() => {
      visible.value = true;
    }, 1500);
  }
});

function accept() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ status: 'accepted', at: new Date().toISOString() })
  );
  visible.value = false;
}

function reject() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ status: 'essential-only', at: new Date().toISOString() })
  );
  visible.value = false;
}
</script>

<style scoped lang="scss">
.cookie-banner {
  position: fixed;
  bottom: 16px;
  left: 16px;
  right: 16px;
  z-index: 9000;
  max-width: 760px;
  margin: 0 auto;
  background: var(--uj-bg-card, #ffffff);
  border: 1px solid var(--uj-border, #e2e8f0);
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(15, 23, 42, 0.12);
  font-family: var(--uj-font-sans);
}
.cookie-banner__inner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  flex-wrap: wrap;
}
.cookie-banner__text {
  flex: 1;
  min-width: 240px;
}
.cookie-banner__title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 4px;
  color: var(--uj-text, #0f172a);
}
.cookie-banner__desc {
  font-size: 13px;
  line-height: 1.55;
  color: var(--uj-text-muted, #475569);
  margin: 0;
}
.cookie-banner__link {
  color: var(--uj-brand, #4a9b8c);
  text-decoration: underline;
}
.cookie-banner__link:focus-visible {
  outline: 2px solid var(--uj-brand, #4a9b8c);
  outline-offset: 2px;
}
.cookie-banner__actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.cookie-banner__btn {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 10px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}
.cookie-banner__btn:focus-visible {
  outline: 2px solid var(--uj-brand, #4a9b8c);
  outline-offset: 2px;
}
.cookie-banner__btn--secondary {
  background: transparent;
  color: var(--uj-text, #0f172a);
  border-color: var(--uj-border, #e2e8f0);
}
.cookie-banner__btn--secondary:hover {
  background: #f1f5f9;
}
.cookie-banner__btn--primary {
  background: var(--uj-brand, #4a9b8c);
  color: #fff;
}
.cookie-banner__btn--primary:hover {
  background: #1d4ed8;
}
.cookie-fade-enter-active,
.cookie-fade-leave-active {
  transition: all 0.3s ease;
}
.cookie-fade-enter-from,
.cookie-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 600px) {
  .cookie-banner__inner {
    flex-direction: column;
    align-items: stretch;
  }
  .cookie-banner__actions {
    justify-content: flex-end;
  }
}

@media (prefers-reduced-motion: reduce) {
  .cookie-fade-enter-active,
  .cookie-fade-leave-active {
    transition: none;
  }
}
</style>
