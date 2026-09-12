/**
 * Shell Nav Kernel — 纯函数，无 Vue 依赖（Google: 可单测的核心逻辑层）
 * 激活态 / 标题 / 路径收集：一处计算，layout · Worktab · 全局搜索共用
 */
import { normalizeLocationPath } from '@/constants/workbenchPathCapabilities';
import type { ShellMenuGroup, ShellNavItem } from '@/types/shellNav';

/** 菜单 hub：只精确匹配，避免 /admin、/admin/system 在子路径下参与前缀竞争 */
const EXACT_ONLY_MENU_PATHS = new Set([
  '/admin',
  '/admin/ai-center',
  '/admin/system',
  '/client/dashboard',
]);

export function walkShellMenuPaths(
  items: ShellNavItem[],
  visit: (item: ShellNavItem) => void,
): void {
  for (const item of items) {
    visit(item);
    if (item.children?.length) walkShellMenuPaths(item.children, visit);
  }
}

export function collectShellMenuPaths(groups: ShellMenuGroup[]): string[] {
  const paths = new Set<string>();
  for (const group of groups) {
    walkShellMenuPaths(group.children, (item) => {
      paths.add(normalizeLocationPath(item.path));
    });
  }
  return [...paths];
}

/** 最长前缀匹配 — 同一时刻只应有一个 leaf 级 active */
export function resolveActiveMenuPath(
  routePath: string,
  groups: ShellMenuGroup[],
): string | null {
  const loc = normalizeLocationPath(routePath);
  let best: string | null = null;
  let bestLen = -1;
  for (const group of groups) {
    walkShellMenuPaths(group.children, (item) => {
      const np = normalizeLocationPath(item.path);
      const prefixMatch =
        !EXACT_ONLY_MENU_PATHS.has(np) && np !== '/' && loc.startsWith(`${np}/`);
      if (loc === np || prefixMatch) {
        if (np.length > bestLen) {
          bestLen = np.length;
          best = np;
        }
      }
    });
  }
  return best;
}

export function resolveNavTitleFromMenu(
  routePath: string,
  groups: ShellMenuGroup[],
): string | null {
  const loc = normalizeLocationPath(routePath);
  let matchedPath: string | null = null;
  let matchedTitle: string | null = null;
  for (const group of groups) {
    walkShellMenuPaths(group.children, (item) => {
      const np = normalizeLocationPath(item.path);
      const prefixMatch =
        !EXACT_ONLY_MENU_PATHS.has(np) && np !== '/' && loc.startsWith(`${np}/`);
      if (loc === np || prefixMatch) {
        if (!matchedPath || np.length > matchedPath.length) {
          matchedPath = np;
          matchedTitle = item.title;
        }
      }
    });
  }
  return matchedTitle;
}

export function isShellNavItemActive(
  item: ShellNavItem,
  activePath: string | null,
): boolean {
  if (!activePath) return false;
  return normalizeLocationPath(item.path) === normalizeLocationPath(activePath);
}

export function isShellNavDescendantActive(
  item: ShellNavItem,
  activePath: string | null,
): boolean {
  if (!item.children?.length) return isShellNavItemActive(item, activePath);
  if (!activePath) return false;
  const root = normalizeLocationPath(item.path);
  const hit = normalizeLocationPath(activePath);
  return hit === root || hit.startsWith(`${root}/`);
}
