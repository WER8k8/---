/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';

interface Props {
  threshold?: number;
  rootMargin?: string;
}

const props = withDefaults(defineProps<Props>(), {
  threshold: 0.1,
  rootMargin: '50px',
});

const containerRef = ref<HTMLElement>();
const isInView = ref(false);
const observer = ref<IntersectionObserver>();

onMounted(() => {
  if (import.meta.client) {
    observer.value = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          isInView.value = entry.isIntersecting;
        });
      },
      {
        threshold: props.threshold,
        rootMargin: props.rootMargin,
      }
    );

    if (containerRef.value) {
      observer.value.observe(containerRef.value);
    }
  }
});

onUnmounted(() => {
  observer.value?.disconnect();
});

const animationClass = computed(() => {
  return isInView.value ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8';
});
</script>

<template>
  <div
    ref="containerRef"
    class="transition-all duration-500 ease-out"
    :class="animationClass"
  >
    <slot :is-in-view="isInView" />
  </div>
</template>
