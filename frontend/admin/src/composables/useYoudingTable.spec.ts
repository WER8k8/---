import { describe, expect, it, beforeEach } from 'vitest';

import { useYoudingTable } from '../../../youding-admin-kit/composables/useYoudingTable';

describe('useYoudingTable', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('cleans empty search params on fetch', async () => {
    const calls: Record<string, unknown>[] = [];
    const table = useYoudingTable({
      immediate: false,
      defaultQuery: { status: 'pending', q: '' },
      fetcher: async (query) => {
        calls.push({ ...query });
        return { items: [{ id: '1' }], total: 1 };
      },
    });

    await table.search();
    expect(calls[0]).toMatchObject({ page: 1, pageSize: 10, status: 'pending' });
    expect(calls[0]).not.toHaveProperty('q');
  });

  it('reorders columns and persists to localStorage', () => {
    const table = useYoudingTable({
      immediate: false,
      columnOrderKey: 'test-table-cols',
      columns: [
        { key: 'a', title: 'A', dataIndex: 'a' },
        { key: 'b', title: 'B', dataIndex: 'b' },
        { key: 'c', title: 'C', dataIndex: 'c' },
      ],
      fetcher: async () => ({ items: [], total: 0 }),
    });

    expect(table.orderedColumns.value.map((c) => c.key)).toEqual(['a', 'b', 'c']);
    table.reorderColumns(0, 2);
    expect(table.orderedColumns.value.map((c) => c.key)).toEqual(['b', 'c', 'a']);
    expect(JSON.parse(localStorage.getItem('test-table-cols')!)).toEqual(['b', 'c', 'a']);
  });
});
