<template>
  <div>
    <section class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-700">
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-secondary-400 rounded-full blur-3xl" />
        <div class="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent-400 rounded-full blur-3xl" />
      </div>
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-24">
        <div class="text-center">
          <div class="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full mb-6">
            <span class="w-2 h-2 bg-secondary-400 rounded-full mr-2" />
            <span class="text-sm font-medium text-white">产品中心</span>
          </div>
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight">
            产品中心
          </h1>
          <p class="text-xl text-white/80">
            全系列轻集料混凝土产品，满足不同工程需求
          </p>
        </div>
      </div>
    </section>

    <section class="py-20 bg-gradient-to-b from-surface-elevated to-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div
          v-if="loading"
          class="text-center py-12"
        >
          <div class="flex items-center justify-center">
            <div class="w-8 h-8 border-2 border-secondary-500 border-t-transparent rounded-full animate-spin" />
            <span class="ml-3 text-text-muted">加载中...</span>
          </div>
        </div>

        <template v-else>
          <div class="flex flex-wrap gap-3 mb-12 justify-center">
            <button
              :class="!activeCategory ? 'bg-gradient-to-r from-secondary-500 to-secondary-600 text-white shadow-lg shadow-secondary-200' : 'bg-white text-text-secondary hover:bg-surface-hover border border-border'"
              class="px-6 py-2.5 rounded-full text-sm font-medium transition-all shadow-card"
              @click="activeCategory = null"
            >
              全部分类
            </button>
            <button
              v-for="cat in categories"
              :key="cat.id"
              :class="activeCategory === cat.id ? 'bg-gradient-to-r from-secondary-500 to-secondary-600 text-white shadow-lg shadow-secondary-200' : 'bg-white text-text-secondary hover:bg-surface-hover border border-border'"
              class="px-6 py-2.5 rounded-full text-sm font-medium transition-all shadow-card"
              @click="activeCategory = cat.id"
            >
              {{ cat.name }}
            </button>
          </div>

          <div
            v-if="filteredProducts.length === 0"
            class="text-center py-16"
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
              暂无相关产品
            </p>
            <NuxtLink
              to="/contact"
              class="mt-4 inline-flex items-center text-secondary-600 font-medium hover:text-secondary-700"
            >
              联系我们了解更多
              <svg
                class="w-4 h-4 ml-1"
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

          <div
            v-else
            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
          >
            <div
              v-for="product in filteredProducts"
              :key="product.id"
              class="group bg-white rounded-2xl overflow-hidden border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all duration-300 hover:-translate-y-1"
            >
              <div class="h-48 bg-gradient-to-br from-secondary-50 via-white to-accent-50 flex items-center justify-center relative overflow-hidden">
                <span class="text-5xl text-secondary-400 font-bold">{{ (product.name || '产').charAt(0) }}</span>
                <div class="absolute inset-0 bg-gradient-to-t from-white/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <div class="p-6">
                <span class="text-xs font-semibold bg-secondary-100 text-secondary-600 px-3 py-1 rounded-full">
                  {{ categoryMap[product.category_id]?.name || '未分类' }}
                </span>
                <h3 class="text-xl font-semibold text-primary-900 mt-3 mb-2 group-hover:text-secondary-600 transition-colors">
                  <NuxtLink :to="'/products/' + product.slug">
                    {{ product.name }}
                  </NuxtLink>
                </h3>
                <p
                  v-if="product.subtitle"
                  class="text-text-muted text-sm mb-3"
                >
                  {{ product.subtitle }}
                </p>
                <p class="text-text-secondary text-sm mb-4 line-clamp-3">
                  {{ product.description }}
                </p>
                <div
                  v-if="product.density || product.strength"
                  class="flex flex-wrap gap-2 mb-4"
                >
                  <span
                    v-if="product.density"
                    class="text-xs bg-surface-elevated text-text-secondary px-2.5 py-1 rounded-lg"
                  >
                    密度: {{ product.density }}
                  </span>
                  <span
                    v-if="product.strength"
                    class="text-xs bg-surface-elevated text-text-secondary px-2.5 py-1 rounded-lg"
                  >
                    强度: {{ product.strength }}
                  </span>
                </div>
                <NuxtLink
                  :to="'/products/' + product.slug"
                  class="inline-flex items-center text-secondary-600 font-medium text-sm group-hover:translate-x-1 transition-all"
                >
                  了解详情
                  <svg
                    class="w-4 h-4 ml-1"
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
          </div>
        </template>
      </div>
    </section>

    <section class="py-16 bg-gradient-to-r from-secondary-600 via-secondary-500 to-accent-500">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">
          找不到合适的产品？
        </h2>
        <p class="text-white/80 mb-8 max-w-2xl mx-auto">
          我们的技术团队可以根据您的具体需求提供定制化产品方案
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <NuxtLink
            to="/contact"
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
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            立即咨询
          </NuxtLink>
          <a
            href="tel:400-888-8888"
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
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
              />
            </svg>
            拨打热线 400-888-8888
          </a>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProductStore } from '~/stores/product'

useHead({
  title: '产品中心 - 优丁轻集料混凝土',
  meta: [
    { name: 'description', content: '优丁建材专业生产轻集料混凝土、陶粒混凝土、加气混凝土、保温砂浆等全系列产品，提供详细技术参数和选型指导' },
    { name: 'keywords', content: '轻集料混凝土,陶粒混凝土,加气混凝土,保温砂浆,优丁建材,轻集料混凝土价格,轻集料混凝土技术参数' },
  ],
})

const store = useProductStore()
const activeCategory = ref<string | null>(null)

const loading = computed(() => store.loading)
const categories = computed(() => store.categories)
const categoryMap = computed(() => store.categoryMap)

const filteredProducts = computed(() => {
  if (!activeCategory.value) return store.products
  return store.products.filter(p => p.category_id === activeCategory.value)
})

onMounted(async () => {
  await Promise.all([
    store.fetchCategories(),
    store.fetchProducts(),
  ])
})
</script>
