#!/usr/bin/env node
/**
 * BJ-03 · 按 top12-crud-manifest.json 生成列表页 + 路由片段
 * 🔒 须符合 docs/youding-omni-pro-design-LOCKED.md · YdPage + 列设置模板
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const adminRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const repoRoot = path.resolve(adminRoot, '../..')
const manifestPath = path.join(adminRoot, 'scripts/top12-crud-manifest.json')
const outDir = path.join(adminRoot, 'src/views/_generated')
const routesOut = path.join(adminRoot, 'src/router/generated-crud-routes.ts')

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'))

function genListPage(entry) {
  const { name, route, tag } = entry
  const title = tag.replace(/管理$/, '').replace(/优化$/, '优化')
  return `<template>
  <YdPage title="${title} 列表" subtitle="数据列表 · 列设置与筛选" surface="elevated">
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
        <YdTableToolbar :loading="loading" :target-ref="tablePanelRef" :show-export="true" @refresh="reload" />
      </template>
    </YdSearchBar>
    <div ref="tablePanelRef" class="yd-panel yd-table-panel">
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
import { ref } from 'vue'
import { YdDataTable, YdPage, YdSearchBar, YdTableColumnSettings, YdTableToolbar } from '@/components/youding'

const tablePanelRef = ref<HTMLElement | null>(null)
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
  columnOrderKey: 'generated-${name.toLowerCase()}-cols',
  defaultQuery: { search: '' },
  columns,
  fetcher: async (q) => {
    const raw = await apiGet('${route}', {
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
`
}

fs.mkdirSync(outDir, { recursive: true })
const generated = []

for (const entry of manifest) {
  const file = path.join(outDir, `${entry.name}List.vue`)
  fs.writeFileSync(file, genListPage(entry), 'utf8')
  generated.push({ ...entry, file: path.relative(repoRoot, file) })
}

const routeLines = manifest.map(
  (e) => `  {
    path: '${e.path.replace(/^generated\//, 'generated/')}',
    name: 'Generated${e.name}List',
    component: () => import('@/views/_generated/${e.name}List.vue'),
    meta: { title: '${e.tag}（生成）', skipCapabilityGuard: true },
  },`,
)

const routesTs = `/** AUTO-GENERATED · BJ-03 · do not edit by hand */
import type { RouteRecordRaw } from 'vue-router';

export const generatedCrudRoutes: RouteRecordRaw[] = [
${routeLines.join('\n')}
];
`
fs.writeFileSync(routesOut, routesTs, 'utf8')

const summary = { count: generated.length, generated, routesFile: path.relative(repoRoot, routesOut) }
fs.writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(summary, null, 2), 'utf8')
console.log(JSON.stringify(summary, null, 2))
