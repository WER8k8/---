<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 64 64"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    :class="['caiwang-mascot', `mood-${mood}`]"
    aria-hidden="true"
  >
    <!-- 光晕 -->
    <circle cx="32" cy="34" r="28" :fill="`url(#cwGlow-${uid})`" opacity="0.4" />

    <!-- 尾巴 -->
    <path
      class="cw-tail"
      d="M52 38c6 2 8 8 6 14-2 4-6 5-8 2"
      :stroke="`url(#cwEar-${uid})`"
      stroke-width="4"
      stroke-linecap="round"
      fill="none"
    />

    <!-- 左耳 -->
    <path
      d="M14 26c-2-10 4-18 12-14 3 2 4 8 2 12l-6 8c-4-2-7-4-8-6z"
      :fill="`url(#cwEar-${uid})`"
    />
    <!-- 右耳 -->
    <path
      d="M50 26c2-10-4-18-12-14-3 2-4 8-2 12l6 8c4-2 7-4 8-6z"
      :fill="`url(#cwEar-${uid})`"
    />
    <path d="M18 24c2 4 4 7 6 9M46 24c-2 4-4 7-6 9" stroke="#b45309" stroke-width="1.2" stroke-linecap="round" opacity="0.25" />

    <!-- 脸 -->
    <ellipse cx="32" cy="36" rx="20" ry="18" :fill="`url(#cwFace-${uid})`" />

    <!-- 眼睛 -->
    <ellipse cx="24" cy="34" rx="5" ry="6" fill="#fff" />
    <ellipse cx="40" cy="34" rx="5" ry="6" fill="#fff" />
    <circle cx="25" cy="35" r="3" fill="#1c1917" />
    <circle cx="41" cy="35" r="3" fill="#1c1917" />
    <circle cx="26.2" cy="33.5" r="1.2" fill="#fff" />
    <circle cx="42.2" cy="33.5" r="1.2" fill="#fff" />
    <!-- 思考眯眼 -->
    <path
      v-if="mood === 'think'"
      d="M20 34q4-3 8 0M36 34q4-3 8 0"
      stroke="#78350f"
      stroke-width="1.8"
      stroke-linecap="round"
      fill="none"
      opacity="0.85"
    />

    <!-- 鼻子 -->
    <ellipse cx="32" cy="40" rx="4" ry="3" fill="#292524" />
    <ellipse cx="32" cy="39.2" rx="1.2" ry="0.8" fill="#fff" opacity="0.35" />

    <!-- 嘴 + 舌头 -->
    <path
      v-if="mood === 'happy'"
      d="M26 42q6 8 12 0"
      stroke="#92400e"
      stroke-width="1.6"
      stroke-linecap="round"
      fill="none"
    />
    <ellipse v-if="mood === 'happy'" cx="32" cy="46" rx="4" ry="3" fill="#fb7185" />
    <path
      v-else-if="mood === 'think'"
      d="M28 44h8"
      stroke="#92400e"
      stroke-width="1.6"
      stroke-linecap="round"
    />
    <path
      v-else
      d="M28 43q4 3 8 0"
      stroke="#92400e"
      stroke-width="1.5"
      stroke-linecap="round"
      fill="none"
    />

    <!-- 腮红 -->
    <ellipse cx="17" cy="38" rx="3.2" ry="2" fill="#fb923c" opacity="0.35" />
    <ellipse cx="47" cy="38" rx="3.2" ry="2" fill="#fb923c" opacity="0.35" />

    <!-- 项圈 + 财字牌 -->
    <path d="M18 48c4 4 24 4 28 0" stroke="var(--uj-brand, #4a9b8c)" stroke-width="3" stroke-linecap="round" />
    <circle cx="32" cy="50" r="6" fill="#fbbf24" stroke="#f59e0b" stroke-width="1" />
    <text x="32" y="52.5" text-anchor="middle" fill="#92400e" font-size="7" font-weight="800" font-family="system-ui,sans-serif">财</text>

    <defs>
      <linearGradient :id="`cwFace-${uid}`" x1="12" y1="18" x2="52" y2="54" gradientUnits="userSpaceOnUse">
        <stop stop-color="#fff7ed" />
        <stop offset="0.55" stop-color="#fde68a" />
        <stop offset="1" stop-color="#fbbf24" />
      </linearGradient>
      <linearGradient :id="`cwEar-${uid}`" x1="10" y1="8" x2="54" y2="30" gradientUnits="userSpaceOnUse">
        <stop stop-color="#fcd34d" />
        <stop offset="1" stop-color="#d97706" />
      </linearGradient>
      <radialGradient
        :id="`cwGlow-${uid}`"
        cx="0"
        cy="0"
        r="1"
        gradientUnits="userSpaceOnUse"
        gradientTransform="translate(32 34) scale(28)"
      >
        <stop stop-color="#fbbf24" />
        <stop offset="1" stop-color="#fbbf24" stop-opacity="0" />
      </radialGradient>
    </defs>
  </svg>
</template>

<script setup lang="ts">
import { useId } from 'vue'

withDefaults(
  defineProps<{
    size?: number | string
    mood?: 'happy' | 'think' | 'idle'
  }>(),
  {
    size: 48,
    mood: 'happy',
  },
)

const uid = useId().replace(/:/g, '')
</script>

<style scoped>
.caiwang-mascot {
  display: block;
  flex-shrink: 0;
  transform-origin: center bottom;
}
.mood-happy {
  animation: cw-wiggle 2s ease-in-out infinite;
}
.mood-happy .cw-tail {
  animation: cw-wag 0.45s ease-in-out infinite alternate;
  transform-origin: 52px 38px;
}
.mood-think {
  animation: cw-bob 1.1s ease-in-out infinite;
}
.mood-idle {
  animation: cw-breathe 2.8s ease-in-out infinite;
}
@keyframes cw-wiggle {
  0%,
  100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(-2deg);
  }
  75% {
    transform: rotate(2deg);
  }
}
@keyframes cw-wag {
  from {
    transform: rotate(-8deg);
  }
  to {
    transform: rotate(14deg);
  }
}
@keyframes cw-bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-2px);
  }
}
@keyframes cw-breathe {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.03);
  }
}
</style>
