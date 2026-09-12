import { computed, toValue, type MaybeRefOrGetter } from 'vue';
import { useRoute } from 'vue-router';

import type { ShellMenuGroup, ShellNavItem } from '@/types/shellNav';
import {
  isShellNavDescendantActive,
  isShellNavItemActive,
  resolveActiveMenuPath,
  resolveNavTitleFromMenu,
} from '@/utils/shellNavKernel';

/** Vue 壳层导航 — 消费 menuItems，输出激活态与标题解析 */
export function useShellNavigation(menuItems: MaybeRefOrGetter<ShellMenuGroup[]>) {
  const route = useRoute();

  const activeMenuPath = computed(() =>
    resolveActiveMenuPath(route.path, toValue(menuItems)),
  );

  function isNavItemActive(item: ShellNavItem): boolean {
    return isShellNavItemActive(item, activeMenuPath.value);
  }

  function isNavDescendantActive(item: ShellNavItem): boolean {
    return isShellNavDescendantActive(item, activeMenuPath.value);
  }

  function resolveNavTitle(path: string): string | null {
    return resolveNavTitleFromMenu(path, toValue(menuItems));
  }

  return {
    activeMenuPath,
    isNavItemActive,
    isNavDescendantActive,
    resolveNavTitle,
  };
}
