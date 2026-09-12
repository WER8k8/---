<template>
  <Card>
    <h2 class="text-lg font-semibold mb-4 bg-gradient-to-r from-teal-700 to-green-500 bg-clip-text text-transparent">
      地区热度
    </h2>
    <ul v-if="regions.length" class="m-0 p-0 list-none">
      <li v-for="(item, index) in regions" :key="item.region"
        class="flex items-center gap-3 min-h-[44px] py-2 border-b border-slate-200 last:border-b-0">
        <span class="w-5 text-xs font-bold text-slate-400 text-center">{{ index + 1 }}</span>
        <span class="min-w-[70px] text-sm font-medium">{{ item.region }}</span>
        <span class="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
          <span
            class="h-full rounded-full transition-[width] duration-600"
            :style="{
              width: barWidth(item.count),
              background: 'linear-gradient(135deg, #0f766e 0%, #22c55e 100%)',
              boxShadow: '0 0 6px 2px rgba(15, 118, 110, 0.25)'
            }"
          />
        </span>
        <span class="text-xs text-slate-500 whitespace-nowrap min-w-[40px] text-right">{{ item.count }} 条</span>
      </li>
    </ul>
    <EmptyState v-else icon="🗺️" title="暂无地区数据" description="还没有来自各地的采购询盘" />
  </Card>
</template>

<script setup lang="ts">
interface RegionItem {
  region: string
  count: number
}

const props = defineProps<{
  regions: RegionItem[]
}>()

const maxCount = computed(() => {
  if (!props.regions.length) return 1
  return Math.max(...props.regions.map((r) => r.count))
})

function barWidth(count: number): string {
  return `${(count / maxCount.value) * 100}%`
}
</script>
