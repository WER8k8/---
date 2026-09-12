<template>
  <header class="topbar">
    <div class="flex items-center gap-3">
      <button class="hamburger-btn" title="菜单" @click="collapsed = !collapsed">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <div class="flex items-center gap-2 min-w-0">
        <h1 class="yd-pro-topbar__title">{{ pageTitle }}</h1>
        <template v-if="showBreadcrumbSubtitle">
          <span class="yd-pro-topbar__sep" aria-hidden="true">/</span>
          <span class="yd-pro-topbar__subtitle">{{ pageSubtitle }}</span>
        </template>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <button
        v-if="showPlatformHome"
        type="button"
        class="platform-home-btn"
        @click="emit('navigate', platformHomePath)"
      >
        返回超管工作台
      </button>
      <YdQueueEntry />
      <button
        type="button"
        class="search-btn"
        title="搜索 (Ctrl+K)"
        aria-label="打开全局搜索 Ctrl+K"
        @click="openSearch"
      >
        <SearchOutlined class="text-sm text-gray-400" />
        <span class="hidden sm:inline yd-pro-topbar__search-hint">搜索...</span>
        <kbd class="yd-pro-topbar__kbd hidden sm:inline">Ctrl+K</kbd>
      </button>

      <span class="yd-pro-topbar__clock hidden lg:inline">{{ timeStr }}</span>

      <button class="icon-btn" title="AI Copilot" @click="copilotOpen = !copilotOpen">
        <YdReliefIcon :icon="RobotOutlined" size="sm" />
      </button>

      <button class="icon-btn" title="主题与布局" @click="themeDrawerOpen = true">
        <YdReliefIcon :icon="SettingOutlined" size="sm" />
      </button>

      <div ref="notifyRef" class="relative">
        <button class="icon-btn" title="通知" @click="showNotify = !showNotify">
          <YdReliefIcon :icon="BellOutlined" size="sm" />
          <span v-if="alertCount" class="badge-num">{{ alertCount > 99 ? '99+' : alertCount }}</span>
          <span v-else class="badge-dot" />
        </button>
        <transition name="dropdown">
          <div v-if="showNotify" class="notify-panel">
            <div class="notify-panel-header">
              <span>告警中心</span>
              <span class="text-red-500 text-xs font-medium">{{ alertCount }} 条待处理</span>
            </div>
            <div v-if="recentAlerts.length" class="notify-list">
              <div
                v-for="a in recentAlerts"
                :key="a.id"
                class="notify-item"
                :class="'level-' + a.level"
                @click="onAlertClick"
              >
                <span class="notify-dot" :class="a.level" />
                <div class="flex-1 min-w-0">
                  <div class="text-[13px] text-gray-700 truncate">{{ a.title }}</div>
                  <div class="text-[11px] text-gray-400 mt-0.5">
                    {{ a.created_at ? new Date(a.created_at).toLocaleString('zh-CN') : '' }}
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="notify-empty">暂无告警</div>
            <div class="notify-panel-footer">
              <router-link
                v-if="isPlatformRole()"
                to="/admin"
                class="text-brand-500 text-[13px]"
                @click="showNotify = false"
              >
                查看全部
              </router-link>
            </div>
          </div>
        </transition>
      </div>

      <div class="user-chip" @click="emit('navigate', brandHome)">
        <div class="sidebar-brand-mark w-6 h-6 rounded-md text-white flex items-center justify-center font-semibold text-[11px]">
          {{ username.charAt(0) || 'A' }}
        </div>
        <span class="hidden sm:inline text-[13px] text-gray-600 font-medium">{{ username }}</span>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  BellOutlined,
  RobotOutlined,
  SearchOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import YdQueueEntry from '@/components/layout/YdQueueEntry.vue'
import { YdReliefIcon } from '@/components/youding'
import { useGlobalSearch } from '@/composables/useGlobalSearch'
import { decodeJwtPayload, jwtRoleFromPayload } from '@/utils/jwtPayload'
import { readStoredAccessToken } from '@/utils/sessionAuth'

const props = withDefaults(
  defineProps<{
    pageTitle: string
    pageSubtitle: string
    showBreadcrumbSubtitle: boolean
    username: string
    brandHome: string
    showPlatformHome?: boolean
    platformHomePath?: string
  }>(),
  { showPlatformHome: false, platformHomePath: '/admin' },
)

const collapsed = defineModel<boolean>('collapsed', { required: true })
const copilotOpen = defineModel<boolean>('copilotOpen', { required: true })
const themeDrawerOpen = defineModel<boolean>('themeDrawerOpen', { required: true })

const emit = defineEmits<{
  navigate: [path: string]
}>()

const router = useRouter()
const { openSearch } = useGlobalSearch()

const showNotify = ref(false)
const notifyRef = ref<HTMLElement>()
const alertCount = ref(0)
const recentAlerts = ref<{ id: string | number; level: string; title: string; created_at?: string }[]>([])
let notifyTimer: ReturnType<typeof setInterval> | null = null

function isPlatformRole(): boolean {
  try {
    const tk = readStoredAccessToken()
    if (!tk) return false
    const role = jwtRoleFromPayload(decodeJwtPayload(tk))
    return role === 'super_admin' || role === 'admin'
  } catch { return false }
}

async function fetchAlerts() {
  if (!isPlatformRole()) return
  try {
    const res = await fetch('/api/v1/super-admin/alerts/summary', {
      headers: { Authorization: `Bearer ${readStoredAccessToken()}` },
    })
    const data = await res.json()
    const d = data.data || data
    alertCount.value = d.open_count || 0
    recentAlerts.value = d.recent || []
  } catch {
    /* non-blocking */
  }
}

function onAlertClick() {
  void router.push('/admin')
  showNotify.value = false
}

function onDocumentClick(e: MouseEvent) {
  if (notifyRef.value && !notifyRef.value.contains(e.target as Node)) {
    showNotify.value = false
  }
}

const timeStr = ref('')
let clockTimer: ReturnType<typeof setInterval> | null = null

function updateClock() {
  timeStr.value = new Date().toLocaleString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

onMounted(() => {
  void fetchAlerts()
  notifyTimer = setInterval(() => {
    if (typeof document !== 'undefined' && document.visibilityState !== 'visible') return
    void fetchAlerts()
  }, 60000)
  if (typeof document !== 'undefined') {
    document.addEventListener('click', onDocumentClick)
  }
  updateClock()
  clockTimer = setInterval(updateClock, 10000)
})

onUnmounted(() => {
  if (notifyTimer) clearInterval(notifyTimer)
  if (clockTimer) clearInterval(clockTimer)
  if (typeof document !== 'undefined') {
    document.removeEventListener('click', onDocumentClick)
  }
})
</script>

<style scoped>
.topbar {
  height: 52px;
  background: var(--uj-glass-bg-strong, #fff);
  border-bottom: 1px solid var(--uj-border-soft, #f1f5f9);
  box-shadow: 0 1px 0 rgb(255 255 255 / 0.8) inset, 0 4px 16px rgb(45 107 96 / 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 30;
}

.yd-pro-topbar__title {
  margin: 0;
  font-family: var(--uj-font-display, 'DM Sans', sans-serif);
  font-size: 15px;
  font-weight: 650;
  letter-spacing: -0.01em;
  color: var(--uj-text-secondary, #1e293b);
  flex-shrink: 0;
}

.yd-pro-topbar__sep {
  color: var(--uj-border-soft, #cbd5e1);
  font-weight: 300;
  flex-shrink: 0;
}

.yd-pro-topbar__subtitle {
  font-size: 13px;
  color: var(--uj-text-muted, #64748b);
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 640px) {
  .yd-pro-topbar__subtitle { display: none; }
}

.yd-pro-topbar__search-hint {
  font-size: 13px;
  color: var(--uj-text-muted, #94a3b8);
}

.yd-pro-topbar__kbd {
  font-size: 11px;
  font-family: var(--uj-font-sans);
  color: var(--uj-text-muted, #94a3b8);
  background: rgb(255 255 255 / 0.65);
  border: 1px solid var(--uj-border-soft, #e2e8f0);
  padding: 1px 6px;
  border-radius: 5px;
  line-height: 1.4;
}

.yd-pro-topbar__clock {
  font-size: 13px;
  font-variant-numeric: tabular-nums;
  color: var(--uj-text-muted, #94a3b8);
  white-space: nowrap;
}

.hamburger-btn {
  display: none;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  align-items: center;
  justify-content: center;
}
@media (max-width: 768px) {
  .hamburger-btn { display: flex; }
  .topbar { padding: 0 12px; height: 48px; }
  .notify-panel { width: 280px; right: -8px; }
}
@media (max-width: 480px) {
  .topbar { height: 44px; padding: 0 8px; }
}

.platform-home-btn {
  display: inline-flex;
  align-items: center;
  height: 34px;
  padding: 0 14px;
  border: none;
  border-radius: 8px;
  background: var(--uj-brand, #0d9488);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  font-family: inherit;
  box-shadow: 0 1px 2px rgb(13 148 136 / 0.2);
  transition: background 0.15s ease;
}

.platform-home-btn:hover {
  background: var(--uj-brand-hover, #3d8578);
}

.search-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: 8px;
  border: 1px solid var(--uj-border-soft, #e2e8f0);
  background: rgb(255 255 255 / 0.5);
  color: var(--uj-text-muted, #94a3b8);
  cursor: pointer;
  font-size: 13px;
  transition: border-color 0.15s ease, color 0.15s ease, background 0.15s ease;
  font-family: inherit;
}
.search-btn:hover {
  border-color: var(--uj-brand, #4a9b8c);
  color: var(--uj-brand-deep, #2a6b60);
  background: rgb(255 255 255 / 0.9);
}

.icon-btn {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.15s;
  padding: 0;
}

.badge-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 7px;
  height: 7px;
  background: #ef4444;
  border-radius: 50%;
  border: 2px solid white;
}
.badge-num {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: #ef4444;
  color: white;
  font-size: 10px;
  font-weight: 700;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

.notify-panel {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  width: 360px;
  background: var(--uj-popover-bg, #fff);
  border-radius: 12px;
  box-shadow: var(--uj-glass-shadow-hover, 0 10px 30px rgba(0, 0, 0, 0.1));
  border: 1px solid var(--uj-popover-border, #f1f5f9);
  overflow: hidden;
  z-index: 100;
}
.notify-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--uj-border-soft, #f1f5f9);
  font-size: 13px;
  font-weight: 600;
  color: var(--uj-text-secondary, #1e293b);
}
.notify-list { max-height: 300px; overflow-y: auto; }
.notify-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid var(--uj-border-soft, #f8fafc);
}
.notify-item:hover { background: var(--uj-surface-hover, #f8fafc); }
.notify-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}
.notify-dot.critical { background: #ef4444; }
.notify-dot.warning { background: #f59e0b; }
.notify-dot.info { background: var(--uj-brand, #4a9b8c); }
.notify-empty { padding: 32px 16px; text-align: center; color: var(--uj-text-muted, #94a3b8); font-size: 13px; }
.notify-panel-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--uj-border-soft, #f1f5f9);
  text-align: center;
}
.notify-panel-footer a { font-size: 13px; color: var(--uj-brand, #4a9b8c); text-decoration: none; }

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.15s;
}
.user-chip:hover { background: var(--uj-surface-hover, #f1f5f9); }
</style>
