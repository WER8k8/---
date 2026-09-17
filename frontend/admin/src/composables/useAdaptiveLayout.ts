/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * AI 自适应布局引擎 — 三维自适应（角色 × 屏幕 × 场景）+ 左出 AI 副驾
 *
 * 维度一：屏幕自适应 — 断点检测 + 设备类型 + 布局模式（单例响应式）
 * 维度二：角色自适应 — 根据用户行为模式调整 UI 复杂度与字号缩放（全局单例同步）
 * 维度三：场景自适应 — 展会/办公/移动端等不同场景的功能优先级
 * 维度四：AI Copilot 停靠自适应 — 默认左出、自由停靠与持久化
 */
import { ref, computed, watch, onMounted, onUnmounted, getCurrentInstance } from 'vue'

// ============ 维度一：屏幕自适应（全局单例共享） ============

export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
export type DeviceType = 'phone' | 'tablet' | 'laptop' | 'desktop' | 'large-desktop'
export type Orientation = 'portrait' | 'landscape'

export interface ScreenInfo {
  width: number
  height: number
  breakpoint: Breakpoint
  device: DeviceType
  orientation: Orientation
  dpr: number
  touch: boolean
  reducedMotion: boolean
  highContrast: boolean
}

const BREAKPOINTS: Record<Breakpoint, number> = {
  xs: 0, sm: 480, md: 768, lg: 1024, xl: 1280, '2xl': 1536,
}

function getBreakpoint(width: number): Breakpoint {
  if (width >= 1536) return '2xl'
  if (width >= 1280) return 'xl'
  if (width >= 1024) return 'lg'
  if (width >= 768) return 'md'
  if (width >= 480) return 'sm'
  return 'xs'
}

function getDevice(bp: Breakpoint): DeviceType {
  const map: Record<Breakpoint, DeviceType> = {
    xs: 'phone', sm: 'phone', md: 'tablet', lg: 'laptop', xl: 'desktop', '2xl': 'large-desktop',
  }
  return map[bp]
}

// 模块级单例状态，确保全站所有组件感知完全同一套屏幕与自适应数据
const sharedWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)
const sharedHeight = ref(typeof window !== 'undefined' ? window.innerHeight : 768)
const sharedDpr = ref(typeof window !== 'undefined' ? window.devicePixelRatio : 1)
const sharedTouch = ref(typeof window !== 'undefined' ? 'ontouchstart' in window : false)
const sharedReducedMotion = ref(false)
const sharedHighContrast = ref(false)
let screenListenersSetup = false

function onGlobalResize() {
  if (typeof window === 'undefined') return
  sharedWidth.value = window.innerWidth
  sharedHeight.value = window.innerHeight
  sharedDpr.value = window.devicePixelRatio || 1
}

function onGlobalMediaQuery(e: MediaQueryListEvent) {
  if (e.matches) {
    if (e.media.includes('prefers-reduced-motion')) sharedReducedMotion.value = true
    if (e.media.includes('prefers-contrast')) sharedHighContrast.value = true
  }
}

function ensureScreenListeners() {
  if (screenListenersSetup || typeof window === 'undefined') return
  screenListenersSetup = true
  window.addEventListener('resize', onGlobalResize)
  if (window.matchMedia) {
    const mqMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
    const mqContrast = window.matchMedia('(prefers-contrast: more)')
    sharedReducedMotion.value = mqMotion.matches
    sharedHighContrast.value = mqContrast.matches
    mqMotion.addEventListener?.('change', onGlobalMediaQuery)
    mqContrast.addEventListener?.('change', onGlobalMediaQuery)
  }
}

if (typeof window !== 'undefined') {
  ensureScreenListeners()
}

export function useAdaptiveScreen() {
  ensureScreenListeners()
  if (typeof window !== 'undefined' && (sharedWidth.value !== window.innerWidth || sharedHeight.value !== window.innerHeight)) {
    onGlobalResize()
  }

  const breakpoint = computed(() => getBreakpoint(sharedWidth.value))
  const device = computed(() => getDevice(breakpoint.value))
  const orientation = computed<Orientation>(() =>
    sharedWidth.value > sharedHeight.value ? 'landscape' : 'portrait',
  )

  const isMobile = computed(() => sharedWidth.value < 768)
  const isTablet = computed(() => sharedWidth.value >= 768 && sharedWidth.value < 1024)
  const isDesktop = computed(() => sharedWidth.value >= 1024)
  const isLargeScreen = computed(() => sharedWidth.value >= 1536)
  const isCompact = computed(() => sharedWidth.value < 480)

  const screenInfo = computed<ScreenInfo>(() => ({
    width: sharedWidth.value,
    height: sharedHeight.value,
    breakpoint: breakpoint.value,
    device: device.value,
    orientation: orientation.value,
    dpr: sharedDpr.value,
    touch: sharedTouch.value,
    reducedMotion: sharedReducedMotion.value,
    highContrast: sharedHighContrast.value,
  }))

  return {
    width: sharedWidth,
    height: sharedHeight,
    breakpoint,
    device,
    orientation,
    dpr: sharedDpr,
    touch: sharedTouch,
    isMobile,
    isTablet,
    isDesktop,
    isLargeScreen,
    isCompact,
    screenInfo,
  }
}

// ============ 维度二：角色自适应与流体字号 ============

export type PersonaComplexity = 'minimal' | 'simple' | 'standard' | 'advanced' | 'expert'

export interface PersonaProfile {
  id: string
  complexity: PersonaComplexity
  showGuidance: boolean
  showAdvanced: boolean
  showAnalytics: boolean
  fontSizeScale: number
  iconSize: 'sm' | 'md' | 'lg'
  density: 'comfortable' | 'default' | 'compact'
  animationLevel: 'none' | 'reduced' | 'normal' | 'rich'
}

export const PERSONA_PRESETS: Record<string, PersonaProfile> = {
  beginner: {
    id: 'beginner', complexity: 'minimal',
    showGuidance: true, showAdvanced: false, showAnalytics: false,
    fontSizeScale: 1.15, iconSize: 'lg', density: 'comfortable',
    animationLevel: 'normal',
  },
  casual: {
    id: 'casual', complexity: 'simple',
    showGuidance: true, showAdvanced: false, showAnalytics: false,
    fontSizeScale: 1.05, iconSize: 'md', density: 'comfortable',
    animationLevel: 'normal',
  },
  standard: {
    id: 'standard', complexity: 'standard',
    showGuidance: false, showAdvanced: false, showAnalytics: true,
    fontSizeScale: 1.0, iconSize: 'md', density: 'default',
    animationLevel: 'normal',
  },
  power: {
    id: 'power', complexity: 'advanced',
    showGuidance: false, showAdvanced: true, showAnalytics: true,
    fontSizeScale: 0.95, iconSize: 'md', density: 'compact',
    animationLevel: 'reduced',
  },
  expert: {
    id: 'expert', complexity: 'expert',
    showGuidance: false, showAdvanced: true, showAnalytics: true,
    fontSizeScale: 0.9, iconSize: 'sm', density: 'compact',
    animationLevel: 'none',
  },
  accessibility: {
    id: 'accessibility', complexity: 'simple',
    showGuidance: true, showAdvanced: false, showAnalytics: false,
    fontSizeScale: 1.35, iconSize: 'lg', density: 'comfortable',
    animationLevel: 'reduced',
  },
}

export type PersonaId = keyof typeof PERSONA_PRESETS

const PERSONA_STORAGE_KEY = 'adaptive_persona'
const FONT_SCALE_STORAGE_KEY = 'adaptive_font_scale'

// 模块级单例状态：角色与自定义字号缩放
const sharedPersonaId = ref<PersonaId>(
  (typeof localStorage !== 'undefined'
    ? (localStorage.getItem(PERSONA_STORAGE_KEY) as PersonaId)
    : null) || 'standard',
)

function getInitialFontScale(): number {
  if (typeof localStorage !== 'undefined') {
    const raw = localStorage.getItem(FONT_SCALE_STORAGE_KEY)
    if (raw) {
      const parsed = parseFloat(raw)
      if (!isNaN(parsed) && parsed >= 0.75 && parsed <= 1.5) {
        return parsed
      }
    }
  }
  return PERSONA_PRESETS[sharedPersonaId.value]?.fontSizeScale || 1.0
}

const sharedUserFontScale = ref<number>(getInitialFontScale())

export function useAdaptivePersona() {
  const profile = computed(() => PERSONA_PRESETS[sharedPersonaId.value] || PERSONA_PRESETS.standard)

  function setPersona(id: PersonaId) {
    sharedPersonaId.value = id
    const presetScale = PERSONA_PRESETS[id]?.fontSizeScale || 1.0
    sharedUserFontScale.value = presetScale
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(PERSONA_STORAGE_KEY, id)
      localStorage.setItem(FONT_SCALE_STORAGE_KEY, String(presetScale))
    }
  }

  function setFontScale(scale: number) {
    const clamped = Math.max(0.75, Math.min(1.5, Math.round(scale * 100) / 100))
    sharedUserFontScale.value = clamped
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(FONT_SCALE_STORAGE_KEY, String(clamped))
    }
  }

  function adjustFontScale(delta: number) {
    setFontScale(sharedUserFontScale.value + delta)
  }

  function autoDetectPersona(): PersonaId {
    if (typeof window === 'undefined') return 'standard'
    const w = window.innerWidth
    if (w < 480) return 'beginner'
    if (w < 768) return 'casual'
    return 'standard'
  }

  const fontSizeScale = computed(() => sharedUserFontScale.value)
  const baseFontSize = computed(() => `${Math.round(15 * fontSizeScale.value)}px`)

  return {
    personaId: sharedPersonaId,
    profile,
    setPersona,
    setFontScale,
    adjustFontScale,
    autoDetectPersona,
    fontSizeScale,
    userFontScale: sharedUserFontScale,
    baseFontSize,
    presets: PERSONA_PRESETS,
  }
}

// ============ 浏览器 Zoom 检测 ============

export function useBrowserZoom() {
  const zoom = ref(typeof window !== 'undefined' ? window.devicePixelRatio : 1)

  function detectZoom() {
    zoom.value = window.devicePixelRatio || 1
  }

  if (typeof window !== 'undefined') {
    if (getCurrentInstance()) {
      onMounted(() => {
        detectZoom()
        window.addEventListener('resize', detectZoom)
        window.addEventListener('DOMContentLoaded', detectZoom)
      })
      onUnmounted(() => {
        window.removeEventListener('resize', detectZoom)
        window.removeEventListener('DOMContentLoaded', detectZoom)
      })
    } else {
      detectZoom()
      window.addEventListener('resize', detectZoom)
    }
  }

  const isZoomed = computed(() => zoom.value > 1.1 || zoom.value < 0.9)

  return { zoom, isZoomed }
}

// ============ 维度三：场景自适应 ============

export type ScenarioMode = 'office' | 'exhibition' | 'mobile-field' | 'presentation' | 'focus'

export interface ScenarioConfig {
  mode: ScenarioMode
  sidebarVisible: boolean
  headerCompact: boolean
  featurePriority: string[]
  dataDensity: 'low' | 'medium' | 'high'
  autoRefresh: boolean
  notificationLevel: 'all' | 'important' | 'silent'
}

export const SCENARIO_PRESETS: Record<ScenarioMode, ScenarioConfig> = {
  office: {
    mode: 'office', sidebarVisible: true, headerCompact: false,
    featurePriority: ['dashboard', 'inquiries', 'products', 'publish', 'copilot'],
    dataDensity: 'high', autoRefresh: true, notificationLevel: 'all',
  },
  exhibition: {
    mode: 'exhibition', sidebarVisible: false, headerCompact: true,
    featurePriority: ['products', 'quote', 'contact'],
    dataDensity: 'low', autoRefresh: false, notificationLevel: 'silent',
  },
  'mobile-field': {
    mode: 'mobile-field', sidebarVisible: false, headerCompact: true,
    featurePriority: ['inquiries', 'copilot', 'products'],
    dataDensity: 'low', autoRefresh: true, notificationLevel: 'important',
  },
  presentation: {
    mode: 'presentation', sidebarVisible: false, headerCompact: true,
    featurePriority: ['dashboard', 'analytics'],
    dataDensity: 'low', autoRefresh: false, notificationLevel: 'silent',
  },
  focus: {
    mode: 'focus', sidebarVisible: false, headerCompact: true,
    featurePriority: ['copilot'],
    dataDensity: 'medium', autoRefresh: false, notificationLevel: 'silent',
  },
}

const SCENARIO_STORAGE_KEY = 'adaptive_scenario'

const sharedScenarioMode = ref<ScenarioMode>(
  (typeof localStorage !== 'undefined'
    ? (localStorage.getItem(SCENARIO_STORAGE_KEY) as ScenarioMode)
    : null) || 'office',
)

export function useAdaptiveScenario() {
  const config = computed(() => SCENARIO_PRESETS[sharedScenarioMode.value] || SCENARIO_PRESETS.office)

  function setScenario(m: ScenarioMode) {
    sharedScenarioMode.value = m
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(SCENARIO_STORAGE_KEY, m)
    }
  }

  function autoDetectScenario(): ScenarioMode {
    if (typeof window === 'undefined') return 'office'
    if (window.innerWidth < 768) return 'mobile-field'
    return 'office'
  }

  return {
    mode: sharedScenarioMode,
    config,
    setScenario,
    autoDetectScenario,
    presets: SCENARIO_PRESETS,
  }
}

// ============ 组合：三维自适应 ============

const DENSITY_CLASSES = ['adaptive-density-comfortable', 'adaptive-density-compact']
const SCENARIO_CLASSES = ['adaptive-scenario-exhibition', 'adaptive-scenario-focus', 'adaptive-scenario-presentation']

function applyScaleToRoot(scale: number) {
  if (typeof document !== 'undefined') {
    document.documentElement.style.setProperty('--uj-adaptive-scale', String(scale))
  }
}

function applyDensityClass(density: string) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  DENSITY_CLASSES.forEach(c => root.classList.remove(c))
  if (density === 'comfortable') root.classList.add('adaptive-density-comfortable')
  else if (density === 'compact') root.classList.add('adaptive-density-compact')
}

function applyScenarioClass(mode: string) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  SCENARIO_CLASSES.forEach(c => root.classList.remove(c))
  if (mode !== 'office' && mode !== 'mobile-field') {
    root.classList.add(`adaptive-scenario-${mode}`)
  }
}

export function screenWidthScale(width: number): number {
  if (width < 480) return 0.88
  if (width < 768) return 0.92
  if (width < 1024) return 0.96
  if (width < 1280) return 1.00
  if (width < 1536) return 1.05
  return 1.10
}

// ============ 维度四：AI Copilot 停靠自适应（左出自适应） ============

export type CopilotDockPosition = 'left' | 'right'

const COPILOT_DOCK_STORAGE_KEY = 'adaptive_copilot_dock'

const sharedCopilotDock = ref<CopilotDockPosition>(
  (typeof localStorage !== 'undefined'
    ? (localStorage.getItem(COPILOT_DOCK_STORAGE_KEY) as CopilotDockPosition)
    : null) || 'left', // 默认左出 AI 自适应
)

export function useAdaptiveCopilotDock() {
  function setDock(position: CopilotDockPosition) {
    sharedCopilotDock.value = position
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(COPILOT_DOCK_STORAGE_KEY, position)
    }
  }

  function toggleDock() {
    setDock(sharedCopilotDock.value === 'left' ? 'right' : 'left')
  }

  return {
    dock: sharedCopilotDock,
    setDock,
    toggleDock,
  }
}

export function useAdaptiveLayout() {
  const screen = useAdaptiveScreen()
  const persona = useAdaptivePersona()
  const scenario = useAdaptiveScenario()
  const copilot = useAdaptiveCopilotDock()

  watch(screen.isMobile, (mobile) => {
    if (mobile && scenario.mode.value === 'office') {
      scenario.setScenario('mobile-field')
    } else if (!mobile && scenario.mode.value === 'mobile-field') {
      scenario.setScenario('office')
    }
  })

  const layoutMode = computed(() => {
    if (screen.isLargeScreen.value) return 'wide'
    if (screen.isDesktop.value) return 'desktop'
    if (screen.isTablet.value) return 'tablet'
    if (screen.isCompact.value) return 'compact'
    return 'mobile'
  })

  const effectiveDensity = computed<'comfortable' | 'default' | 'compact'>(() => {
    if (screen.isCompact.value) return 'compact'
    if (persona.profile.value.density !== 'default') return persona.profile.value.density
    if (screen.isMobile.value) return 'compact'
    if (screen.isLargeScreen.value) return 'comfortable'
    return 'default'
  })

  const showSidebar = computed(() => {
    if (screen.isMobile.value) return false
    return scenario.config.value.sidebarVisible
  })

  const sidebarMode = computed<'expanded' | 'collapsed' | 'hidden'>(() => {
    if (screen.isMobile.value) return 'hidden'
    if (screen.isTablet.value) return 'collapsed'
    return 'expanded'
  })

  const combinedScale = computed(() => {
    const personaScale = persona.fontSizeScale.value
    const screenScale = screenWidthScale(screen.width.value)
    const combined = personaScale * screenScale
    return Math.max(0.75, Math.min(1.5, Math.round(combined * 100) / 100))
  })

  watch(combinedScale, (scale) => {
    applyScaleToRoot(scale)
  }, { immediate: true })

  watch(effectiveDensity, (d) => {
    applyDensityClass(d === 'comfortable' ? 'comfortable' : d === 'compact' ? 'compact' : '')
  }, { immediate: true })

  watch(scenario.mode, (m) => {
    applyScenarioClass(m)
  }, { immediate: true })

  const cssVars = computed(() => ({
    '--uj-adaptive-scale': combinedScale.value,
    '--uj-adaptive-layout': layoutMode.value,
    '--uj-adaptive-scenario': scenario.mode.value,
  }))

  const tableColumns = computed(() => {
    if (screen.isCompact.value) return 1
    if (screen.isMobile.value) return 2
    if (screen.isTablet.value) return 3
    return 4
  })

  const cardColumns = computed(() => {
    if (screen.isCompact.value) return 1
    if (screen.isMobile.value) return 1
    if (screen.isTablet.value) return 2
    if (screen.isLargeScreen.value) return 4
    return 3
  })

  return {
    screen,
    persona,
    scenario,
    copilot,
    layoutMode,
    effectiveDensity,
    showSidebar,
    sidebarMode,
    combinedScale,
    cssVars,
    tableColumns,
    cardColumns,
  }
}

/**
 * 重置全局自适应单例状态（供自动化测试隔离使用）
 */
export function resetAdaptiveState() {
  sharedPersonaId.value = 'standard'
  sharedUserFontScale.value = PERSONA_PRESETS.standard.fontSizeScale
  sharedScenarioMode.value = 'office'
  sharedCopilotDock.value = 'left'
  if (typeof window !== 'undefined') {
    sharedWidth.value = window.innerWidth || 1024
    sharedHeight.value = window.innerHeight || 768
    sharedDpr.value = window.devicePixelRatio || 1
  }
}
