/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div
    class="meoo-cat-mascot-wrapper"
    :class="[`mood-${mood}`, { 'is-thinking': mood === 'think' }]"
    :style="{ width: typeof size === 'number' ? `${size}px` : size, height: typeof size === 'number' ? `${size}px` : size }"
    aria-hidden="true"
  >
    <div class="meoo-cat-glow-halo" />
    <img
      :src="meooCatImg"
      alt="小 Me"
      class="meoo-cat-img"
      draggable="false"
    />
    <!-- 思考状态微光指示晶片 -->
    <span v-if="mood === 'think'" class="meoo-think-sparkle" />
  </div>
</template>

<script setup lang="ts">
import meooCatImg from '@/assets/images/meoo-cat.png'

withDefaults(
  defineProps<{
    size?: number | string;
    mood?: 'happy' | 'think' | 'idle';
  }>(),
  {
    size: 48,
    mood: 'happy',
  },
);
</script>

<style scoped>
.meoo-cat-mascot-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  user-select: none;
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.meoo-cat-mascot-wrapper:hover {
  transform: translateY(-2px) scale(1.04);
}

.meoo-cat-glow-halo {
  position: absolute;
  inset: -15%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(244, 63, 94, 0.22) 0%, rgba(99, 102, 241, 0.12) 40%, transparent 70%);
  pointer-events: none;
  filter: blur(4px);
  opacity: 0.8;
  transition: opacity 0.3s ease;
}

.meoo-cat-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  filter: drop-shadow(0 4px 10px rgba(15, 23, 42, 0.35));
}

.mood-think .meoo-cat-glow-halo {
  opacity: 1;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.3) 0%, rgba(99, 102, 241, 0.2) 50%, transparent 70%);
}

.meoo-think-sparkle {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 8px #38bdf8;
  animation: pulse-sparkle 1.6s ease-in-out infinite alternate;
}

@keyframes pulse-sparkle {
  0% { transform: scale(0.8); opacity: 0.5; }
  100% { transform: scale(1.2); opacity: 1; }
}
</style>
