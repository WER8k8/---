import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, '..');

const registrySrc = fs.readFileSync(
  path.join(root, 'src/constants/workbenchCapabilityRegistry.ts'),
  'utf8',
);
const routerSrc = fs.readFileSync(path.join(root, 'src/router/index.ts'), 'utf8');

const chunks = registrySrc.split(/\{\s*id:/).slice(1);
const entries = chunks.map((ch) => {
  const id = ch.match(/id:\s*'([^']+)'/)?.[1] ?? '?';
  const p = ch.match(/path:\s*'([^']+)'/)?.[1] ?? '';
  const guardOnly = /guardOnly:\s*true/.test(ch);
  return { id, path: p, guardOnly };
});

const routePaths = new Set();
for (const m of routerSrc.matchAll(/path:\s*'([^']+)'/g)) {
  routePaths.add(m[1]);
}

function normalize(p) {
  return (p || '/').split('?')[0].replace(/\/$/, '') || '/';
}

function routeRegistered(target) {
  const norm = normalize(target);
  if (routePaths.has(norm.replace(/^\//, ''))) return true;
  if (routePaths.has(norm)) return true;
  const tail = norm.replace(/^\//, '');
  for (const rp of routePaths) {
    const r = normalize(rp.startsWith('/') ? rp : `/${rp}`);
    if (r === norm || r.endsWith(`/${tail}`) || norm.endsWith(r)) return true;
  }
  return false;
}

function vueGuess(target) {
  const norm = normalize(target);
  const rel = norm.replace(/^\//, '');
  const candidates = [
    path.join(root, 'src/views', `${rel}.vue`),
    path.join(root, 'src/views', rel, 'index.vue'),
    path.join(root, 'src/views', `${rel}/index.vue`),
  ];
  return candidates.some((c) => fs.existsSync(c));
}

const visible = entries.filter((e) => !e.guardOnly);
const noRoute = visible.filter((e) => !routeRegistered(e.path));
const noVue = visible.filter((e) => !vueGuess(e.path));

console.log(
  JSON.stringify(
    {
      registry_total: entries.length,
      guard_only: entries.filter((e) => e.guardOnly).length,
      visible_on_workbench: visible.length,
      missing_route: noRoute.length,
      missing_vue_guess: noVue.length,
      missing_route_paths: noRoute.map((e) => e.path),
      missing_vue_paths: noVue.map((e) => e.path),
    },
    null,
    2,
  ),
);
