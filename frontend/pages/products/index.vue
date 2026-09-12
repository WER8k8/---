<template>
  <div class="products-page">
    <!-- Hero Section -->
    <section
      class="products-hero bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20"
    >
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <AnimatedSection
          animation="fade-in-up"
          :delay="0"
        >
          <h1
            class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4"
          >
            {{ t('products.title') }}
          </h1>
          <p
            class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto"
          >
            {{ t('products.subtitle') }}
          </p>
        </AnimatedSection>
      </div>
    </section>

    <!-- Filter & Search -->
    <section
      class="filter-section bg-surface-elevated border-b border-border sticky top-14 lg:top-20 z-40"
    >
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-3 sm:py-4">
        <div class="flex flex-col md:flex-row gap-3 sm:gap-4 items-center justify-between">
          <!-- Category Filter -->
          <div class="flex flex-wrap gap-2 justify-center w-full md:w-auto">
            <button
              v-for="cat in categories"
              :key="cat.id"
              @click="selectedCategory = cat.id"
              :class="[
                'px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs sm:text-sm font-medium transition-all duration-200 min-w-[70px] sm:min-w-auto text-center',
                selectedCategory === cat.id
                  ? 'bg-primary text-white shadow-md'
                  : 'bg-surface text-text-secondary hover:bg-primary/10 hover:text-primary',
              ]"
            >
              {{ cat.name }}
            </button>
          </div>

          <!-- Search -->
          <div class="relative w-full md:w-48 lg:w-64">
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="t('products.searchPlaceholder')"
              class="w-full pl-9 pr-3 py-1.5 sm:py-2 border border-border rounded-lg sm:rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm"
            >
            <svg
              class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-text-secondary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>
      </div>
    </section>

    <!-- Products Grid -->
    <section class="products-section py-8 sm:py-10 lg:py-14">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <!-- Loading State -->
        <div
          v-if="loading"
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6"
        >
          <div
            v-for="i in 6"
            :key="i"
            class="product-card-skeleton animate-pulse"
          >
            <div class="bg-gray-200 h-36 sm:h-40 lg:h-48 rounded-t-xl sm:rounded-t-2xl" />
            <div class="p-4 sm:p-6">
              <div class="h-5 sm:h-6 bg-gray-200 rounded w-3/4 mb-3 sm:mb-4" />
              <div class="h-3 sm:h-4 bg-gray-200 rounded w-full mb-1.5 sm:mb-2" />
              <div class="h-3 sm:h-4 bg-gray-200 rounded w-2/3" />
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-else-if="products.length === 0"
          class="text-center py-10 sm:py-16"
        >
          <svg
            class="w-16 h-16 sm:w-24 sm:h-24 mx-auto text-text-secondary/30 mb-3 sm:mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
            />
          </svg>
          <h3 class="text-base sm:text-lg lg:text-xl font-semibold text-text-primary mb-2">
            {{ t('products.noProducts') }}
          </h3>
          <p class="text-xs sm:text-sm text-text-secondary">
            {{ t('products.noProductsDesc') }}
          </p>
        </div>

        <!-- Products List -->
        <div
          v-else
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6"
        >
          <AnimatedSection
            v-for="(product, index) in paginatedProducts"
            :key="product.id"
            animation="fade-in-up"
            :delay="index * 50"
          >
            <NuxtLink
              :to="`/products/${product.slug}`"
              class="product-card group bg-surface-elevated rounded-xl sm:rounded-2xl shadow-card overflow-hidden hover:shadow-card-hover hover:-translate-y-1.5 transition-all duration-300"
            >
              <!-- Product Image -->
              <div
                class="product-image relative h-36 sm:h-40 lg:h-48 overflow-hidden bg-gradient-to-br from-primary/5 to-accent/5"
              >
                <img
                  :src="product.image_url || '/images/product-default.jpg'"
                  :alt="product.name"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                >
                <div class="absolute top-2 sm:top-3 lg:top-4 right-2 sm:right-3 lg:right-4">
                  <span
                    v-if="product.is_active"
                    class="px-2 py-0.5 sm:px-3 sm:py-1 bg-green-500 text-white text-xs font-medium rounded-full"
                  >
                    {{ t('products.inStock') }}
                  </span>
                </div>
              </div>

              <!-- Product Info -->
              <div class="p-3 sm:p-4 lg:p-6">
                <h3
                  class="text-sm sm:text-base lg:text-lg font-semibold text-text-primary mb-1.5 sm:mb-2 group-hover:text-primary transition-colors"
                >
                  {{ product.name }}
                </h3>
                <p
                  v-if="product.subtitle"
                  class="text-xs sm:text-sm text-primary mb-2 sm:mb-3"
                >
                  {{ product.subtitle }}
                </p>
                <p class="text-xs sm:text-sm text-text-secondary line-clamp-2 mb-3 sm:mb-4">
                  {{ product.description || t('products.clickViewDetails') }}
                </p>

                <!-- Quick Specs -->
                <div class="flex flex-wrap gap-1.5 sm:gap-2 mb-3 sm:mb-4">
                  <span
                    v-if="product.density"
                    class="spec-tag px-1.5 py-0.5 sm:px-2 sm:py-1 bg-primary/10 text-primary text-xs rounded-lg"
                  >
                    {{ t('products.density') }} {{ product.density }}
                  </span>
                  <span
                    v-if="product.strength"
                    class="spec-tag px-1.5 py-0.5 sm:px-2 sm:py-1 bg-accent/10 text-accent text-xs rounded-lg"
                  >
                    {{ t('products.strength') }} {{ product.strength }}
                  </span>
                </div>

                <!-- View Count -->
                <div
                  class="flex items-center justify-between text-xs sm:text-sm text-text-secondary"
                >
                  <div class="flex items-center">
                    <svg
                      class="w-3 h-3 sm:w-4 sm:h-4 mr-1"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                      />
                    </svg>
                    {{ product.view_count }} {{ t('products.viewCount') }}
                  </div>
                  <span class="text-primary font-medium group-hover:underline"> {{ t('products.viewDetails') }} </span>
                </div>
              </div>
            </NuxtLink>
          </AnimatedSection>
        </div>

        <!-- Pagination -->
        <div
          v-if="totalPages > 1"
          class="mt-8 sm:mt-10 lg:mt-12 flex justify-center"
        >
          <nav class="flex items-center gap-1.5 sm:gap-2">
            <button
              @click="currentPage--"
              :disabled="currentPage === 1"
              class="px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg border border-border text-xs sm:text-sm text-text-secondary hover:bg-primary/10 hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all min-w-[60px] sm:min-w-[80px] text-center"
            >
              {{ t('products.prevPage') }}
            </button>
            <button
              v-for="page in visiblePages"
              :key="page"
              @click="currentPage = page"
              :class="[
                'w-8 h-8 sm:w-10 sm:h-10 rounded-lg font-medium text-xs sm:text-sm transition-all',
                currentPage === page
                  ? 'bg-primary text-white'
                  : 'border border-border text-text-secondary hover:bg-primary/10 hover:text-primary',
              ]"
            >
              {{ page }}
            </button>
            <button
              @click="currentPage++"
              :disabled="currentPage === totalPages"
              class="px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg border border-border text-xs sm:text-sm text-text-secondary hover:bg-primary/10 hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all min-w-[60px] sm:min-w-[80px] text-center"
            >
              {{ t('products.nextPage') }}
            </button>
          </nav>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section
      class="cta-section py-16 bg-gradient-to-br from-primary/5 via-surface-elevated to-accent/5"
    >
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <AnimatedSection
          animation="fade-in-up"
          :delay="0"
        >
          <h2 class="text-2xl md:text-3xl font-bold text-text-primary mb-4">
            {{ t('products.ctaTitle') }}
          </h2>
          <p class="text-lg text-text-secondary mb-8">
            {{ t('products.ctaDesc') }}
          </p>
          <div class="flex flex-wrap justify-center gap-4">
            <NuxtLink
              to="/contact"
              class="btn-primary btn-primary-lg"
            >
              {{ t('products.ctaConsult') }}
            </NuxtLink>
            <a
              :href="`tel:${contactPhone}`"
              class="btn-outline"
            > {{ t('products.ctaPhonePrefix') }}{{ contactPhone }} </a>
          </div>
        </AnimatedSection>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useProductStore } from '~/stores/product';
import { SITE_CONFIG } from '~/config/site';

const { t } = useI18n();
const productStore = useProductStore();
const contactPhone = SITE_CONFIG.phone;

const selectedCategory = ref<string>('all');
const searchQuery = ref('');
const currentPage = ref(1);
const pageSize = 9;

const loading = computed(() => productStore.loading);

const categories = computed(() => [{ id: 'all', name: t('products.filterAll') }, ...productStore.categories]);

const products = computed(() => {
  let filtered = productStore.products;

  if (selectedCategory.value !== 'all') {
    filtered = filtered.filter((p) => p.category_id === selectedCategory.value);
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(
      (p) =>
        p.name.toLowerCase().includes(query) ||
        (p.description && p.description.toLowerCase().includes(query))
    );
  }

  return filtered;
});

const totalPages = computed(() => Math.ceil(products.value.length / pageSize));
const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return products.value.slice(start, start + pageSize);
});

const visiblePages = computed(() => {
  const pages: number[] = [];
  const maxVisible = 5;
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2));
  const end = Math.min(totalPages.value, start + maxVisible - 1);

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1);
  }

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return pages;
});

watch([selectedCategory, searchQuery], () => {
  currentPage.value = 1;
});

onMounted(async () => {
  await productStore.fetchCategories();
  await productStore.fetchProducts();
});

useHead({
  title: computed(() => t('products.seo.title')),
  meta: [
    {
      name: 'description',
      content: computed(() => t('products.seo.desc')),
    },
    { name: 'keywords', content: computed(() => t('products.seo.keywords')) },
  ],
});
</script>

<style scoped>
.product-card-skeleton {
  border-radius: 1rem;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.spec-tag {
  white-space: nowrap;
}
</style>
