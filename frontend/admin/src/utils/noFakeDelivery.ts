/**
 * 前端 API 层假交付硬拒绝（与后端 no_fake_delivery 宪章对齐）
 */

import { ApiError } from '@/utils/api';

const FAKE_MESSAGE_RE = /模拟数据|演示数据|以下为演示|暂时返回模拟|模拟模式/i;

export type MockTaggedPayload = {
  __mockPayload?: boolean;
  __mockReason?: string;
};

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}

function subtreeMarkedMock(obj: Record<string, unknown>): boolean {
  if (obj.mode === 'mock') return true;
  const data = obj.data;
  return isPlainObject(data) && data.mode === 'mock';
}

export function findClientPayloadViolations(payload: unknown, path = ''): string[] {
  const out: string[] = [];
  const walk = (node: unknown, p: string, budget: { n: number }) => {
    if (budget.n <= 0 || node === null || node === undefined) return;
    budget.n -= 1;
    if (Array.isArray(node)) {
      node.slice(0, 40).forEach((item, i) => walk(item, `${p}[${i}]`, budget));
      return;
    }
    if (!isPlainObject(node)) return;

    if (node.mock === true && node.mode !== 'mock') {
      out.push(`${p || '$'}: mock=true 无 mode=mock`);
    }
    if (node.data_source === 'mock') {
      out.push(`${p || '$'}: data_source=mock`);
    }
    if (
      (node.probe_mode === 'stub' || node.probe_mode === 'mock' || node.probe_mode === 'demo')
      && node.included === true
    ) {
      out.push(`${p || '$'}: stub 探测 included=true`);
    }
    const msg = node.message;
    if (typeof msg === 'string' && FAKE_MESSAGE_RE.test(msg) && !subtreeMarkedMock(node)) {
      out.push(`${p || '$'}: message 含模拟/演示文案`);
    }

    for (const [key, value] of Object.entries(node)) {
      if (typeof value === 'object' && value !== null) {
        walk(value, p ? `${p}.${key}` : key, budget);
      }
    }
  };
  walk(payload, path, { n: 2000 });
  return out.slice(0, 20);
}

export function guardApiPayload<T>(
  data: T,
  endpoint: string,
  opts?: { allowMock?: boolean },
): T {
  if (data === null || data === undefined) return data;

  const violations = import.meta.env.PROD ? findClientPayloadViolations(data) : [];
  if (violations.length && !opts?.allowMock) {
    throw new ApiError(503, endpoint, `生产路径拒绝假数据：${violations[0]}`);
  }

  if (isPlainObject(data)) {
    const isMock =
      data.mode === 'mock'
      || data.mock === true
      || data.probe_mode === 'stub'
      || (isPlainObject(data.data) && data.data.mode === 'mock');
    if (isMock) {
      (data as MockTaggedPayload).__mockPayload = true;
      if (typeof data.mock_reason === 'string') {
        (data as MockTaggedPayload).__mockReason = data.mock_reason;
      }
    }
  }
  return data;
}
