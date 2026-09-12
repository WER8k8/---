<template>
  <Teleport to="body">
    <div v-if="paletteOpen" class="search-overlay" @click.self="close">
      <div class="search-modal" role="dialog" aria-modal="true" aria-label="全局搜索">
        <div class="search-input-wrap">
          <SearchOutlined class="search-prefix" />
          <input
            ref="inputRef"
            v-model="q"
            class="search-input"
            placeholder="搜索菜单、页面、功能..."
            autocomplete="off"
            @keydown.down.prevent="down"
            @keydown.up.prevent="up"
            @keydown.enter.prevent="select"
            @keydown.escape.prevent="close"
          />
          <kbd class="search-kbd">ESC</kbd>
        </div>
        <div v-if="results.length" class="search-results">
          <button
            v-for="(r, i) in results"
            :key="`${r.path}-${i}`"
            type="button"
            class="search-item"
            :class="{ active: i === idx }"
            @click="go(r)"
          >
            <YdNavIcon :name="normalizeIcon(r.icon)" size="sm" />
            <span class="flex-1 text-left">{{ r.title }}</span>
            <span class="search-tag">{{ r.group }}</span>
          </button>
        </div>
        <div v-else-if="q" class="search-empty">未找到「{{ q }}」相关结果</div>
        <div v-else class="search-quick">
          <div class="search-quick-title">快速导航</div>
          <div class="search-quick-grid">
            <button
              v-for="item in quickNav"
              :key="item.path"
              type="button"
              class="search-quick-item"
              @click="go(item)"
            >
              <YdNavIcon :name="normalizeIcon(item.icon)" size="sm" />
              <span>{{ item.title }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch, inject, type ComputedRef } from 'vue'
import { useRouter } from 'vue-router'
import { SearchOutlined } from '@ant-design/icons-vue'

import { YdNavIcon } from '@/components/youding'
import { useGlobalSearch } from '@/composables/useGlobalSearch'
import { homePathForRole, isPathAllowedForRoleTier } from '@/constants/roleShellLock'
import { useAuthStore } from '@/stores/auth'
import type { SearchMenuRow } from '@/utils/flattenMenuNav'

const FALLBACK_MENU: SearchMenuRow[] = [
  { title: '超管工作台', path: '/admin', icon: 'CrownOutlined', group: '控制台' },
  { title: '运营看板', path: '/admin/dashboard', icon: 'DashboardOutlined', group: '运营' },
  { title: '租户列表', path: '/admin/tenants', icon: 'TeamOutlined', group: '租户' },
  { title: '询盘管理', path: '/inquiries', icon: 'MessageOutlined', group: '业务' },
  { title: '支付码与接口', path: '/admin/finance/payment-ops', icon: 'PayCircleOutlined', group: '财务' },
  { title: '超管司令部', path: '/admin/system/command-center', icon: 'MonitorOutlined', group: '系统' },
  { title: 'AI 平台接入', path: '/admin/ai-center/provider-setup', icon: 'ApiOutlined', group: 'AI' },
  { title: '套餐配置', path: '/tenants/plans', icon: 'ShopOutlined', group: 'SaaS' },
]

const router = useRouter()
const { paletteOpen, closeSearch } = useGlobalSearch()
const menuIndex = inject<ComputedRef<SearchMenuRow[]>>(
  'globalSearchMenuIndex',
  computed(() => FALLBACK_MENU),
)

const q = ref('')
const idx = ref(0)
const inputRef = ref<HTMLInputElement>()

const quickNav = computed(() => menuIndex.value.slice(0, 6))

const apiResults = ref<SearchMenuRow[]>([])

function normalizeIcon(icon?: string) {
  if (!icon || /[\u{1F300}-\u{1FAFF}]/u.test(icon)) return 'SearchOutlined'
  if (icon.endsWith('Outlined') || icon.endsWith('Filled') || icon.endsWith('TwoTone')) return icon
  return 'SearchOutlined'
}

const results = computed(() => {
  if (!q.value.trim()) return []
  const s = q.value.trim().toLowerCase()
  const local = menuIndex.value
    .filter(
      (m) =>
        m.title.toLowerCase().includes(s) ||
        m.group.toLowerCase().includes(s) ||
        m.path.toLowerCase().includes(s),
    )
    .slice(0, 8)
  const remote = apiResults.value
  const seen = new Set<string>()
  const merged: SearchMenuRow[] = []
  for (const item of [...remote, ...local]) {
    if (seen.has(item.path)) continue
    seen.add(item.path)
    merged.push(item)
    if (merged.length >= 12) break
  }
  return merged
})

watch(q, () => {
  idx.value = 0
})

watch(paletteOpen, (open) => {
  if (open) {
    q.value = ''
    idx.value = 0
    apiResults.value = []
    nextTick(() => inputRef.value?.focus())
  }
})

let searchTimer: ReturnType<typeof setTimeout> | null = null

async function fetchWorkspace(qstr: string) {
  try {
    const { getAuthToken } = await import('@/utils/api')
    const tk = getAuthToken()
    const res = await fetch(`/api/v1/search/workspace?q=${encodeURIComponent(qstr)}&limit=8`, {
      headers: tk ? { Authorization: `Bearer ${tk}` } : {},
    })
    if (!res.ok) {
      apiResults.value = []
      return
    }
    const body = await res.json()
    const items = body.data?.items || body.items || []
    apiResults.value = items.map((r: Record<string, string>) => ({
      title: r.title || '结果',
      path: r.path || '/admin',
      group: r.subtitle || r.type || '工作区',
      icon: normalizeIcon(r.icon),
    }))
  } catch {
    apiResults.value = []
  }
}

watch(q, (val) => {
  if (searchTimer) clearTimeout(searchTimer)
  const trimmed = val.trim()
  if (!trimmed || trimmed.length < 2) {
    apiResults.value = []
    return
  }
  searchTimer = setTimeout(() => fetchWorkspace(trimmed), 280)
})

function down() {
  if (idx.value < results.value.length - 1) idx.value++
}
function up() {
  if (idx.value > 0) idx.value--
}
function select() {
  const r = results.value[idx.value]
  if (r) go(r)
}
async function go(item: { path: string }) {
  close()
  const auth = useAuthStore()
  const target = isPathAllowedForRoleTier(item.path, auth.currentRole)
    ? item.path
    : homePathForRole(auth.currentRole)
  try {
    await router.push(target)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    if (msg.includes('Avoided redundant navigation') || msg.includes('NavigationDuplicated')) return
    if (import.meta.env.DEV) console.warn('[search-nav]', target, err)
  }
}
function close() {
  closeSearch()
  q.value = ''
  idx.value = 0
  apiResults.value = []
}

function onKey(e: KeyboardEvent) {
  const tag = (e.target as HTMLElement | null)?.tagName?.toLowerCase()
  const typing = tag === 'input' || tag === 'textarea' || (e.target as HTMLElement)?.isContentEditable
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    paletteOpen.value = true
    nextTick(() => inputRef.value?.focus())
    return
  }
  if (e.key === 'Escape' && paletteOpen.value) {
    e.preventDefault()
    close()
    return
  }
  if (typing && !paletteOpen.value) return
}

onMounted(() => document.addEventListener('keydown', onKey, true))
onUnmounted(() => document.removeEventListener('keydown', onKey, true))
</script>

<style scoped>
.search-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(4px);
  z-index: 5000;
  display: flex;
  justify-content: center;
  padding-top: 12vh;
}
.search-modal {
  width: min(560px, calc(100vw - 32px));
  max-height: min(480px, calc(100vh - 120px));
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}
.search-input-wrap {
  display: flex;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #f1f5f9;
  gap: 0.75rem;
}
.search-prefix {
  color: #94a3b8;
  font-size: 1.1rem;
}
.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.95rem;
  color: #1e293b;
  background: transparent;
}
.search-input::placeholder {
  color: #cbd5e1;
}
.search-kbd {
  font-size: 0.65rem;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}
.search-results {
  padding: 0.5rem;
  max-height: 360px;
  overflow-y: auto;
}
.search-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0.6rem 0.75rem;
  gap: 0.6rem;
  border: none;
  border-radius: 10px;
  background: transparent;
  cursor: pointer;
  font-size: 0.82rem;
  color: #475569;
  transition: all 0.15s;
}
.search-item:hover,
.search-item.active {
  background: #f1f5f9;
  color: #1e293b;
}
.search-tag {
  font-size: 0.65rem;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.search-empty {
  padding: 3rem 1rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.85rem;
}
.search-quick {
  padding: 1rem;
}
.search-quick-title {
  font-size: 0.7rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
}
.search-quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}
.search-quick-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  border: none;
  background: #f8fafc;
  cursor: pointer;
  font-size: 0.8rem;
  color: #475569;
  transition: all 0.15s;
}
.search-quick-item:hover {
  background: #f1f5f9;
  color: #1e293b;
}
</style>
