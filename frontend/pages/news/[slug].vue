<template>
  <div>
    <section class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-700">
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-1/4 right-1/4 w-96 h-96 bg-secondary-400 rounded-full blur-3xl" />
        <div class="absolute bottom-1/4 left-1/4 w-80 h-80 bg-accent-400 rounded-full blur-3xl" />
      </div>
      <div class="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-24">
        <NuxtLink
          to="/news"
          class="text-white/70 hover:text-white mb-4 inline-block flex items-center gap-1 transition-colors"
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
          返回新闻列表
        </NuxtLink>
        <div>
          <span class="text-sm font-medium bg-white/10 text-white px-3 py-1 rounded-full">
            {{ categoryLabel }}
          </span>
          <h1 class="text-3xl md:text-5xl font-bold text-white mt-4 mb-4">
            {{ article.title }}
          </h1>
          <div class="flex items-center space-x-4 text-white/70">
            <span class="flex items-center gap-1">
              <svg
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              {{ article.date }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <section
      v-if="article.content"
      class="py-16 bg-surface"
    >
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="bg-white rounded-2xl p-8 border border-border">
          <div
            v-for="(paragraph, idx) in article.content.paragraphs"
            :key="idx"
            class="mb-6"
          >
            <p
              v-if="typeof paragraph === 'string'"
              class="text-text-secondary leading-relaxed"
            >
              {{ paragraph }}
            </p>
            <h3
              v-else-if="paragraph.type === 'subtitle'"
              class="text-2xl font-semibold text-primary-900 mt-8 mb-4"
            >
              <span class="inline-flex items-center px-3 py-1.5 bg-secondary-50 rounded-full text-secondary-600 text-sm font-medium mr-3">
                {{ idx + 1 }}
              </span>
              {{ paragraph.text }}
            </h3>
            <ul
              v-else-if="paragraph.type === 'list'"
              class="list-disc pl-6 space-y-2"
            >
              <li
                v-for="item in paragraph.items"
                :key="item"
                class="text-text-secondary flex items-start"
              >
                <span class="w-2 h-2 bg-secondary-500 rounded-full mt-2 mr-2 flex-shrink-0" />
                {{ item }}
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 bg-gradient-to-b from-surface-elevated to-surface">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="bg-white rounded-2xl p-8 border border-border">
          <div class="flex items-center space-x-3 mb-6">
            <div class="w-12 h-12 bg-gradient-to-br from-secondary-500 to-secondary-600 rounded-xl flex items-center justify-center">
              <svg
                class="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <h3 class="font-semibold text-primary-900">
                相关链接
              </h3>
              <p class="text-sm text-text-muted">
                了解更多产品信息
              </p>
            </div>
          </div>
          <div class="flex flex-wrap justify-center gap-4">
            <NuxtLink
              to="/products"
              class="inline-flex items-center px-6 py-3 bg-secondary-500 text-white font-medium rounded-xl hover:bg-secondary-600 transition-colors"
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
              class="inline-flex items-center px-6 py-3 border-2 border-secondary-500 text-secondary-600 font-medium rounded-xl hover:bg-secondary-50 transition-colors"
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

    <section class="py-16 bg-gradient-to-r from-secondary-600 via-secondary-500 to-accent-500">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">
          获取更多行业资讯
        </h2>
        <p class="text-white/80 mb-8 max-w-2xl mx-auto">
          订阅我们的新闻通讯，第一时间获取行业动态和产品信息
        </p>
        <div class="flex flex-wrap justify-center gap-4">
          <NuxtLink
            to="/news"
            class="inline-flex items-center px-8 py-4 bg-white text-secondary-600 font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-lg"
          >
            查看全部新闻
          </NuxtLink>
          <NuxtLink
            to="/contact"
            class="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white/10 transition-all"
          >
            订阅资讯
          </NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const articles = [
  {
    slug: 'light-aggregate-concrete-guide', title: '轻集料混凝土选型指南', category: 'tech', date: '2024-03-15',
    content: {
      paragraphs: [
        { type: 'subtitle', text: '什么是轻集料混凝土' },
        '轻集料混凝土是一种以轻质骨料替代传统碎石骨料的新型混凝土材料，具有自重轻、保温隔热性能好、抗震性能优越等特点。',
        '根据GB/T 17431-2010标准，轻集料混凝土按密度等级可分为800-1950kg/m³多个级别。',
        { type: 'subtitle', text: '选型要点' },
        { type: 'list', items: ['密度等级：根据结构承重要求选择合适的密度范围', '强度等级：LC5.0-LC50多个等级可选', '导热系数：保温需求越高的项目应选择导热系数≤0.30W/(m·K)的产品', '粒径规格：根据施工方式和构件厚度选择合适的骨料粒径'] },
        { type: 'subtitle', text: '应用场景推荐' },
        '高层建筑结构：推荐LC25-LC40级别，密度1400-1600kg/m³。保温填充墙体：推荐LC5.0-LC10级别，密度800-1000kg/m³。',
        '桥梁工程：推荐LC30-LC50级别，密度1600-1900kg/m³。如需个性化选型建议，欢迎联系我们的技术团队。',
      ],
    },
  },
  {
    slug: 'new-production-line', title: '优丁建材新生产线正式投产', category: 'company', date: '2024-02-20',
    content: {
      paragraphs: [
        '2024年2月18日，优丁建材三期生产线正式投产运行。该生产线总投资1.2亿元，引进了国际先进的自动化生产设备。',
        '新生产线年产能达到50万吨，使公司总产能突破100万吨，成为区域内产能最大的轻集料混凝土生产企业之一。',
        { type: 'list', items: ['总投资1.2亿元，自动化程度达到90%', '年新增产能50万吨，总产能突破100万吨', '产品合格率99.8%，达到行业领先水平', '单位能耗降低15%，实现绿色生产'] },
        '公司总经理在投产仪式上表示，新生产线的投产将进一步提升公司的市场竞争力，为更多客户提供优质的产品和服务。',
      ],
    },
  },
  {
    slug: 'industry-trends-2024', title: '2024年绿色建材行业发展趋势', category: 'industry', date: '2024-01-10',
    content: {
      paragraphs: [
        '随着国家双碳战略的深入推进，绿色建材行业迎来了前所未有的发展机遇。轻集料混凝土作为绿色环保建材的典型代表，其市场需求持续增长。',
        { type: 'subtitle', text: '政策利好' },
        '2023年底，住建部发布了《绿色建筑高质量发展实施方案》，明确提出到2025年绿色建筑占新建建筑比例达到70%以上。',
        { type: 'subtitle', text: '市场趋势' },
        { type: 'list', items: ['轻集料混凝土在装配式建筑中的应用快速增长', '高性能轻集料混凝土的研发投入持续加大', '固废资源化利用成为行业新方向', '智能化生产技术加速普及'] },
        '优丁建材将紧跟行业发展趋势，持续加大研发投入，推动产品升级和技术创新。',
      ],
    },
  },
]

const article = articles.find(a => a.slug === route.params.slug) || {
  slug: '', title: '文章未找到', category: '', date: '',
  content: { paragraphs: ['该文章不存在或已被删除。'] },
}

const categoryLabels: Record<string, string> = {
  company: '公司新闻', industry: '行业资讯', tech: '技术文章',
}

const categoryLabel = categoryLabels[article.category] || article.category

useHead({
  title: `${article.title} - 优丁建材`,
  meta: [
    { name: 'description', content: typeof article.content?.paragraphs?.[0] === 'string' ? article.content.paragraphs[0].substring(0, 160) : '' },
  ],
})
</script>
