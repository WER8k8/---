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
            <span class="text-sm font-medium text-white">关于我们</span>
          </div>
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight">
            关于优丁
          </h1>
          <p class="text-xl text-white/80 max-w-3xl mx-auto">
            专注轻集料混凝土研发与生产，以技术创新驱动绿色建材发展
          </p>
        </div>
      </div>
    </section>

    <section class="py-20 bg-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <div class="inline-flex items-center px-3 py-1.5 bg-secondary-50 rounded-full mb-4">
              <span class="w-1.5 h-1.5 bg-secondary-500 rounded-full mr-2" />
              <span class="text-sm font-medium text-secondary-600">企业简介</span>
            </div>
            <h2 class="text-3xl md:text-4xl font-bold text-primary-900 mb-6">
              专注建材领域<br><span class="text-secondary-600">二十余年</span>
            </h2>
            <div class="space-y-4 text-text-secondary leading-relaxed">
              <p>优丁建材有限公司成立于2000年，是一家专业从事轻集料混凝土研发、生产和销售的高新技术企业。公司位于中国建材产业园区，占地面积超过10万平方米，拥有现代化的生产基地和研发中心。</p>
              <p>公司引进国际先进的生产设备和检测仪器，建立了完善的质量管理体系，产品全面符合GB/T 17431-2010《轻集料混凝土》标准。年生产能力超过100万吨，产品广泛应用于各类建筑工程、桥梁隧道、保温节能等领域。</p>
              <p>公司始终坚持以技术创新为核心驱动力，与多所知名高校和科研院所建立了长期合作关系，拥有30多项发明专利和实用新型专利。</p>
            </div>
          </div>
          <div class="bg-gradient-to-br from-secondary-50 to-accent-50 rounded-2xl p-8 border border-secondary-100">
            <div class="grid grid-cols-2 gap-8 text-center">
              <div
                v-for="stat in stats"
                :key="stat.label"
                class="group"
              >
                <div class="w-16 h-16 mx-auto mb-3 bg-gradient-to-br from-secondary-500 to-secondary-600 rounded-xl flex items-center justify-center shadow-lg shadow-secondary-200 group-hover:scale-110 transition-transform duration-300">
                  <span class="text-2xl font-bold text-white">{{ stat.value.charAt(0) }}</span>
                </div>
                <div class="text-3xl font-bold text-primary-900">
                  {{ stat.value }}
                </div>
                <div class="text-sm text-text-muted mt-1">
                  {{ stat.label }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-20 bg-gradient-to-b from-surface-elevated to-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="section-title">
          发展历程
        </h2>
        <p class="section-subtitle">
          从创立到领先，见证优丁的成长之路
        </p>
        <div class="max-w-4xl mx-auto relative">
          <div class="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-secondary-400 via-accent-400 to-warm-400 hidden md:block" />
          <div
            v-for="(milestone, idx) in milestones"
            :key="idx"
            class="relative flex items-start space-x-4 md:space-x-8 mb-8 last:mb-0"
          >
            <div class="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-secondary-500 to-accent-500 text-white rounded-full flex items-center justify-center font-bold shadow-lg shadow-secondary-200">
              {{ idx + 1 }}
            </div>
            <div class="flex-1 bg-white rounded-2xl p-6 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all duration-300">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-semibold text-secondary-600 bg-secondary-50 px-3 py-1 rounded-full">{{ milestone.year }}</span>
              </div>
              <p class="text-text-secondary">
                {{ milestone.text }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-20 bg-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="section-title">
          资质荣誉
        </h2>
        <p class="section-subtitle">
          公司先后获得多项行业资质和荣誉认证
        </p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div
            v-for="cert in certifications"
            :key="cert"
            class="group bg-white rounded-2xl p-6 text-center border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all duration-300 hover:-translate-y-1"
          >
            <div class="w-14 h-14 bg-gradient-to-br from-secondary-50 to-accent-50 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-300">
              <svg
                class="w-7 h-7 text-secondary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <p class="text-sm font-medium text-primary-900 leading-tight">
              {{ cert }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 bg-gradient-to-r from-secondary-600 via-secondary-500 to-accent-500">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">
          准备好开始您的项目了吗？
        </h2>
        <p class="text-white/80 mb-8 max-w-2xl mx-auto">
          我们的专业团队随时准备为您提供定制化的建材解决方案
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
            联系我们
          </NuxtLink>
          <NuxtLink
            to="/products"
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
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
              />
            </svg>
            查看产品
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useHead } from '@vueuse/head'

useHead({
  title: '关于优丁 - 专业轻集料混凝土生产企业',
  meta: [
    { name: 'description', content: '了解优丁建材的发展历程、企业资质和生产实力，20年专注轻集料混凝土研发与生产' },
    { name: 'keywords', content: '优丁建材,轻集料混凝土企业,混凝土生产企业,建材公司' },
  ],
})

const stats = [
  { label: '年行业经验', value: '20+' },
  { label: '合作客户', value: '500+' },
  { label: '产品型号', value: '100+' },
  { label: '专利技术', value: '30+' },
]

const milestones = [
  { year: '2000年', text: '公司成立，引进第一条轻集料混凝土生产线' },
  { year: '2005年', text: '通过ISO9001质量管理体系认证' },
  { year: '2010年', text: '获评高新技术企业，建立企业技术中心' },
  { year: '2015年', text: '年产能突破50万吨，产品覆盖全国市场' },
  { year: '2020年', text: '年产能突破100万吨，获得30项国家专利' },
  { year: '2024年', text: '建成AI智能运营系统，实现数字化转型' },
]

const certifications = [
  'ISO9001 质量管理体系',
  '高新技术企业认证',
  'GB/T 17431-2010 标准',
  '绿色建材产品认证',
  '安全生产标准化企业',
  '重合同守信用企业',
  '省级企业技术中心',
  'AAA级信用企业',
]
</script>
