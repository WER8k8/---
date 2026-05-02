<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-purple-600 to-indigo-800 text-white py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <span class="inline-block px-3 py-1 bg-white/20 rounded-full text-sm mb-4">
          {{ caseStudy.category }}
        </span>
        <h1 class="text-4xl font-bold mb-4">
          {{ caseStudy.title }}
        </h1>
        <p class="text-xl text-purple-100">
          {{ caseStudy.location }} | {{ caseStudy.completionDate }}
        </p>
      </div>
    </section>

    <!-- Case Details -->
    <section class="py-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <!-- Main Content -->
          <div class="lg:col-span-2 space-y-8">
            <!-- Project Overview -->
            <div class="bg-white rounded-xl shadow-sm p-6">
              <h2 class="text-2xl font-bold text-gray-900 mb-4">
                项目概述
              </h2>
              <p class="text-gray-600 leading-relaxed">
                {{ caseStudy.description }}
              </p>
            </div>

            <!-- Challenges & Solutions -->
            <div class="bg-white rounded-xl shadow-sm p-6">
              <h2 class="text-2xl font-bold text-gray-900 mb-4">
                挑战与解决方案
              </h2>
              <div class="space-y-4">
                <div>
                  <h3 class="font-semibold text-gray-800 mb-2">
                    面临的挑战
                  </h3>
                  <p class="text-gray-600">
                    {{ caseStudy.challenges }}
                  </p>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-800 mb-2">
                    解决方案
                  </h3>
                  <p class="text-gray-600">
                    {{ caseStudy.solutions }}
                  </p>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-800 mb-2">
                    项目成果
                  </h3>
                  <p class="text-gray-600">
                    {{ caseStudy.results }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Before/After Images -->
            <div
              v-if="caseStudy.beforeImages?.length || caseStudy.afterImages?.length"
              class="bg-white rounded-xl shadow-sm p-6"
            >
              <h2 class="text-2xl font-bold text-gray-900 mb-4">
                施工前后对比
              </h2>
              <div class="grid grid-cols-2 gap-4">
                <div v-if="caseStudy.beforeImages?.length">
                  <p class="text-sm text-gray-500 mb-2">
                    施工前
                  </p>
                  <img
                    :src="caseStudy.beforeImages[0]"
                    alt="施工前"
                    class="w-full h-48 object-cover rounded-lg"
                  >
                </div>
                <div v-if="caseStudy.afterImages?.length">
                  <p class="text-sm text-gray-500 mb-2">
                    施工后
                  </p>
                  <img
                    :src="caseStudy.afterImages[0]"
                    alt="施工后"
                    class="w-full h-48 object-cover rounded-lg"
                  >
                </div>
              </div>
            </div>
          </div>

          <!-- Sidebar -->
          <div class="space-y-6">
            <!-- Project Stats -->
            <div class="bg-white rounded-xl shadow-sm p-6 sticky top-24">
              <h3 class="text-lg font-semibold text-gray-900 mb-4">
                项目数据
              </h3>
              <div class="space-y-4">
                <div>
                  <p class="text-sm text-gray-500 mb-1">
                    项目价值
                  </p>
                  <p class="text-2xl font-bold text-purple-600">
                    ¥{{ formatNumber(caseStudy.projectValue) }}
                  </p>
                </div>
                <div>
                  <p class="text-sm text-gray-500 mb-1">
                    工期
                  </p>
                  <p class="text-lg font-semibold text-gray-900">
                    {{ caseStudy.duration }}
                  </p>
                </div>
                <div>
                  <p class="text-sm text-gray-500 mb-1">
                    完工日期
                  </p>
                  <p class="text-lg font-semibold text-gray-900">
                    {{ caseStudy.completionDate }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SEO Head with Case Schema -->
    <SEOHead
      :title="pageTitle"
      :description="pageDescription"
      :keywords="pageKeywords"
      og-type="article"
      :og-image="caseStudy.images?.[0]"
      :canonical-url="canonicalUrl"
      :structured-data="structuredData"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import SEOHead from '~/components/SEOHead.vue'
import { useSEOHead } from '~/composables/useSEOHead'
import type { Case } from '~/types'

const { generateCaseSchema, generateBreadcrumbSchema } = useSEOHead()

// Sample case data (in real app, fetch from API)
const caseStudy: Case = {
  id: 'case-001',
  title: '上海某商业综合体保温工程',
  description: '为5万平方米的商业综合体提供外墙保温解决方案，采用模块化安装工艺，有效解决高层建筑保温施工难题。项目完成后节能效率提升45%，获得客户高度评价。',
  category: '商业建筑',
  images: ['https://via.placeholder.com/800x600?text=Project'],
  beforeImages: ['https://via.placeholder.com/400x300?text=Before'],
  afterImages: ['https://via.placeholder.com/400x300?text=After'],
  projectValue: 2800000,
  duration: '90天',
  location: '上海市浦东新区',
  completionDate: '2025-12-20',
  challenges: '高层建筑保温施工难度大，传统材料重量大影响结构安全，工期紧张需要快速施工方案。',
  solutions: '采用轻质高效保温材料配合模块化安装工艺，大幅降低施工难度和工期，同时保证保温效果。',
  results: '节能效率提升45%，施工周期缩短30%，获得客户高度评价并建立长期合作关系。',
  isActive: true
}

// SEO Configuration
const pageTitle = computed(() => `${caseStudy.title} - 保温工程案例 | 优丁建材`)
const pageDescription = computed(() => caseStudy.description || '')
const pageKeywords = computed(() => [
  caseStudy.title,
  caseStudy.category || '',
  '保温工程',
  '施工案例',
  '建筑节能'
].filter(Boolean))

const canonicalUrl = `https://www.youdingjiancai.com/cases/${caseStudy.id}`

// Structured Data
const structuredData = computed(() => [
  generateCaseSchema(caseStudy),
  generateBreadcrumbSchema([
    { name: '首页', url: '/' },
    { name: '工程案例', url: '/cases' },
    { name: caseStudy.title, url: `/cases/${caseStudy.id}` }
  ])
])

// Helper function
const formatNumber = (num?: number) => {
  if (!num) return '0'
  return num.toLocaleString('zh-CN')
}
</script>
