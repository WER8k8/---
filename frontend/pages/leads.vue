/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="leads-page max-w-[430px] mx-auto px-4 py-6">
    <!-- 页眉 -->
    <header class="relative mb-6">
      <p class="text-xs font-bold text-teal-700 uppercase tracking-wide mb-2">
        移动端询盘看板
      </p>
      <h1 class="text-2xl font-bold mb-2 bg-gradient-to-r from-teal-700 to-green-500 bg-clip-text text-transparent">
        线索跟进
      </h1>
      <p class="text-sm text-slate-500 leading-relaxed mb-4">
        汇总移动端 H5 带来的采购线索，优先查看地区、采购量、预估到场价和联系方式。
      </p>
      <div class="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          @click="handleExport"
        >
          导出 CSV
        </Button>
        <Button
          variant="ghost"
          size="sm"
          :loading="refreshing"
          @click="refresh"
        >
          刷新
        </Button>
      </div>
      <!-- Divider -->
      <div
        class="absolute -bottom-4 left-0 right-0 h-px opacity-30"
        style="background: linear-gradient(135deg, #0f766e 0%, #22c55e 100%)"
      />
    </header>

    <!-- 统计卡片 -->
    <section class="grid grid-cols-3 gap-2 mb-3 mt-6">
      <StatCard
        label="总询盘"
        :value="summary.total"
      />
      <StatCard
        label="总采购量"
        :value="summary.total_quantity_m3"
        unit="m³"
      />
      <StatCard
        label="均价"
        :value="`¥${summary.avg_estimated_price}`"
        unit="/m³"
      />
    </section>

    <!-- 地区热度 -->
    <RegionHeatmap :regions="summary.top_regions" />

    <!-- 最近询盘 -->
    <section class="mt-4">
      <h2
        class="flex items-center gap-2 text-lg font-semibold mb-3
        bg-gradient-to-r from-teal-700 to-green-500 bg-clip-text text-transparent"
      >
        <span
          class="block w-1 h-5 rounded-sm"
          style="background: linear-gradient(135deg, #0f766e 0%, #22c55e 100%); box-shadow: 0 0 6px 2px rgba(15, 118, 110, 0.25)"
        />
        最近询盘
      </h2>

      <!-- 骨架屏加载 -->
      <template v-if="pending">
        <Skeleton
          v-for="i in 5"
          :key="i"
          variant="rect"
          class="h-20 mb-3"
        />
      </template>

      <!-- 询盘列表 -->
      <template v-else-if="leads.length">
        <LeadItem
          v-for="lead in leads"
          :key="lead.id"
          :lead="lead"
        />
        <div
          v-if="hasMore"
          class="py-4 text-center"
        >
          <Button
            variant="ghost"
            size="sm"
            :loading="loadingMore"
            @click="loadMore"
          >
            加载更多
          </Button>
        </div>
      </template>

      <!-- 空状态 -->
      <EmptyState
        v-else
        icon="📋"
        title="暂无询盘"
        description="还没有采购线索，先从产品页提交一条测试线索。"
      >
        <Button
          variant="primary"
          size="sm"
          class="mt-4"
          @click="navigateTo('/product/polyurethane-lightweight-concrete')"
        >
          去提交询盘
        </Button>
      </EmptyState>
    </section>
  </div>
</template>

<script setup lang="ts">
import { SITE_CONFIG } from '~/config/site';

interface Lead {
  id: number
  keyword?: string
  name?: string
  phone: string
  region?: string
  quantity_m3?: number
  estimated_price?: number
  message?: string
  status?: string
  created_at?: string
}

interface Summary {
  total: number
  total_quantity_m3: number
  avg_estimated_price: number
  top_regions: { region: string; count: number }[]
}

const fallbackSummary: Summary = {
  total: 0,
  total_quantity_m3: 0,
  avg_estimated_price: 0,
  top_regions: [],
}

const allLeads = ref<Lead[]>([])
const limit = ref(20)
const hasMore = ref(true)
const loadingMore = ref(false)
const refreshing = ref(false)

const { data: leadsResponse, pending, refresh: refreshLeads } = useFetch<{
  success: boolean
  data: { items: Lead[]; count: number }
}>('/api/leads', {
  query: { limit },
  server: true,
})

const { data: summaryResponse, refresh: refreshSummary } = useFetch<{
  success: boolean
  data: Summary
}>('/api/leads/summary', {
  server: true,
})

// 当 API 返回新数据时累加而非替换
watch(leadsResponse, (newVal) => {
  const items = newVal?.data?.items
  if (!items) return
  if (limit.value <= 20) {
    allLeads.value = items
  } else {
    const existingIds = new Set(allLeads.value.map((l) => l.id))
    const newItems = items.filter((l) => !existingIds.has(l.id))
    allLeads.value = [...allLeads.value, ...newItems]
  }
  hasMore.value = items.length >= limit.value
}, { immediate: true })

const leads = computed(() => allLeads.value)
const summary = computed(() => summaryResponse.value?.data || fallbackSummary)

async function refresh() {
  refreshing.value = true
  limit.value = 20
  try {
    await Promise.all([refreshLeads(), refreshSummary()])
  } catch { /* 刷新失败静默处理 */ }
  refreshing.value = false
}

async function loadMore() {
  if (loadingMore.value || !hasMore.value) return
  loadingMore.value = true
  limit.value += 20
  try {
    await refreshLeads()
  } catch {
    limit.value -= 20
    hasMore.value = false
  }
  loadingMore.value = false
}

function handleExport() {
  const a = document.createElement('a')
  a.href = '/api/leads/export'
  a.download = 'mobile-leads.csv'
  a.click()
}

useHead({
  title: `移动端询盘看板 - ${SITE_CONFIG.name}`,
  meta: [
    {
      name: 'description',
      content: '查看移动端 H5 采购询盘、地区热度、采购量和预估到场价。',
    },
  ],
})
</script>
