/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { onMounted, reactive, ref, type Ref } from 'vue';

import { adaptPaginatedResponse } from '@/utils/ydTableUtils';

export interface YdTablePagination {
  current: number;
  pageSize: number;
  total: number;
}

export interface UseYdTableOptions {
  /** 分页请求；须返回 items/records/list 或数组 */
  fetchPage: (params: Record<string, unknown>) => Promise<unknown>;
  defaultPageSize?: number;
  immediate?: boolean;
  extraParams?: Record<string, unknown>;
}

export interface UseYdTableReturn<T> {
  loading: Ref<boolean>;
  rows: Ref<T[]>;
  pagination: YdTablePagination;
  reload: () => Promise<void>;
  onTableChange: (pag: { current?: number; pageSize?: number }) => void;
  setFilters: (filters: Record<string, unknown>) => void;
}

/** PAGE-01 · 精简版 useTable：分页 + 筛选 + 刷新 */
export function useYdTable<T = Record<string, unknown>>(
  options: UseYdTableOptions,
): UseYdTableReturn<T> {
  const loading = ref(false);
  const rows = ref<T[]>([]) as Ref<T[]>;
  const filters = ref<Record<string, unknown>>({});
  const pagination = reactive<YdTablePagination>({
    current: 1,
    pageSize: options.defaultPageSize ?? 20,
    total: 0,
  });

  async function reload() {
    loading.value = true;
    try {
      const raw = await options.fetchPage({
        page: pagination.current,
        page_size: pagination.pageSize,
        ...options.extraParams,
        ...filters.value,
      });
      const { rows: nextRows, total } = adaptPaginatedResponse<T>(raw);
      rows.value = nextRows;
      pagination.total = total;
    } catch {
      rows.value = [];
      pagination.total = 0;
    } finally {
      loading.value = false;
    }
  }

  function onTableChange(pag: { current?: number; pageSize?: number }) {
    if (pag.current) pagination.current = pag.current;
    if (pag.pageSize) pagination.pageSize = pag.pageSize;
    void reload();
  }

  function setFilters(next: Record<string, unknown>) {
    filters.value = next;
    pagination.current = 1;
    void reload();
  }

  onMounted(() => {
    if (options.immediate !== false) void reload();
  });

  return { loading, rows, pagination, reload, onTableChange, setFilters };
}
