#!/usr/bin/env node
/** 批量替换假数据回退文案（补贴审计红旗） */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const viewsDir = path.join(path.dirname(fileURLToPath(import.meta.url)), '../src/views')
const FROM = /API不可用，使用本地数据|测距完成（本地模式）|本地搜索无结果/g
const TO = '数据加载失败，请稍后重试'

function walk(dir, out = []) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name)
    if (fs.statSync(p).isDirectory()) walk(p, out)
    else if (name.endsWith('.vue')) out.push(p)
  }
  return out
}

let n = 0
for (const f of walk(viewsDir)) {
  let s = fs.readFileSync(f, 'utf8')
  if (!FROM.test(s)) continue
  FROM.lastIndex = 0
  s = s.replace(FROM, TO)
  fs.writeFileSync(f, s, 'utf8')
  n++
}
console.log(JSON.stringify({ updated: n }))
