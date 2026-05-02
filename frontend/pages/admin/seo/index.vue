<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      SEO 概览
    </h1>
    <div
      v-if="loading"
      class="text-center py-12 text-text-muted"
    >
      加载中...
    </div>
    <div
      v-else-if="error"
      class="text-center py-12 text-danger"
    >
      {{ error }}
    </div>
    <template v-else-if="data">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-surface rounded-xl border border-border p-6">
          <div class="text-sm text-text-secondary mb-2">
            关键词总数
          </div>
          <div class="text-3xl font-bold text-primary-900">
            {{ data.total_keywords }}
          </div>
        </div>
        <div class="bg-surface rounded-xl border border-border p-6">
          <div class="text-sm text-text-secondary mb-2">
            已排名关键词
          </div>
          <div class="text-3xl font-bold text-accent">
            {{ data.ranked_keywords }}
          </div>
        </div>
        <div class="bg-surface rounded-xl border border-border p-6">
          <div class="text-sm text-text-secondary mb-2">
            平均排名
          </div>
          <div class="text-3xl font-bold text-primary-900">
            {{ data.avg_rank ?? '-' }}
          </div>
        </div>
        <div class="bg-surface rounded-xl border border-border p-6">
          <div class="text-sm text-text-secondary mb-2">
            AI 优化页面
          </div>
          <div class="text-3xl font-bold text-secondary">
            {{ data.ai_optimized_pages }}
          </div>
        </div>
        <div class="bg-surface rounded-xl border border-border p-6">
          <div class="text-sm text-text-secondary mb-2">
            LLMs.txt 状态
          </div>
          <div
            class="text-3xl font-bold"
            :class="data.llms_txt_generated ? 'text-accent' : 'text-text-muted'"
          >
            {{ data.llms_txt_generated ? '已生成' : '未生成' }}
          </div>
        </div>
        <div class="bg-surface rounded-xl border border-border p-6">
          <div class="text-sm text-text-secondary mb-2">
            上次审计评分
          </div>
          <div class="text-3xl font-bold text-primary-900">
            {{ data.last_audit_score ?? '-' }}
          </div>
        </div>
      </div>
      <div
        v-if="data.page_coverage && data.page_coverage.length"
        class="bg-surface rounded-xl border border-border p-6"
      >
        <h2 class="text-lg font-semibold text-primary-900 mb-4">
          页面覆盖
        </h2>
        <div class="space-y-3">
          <div
            v-for="item in data.page_coverage"
            :key="item.type"
            class="flex items-center justify-between py-3 border-b border-border-light last:border-0"
          >
            <span class="text-text-secondary">{{ item.type }}</span>
            <span class="text-sm font-semibold text-primary-900">{{ item.count }} 页</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })

interface DashboardData {
  total_keywords: number
  ranked_keywords: number
  avg_rank: number | null
  ai_optimized_pages: number
  llms_txt_generated: boolean
  last_audit_score: number | null
  keyword_trend: Array<{ date: string; avg_rank: number | null }>
  page_coverage: Array<{ type: string; count: number }>
}

const data = ref<DashboardData | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  loading.value = true
  error.value = null
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch('/api/v1/seo/dashboard', {
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
    })
    if (!res.ok) throw new Error(`请求失败: ${res.status}`)
    data.value = await res.json()
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})
</script>
