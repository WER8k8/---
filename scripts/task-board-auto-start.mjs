#!/usr/bin/env node
/**
 * 全自动开始：校验看板 → 领取队首任务 → 写入会话文件 →（可选）启动 admin dev
 *   node scripts/task-board-auto-start.mjs
 *   node scripts/task-board-auto-start.mjs --no-dev
 */
import { execSync, spawn } from 'child_process'
import { writeFileSync, mkdirSync, createWriteStream, appendFileSync } from 'fs'
import { dirname, join } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = join(__dirname, '..')
const STATE_DIR = join(ROOT, 'docs', '.task-board')
const ACTIVE = join(STATE_DIR, 'active-task.json')
const SESSION = join(STATE_DIR, 'session.json')

process.chdir(ROOT)

const noDev = process.argv.includes('--no-dev')

function run(cmd) {
  return execSync(cmd, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'inherit'] })
}

console.log('=== Task board: validate ===')
run('node scripts/admin-task-board.mjs validate')

console.log('\n=== Task board: next (claim head) ===')
const nextJson = run('node scripts/admin-task-board.mjs next').trim()
const task = JSON.parse(nextJson || '{}')

mkdirSync(STATE_DIR, { recursive: true })
const session = {
  startedAt: new Date().toISOString(),
  pid: process.pid,
  activeTask: task.id ? task : null,
  devServer: null,
}
writeFileSync(ACTIVE, JSON.stringify(task, null, 2), 'utf8')
writeFileSync(SESSION, JSON.stringify(session, null, 2), 'utf8')

console.log('\n已锁定任务 →', ACTIVE)
console.log(JSON.stringify(task, null, 2))

const devBase = 'http://127.0.0.1:5173'

console.log('\n--- 验收步骤（全自动流程）---')
console.log('1. 浏览器打开 ' + devBase + (task.route || '') + '（若失败见下方排障）')
console.log('2. 对照 docs/4-API接口定义.md 章节 §' + (task.api_sections || []).join(' §'))
console.log('3. 勾选 acceptance：', (task.acceptance || []).join('；'))

if (!noDev) {
  const adminDir = join(ROOT, 'frontend', 'admin')
  const devLog = join(STATE_DIR, 'vite-dev.log')
  mkdirSync(STATE_DIR, { recursive: true })
  writeFileSync(
    devLog,
    `[${new Date().toISOString()}] npm run dev (cwd=${adminDir})\n`,
    'utf8'
  )
  console.log('\n=== 启动管理端 Vite（后台）: frontend/admin ===')
  console.log('提示：首次启动可能需 10–40s 预构建依赖；排障请查看', devLog)
  console.log('也可在项目根执行：npm run admin:dev（前台可见端口与报错）')
  const logStream = createWriteStream(devLog, { flags: 'a' })
  const child = spawn('npm', ['run', 'dev'], {
    cwd: adminDir,
    shell: true,
    detached: true,
    stdio: ['ignore', logStream, logStream],
    windowsHide: true,
  })
  child.on('error', (err) => {
    try {
      appendFileSync(devLog, `\nspawn error: ${err.message}\n`)
    } catch {
      /* ignore */
    }
  })
  child.unref()
  session.devServer = { npmPid: child.pid, cwd: adminDir, url: devBase, log: devLog }
  writeFileSync(SESSION, JSON.stringify(session, null, 2), 'utf8')
  console.log('Dev server spawning (默认端口 5173). Session →', SESSION)
} else {
  console.log('\n(--no-dev) 跳过启动 Vite。请在项目根执行 npm run admin:dev，或 cd frontend/admin && npm run dev')
}

console.log(
  '\n完成。推进队列：npm run task-board:done -- --id=<刚完成的任务id> 后再 npm run task-board:auto:no-dev'
)
