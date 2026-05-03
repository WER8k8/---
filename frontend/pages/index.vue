<template>
  <div class="homepage">
    <section class="relative overflow-hidden hero-section">
      <div class="absolute inset-0 gradient-hero" />
      <div class="absolute top-0 right-0 w-1/2 h-full opacity-10">
        <div class="absolute top-20 right-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-float" />
        <div class="absolute bottom-20 right-40 w-96 h-96 bg-accent/20 rounded-full blur-3xl animate-float-delayed" />
      </div>
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16 md:pt-32 md:pb-24">
        <div class="max-w-3xl">
          <div class="inline-flex items-center px-4 py-2 bg-primary/10 rounded-full mb-6 animate-fade-in">
            <span class="w-2 h-2 bg-primary rounded-full mr-2 animate-pulse-soft" />
            <span class="text-sm font-medium text-primary">专业轻集料混凝土生产企业</span>
          </div>
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-text-primary mb-6 leading-tight animate-slide-up">
            高品质轻集料混凝土<br>
            <span class="text-primary">建筑材料解决方案</span>
          </h1>
          <p
            class="text-xl md:text-2xl text-text-secondary mb-10 leading-relaxed animate-slide-up"
            style="animation-delay: 0.1s"
          >
            优丁建材专注新型建筑材料研发与生产，为客户提供优质、环保、高性能的轻集料混凝土产品
          </p>
          <div
            class="flex flex-wrap gap-4 animate-slide-up"
            style="animation-delay: 0.2s"
          >
            <NuxtLink
              to="/products"
              class="btn-primary btn-primary-lg group"
            >
              <svg
                class="w-5 h-5 mr-2 group-hover:rotate-12 transition-transform"
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
            <NuxtLink
              to="/contact"
              class="btn-outline group"
            >
              <svg
                class="w-5 h-5 mr-2 group-hover:scale-110 transition-transform"
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
          </div>
        </div>
      </div>
      <div class="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
        <svg
          class="w-6 h-6 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19 14l-7 7m0 0l-7-7m7 7V3"
          />
        </svg>
      </div>
    </section>

    <section
      class="py-20 bg-surface-elevated"
      v-intersect="onIntersect"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2
          class="section-title"
          :class="{ 'animate-fade-in-up': isVisible }"
        >
          产品中心
        </h2>
        <p
          class="section-subtitle"
          :class="{ 'animate-fade-in-up': isVisible }"
          style="animation-delay: 0.1s"
        >
          提供全系列轻集料混凝土产品，满足不同工程需求
        </p>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-8">
          <div
            v-for="(cat, index) in categories"
            :key="cat.id"
            class="card group cursor-pointer"
            :class="{ 'animate-fade-in-up': isVisible }"
            :style="{ animationDelay: `${index * 0.1 + 0.2}s` }"
          >
            <div class="w-14 h-14 bg-gradient-to-br from-primary/10 to-accent/10 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
              <component
                :is="cat.icon"
                class="w-7 h-7 text-primary"
              />
            </div>
            <h3 class="text-xl font-semibold text-text-primary mb-3">
              {{ cat.name }}
            </h3>
            <p class="text-text-secondary mb-4">
              {{ cat.description }}
            </p>
            <NuxtLink
              :to="'/products?category=' + cat.id"
              class="inline-flex items-center text-primary font-medium hover:text-primary-dark transition-colors group/link"
            >
              了解更多
              <svg
                class="w-4 h-4 ml-1 group-hover/link:translate-x-2 transition-transform"
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
    </section>

    <section
      class="py-20"
      v-intersect="onIntersect"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2
          class="section-title"
          :class="{ 'animate-fade-in-up': isVisible }"
        >
          为什么选择优丁
        </h2>
        <p
          class="section-subtitle"
          :class="{ 'animate-fade-in-up': isVisible }"
          style="animation-delay: 0.1s"
        >
          多年的行业经验，为客户提供最优质的建材产品
        </p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
          <div
            v-for="(feature, index) in features"
            :key="index"
            class="text-center p-8 rounded-2xl bg-surface hover:shadow-elevated transition-all duration-500 group"
            :class="{ 'animate-fade-in-up': isVisible }"
            :style="{ animationDelay: `${index * 0.15 + 0.2}s` }"
          >
            <div class="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-2xl flex items-center justify-center group-hover:scale-110 group-hover:rotate-12 group-hover:shadow-soft transition-all duration-500">
              <component
                :is="feature.icon"
                class="w-10 h-10 text-primary"
              />
            </div>
            <h3 class="text-xl font-semibold text-text-primary mb-3">
              {{ feature.title }}
            </h3>
            <p class="text-text-secondary leading-relaxed">
              {{ feature.description }}
            </p>
          </div>
        </div>
      </div>
    </section>

    <section
      class="py-20 bg-gradient-to-br from-primary/5 via-surface-elevated to-accent/5"
      v-intersect="onIntersect"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div
          class="bg-surface rounded-2xl shadow-card p-8 md:p-12"
          :class="{ 'animate-fade-in-up': isVisible }"
        >
          <div class="text-center mb-10">
            <h3 class="text-2xl font-bold text-text-primary mb-2">
              企业实力
            </h3>
            <p class="text-text-secondary">
              持续创新，引领行业发展
            </p>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div
              v-for="(stat, index) in stats"
              :key="index"
              class="text-center p-6 rounded-xl bg-surface-elevated hover:bg-primary/5 transition-all duration-300 group"
              :class="{ 'animate-fade-in-up': isVisible }"
              :style="{ animationDelay: `${index * 0.1 + 0.2}s` }"
            >
              <div class="text-4xl md:text-5xl font-bold text-primary mb-2 group-hover:scale-110 transition-transform">
                {{ stat.value }}
              </div>
              <div class="text-text-secondary">
                {{ stat.label }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section
      class="py-20 bg-surface-elevated"
      v-intersect="onIntersect"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2
          class="section-title"
          :class="{ 'animate-fade-in-up': isVisible }"
        >
          应用领域
        </h2>
        <p
          class="section-subtitle"
          :class="{ 'animate-fade-in-up': isVisible }"
          style="animation-delay: 0.1s"
        >
          广泛应用于各类建筑工程
        </p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          <div
            v-for="(area, index) in applications"
            :key="index"
            class="p-6 rounded-xl bg-surface text-center hover:shadow-card-hover hover:-translate-y-2 transition-all duration-300 cursor-pointer group"
            :class="{ 'animate-fade-in-up': isVisible }"
            :style="{ animationDelay: `${index * 0.05 + 0.2}s` }"
          >
            <div class="text-4xl mb-3 group-hover:scale-125 transition-transform duration-300">
              {{ area.icon }}
            </div>
            <h4 class="font-semibold text-text-primary group-hover:text-primary transition-colors">
              {{ area.name }}
            </h4>
          </div>
        </div>
      </div>
    </section>

    <section
      class="py-20"
      v-intersect="onIntersect"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div
          class="bg-gradient-to-r from-primary to-primary-dark rounded-3xl p-8 md:p-12 text-center text-white relative overflow-hidden"
          :class="{ 'animate-fade-in-up': isVisible }"
        >
          <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 animate-float" />
          <div class="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2 animate-float-delayed" />
          <div class="relative">
            <h2 class="text-3xl md:text-4xl font-bold mb-4">
              立即咨询
            </h2>
            <p class="text-lg text-white/80 mb-8 max-w-2xl mx-auto">
              专业工程师为您提供产品选型和技术支持，助力您的工程项目顺利进行
            </p>
            <div class="flex flex-wrap justify-center gap-4">
              <a
                href="tel:400-888-8888"
                class="inline-flex items-center px-8 py-4 bg-white text-primary font-semibold rounded-xl hover:bg-gray-100 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group"
              >
                <svg
                  class="w-5 h-5 mr-2 group-hover:animate-pulse"
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
                电话咨询：400-888-8888
              </a>
              <NuxtLink
                to="/contact"
                class="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white/10 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group"
              >
                <svg
                  class="w-5 h-5 mr-2 group-hover:scale-110 transition-transform"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
                在线留言
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FactoryIcon from '~/components/icons/FactoryIcon.vue'
import DropletsIcon from '~/components/icons/DropletsIcon.vue'
import BrickIcon from '~/components/icons/BrickIcon.vue'
import ThermometerIcon from '~/components/icons/ThermometerIcon.vue'
import ShieldIcon from '~/components/icons/ShieldIcon.vue'
import AwardIcon from '~/components/icons/AwardIcon.vue'

useHead({
  title: '优丁建材 - 专业轻集料混凝土生产企业 | 高品质建筑材料解决方案',
  meta: [
    { name: 'description', content: '优丁建材专注新型建筑材料研发与生产20年，提供轻集料混凝土、陶粒混凝土、加气混凝土、保温砂浆等高品质产品，ISO9001认证，年产能力超百万吨' },
    { name: 'keywords', content: '轻集料混凝土,陶粒混凝土,加气混凝土,保温砂浆,建筑材料,新型建材,环保建材,高性能混凝土' },
    { property: 'og:title', content: '优丁建材 - 专业轻集料混凝土生产企业' },
    { property: 'og:description', content: '优丁建材专注新型建筑材料研发与生产，为客户提供优质、环保、高性能的轻集料混凝土产品' },
    { property: 'og:type', content: 'website' },
    { property: 'og:url', content: 'https://www.youdingjiancai.com' },
    { property: 'og:image', content: 'https://www.youdingjiancai.com/images/og-home.jpg' },
    { name: 'twitter:card', content: 'summary_large_image' },
    { name: 'twitter:title', content: '优丁建材 - 专业轻集料混凝土生产企业' },
    { name: 'twitter:description', content: '优丁建材专注新型建筑材料研发与生产，为客户提供优质、环保、高性能的轻集料混凝土产品' }
  ],
  link: [
    { rel: 'canonical', href: 'https://www.youdingjiancai.com' }
  ],
  script: [
    {
      type: 'application/ld+json',
      children: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'Organization',
        name: '优丁建材有限公司',
        url: 'https://www.youdingjiancai.com',
        logo: 'https://www.youdingjiancai.com/images/logo.png',
        description: '专注新型建筑材料研发与生产20年，提供轻集料混凝土、陶粒混凝土、加气混凝土、保温砂浆等高品质产品',
        foundingDate: '2006',
        numberOfEmployees: {
          '@type': 'QuantitativeValue',
          minValue: 200,
          maxValue: 500
        },
        contactPoint: {
          '@type': 'ContactPoint',
          telephone: '+86-400-888-8888',
          contactType: 'customer service',
          availableLanguage: ['Chinese', 'English']
        },
        sameAs: [
          'https://www.youdingjiancai.com'
        ],
        address: {
          '@type': 'PostalAddress',
          addressCountry: 'CN',
          addressRegion: '中国'
        }
      })
    }
  ]
})

const isVisible = ref(false)

const onIntersect = (isIntersecting: boolean) => {
  if (isIntersecting) {
    isVisible.value = true
  }
}

const categories = [
  { id: '1', name: '轻集料混凝土', description: '各类轻集料混凝土产品，满足不同强度等级需求', icon: FactoryIcon },
  { id: '2', name: '陶粒混凝土', description: '轻质高强陶粒混凝土系列', icon: DropletsIcon },
  { id: '3', name: '加气混凝土', description: '加气混凝土制品，保温隔热性能优异', icon: BrickIcon },
  { id: '4', name: '保温砂浆', description: '建筑保温砂浆系列，节能环保', icon: ThermometerIcon },
]

const features = [
  { 
    title: '先进生产线', 
    description: '引进国际先进生产设备，年产能力超百万吨，确保产品质量稳定可靠',
    icon: FactoryIcon 
  },
  { 
    title: '品质保证', 
    description: '严格质量管控体系，产品符合GB/T 17431-2010标准，通过ISO9001认证',
    icon: ShieldIcon 
  },
  { 
    title: '技术研发', 
    description: '持续技术创新，拥有多项发明专利，为客户提供定制化解决方案',
    icon: AwardIcon 
  },
]

const stats = [
  { value: '20+', label: '年行业经验' },
  { value: '500+', label: '合作客户' },
  { value: '100+', label: '产品型号' },
  { value: '30+', label: '专利技术' },
]

const applications = [
  { name: '住宅建筑', icon: '🏠' },
  { name: '商业大厦', icon: '🏢' },
  { name: '桥梁工程', icon: '🌉' },
  { name: '市政道路', icon: '🛣️' },
  { name: '工业厂房', icon: '🏭' },
  { name: '园林绿化', icon: '🌳' },
  { name: '水利工程', icon: '💧' },
  { name: '地下空间', icon: '🏗️' },
]
</script>

<style scoped>
.gradient-hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

@keyframes float-delayed {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-15px); }
}

.animate-float {
  animation: float 6s ease-in-out infinite;
}

.animate-float-delayed {
  animation: float-delayed 8s ease-in-out infinite;
  animation-delay: 1s;
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fade-in-up 0.6s ease-out forwards;
}

.hero-section {
  min-height: 90vh;
  display: flex;
  align-items: center;
}
</style>
