<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Header -->
    <MobileNavbar>
      <div class="flex justify-between items-center h-14">
        <NuxtLink to="/mobile" class="flex items-center gap-2">
          <div class="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center">
            <span class="text-white font-bold text-sm">{{ $t('mobile.brandChar') }}</span>
          </div>
          <span class="text-lg font-bold text-gray-900">{{ $t('mobile.brandName') }}</span>
        </NuxtLink>
        <button class="p-2 rounded-lg hover:bg-gray-100 transition-colors" @click="isSearchOpen = !isSearchOpen">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>
      </div>
    </MobileNavbar>

    <!-- Page Title -->
    <div class="pt-16 px-4 pb-2">
      <h1 class="text-xl font-bold text-gray-900">{{ $t('mobile.products.pageTitle') }}</h1>
      <p class="text-sm text-gray-500 mt-1">{{ $t('mobile.products.pageSubtitle') }}</p>
    </div>

    <!-- Category Tabs -->
    <div class="sticky top-14 z-40 bg-white border-b border-gray-100">
      <div class="flex gap-2 px-4 py-3 overflow-x-auto no-scrollbar touch-pan-x snap-x">
        <button
          v-for="cat in categories"
          :key="cat.id"
          @click="selectedCategory = cat.id"
          class="flex-shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-all snap-center whitespace-nowrap"
          :class="selectedCategory === cat.id ? 'bg-blue-600 text-white shadow-md' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          {{ cat.name }}
        </button>
      </div>
    </div>

    <!-- Search Bar -->
    <div v-if="isSearchOpen" class="px-4 py-3 bg-white border-b border-gray-100">
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="$t('mobile.products.searchPlaceholder')"
          class="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all bg-gray-50"
        >
        <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>

    <!-- Products Grid with Pull-to-Refresh -->
    <MobilePerformanceLayer
      :enable-infinite-scroll="false"
      @refresh="handleRefresh"
    >
      <div class="px-4 py-4">
        <!-- Loading State -->
        <div v-if="loading" class="grid grid-cols-2 gap-3">
          <div v-for="i in 4" :key="i" class="bg-white rounded-xl overflow-hidden animate-pulse">
            <div class="aspect-square bg-gray-200" />
            <div class="p-3 space-y-2">
              <div class="h-4 bg-gray-200 rounded w-3/4" />
              <div class="h-3 bg-gray-200 rounded w-1/2" />
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="products.length === 0" class="text-center py-16">
          <svg class="w-16 h-16 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          <h3 class="text-base font-semibold text-gray-700 mb-1">{{ $t('mobile.products.noProducts') }}</h3>
          <p class="text-sm text-gray-400">{{ $t('mobile.products.noProductsDesc') }}</p>
        </div>

        <!-- Products -->
        <div v-else class="grid grid-cols-2 gap-3">
          <NuxtLink
            v-for="product in products"
            :key="product.id"
            :to="`/products/${product.slug}`"
            class="bg-white rounded-xl overflow-hidden shadow-sm border border-gray-100 active:scale-[0.97] transition-transform"
          >
            <div class="aspect-square bg-gray-100 relative overflow-hidden">
              <img
                :src="product.image_url || '/images/product-default.jpg'"
                :alt="product.name"
                class="w-full h-full object-cover"
                loading="lazy"
              >
              <div v-if="product.is_active" class="absolute top-2 right-2">
                <span class="px-2 py-0.5 bg-green-500 text-white text-[10px] font-medium rounded-full">{{ $t('mobile.products.onSale') }}</span>
              </div>
            </div>
            <div class="p-3">
              <h3 class="text-sm font-medium text-gray-900 line-clamp-2 mb-1">{{ product.name }}</h3>
              <div class="flex flex-wrap gap-1">
                <span v-if="product.density" class="px-1.5 py-0.5 bg-blue-50 text-blue-600 text-[10px] rounded-lg">{{ product.density }}</span>
                <span v-if="product.strength" class="px-1.5 py-0.5 bg-purple-50 text-purple-600 text-[10px] rounded-lg">{{ product.strength }}</span>
              </div>
            </div>
          </NuxtLink>
        </div>
      </div>
    </MobilePerformanceLayer>

    <!-- Mobile Bottom Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useProductStore } from '~/stores/product';

const { t } = useI18n();
const productStore = useProductStore();
const selectedCategory = ref<string>('all');
const searchQuery = ref('');
const isSearchOpen = ref(false);

const loading = computed(() => productStore.loading);

const categories = computed(() => [{ id: 'all', name: t('mobile.products.all') }, ...productStore.categories]);

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

watch(selectedCategory, () => {
  searchQuery.value = '';
});

onMounted(async () => {
  await productStore.fetchCategories();
  await productStore.fetchProducts();
});

async function handleRefresh() {
  await productStore.fetchProducts();
}

useHead({
  title: t('mobile.products.seoTitle'),
  meta: [
    {
      name: 'description',
      content: t('mobile.products.seoDesc'),
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
