#!/usr/bin/env node
/** 校验侧栏 PLATFORM_SHELL_MENU 路径是否在 vue-router 中可解析 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const menuFile = fs.readFileSync(path.join(root, 'src/constants/platformShellMenu.ts'), 'utf8');
const routerTs = fs.readFileSync(path.join(root, 'src/router/index.ts'), 'utf8');

const menuPaths = [...new Set([...menuFile.matchAll(/path:\s*['']([^'']+)['']/g)].map((m) => m[1]))];
const rawRoutes = [...routerTs.matchAll(/path:\s*['`]([^'`]+)['`]/g)].map((m) => m[1]);

const routeSet = new Set(['/']);
for (const r of rawRoutes) {
  if (r.startsWith('/')) routeSet.add(r.replace(/\/+$/, '') || '/');
}
for (const r of rawRoutes) {
  if (r.startsWith('/') || r.includes(':')) continue;
  const full = `/${r}`.replace(/\/+/g, '/').replace(/\/+$/, '');
  routeSet.add(full);
}
const adminChild = [...routerTs.matchAll(/path:\s*'admin\/([^']+)'/g)].map((m) => `/admin/${m[1]}`);
adminChild.forEach((p) => routeSet.add(p.replace(/\/+$/, '')));

function resolveable(navPath) {
  const p = navPath.startsWith('/') ? navPath : `/${navPath}`;
  const loc = p.replace(/\/+$/, '') || '/';
  if (routeSet.has(loc)) return true;
  for (const r of routeSet) {
    if (loc === r || loc.startsWith(`${r}/`)) return true;
  }
  const parts = loc.split('/');
  while (parts.length > 1) {
    parts.pop();
    const parent = parts.join('/') || '/';
    if (routeSet.has(parent)) return true;
  }
  return false;
}

const missing = menuPaths.filter((p) => !resolveable(p));
console.log(JSON.stringify({ total: menuPaths.length, missing, source: 'platformShellMenu.ts' }, null, 2));
process.exit(missing.length ? 1 : 0);
