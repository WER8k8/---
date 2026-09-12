<template>
  <a-drawer
    v-model:open="open"
    title="主题与布局"
    placement="right"
    width="320"
    :destroy-on-close="false"
  >
    <a-form layout="vertical" size="small">
      <a-form-item label="外观">
        <a-segmented
          v-model:value="themeModel"
          block
          :options="[
            { label: '浅色', value: 'light' },
            { label: '深色', value: 'dark' },
          ]"
        />
      </a-form-item>
      <a-form-item label="角色主题">
        <a-segmented
          v-model:value="accentModel"
          block
          :options="[
            { label: '超管', value: 'platform' },
            { label: '租户', value: 'client' },
            { label: '代理', value: 'agent' },
          ]"
        />
      </a-form-item>
      <p class="theme-hint">切换外观与主色时页面不会刷新；送检演示可在此试深色。</p>
      <a-form-item v-if="ui.accentRole === 'platform'" label="主色（Platform）">
        <div class="flex gap-2 flex-wrap">
          <button
            v-for="c in presetColors"
            :key="c"
            type="button"
            class="color-swatch"
            :style="{ background: c }"
            :class="{ active: ui.primaryColor === c }"
            :title="`主色 ${c} · 白字对比度 ${contrastRatio(c).toFixed(1)}:1（${readabilityLabel(contrastRatio(c))}）`"
            @click="pickColor(c)"
          />
        </div>
        <p v-if="rejectReason" class="contrast-warn">{{ rejectReason }}</p>
        <p class="theme-hint">
          当前主色白字对比度 {{ activeContrast.toFixed(1) }}:1（{{ activeReadability }}）·
          WCAG AA 大文本阈值 ≥ 3:1
        </p>
      </a-form-item>
      <a-form-item label="圆角">
        <a-radio-group v-model:value="radiusModel" button-style="solid">
          <a-radio-button value="sm">小</a-radio-button>
          <a-radio-button value="md">中</a-radio-button>
          <a-radio-button value="lg">大</a-radio-button>
        </a-radio-group>
      </a-form-item>
      <a-form-item label="表格密度">
        <a-radio-group v-model:value="densityModel" button-style="solid">
          <a-radio-button value="compact">紧凑</a-radio-button>
          <a-radio-button value="default">默认</a-radio-button>
          <a-radio-button value="comfortable">宽松</a-radio-button>
        </a-radio-group>
      </a-form-item>
      <a-form-item label="多标签 Worktab">
        <a-switch v-model:checked="worktabModel" />
      </a-form-item>
      <a-button block @click="ui.reset()">恢复默认</a-button>
    </a-form>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import {
  useUiPreferencesStore,
  type UiAccentRole,
  type UiRadiusScale,
  type UiTableDensity,
  type UiTheme,
} from '@/stores/uiPreferences';

const open = defineModel<boolean>('open', { default: false });

const ui = useUiPreferencesStore();
/**
 * 主色预设：统一收敛到薄荷/青绿系（与 DESIGN-TOKEN-LOCK-01 平台主色一致），
 * 每个色对白色文字的对比度均 ≥ 3:1（WCAG AA 大文本下限），避免不可读主色。
 */
const presetColors = ['#4a9b8c', '#2a9d8f', '#0d9488', '#157a6e', '#0f766e', '#3d8578'];

/* —— WCAG 对比度校验（D10：用户自定义主色须可读） —— */
function hexToRgb(hex: string): [number, number, number] | null {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex.trim());
  if (!m) return null;
  return [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)];
}
function relativeLuminance([r, g, b]: [number, number, number]): number {
  const lin = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}
/** 前景 hex 对背景 bg 的对比度，默认背景为白（主色按钮白字场景） */
function contrastRatio(hex: string, bg = '#ffffff'): number {
  const fg = hexToRgb(hex);
  const bgRgb = hexToRgb(bg);
  if (!fg || !bgRgb) return 0;
  const l1 = relativeLuminance(fg);
  const l2 = relativeLuminance(bgRgb);
  const [hi, lo] = l1 > l2 ? [l1, l2] : [l2, l1];
  return (hi + 0.05) / (lo + 0.05);
}
function readabilityLabel(c: number): '优' | '良' | '差' {
  if (c >= 4.5) return '优'; // WCAG AA 正文
  if (c >= 3) return '良'; // WCAG AA 大文本/图形
  return '差'; // 低于下限，白字不可读
}

const rejectReason = ref('');
function pickColor(c: string) {
  const ratio = contrastRatio(c, '#ffffff');
  if (ratio < 3) {
    rejectReason.value = `该颜色白字对比度仅 ${ratio.toFixed(1)}:1，低于可读性下限 3:1，未应用。`;
    return;
  }
  rejectReason.value = '';
  ui.setPrimaryColor(c);
}

const themeModel = computed({
  get: () => ui.theme,
  set: (v: UiTheme) => ui.setTheme(v),
});
const accentModel = computed({
  get: () => ui.accentRole,
  set: (v: UiAccentRole) => ui.setAccentRole(v),
});
const radiusModel = computed({
  get: () => ui.radiusScale,
  set: (v: UiRadiusScale) => ui.setRadiusScale(v),
});
const densityModel = computed({
  get: () => ui.tableDensity,
  set: (v: UiTableDensity) => ui.setTableDensity(v),
});
const worktabModel = computed({
  get: () => ui.worktabEnabled,
  set: (v: boolean) => ui.setWorktabEnabled(v),
});
const activeContrast = computed(() => contrastRatio(ui.primaryColor, '#ffffff'));
const activeReadability = computed(() => readabilityLabel(activeContrast.value));
</script>

<style scoped>
.color-swatch {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 2px solid transparent;
  cursor: pointer;
}
.color-swatch.active {
  border-color: var(--uj-brand-deep, #2a6b60);
  box-shadow: 0 0 0 2px var(--uj-glass-bg-strong, #fff) inset;
}
.theme-hint {
  margin: -8px 0 12px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--uj-text-muted, #64748b);
}
.contrast-warn {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: #d4380d;
}
</style>
