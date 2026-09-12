<template>
  <div>
    <!-- This component doesn't render anything visible in production -->
    <div
      v-if="showMetrics && isDev"
      class="fixed bottom-4 right-4 bg-black/80 text-white text-xs p-3 rounded-lg z-50 font-mono"
    >
      <div class="space-y-1">
        <div>FPS: {{ fps }}</div>
        <div>Memory: {{ memoryUsage }} MB</div>
        <div>Load Time: {{ loadTime }} ms</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Performance Monitor Component
 * 
 * Displays real-time performance metrics in development mode.
 * Tracks FPS, memory usage, and page load time.
 */

const props = withDefaults(defineProps<{
  showMetrics?: boolean
}>(), {
  showMetrics: false
})

const isDev = process.dev
const fps = ref(0)
const memoryUsage = ref(0)
const loadTime = ref(0)

let frameCount = 0
let lastTime = performance.now()
let fpsInterval: ReturnType<typeof setInterval> | null = null
let rafId: number | null = null

const calculateFPS = () => {
  const now = performance.now()
  const delta = now - lastTime

  if (delta >= 1000) {
    fps.value = Math.round((frameCount * 1000) / delta)
    frameCount = 0
    lastTime = now
  } else {
    frameCount++
  }
}

const getMemoryUsage = () => {
  // @ts-ignore - performance.memory is Chrome-specific
  if (performance.memory) {
    // @ts-ignore
    const usedMB = performance.memory.usedJSHeapSize / 1048576
    memoryUsage.value = Math.round(usedMB * 100) / 100
  }
}

const calculateLoadTime = () => {
  if (process.client && window.performance?.timing) {
    loadTime.value = window.performance.timing.loadEventEnd - window.performance.timing.navigationStart
  }
}

onMounted(() => {
  if (!isDev || !props.showMetrics) return

  calculateLoadTime()

  const loop = () => {
    calculateFPS()
    rafId = requestAnimationFrame(loop)
  }
  rafId = requestAnimationFrame(loop)

  fpsInterval = setInterval(() => {
    getMemoryUsage()
  }, 1000)
})

onUnmounted(() => {
  if (fpsInterval) {
    clearInterval(fpsInterval)
    fpsInterval = null
  }
  if (rafId !== null) {
    cancelAnimationFrame(rafId)
    rafId = null
  }
})

// Web Vitals reporting (dev only)
if (process.dev && process.client && 'PerformanceObserver' in window) {
  try {
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      if (process.dev) console.log('[Perf] LCP:', entries[entries.length - 1]?.startTime)
    })
    lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })
  } catch (_) { /* not supported */ }

  try {
    const fidObserver = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (process.dev) console.log('[Perf] FID:', entry.processingStart - entry.startTime)
      })
    })
    fidObserver.observe({ entryTypes: ['first-input'] })
  } catch (_) { /* not supported */ }

  try {
    let clsValue = 0
    const clsObserver = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry: any) => {
        if (!entry.hadRecentInput) clsValue += entry.value
      })
      if (process.dev) console.log('[Perf] CLS:', clsValue)
    })
    clsObserver.observe({ entryTypes: ['layout-shift'] })
  } catch (_) { /* not supported */ }
}
</script>
