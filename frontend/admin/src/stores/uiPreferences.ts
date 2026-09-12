import { watch } from 'vue';
import { defineStore } from 'pinia';

export type UiTheme = 'light' | 'dark';
export type UiAccentRole = 'platform' | 'client' | 'agent';
export type UiRadiusScale = 'sm' | 'md' | 'lg';
export type UiTableDensity = 'compact' | 'default' | 'comfortable';

export interface UiPreferencesState {
  theme: UiTheme;
  accentRole: UiAccentRole;
  primaryColor: string;
  radiusScale: UiRadiusScale;
  tableDensity: UiTableDensity;
  worktabEnabled: boolean;
  sidebarWidth: number;
}

const STORAGE_KEY = 'uj-ui-preferences-v1';

/** 超管 Platform 主色：马卡龙薄荷（Pastel Mint Glass） */
export const PLATFORM_BRAND_DEFAULT = '#4a9b8c';

/** 旧版紫 / 蓝灰主色 → 统一迁移到薄荷 */
const LEGACY_PLATFORM_COLORS = new Set([
  '#7c3aed',
  '#8b5cf6',
  '#6d28d9',
  '#9333ea',
  '#a855f7',
  '#55778f',
  '#5f88a0',
  '#6f93ab',
  '#8094ad',
]);

const defaults: UiPreferencesState = {
  theme: 'light',
  accentRole: 'platform',
  primaryColor: PLATFORM_BRAND_DEFAULT,
  radiusScale: 'md',
  tableDensity: 'default',
  worktabEnabled: true,
  sidebarWidth: 248,
};

function normalizePrimaryColor(color: string | undefined): string {
  const c = (color || '').trim().toLowerCase();
  if (LEGACY_PLATFORM_COLORS.has(c)) return PLATFORM_BRAND_DEFAULT;
  return color || PLATFORM_BRAND_DEFAULT;
}

function loadState(): UiPreferencesState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...defaults };
    const parsed = { ...defaults, ...JSON.parse(raw) } as UiPreferencesState;
    parsed.primaryColor = normalizePrimaryColor(parsed.primaryColor);
    return parsed;
  } catch {
    return { ...defaults };
  }
}

function densityToAntSize(d: UiTableDensity): 'small' | 'middle' | 'large' {
  if (d === 'compact') return 'small';
  if (d === 'comfortable') return 'large';
  return 'middle';
}

function radiusToPx(scale: UiRadiusScale): number {
  if (scale === 'sm') return 8;
  if (scale === 'lg') return 14;
  return 10;
}

const ACCENT_BRAND: Record<UiAccentRole, string> = {
  platform: '', // uses primaryColor
  client: '#4a9b8c',
  agent: '#0d9488',
};

export const useUiPreferencesStore = defineStore('uiPreferences', {
  state: (): UiPreferencesState => loadState(),
  getters: {
    antTableSize(): 'small' | 'middle' | 'large' {
      return densityToAntSize(this.tableDensity);
    },
    antBorderRadius(): number {
      return radiusToPx(this.radiusScale);
    },
    isDark(): boolean {
      return this.theme === 'dark';
    },
  },
  actions: {
    persist() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.$state));
      this.applyDom();
    },
    applyDom() {
      if (typeof document === 'undefined') return;
      const root = document.documentElement;
      root.dataset.ujTheme = this.theme;
      root.dataset.ujAccent = this.accentRole;
      root.dataset.ujRadius = this.radiusScale;
      root.style.colorScheme = this.theme === 'dark' ? 'dark' : 'light';
      root.style.setProperty('--uj-sidebar-width', `${this.sidebarWidth}px`);
      root.style.setProperty('--uj-sidebar-collapsed-width', '64px');

      const isDark = this.theme === 'dark';
      const metaTheme = document.querySelector('meta[name="theme-color"]');

      if (this.accentRole === 'platform') {
        const brand = normalizePrimaryColor(this.primaryColor);
        root.style.setProperty('--uj-brand', isDark ? '#58c4ae' : brand);
        root.style.setProperty('--uj-brand-hover', isDark ? '#7ed4c0' : '#3d8578');
        root.style.setProperty(
          '--uj-brand-muted',
          isDark ? 'rgb(88 196 174 / 0.16)' : 'rgb(74 155 140 / 0.14)',
        );
        root.style.setProperty('--uj-brand-deep', isDark ? '#c8f0e8' : '#2a6b60');
        if (metaTheme) metaTheme.setAttribute('content', isDark ? '#2a3038' : '#e2f5f0');
        return;
      }

      const brand = ACCENT_BRAND[this.accentRole] ?? this.primaryColor;
      root.style.setProperty('--uj-brand', isDark && this.accentRole === 'client' ? '#6ba3e8' : isDark && this.accentRole === 'agent' ? '#5cc4b0' : brand);
      if (this.accentRole === 'client') {
        root.style.setProperty('--uj-brand-hover', isDark ? '#93c5fd' : '#1d4ed8');
        root.style.setProperty(
          '--uj-brand-muted',
          isDark ? 'rgb(59 130 246 / 0.16)' : 'rgb(37 99 235 / 0.1)',
        );
        root.style.setProperty('--uj-brand-deep', isDark ? '#b4d4f5' : '#1e40af');
      } else if (this.accentRole === 'agent') {
        root.style.setProperty('--uj-brand-hover', isDark ? '#7dd3c0' : '#0f766e');
        root.style.setProperty(
          '--uj-brand-muted',
          isDark ? 'rgb(77 182 160 / 0.16)' : 'rgb(13 148 136 / 0.12)',
        );
        root.style.setProperty('--uj-brand-deep', isDark ? '#a8e6d8' : '#115e59');
      } else {
        root.style.setProperty('--uj-brand-hover', '#4a6a7f');
        root.style.setProperty('--uj-brand-muted', '#edf3f6');
        root.style.setProperty('--uj-brand-deep', '#3d5566');
      }
      if (metaTheme) {
        metaTheme.setAttribute('content', isDark ? '#2a3038' : '#e8eef8');
      }
    },
    setTheme(theme: UiTheme) {
      this.theme = theme;
      this.persist();
    },
    setAccentRole(role: UiAccentRole) {
      this.accentRole = role;
      this.persist();
    },
    setPrimaryColor(color: string) {
      this.primaryColor = color;
      this.persist();
    },
    setRadiusScale(scale: UiRadiusScale) {
      this.radiusScale = scale;
      this.persist();
    },
    setTableDensity(density: UiTableDensity) {
      this.tableDensity = density;
      this.persist();
    },
    setWorktabEnabled(enabled: boolean) {
      this.worktabEnabled = enabled;
      this.persist();
    },
    reset() {
      Object.assign(this, defaults);
      this.persist();
    },
    init() {
      const normalized = normalizePrimaryColor(this.primaryColor);
      if (normalized !== this.primaryColor) {
        this.primaryColor = normalized;
        this.persist();
      } else {
        this.applyDom();
      }
    },
  },
});

export function initUiPreferencesWatch() {
  const store = useUiPreferencesStore();
  store.init();
  watch(
    () => ({ ...store.$state }),
    () => store.applyDom(),
    { deep: true },
  );
}
