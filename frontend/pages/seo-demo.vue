<template>
  <div class="min-h-screen bg-gray-50 py-12">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-white rounded-xl shadow-sm p-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-6">
          SEO 元数据管理演示
        </h1>

        <div class="space-y-8">
          <!-- Section 1: Basic SEO -->
          <section>
            <h2 class="text-xl font-semibold text-gray-800 mb-4">
              基础 SEO 配置
            </h2>
            <div class="bg-gray-50 rounded-lg p-6 space-y-4">
              <div>
                <h3 class="font-medium text-gray-700 mb-2">页面标题</h3>
                <p class="text-sm text-gray-600">
                  {{ seoConfig.title }}
                </p>
              </div>
              <div>
                <h3 class="font-medium text-gray-700 mb-2">页面描述</h3>
                <p class="text-sm text-gray-600">
                  {{ seoConfig.description }}
                </p>
              </div>
              <div>
                <h3 class="font-medium text-gray-700 mb-2">关键词</h3>
                <div class="flex flex-wrap gap-2">
                  <span
                    v-for="keyword in seoConfig.keywords"
                    :key="keyword"
                    class="px-3 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                  >
                    {{ keyword }}
                  </span>
                </div>
              </div>
            </div>
          </section>

          <!-- Section 2: Open Graph -->
          <section>
            <h2 class="text-xl font-semibold text-gray-800 mb-4">
              Open Graph 标签
            </h2>
            <div class="bg-gray-50 rounded-lg p-6 space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <h3 class="font-medium text-gray-700 mb-2">OG Type</h3>
                  <p class="text-sm text-gray-600">
                    {{ seoConfig.ogType }}
                  </p>
                </div>
                <div>
                  <h3 class="font-medium text-gray-700 mb-2">OG Image</h3>
                  <p class="text-sm text-gray-600">
                    {{ seoConfig.ogImage || '使用默认图片' }}
                  </p>
                </div>
              </div>
            </div>
          </section>

          <!-- Section 3: Twitter Card -->
          <section>
            <h2 class="text-xl font-semibold text-gray-800 mb-4">
              Twitter Card
            </h2>
            <div class="bg-gray-50 rounded-lg p-6 space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <h3 class="font-medium text-gray-700 mb-2">Card Type</h3>
                  <p class="text-sm text-gray-600">
                    {{ seoConfig.twitterCard }}
                  </p>
                </div>
                <div>
                  <h3 class="font-medium text-gray-700 mb-2">Twitter Image</h3>
                  <p class="text-sm text-gray-600">
                    {{ seoConfig.twitterImage || '使用默认图片' }}
                  </p>
                </div>
              </div>
            </div>
          </section>

          <!-- Section 4: Structured Data -->
          <section>
            <h2 class="text-xl font-semibold text-gray-800 mb-4">
              结构化数据 (JSON-LD)
            </h2>
            <div class="bg-gray-50 rounded-lg p-6">
              <pre class="text-xs text-gray-700 overflow-x-auto">{{ structuredDataPreview }}</pre>
            </div>
          </section>

          <!-- Actions -->
          <div class="flex gap-4 pt-4">
            <button
              class="px-6 py-3 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
              @click="viewPageSource"
            >
              查看页面源码
            </button>
            <button
              class="px-6 py-3 bg-green-500 text-white font-medium rounded-lg hover:bg-green-600 transition-colors"
              @click="testSEOTools"
            >
              测试 SEO 工具
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- SEO Head Component -->
    <SEOHead
      :title="seoConfig.title"
      :description="seoConfig.description"
      :keywords="seoConfig.keywords"
      :og-type="seoConfig.ogType"
      :og-image="seoConfig.ogImage"
      :twitter-card="seoConfig.twitterCard"
      :twitter-image="seoConfig.twitterImage"
      :canonical-url="seoConfig.canonicalUrl"
      :structured-data="seoConfig.structuredData"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SEOHead from '~/components/SEOHead.vue'
import { useSEOHead } from '~/composables/useSEOHead'

const { generateProductSchema, generateBreadcrumbSchema } = useSEOHead()

// SEO Configuration
const seoConfig = {
  title: '保温材料产品展示 - 优丁建材',
  description: '浏览优丁建材全系列保温产品，包括轻集料混凝土、陶粒混凝土等高性能建筑材料，提供详细技术参数和应用案例',
  keywords: ['保温材料', '轻集料混凝土', '陶粒混凝土', '建筑节能', '绿色建材'],
  ogType: 'website' as const,
  ogImage: '/images/products-og.jpg',
  twitterCard: 'summary_large_image' as const,
  twitterImage: '/images/products-twitter.jpg',
  canonicalUrl: 'https://www.youdingjiancai.com/seo-demo',
  structuredData: [
    generateBreadcrumbSchema([
      { name: '首页', url: '/' },
      { name: 'SEO演示', url: '/seo-demo' }
    ])
  ]
}

// Preview structured data
const structuredDataPreview = computed(() => {
  return JSON.stringify(seoConfig.structuredData, null, 2)
})

// Actions
const viewPageSource = () => {
  window.open('view-source:' + window.location.href, '_blank')
}

const testSEOTools = () => {
  // Open Google's Rich Results Test
  window.open('https://search.google.com/test/rich-results', '_blank')
}
</script>
