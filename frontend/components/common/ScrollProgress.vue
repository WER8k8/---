<template>
  <div
    ref="container"
    class="scroll-progress-container"
  >
    <div
      class="scroll-progress-bar"
      :style="{ width: `${progress}%` }"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const container = ref<HTMLElement | null>(null)
const progress = ref(0)

const handleScroll = () => {
  const scrollTop = window.scrollY
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  if (docHeight > 0) {
    progress.value = (scrollTop / docHeight) * 100
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.scroll-progress-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.1);
}

.scroll-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  transition: width 0.1s ease-out;
}
</style>
