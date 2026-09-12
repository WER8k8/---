#!/usr/bin/env node
/**
 * 管理端任务看板 CLI（消费 docs/admin-route-task-board.json）
 * 用法：
 *   node scripts/admin-task-board.mjs validate
 *   node scripts/admin-task-board.mjs list [--pool=frontend] [--json]
 *   node scripts/admin-task-board.mjs next [--pool=fullstack]   # 按 priority 数值升序领下一条（跳过 docs/.task-board/completed-ids.json）
 *   node scripts/admin-task-board.mjs roll [--limit=5]          # 「滚动」输出待领任务队列
 *   node scripts/admin-task-board.mjs done --id=<taskId>        # 标记完成，后续 next/roll 不再出现
 */
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..')
const BOARD = join(ROOT, 'docs', 'admin-route-task-board.json')
const STATE_DIR = join(ROOT, 'docs', '.task-board')
const COMPLETED_IDS = join(STATE_DIR, 'completed-ids.json')

function loadCompletedIds() {
  if (!existsSync(COMPLETED_IDS)) return new Set()
  try {
    const raw = JSON.parse(readFileSync(COMPLETED_IDS, 'utf8'))
    return new Set(Array.isArray(raw) ? raw : [])
  } catch {
    return new Set()
  }
}

function filterPending(tasks, completed) {
  return tasks.filter((t) => !completed.has(t.id))
}

function loadBoard() {
  if (!existsSync(BOARD)) {
    console.error('Missing:', BOARD)
    process.exit(1)
  }
  return JSON.parse(readFileSync(BOARD, 'utf8'))
}

function validate(data) {
  const errs = []
  if (!data.schema_version) errs.push('missing schema_version')
  if (!Array.isArray(data.tasks)) errs.push('tasks must be array')
  const ids = new Set()
  for (const t of data.tasks || []) {
    if (!t.id) errs.push('task without id')
    if (ids.has(t.id)) errs.push(`duplicate id: ${t.id}`)
    ids.add(t.id)
    if (!t.route) errs.push(`task ${t.id}: missing route`)
    if (!Array.isArray(t.acceptance)) errs.push(`task ${t.id}: acceptance must be array`)
    if (t.priority != null && typeof t.priority !== 'number') errs.push(`task ${t.id}: priority must be number`)
  }
  if (errs.length) {
    console.error('Validation failed:\n', errs.join('\n'))
    process.exit(1)
  }
  console.log(`OK: ${data.tasks.length} tasks, schema ${data.schema_version}`)
}

function list(data, pool, asJson, pendingOnly) {
  const completed = pendingOnly ? loadCompletedIds() : null
  let ts = data.tasks
  if (pool) ts = ts.filter((t) => (t.owner_pool || data.task_defaults?.owner_pool) === pool)
  if (completed) ts = filterPending(ts, completed)
  ts = [...ts].sort((a, b) => (a.priority ?? 999) - (b.priority ?? 999))
  if (asJson) {
    console.log(JSON.stringify(ts, null, 2))
    return
  }
  for (const t of ts) {
    const sec = (t.api_sections || []).join(',') || '—'
    console.log(
      `[${t.priority ?? '—'}] ${t.id}\t${t.route}\t§${sec}\t${t.title}`
    )
  }
}

function nextTask(data, pool) {
  const completed = loadCompletedIds()
  let ts = filterPending(data.tasks, completed)
  if (pool) ts = ts.filter((t) => (t.owner_pool || data.task_defaults?.owner_pool) === pool)
  const sorted = [...ts].sort((a, b) => (a.priority ?? 999) - (b.priority ?? 999))
  const t = sorted[0]
  if (!t) {
    console.log('{}')
    return
  }
  console.log(JSON.stringify(t, null, 2))
}

function roll(data, limit) {
  const completed = loadCompletedIds()
  const pending = filterPending(data.tasks, completed)
  const sorted = [...pending].sort((a, b) => (a.priority ?? 999) - (b.priority ?? 999))
  const slice = sorted.slice(0, limit)
  console.log(
    JSON.stringify(
      { queue: slice, total: data.tasks.length, pending: pending.length, completed: completed.size },
      null,
      2
    )
  )
}

function markDone(taskId) {
  if (!taskId) {
    console.error('Usage: done --id=<taskId>')
    process.exit(1)
  }
  mkdirSync(STATE_DIR, { recursive: true })
  const set = loadCompletedIds()
  set.add(taskId)
  writeFileSync(COMPLETED_IDS, JSON.stringify([...set].sort(), null, 2), 'utf8')
  console.log('Marked done:', taskId, '→', COMPLETED_IDS)
}

const [cmd, ...rest] = process.argv.slice(2)
const opts = Object.fromEntries(
  rest.filter((x) => x.startsWith('--')).map((x) => {
    const [k, v] = x.slice(2).split('=')
    return [k, v === undefined ? true : v]
  })
)

const data = loadBoard()

switch (cmd) {
  case 'validate':
    validate(data)
    break
  case 'list':
    list(
      data,
      opts.pool,
      opts.json === true || opts.json === '',
      opts.pending === true || opts.pending === ''
    )
    break
  case 'next':
    nextTask(data, opts.pool)
    break
  case 'roll':
    roll(data, Math.min(100, parseInt(String(opts.limit || '10'), 10) || 10))
    break
  case 'done':
    markDone(opts.id)
    break
  default:
    console.log(
      `Usage: validate | list [--pool=] [--json] [--pending] | next [--pool=] | roll [--limit=N] | done --id=`
    )
    process.exit(cmd ? 1 : 0)
}
