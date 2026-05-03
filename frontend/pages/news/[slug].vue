<template>
  <div class="news-detail-page">
    <div v-if="loading" class="min-h-screen flex items-center justify-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-500"></div>
    </div>

    <div v-else-if="error" class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <h2 class="text-2xl font-bold text-text-primary mb-4">文章加载失败</h2>
        <p class="text-text-secondary mb-6">{{ error }}</p>
        <NuxtLink to="/news" class="btn-primary">返回新闻列表</NuxtLink>
      </div>
    </div>

    <div v-else-if="article" class="news-detail">
      <section class="article-hero relative h-96 md:h-[500px] overflow-hidden">
        <img
          :src="article.cover_image || '/images/news-default.jpg'"
          :alt="article.title"
          class="w-full h-full object-cover"
        />
        <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>
        <div class="absolute bottom-0 left-0 right-0 p-8 md:p-16">
          <div class="max-w-4xl mx-auto">
            <div class="flex flex-wrap gap-2 mb-4">
              <span class="px-3 py-1 bg-accent/90 text-white text-sm font-medium rounded-full">
                {{ categoryLabels[article.category] || article.category }}
              </span>
              <span v-if="article.author" class="px-3 py-1 bg-white/20 text-white text-sm font-medium rounded-full">
                {{ article.author }}
              </span>
            </div>
            <h1 class="text-3xl md:text-5xl font-bold text-white mb-4">{{ article.title }}</h1>
            <p v-if="article.subtitle" class="text-xl text-white/80 mb-4">{{ article.subtitle }}</p>
            <div class="flex flex-wrap gap-4 text-white/70 text-sm">
              <span class="flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {{ formatDate(article.published_at) }}
              </span>
              <span class="flex items-center gap-1">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                {{ article.view_count }} 次阅读
              </span>
            </div>
          </div>
        </div>
      </section>

      <section class="article-content bg-surface py-12 md:py-16">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="prose prose-lg max-w-none" v-html="article.content"></div>

          <div v-if="article.tags" class="mt-12 pt-8 border-t border-border">
            <h3 class="text-sm font-medium text-text-secondary mb-3">标签</h3>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in parseTags(article.tags)"
                :key="tag"
                class="px-3 py-1 bg-accent/10 text-accent text-sm rounded-full"
              >
                {{ tag }}
              </span>
            </div>
          </div>

          <div class="mt-12 pt-8 border-t border-border flex flex-col sm:flex-row justify-between items-center gap-4">
            <NuxtLink to="/news" class="text-accent hover:text-accent/80 flex items-center gap-2">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
              返回新闻列表
            </NuxtLink>
            <div class="flex items-center gap-4">
              <span class="text-text-secondary text-sm">分享：</span>
              <button class="p-2 rounded-full bg-surface-elevated hover:bg-accent/10 transition-colors" title="微信分享">
                <svg class="w-5 h-5 text-text-secondary" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.028.14-.028.213 0 .187.125.34.31.34a.35.35 0 00.16-.04l1.903-1.142a.87.87 0 01.45-.126c.09 0 .18.014.265.042a9.07 9.07 0 002.806.44c.28 0 .555-.014.825-.04a6.13 6.13 0 01-.23-1.65c0-3.38 3.27-6.12 7.31-6.12h.33c-.62-3.32-3.87-5.95-7.83-5.95zm-2.6 4.41c.67 0 1.21.54 1.21 1.21s-.54 1.21-1.21 1.21-1.21-.54-1.21-1.21.54-1.21 1.21-1.21zm5.19 0c.67 0 1.21.54 1.21 1.21s-.54 1.21-1.21 1.21-1.21-.54-1.21-1.21.54-1.21 1.21-1.21zm5.69 3.05c-3.59 0-6.5 2.44-6.5 5.45 0 3.01 2.91 5.45 6.5 5.45.73 0 1.43-.11 2.09-.31a.63.63 0 01.33.09l1.38.83a.25.25 0 00.12.03c.13 0 .23-.1.23-.24a.6.6 0 00-.02-.15l-.28-1.06a.42.42 0 01.15-.47c1.3-.96 2.13-2.38 2.13-3.96 0-3.01-2.91-5.45-6.5-5.45zm-2.27 3.07c.47 0 .85.38.85.85s-.38.85-.85.85-.85-.38-.85-.85.38-.85.85-.85zm4.54 0c.47 0 .85.38.85.85s-.38.85-.85.85-.85-.38-.85-.85.38-.85.85-.85z"/>
                </svg>
              </button>
              <button class="p-2 rounded-full bg-surface-elevated hover:bg-accent/10 transition-colors" title="微博分享">
                <svg class="w-5 h-5 text-text-secondary" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M10.1 18.3c-3.5.4-6.6-1.2-6.8-3.6-.3-2.4 2.4-4.7 5.9-5.1 3.5-.4 6.6 1.2 6.8 3.6.3 2.4-2.4 4.7-5.9 5.1zm6.9-9.4c-.3-.9-1.3-1.4-2.2-1.1l-.1-.1c.1-.3.1-.6.1-.9 0-2.2-2.2-4-5-4s-5 1.8-5 4c0 .3 0 .6.1.9l-.1.1c-.9-.3-1.9.2-2.2 1.1-.3.9.2 1.9 1.1 2.2.1 0 .2.1.3.1-.4.8-.6 1.7-.6 2.6 0 3.3 3.1 6 7 6s7-2.7 7-6c0-.9-.2-1.8-.6-2.6.1 0 .2-.1.3-.1.9-.3 1.4-1.3 1.1-2.2zM9.5 14.5c-.3.1-.6-.1-.7-.4-.1-.3.1-.6.4-.7.3-.1.6.1.7.4.1.3-.1.6-.4.7zm1.8-.6c-.3.1-.6-.1-.7-.4-.1-.3.1-.6.4-.7.3-.1.6.1.7.4.1.3-.1.6-.4.7z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </section>

      <section v-if="relatedArticles.length > 0" class="related-articles py-12 md:py-16 bg-surface-elevated">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 class="text-2xl font-bold text-text-primary mb-8">相关文章</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <NuxtLink
              v-for="related in relatedArticles"
              :key="related.id"
              :to="'/news/' + related.slug"
              class="bg-white rounded-xl border border-border hover:border-accent-500/30 hover:shadow-lg transition-all overflow-hidden group"
            >
              <div class="aspect-[16/9] overflow-hidden bg-gradient-to-br from-accent/10 to-primary/10">
                <img
                  v-if="related.cover_image"
                  :src="related.cover_image"
                  :alt="related.title"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <span class="text-4xl opacity-30">{{ categoryIcons[related.category] || '📰' }}</span>
                </div>
              </div>
              <div class="p-4">
                <h3 class="text-base font-semibold text-text-primary line-clamp-2 group-hover:text-accent transition-colors">
                  {{ related.title }}
                </h3>
                <p class="text-text-muted text-sm mt-2">{{ formatDate(related.published_at) }}</p>
              </div>
            </NuxtLink>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useNewsStore } from '~/stores/news'
import { SITE_CONFIG } from '~/config/site'

const route = useRoute()
const newsStore = useNewsStore()
const contactPhone = SITE_CONFIG.phone

const { slug } = route.params as { slug: string }

await newsStore.fetchArticleBySlug(slug)

const article = computed(() => newsStore.currentArticle)
const loading = computed(() => newsStore.loading)
const error = computed(() => newsStore.error)

const relatedArticles = computed(() => {
  return newsStore.articles
    .filter(a => a.id !== article.value?.id && a.category === article.value?.category)
    .slice(0, 3)
})

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

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '未知'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function parseTags(tagsStr: string | null): string[] {
  if (!tagsStr) return []
  try {
    return JSON.parse(tagsStr)
  } catch {
    return tagsStr.split(',').map(t => t.trim()).filter(Boolean)
  }
}

useHead({
  title: computed(() => article.value ? `${article.value.title} - 新闻资讯 | 优丁建材` : '文章详情 | 优丁建材'),
  meta: [
    { name: 'description', content: computed(() => article.value?.summary || '') },
    { property: 'og:title', content: computed(() => article.value?.title || '') },
    { property: 'og:description', content: computed(() => article.value?.summary || '') },
    { property: 'og:type', content: 'article' },
    { property: 'og:url', content: computed(() => `https://www.youdingjiancai.com/news/${slug}`) },
    { property: 'og:image', content: computed(() => article.value?.cover_image || 'https://www.youdingjiancai.com/images/news-default.jpg') },
  ],
})
</script>

<style scoped>
.prose :deep(h1) {
  @apply text-3xl font-bold text-text-primary mt-8 mb-4;
}
.prose :deep(h2) {
  @apply text-2xl font-bold text-text-primary mt-6 mb-3;
}
.prose :deep(h3) {
  @apply text-xl font-semibold text-text-primary mt-5 mb-2;
}
.prose :deep(p) {
  @apply text-text-secondary leading-relaxed mb-4;
}
.prose :deep(img) {
  @apply rounded-xl my-6;
}
.prose :deep(ul) {
  @apply list-disc list-inside mb-4;
}
.prose :deep(ol) {
  @apply list-decimal list-inside mb-4;
}
.prose :deep(li) {
  @apply text-text-secondary mb-2;
}
.prose :deep(blockquote) {
  @apply border-l-4 border-accent-500 pl-4 italic text-text-secondary my-6;
}
.prose :deep(a) {
  @apply text-accent hover:text-accent/80 underline;
}
.prose :deep(code) {
  @apply bg-surface-elevated px-2 py-1 rounded text-sm;
}
.prose :deep(pre) {
  @apply bg-surface-elevated p-4 rounded-xl overflow-x-auto my-6;
}
.prose :deep(table) {
  @apply w-full border-collapse my-6;
}
.prose :deep(th) {
  @apply bg-surface-elevated px-4 py-2 text-left font-semibold border border-border;
}
.prose :deep(td) {
  @apply px-4 py-2 border border-border;
}
</style>
