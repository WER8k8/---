<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-blue-600 to-blue-800 text-white py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 class="text-4xl font-bold mb-4">
          {{ product.name }}
        </h1>
        <p class="text-xl text-blue-100">
          {{ product.subtitle }}
        </p>
      </div>
    </section>

    <!-- Product Details -->
    <section class="py-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Product Image -->
          <div class="bg-white rounded-xl shadow-sm overflow-hidden">
            <img
              :src="product.images?.[0] || '/images/product-placeholder.jpg'"
              :alt="product.name"
              class="w-full h-96 object-cover"
            >
          </div>

          <!-- Product Info -->
          <div class="space-y-6">
            <div class="bg-white rounded-xl shadow-sm p-6">
              <h2 class="text-2xl font-bold text-gray-900 mb-4">
                产品详情
              </h2>
              <p class="text-gray-600 mb-6">
                {{ product.description }}
              </p>

              <div class="grid grid-cols-2 gap-4">
                <div class="bg-gray-50 rounded-lg p-4">
                  <p class="text-sm text-gray-500 mb-1">
                    价格
                  </p>
                  <p class="text-2xl font-bold text-blue-600">
                    ¥{{ product.price }}
                  </p>
                </div>
                <div class="bg-gray-50 rounded-lg p-4">
                  <p class="text-sm text-gray-500 mb-1">
                    库存
                  </p>
                  <p class="text-2xl font-bold text-green-600">
                    {{ product.stock }} 件
                  </p>
                </div>
              </div>
            </div>

            <!-- Rating -->
            <div
              v-if="product.rating"
              class="bg-white rounded-xl shadow-sm p-6"
            >
              <div class="flex items-center gap-4">
                <div class="flex items-center">
                  <svg
                    v-for="i in 5"
                    :key="i"
                    class="w-6 h-6"
                    :class="i <= Math.round(product.rating) ? 'text-yellow-400' : 'text-gray-300'"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </div>
                <span class="text-lg font-semibold text-gray-900">{{ product.rating }}</span>
                <span class="text-gray-500">({{ product.reviewCount }} 条评价)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SEO Head with Product Schema -->
    <SEOHead
      :title="pageTitle"
      :description="pageDescription"
      :keywords="pageKeywords"
      og-type="product"
      :og-image="product.images?.[0]"
      :canonical-url="canonicalUrl"
      :structured-data="structuredData"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SEOHead from '~/components/SEOHead.vue'
import { useSEOHead } from '~/composables/useSEOHead'
import type { Product } from '~/types'

const { generateProductSchema, generateBreadcrumbSchema } = useSEOHead()

// Sample product data (in real app, fetch from API)
const product: Product = {
  id: 'prod-001',
  name: '高效保温板 Pro',
  subtitle: '纳米技术超低导热保温材料',
  description: '采用最新纳米技术，导热系数低至0.023W/(m·K)，防火A级，防潮防水，适用于建筑外墙保温、冷库建设等场景。通过ISO 9001和CE认证，品质保证。',
  price: 188,
  images: ['https://via.placeholder.com/600x400?text=Insulation+Board'],
  category: '板材类',
  rating: 4.8,
  reviewCount: 156,
  stock: 5000,
  tags: ['热销', '节能', '环保'],
  specifications: {
    density: '800-1950kg/m³',
    strength: 'A3.5',
    thermal_conductivity: '0.023W/(m·K)'
  },
  isActive: true
}

// SEO Configuration
const pageTitle = computed(() => `${product.name} - 技术参数与报价 | 优丁建材`)
const pageDescription = computed(() => product.description || '')
const pageKeywords = computed(() => [
  product.name,
  product.category || '',
  '保温材料',
  '建筑节能',
  ...(product.tags || [])
].filter(Boolean))

const canonicalUrl = `https://www.youdingjiancai.com/products/${product.id}`

// Structured Data
const structuredData = computed(() => [
  generateProductSchema(product),
  generateBreadcrumbSchema([
    { name: '首页', url: '/' },
    { name: '产品中心', url: '/products' },
    { name: product.name, url: `/products/${product.id}` }
  ])
])
</script>
