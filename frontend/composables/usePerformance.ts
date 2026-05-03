export function useLazyImage(src: string, options?: {
  rootMargin?: string
  threshold?: number
}) {
  const imageRef = ref<HTMLImageElement | null>(null)
  const isLoaded = ref(false)
  const isInView = ref(false)

  const loadImage = () => {
    if (!src) return

    const img = new Image()
    img.onload = () => {
      isLoaded.value = true
    }
    img.src = src
  }

  onMounted(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            isInView.value = true
            loadImage()
            observer.unobserve(entry.target)
          }
        })
      },
      {
        rootMargin: options?.rootMargin || '50px',
        threshold: options?.threshold || 0.1
      }
    )

    if (imageRef.value) {
      observer.observe(imageRef.value)
    }

    onUnmounted(() => {
      observer.disconnect()
    })
  })

  return {
    imageRef,
    isLoaded,
    isInView
  }
}

export function useDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    timeoutId = setTimeout(() => {
      fn(...args)
      timeoutId = null
    }, delay)
  }
}

export function useThrottle<T extends (...args: any[]) => any>(
  fn: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false

  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      fn(...args)
      inThrottle = true
      setTimeout(() => {
        inThrottle = false
      }, limit)
    }
  }
}

export function useImagePreloader(sources: string[]) {
  const loaded = ref(0)
  const total = sources.length

  const preload = (src: string) => {
    return new Promise<void>((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve()
      img.onerror = reject
      img.src = src
    })
  }

  const preloadAll = async () => {
    const promises = sources.map(src => preload(src).catch(() => {}))
    await Promise.all(promises)
    loaded.value = total
  }

  onMounted(() => {
    preloadAll()
  })

  return {
    loaded,
    total,
    progress: computed(() => (loaded.value / total) * 100)
  }
}

export function useScrollToTop() {
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    })
  }

  return {
    scrollToTop
  }
}

export function useReducedMotion() {
  const prefersReducedMotion = ref(false)

  if (import.meta.client) {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.value = mediaQuery.matches

    mediaQuery.addEventListener('change', (e) => {
      prefersReducedMotion.value = e.matches
    })
  }

  return {
    prefersReducedMotion
  }
}

export function useInView(options?: {
  threshold?: number
  rootMargin?: string
}) {
  const elementRef = ref<HTMLElement | null>(null)
  const isInView = ref(false)

  onMounted(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        isInView.value = entry.isIntersecting
      },
      {
        threshold: options?.threshold || 0,
        rootMargin: options?.rootMargin || '0px'
      }
    )

    if (elementRef.value) {
      observer.observe(elementRef.value)
    }

    onUnmounted(() => {
      observer.disconnect()
    })
  })

  return {
    elementRef,
    isInView
  }
}
