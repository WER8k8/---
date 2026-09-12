#!/usr/bin/env node
/**
 * ROLE-SHELL-LOCK-01 — 租户 / 超管 / 代理 壳隔离 + 入口 SSOT 校验
 * Usage: node scripts/check-role-shell-lock.mjs
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const adminRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(adminRoot, '../..')
const lockPath = path.join(repoRoot, '.project', 'role-shell-lock.json')

function readText(relFromAdmin) {
  const p = path.join(adminRoot, relFromAdmin)
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : ''
}

function repoPath(rel) {
  return path.join(repoRoot, rel.replace(/\//g, path.sep))
}

function resolveAliasImport(spec) {
  const normalized = spec.replace(/^@\//, 'src/')
  return path.join(adminRoot, normalized.replace(/\//g, path.sep))
}

function fail(violations) {
  console.log(JSON.stringify({ ok: false, violations }, null, 2))
  process.exit(1)
}

if (!fs.existsSync(lockPath)) {
  fail(['missing contract: .project/role-shell-lock.json'])
}

const lock = JSON.parse(fs.readFileSync(lockPath, 'utf8'))
const violations = []

const ssot = readText('src/constants/roleShellLock.ts')
if (!ssot.includes('ROLE_SHELL_LOCK_ID')) {
  violations.push('missing ROLE_SHELL_LOCK_ID in roleShellLock.ts')
}
for (const key of Object.values(lock.worktab_storage_keys ?? {})) {
  if (typeof key === 'string' && key.startsWith('uj-worktabs') && !ssot.includes(key)) {
    violations.push(`roleShellLock.ts missing worktab key: ${key}`)
  }
}

for (const rel of lock.forbidden_new_files ?? []) {
  const abs = repoPath(rel)
  if (fs.existsSync(abs)) {
    violations.push(`forbidden path exists (do not create): ${rel}`)
  }
}

const routerTs = readText('src/router/index.ts')
if (!routerTs.includes('decideRoleShellNavigation')) {
  violations.push('router must use decideRoleShellNavigation from roleShellLock.ts')
}
if (routerTs.includes('tenantLegacyRedirects')) {
  violations.push('router must not define inline tenantLegacyRedirects (use roleShellLock SSOT)')
}
if (routerTs.includes('PLATFORM_MEDIA_LEGACY_REDIRECTS')) {
  violations.push('router must not import PLATFORM_MEDIA_LEGACY_REDIRECTS directly')
}

for (const banned of lock.forbidden_router_imports ?? []) {
  if (routerTs.includes(banned)) {
    violations.push(`router must not import forbidden wrapper: ${banned}`)
  }
}

for (const entry of lock.shell_entries ?? []) {
  const forbiddenShort = entry.forbidden_component
    ?.replace(/^frontend\/admin\/src\//, '')
    ?.replace(/^frontend\/admin\//, '')
  if (forbiddenShort && routerTs.includes(forbiddenShort)) {
    violations.push(`router references forbidden component for ${entry.id}: ${forbiddenShort}`)
  }
  const comp = entry.component ?? entry.route_component
  if (comp) {
    const vueRel = comp
      .replace(/^frontend\/admin\/src\//, '')
      .replace(/^frontend\/admin\//, '')
    const alias = `@/${vueRel}`
    if (!routerTs.includes(alias) && !routerTs.includes(vueRel)) {
      violations.push(`router must wire ${entry.id} to ${alias}`)
    }
    if (!fs.existsSync(repoPath(comp))) {
      violations.push(`required component missing for ${entry.id}: ${comp}`)
    }
  }
  if (entry.code_dir && !fs.existsSync(repoPath(entry.code_dir))) {
    violations.push(`required code dir missing for ${entry.id}: ${entry.code_dir}`)
  }
}

const dynamicImportRe = /import\s*\(\s*['"](@\/[^'"]+)['"]\s*\)/g
let m
while ((m = dynamicImportRe.exec(routerTs)) !== null) {
  const target = resolveAliasImport(m[1])
  if (!fs.existsSync(target)) {
    violations.push(`router dynamic import target missing: ${m[1]} (from router/index.ts)`)
  }
}

const workTabsTs = readText('src/stores/workTabs.ts')
if (!workTabsTs.includes('bindRoleStorage')) {
  violations.push('workTabs store must implement bindRoleStorage')
}
if (!workTabsTs.includes('workTabStorageKeyForRole')) {
  violations.push('workTabs must use workTabStorageKeyForRole')
}

const layoutVue = readText('src/layout/index.vue')
if (layoutVue.includes("path:'/client/traffic'") || layoutVue.includes("path: '/client/traffic'")) {
  violations.push('platform admin menu must not link to /client/traffic (use /operations/traffic)')
}

const loginCopy = readText('src/constants/loginPortalCopy.ts')
if (!loginCopy.includes("from '@/constants/roleShellLock'")) {
  violations.push('loginPortalCopy must re-export homePathForRole/resolveLoginTarget from roleShellLock')
}

if (!routerTs.includes("redirect: '/client/today'") && !routerTs.includes('redirect: "/client/today"')) {
  violations.push('client shell default redirect must be /client/today')
}
if (!routerTs.includes("path: 'today'") && !routerTs.includes('path: "today"')) {
  violations.push('router must register /client/today route for tenant home')
}

if (violations.length) fail(violations)

console.log(
  JSON.stringify(
    {
      ok: true,
      decision_id: lock.decision_id,
      personas: (lock.personas ?? []).map((p) => p.id),
      shell_entries: (lock.shell_entries ?? []).map((e) => e.id),
      worktab_keys: Object.values(lock.worktab_storage_keys ?? {}).filter((k) =>
        String(k).startsWith('uj-worktabs'),
      ),
    },
    null,
    2,
  ),
)
