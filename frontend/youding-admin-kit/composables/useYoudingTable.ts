/**
 * useYoudingTable — 百家组装表格 composable
 * 交互参考：Art Design Pro useTable
 * 组件：Ant Design Vue Table
 * 约定：frontend/youding-admin-kit/conventions/table.md
 */
import { computed, reactive, ref, watch, type Ref } from 'vue'

import { useYoudingColumnLayout } from './useYoudingColumnLayout'

export type YoudingTableFetcher<T, Q extends Record<string, unknown>> = (
  query: Q & { page: number; pageSize: number },
) => Promise<{ items: T[]; total: number }>

export interface YoudingTableColumn {
  key: string
  title: string
  dataIndex?: string
  [prop: string]: unknown
}

export interface UseYoudingTableOptions<T, Q extends Record<string, unknown>> {
  fetcher: YoudingTableFetcher<T, Q>
  defaultQuery?: Q
  pageSize?: number
  immediate?: boolean
  /** 列定义；支持拖拽排序（Art 734） */
  columns?: YoudingTableColumn[]
  /** localStorage key；传入则持久化列顺序 */
  columnOrderKey?: string
}

export function useYoudingTable<T, Q extends Record<string, unknown> = Record<string, unknown>>(
  options: UseYoudingTableOptions<T, Q>,
) {
  const loading = ref(false)
  const items = ref<T[]>([]) as Ref<T[]>
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(options.pageSize ?? 10)
  const query = reactive({ ...(options.defaultQuery ?? {}) }) as Q

  const baseColumns = options.columns ?? []
  const {
    orderedColumns,
    visibleColumns,
    columnOrder,
    hiddenColumnKeys,
    reorderColumns,
    toggleColumnVisibility,
    moveColumnUp,
    moveColumnDown,
    resetColumnLayout,
  } = useYoudingColumnLayout(baseColumns, options.columnOrderKey)

  const pagination = computed(() => ({
    current: page.value,
    pageSize: pageSize.value,
    total: total.value,
    showSizeChanger: true,
    showTotal: (t: number) => `共 ${t} 条`,
  }))

  function cleanQuery(raw: Record<string, unknown>) {
    const out: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(raw)) {
      if (v === undefined || v === null) continue
      if (typeof v === 'string' && v.trim() === '') continue
      out[k] = v
    }
    return out as Q
  }

  async function reload() {
    loading.value = true
    try {
      const res = await options.fetcher({
        ...cleanQuery(query as Record<string, unknown>),
        page: page.value,
        pageSize: pageSize.value,
      } as Q & { page: number; pageSize: number })
      items.value = res.items
      total.value = res.total
    } finally {
      loading.value = false
    }
  }

  function search() {
    page.value = 1
    return reload()
  }

  function reset() {
    Object.keys(query as object).forEach((k) => {
      delete (query as Record<string, unknown>)[k]
    })
    Object.assign(query, options.defaultQuery ?? {})
    page.value = 1
    return reload()
  }

  function onPageChange(p: number, ps?: number) {
    page.value = p
    if (ps) pageSize.value = ps
    return reload()
  }

  /** 空值占位 — Art Edge 约定 */
  function cellText(value: unknown) {
    if (value === 0 || value === false) return String(value)
    if (value === undefined || value === null || value === '') return '--'
    return String(value)
  }

  if (options.immediate !== false) {
    watch([page, pageSize], () => reload(), { immediate: true })
  }

  return {
    loading,
    items,
    total,
    page,
    pageSize,
    query,
    pagination,
    orderedColumns,
    visibleColumns,
    columnOrder,
    hiddenColumnKeys,
    reorderColumns,
    toggleColumnVisibility,
    moveColumnUp,
    moveColumnDown,
    resetColumnLayout,
    reload,
    search,
    reset,
    onPageChange,
    cellText,
  }
}
