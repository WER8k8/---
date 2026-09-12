#!/usr/bin/env node
/**
 * LOGIN-LOCK-01 — 管理端唯一超管登录入口校验
 * Usage: node scripts/check-login-entry-lock.mjs
 * Contract: .project/login-entry-lock.json
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const adminRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(adminRoot, '../..')
const lockPath = path.join(repoRoot, '.project', 'login-entry-lock.json')

function readText(relFromAdmin) {
  const p = path.join(adminRoot, relFromAdmin)
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : ''
}

function fail(violations) {
  console.log(JSON.stringify({ ok: false, violations }, null, 2))
  process.exit(1)
}

if (!fs.existsSync(lockPath)) {
  fail(['missing contract: .project/login-entry-lock.json'])
}

const lock = JSON.parse(fs.readFileSync(lockPath, 'utf8'))
const violations = []

for (const rel of lock.forbidden?.forbidden_new_files ?? []) {
  const abs = path.join(repoRoot, rel.replace(/\//g, path.sep))
  if (fs.existsSync(abs)) violations.push(`forbidden file exists: ${rel}`)
}

const scanFiles = [
  'src/constants/loginPortalCopy.ts',
  'src/router/index.ts',
  'src/views/login/index.vue',
  'src/views/landing/index.vue',
]

const forbiddenPatterns = lock.forbidden?.patterns_in_product_code ?? []
for (const rel of scanFiles) {
  const text = readText(rel)
  if (!text) continue
  for (const pat of forbiddenPatterns) {
    if (text.includes(pat)) {
      violations.push(`forbidden pattern "${pat}" in ${rel}`)
    }
  }
}

const routerTs = readText('src/router/index.ts')
const legacy = lock.allowed?.legacy_redirects_only ?? []
for (const route of legacy) {
  if (!routerTs.includes(`'${route}'`) && !routerTs.includes(`"${route}"`)) {
    violations.push(`missing legacy redirect route: ${route}`)
  }
}

if (!routerTs.includes("path: '/login'") && !routerTs.includes('path: "/login"')) {
  violations.push('missing primary /login route')
}

const loginVue = readText('src/views/login/index.vue')
if (!loginVue.includes('data-portal="platform"')) {
  violations.push('login page must be fixed platform portal (data-portal="platform")')
}
if (
  loginVue.includes('normalizeLoginPortal') ||
  loginVue.includes(':data-portal="loginPortal"') ||
  loginVue.includes('DEV_PORTAL_CREDENTIALS')
) {
  violations.push('login page must not use multi-portal switching')
}

const loginSecretLeakPatterns = [
  'admin123',
  'tenant123',
  'agent123',
  '本地三套',
  'DEV_LOGIN_ACCOUNTS',
]
for (const pat of loginSecretLeakPatterns) {
  if (loginVue.includes(pat)) {
    violations.push(`login page must not expose dev credentials: "${pat}"`)
  }
}

const copyTs = readText('src/constants/loginPortalCopy.ts')
for (const required of ['PLATFORM_LOGIN_COPY', 'LOGIN_PATH', 'homePathForRole']) {
  if (!copyTs.includes(required)) {
    violations.push(`loginPortalCopy.ts missing export/symbol: ${required}`)
  }
}

if (violations.length) fail(violations)

console.log(
  JSON.stringify(
    {
      ok: true,
      decision_id: lock.decision_id,
      login_route: lock.allowed?.login_route,
      checked_files: scanFiles.length,
      legacy_redirects: legacy.length,
    },
    null,
    2,
  ),
)
