#!/usr/bin/env node
/**
 * 扫描 views 下占位/假数据/无 API 页面，输出分级清单
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const viewsDir = path.join(root, 'src/views')

const STUB_MARKERS = [
  /<!--\s*模板页面：待定制\s*-->/,
  /setTimeout\s*\(\s*resolve/,
  /Math\.random\s*\(\s*\)/, // 仅裸 random()；id 用 toString(36) 不命中
  /chart-placeholder/,
  /message\.info\s*\(\s*['"].*开发中/,
  /API不可用，使用本地数据/,
  /演示数据/,
]

const API_MARKERS = [
  /\bapiGet\b/,
  /\bapiPost\b/,
  /\bapiPut\b/,
  /\bapiDelete\b/,
  /\bpageGet\b/,
  /\busePageData\b/,
  /\bfetch\s*\(\s*['"`]\/api/,
  /\bfetch\s*\(\s*['"`]https?:\/\//,
  /\bapi\.(get|post|put|delete|patch)\b/,
  /from\s+['"]@\/api['"]/,
  /from\s+['"]@\/api\/[^'"]+['"]/,
  /\baxios\.(get|post|put|delete|patch)\b/,
  /\busePageData\b|\bpageGet\b/,
  /from\s+['"]@\/utils\/api['"]/,
  /\buseClientTodayThree\b/,
  /unwrapApiData|unwrapFetchedJson/,
  /productsAPI|v2rayAPI|systemAPI|aiGenerateAPI/,
  /AdminAuditLogTable/,
]

/** 合法静态页：不计入 P2 */
const AUDIT_EXCLUDE = new Set([
  'NotFound.vue',
  'access-denied.vue',
  'login/oauth-callback.vue',
  'login/index.vue',
  'PrivacyPolicy.vue',
  'TermsOfService.vue',
  'admin/components/AdminModulePlaceholder.vue',
  'client/layout.vue',
  'agent/layout.vue',
])

function isExcluded(rel) {
  if (AUDIT_EXCLUDE.has(rel)) return true
  if (rel.startsWith('templates/')) return true
  return false
}

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name)
    const st = fs.statSync(p)
    if (st.isDirectory()) walk(p, out)
    else if (name.endsWith('.vue')) out.push(p)
  }
  return out
}

function isLayoutShell(src) {
  const hasRv = /<router-view/i.test(src)
  const lines = src.split('\n').filter((l) => l.trim() && !l.trim().startsWith('//'))
  const body = src.replace(/<script[\s\S]*<\/script>/gi, '').replace(/<style[\s\S]*<\/style>/gi, '')
  const textLen = body.replace(/<[^>]+>/g, '').trim().length
  return hasRv && textLen < 80
}

function classify(file, src) {
  const rel = path.relative(viewsDir, file).replace(/\\/g, '/')
  if (isExcluded(rel)) return null
  if (isLayoutShell(src)) return null

  const hasStubComment = /<!--\s*模板页面：待定制\s*-->/.test(src)
  const hasApi = API_MARKERS.some((re) => re.test(src))
  const stubHits = STUB_MARKERS.filter((re) => re.test(src)).map((re) => re.source)
  const hardcodedStats = /const\s+st\s*=\s*\[|statCards\s*=\s*ref\s*\(\s*\[|stats\s*=\s*ref\s*\(\s*\[/.test(src)
  const mainLayout = /<MainLayout/i.test(src)

  let tier = 'P3'
  const issues = []

  if (mainLayout) {
    tier = 'P0'
    issues.push('MainLayout双壳/遗留页')
  }
  if (hasStubComment && !hasApi) {
    tier = 'P1'
    issues.push('待定制且无API')
  } else if (hasStubComment && hasApi) {
    tier = 'P2'
    issues.push('待定制但有API尝试')
  } else if (!hasApi && hardcodedStats) {
    tier = tier === 'P0' ? 'P0' : 'P1'
    issues.push('纯静态假数据')
  } else if (!hasApi) {
    tier = tier === 'P0' ? 'P0' : 'P2'
    issues.push('无API调用')
  } else if (stubHits.length) {
    tier = tier === 'P3' ? 'P2' : tier
    issues.push(...stubHits.slice(0, 3))
  }

  if (issues.length === 0) return null
  return { path: rel, tier, issues, hasApi }
}

const files = walk(viewsDir)
const rows = files.map((f) => classify(f, fs.readFileSync(f, 'utf8'))).filter(Boolean)

const byTier = { P0: [], P1: [], P2: [] }
for (const r of rows) {
  if (r.tier === 'P0') byTier.P0.push(r)
  else if (r.tier === 'P1') byTier.P1.push(r)
  else byTier.P2.push(r)
}

const report = {
  totalVue: files.length,
  flagged: rows.length,
  P0: byTier.P0.length,
  P1: byTier.P1.length,
  P2: byTier.P2.length,
  items: rows.sort((a, b) => a.tier.localeCompare(b.tier) || a.path.localeCompare(b.path)),
}

console.log(JSON.stringify(report, null, 2))
process.exit(byTier.P0.length ? 1 : 0)
