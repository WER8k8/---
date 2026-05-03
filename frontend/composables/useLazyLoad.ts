/**
 * Code Splitting and Lazy Loading Utilities
 * 
 * Provides utilities for:
 * - Lazy loading Vue components
 * - Route-based code splitting
 * - Dynamic imports with loading states
 * - Prefetching resources
 */

import { defineAsyncComponent, ref, readonly, onUnmounted } from 'vue'

/**
 * Create a lazy-loaded component with loading and error states
 */
export function createLazyComponent(options: {
  loader: () => Promise<any>
  loadingComponent?: any
  errorComponent?: any
  delay?: number
  timeout?: number
}) {
  return defineAsyncComponent({
    loader: options.loader,
    loadingComponent: options.loadingComponent,
    errorComponent: options.errorComponent,
    delay: options.delay ?? 200,
    timeout: options.timeout ?? 8000
  })
}

/**
 * Lazy load a component from a specific path
 */
export function lazyComponent(path: string, name: string) {
  return createLazyComponent({
    loader: () => import(`~/components/${path}/${name}.vue`)
  })
}

/**
 * Prefetch a module when idle or visible
 */
export function usePrefetch() {
  const prefetch = async (importFn: () => Promise<any>) => {
    if ('requestIdleCallback' in window) {
      // @ts-ignore - requestIdleCallback is not in standard types
      window.requestIdleCallback(async () => {
        await importFn()
      })
    } else {
      setTimeout(async () => {
        await importFn()
      }, 1)
    }
  }

  return {
    prefetch
  }
}

/**
 * Prefetch links on hover or when visible
 */
export function useLinkPrefetch() {
  const prefetchedUrls = new Set<string>()

  const prefetchLink = async (url: string) => {
    if (prefetchedUrls.has(url)) return
    
    try {
      // Use Nuxt's built-in prefetch if available
      if (typeof window !== 'undefined' && 'connection' in navigator) {
        // @ts-ignore - connection API
        const conn = (navigator as any).connection
        // Only prefetch on fast connections
        if (conn?.effectiveType === '4g' || conn?.effectiveType === 'wifi') {
          const link = document.createElement('link')
          link.rel = 'prefetch'
          link.href = url
          document.head.appendChild(link)
          prefetchedUrls.add(url)
        }
      }
    } catch (error) {
      console.warn('Prefetch failed:', error)
    }
  }

  return {
    prefetchLink
  }
}

/**
 * Load script dynamically
 */
export function useScriptLoader() {
  const loadScript = (src: string, options?: {
    async?: boolean
    defer?: boolean
    crossorigin?: string
    integrity?: string
  }): Promise<void> => {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = src
      
      if (options?.async) script.async = true
      if (options?.defer) script.defer = true
      if (options?.crossorigin) script.crossOrigin = options.crossorigin
      if (options?.integrity) script.integrity = options.integrity
      
      script.onload = () => resolve()
      script.onerror = () => reject(new Error(`Failed to load script: ${src}`))
      
      document.head.appendChild(script)
    })
  }

  return {
    loadScript
  }
}

/**
 * Load CSS dynamically
 */
export function useStyleLoader() {
  const loadStyle = (href: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      const link = document.createElement('link')
      link.rel = 'stylesheet'
      link.href = href
      
      link.onload = () => resolve()
      link.onerror = () => reject(new Error(`Failed to load style: ${href}`))
      
      document.head.appendChild(link)
    })
  }

  return {
    loadStyle
  }
}

/**
 * Cache API responses for better performance
 */
export function useApiCache(ttl: number = 5 * 60 * 1000) {
  interface CacheEntry {
    data: any
    timestamp: number
  }

  const cache = new Map<string, CacheEntry>()

  const get = <T>(key: string): T | null => {
    const entry = cache.get(key)
    if (!entry) return null
    
    const now = Date.now()
    if (now - entry.timestamp > ttl) {
      cache.delete(key)
      return null
    }
    
    return entry.data as T
  }

  const set = (key: string, data: any) => {
    cache.set(key, {
      data,
      timestamp: Date.now()
    })
  }

  const clear = () => {
    cache.clear()
  }

  const remove = (key: string) => {
    cache.delete(key)
  }

  return {
    get,
    set,
    clear,
    remove
  }
}

/**
 * Debounce input for search/filter operations
 */
export function useDebouncedRef<T>(initialValue: T, delay: number = 300) {
  const value = ref<T>(initialValue)
  let timeout: ReturnType<typeof setTimeout> | null = null

  const setValue = (newValue: T) => {
    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(() => {
      value.value = newValue
    }, delay)
  }

  onUnmounted(() => {
    if (timeout) {
      clearTimeout(timeout)
    }
  })

  return {
    value: readonly(value),
    setValue
  }
}
