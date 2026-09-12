<template>
  <aside class="sidebar" :class="{ collapsed, 'flyout-open': !!flyoutMenu }">
    <div class="sidebar-brand">
      <router-link
        :to="brandHome"
        class="flex items-center gap-3 no-underline"
        @click="emit('brand-click')"
      >
        <div class="sidebar-brand-mark flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center">
          <span class="text-white font-bold text-xs">{{ brandMark }}</span>
        </div>
        <transition name="brand-fade">
          <div v-show="!collapsed" class="flex flex-col">
            <span class="text-[15px] font-semibold text-gray-900 leading-tight">{{ brandTitle }}</span>
            <span class="text-[10px] text-gray-400 tracking-wide uppercase">{{ brandSubtitle }}</span>
          </div>
        </transition>
      </router-link>
    </div>

    <nav class="sidebar-nav">
      <div v-for="(group, gi) in menuItems" :key="gi" class="mb-1">
        <div v-if="group.title && !collapsed" class="nav-group-title">{{ group.title }}</div>
        <div v-for="item in group.children" :key="item.name">
          <template v-if="item.children?.length">
            <div class="nav-item-group" :class="{ 'has-active-child': isNavDescendantActive(item) }">
              <button
                type="button"
                class="nav-item nav-item-main"
                :class="{ active: isNavItemActive(item), expanded: expandedSubMenus.includes(item.name) }"
                @click.stop="emit('parent-main-click', item)"
              >
                <span class="nav-icon"><YdNavIcon :name="item.icon" :active="isNavItemActive(item)" /></span>
                <span v-show="!collapsed" class="nav-text">{{ item.title }}</span>
                <span v-if="collapsed" class="tooltip">{{ item.title }}</span>
              </button>
              <button
                v-show="!collapsed"
                type="button"
                class="nav-arrow-btn"
                :aria-expanded="expandedSubMenus.includes(item.name)"
                @click.stop="emit('toggle-submenu', item.name)"
              >
                <svg
                  class="nav-arrow"
                  :class="{ open: expandedSubMenus.includes(item.name) }"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.5"
                >
                  <path d="M9 6l6 6-6 6" />
                </svg>
              </button>
              <div v-if="collapsed && flyoutMenu === item.name" class="nav-flyout" @click.stop>
                <button
                  v-for="sub in item.children"
                  :key="sub.name"
                  type="button"
                  class="submenu-item"
                  :class="{ active: isNavItemActive(sub) }"
                  @click.stop="emit('navigate', sub.path)"
                >
                  <YdNavIcon :name="sub.icon" size="sm" :active="isNavItemActive(sub)" />
                  <span>{{ sub.title }}</span>
                </button>
              </div>
            </div>
            <div v-if="expandedSubMenus.includes(item.name) && !collapsed" class="submenu">
              <template v-if="hasGroupedChildren(item)">
                <template v-for="(gItems, gName) in groupChildren(item)" :key="gName">
                  <div v-if="gName !== 'default'" class="submenu-group-label" @click.stop="toggleSubGroup(item.name + ':' + gName)">
                    <span>{{ gName }}</span>
                    <svg class="nav-arrow" :class="{ open: !collapsedSubGroups.includes(item.name + ':' + gName) }" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 6l6 6-6 6" /></svg>
                  </div>
                  <template v-if="gName === 'default' || !collapsedSubGroups.includes(item.name + ':' + gName)">
                    <button
                      v-for="sub in gItems"
                      :key="sub.name"
                      type="button"
                      class="submenu-item"
                      :class="{ active: isNavItemActive(sub) }"
                      @click.stop="emit('navigate', sub.path)"
                    >
                      <YdNavIcon :name="sub.icon" size="sm" :active="isNavItemActive(sub)" />
                      <span>{{ sub.title }}</span>
                    </button>
                  </template>
                </template>
              </template>
              <template v-else>
              <button
                v-for="sub in item.children"
                :key="sub.name"
                type="button"
                class="submenu-item"
                :class="{ active: isNavItemActive(sub) }"
                @click.stop="emit('navigate', sub.path)"
              >
                <YdNavIcon :name="sub.icon" size="sm" :active="isNavItemActive(sub)" />
                <span>{{ sub.title }}</span>
              </button>
              </template>
            </div>
          </template>
          <button
            v-else
            type="button"
            class="nav-item"
            :class="{ active: isNavItemActive(item) }"
            @click.stop="emit('navigate', item.path)"
          >
            <span class="nav-icon"><YdNavIcon :name="item.icon" :active="isNavItemActive(item)" /></span>
            <span v-show="!collapsed" class="nav-text">{{ item.title }}</span>
            <span v-if="collapsed" class="tooltip">{{ item.title }}</span>
          </button>
        </div>
      </div>
    </nav>

    <div class="sidebar-footer">
      <div v-show="!collapsed" class="flex items-center gap-2 px-1 mb-2">
        <div class="w-7 h-7 rounded-md sidebar-user-avatar text-white flex items-center justify-center font-semibold text-xs flex-shrink-0">
          {{ username.charAt(0) || 'A' }}
        </div>
        <div class="flex flex-col min-w-0">
          <span class="text-[13px] text-gray-700 font-medium truncate">{{ username }}</span>
          <span class="text-[10px] text-gray-400">{{ roleLabel }}</span>
        </div>
      </div>
      <div class="flex justify-center gap-1">
        <button class="sidebar-footer-btn" :title="collapsed ? '展开' : '收起'" @click="collapsed = !collapsed">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
        <button class="sidebar-footer-btn" title="退出" @click="emit('logout')">
          <LogoutOutlined />
        </button>
      </div>
    </div>
  </aside>

  <button v-if="collapsed && !isMobile" class="expand-btn" @click="collapsed = false">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M9 5l7 7-7 7" />
    </svg>
  </button>

  <div v-show="!collapsed && isMobile" class="mobile-overlay" @click="collapsed = true" />
</template>

<script setup lang="ts">
import { LogoutOutlined } from '@ant-design/icons-vue'
import { YdNavIcon } from '@/components/youding'
import type { ShellMenuGroup, ShellNavItem } from '@/types/shellNav'
import { ref } from 'vue'

const collapsedSubGroups = ref<string[]>([])

function toggleSubGroup(key: string) {
  const idx = collapsedSubGroups.value.indexOf(key)
  if (idx >= 0) collapsedSubGroups.value.splice(idx, 1)
  else collapsedSubGroups.value.push(key)
}

function hasGroupedChildren(item: ShellNavItem): boolean {
  return item.children?.some((c: any) => c.group) ?? false
}

function groupChildren(item: ShellNavItem): Record<string, ShellNavItem[]> {
  const groups: Record<string, ShellNavItem[]> = {}
  for (const child of item.children ?? []) {
    const g = (child as any).group || 'default'
    if (!groups[g]) groups[g] = []
    groups[g].push(child)
  }
  return groups
}

defineProps<{
  menuItems: ShellMenuGroup[]
  isMobile: boolean
  flyoutMenu: string | null
  expandedSubMenus: string[]
  brandHome: string
  brandMark: string
  brandTitle: string
  brandSubtitle: string
  username: string
  roleLabel: string
  isNavItemActive: (item: ShellNavItem) => boolean
  isNavDescendantActive: (item: ShellNavItem) => boolean
}>()

const collapsed = defineModel<boolean>('collapsed', { required: true })

const emit = defineEmits<{
  navigate: [path: string]
  logout: []
  'toggle-submenu': [name: string]
  'parent-main-click': [item: ShellNavItem]
  'brand-click': []
}>()
</script>

<style scoped>
.sidebar {
  width: var(--uj-sidebar-width, 248px);
  min-height: 100vh;
  background: var(--uj-sidebar-bg, var(--uj-glass-bg-strong, #fff));
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
  overflow-x: hidden;
  transition: width 0.25s ease;
  border-right: 1px solid var(--uj-border-soft, #f1f5f9);
}
.sidebar.collapsed { width: var(--uj-sidebar-collapsed-width, 64px); }
.sidebar.flyout-open .sidebar-nav { overflow: visible; }

.nav-item-group {
  display: flex;
  align-items: stretch;
  position: relative;
  gap: 0;
}
.nav-item-main { flex: 1; min-width: 0; }
.nav-arrow-btn {
  flex-shrink: 0;
  width: 32px;
  border: none;
  background: transparent;
  color: #cbd5e1;
  cursor: pointer;
  border-radius: 0 8px 8px 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.nav-arrow-btn:hover { background: #f8fafc; color: #64748b; }

.nav-flyout {
  position: absolute;
  left: calc(100% + 4px);
  top: 0;
  min-width: 180px;
  padding: 6px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
  z-index: 80;
}

.sidebar-brand {
  padding: 18px 16px;
  border-bottom: 1px solid #f1f5f9;
}
.sidebar-brand a { text-decoration: none; }

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 8px 8px;
}
.sidebar-nav::-webkit-scrollbar { width: 3px; }
.sidebar-nav::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 2px; }

.nav-group-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  padding: 12px 10px 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  margin: 1px 0;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 14px;
  font-weight: 450;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
  position: relative;
  text-align: left;
  font-family: inherit;
}
.nav-item:hover { background: #f8fafc; color: #334155; }

.nav-item-group.has-active-child > .nav-item-main:not(.active) {
  color: var(--uj-brand-deep, #2a6b60);
  font-weight: 500;
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--uj-brand, #4a9b8c);
  border-radius: 0 3px 3px 0;
}

.nav-icon {
  width: 32px;
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: visible;
}

.nav-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-arrow {
  flex-shrink: 0;
  color: #cbd5e1;
  transition: transform 0.2s ease;
}
.nav-arrow.open { transform: rotate(90deg); }

.tooltip {
  position: absolute;
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  padding: 5px 10px;
  background: #1e293b;
  color: #f1f5f9;
  font-size: 12px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s;
  z-index: 60;
}
.nav-item:hover .tooltip { opacity: 1; }

.submenu {
  padding: 2px 0 2px 20px;
  margin-left: 16px;
  border-left: 1px solid #f1f5f9;
}
.submenu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 4px 8px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
  font-family: inherit;
}
.submenu-item:hover { color: #334155; background: #f8fafc; }

.submenu-group-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px 4px;
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  user-select: none;
}
.submenu-group-label:hover { color: #6b7280; }
.submenu-group-label .nav-arrow { transition: transform 0.15s ease; }
.submenu-group-label .nav-arrow.open { transform: rotate(90deg); }

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid #f1f5f9;
}
.sidebar-footer-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.sidebar-footer-btn:hover { background: #f1f5f9; color: #64748b; }

.expand-btn {
  position: fixed;
  left: calc(var(--uj-sidebar-collapsed-width, 64px) + 12px);
  top: 50%;
  transform: translateY(-50%);
  z-index: 45;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid #e2e8f0;
  background: white;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: all 0.15s;
}
.expand-btn:hover { color: var(--uj-brand, #4a9b8c); border-color: var(--uj-brand, #4a9b8c); }

.mobile-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 55;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed !important;
    z-index: 60;
    width: 248px;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
  }
  .sidebar:not(.collapsed) { transform: translateX(0); }
  .expand-btn { display: none !important; }
  .mobile-overlay { display: block; }
}
</style>
