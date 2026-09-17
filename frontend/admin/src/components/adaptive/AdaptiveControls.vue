/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 自适应控制面板 — 字体大小 + 角色模式 + 场景模式
 * 放置于 Topbar 右侧工具区
 */
<template>
  <div class="adaptive-controls">
    <!-- 字体大小调整 -->
    <div class="adaptive-group" title="字体大小">
      <button
        class="adaptive-btn"
        :class="{ active: persona.fontSizeScale.value <= 0.9 }"
        @click="persona.adjustFontScale(-0.1)"
        :disabled="persona.fontSizeScale.value <= 0.75"
        aria-label="缩小字体"
      >
        <span class="font-label">A-</span>
      </button>
      <span class="font-indicator">{{ fontLevelLabel }}</span>
      <button
        class="adaptive-btn"
        :class="{ active: persona.fontSizeScale.value >= 1.15 }"
        @click="persona.adjustFontScale(0.1)"
        :disabled="persona.fontSizeScale.value >= 1.5"
        aria-label="放大字体"
      >
        <span class="font-label">A+</span>
      </button>
    </div>

    <!-- 角色模式快捷切换 -->
    <div class="adaptive-group" title="显示模式">
      <button
        v-for="p in quickPersonas"
        :key="p.id"
        class="adaptive-btn persona-btn"
        :class="{ active: persona.personaId.value === p.id }"
        @click="persona.setPersona(p.id)"
        :title="p.label"
      >
        {{ p.icon }}
      </button>
    </div>

    <!-- 场景模式 -->
    <div class="adaptive-group" title="场景模式">
      <button
        v-for="s in quickScenarios"
        :key="s.mode"
        class="adaptive-btn scenario-btn"
        :class="{ active: scenario.mode.value === s.mode }"
        @click="scenario.setScenario(s.mode)"
        :title="s.label"
      >
        {{ s.icon }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAdaptivePersona, useAdaptiveScenario, type PersonaId, type ScenarioMode } from '@/composables/useAdaptiveLayout'

const persona = useAdaptivePersona()
const scenario = useAdaptiveScenario()

const fontLevelLabel = computed(() => {
  const scale = persona.fontSizeScale.value
  if (scale <= 0.85) return '小'
  if (scale <= 0.95) return '较小'
  if (scale <= 1.05) return '标准'
  if (scale <= 1.2) return '大'
  return '超大'
})

const quickPersonas = [
  { id: 'beginner' as PersonaId, label: '新手模式', icon: '🌱' },
  { id: 'standard' as PersonaId, label: '标准模式', icon: '⚡' },
  { id: 'power' as PersonaId, label: '专业模式', icon: '🔧' },
  { id: 'accessibility' as PersonaId, label: '大字/无障碍', icon: '👁' },
]

const quickScenarios = [
  { mode: 'office' as ScenarioMode, label: '办公', icon: '🖥' },
  { mode: 'mobile-field' as ScenarioMode, label: '外出', icon: '📱' },
  { mode: 'exhibition' as ScenarioMode, label: '展会', icon: '🏛' },
  { mode: 'focus' as ScenarioMode, label: '专注', icon: '🎯' },
]
</script>

<style scoped lang="scss">
.adaptive-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.adaptive-group {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 4px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.04);
}

.adaptive-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: var(--uj-text-secondary, #475569);
  transition: all 0.15s;

  &:hover { background: rgba(74, 155, 140, 0.1); color: var(--uj-text, #0f172a); }
  &.active { background: var(--uj-mint, #4a9b8c); color: #fff; }
  &:disabled { opacity: 0.3; cursor: not-allowed; }
}

.font-label { font-weight: 700; font-size: 12px; }
.font-indicator { font-size: 11px; color: var(--uj-text-muted, #728696); margin: 0 4px; min-width: 28px; text-align: center; }
.persona-btn, .scenario-btn { font-size: 14px; width: 30px; }

@media (max-width: 768px) {
  .adaptive-controls { gap: 4px; }
  .adaptive-group { gap: 1px; padding: 1px 2px; }
  .adaptive-btn { width: 26px; height: 26px; }
  .font-indicator { display: none; }
}
</style>
