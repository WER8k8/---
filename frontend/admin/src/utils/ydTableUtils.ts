/** PAGE-01 · 分页响应适配（对齐 Art useTable 多格式） */

export interface YdPageResult<T> {
  rows: T[];
  total: number;
}

const ROW_KEYS = ['items', 'records', 'list', 'rows', 'result'] as const;
const TOTAL_KEYS = ['total', 'count', 'totalCount'] as const;

function pickRows(obj: Record<string, unknown>): unknown[] {
  for (const key of ROW_KEYS) {
    const val = obj[key];
    if (Array.isArray(val)) return val;
  }
  const nested = obj.data;
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
    return pickRows(nested as Record<string, unknown>);
  }
  if (Array.isArray(nested)) return nested;
  return [];
}

function pickTotal(obj: Record<string, unknown>, fallback: number): number {
  for (const key of TOTAL_KEYS) {
    const val = obj[key];
    if (typeof val === 'number' && Number.isFinite(val)) return val;
  }
  const nested = obj.data;
  if (nested && typeof nested === 'object' && !Array.isArray(nested)) {
    return pickTotal(nested as Record<string, unknown>, fallback);
  }
  return fallback;
}

export function adaptPaginatedResponse<T>(raw: unknown): YdPageResult<T> {
  if (Array.isArray(raw)) {
    return { rows: raw as T[], total: raw.length };
  }
  if (!raw || typeof raw !== 'object') {
    return { rows: [], total: 0 };
  }
  const obj = raw as Record<string, unknown>;
  const rows = pickRows(obj) as T[];
  const total = pickTotal(obj, rows.length);
  return { rows, total };
}
