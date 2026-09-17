/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, watch, type Ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { Key } from 'ant-design-vue/es/_util/type'

/** Tab 与嵌套路由同步（默认子页为 `/prefix/dashboard`） */
export function useModuleTabSync(
  modulePrefix: string,
  tabKeys: readonly string[],
  defaultKey = 'dashboard',
): {
  tab: Ref<string>
  onTab: (key: Key) => void
  isTabManagedRoute: Ref<boolean>
  navigating: Ref<boolean>
} {
  const router = useRouter()
  const route = useRoute()
  const keySet = new Set<string>(tabKeys)

  const pathToTab = (path: string): string | null => {
    const tail = path.replace(new RegExp(`^${modulePrefix}/?`), '').split('/')[0] || ''
    if (!tail || tail === defaultKey) return defaultKey
    return keySet.has(tail) ? tail : null
  }

  const tabToPath = (tabKey: string): string =>
    `${modulePrefix}/${tabKey === defaultKey ? defaultKey : tabKey}`

  const tab = ref(pathToTab(route.path) ?? defaultKey)
  const isTabManagedRoute = ref(pathToTab(route.path) != null)
  const navigating = ref(false)
  let syncingFromRoute = false

  watch(
    () => route.path,
    (path) => {
      const next = pathToTab(path)
      isTabManagedRoute.value = next != null
      navigating.value = false
      if (next == null || next === tab.value) return
      syncingFromRoute = true
      tab.value = next
      queueMicrotask(() => {
        syncingFromRoute = false
      })
    },
  )

  const onTab = (key: Key) => {
    if (syncingFromRoute) return
    const nextKey = String(key)
    const target = tabToPath(nextKey)
    // 先切 Tab 视觉，避免等路由/懒加载 chunk 才高亮（体感「点不动」）
    tab.value = nextKey
    if (route.path === target) return
    navigating.value = true
    void router.push(target).finally(() => {
      navigating.value = false
    })
  }

  return { tab, onTab, isTabManagedRoute, navigating }
}
