<template>
  <div>
    <section class="relative overflow-hidden">
      <div class="absolute inset-0 gradient-hero" />
      <div class="absolute top-0 right-0 w-1/2 h-full opacity-10">
        <div class="absolute top-20 right-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl" />
        <div class="absolute bottom-20 right-40 w-96 h-96 bg-accent/20 rounded-full blur-3xl" />
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
              class="btn-primary btn-primary-lg"
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
            <NuxtLink
              to="/contact"
              class="btn-outline"
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
          </div>
        </div>
      </div>
    </section>

    <section class="py-20 bg-surface-elevated">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="section-title">
          产品中心
        </h2>
        <p class="section-subtitle">
          提供全系列轻集料混凝土产品，满足不同工程需求
        </p>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-8">
          <div 
            v-for="(cat, index) in categories" 
            :key="cat.id" 
            class="card group cursor-pointer"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <div class="w-14 h-14 bg-gradient-to-br from-primary/10 to-accent/10 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
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
              class="inline-flex items-center text-primary font-medium hover:text-primary-dark transition-colors"
            >
              了解更多
              <svg
                class="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform"
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

    <section class="py-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="section-title">
          为什么选择优丁
        </h2>
        <p class="section-subtitle">
          多年的行业经验，为客户提供最优质的建材产品
        </p>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12">
          <div 
            v-for="(feature, index) in features" 
            :key="index" 
            class="text-center p-8 rounded-2xl bg-surface hover:shadow-elevated transition-all duration-300 group"
          >
            <div class="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-2xl flex items-center justify-center group-hover:scale-110 group-hover:shadow-soft transition-all duration-300">
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

    <section class="py-20 bg-gradient-to-br from-primary/5 via-surface-elevated to-accent/5">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="bg-surface rounded-2xl shadow-card p-8 md:p-12">
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
              class="text-center p-6 rounded-xl bg-surface-elevated hover:bg-primary/5 transition-colors duration-300"
            >
              <div class="text-4xl md:text-5xl font-bold text-primary mb-2">
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

    <section class="py-20 bg-surface-elevated">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="section-title">
          应用领域
        </h2>
        <p class="section-subtitle">
          广泛应用于各类建筑工程
        </p>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
          <div 
            v-for="(area, index) in applications" 
            :key="index" 
            class="p-6 rounded-xl bg-surface text-center hover:shadow-card-hover hover:-translate-y-1 transition-all duration-300 cursor-pointer"
          >
            <div class="text-3xl mb-3">
              {{ area.icon }}
            </div>
            <h4 class="font-semibold text-text-primary">
              {{ area.name }}
            </h4>
          </div>
        </div>
      </div>
    </section>

    <section class="py-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="bg-gradient-to-r from-primary to-primary-dark rounded-3xl p-8 md:p-12 text-center text-white relative overflow-hidden">
          <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
          <div class="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
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
                class="inline-flex items-center px-8 py-4 bg-white text-primary font-semibold rounded-xl hover:bg-gray-100 transition-all duration-200"
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
                电话咨询：400-888-8888
              </a>
              <NuxtLink
                to="/contact"
                class="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white/10 transition-all duration-200"
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
import { markRaw, h } from 'vue'

const FactoryIcon = markRaw({
  render() {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-full h-full' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' })
    ])
  }
})

const DropletsIcon = markRaw({
  render() {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-full h-full' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z' })
    ])
  }
})

const BrickIcon = markRaw({
  render() {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-full h-full' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4' })
    ])
  }
})

const ThermometerIcon = markRaw({
  render() {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-full h-full' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' })
    ])
  }
})

const ShieldIcon = markRaw({
  render() {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-full h-full' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' })
    ])
  }
})

const AwardIcon = markRaw({
  render() {
    return h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24', class: 'w-full h-full' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'stroke-width': '2', d: 'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z' })
    ])
  }
})

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
