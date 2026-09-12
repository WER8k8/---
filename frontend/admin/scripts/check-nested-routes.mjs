#!/usr/bin/env node
/**
 * 批量审计嵌套路由：父组件 router-view、Tab 与 dashboard 路径、菜单可达性
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const routerTs = fs.readFileSync(path.join(root, 'src/router/index.ts'), 'utf8')
const layoutVue = fs.readFileSync(path.join(root, 'src/layout/index.vue'), 'utf8')

const menuPaths = [...new Set([...layoutVue.matchAll(/path:'([^']+)'/g)].map((m) => m[1]))]

/** @type {{ parent: string, child: string, component: string, emptyDefault: boolean }[]} */
const nested = []
const importRe = /component:\s*\(\)\s*=>\s*import\('(@\/views\/[^']+)'\)/g
const pathRe = /path:\s*'([^']*)'/g

// 粗解析：找带 children 的块（足够发现 Tab 类问题）
const blocks = routerTs.split(/\n\s{6}\{\n\s{8}path:/)
for (const block of blocks) {
  if (!block.includes('children:')) continue
  const parentPathM = block.match(/^ '([^']+)'/)
  if (!parentPathM) continue
  const parentSeg = parentPathM[1]
  if (parentSeg.includes(':') || parentSeg.startsWith('/')) continue
  if (block.includes('appShell: true')) continue

  const compM = block.match(/component:\s*\(\)\s*=>\s*import\('(@\/views\/[^']+)'\)/)
  if (!compM) continue
  const parentComp = compM[1].replace('@/', 'src/')
  const compFile = parentComp.endsWith('.vue') ? parentComp : `${parentComp}.vue`

  const childPaths = [...block.matchAll(/\n\s{12}path:\s*'([^']*)'/g)].map((m) => m[1])
  const nonEmptyChildren = childPaths.filter((p) => p !== '')
  if (nonEmptyChildren.length === 0 && !childPaths.includes('')) continue
  const emptyDefault = childPaths.includes('')
  nested.push({
    parent: `/${parentSeg}`,
    parentComp: compFile,
    emptyDefault,
    children: childPaths.filter((p) => p !== ''),
  })
}

const issues = []

for (const row of nested) {
  const compPath = path.join(root, row.parentComp)
  if (!fs.existsSync(compPath)) {
    issues.push({ type: 'missing-parent', path: row.parent, file: row.parentComp })
    continue
  }
  const src = fs.readFileSync(compPath, 'utf8')
  if (!/<router-view/i.test(src)) {
    issues.push({ type: 'no-router-view', path: row.parent, file: row.parentComp })
  }
  if (row.emptyDefault && /push\(`\$\{[^}]+\}\/dashboard`\)|replace\([^)]*\/dashboard['"]\s*\)/.test(src)) {
    issues.push({
      type: 'tab-empty-path-mismatch',
      path: row.parent,
      file: row.parentComp,
      hint: '默认子路由 path 为空，但 Tab 推 /dashboard 会 404；应改用 useModuleTabSync 或显式 dashboard 子路径',
    })
  }
  if (/replace\([^)]*\/dashboard/.test(src) && !row.children.includes('dashboard')) {
    issues.push({ type: 'bad-redirect-dashboard', path: row.parent, file: row.parentComp })
  }
}

// 菜单路径：父级空默认子路由时，/foo 应可解析；显式 dashboard 时 /foo/dashboard 也要存在
const routePaths = new Set(['/'])
for (const m of routerTs.matchAll(/path:\s*'([^']+)'/g)) {
  const p = m[1]
  if (p.startsWith('/')) routePaths.add(p.replace(/\/+$/, '') || '/')
  else routePaths.add(`/${p}`.replace(/\/+/g, '/').replace(/\/+$/, ''))
}

function resolveable(navPath) {
  const loc = navPath.replace(/\/+$/, '') || '/'
  if (routePaths.has(loc)) return true
  for (const r of routePaths) {
    if (loc.startsWith(`${r}/`)) return true
  }
  const parts = loc.split('/')
  while (parts.length > 1) {
    parts.pop()
    const parent = parts.join('/') || '/'
    if (routePaths.has(parent)) return true
  }
  return false
}

const menuMissing = menuPaths.filter((p) => !resolveable(p))

const report = {
  nestedParents: nested.length,
  issues,
  menuMissing,
  ok: issues.length === 0 && menuMissing.length === 0,
}
console.log(JSON.stringify(report, null, 2))
process.exit(report.ok ? 0 : 1)
