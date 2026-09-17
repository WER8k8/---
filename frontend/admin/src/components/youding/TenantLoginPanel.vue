/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <aside class="brand-col" :class="{ 'brand-col--dark': variant === 'dark' }">
    <div class="brand-col__inner">
      <div class="brand-col__logo">
        <span class="brand-col__mark">优</span>
        <span class="brand-col__name">优丁 YOU DING</span>
      </div>

      <h1 class="brand-col__title">
        {{ brandTitle[0] }}<br />
        {{ brandTitle[1] }}
      </h1>
      <p class="brand-col__lead">{{ subtitle }}</p>

      <div class="brand-col__features">
        <div v-for="(item, i) in features" :key="i" class="brand-col__feat">
          <LoginFeatureIcon :glyph="item.icon" />
          <div>
            <strong>{{ item.title }}</strong>
            <p>{{ item.desc }}</p>
          </div>
        </div>
      </div>

      <p class="brand-col__foot">{{ foot }}</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { LoginPortalFeature } from '@/constants/loginPortalCopy';
import LoginFeatureIcon from './LoginFeatureIcon.vue';

withDefaults(
  defineProps<{
    variant?: 'dark' | 'light';
    brandTitle?: [string, string];
    subtitle?: string;
    features?: LoginPortalFeature[];
    foot?: string;
  }>(),
  {
    variant: 'dark',
    brandTitle: () => ['外贸卖家', '出海工作台'],
    subtitle: '今天该盯哪条询盘、发哪批品，登录 30 秒就知道。',
    features: () => [
      { icon: '获', title: '获客', desc: '询盘、IM、国际线索进一个 inbox' },
      { icon: '发', title: '发品', desc: '母版 → 多平台发布，进度看得见' },
      { icon: '账', title: '账户', desc: '套餐、域名、用量一目了然' },
    ],
    foot: '建材外贸 · AI 卖货操作系统',
  },
);
</script>

<style scoped lang="scss">
.brand-col {
  width: 100%;
  max-width: 420px;
  position: relative;
  z-index: 1;
}
.brand-col__inner {
  width: 100%;
}
.brand-col--dark .brand-col__mark {
  background: linear-gradient(135deg, var(--uj-brand, #4a9b8c), #2a6b60);
  box-shadow: 0 8px 24px rgb(37 99 235 / 0.35);
}
.brand-col--dark .brand-col__name {
  color: rgb(255 255 255 / 0.88);
}
.brand-col--dark .brand-col__title {
  color: var(--login-text-on-dark);
}
.brand-col--dark .brand-col__lead {
  color: var(--login-text-on-dark-muted);
}
.brand-col--dark .brand-col__feat {
  background: var(--login-glass);
  border: 1px solid var(--login-glass-border);
  border-radius: var(--login-radius);
  backdrop-filter: blur(12px);
}
.brand-col--dark .brand-col__feat strong {
  color: var(--login-text-on-dark);
}
.brand-col--dark .brand-col__feat p {
  color: var(--login-text-on-dark-muted);
}
.brand-col--dark .brand-col__foot {
  color: var(--login-text-on-dark-muted);
}
.brand-col--dark :deep(.login-feat-icon) {
  background: rgb(37 99 235 / 0.2);
  color: #93c5fd;
}
.brand-col__logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 28px;
}
.brand-col__mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--login-primary), var(--login-primary-hover));
  color: #fff;
  font-weight: 700;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-col__name {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.brand-col__title {
  margin: 0 0 12px;
  font-size: 32px;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.02em;
}
.brand-col__lead {
  margin: 0 0 28px;
  font-size: 15px;
  font-weight: 400;
  line-height: 1.65;
}
.brand-col__features {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
}
.brand-col__feat {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 16px;
}
.brand-col__feat :deep(.login-feat-icon) {
  flex-shrink: 0;
}
.brand-col__feat strong {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 2px;
}
.brand-col__feat p {
  margin: 0;
  font-size: 12px;
  font-weight: 400;
  line-height: 1.5;
}
.brand-col__foot {
  margin: 0;
  font-size: 12px;
  font-weight: 400;
}
</style>
