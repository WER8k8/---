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

interface PerformanceMetrics {
  fps: number
  memoryUsage: number
  loadTime: number
}

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
let fpsInterval: NodeJS.Timeout | null = null

// Calculate FPS
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

// Get memory usage (Chrome only)
const getMemoryUsage = () => {
  // @ts-ignore - performance.memory is Chrome-specific
  if (performance.memory) {
    // @ts-ignore
    const usedMB = performance.memory.usedJSHeapSize / 1048576
    memoryUsage.value = Math.round(usedMB * 100) / 100
  }
}

// Calculate page load time
const calculateLoadTime = () => {
  if (process.client && window.performance) {
    const timing = window.performance.timing
    loadTime.value = timing.loadEventEnd - timing.navigationStart
  }
}

// Start monitoring
onMounted(() => {
  if (!isDev || !props.showMetrics) return

  calculateLoadTime()

  // Animation frame loop for FPS
  const loop = () => {
    calculateFPS()
    requestAnimationFrame(loop)
  }
  requestAnimationFrame(loop)

  // Update memory every second
  fpsInterval = setInterval(() => {
    getMemoryUsage()
  }, 1000)
})

onUnmounted(() => {
  if (fpsInterval) {
    clearInterval(fpsInterval)
  }
})

// Web Vitals reporting
if (process.client && 'PerformanceObserver' in window) {
  // Largest Contentful Paint
  try {
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      const lastEntry = entries[entries.length - 1]
      console.log('LCP:', lastEntry.startTime)
    })
    lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] })
  } catch (e) {
    // LCP not supported
  }

  // First Input Delay
  try {
    const fidObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      entries.forEach((entry) => {
        console.log('FID:', entry.processingStart - entry.startTime)
      })
    })
    fidObserver.observe({ entryTypes: ['first-input'] })
  } catch (e) {
    // FID not supported
  }

  // Cumulative Layout Shift
  try {
    let clsValue = 0
    const clsObserver = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry: any) => {
        if (!entry.hadRecentInput) {
          clsValue += entry.value
        }
      })
      console.log('CLS:', clsValue)
    })
    clsObserver.observe({ entryTypes: ['layout-shift'] })
  } catch (e) {
    // CLS not supported
  }
}
</script>
