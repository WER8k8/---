/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export type SearchMenuRow = {
  title: string
  path: string
  icon: string
  group: string
}

type MenuNavItem = {
  title: string
  path: string
  icon?: string
  name?: string
  children?: MenuNavItem[]
}

type MenuGroup = {
  title?: string
  children: MenuNavItem[]
}

function walk(items: MenuNavItem[], group: string, out: SearchMenuRow[]) {
  for (const item of items) {
    if (item.children?.length) {
      walk(item.children, item.title || group, out)
      continue
    }
    if (!item.path || !item.title) continue
    out.push({
      title: item.title,
      path: item.path,
      icon: item.icon || 'AppstoreOutlined',
      group: group || '导航',
    })
  }
}

/** 侧栏菜单 → 搜索索引（去重 path） */
export function flattenMenuNav(groups: MenuGroup[]): SearchMenuRow[] {
  const out: SearchMenuRow[] = []
  for (const g of groups) {
    walk(g.children || [], g.title || '导航', out)
  }
  const seen = new Set<string>()
  return out.filter((row) => {
    if (seen.has(row.path)) return false
    seen.add(row.path)
    return true
  })
}

/** 页面 meta 标题 → 搜索条目 */
export function pageTitlesToSearchRows(
  pageTitles: Record<string, { title: string; subtitle?: string }>,
): SearchMenuRow[] {
  return Object.entries(pageTitles).map(([path, meta]) => ({
    title: meta.title,
    path,
    icon: 'FileOutlined',
    group: meta.subtitle || '页面',
  }))
}
