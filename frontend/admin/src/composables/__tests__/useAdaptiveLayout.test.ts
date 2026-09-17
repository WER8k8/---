/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * AI 自适应布局引擎测试
 *
 * 覆盖：
 * - 屏幕断点检测与连续比例尺
 * - 角色 persona 预设切换
 * - 用户细粒度字号微调（A+ / A- 响应与边界截断）
 * - 多组件实例全局状态单例同步
 * - 场景模式切换与联动
 * - 三维组合联动与 CSS 变量注入
 * - AI Copilot 默认左出、自由停靠与持久化
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  useAdaptiveScreen,
  useAdaptivePersona,
  useAdaptiveScenario,
  useAdaptiveLayout,
  useAdaptiveCopilotDock,
  resetAdaptiveState,
} from '../useAdaptiveLayout'
import type { Breakpoint, DeviceType } from '../useAdaptiveLayout'

function setWindowSize(width: number, height = 768) {
  Object.defineProperty(window, 'innerWidth', { value: width, writable: true })
  Object.defineProperty(window, 'innerHeight', { value: height, writable: true })
  window.dispatchEvent(new Event('resize'))
}

describe('useAdaptiveScreen', () => {
  beforeEach(() => {
    resetAdaptiveState()
    setWindowSize(1280)
  })

  it('detects xs breakpoint for width < 480', () => {
    setWindowSize(375)
    const screen = useAdaptiveScreen()
    expect(screen.breakpoint.value).toBe('xs')
    expect(screen.device.value).toBe('phone')
    expect(screen.isMobile.value).toBe(true)
    expect(screen.isCompact.value).toBe(true)
  })

  it('detects sm breakpoint for 480 <= width < 768', () => {
    setWindowSize(640)
    const screen = useAdaptiveScreen()
    expect(screen.breakpoint.value).toBe('sm')
    expect(screen.device.value).toBe('phone')
    expect(screen.isMobile.value).toBe(true)
    expect(screen.isCompact.value).toBe(false)
  })

  it('detects md breakpoint for 768 <= width < 1024', () => {
    setWindowSize(800)
    const screen = useAdaptiveScreen()
    expect(screen.breakpoint.value).toBe('md')
    expect(screen.device.value).toBe('tablet')
    expect(screen.isTablet.value).toBe(true)
    expect(screen.isDesktop.value).toBe(false)
  })

  it('detects lg breakpoint for 1024 <= width < 1280', () => {
    setWindowSize(1100)
    const screen = useAdaptiveScreen()
    expect(screen.breakpoint.value).toBe('lg')
    expect(screen.device.value).toBe('laptop')
    expect(screen.isDesktop.value).toBe(true)
  })

  it('detects xl breakpoint for 1280 <= width < 1536', () => {
    setWindowSize(1300)
    const screen = useAdaptiveScreen()
    expect(screen.breakpoint.value).toBe('xl')
    expect(screen.device.value).toBe('desktop')
  })

  it('detects 2xl breakpoint for width >= 1536', () => {
    setWindowSize(1600)
    const screen = useAdaptiveScreen()
    expect(screen.breakpoint.value).toBe('2xl')
    expect(screen.device.value).toBe('large-desktop')
    expect(screen.isLargeScreen.value).toBe(true)
  })

  it('handles window resize events reactively', () => {
    const screen = useAdaptiveScreen()
    setWindowSize(1280)
    expect(screen.isDesktop.value).toBe(true)

    setWindowSize(375)
    expect(screen.isMobile.value).toBe(true)
    expect(screen.breakpoint.value).toBe('xs')
  })

  it('calculates orientation correctly', () => {
    const screen = useAdaptiveScreen()
    setWindowSize(1280, 800)
    expect(screen.orientation.value).toBe('landscape')

    setWindowSize(768, 1024)
    expect(screen.orientation.value).toBe('portrait')
  })
})

describe('useAdaptivePersona', () => {
  beforeEach(() => {
    localStorage.clear()
    resetAdaptiveState()
  })

  it('defaults to standard persona', () => {
    const persona = useAdaptivePersona()
    expect(persona.personaId.value).toBe('standard')
    expect(persona.profile.value.complexity).toBe('standard')
    expect(persona.profile.value.showGuidance).toBe(false)
  })

  it('switches persona and persists to localStorage', () => {
    const persona = useAdaptivePersona()
    persona.setPersona('power')
    expect(persona.personaId.value).toBe('power')
    expect(persona.profile.value.density).toBe('compact')
    expect(localStorage.getItem('adaptive_persona')).toBe('power')
  })

  it('accessibility persona has large font scale', () => {
    const persona = useAdaptivePersona()
    persona.setPersona('accessibility')
    expect(persona.fontSizeScale.value).toBe(1.35)
    expect(persona.profile.value.iconSize).toBe('lg')
  })

  it('expert persona has compact density and no animation', () => {
    const persona = useAdaptivePersona()
    persona.setPersona('expert')
    expect(persona.profile.value.density).toBe('compact')
    expect(persona.profile.value.animationLevel).toBe('none')
    expect(persona.profile.value.showAdvanced).toBe(true)
  })

  it('autoDetectPersona returns beginner for small screens', () => {
    setWindowSize(375)
    const persona = useAdaptivePersona()
    expect(persona.autoDetectPersona()).toBe('beginner')
  })

  it('autoDetectPersona returns standard for desktop', () => {
    setWindowSize(1280)
    const persona = useAdaptivePersona()
    expect(persona.autoDetectPersona()).toBe('standard')
  })

  it('supports fine-grained font scaling (A+ / A-)', () => {
    const persona = useAdaptivePersona()
    persona.setPersona('standard')
    expect(persona.fontSizeScale.value).toBe(1.0)

    // A+ 放大 0.1
    persona.adjustFontScale(0.1)
    expect(persona.fontSizeScale.value).toBe(1.1)

    // A- 缩小 0.1
    persona.adjustFontScale(-0.1)
    expect(persona.fontSizeScale.value).toBe(1.0)

    // 边界下限截断 0.75
    persona.setFontScale(0.5)
    expect(persona.fontSizeScale.value).toBe(0.75)

    // 边界上限截断 1.50
    persona.setFontScale(2.0)
    expect(persona.fontSizeScale.value).toBe(1.50)
  })

  it('shares state across multiple composable instances (单例全局同步)', () => {
    const p1 = useAdaptivePersona()
    const p2 = useAdaptivePersona()

    p1.setPersona('power')
    expect(p2.personaId.value).toBe('power')
    expect(p2.fontSizeScale.value).toBe(0.95)

    p2.adjustFontScale(0.1)
    expect(p1.fontSizeScale.value).toBe(1.05)
  })
})

describe('useAdaptiveLayout (combined)', () => {
  beforeEach(() => {
    localStorage.clear()
    resetAdaptiveState()
    setWindowSize(1280)
  })

  it('returns sidebarMode=expanded on desktop', () => {
    setWindowSize(1280)
    const layout = useAdaptiveLayout()
    expect(layout.sidebarMode.value).toBe('expanded')
    expect(layout.showSidebar.value).toBe(true)
  })

  it('returns sidebarMode=hidden on mobile', () => {
    setWindowSize(375)
    const layout = useAdaptiveLayout()
    expect(layout.sidebarMode.value).toBe('hidden')
    expect(layout.showSidebar.value).toBe(false)
  })

  it('returns sidebarMode=collapsed on tablet', () => {
    setWindowSize(810)
    const layout = useAdaptiveLayout()
    expect(layout.sidebarMode.value).toBe('collapsed')
  })

  it('compact screen forces compact density', () => {
    setWindowSize(375)
    const layout = useAdaptiveLayout()
    expect(layout.effectiveDensity.value).toBe('compact')
  })

  it('large screen defaults to comfortable density', () => {
    setWindowSize(1920)
    const layout = useAdaptiveLayout()
    expect(layout.effectiveDensity.value).toBe('comfortable')
  })

  it('combinedScale respects persona fontSizeScale', () => {
    const layout = useAdaptiveLayout()
    layout.persona.setPersona('accessibility')
    expect(layout.combinedScale.value).toBeGreaterThan(1.0)
  })

  it('combinedScale reduces on small screens', () => {
    setWindowSize(375)
    const layout = useAdaptiveLayout()
    expect(layout.combinedScale.value).toBeLessThan(1.0)
  })

  it('tableColumns adapts to screen width', () => {
    setWindowSize(375)
    const layout = useAdaptiveLayout()
    expect(layout.tableColumns.value).toBe(1)

    setWindowSize(1280)
    expect(layout.tableColumns.value).toBe(4)
  })

  it('cardColumns adapts to screen width', () => {
    setWindowSize(375)
    const layout = useAdaptiveLayout()
    expect(layout.cardColumns.value).toBe(1)

    setWindowSize(1920)
    expect(layout.cardColumns.value).toBe(4)
  })

  it('cssVars contains expected properties', () => {
    const layout = useAdaptiveLayout()
    const vars = layout.cssVars.value
    expect(vars).toHaveProperty('--uj-adaptive-scale')
    expect(vars).toHaveProperty('--uj-adaptive-layout')
    expect(vars).toHaveProperty('--uj-adaptive-scenario')
  })

  it('combinedScale scales dynamically across all screen breakpoints', () => {
    const layout = useAdaptiveLayout()
    layout.persona.setPersona('standard')
    
    // xs screen (<480) -> scale 0.88
    setWindowSize(360)
    expect(layout.combinedScale.value).toBeCloseTo(0.88, 2)

    // sm screen (480-768) -> scale 0.92
    setWindowSize(600)
    expect(layout.combinedScale.value).toBeCloseTo(0.92, 2)

    // md screen (768-1024) -> scale 0.96
    setWindowSize(800)
    expect(layout.combinedScale.value).toBeCloseTo(0.96, 2)

    // lg screen (1024-1280) -> scale 1.00
    setWindowSize(1100)
    expect(layout.combinedScale.value).toBeCloseTo(1.00, 2)

    // xl screen (1280-1536) -> scale 1.05
    setWindowSize(1400)
    expect(layout.combinedScale.value).toBeCloseTo(1.05, 2)

    // 2xl screen (>=1536) -> scale 1.10
    setWindowSize(1920)
    expect(layout.combinedScale.value).toBeCloseTo(1.10, 2)
  })

  it('synchronizes combinedScale when separate persona instance updates', () => {
    const layout = useAdaptiveLayout()
    const separatePersona = useAdaptivePersona()

    setWindowSize(1100) // 1.00x screen (lg: 1024-1280)
    separatePersona.setPersona('standard')
    expect(layout.combinedScale.value).toBe(1.0)

    separatePersona.adjustFontScale(0.2) // 1.20
    expect(layout.combinedScale.value).toBe(1.2)
  })
})

describe('useAdaptiveCopilotDock (左出 AI 自适应)', () => {
  beforeEach(() => {
    localStorage.clear()
    resetAdaptiveState()
  })

  it('defaults to left dock (左出自适应)', () => {
    const copilot = useAdaptiveCopilotDock()
    expect(copilot.dock.value).toBe('left')
  })

  it('can toggle dock between left and right', () => {
    const copilot = useAdaptiveCopilotDock()
    expect(copilot.dock.value).toBe('left')
    copilot.toggleDock()
    expect(copilot.dock.value).toBe('right')
    copilot.toggleDock()
    expect(copilot.dock.value).toBe('left')
  })

  it('persists dock position to localStorage', () => {
    const copilot = useAdaptiveCopilotDock()
    copilot.setDock('right')
    expect(localStorage.getItem('adaptive_copilot_dock')).toBe('right')
  })

  it('shares dock position across multiple composable instances', () => {
    const c1 = useAdaptiveCopilotDock()
    const c2 = useAdaptiveCopilotDock()

    c1.toggleDock()
    expect(c2.dock.value).toBe('right')
  })
})
