#!/usr/bin/env node
/**
 * 检测导航子页面：假数据种子、无点击处理器按钮、待定制空壳
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const viewsDir = path.join(root, 'src/views')
const layoutVue = fs.readFileSync(path.join(root, 'src/layout/index.vue'), 'utf8')
const menuPaths = [...new Set([...layoutVue.matchAll(/path:'([^']+)'/g)].map((m) => m[1]))]

const SEED = /const\s+\w+\s*=\s*ref\(\s*\[\s*\{[^}]+\}/
const FAKE_CATCH = /API不可用，使用本地数据|显示缓存数据|模拟数据|测距完成（本地模式）/
const STUB = /<!--\s*模板页面：待定制\s*-->/

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name)
    if (fs.statSync(p).isDirectory()) walk(p, out)
    else if (name.endsWith('.vue')) out.push(p)
  }
  return out
}

function inMenu(rel) {
  const base = '/' + rel.replace(/\/index\.vue$/, '').replace(/\.vue$/, '').replace(/\/dashboard$/, '')
  return menuPaths.some((m) => m === base || m.startsWith(base + '/') || base.startsWith(m + '/'))
}

const issues = []
for (const file of walk(viewsDir)) {
  const rel = path.relative(viewsDir, file).replace(/\\/g, '/')
  const src = fs.readFileSync(file, 'utf8')
  const hits = []
  if (STUB.test(src)) hits.push('待定制标记')
  if (SEED.test(src)) hits.push('硬编码种子数据')
  if (FAKE_CATCH.test(src)) hits.push('假数据回退')
  const deadBtn = src.match(/<a-button[^>]*>([^<]+)<\/a-button>/gs)?.filter((b, _i, arr) => {
    if (b.includes('@click') || b.includes('html-type') || b.includes('type="link"')) return false
    if (b.includes(':loading') || b.includes('disabled')) return false
    if (/刷新|导出|搜索|查询|保存|提交|添加|新建|删除|取消|登录|注册|启动|停止|测试|编辑|查看|复制|下载|上传|关闭|确定|返回/.test(b)) return false
    const idx = src.indexOf(b)
    if (idx > 0) {
      const before = src.slice(Math.max(0, idx - 120), idx)
      if (/<router-link[^>]*>\s*$/.test(before) || before.includes('<router-link')) return false
      if (/<a\s[^>]*>\s*$/.test(before) || /\s<a\s/.test(before.slice(-80))) return false
    }
    return true
  })
  if (deadBtn?.length) hits.push(`疑似无事件按钮×${deadBtn.length}`)
  if (hits.length) issues.push({ path: rel, inMenu: inMenu(rel), hits })
}

issues.sort((a, b) => Number(b.inMenu) - Number(a.inMenu) || a.path.localeCompare(b.path))
console.log(JSON.stringify({ menuLinked: issues.filter((i) => i.inMenu).length, total: issues.length, items: issues.filter((i) => i.inMenu).slice(0, 40) }, null, 2))
