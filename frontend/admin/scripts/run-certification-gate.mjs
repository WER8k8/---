#!/usr/bin/env node
/**
 * 省级软件评测 — 管理端一键门禁（聚合 audit / nav / nested / corrupt / interactive）
 * Usage: node scripts/run-certification-gate.mjs
 * Exit 1 if any blocking gate fails.
 */
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import fs from 'node:fs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const adminRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(adminRoot, '../..')
const outPath = path.join(repoRoot, 'docs', 'certification-gate-admin-latest.json')

function isDevStackUp() {
  const probe = spawnSync(
    process.execPath,
    [
      '-e',
      `Promise.all([
        fetch('http://127.0.0.1:8001/api/v1/health',{signal:AbortSignal.timeout(2500)}).then(r=>r.status<500).catch(()=>false),
        fetch('http://127.0.0.1:3000/tenant?__tenant=dev.local&lpro=1',{signal:AbortSignal.timeout(2500)}).then(r=>r.status<500).catch(()=>false),
      ]).then(([a,n])=>process.exit(a&&n?0:1)).catch(()=>process.exit(1))`,
    ],
    { encoding: 'utf8', timeout: 8000 },
  )
  return probe.status === 0
}

function runRepoAudit(name, scriptRel, extraArgs = []) {
  const py = path.join(repoRoot, 'backend', '.venv', 'Scripts', 'python.exe')
  const pyCmd = fs.existsSync(py) ? py : 'python'
  const script = path.join(repoRoot, scriptRel)
  const res = spawnSync(pyCmd, [script, ...extraArgs], {
    cwd: repoRoot,
    encoding: 'utf8',
    maxBuffer: 20 * 1024 * 1024,
  })
  const raw = (res.stdout || '').trim()
  let json = null
  try {
    const start = raw.indexOf('{')
    const end = raw.lastIndexOf('}')
    if (start >= 0 && end > start) json = JSON.parse(raw.slice(start, end + 1))
  } catch {
    json = { parseError: true, stdout: raw.slice(0, 500) }
  }
  const p0 = json?.summary?.P0 ?? json?.issues?.filter?.((i) => i.severity === 'P0')?.length ?? 0
  const block = res.status !== 0 || json?.ok === false || p0 > 0
  return {
    script: name,
    ok: !block,
    blocking: block,
    exitCode: res.status ?? 1,
    summary: json?.ok === true ? 'ok' : `P0=${p0} exit=${res.status}`,
    raw: json,
    skipped: false,
  }
}

const scripts = [
  { name: 'check-login-entry-lock', file: 'check-login-entry-lock.mjs', blockOn: (r) => r.ok === false },
  { name: 'check-role-shell-lock', file: 'check-role-shell-lock.mjs', blockOn: (r) => r.ok === false },
  { name: 'check-console-regression-lock', file: 'check-console-regression-lock.mjs', blockOn: (r) => r.ok === false },
  { name: 'audit-page-stubs', file: 'audit-page-stubs.mjs', blockOn: (r) => (r.P0 ?? 0) > 0 || (r.P1 ?? 0) > 0 || (r.P2 ?? 0) > 0 },
  { name: 'check-nav-routes', file: 'check-nav-routes.mjs', blockOn: (r) => (r.missing?.length ?? 0) > 0 },
  { name: 'check-nested-routes', file: 'check-nested-routes.mjs', blockOn: (r) => r.ok === false },
  { name: 'find-corrupt-vue', file: 'find-corrupt-vue.mjs', blockOn: (r) => (r.corrupt ?? 0) > 0 },
  { name: 'check-interactive-stubs', file: 'check-interactive-stubs.mjs', blockOn: (r) => (r.menuLinked ?? 0) > 0 },
  { name: 'check-demo-rehearsal-path', file: 'check-demo-rehearsal-path.mjs', blockOn: (r) => r.ok === false },
]

function runScript(file) {
  const res = spawnSync(process.execPath, [path.join(__dirname, file)], {
    cwd: adminRoot,
    encoding: 'utf8',
    maxBuffer: 20 * 1024 * 1024,
  })
  const raw = (res.stdout || '').trim()
  let json = null
  try {
    const start = raw.indexOf('{')
    const end = raw.lastIndexOf('}')
    if (start >= 0 && end > start) json = JSON.parse(raw.slice(start, end + 1))
  } catch {
    json = { parseError: true, stdout: raw.slice(0, 500), stderr: (res.stderr || '').slice(0, 500) }
  }
  return { exitCode: res.status ?? 1, json, ok: res.status === 0 }
}

const results = []
let blocked = false

for (const s of scripts) {
  const { exitCode, json, ok } = runScript(s.file)
  const block = json && s.blockOn(json)
  if (block) blocked = true
  results.push({
    script: s.name,
    ok: ok && !block,
    blocking: block,
    exitCode,
    summary: summarize(s.name, json),
    raw: json,
  })
}

results.push(runRepoAudit('no-fake-delivery', 'scripts/validate-no-fake-delivery.py'))
if (results[results.length - 1].blocking) blocked = true

const stackUp = isDevStackUp()
if (stackUp) {
  results.push(runRepoAudit('tenant-seo-audit', 'scripts/validate-tenant-seo-audit.py', ['--tenant', 'dev.local']))
  results.push(
    runRepoAudit('tenant-geo-audit', 'scripts/validate-tenant-geo-audit.py', [
      '--tenant',
      'dev.local',
      '--skip-probes',
    ]),
  )
  if (results.some((r) => r.blocking)) blocked = true
} else {
  results.push({
    script: 'tenant-seo-audit',
    ok: true,
    blocking: false,
    exitCode: 0,
    summary: 'skipped — dev stack not up',
    raw: { skipped: true },
    skipped: true,
  })
  results.push({
    script: 'tenant-geo-audit',
    ok: true,
    blocking: false,
    exitCode: 0,
    summary: 'skipped — dev stack not up',
    raw: { skipped: true },
    skipped: true,
  })
}

const report = {
  generatedAt: new Date().toISOString(),
  target: '省级软件评测 — 管理端功能门禁',
  ready: !blocked,
  blocked,
  gates: results,
  recommendation: blocked
    ? '存在阻断项：须清零 P0/P1、路由缺失、Vue 损坏后再提交评测'
    : '管理端门禁通过；继续完成后端 preflight、测试报告实填、PM 签字与性能/安全附件',
}

fs.mkdirSync(path.dirname(outPath), { recursive: true })
fs.writeFileSync(outPath, JSON.stringify(report, null, 2), 'utf8')

console.log(JSON.stringify({
  ready: report.ready,
  blocked: report.blocked,
  gates: results.map((g) => ({ script: g.script, ok: g.ok, blocking: g.blocking, summary: g.summary })),
  outPath,
}, null, 2))

process.exit(blocked ? 1 : 0)

function summarize(name, j) {
  if (!j || j.parseError) return 'parse failed'
  switch (name) {
    case 'check-login-entry-lock':
      return j.ok ? 'ok' : `violations=${j.violations?.length ?? '?'}`
    case 'check-role-shell-lock':
      return j.ok ? 'ok' : `violations=${j.violations?.length ?? '?'}`
    case 'check-console-regression-lock':
      return j.ok ? 'ok' : `violations=${j.violations?.length ?? '?'}`
    case 'audit-page-stubs':
      return `P0=${j.P0 ?? '?'} P1=${j.P1 ?? '?'} P2=${j.P2 ?? '?'}`
    case 'check-nav-routes':
      return `missing=${j.missing?.length ?? 0}/${j.total ?? '?'}`
    case 'check-nested-routes':
      return `issues=${j.issues?.length ?? 0}`
    case 'find-corrupt-vue':
      return `corrupt=${j.corrupt ?? '?'}`
    case 'check-interactive-stubs':
      return `menuLinked=${j.menuLinked ?? '?'} flagged=${j.items?.length ?? '?'}`
    case 'check-demo-rehearsal-path':
      return `issues=${j.issues?.length ?? 0}`
    case 'tenant-seo-audit':
    case 'tenant-geo-audit':
      return j?.skipped ? 'skipped' : j?.ok === true ? 'ok' : `P0 issues`
    case 'no-fake-delivery':
      return j?.ok === true ? 'ok' : `P0=${j?.p0_count ?? '?'}`
    default:
      return JSON.stringify(j).slice(0, 120)
  }
}
