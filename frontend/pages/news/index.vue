<template>
  <div>
    <section class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-700">
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-secondary-400 rounded-full blur-3xl" />
        <div class="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent-400 rounded-full blur-3xl" />
      </div>
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-24 text-center">
        <div class="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full mb-6">
          <span class="w-2 h-2 bg-secondary-400 rounded-full mr-2" />
          <span class="text-sm font-medium text-white">新闻资讯</span>
        </div>
        <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight">
          新闻资讯
        </h1>
        <p class="text-xl text-white/80">
          了解优丁建材最新动态和行业资讯
        </p>
      </div>
    </section>

    <section class="py-20 bg-gradient-to-b from-surface-elevated to-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-wrap gap-3 mb-12 justify-center">
          <button
            v-for="cat in categories"
            :key="cat.value"
            :class="activeCategory === cat.value
              ? 'bg-gradient-to-r from-secondary-500 to-secondary-600 text-white shadow-lg shadow-secondary-200'
              : 'bg-white text-text-secondary hover:bg-surface-hover border border-border'"
            class="px-6 py-2.5 rounded-full text-sm font-medium transition-all shadow-card"
            @click="activeCategory = cat.value"
          >
            {{ cat.label }}
          </button>
        </div>

        <div
          v-if="loading"
          class="text-center py-12"
        >
          <div class="flex items-center justify-center">
            <div class="w-8 h-8 border-2 border-secondary-500 border-t-transparent rounded-full animate-spin" />
            <span class="ml-3 text-text-muted">加载中...</span>
          </div>
        </div>

        <div
          v-else-if="filteredArticles.length === 0"
          class="text-center py-12"
        >
          <div class="w-20 h-20 bg-surface-elevated rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              class="w-10 h-10 text-text-muted"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p class="text-text-muted text-lg">
            暂无相关新闻
          </p>
        </div>

        <div
          v-else
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          <article
            v-for="article in filteredArticles"
            :key="article.id"
            class="bg-white rounded-2xl border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all duration-300 hover:-translate-y-1 overflow-hidden"
          >
            <div class="p-6">
              <span class="text-xs font-semibold bg-secondary-50 text-secondary-600 px-3 py-1 rounded-full">
                {{ categoryLabels[article.category] || article.category }}
              </span>
              <h3 class="text-lg font-semibold text-primary-900 mt-3 mb-2 group-hover:text-secondary-600 transition-colors">
                <NuxtLink :to="'/news/' + article.slug">
                  {{ article.title }}
                </NuxtLink>
              </h3>
              <p class="text-text-secondary text-sm mb-4 line-clamp-2">
                {{ article.summary }}
              </p>
              <div class="flex items-center justify-between text-sm">
                <span class="text-text-muted flex items-center gap-1">
                  <svg
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  {{ article.date }}
                </span>
                <NuxtLink
                  :to="'/news/' + article.slug"
                  class="text-secondary-600 font-medium hover:text-secondary-700 flex items-center gap-1 group-hover:translate-x-1 transition-all"
                >
                  阅读更多
                  <svg
                    class="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </NuxtLink>
              </div>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section class="py-16 bg-gradient-to-r from-secondary-600 via-secondary-500 to-accent-500">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">
          需要了解更多？
        </h2>
        <p class="text-white/80 mb-8 max-w-2xl mx-auto">
          订阅我们的新闻通讯，获取最新行业资讯和产品动态
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <NuxtLink
            to="/products"
            class="inline-flex items-center px-8 py-4 bg-white text-secondary-600 font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-lg"
          >
            <svg
              class="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
              />
            </svg>
            查看产品
          </NuxtLink>
          <NuxtLink
            to="/contact"
            class="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white/10 transition-all"
          >
            <svg
              class="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            联系我们
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

useHead({
  title: '新闻资讯 - 优丁建材',
  meta: [
    { name: 'description', content: '优丁建材最新动态，轻集料混凝土行业资讯、技术文章和企业新闻' },
    { name: 'keywords', content: '轻集料混凝土新闻,建材行业资讯,优丁动态,混凝土技术' },
  ],
})

const categories = [
  { label: '全部', value: 'all' },
  { label: '公司新闻', value: 'company' },
  { label: '行业资讯', value: 'industry' },
  { label: '技术文章', value: 'tech' },
]

const categoryLabels: Record<string, string> = {
  company: '公司新闻',
  industry: '行业资讯',
  tech: '技术文章',
}

const activeCategory = ref('all')
const loading = ref(false)

const articles = [
  {
    id: '1', slug: 'light-aggregate-concrete-guide', title: '轻集料混凝土选型指南', category: 'tech',
    summary: '详细介绍轻集料混凝土的选型要点，包括密度等级、强度等级和应用场景的匹配原则。',
    date: '2024-03-15',
  },
  {
    id: '2', slug: 'new-production-line', title: '优丁建材新生产线正式投产', category: 'company',
    summary: '公司三期生产线正式投产运行，年产能突破100万吨，为更多客户提供优质产品。',
    date: '2024-02-20',
  },
  {
    id: '3', slug: 'industry-trends-2024', title: '2024年绿色建材行业发展趋势', category: 'industry',
    summary: '绿色建材行业迎来快速发展期，轻集料混凝土作为绿色环保建材的应用前景广阔。',
    date: '2024-01-10',
  },
  {
    id: '4', slug: 'thermal-insulation-solution', title: '轻集料混凝土保温性能分析', category: 'tech',
    summary: '深入分析轻集料混凝土的保温隔热性能，与传统保温材料对比分析。',
    date: '2023-12-05',
  },
  {
    id: '5', slug: 'quality-control-system', title: '优丁建材质量管理体系全面升级', category: 'company',
    summary: '公司引入数字化质量管理平台，实现从原材料到成品的全流程质量追溯。',
    date: '2023-11-18',
  },
  {
    id: '6', slug: 'green-building-policy', title: '绿色建筑政策对建材行业的影响', category: 'industry',
    summary: '解读最新绿色建筑政策导向，分析政策对轻集料混凝土行业的影响和发展机遇。',
    date: '2023-10-25',
  },
]

const filteredArticles = computed(() => {
  if (activeCategory.value === 'all') return articles
  return articles.filter(a => a.category === activeCategory.value)
})
</script>
