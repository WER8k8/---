/**
 * Responsive Design Utilities
 * Enhanced mobile-first responsive design helpers
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'

export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'

export interface BreakpointConfig {
  xs: number   // 0-639px (mobile)
  sm: number   // 640-767px (small tablet)
  md: number   // 768-1023px (tablet)
  lg: number   // 1024-1279px (desktop)
  xl: number   // 1280-1535px (large desktop)
  '2xl': number // 1536px+ (extra large desktop)
}

// Default breakpoint configuration (matches Tailwind CSS)
const defaultBreakpoints: BreakpointConfig = {
  xs: 0,
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536
}

/**
 * Composable for responsive design utilities
 */
export function useResponsive() {
  // Get current window width
  const getWindowWidth = () => {
    if (process.client) {
      return window.innerWidth
    }
    return defaultBreakpoints.lg // Default to desktop on server
  }

  // Current window width reactive ref
  const windowWidth = ref(getWindowWidth())

  // Update window width on resize
  if (process.client) {
    let resizeTimer: ReturnType<typeof setTimeout>
    const handleResize = () => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(() => {
        windowWidth.value = getWindowWidth()
      }, 100) // Debounce resize events
    }

    onMounted(() => {
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
    })
  }

  // Check if current viewport matches a breakpoint
  const isBreakpoint = (breakpoint: Breakpoint): boolean => {
    return windowWidth.value >= defaultBreakpoints[breakpoint]
  }

  // Computed properties for each breakpoint
  const isMobile = computed(() => !isBreakpoint('md')) // < 768px
  const isTablet = computed(() => isBreakpoint('md') && !isBreakpoint('lg')) // 768-1023px
  const isDesktop = computed(() => isBreakpoint('lg')) // >= 1024px
  const isLargeDesktop = computed(() => isBreakpoint('xl')) // >= 1280px

  // Get current active breakpoint
  const currentBreakpoint = computed<Breakpoint>(() => {
    if (windowWidth.value >= defaultBreakpoints['2xl']) return '2xl'
    if (windowWidth.value >= defaultBreakpoints.xl) return 'xl'
    if (windowWidth.value >= defaultBreakpoints.lg) return 'lg'
    if (windowWidth.value >= defaultBreakpoints.md) return 'md'
    if (windowWidth.value >= defaultBreakpoints.sm) return 'sm'
    return 'xs'
  })

  // Generate responsive class names
  const responsiveClass = (baseClass: string, options?: {
    sm?: string
    md?: string
    lg?: string
    xl?: string
    '2xl'?: string
  }): string => {
    if (!options) return baseClass
    
    const classes = [baseClass]
    if (options.sm) classes.push(`sm:${options.sm}`)
    if (options.md) classes.push(`md:${options.md}`)
    if (options.lg) classes.push(`lg:${options.lg}`)
    if (options.xl) classes.push(`xl:${options.xl}`)
    if (options['2xl']) classes.push(`2xl:${options['2xl']}`)
    
    return classes.join(' ')
  }

  // Touch device detection
  const isTouchDevice = computed(() => {
    if (process.client) {
      return 'ontouchstart' in window || navigator.maxTouchPoints > 0
    }
    return false
  })

  // Get grid columns based on breakpoint
  const getGridColumns = (cols: {
    xs?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
  }): string => {
    const { xs = 1, sm = 2, md = 3, lg = 4, xl = 4 } = cols
    
    return `grid-cols-${xs} sm:grid-cols-${sm} md:grid-cols-${md} lg:grid-cols-${lg} xl:grid-cols-${xl}`
  }

  // Get spacing based on breakpoint
  const getResponsiveSpacing = (sizes: {
    xs: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
  }): string => {
    const { xs, sm = xs, md = sm, lg = md, xl = lg } = sizes
    
    const classes = [`p-${xs}`]
    if (sm !== xs) classes.push(`sm:p-${sm}`)
    if (md !== sm) classes.push(`md:p-${md}`)
    if (lg !== md) classes.push(`lg:p-${lg}`)
    if (xl !== lg) classes.push(`xl:p-${xl}`)
    
    return classes.join(' ')
  }

  return {
    windowWidth,
    currentBreakpoint,
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,
    isBreakpoint,
    responsiveClass,
    isTouchDevice,
    getGridColumns,
    getResponsiveSpacing,
    breakpoints: defaultBreakpoints
  }
}

/**
 * Helper to create touch-friendly UI elements
 */
export function useTouchFriendly() {
  const { isTouchDevice } = useResponsive()

  // Minimum touch target size (44x44px per WCAG guidelines)
  const minTouchTarget = 'min-w-[44px] min-h-[44px]'

  // Touch-friendly padding
  const touchPadding = 'px-4 py-3'

  // Touch-friendly button styles
  const touchButtonStyles = computed(() => {
    const base = 'rounded-lg font-medium transition-all'
    const touch = isTouchDevice.value ? `${minTouchTarget} ${touchPadding}` : ''
    return `${base} ${touch}`
  })

  return {
    isTouchDevice,
    minTouchTarget,
    touchPadding,
    touchButtonStyles
  }
}

/**
 * Helper for responsive images
 */
export function useResponsiveImage(options: {
  src: string
  alt: string
  widths?: number[]
  sizes?: string
}) {
  const { src, alt, widths = [320, 640, 768, 1024, 1280], sizes = '(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw' } = options

  // Generate srcset
  const srcset = computed(() => {
    return widths.map(width => {
      // For external images, just append query params
      // For local images, you might want to use Nuxt Image module
      return `${src}?w=${width} ${width}w`
    }).join(', ')
  })

  return {
    src,
    alt,
    srcset: srcset.value,
    sizes,
    loading: 'lazy' as const,
    decoding: 'async' as const
  }
}
