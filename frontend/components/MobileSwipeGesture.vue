/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

interface SwipeResult {
  direction: 'left' | 'right' | 'up' | 'down';
  velocity: number;
}

interface Props {
  threshold?: number;
  onSwipe?: (result: SwipeResult) => void;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
}

const props = withDefaults(defineProps<Props>(), {
  threshold: 50,
});

const startX = ref(0);
const startY = ref(0);
const isSwiping = ref(false);

function handleTouchStart(e: TouchEvent) {
  const touch = e.touches[0];
  startX.value = touch.clientX;
  startY.value = touch.clientY;
  isSwiping.value = true;
}

function handleTouchEnd(e: TouchEvent) {
  if (!isSwiping.value) return;

  const touch = e.changedTouches[0];
  const deltaX = touch.clientX - startX.value;
  const deltaY = touch.clientY - startY.value;
  const absDeltaX = Math.abs(deltaX);
  const absDeltaY = Math.abs(deltaY);

  let direction: 'left' | 'right' | 'up' | 'down';
  let velocity: number;

  if (absDeltaX > absDeltaY) {
    velocity = absDeltaX;
    direction = deltaX > 0 ? 'right' : 'left';
  } else {
    velocity = absDeltaY;
    direction = deltaY > 0 ? 'down' : 'up';
  }

  if (velocity > props.threshold) {
    props.onSwipe?.({ direction, velocity });

    switch (direction) {
      case 'left':
        props.onSwipeLeft?.();
        break;
      case 'right':
        props.onSwipeRight?.();
        break;
      case 'up':
        props.onSwipeUp?.();
        break;
      case 'down':
        props.onSwipeDown?.();
        break;
    }
  }

  isSwiping.value = false;
}
</script>

<template>
  <div
    @touchstart="handleTouchStart"
    @touchend="handleTouchEnd"
  >
    <slot />
  </div>
</template>
