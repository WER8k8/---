<template>
  <div class="products-page">
    <!-- Hero Section -->
    <section class="products-hero bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-16 md:py-24">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <AnimatedSection
          animation="fade-in-up"
          :delay="0"
        >
          <h1 class="text-4xl md:text-5xl font-bold text-text-primary mb-4">
            产品中心
          </h1>
          <p class="text-xl text-text-secondary max-w-2xl mx-auto">
            专业轻集料混凝土与保温材料，满足各类建筑节能需求
          </p>
        </AnimatedSection>
      </div>
    </section>

    <!-- Filter & Search -->
    <section class="filter-section bg-surface-elevated border-b border-border">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex flex-col md:flex-row gap-4 items-center justify-between">
          <!-- Category Filter -->
          <div class="flex flex-wrap gap-2">
            <button
              v-for="cat in categories"
              :key="cat.id"
              @click="selectedCategory = cat.id"
              :class="[
                'px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
                selectedCategory === cat.id
                  ? 'bg-primary text-white shadow-md'
                  : 'bg-surface text-text-secondary hover:bg-primary/10 hover:text-primary'
              ]"
            >
              {{ cat.name }}
            </button>
          </div>

          <!-- Search -->
          <div class="relative w-full md:w-64">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索产品..."
              class="w-full pl-10 pr-4 py-2 border border-border rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
            >
            <svg
              class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary"
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
    <section class="products-section py-12 md:py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- Loading State -->
        <div
          v-if="loading"
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          <div
            v-for="i in 6"
            :key="i"
            class="product-card-skeleton animate-pulse"
          >
            <div class="bg-gray-200 h-48 rounded-t-2xl" />
            <div class="p-6">
              <div class="h-6 bg-gray-200 rounded w-3/4 mb-4" />
              <div class="h-4 bg-gray-200 rounded w-full mb-2" />
              <div class="h-4 bg-gray-200 rounded w-2/3" />
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div
          v-else-if="products.length === 0"
          class="text-center py-16"
        >
          <svg
            class="w-24 h-24 mx-auto text-text-secondary/30 mb-4"
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
          <h3 class="text-xl font-semibold text-text-primary mb-2">
            暂无产品
          </h3>
          <p class="text-text-secondary">
            当前分类下暂无产品，请稍后查看
          </p>
        </div>

        <!-- Products List -->
        <div
          v-else
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          <AnimatedSection
            v-for="(product, index) in paginatedProducts"
            :key="product.id"
            animation="fade-in-up"
            :delay="index * 50"
          >
            <NuxtLink
              :to="`/products/${product.slug}`"
              class="product-card group bg-surface-elevated rounded-2xl shadow-card overflow-hidden hover:shadow-card-hover hover:-translate-y-2 transition-all duration-300"
            >
              <!-- Product Image -->
              <div class="product-image relative h-48 overflow-hidden bg-gradient-to-br from-primary/5 to-accent/5">
                <img
                  :src="product.image_url || '/images/product-default.jpg'"
                  :alt="product.name"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                >
                <div class="absolute top-4 right-4">
                  <span
                    v-if="product.is_active"
                    class="px-3 py-1 bg-green-500 text-white text-xs font-medium rounded-full"
                  >
                    在售
                  </span>
                </div>
              </div>

              <!-- Product Info -->
              <div class="p-6">
                <h3 class="text-lg font-semibold text-text-primary mb-2 group-hover:text-primary transition-colors">
                  {{ product.name }}
                </h3>
                <p
                  v-if="product.subtitle"
                  class="text-sm text-primary mb-3"
                >
                  {{ product.subtitle }}
                </p>
                <p class="text-sm text-text-secondary line-clamp-2 mb-4">
                  {{ product.description || '点击查看详情' }}
                </p>

                <!-- Quick Specs -->
                <div class="flex flex-wrap gap-2 mb-4">
                  <span
                    v-if="product.density"
                    class="spec-tag px-2 py-1 bg-primary/10 text-primary text-xs rounded-lg"
                  >
                    密度 {{ product.density }}
                  </span>
                  <span
                    v-if="product.strength"
                    class="spec-tag px-2 py-1 bg-accent/10 text-accent text-xs rounded-lg"
                  >
                    强度 {{ product.strength }}
                  </span>
                </div>

                <!-- View Count -->
                <div class="flex items-center justify-between text-sm text-text-secondary">
                  <div class="flex items-center">
                    <svg
                      class="w-4 h-4 mr-1"
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
                    {{ product.view_count }} 次浏览
                  </div>
                  <span class="text-primary font-medium group-hover:underline">
                    查看详情 →
                  </span>
                </div>
              </div>
            </NuxtLink>
          </AnimatedSection>
        </div>

        <!-- Pagination -->
        <div
          v-if="totalPages > 1"
          class="mt-12 flex justify-center"
        >
          <nav class="flex items-center gap-2">
            <button
              @click="currentPage--"
              :disabled="currentPage === 1"
              class="px-4 py-2 rounded-lg border border-border text-text-secondary hover:bg-primary/10 hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              上一页
            </button>
            <button
              v-for="page in visiblePages"
              :key="page"
              @click="currentPage = page"
              :class="[
                'w-10 h-10 rounded-lg font-medium transition-all',
                currentPage === page
                  ? 'bg-primary text-white'
                  : 'border border-border text-text-secondary hover:bg-primary/10 hover:text-primary'
              ]"
            >
              {{ page }}
            </button>
            <button
              @click="currentPage++"
              :disabled="currentPage === totalPages"
              class="px-4 py-2 rounded-lg border border-border text-text-secondary hover:bg-primary/10 hover:text-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              下一页
            </button>
          </nav>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section py-16 bg-gradient-to-br from-primary/5 via-surface-elevated to-accent/5">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <AnimatedSection
          animation="fade-in-up"
          :delay="0"
        >
          <h2 class="text-2xl md:text-3xl font-bold text-text-primary mb-4">
            找不到合适的产品？
          </h2>
          <p class="text-lg text-text-secondary mb-8">
            我们提供定制化解决方案，满足您的特殊需求
          </p>
          <div class="flex flex-wrap justify-center gap-4">
            <NuxtLink
              to="/contact"
              class="btn-primary btn-primary-lg"
            >
              立即咨询
            </NuxtLink>
            <a
              :href="`tel:${contactPhone}`"
              class="btn-outline"
            >
              电话咨询：{{ contactPhone }}
            </a>
          </div>
        </AnimatedSection>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useProductStore } from '~/stores/product'
import { SITE_CONFIG } from '~/config/site'

const productStore = useProductStore()
const contactPhone = SITE_CONFIG.phone

const selectedCategory = ref<string>('all')
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = 9

const loading = computed(() => productStore.loading)

const categories = computed(() => [
  { id: 'all', name: '全部产品' },
  ...productStore.categories
])

const products = computed(() => {
  let filtered = productStore.products
  
  if (selectedCategory.value !== 'all') {
    filtered = filtered.filter(p => p.category_id === selectedCategory.value)
  }
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(p => 
      p.name.toLowerCase().includes(query) || 
      (p.description && p.description.toLowerCase().includes(query))
    )
  }
  
  return filtered
})

const totalPages = computed(() => Math.ceil(products.value.length / pageSize))
const paginatedProducts = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return products.value.slice(start, start + pageSize)
})

const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  const end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

watch([selectedCategory, searchQuery], () => {
  currentPage.value = 1
})

onMounted(async () => {
  await productStore.fetchCategories()
  await productStore.fetchProducts()
})

useHead({
  title: '产品中心 - 轻集料混凝土与保温材料 | 优丁建材',
  meta: [
    { name: 'description', content: '优丁建材产品中心，提供轻集料混凝土、陶粒混凝土、保温材料等系列产品，符合国家标准，品质保证。' },
    { name: 'keywords', content: '产品中心,轻集料混凝土,陶粒混凝土,保温材料,优丁建材' },
  ],
})
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
