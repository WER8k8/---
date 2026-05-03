<template>
  <div
    ref="target"
    :class="{ 'is-visible': isVisible, 'animate-on-scroll': true }"
    :style="animationStyle"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  animation?: 'fade-in' | 'slide-up' | 'slide-left' | 'slide-right' | 'zoom-in' | 'flip'
  delay?: number
  duration?: number
  threshold?: number
}>(), {
  animation: 'fade-in',
  delay: 0,
  duration: 600,
  threshold: 0.1
})

const target = ref<HTMLElement | null>(null)
const isVisible = ref(false)

const animationStyle = computed(() => ({
  '--animation-delay': `${props.delay}ms`,
  '--animation-duration': `${props.duration}ms`
}))

let observer: IntersectionObserver | null = null

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          isVisible.value = true
          observer?.unobserve(entry.target)
        }
      })
    },
    { threshold: props.threshold }
  )

  if (target.value) {
    observer.observe(target.value)
  }
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
})
</script>

<style scoped>
.animate-on-scroll {
  opacity: 0;
  transition: opacity var(--animation-duration) ease-out, transform var(--animation-duration) ease-out;
}

.animate-on-scroll.is-visible {
  opacity: 1;
}

.animate-on-scroll[animation="fade-in"] {
  transform: none;
}

.animate-on-scroll[animation="slide-up"] {
  transform: translateY(40px);
}

.animate-on-scroll[animation="slide-left"] {
  transform: translateX(40px);
}

.animate-on-scroll[animation="slide-right"] {
  transform: translateX(-40px);
}

.animate-on-scroll[animation="zoom-in"] {
  transform: scale(0.9);
}

.animate-on-scroll[animation="flip"] {
  transform: perspective(400px) rotateY(15deg);
}

.animate-on-scroll.is-visible[animation="fade-in"] {
  transform: none;
}

.animate-on-scroll.is-visible[animation="slide-up"] {
  transform: translateY(0);
}

.animate-on-scroll.is-visible[animation="slide-left"] {
  transform: translateX(0);
}

.animate-on-scroll.is-visible[animation="slide-right"] {
  transform: translateX(0);
}

.animate-on-scroll.is-visible[animation="zoom-in"] {
  transform: scale(1);
}

.animate-on-scroll.is-visible[animation="flip"] {
  transform: perspective(400px) rotateY(0);
}
</style>
