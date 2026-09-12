#!/usr/bin/env node
/**
 * W6 · 90 秒送检路径静态门禁 — docs/youding-omni-pro-design-LOCKED.md §10
 * Usage: node scripts/check-demo-rehearsal-path.mjs
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const adminRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const viewsDir = path.join(adminRoot, 'src/views')
const layoutPath = path.join(adminRoot, 'src/layout/index.vue')
const uiPrefsPath = path.join(adminRoot, 'src/stores/uiPreferences.ts')
const loginPath = path.join(viewsDir, 'login/index.vue')
const routerPath = path.join(adminRoot, 'src/router/index.ts')

/** 与 demo-rehearsal.vue LOCKED_DEMO_STEPS 对齐 */
const STEPS = [
  { id: 1, path: '/login', vue: 'login/index.vue', checks: ['brandHero', 'noPlaceholder'] },
  { id: 2, path: '/admin/dashboard', vue: 'admin/dashboard.vue', checks: ['ydPage', 'ydDataTable', 'inquiryClick'] },
  { id: 3, path: '/admin/tenants', vue: 'tenants/dashboard.vue', checks: ['ydPage', 'ydDataTable', 'columnSettings'] },
  { id: 4, path: '/inquiries', vue: 'inquiries/index.vue', checks: ['ydPage', 'ydDataTable', 'columnSettings'] },
  { id: 5, path: '/client/dashboard', vue: 'client/dashboard.vue', checks: ['ydPage', 'clientShell'] },
  { id: 6, path: '/agent/performance', vue: 'agent/performance.vue', checks: ['ydPage', 'agentShell'] },
]

const FORBIDDEN = /敬请期待|对接中|演示，可对接|message\.info\(/

function read(p) {
  return fs.readFileSync(p, 'utf8')
}

function routeRegistered(routePath) {
  const base = routePath.split('?')[0]
  const router = read(routerPath)
  const segments = base.replace(/^\//, '').split('/').filter(Boolean)
  if (segments.length === 0) return router.includes("path: 'login'") || router.includes('path: "/login"')
  const last = segments[segments.length - 1]
  return router.includes(`'${last}'`) || router.includes(`"${last}"`) || router.includes(`path: '${base}'`)
}

function mainListHasBareTable(src) {
  const template = src.match(/<template[^>]*>([\s\S]*)<\/template>/)?.[1] ?? src
  const withoutDrawers = template.replace(/<a-drawer[\s\S]*?<\/a-drawer>/g, '')
  return /<a-table[\s>]/.test(withoutDrawers)
}

const layout = read(layoutPath)
const uiPrefs = read(uiPrefsPath)
const issues = []

for (const step of STEPS) {
  const file = path.join(viewsDir, step.vue)
  if (!fs.existsSync(file)) {
    issues.push({ step: step.id, path: step.path, hit: `缺少视图 ${step.vue}` })
    continue
  }
  if (!routeRegistered(step.path)) {
    issues.push({ step: step.id, path: step.path, hit: '路由未注册' })
  }
  const src = read(file)
  if (FORBIDDEN.test(src)) {
    issues.push({ step: step.id, path: step.path, hit: '含送检零容忍文案' })
  }
  if (step.checks.includes('ydPage') && !src.includes('<YdPage')) {
    issues.push({ step: step.id, path: step.path, hit: '缺少 YdPage' })
  }
  if (step.checks.includes('ydDataTable')) {
    if (!src.includes('YdDataTable')) {
      issues.push({ step: step.id, path: step.path, hit: '主列表缺少 YdDataTable' })
    }
    if (mainListHasBareTable(src)) {
      issues.push({ step: step.id, path: step.path, hit: '主区域仍含裸 a-table' })
    }
  }
  if (step.checks.includes('columnSettings') && !src.includes('YdTableColumnSettings')) {
    issues.push({ step: step.id, path: step.path, hit: '缺少 YdTableColumnSettings' })
  }
  if (step.checks.includes('inquiryClick') && !src.includes("router.push('/inquiries')")) {
    issues.push({ step: step.id, path: step.path, hit: '待办询盘未链至 /inquiries' })
  }
  if (step.checks.includes('brandHero') && !src.includes('brand-hero') && !src.includes('TenantLoginPanel')) {
    issues.push({ step: step.id, path: step.path, hit: '登录页缺少 brand-hero 结构' })
  }
  if (step.checks.includes('noPlaceholder')) {
    const login = read(loginPath)
    if (/placeholder="[^"]*(TODO|lorem|示例文案)/i.test(login)) {
      issues.push({ step: step.id, path: step.path, hit: '登录含占位 placeholder' })
    }
  }
}

if (!layout.includes('ThemeSettingsDrawer')) {
  issues.push({ step: 'shell', path: 'layout', hit: '缺少 ThemeSettingsDrawer' })
}
if (!layout.includes('setAccentRole')) {
  issues.push({ step: 'shell', path: 'layout', hit: '路由未同步 accentRole' })
}
if (!layout.includes('GlobalSearch')) {
  issues.push({ step: 'shell', path: 'layout', hit: '缺少 GlobalSearch (Ctrl+K)' })
}
if (!uiPrefs.includes("'#2563eb'") || !uiPrefs.includes("'#0d9488'")) {
  issues.push({ step: 'shell', path: 'uiPreferences', hit: '三角色 accent 品牌色未写入 DOM token' })
}

const demoRehearsal = path.join(viewsDir, 'admin/demo-rehearsal.vue')
if (!fs.existsSync(demoRehearsal) || !read(demoRehearsal).includes('LOCKED_DEMO_STEPS')) {
  issues.push({ step: 'meta', path: '/admin/demo-rehearsal', hit: '彩排页缺少 LOCKED 步骤定义' })
}

const report = {
  ok: issues.length === 0,
  spec: 'youding-omni-pro-design-LOCKED.md §10',
  steps: STEPS.length,
  issues,
}

console.log(JSON.stringify(report, null, 2))
process.exit(report.ok ? 0 : 1)
