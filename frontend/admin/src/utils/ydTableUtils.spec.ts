import { describe, expect, it } from 'vitest';

import { adaptPaginatedResponse } from '@/utils/ydTableUtils';

describe('adaptPaginatedResponse', () => {
  it('handles direct array', () => {
    const r = adaptPaginatedResponse([{ id: 1 }, { id: 2 }]);
    expect(r.rows).toHaveLength(2);
    expect(r.total).toBe(2);
  });

  it('handles items + total', () => {
    const r = adaptPaginatedResponse({ items: [{ id: 'a' }], total: 42 });
    expect(r.rows).toHaveLength(1);
    expect(r.total).toBe(42);
  });

  it('handles nested data.records', () => {
    const r = adaptPaginatedResponse({
      data: { records: [{ id: 1 }], total: 5 },
    });
    expect(r.total).toBe(5);
  });

  it('returns empty on invalid', () => {
    expect(adaptPaginatedResponse(null)).toEqual({ rows: [], total: 0 });
  });
});
