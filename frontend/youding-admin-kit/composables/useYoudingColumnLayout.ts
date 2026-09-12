import { computed, ref, type Ref } from 'vue'

import type { YoudingTableColumn } from './useYoudingTable'

function loadColumnOrder(key: string, columns: YoudingTableColumn[]): string[] {
  const defaults = columns.map((c) => c.key)
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return defaults
    const saved = JSON.parse(raw) as string[]
    const valid = saved.filter((k) => defaults.includes(k))
    const missing = defaults.filter((k) => !valid.includes(k))
    return [...valid, ...missing]
  } catch {
    return defaults
  }
}

function loadHiddenKeys(key: string, columns: YoudingTableColumn[]): string[] {
  try {
    const raw = localStorage.getItem(`${key}-hidden`)
    if (!raw) return []
    const saved = JSON.parse(raw) as string[]
    const allowed = new Set(columns.map((c) => c.key))
    return saved.filter((k) => allowed.has(k))
  } catch {
    return []
  }
}

/** 列顺序与显隐（不含分页/拉数），供 a-table 与 useYoudingTable 共用 */
export function useYoudingColumnLayout(
  columns: YoudingTableColumn[] | Ref<YoudingTableColumn[]>,
  columnOrderKey?: string,
) {
  const baseColumns = computed(() => (Array.isArray(columns) ? columns : columns.value))

  const columnOrder = ref<string[]>(
    columnOrderKey && baseColumns.value.length
      ? loadColumnOrder(columnOrderKey, baseColumns.value)
      : baseColumns.value.map((c) => c.key),
  )

  const hiddenColumnKeys = ref<string[]>(
    columnOrderKey && baseColumns.value.length
      ? loadHiddenKeys(columnOrderKey, baseColumns.value)
      : [],
  )

  const orderedColumns = computed(() => {
    const cols = baseColumns.value
    if (!cols.length) return []
    const map = new Map(cols.map((c) => [c.key, c]))
    return columnOrder.value.map((k) => map.get(k)).filter(Boolean) as YoudingTableColumn[]
  })

  const visibleColumns = computed(() =>
    orderedColumns.value.filter((c) => !hiddenColumnKeys.value.includes(c.key)),
  )

  function persistHidden() {
    if (columnOrderKey) {
      localStorage.setItem(`${columnOrderKey}-hidden`, JSON.stringify(hiddenColumnKeys.value))
    }
  }

  function toggleColumnVisibility(key: string) {
    const idx = hiddenColumnKeys.value.indexOf(key)
    if (idx >= 0) hiddenColumnKeys.value.splice(idx, 1)
    else hiddenColumnKeys.value.push(key)
    persistHidden()
  }

  function resetColumnLayout() {
    columnOrder.value = baseColumns.value.map((c) => c.key)
    hiddenColumnKeys.value = []
    if (columnOrderKey) {
      localStorage.removeItem(columnOrderKey)
      localStorage.removeItem(`${columnOrderKey}-hidden`)
    }
  }

  function reorderColumns(fromIndex: number, toIndex: number) {
    const next = [...columnOrder.value]
    const [moved] = next.splice(fromIndex, 1)
    if (moved === undefined) return
    next.splice(toIndex, 0, moved)
    columnOrder.value = next
    if (columnOrderKey) {
      localStorage.setItem(columnOrderKey, JSON.stringify(next))
    }
  }

  function moveColumnUp(key: string) {
    const i = columnOrder.value.indexOf(key)
    if (i > 0) reorderColumns(i, i - 1)
  }

  function moveColumnDown(key: string) {
    const i = columnOrder.value.indexOf(key)
    if (i >= 0 && i < columnOrder.value.length - 1) reorderColumns(i, i + 1)
  }

  return {
    orderedColumns,
    visibleColumns,
    columnOrder,
    hiddenColumnKeys,
    reorderColumns,
    toggleColumnVisibility,
    moveColumnUp,
    moveColumnDown,
    resetColumnLayout,
  }
}
