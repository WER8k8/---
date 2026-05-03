<template>
  <div class="news-page">
    <section class="news-hero bg-gradient-to-br from-primary/90 via-primary to-accent/90 py-16 md:py-24">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <AnimatedSection animation="fade-in-up" :delay="0">
          <h1 class="text-4xl md:text-5xl font-bold text-white mb-4">新闻资讯</h1>
          <p class="text-xl text-white/80 max-w-2xl mx-auto">
            了解优丁建材最新动态和行业资讯
          </p>
        </AnimatedSection>
      </div>
    </section>

    <section class="filter-section bg-surface-elevated border-b border-border">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex flex-wrap gap-3 justify-center">
          <button
            v-for="cat in categories"
            :key="cat.value"
            @click="selectedCategory = cat.value"
            :class="[
              'px-6 py-2.5 rounded-full text-sm font-medium transition-all duration-200',
              selectedCategory === cat.value
                ? 'bg-accent text-white shadow-lg'
                : 'bg-surface text-text-secondary hover:bg-accent/10 hover:text-accent border border-border'
            ]"
          >
            {{ cat.label }}
          </button>
        </div>
      </div>
    </section>

    <section class="articles-section py-12 md:py-20 bg-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div v-if="loading" class="text-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-500 mx-auto"></div>
          <p class="mt-4 text-text-secondary">加载中...</p>
        </div>

        <div v-else-if="filteredArticles.length === 0" class="text-center py-12">
          <div class="w-20 h-20 bg-surface-elevated rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-10 h-10 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p class="text-text-muted text-lg">暂无相关新闻</p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <AnimatedSection
            v-for="(article, index) in filteredArticles"
            :key="article.id"
            animation="fade-in-up"
            :delay="index * 50"
          >
            <article class="bg-white rounded-2xl border border-border hover:border-accent-500/30 hover:shadow-xl transition-all duration-300 hover:-translate-y-1 overflow-hidden group">
              <div class="aspect-[16/9] overflow-hidden bg-gradient-to-br from-accent/10 to-primary/10 relative">
                <img
                  v-if="article.cover_image"
                  :src="article.cover_image"
                  :alt="article.title"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="text-6xl opacity-30">{{ categoryIcons[article.category] || '📰' }}</span>
                </div>
                <div class="absolute top-3 left-3">
                  <span class="text-xs font-semibold bg-white/90 backdrop-blur-sm text-accent px-3 py-1 rounded-full shadow-sm">
                    {{ categoryLabels[article.category] || article.category }}
                  </span>
                </div>
              </div>
              <div class="p-6">
                <h3 class="text-lg font-semibold text-text-primary mb-2 line-clamp-2 group-hover:text-accent transition-colors">
                  <NuxtLink :to="'/news/' + article.slug">{{ article.title }}</NuxtLink>
                </h3>
                <p class="text-text-secondary text-sm mb-4 line-clamp-3">{{ article.summary }}</p>
                <div class="flex items-center justify-between text-sm pt-4 border-t border-border">
                  <span class="text-text-muted flex items-center gap-1">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ formatDate(article.published_at) }}
                  </span>
                  <NuxtLink
                    :to="'/news/' + article.slug"
                    class="text-accent font-medium hover:text-accent/80 flex items-center gap-1 group-hover:translate-x-1 transition-all"
                  >
                    阅读
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </NuxtLink>
                </div>
              </div>
            </article>
          </AnimatedSection>
        </div>
      </div>
    </section>

    <section class="cta-section py-16 bg-gradient-to-r from-accent to-primary">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">需要了解更多？</h2>
        <p class="text-white/80 mb-8 max-w-2xl mx-auto">
          联系我们获取最新行业资讯和产品动态
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <NuxtLink to="/products" class="inline-flex items-center px-8 py-4 bg-white text-accent font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-lg">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            查看产品
          </NuxtLink>
          <NuxtLink to="/contact" class="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white/10 transition-all">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            联系我们
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNewsStore } from '~/stores/news'
import { SITE_CONFIG } from '~/config/site'

const newsStore = useNewsStore()
const contactPhone = SITE_CONFIG.phone

const selectedCategory = ref('all')
const loading = computed(() => newsStore.loading)

const categories = [
  { label: '全部', value: 'all' },
  { label: '公司新闻', value: 'company' },
  { label: '行业资讯', value: 'industry' },
  { label: '产品动态', value: 'product' },
  { label: '技术文章', value: 'technology' },
]

const categoryLabels: Record<string, string> = {
  company: '公司新闻',
  industry: '行业资讯',
  product: '产品动态',
  technology: '技术文章',
}

const categoryIcons: Record<string, string> = {
  company: '🏢',
  industry: '📊',
  product: '📦',
  technology: '🔬',
}

const filteredArticles = computed(() => {
  if (selectedCategory.value === 'all') return newsStore.articles
  return newsStore.articles.filter(a => a.category === selectedCategory.value)
})

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

onMounted(async () => {
  await newsStore.fetchArticles()
})

useHead({
  title: '新闻资讯 - 优丁建材',
  meta: [
    { name: 'description', content: '优丁建材最新动态，轻集料混凝土行业资讯、技术文章和企业新闻' },
    { name: 'keywords', content: '轻集料混凝土新闻,建材行业资讯,优丁动态,混凝土技术' },
  ],
})
</script>
