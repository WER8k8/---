<template>
  <div class="news-page">
    <section class="news-hero bg-gradient-to-br from-[#667eea] to-[#764ba2] py-16 md:py-24">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <AnimatedSection
          animation="fade-in-up"
          :delay="0"
        >
          <h1 class="text-4xl md:text-5xl font-bold text-white mb-4">
            {{ t('news.title') }}
          </h1>
          <p class="text-xl text-white/80 max-w-2xl mx-auto">
            {{ t('news.subtitle') }}
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
                : 'bg-surface text-text-secondary hover:bg-accent/10 hover:text-accent border border-border',
            ]"
          >
            {{ cat.label }}
          </button>
        </div>
      </div>
    </section>

    <section class="articles-section py-12 md:py-20 bg-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div
          v-if="loading"
          class="text-center py-12"
        >
          <div
            class="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-500 mx-auto"
          />
          <p class="mt-4 text-text-secondary">
            {{ t('news.loading') }}
          </p>
        </div>

        <div
          v-else-if="filteredArticles.length === 0"
          class="text-center py-12"
        >
          <div
            class="w-20 h-20 bg-surface-elevated rounded-full flex items-center justify-center mx-auto mb-4"
          >
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
            {{ t('news.noNews') }}
          </p>
        </div>

        <div
          v-else
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          <AnimatedSection
            v-for="(article, index) in filteredArticles"
            :key="article.id"
            animation="fade-in-up"
            :delay="index * 50"
          >
            <article
              class="bg-white rounded-2xl border border-border hover:border-accent-500/30 hover:shadow-xl transition-all duration-300 hover:-translate-y-1 overflow-hidden group"
            >
              <div
                class="aspect-[16/9] overflow-hidden bg-gradient-to-br from-accent/10 to-primary/10 relative"
              >
                <img
                  v-if="article.cover_image"
                  :src="article.cover_image"
                  :alt="article.title"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                >
                <div
                  v-else
                  class="w-full h-full flex items-center justify-center"
                >
                  <span class="text-6xl opacity-30">{{
                    categoryIcons[article.category] || '📰'
                  }}</span>
                </div>
                <div class="absolute top-3 left-3">
                  <span
                    class="text-xs font-semibold bg-white/90 backdrop-blur-sm text-accent px-3 py-1 rounded-full shadow-sm"
                  >
                    {{ categoryLabels[article.category] || article.category }}
                  </span>
                </div>
              </div>
              <div class="p-6">
                <h3
                  class="text-lg font-semibold text-text-primary mb-2 line-clamp-2 group-hover:text-accent transition-colors"
                >
                  <NuxtLink :to="'/news/' + article.slug">
                    {{ article.title }}
                  </NuxtLink>
                </h3>
                <p class="text-text-secondary text-sm mb-4 line-clamp-3">
                  {{ article.summary }}
                </p>
                <div class="flex items-center justify-between text-sm pt-4 border-t border-border">
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
                    {{ formatDate(article.published_at) }}
                  </span>
                  <NuxtLink
                    :to="'/news/' + article.slug"
                    class="text-accent font-medium hover:text-accent/80 flex items-center gap-1 group-hover:translate-x-1 transition-all"
                  >
                    {{ t('news.read') }}
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
          </AnimatedSection>
        </div>
      </div>
    </section>

    <section class="cta-section py-16 bg-gradient-to-r from-primary to-primary-dark">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">
          {{ t('news.ctaTitle') }}
        </h2>
        <p class="text-white/80 mb-8 max-w-2xl mx-auto">
          {{ t('news.ctaDesc') }}
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <NuxtLink
            to="/products"
            class="inline-flex items-center px-8 py-4 bg-white text-primary font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-lg"
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
            {{ t('news.viewProducts') }}
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
            {{ t('news.contactUs') }}
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useNewsStore } from '~/stores/news';
import { SITE_CONFIG } from '~/config/site';

const { t } = useI18n();
const newsStore = useNewsStore();
const contactPhone = SITE_CONFIG.phone;

const selectedCategory = ref('all');
const loading = computed(() => newsStore.loading);

const categories = computed(() => [
  { label: t('news.filterAll'), value: 'all' },
  { label: t('news.filterCompany'), value: 'company' },
  { label: t('news.filterIndustry'), value: 'industry' },
  { label: t('news.filterProduct'), value: 'product' },
  { label: t('news.filterTechnology'), value: 'technology' },
]);

const categoryLabels = computed<Record<string, string>>(() => ({
  company: t('news.filterCompany'),
  industry: t('news.filterIndustry'),
  product: t('news.filterProduct'),
  technology: t('news.filterTechnology'),
}));

const categoryIcons: Record<string, string> = {
  company: '🏢',
  industry: '📊',
  product: '📦',
  technology: '🔬',
};

const filteredArticles = computed(() => {
  if (selectedCategory.value === 'all') return newsStore.articles;
  return newsStore.articles.filter((a) => a.category === selectedCategory.value);
});

function formatDate(dateStr: string | null): string {
  if (!dateStr) return t('news.unknownDate');
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

onMounted(async () => {
  await newsStore.fetchArticles();
});

useHead({
  title: computed(() => t('news.seo.title')),
  meta: [
    { name: 'description', content: computed(() => t('news.seo.desc')) },
    { name: 'keywords', content: computed(() => t('news.seo.keywords')) },
  ],
});
</script>
