/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="新闻 列表" subtitle="数据列表 · 列设置与筛选" surface="elevated">
    <YdSearchBar @search="search" @reset="reset">
      <a-input v-model:value="query.search" placeholder="关键词" allow-clear style="width: 200px" />
      <template #extra>
        <YdTableColumnSettings
          :columns="orderedColumns"
          :hidden-keys="hiddenColumnKeys"
          @toggle="toggleColumnVisibility"
          @move-up="moveColumnUp"
          @move-down="moveColumnDown"
          @reset="resetColumnLayout"
        />
        <YdTableToolbar :loading="loading" :show-export="false" @refresh="reload" />
      </template>
    </YdSearchBar>
    <div class="yd-panel yd-table-panel">
      <YdDataTable
        :columns="visibleColumns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        @page-change="(p) => onPageChange(p.current, p.pageSize)"
      />
    </div>
  </YdPage>
</template>
<script setup lang="ts">
import { YdDataTable, YdPage, YdSearchBar, YdTableColumnSettings, YdTableToolbar } from '@/components/youding'
import { useYoudingTable } from '@/composables/useYoudingTableBridge'
import { apiGet } from '@/utils/api'

const columns = [
  { key: 'id', title: 'ID', dataIndex: 'id', align: 'center' },
  { key: 'name', title: '名称', dataIndex: 'name', align: 'center' },
  { key: 'status', title: '状态', dataIndex: 'status', align: 'center' },
]

type ListQuery = { search: string }

const {
  loading,
  items,
  pagination,
  orderedColumns,
  visibleColumns,
  hiddenColumnKeys,
  query,
  search,
  reset,
  reload,
  onPageChange,
  toggleColumnVisibility,
  moveColumnUp,
  moveColumnDown,
  resetColumnLayout,
} = useYoudingTable<Record<string, unknown>, ListQuery>({
  columnOrderKey: 'generated-news-cols',
  defaultQuery: { search: '' },
  columns,
  fetcher: async (q) => {
    const raw = await apiGet('/news/', {
      page: q.page,
      page_size: q.pageSize,
      search: q.search,
    })
    const data = raw?.data ?? raw
    const rows = data?.items ?? data?.records ?? data?.list ?? (Array.isArray(data) ? data : [])
    const total = data?.total ?? rows.length
    return { items: rows, total }
  },
})
</script>
<style scoped>
</style>
