import { WORKBENCH_CAPABILITY_REGISTRY } from '@/constants/workbenchCapabilityRegistry';

/** 去掉 query/hash，并折叠末尾 `/`（根路径除外） */
export function normalizeLocationPath(path: string): string {
  const raw = ((path ?? '').split('?')[0] || '/').split('#')[0] || '/';
  if (raw === '/') return '/';
  const trimmed = raw.replace(/\/+$/, '');
  return trimmed || '/';
}

let sortedPairs: { path: string; id: string }[] | null = null;

/** 按 path 长度降序，供最长前缀匹配 */
export function getWorkbenchPathCapabilityPairsSorted(): {
  path: string;
  id: string;
}[] {
  if (sortedPairs) return sortedPairs;
  const pairs: { path: string; id: string }[] = [];
  for (const sec of WORKBENCH_CAPABILITY_REGISTRY) {
    for (const item of sec.items) {
      if (item.guardOnly) continue;
      pairs.push({
        path: normalizeLocationPath(item.path),
        id: item.id,
      });
    }
  }
  pairs.sort((a, b) => b.path.length - a.path.length);
  sortedPairs = pairs;
  return sortedPairs;
}

/** 将当前 URL 解析为工作台能力 id；未注册的路径返回 null（放行，由业务页自行处理） */
export function resolveCapabilityIdForPath(routePath: string): string | null {
  const loc = normalizeLocationPath(routePath);
  if (loc === '/admin') return 'suite.workbench';
  for (const { path, id } of getWorkbenchPathCapabilityPairsSorted()) {
    if (loc === path) return id;
    if (loc.startsWith(`${path}/`)) return id;
  }
  return null;
}

/** 不参与能力校验的路由（如无权提示页） */
export function isCapabilityGuardBypassPath(routePath: string): boolean {
  const loc = normalizeLocationPath(routePath);
  return loc === '/access-denied' || loc === '/login';
}
