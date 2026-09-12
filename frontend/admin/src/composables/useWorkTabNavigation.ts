import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router'

import { resolveShellMode } from '@/constants/proShellMenus'
import { normalizeLocationPath } from '@/constants/workbenchPathCapabilities'
import { useAuthStore } from '@/stores/auth'
import { useWorkTabsStore } from '@/stores/workTabs'
import { resolveWorkTabNavigatePath } from '@/utils/workTabPath'

export function useWorkTabNavigation() {
  const router = useRouter()
  const workTabs = useWorkTabsStore()
  const { tabs, activePath } = storeToRefs(workTabs)

  async function go(path: string) {
    const auth = useAuthStore()
    const shell = resolveShellMode(router.currentRoute.value.path)
    const target = resolveWorkTabNavigatePath(path, shell, auth.currentRole)
    const current = normalizeLocationPath(router.currentRoute.value.path)
    if (target === current) {
      workTabs.setActive(target)
      return
    }
    try {
      await router.push(target)
      // activePath 由 layout route watch → openTab 同步；此处仅兜底
      workTabs.setActive(target)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      if (msg.includes('Avoided redundant navigation') || msg.includes('NavigationDuplicated')) {
        workTabs.setActive(target)
        return
      }
      workTabs.setActive(current)
      console.warn('[worktab-nav]', path, err)
    }
  }

  function close(path: string) {
    const closingActive =
      normalizeLocationPath(workTabs.activePath) === normalizeLocationPath(path)
    const next = workTabs.closeTab(path)
    if (closingActive) void router.push(next)
  }

  function closeOthers(keepPath: string) {
    const keep = normalizeLocationPath(keepPath)
    const toRemove = workTabs.tabs.filter(
      (t) => !t.affix && normalizeLocationPath(t.path) !== keep,
    )
    for (const tab of toRemove) {
      workTabs.closeTab(tab.path)
    }
  }

  return { tabs, activePath, go, close, closeOthers }
}
