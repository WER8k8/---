<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Header with hide on scroll -->
    <MobileNavbar
      safe-area-top
      :blur="true"
    >
      <div class="flex justify-between items-center h-14">
        <NuxtLink
          to="/"
          class="flex items-center gap-2"
        >
          <div
            class="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full flex items-center justify-center"
          >
            <span class="text-white font-bold text-sm">{{ $t('mobile.brandChar') }}</span>
          </div>
          <span class="text-lg font-bold text-gray-900">{{ $t('mobile.brandName') }}</span>
        </NuxtLink>
        <button
          class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          @click="toggleSearch"
        >
          <svg
            class="w-5 h-5 text-gray-600"
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
        </button>
      </div>
    </MobileNavbar>

    <!-- Hero Section with Scroll Reveal -->
    <section class="pt-20 px-4 pb-6">
      <MobileScrollReveal>
        <div class="text-center">
          <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 mb-3">
            {{ $t('mobile.index.heroTitle') }}
          </h1>
          <p class="text-sm sm:text-base text-gray-600 mb-6">
            {{ $t('mobile.index.heroSubtitle') }}
          </p>
          <div class="flex flex-col sm:flex-row gap-3 justify-center">
            <NuxtLink
              to="/products"
              class="mobile-btn-primary px-6 py-3 rounded-full"
            >
              {{ $t('mobile.index.browseProducts') }}
            </NuxtLink>
            <NuxtLink
              to="/contact"
              class="mobile-btn-secondary px-6 py-3 rounded-full"
            >
              {{ $t('mobile.index.contactUs') }}
            </NuxtLink>
          </div>
        </div>
      </MobileScrollReveal>
    </section>

    <!-- Product Categories with Horizontal Scroll -->
    <section class="py-4">
      <MobileScrollReveal>
        <div class="px-4 mb-3">
          <h2 class="text-lg font-semibold text-gray-900">
            {{ $t('mobile.index.productCategories') }}
          </h2>
        </div>
        <div class="touch-pan-x px-4 gap-3 flex overflow-x-auto snap-x no-scrollbar">
          <div
            v-for="cat in categories"
            :key="cat.id"
            class="flex-shrink-0 w-28 sm:w-32 bg-white rounded-xl p-4 shadow-sm border border-gray-100 snap-center"
          >
            <div class="text-2xl mb-2">
              {{ cat.icon }}
            </div>
            <div class="text-xs font-medium text-gray-700 text-center truncate">
              {{ cat.name }}
            </div>
          </div>
        </div>
      </MobileScrollReveal>
    </section>

    <!-- Products Grid with Expandable -->
    <section class="py-4 px-4">
      <MobileScrollReveal>
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold text-gray-900">
            {{ $t('mobile.index.hotProducts') }}
          </h2>
          <NuxtLink
            to="/products"
            class="text-sm text-blue-600"
          >
            {{ $t('mobile.index.viewAll') }}
          </NuxtLink>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <NuxtLink
            v-for="product in products"
            :key="product.id"
            :to="`/products/${product.slug}`"
            class="mobile-card overflow-hidden"
          >
            <div class="aspect-square bg-gray-100 relative">
              <UiLazyImage
                :src="product.image"
                :alt="product.name"
                class="w-full h-full object-cover"
              />
            </div>
            <div class="p-3">
              <h3 class="text-sm font-medium text-gray-900 text-ellipsis-2 mb-1">
                {{ product.name }}
              </h3>
              <p class="text-xs text-gray-500">
                {{ product.spec }}
              </p>
            </div>
          </NuxtLink>
        </div>
      </MobileScrollReveal>
    </section>

    <!-- Case Studies -->
    <section class="py-4 px-4">
      <MobileScrollReveal>
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-semibold text-gray-900">
            {{ $t('mobile.index.engineeringCases') }}
          </h2>
          <NuxtLink
            to="/cases"
            class="text-sm text-blue-600"
          >
            {{ $t('mobile.index.viewAll') }}
          </NuxtLink>
        </div>
        <div class="space-y-3">
          <NuxtLink
            v-for="caseItem in cases"
            :key="caseItem.id"
            :to="`/cases/${caseItem.slug}`"
            class="mobile-card p-4 flex gap-4"
          >
            <div class="w-20 h-20 rounded-lg bg-gray-100 flex-shrink-0 overflow-hidden">
              <UiLazyImage
                :src="caseItem.image"
                :alt="caseItem.title"
                class="w-full h-full object-cover"
              />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-medium text-gray-900 text-ellipsis-2 mb-1">
                {{ caseItem.title }}
              </h3>
              <p class="text-xs text-gray-500 text-ellipsis-2">
                {{ caseItem.desc }}
              </p>
            </div>
          </NuxtLink>
        </div>
      </MobileScrollReveal>
    </section>

    <!-- Contact CTA -->
    <section class="py-6 px-4">
      <MobileScrollReveal>
        <div class="bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl p-6 text-white">
          <h2 class="text-xl font-bold mb-2">
            {{ $t('mobile.index.getQuote') }}
          </h2>
          <p class="text-sm text-blue-100 mb-4">
            {{ $t('mobile.index.getQuoteDesc') }}
          </p>
          <div class="flex flex-col gap-3">
            <a
              :href="'tel:' + SITE_CONFIG.phone"
              class="mobile-btn bg-white text-blue-600 justify-center gap-2"
            >
              <svg
                class="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                />
              </svg>
              {{ $t('mobile.index.callUs') }}
            </a>
            <NuxtLink
              to="/contact"
              class="mobile-btn border-2 border-white text-white justify-center"
            >
              {{ $t('mobile.index.onlineConsult') }}
            </NuxtLink>
          </div>
        </div>
      </MobileScrollReveal>
    </section>

    <!-- Mobile Bottom Tab Bar -->
    <MobileTabBar />

    <!-- Mobile Search Modal -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="isSearchOpen"
          class="fixed inset-0 z-[100] bg-black/50 flex items-start justify-center pt-16 px-4"
          @click.self="toggleSearch"
        >
          <div class="w-full max-w-md bg-white rounded-2xl shadow-xl overflow-hidden">
            <div class="flex items-center gap-3 p-4 border-b border-gray-100">
              <svg
                class="w-5 h-5 text-gray-400"
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
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="$t('mobile.index.searchPlaceholder')"
                class="flex-1 h-11 bg-gray-50 rounded-lg px-4 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
                @keyup.enter="handleSearch"
              >
              <button
                @click="toggleSearch"
                class="p-2 hover:bg-gray-100 rounded-lg"
              >
                <svg
                  class="w-5 h-5 text-gray-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <div class="p-4">
              <p class="text-xs text-gray-500 mb-2">
                {{ $t('mobile.index.hotSearch') }}
              </p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="kw in hotKeywords"
                  :key="kw"
                  class="px-3 py-1.5 bg-gray-100 rounded-full text-sm text-gray-700 hover:bg-gray-200 transition-colors"
                  @click="searchQuery = kw"
                >
                  {{ kw }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { SITE_CONFIG } from '~/config/site';

const { t } = useI18n();

const isSearchOpen = ref(false);
const searchQuery = ref('');

const categories = computed(() => [
  { id: 1, name: t('mobile.index.catLightweight'), icon: '🏗️' },
  { id: 2, name: t('mobile.index.catCeramsite'), icon: '🧱' },
  { id: 3, name: t('mobile.index.catInsulation'), icon: '🛡️' },
  { id: 4, name: t('mobile.index.catSpecial'), icon: '⚙️' },
]);

const products = computed(() => [
  {
    id: 1,
    name: t('mobile.index.product1Name'),
    slug: 'cl30',
    image: '/images/products/cl30.jpg',
    spec: t('mobile.index.product1Spec'),
  },
  {
    id: 2,
    name: t('mobile.index.product2Name'),
    slug: 'taoli',
    image: '/images/products/taoli.jpg',
    spec: t('mobile.index.product2Spec'),
  },
  {
    id: 3,
    name: t('mobile.index.product3Name'),
    slug: 'lc35',
    image: '/images/products/lc35.jpg',
    spec: t('mobile.index.product3Spec'),
  },
  {
    id: 4,
    name: t('mobile.index.product4Name'),
    slug: 'jiaqi',
    image: '/images/products/jiaqi.jpg',
    spec: t('mobile.index.product4Spec'),
  },
]);

const cases = computed(() => [
  {
    id: 1,
    title: t('mobile.index.case1Title'),
    slug: 'daxing',
    image: '/images/cases/daxing.jpg',
    desc: t('mobile.index.case1Desc'),
  },
  {
    id: 2,
    title: t('mobile.index.case2Title'),
    slug: 'shanghai',
    image: '/images/cases/shanghai.jpg',
    desc: t('mobile.index.case2Desc'),
  },
  {
    id: 3,
    title: t('mobile.index.case3Title'),
    slug: 'shenzhen',
    image: '/images/cases/shenzhen.jpg',
    desc: t('mobile.index.case3Desc'),
  },
]);

const hotKeywords = computed(() => [
  t('mobile.index.hotKeyword1'),
  t('mobile.index.hotKeyword2'),
  t('mobile.index.hotKeyword3'),
  t('mobile.index.hotKeyword4'),
]);

function toggleSearch() {
  isSearchOpen.value = !isSearchOpen.value;
  if (!isSearchOpen.value) {
    searchQuery.value = '';
  }
}

function handleSearch() {
  if (searchQuery.value.trim()) {
    navigateTo(`/search?q=${encodeURIComponent(searchQuery.value)}`);
    toggleSearch();
  }
}

useHead({
  title: t('mobile.index.seoTitle'),
  meta: [
    { name: 'description', content: t('mobile.index.seoDesc') },
  ],
});
</script>
