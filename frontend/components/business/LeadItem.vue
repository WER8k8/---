/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <article
    class="p-4 mb-3 bg-white rounded-xl border border-slate-200 transition-all duration-200 relative overflow-hidden
    hover:-translate-y-0.5 hover:shadow-lg hover:border-teal-600"
  >
    <!-- Top gradient accent -->
    <div
      class="absolute top-0 left-0 right-0 h-[3px] opacity-40"
      style="background: linear-gradient(135deg, #0f766e 0%, #22c55e 100%)"
    />

    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-3">
        <strong class="text-base font-semibold">{{ lead.name || '未留姓名' }}</strong>
        <a
          :href="`tel:${lead.phone}`"
          class="text-sm font-semibold px-2 py-1 rounded-lg transition-all duration-200"
          style="color: #0f766e; background: rgba(15, 118, 110, 0.1)"
        >
          {{ lead.phone }}
        </a>
      </div>
      <span
        :class="badgeClass"
        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold"
      >
        {{ statusLabel }}
      </span>
    </div>

    <div
      class="text-sm text-slate-500 mb-1 p-2 rounded-r-lg border-l-[3px] border-l-green-500"
      style="background: rgba(34, 197, 94, 0.05)"
    >
      {{ lead.region || '未知地区' }} ·
      {{ lead.quantity_m3 || 0 }}m³ ·
      ¥{{ lead.estimated_price || 0 }}/m³
    </div>

    <div class="flex items-center justify-between">
      <span class="text-xs text-slate-400">{{ lead.message || lead.keyword || '移动端询盘' }}</span>
      <span class="text-xs text-slate-400 px-2 py-0.5 rounded-lg bg-slate-100">{{ displayTime }}</span>
    </div>
  </article>
</template>

<script setup lang="ts">
interface Lead {
  id: number
  name?: string
  phone: string
  region?: string
  quantity_m3?: number
  estimated_price?: number
  message?: string
  keyword?: string
  status?: string
  created_at?: string
}

const props = defineProps<{
  lead: Lead
}>()

const displayTime = ref('')

const statusLabel = computed(() => {
  switch (props.lead.status) {
    case 'new': return '新增'
    case 'contacted': return '已联系'
    case 'quoted': return '已报价'
    case 'closed': return '已完成'
    default: return '新增'
  }
})

const badgeClass = computed(() => {
  switch (props.lead.status) {
    case 'new': return 'bg-teal-600 text-white'
    case 'contacted': return 'bg-amber-100 text-amber-700 border border-amber-300'
    case 'quoted': return 'bg-green-100 text-green-700 border border-green-300'
    case 'closed': return 'bg-slate-100 text-slate-500 border border-slate-200'
    default: return 'bg-slate-100 text-slate-500 border border-slate-200'
  }
})

function calculateTimeAgo(): string {
  if (!props.lead.created_at) return ''
  const now = Date.now()
  const created = new Date(props.lead.created_at).getTime()
  const diff = now - created
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return new Date(props.lead.created_at).toLocaleDateString('zh-CN')
}

onMounted(() => {
  displayTime.value = calculateTimeAgo()
})

watch(() => props.lead.created_at, () => {
  displayTime.value = calculateTimeAgo()
})
</script>
