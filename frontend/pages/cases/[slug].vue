<template>
  <div class="case-detail-page">
    <!-- Loading State -->
    <div
      v-if="loading"
      class="min-h-screen flex items-center justify-center"
    >
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-500" />
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="min-h-screen flex items-center justify-center"
    >
      <div class="text-center">
        <h2 class="text-2xl font-bold text-text-primary mb-4">
          {{ t('cases.detail.loadFailed') }}
        </h2>
        <p class="text-text-secondary mb-6">
          {{ error }}
        </p>
        <NuxtLink
          to="/cases"
          class="btn-primary"
        >
          {{ t('cases.detail.backToList') }}
        </NuxtLink>
      </div>
    </div>

    <!-- Case Detail -->
    <div
      v-else-if="caseItem"
      class="case-detail"
    >
      <!-- Hero Section -->
      <section class="case-hero relative h-96 md:h-[500px] overflow-hidden">
        <img
          :src="caseItem.cover_image || '/images/case-default.jpg'"
          :alt="caseItem.project_name"
          class="w-full h-full object-cover"
        >
        <div
          class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"
        />
        <div class="absolute bottom-0 left-0 right-0 p-8 md:p-16">
          <div class="max-w-7xl mx-auto">
            <div class="flex flex-wrap gap-2 mb-4">
              <span class="px-3 py-1 bg-accent/90 text-white text-sm font-medium rounded-full">
                {{ caseItem.location || t('cases.nationWide') }}
              </span>
              <span class="px-3 py-1 bg-white/20 text-white text-sm font-medium rounded-full">
                {{ caseItem.project_date || t('cases.detail.unknownDate') }}
              </span>
            </div>
            <h1 class="text-3xl md:text-5xl font-bold text-white mb-4">
              {{ caseItem.project_name }}
            </h1>
            <p class="text-lg text-white/80 max-w-2xl">
              {{ caseItem.description }}
            </p>
          </div>
        </div>
      </section>

      <!-- Breadcrumb -->
      <section class="breadcrumb-section bg-surface-elevated border-b border-border">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <nav class="flex items-center text-sm text-text-secondary">
            <NuxtLink
              to="/"
              class="hover:text-accent transition-colors"
            >
              {{ t('cases.detail.breadcrumbHome') }}
            </NuxtLink>
            <svg
              class="w-4 h-4 mx-2"
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
            <NuxtLink
              to="/cases"
              class="hover:text-accent transition-colors"
            >
              {{ t('cases.detail.breadcrumbCases') }}
            </NuxtLink>
            <svg
              class="w-4 h-4 mx-2"
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
            <span class="text-text-primary">{{ caseItem.project_name }}</span>
          </nav>
        </div>
      </section>

      <!-- Case Info Grid -->
      <section class="case-info-section py-12 md:py-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Main Content -->
            <div class="lg:col-span-2">
              <!-- Project Overview -->
              <div class="bg-surface-elevated rounded-2xl shadow-card p-8 mb-8">
                <h2 class="text-2xl font-bold text-text-primary mb-6">
                  {{ t('cases.detail.projectOverview') }}
                </h2>
                <div class="prose prose-lg max-w-none text-text-secondary">
                  <p v-if="caseItem.description">
                    {{ caseItem.description }}
                  </p>
                  <p
                    v-else
                    class="text-text-secondary/60"
                  >
                    {{ t('cases.detail.noDesc') }}
                  </p>
                </div>
              </div>

              <!-- Project Images -->
              <div
                v-if="caseItem.images && caseItem.images.length > 0"
                class="bg-surface-elevated rounded-2xl shadow-card p-8 mb-8"
              >
                <h2 class="text-2xl font-bold text-text-primary mb-6">
                  {{ t('cases.detail.projectImages') }}
                </h2>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div
                    v-for="image in caseItem.images"
                    :key="image.id"
                    class="rounded-xl overflow-hidden aspect-video"
                  >
                    <img
                      :src="image.image_url"
                      :alt="image.image_alt || caseItem.project_name"
                      class="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    >
                  </div>
                </div>
              </div>

              <!-- Materials Used -->
              <div
                v-if="caseItem.materials_used"
                class="bg-surface-elevated rounded-2xl shadow-card p-8 mb-8"
              >
                <h2 class="text-2xl font-bold text-text-primary mb-6">
                  {{ t('cases.detail.materialsUsed') }}
                </h2>
                <div class="prose prose-lg max-w-none text-text-secondary">
                  <p>{{ caseItem.materials_used }}</p>
                </div>
              </div>
            </div>

            <!-- Sidebar -->
            <div class="lg:col-span-1">
              <!-- Project Details -->
              <div class="bg-surface-elevated rounded-2xl shadow-card p-6 mb-8 sticky top-24">
                <h3 class="text-xl font-bold text-text-primary mb-6">
                  {{ t('cases.detail.projectInfo') }}
                </h3>
                <dl class="space-y-4">
                  <div v-if="caseItem.client_name">
                    <dt class="text-sm font-medium text-text-secondary">
                      {{ t('cases.detail.clientName') }}
                    </dt>
                    <dd class="mt-1 text-text-primary">
                      {{ caseItem.client_name }}
                    </dd>
                  </div>
                  <div v-if="caseItem.location">
                    <dt class="text-sm font-medium text-text-secondary">
                      {{ t('cases.detail.projectLocation') }}
                    </dt>
                    <dd class="mt-1 text-text-primary">
                      {{ caseItem.location }}
                    </dd>
                  </div>
                  <div v-if="caseItem.construction_area">
                    <dt class="text-sm font-medium text-text-secondary">
                      {{ t('cases.detail.constructionArea') }}
                    </dt>
                    <dd class="mt-1 text-text-primary">
                      {{ caseItem.construction_area }}
                    </dd>
                  </div>
                  <div v-if="caseItem.project_date">
                    <dt class="text-sm font-medium text-text-secondary">
                      {{ t('cases.detail.projectDate') }}
                    </dt>
                    <dd class="mt-1 text-text-primary">
                      {{ caseItem.project_date }}
                    </dd>
                  </div>
                  <div>
                    <dt class="text-sm font-medium text-text-secondary">
                      {{ t('cases.detail.viewCount') }}
                    </dt>
                    <dd class="mt-1 text-text-primary">
                      {{ caseItem.view_count }} {{ t('cases.detail.times') }}
                    </dd>
                  </div>
                </dl>

                <!-- CTA -->
                <div class="mt-8 pt-6 border-t border-border">
                  <p class="text-sm text-text-secondary mb-4">
                    {{ t('cases.detail.interestedContact') }}
                  </p>
                  <NuxtLink
                    to="/contact"
                    class="btn-primary w-full text-center block"
                  >
                    {{ t('cases.detail.consultNow') }}
                  </NuxtLink>
                  <a
                    :href="`tel:${contactPhone}`"
                    class="btn-outline w-full text-center block mt-3"
                  >
                    {{ t('cases.detail.phoneConsult') }}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Related Cases -->
      <section class="related-cases py-12 md:py-16 bg-surface-elevated">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 class="text-2xl font-bold text-text-primary mb-8">
            {{ t('cases.detail.relatedCases') }}
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <NuxtLink
              v-for="related in relatedCases"
              :key="related.id"
              :to="`/cases/${related.slug}`"
              class="case-card group bg-surface rounded-2xl shadow-card overflow-hidden hover:shadow-card-hover hover:-translate-y-2 transition-all duration-300"
            >
              <div class="h-48 overflow-hidden bg-gradient-to-br from-accent/5 to-primary/5">
                <img
                  :src="related.cover_image || '/images/case-default.jpg'"
                  :alt="related.project_name"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                >
              </div>
              <div class="p-6">
                <h3
                  class="text-lg font-semibold text-text-primary mb-2 group-hover:text-accent transition-colors"
                >
                  {{ related.project_name }}
                </h3>
                <p class="text-sm text-text-secondary line-clamp-2">
                  {{ related.description || t('cases.clickViewDetails') }}
                </p>
              </div>
            </NuxtLink>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useCaseStore } from '~/stores/case';
import { SITE_CONFIG } from '~/config/site';

const route = useRoute();
const { t } = useI18n();
const caseStore = useCaseStore();
const contactPhone = SITE_CONFIG.phone;

const { slug } = route.params as { slug: string };

await caseStore.fetchCaseBySlug(slug);

const caseItem = computed(() => caseStore.currentCase);
const loading = computed(() => caseStore.loading);
const error = computed(() => caseStore.error);

const relatedCases = computed(() => {
  return caseStore.publishedCases.filter((c) => c.id !== caseItem.value?.id).slice(0, 3);
});

useHead({
  title: computed(() =>
    caseItem.value ? `${caseItem.value.project_name} - ${t('cases.seo.detailTitle')}` : t('cases.seo.detailFallbackTitle')
  ),
  meta: [
    { name: 'description', content: computed(() => caseItem.value?.description || '') },
    { property: 'og:title', content: computed(() => caseItem.value?.project_name || '') },
    { property: 'og:description', content: computed(() => caseItem.value?.description || '') },
    { property: 'og:type', content: 'article' },
    { property: 'og:url', content: computed(() => `${SITE_CONFIG.url}/cases/${slug}`) },
    {
      property: 'og:image',
      content: computed(
        () =>
          caseItem.value?.cover_image || `${SITE_CONFIG.url}/images/case-default.jpg`
      ),
    },
  ],
});
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
