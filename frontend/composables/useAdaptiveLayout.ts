/**
 * 官网(3000) AI 自适应布局 composable
 * 三维：屏幕 × 角色 × 场景
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
export type FontSizeLevel = 'xs' | 'sm' | 'default' | 'lg' | 'xl' | 'xxl'
export type DensityLevel = 'comfortable' | 'default' | 'compact'
export type ScenarioMode = 'default' | 'exhibition' | 'presentation'

const FONT_SCALES: Record<FontSizeLevel, number> = {
  xs: 0.85, sm: 0.92, default: 1, lg: 1.12, xl: 1.25, xxl: 1.4,
}

const FONT_STORAGE_KEY = 'sb_font_size'
const DENSITY_STORAGE_KEY = 'sb_density'
const SCENARIO_STORAGE_KEY = 'sb_scenario'

export function useAdaptiveLayout() {
  const width = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)
  const height = ref(typeof window !== 'undefined' ? window.innerHeight : 768)

  const breakpoint = computed<Breakpoint>(() => {
    const w = width.value
    if (w >= 1536) return '2xl'
    if (w >= 1280) return 'xl'
    if (w >= 1024) return 'lg'
    if (w >= 768) return 'md'
    if (w >= 375) return 'sm'
    return 'xs'
  })

  const isMobile = computed(() => width.value < 768)
  const isTablet = computed(() => width.value >= 768 && width.value < 1024)
  const isDesktop = computed(() => width.value >= 1024)
  const isLargeScreen = computed(() => width.value >= 1536)
  const isCompact = computed(() => width.value < 375)

  // 字体大小
  const fontSizeLevel = ref<FontSizeLevel>(
    (typeof localStorage !== 'undefined'
      ? (localStorage.getItem(FONT_STORAGE_KEY) as FontSizeLevel)
      : null) || 'default',
  )

  function getScreenWidthScale(w: number): number {
    if (w < 375) return 0.88
    if (w < 768) return 0.92
    if (w < 1024) return 0.96
    if (w < 1280) return 1.00
    if (w < 1536) return 1.05
    return 1.10
  }

  const combinedScale = computed(() => {
    const base = FONT_SCALES[fontSizeLevel.value] || 1
    const screenScale = getScreenWidthScale(width.value)
    return Math.round(base * screenScale * 100) / 100
  })

  const fontSizeScale = computed(() => combinedScale.value)

  function setFontSize(level: FontSizeLevel) {
    fontSizeLevel.value = level
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(FONT_STORAGE_KEY, level)
    }
    applyFontClass(level)
  }

  function applyFontClass(level: FontSizeLevel) {
    if (typeof document === 'undefined') return
    const root = document.documentElement
    Object.keys(FONT_SCALES).forEach(l => {
      root.classList.remove(`sb-font-${l}`)
    })
    root.classList.add(`sb-font-${level}`)
    root.style.setProperty('--sb-adaptive-scale', String(combinedScale.value))
  }

  watch(combinedScale, (s) => {
    if (typeof document !== 'undefined') {
      document.documentElement.style.setProperty('--sb-adaptive-scale', String(s))
    }
  })

  // 密度
  const density = ref<DensityLevel>(
    (typeof localStorage !== 'undefined'
      ? (localStorage.getItem(DENSITY_STORAGE_KEY) as DensityLevel)
      : null) || 'default',
  )

  function setDensity(d: DensityLevel) {
    density.value = d
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(DENSITY_STORAGE_KEY, d)
    }
    if (typeof document !== 'undefined') {
      document.documentElement.classList.remove('sb-density-comfortable', 'sb-density-compact')
      if (d !== 'default') {
        document.documentElement.classList.add(`sb-density-${d}`)
      }
    }
  }

  // 场景
  const scenario = ref<ScenarioMode>(
    (typeof localStorage !== 'undefined'
      ? (localStorage.getItem(SCENARIO_STORAGE_KEY) as ScenarioMode)
      : null) || 'default',
  )

  function setScenario(s: ScenarioMode) {
    scenario.value = s
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(SCENARIO_STORAGE_KEY, s)
    }
    if (typeof document !== 'undefined') {
      document.documentElement.classList.remove('sb-scenario-exhibition', 'sb-scenario-presentation')
      if (s !== 'default') {
        document.documentElement.classList.add(`sb-scenario-${s}`)
      }
    }
  }

  // 自动检测
  function autoDetect() {
    if (width.value < 768) {
      if (fontSizeLevel.value === 'default') setFontSize('lg')
    } else {
      if (fontSizeLevel.value === 'lg' || fontSizeLevel.value === 'xl') setFontSize('default')
    }
  }

  // 响应式监听
  function onResize() {
    width.value = window.innerWidth
    height.value = window.innerHeight
  }

  let resizeTimer: ReturnType<typeof setTimeout>
  function onResizeDebounced() {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      onResize()
      autoDetect()
    }, 200)
  }

  onMounted(() => {
    applyFontClass(fontSizeLevel.value)
    if (density.value !== 'default') {
      document.documentElement.classList.add(`sb-density-${density.value}`)
    }
    if (scenario.value !== 'default') {
      document.documentElement.classList.add(`sb-scenario-${scenario.value}`)
    }
    window.addEventListener('resize', onResizeDebounced)
    autoDetect()
  })

  onUnmounted(() => {
    window.removeEventListener('resize', onResizeDebounced)
    clearTimeout(resizeTimer)
  })

  return {
    width, height, breakpoint,
    isMobile, isTablet, isDesktop, isLargeScreen, isCompact,
    fontSizeLevel, fontSizeScale, setFontSize,
    density, setDensity,
    scenario, setScenario,
    fontLevels: Object.keys(FONT_SCALES) as FontSizeLevel[],
  }
}
