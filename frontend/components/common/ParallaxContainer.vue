<template>
  <div
    ref="container"
    class="parallax-container"
    :style="containerStyle"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  speed?: number
  direction?: 'up' | 'down' | 'left' | 'right'
}>(), {
  speed: 0.5,
  direction: 'up'
})

const container = ref<HTMLElement | null>(null)
const scrollY = ref(0)

const containerStyle = computed(() => {
  const offset = scrollY.value * props.speed
  const transforms: string[] = []
  
  switch (props.direction) {
    case 'up':
      transforms.push(`translateY(${offset}px)`)
      break
    case 'down':
      transforms.push(`translateY(${-offset}px)`)
      break
    case 'left':
      transforms.push(`translateX(${offset}px)`)
      break
    case 'right':
      transforms.push(`translateX(${-offset}px)`)
      break
  }
  
  return {
    transform: transforms.join(' '),
    willChange: 'transform'
  }
})

const handleScroll = () => {
  scrollY.value = window.scrollY
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.parallax-container {
  transition: transform 0.1s linear;
}
</style>
