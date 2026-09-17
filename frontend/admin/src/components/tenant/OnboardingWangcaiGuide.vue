/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div
    class="wangcai-guide"
    :class="{
      'wangcai-guide--nod': nodding,
      'wangcai-guide--peek': peeking,
      'wangcai-guide--point': pointing,
    }"
    aria-hidden="true"
  >
    <div class="wangcai-guide-bubble">
      <p>{{ bubbleText }}</p>
    </div>

    <!-- 狗爪指引 -->
    <svg class="wangcai-guide-paw" viewBox="0 0 64 64" aria-hidden="true">
      <ellipse cx="32" cy="38" rx="14" ry="12" fill="#fda4af" opacity="0.95" />
      <circle cx="18" cy="22" r="7" fill="#fda4af" />
      <circle cx="32" cy="16" r="8" fill="#fda4af" />
      <circle cx="46" cy="22" r="7" fill="#fda4af" />
      <circle cx="24" cy="12" r="5" fill="#fda4af" />
      <circle cx="40" cy="12" r="5" fill="#fda4af" />
    </svg>

    <!-- 旺财探头（开户指引专用 · 客户站挂件逻辑不变） -->
    <div class="wangcai-guide-mascot">
      <svg viewBox="0 0 120 120" class="wangcai-guide-face">
        <defs>
          <linearGradient id="og-body" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0f172a" />
            <stop offset="100%" stop-color="#312e81" />
          </linearGradient>
        </defs>
        <ellipse cx="60" cy="78" rx="36" ry="28" fill="url(#og-body)" />
        <path d="M30 52 L38 68 L46 50 Z" fill="#0f172a" />
        <path d="M90 52 L82 68 L74 50 Z" fill="#0f172a" />
        <circle cx="46" cy="76" r="9" fill="#fff" />
        <circle cx="74" cy="76" r="9" fill="#fff" />
        <circle cx="48" cy="78" r="4" fill="#0f172a" />
        <circle cx="76" cy="78" r="4" fill="#0f172a" />
        <ellipse cx="60" cy="88" rx="4" ry="2.5" fill="#fda4af" />
        <path d="M54 92 Q60 98 66 92" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" />
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue';

const props = withDefaults(
  defineProps<{
    bubbleText?: string;
    /** 指向的目标字段 key，用于触发 pointing 动画 */
    pointAt?: string;
  }>(),
  {
    bubbleText: '填好 WhatsApp / 微信，客户官网挂件就能一键联系您！',
    pointAt: 'whatsapp',
  },
);

const nodding = ref(false);
const peeking = ref(true);
const pointing = ref(false);

let nodTimer: ReturnType<typeof setInterval> | null = null;

watch(
  () => props.pointAt,
  () => {
    pointing.value = true;
    window.setTimeout(() => {
      pointing.value = false;
    }, 1800);
  },
  { immediate: true },
);

onMounted(() => {
  peeking.value = true;
  nodTimer = setInterval(() => {
    nodding.value = true;
    window.setTimeout(() => {
      nodding.value = false;
    }, 700);
  }, 3200);
});

onUnmounted(() => {
  if (nodTimer) clearInterval(nodTimer);
});
</script>

<style scoped lang="scss">
.wangcai-guide {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-bottom: 16px;
  padding-right: 8px;
  pointer-events: none;
  user-select: none;
}

.wangcai-guide-bubble {
  flex: 1;
  position: relative;
  padding: 10px 14px;
  background: linear-gradient(135deg, #eef2ff, #fdf4ff);
  border: 1px solid #c7d2fe;
  border-radius: 14px 14px 14px 4px;
  box-shadow: 0 6px 20px rgb(99 102 241 / 0.12);

  p {
    margin: 0;
    font-size: 13px;
    line-height: 1.5;
    color: #312e81;
    font-weight: 500;
  }
}

.wangcai-guide-mascot {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  animation: guide-bob 2.2s ease-in-out infinite;
}

.wangcai-guide-face {
  width: 100%;
  height: 100%;
  display: block;
  filter: drop-shadow(0 4px 12px rgb(49 46 129 / 0.25));
}

.wangcai-guide-paw {
  position: absolute;
  right: 62px;
  bottom: -4px;
  width: 36px;
  height: 36px;
  transform: rotate(-25deg);
  opacity: 0;
  transition: opacity 0.2s;
}

.wangcai-guide--peek .wangcai-guide-mascot {
  animation: guide-peek 1.2s ease-out 1, guide-bob 2.2s ease-in-out 1.2s infinite;
}

.wangcai-guide--nod .wangcai-guide-mascot {
  animation: guide-nod 0.65s ease-in-out;
}

.wangcai-guide--point .wangcai-guide-paw {
  opacity: 1;
  animation: guide-paw-tap 0.55s ease-in-out 3;
}

@keyframes guide-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

@keyframes guide-peek {
  0% { transform: translateY(12px) scale(0.85); opacity: 0; }
  70% { transform: translateY(-2px) scale(1.02); opacity: 1; }
  100% { transform: translateY(0) scale(1); opacity: 1; }
}

@keyframes guide-nod {
  0%, 100% { transform: rotate(0deg); }
  35% { transform: rotate(8deg); }
  70% { transform: rotate(-4deg); }
}

@keyframes guide-paw-tap {
  0%, 100% { transform: rotate(-25deg) translateY(0); }
  50% { transform: rotate(-15deg) translateY(-6px); }
}
</style>
