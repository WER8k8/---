import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, '..');

const routerSrc = fs.readFileSync(path.join(root, 'src/router/index.ts'), 'utf8');
const routePaths = new Set();
for (const m of routerSrc.matchAll(/path:\s*'([^']+)'/g)) routePaths.add(m[1]);

function fullPath(segments) {
  return '/' + segments.filter(Boolean).join('/');
}

// lab prefixes from stubVisibility
const LAB_PREFIXES = [
  '/admin/geo-engine','/admin/geo','/admin/v2ray','/admin/v2ray-legacy','/agent-hub',
  '/media-factory','/admin/code-tools','/cognitive','/edge-cdn','/developer',
  '/admin/demo-rehearsal','/templates','/globalization','/logistics','/referral',
  '/admin/automation','/admin/projects','/admin/runtime','/admin/scheduler-hub',
  '/admin/ai-center/article-to-video','/admin/ai-center/article-generator','/admin/ai-center/knowledge',
  '/tenants/product-showcase','/tenants/white-label',
];

const CLIENT_STUB = [
  '/client/media-factory','/client/article-to-video','/client/egress','/client/ai-scenarios','/client/app','/client/copilot',
];

// extModuleNav sibling paths that may be unregistered
const EXT_SIBLINGS = [
  '/agent-hub/mcp-bridge','/agent-hub/task-orchestrator','/agent-hub/execution-review',
  '/media-factory/tts','/media-factory/charts','/media-factory/render-queue',
  '/globalization/glossary','/globalization/translator','/globalization/culture-adapt',
  '/logistics/lbs-routing','/logistics/freight-calc','/logistics/quotation',
  '/system-health/stress-test','/system-health/resource-monitor','/system-health/backup',
  '/ai-learning','/ai-learning/behavior','/ai-learning/conversion-funnel','/ai-learning/auto-ab-test',
  '/cognitive/qa-engine','/cognitive/expert-system','/cognitive/semantic-index',
  '/edge-cdn/nodes','/edge-cdn/preheat','/edge-cdn/protocol',
  '/developer/sdk','/developer/low-code','/developer/plugins',
];

function hasRoute(p) {
  const norm = p.replace(/^\//, '');
  if (routePaths.has(norm)) return true;
  if (routePaths.has(p)) return true;
  for (const rp of routePaths) {
    if (rp === norm || ('/' + rp) === p) return true;
  }
  return false;
}

function vueExists(p) {
  const rel = p.replace(/^\//, '');
  const candidates = [
    path.join(root, 'src/views', rel + '.vue'),
    path.join(root, 'src/views', rel, 'index.vue'),
  ];
  return candidates.some((c) => fs.existsSync(c));
}

function auditList(paths, label) {
  const rows = paths.map((p) => ({
    path: p,
    route: hasRoute(p),
    vue: vueExists(p),
  }));
  const missingRoute = rows.filter((r) => !r.route);
  const noVue = rows.filter((r) => r.route && !r.vue);
  return { label, total: paths.length, missingRoute, noVue, rows };
}

const labAudit = auditList(LAB_PREFIXES, 'lab');
const clientAudit = auditList(CLIENT_STUB, 'client_stub');
const extAudit = auditList(EXT_SIBLINGS, 'ext_siblings');

// workbench paths missing vue (from prior audit)
const wbMissing = [
  '/users','/analytics','/settings','/settings/drag-module','/settings/effects',
  '/ai-config','/ab-test','/feishu','/admin/ai-center/prompts','/admin/ai-center/tasks','/admin/scheduler-hub',
].map((p) => ({ path: p, route: hasRoute(p), vue: vueExists(p) }));

console.log(JSON.stringify({ labAudit, clientAudit, extAudit, wbMissing }, null, 2));
