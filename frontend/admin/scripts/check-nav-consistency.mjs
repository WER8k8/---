#!/usr/bin/env node
/** 检查 proShellMenus 和 navRouteRegistry 中的路径一致性 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const proShellMenu = fs.readFileSync(path.join(root, 'src/constants/proShellMenus.ts'), 'utf8');
const navRoute = fs.readFileSync(path.join(root, 'src/constants/navRouteRegistry.ts'), 'utf8');

const menuPathRegex = /path:\s*['"](\/client\/[^'"]+)['"]/g;
const navPathRegex = /'client-[^']+':\s*['"]([^'"]+)['"]/g;

const menuPaths = [...new Set([...proShellMenu.matchAll(menuPathRegex)].map((m) => m[1]))];
const navPaths = [...new Set([...navRoute.matchAll(navPathRegex)].map((m) => m[1]))];

console.log('=== proShellMenus.ts 中的 /client/ 路径 ===');
console.log(menuPaths.sort());
console.log(`\n共 ${menuPaths.length} 个路径`);

console.log('\n=== navRouteRegistry.ts 中的 client-* 映射 ===');
console.log(navPaths.sort());
console.log(`\n共 ${navPaths.length} 个路径`);

const missingInNav = menuPaths.filter(p => !navPaths.includes(p));
const missingInMenu = navPaths.filter(p => !menuPaths.includes(p));

console.log('\n=== proShellMenus中有但navRouteRegistry中缺失的路径 ===');
console.log(missingInNav.length ? missingInNav : '无');

console.log('\n=== navRouteRegistry中有但proShellMenus中缺失的路径 ===');
console.log(missingInMenu.length ? missingInMenu : '无');

if (missingInNav.length > 0 || missingInMenu.length > 0) {
  process.exit(1);
}
console.log('\n✓ 所有路径一致');
