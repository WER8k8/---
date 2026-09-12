#!/usr/bin/env node
/**
 * CONSOLE-REGRESSION-LOCK-01 — Trae 控制台三类红错静态门禁
 * Usage: node scripts/check-console-regression-lock.mjs
 * Contract: .project/console-regression-lock.json
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const adminRoot = path.resolve(__dirname, '..')
const repoRoot = path.resolve(adminRoot, '../..')
const lockPath = path.join(repoRoot, '.project', 'console-regression-lock.json')

function walk(dir, acc = []) {
  if (!fs.existsSync(dir)) return acc
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name)
    const st = fs.statSync(p)
    if (st.isDirectory()) {
      if (name === 'node_modules' || name === 'dist') continue
      walk(p, acc)
    } else if (name.endsWith('.vue')) acc.push(p)
  }
  return acc
}

function rel(p) {
  return path.relative(repoRoot, p).split(path.sep).join('/')
}

function fail(violations) {
  console.log(JSON.stringify({ ok: false, violations, count: violations.length }, null, 2))
  process.exit(1)
}

if (!fs.existsSync(lockPath)) {
  fail(['missing contract: .project/console-regression-lock.json'])
}

const lock = JSON.parse(fs.readFileSync(lockPath, 'utf8'))
const violations = []

// 1) ant-design-vue Modal/Drawer — v-model:visible
const modalRe = /<a-(modal|drawer)[\s\S]{0,240}?v-model:visible/gi
const srcRoot = path.join(adminRoot, 'src')
for (const file of walk(srcRoot)) {
  const text = fs.readFileSync(file, 'utf8')
  if (modalRe.test(text)) {
    violations.push(`antd modal/drawer must use v-model:open: ${rel(file)}`)
  }
  modalRe.lastIndex = 0
}

// 2) Formily — effect hooks only inside createForm.effects
const formilyRel = lock.rules?.formily_effects_in_createForm?.file
const formilyPath = path.join(repoRoot, formilyRel.replace(/\//g, path.sep))
if (!fs.existsSync(formilyPath)) {
  violations.push(`missing YdFormilyForm: ${formilyRel}`)
} else {
  const text = fs.readFileSync(formilyPath, 'utf8')
  for (const snip of lock.rules.formily_effects_in_createForm.required_snippets ?? []) {
    if (!text.includes(snip)) violations.push(`YdFormilyForm missing "${snip}"`)
  }
  const stripped = text.replace(/effects\s*\(\s*\)\s*\{[\s\S]*?\}/, '')
  if (stripped.includes('onFormValuesChange(')) {
    violations.push('YdFormilyForm: onFormValuesChange must only appear inside createForm.effects()')
  }
}

// 3) Global scan — no bare onFormValuesChange in product vue/ts (except YdFormilyForm)
const effectImportRe = /from\s+['"]@formily\/core['"]/
const bareEffectRe = /^\s*on(?:Form|Field)\w+\(/
for (const ext of ['.vue', '.ts']) {
  const root = path.join(adminRoot, 'src')
  const files = walk(root).filter((f) => f.endsWith(ext))
  for (const file of files) {
    if (path.normalize(file) === path.normalize(formilyPath)) continue
    const text = fs.readFileSync(file, 'utf8')
    if (!effectImportRe.test(text)) continue
    const lines = text.split('\n')
    let inEffects = false
    let brace = 0
    for (const line of lines) {
      if (/effects\s*\(\s*\)\s*\{/.test(line)) {
        inEffects = true
        brace = (line.match(/\{/g) || []).length - (line.match(/\}/g) || []).length
        continue
      }
      if (inEffects) {
        brace += (line.match(/\{/g) || []).length - (line.match(/\}/g) || []).length
        if (brace <= 0) inEffects = false
        continue
      }
      if (bareEffectRe.test(line) && /onFormValuesChange|onFieldValueChange|onFormMount/.test(line)) {
        violations.push(`Formily effect hook outside effects(): ${rel(file)} — ${line.trim().slice(0, 80)}`)
      }
    }
  }
}

// 4) tenants/billing — tenant_id guard
const billingRel = lock.rules?.tenant_billing_guard?.file
const billingPath = path.join(repoRoot, billingRel.replace(/\//g, path.sep))
if (!fs.existsSync(billingPath)) {
  violations.push(`missing tenants billing page: ${billingRel}`)
} else {
  const text = fs.readFileSync(billingPath, 'utf8')
  for (const snip of lock.rules.tenant_billing_guard.required_snippets ?? []) {
    if (!text.includes(snip)) violations.push(`tenants/billing.vue missing guard snippet: ${snip}`)
  }
  if (/onMounted\s*\([\s\S]*?loadBills\s*\(\s*\)/.test(text)) {
    const mountBlock = text.match(/onMounted\s*\([\s\S]*?\}\s*\)/)?.[0] ?? ''
    if (mountBlock.includes('loadBills') && !mountBlock.includes('selectedTenantId')) {
      violations.push('tenants/billing.vue onMounted must gate loadBills with selectedTenantId')
    }
  }
}

// 5) 表格 customRender 禁止 r.value（须解构 { text, record }）
for (const file of walk(srcRoot)) {
  const text = fs.readFileSync(file, 'utf8')
  if (/customRender:\s*\([^)]*\)\s*=>\s*r\.value/.test(text)) {
    violations.push(`table customRender must use { text, record }, not r.value: ${rel(file)}`)
  }
}

// 6) Modal.confirm 禁止 async onOk（须 utils/ydModal.ydConfirm + return Promise）
for (const file of walk(srcRoot)) {
  const text = fs.readFileSync(file, 'utf8')
  if (/Modal\.confirm\s*\(\s*\{[\s\S]*?async\s+onOk\s*\(/.test(text)) {
    violations.push(`use ydConfirm instead of Modal.confirm async onOk: ${rel(file)}`)
  }
}

if (violations.length) fail(violations)

console.log(
  JSON.stringify(
    {
      ok: true,
      decision_id: lock.decision_id,
      checked: {
        vue_files: walk(srcRoot).length,
        formily: formilyRel,
        billing: billingRel,
      },
    },
    null,
    2,
  ),
)
