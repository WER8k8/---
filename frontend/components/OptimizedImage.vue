<template>
  <div
    ref="containerRef"
    class="relative overflow-hidden"
    :class="containerClass"
  >
    <!-- Placeholder/Loading state -->
    <div
      v-show="!isLoaded"
      class="absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center"
      :class="placeholderClass"
    >
      <svg
        v-if="showPlaceholderIcon"
        class="w-8 h-8 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
        />
      </svg>
    </div>

    <!-- Actual image -->
    <img
      v-show="isLoaded"
      ref="imageRef"
      :src="finalSrc"
      :alt="alt"
      :width="width"
      :height="height"
      :class="['transition-opacity duration-300', isLoaded ? 'opacity-100' : 'opacity-0', imageClass]"
      :loading="loadingStrategy"
      :decoding="decoding"
      @load="handleLoad"
      @error="handleError"
    >

    <!-- Error state -->
    <div
      v-if="hasError && showFallback"
      class="absolute inset-0 bg-gray-100 flex items-center justify-center"
    >
      <slot name="fallback">
        <div class="text-center text-gray-400">
          <svg
            class="w-8 h-8 mx-auto mb-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span class="text-sm">图片加载失败</span>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface LazyImageProps {
  src: string
  alt?: string
  width?: number | string
  height?: number | string
  
  // Styling
  containerClass?: string
  imageClass?: string
  placeholderClass?: string
  
  // Loading behavior
  threshold?: number
  rootMargin?: string
  loading?: 'lazy' | 'eager'
  
  // Display options
  showPlaceholderIcon?: boolean
  showFallback?: boolean
  decoding?: 'async' | 'sync' | 'auto'
}

const props = withDefaults(defineProps<LazyImageProps>(), {
  alt: '',
  threshold: 0.1,
  rootMargin: '50px',
  loading: 'lazy',
  showPlaceholderIcon: true,
  showFallback: true,
  decoding: 'async'
})

const containerRef = ref<HTMLElement | null>(null)
const imageRef = ref<HTMLImageElement | null>(null)
const isLoaded = ref(false)
const hasError = ref(false)
const isVisible = ref(false)

// Determine loading strategy based on prop and visibility
const loadingStrategy = computed(() => {
  if (props.loading === 'eager') return 'eager'
  return isVisible.value ? 'eager' : 'lazy'
})

// Final source URL (could be modified for responsive images)
const finalSrc = computed(() => props.src)

// Handle image load event
const handleLoad = () => {
  isLoaded.value = true
}

// Handle image error event
const handleError = (e: Event) => {
  console.warn('Image failed to load:', props.src)
  hasError.value = true
}

// Setup intersection observer for lazy loading
onMounted(() => {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          isVisible.value = true
          observer.unobserve(entry.target)
        }
      })
    },
    {
      threshold: props.threshold,
      rootMargin: props.rootMargin
    }
  )

  if (containerRef.value) {
    observer.observe(containerRef.value)
  }

  onUnmounted(() => {
    observer.disconnect()
  })
})

// Expose refs for parent component access
defineExpose({
  containerRef,
  imageRef,
  isLoaded,
  hasError
})
</script>
