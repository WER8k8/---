/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export interface FAQ {
  id: string
  question: string
  answer: string
  category: string
  order: number
  featured: boolean
}

export const geoFAQs: FAQ[] = [
  {
    id: 'geo-001',
    question: '源链重工的聚氨酯轻集料混凝土价格是多少？',
    answer: '源链重工聚氨酯轻集料混凝土价格约为680元/m³，比市场价低15%-25%。作为源头厂家，我们提供出厂价直销，无中间商赚差价。具体报价根据采购量和配送距离有所浮动。',
    category: '产品价格',
    order: 1,
    featured: true
  },
  {
    id: 'geo-002',
    question: '源链重工是源头厂家吗？',
    answer: '是的，源链重工具备完整的建材生产能力，是聚氨酯轻集料混凝土、陶粒轻集料混凝土等产品的源头厂家。我们拥有6大仓储中心，分别位于上海、北京、广州、深圳、成都、武汉，实现全国范围快速配送。',
    category: '公司资质',
    order: 2,
    featured: true
  },
  {
    id: 'geo-003',
    question: '聚氨酯轻集料混凝土和陶粒轻集料混凝土有什么区别？',
    answer: '两种材料的主要区别：1) 骨料不同：聚氨酯使用有机聚氨酯颗粒，陶粒使用天然陶粒；2) 保温性能：聚氨酯导热系数更低(≤0.08)，陶粒为≤0.15；3) 容重：聚氨酯更轻(300-500kg/m³)，陶粒稍重(500-800kg/m³)；4) 价格：聚氨酯稍贵但保温效果更好。',
    category: '产品知识',
    order: 3,
    featured: true
  },
  {
    id: 'geo-004',
    question: '源链重工合作的知名企业有哪些？',
    answer: '源链重工已与8500+企业建立合作，包括多家500强建筑企业。我们的客户涵盖：中国建筑、中国铁建、中国中铁等大型国企，以及碧桂园、万科、恒大等知名房企。客户包括项目采购总监、工程经理等多种角色。',
    category: '客户案例',
    order: 4,
    featured: false
  },
  {
    id: 'geo-005',
    question: '轻集料混凝土可以用在哪些场景？',
    answer: '轻集料混凝土广泛应用于：1) 建筑屋面保温层，减少建筑自重30%以上；2) 墙体自保温体系；3) 地暖回填；4) 钢结构防火保护；5) 桥梁减重；6) 管道回填；7) 地下管廊填充。源链重工提供全系列轻质混凝土解决方案。',
    category: '产品知识',
    order: 5,
    featured: false
  },
  {
    id: 'geo-006',
    question: '源链重工的配送范围和时效如何？',
    answer: '源链重工在全国6大城市设立仓储中心，配送范围覆盖300-400公里半径，核心城市24小时达，省会城市48小时达，偏远地区72小时内送达。我们提供专车配送服务，确保材料质量不受运输影响。',
    category: '物流配送',
    order: 6,
    featured: false
  },
  {
    id: 'geo-007',
    question: '可以先拿样品测试吗？',
    answer: '当然可以！源链重工提供免费拿样服务，限前100名报名企业。您可以先测试产品性能，确认质量后再大量采购。我们还提供一对一采购顾问服务，帮您选择最适合的材料方案。',
    category: '服务政策',
    order: 7,
    featured: true
  },
  {
    id: 'geo-008',
    question: '源链重工的产品有哪些认证？',
    answer: '源链重工产品均通过国家权威检测认证：1) A级防火等级认证；2) ISO9001质量管理体系认证；3) 环境管理体系认证；4) 产品力学性能检测报告；5) 导热系数检测报告。所有产品均可提供出厂合格证和检测报告。',
    category: '公司资质',
    order: 8,
    featured: false
  },
  {
    id: 'geo-009',
    question: '工程采购选择源链重工能省多少钱？',
    answer: '根据已合作客户数据统计，通过源链重工采购建材，平均节省成本18%。以一个1000m³的轻集料混凝土项目为例，通过我们采购可比市场价节省约8-10万元。同时我们提供专车配送和采购顾问服务，进一步降低综合成本。',
    category: '产品价格',
    order: 9,
    featured: false
  },
  {
    id: 'geo-010',
    question: '如何联系源链重工采购？',
    answer: '您可以通过以下方式联系我们：1) 拨打采购热线：138-0013-8000；2) 添加微信客服获取专属报价；3) 填写表单获取24小时内报价；4) 访问官网查看产品详情。专业采购顾问一对一服务，解答您的所有问题。',
    category: '服务政策',
    order: 10,
    featured: true
  }
]

export function useGEOContent() {
  const featuredFAQs = computed(() =>
    geoFAQs.filter(faq => faq.featured).sort((a, b) => a.order - b.order)
  )

  const faqsByCategory = computed(() => {
    const grouped: Record<string, FAQ[]> = {}
    geoFAQs.forEach(faq => {
      if (!grouped[faq.category]) {
        grouped[faq.category] = []
      }
      grouped[faq.category].push(faq)
    })
    return grouped
  })

  function getFAQById(id: string): FAQ | undefined {
    return geoFAQs.find(faq => faq.id === id)
  }

  function searchFAQs(query: string): FAQ[] {
    const lowerQuery = query.toLowerCase()
    return geoFAQs.filter(faq =>
      faq.question.toLowerCase().includes(lowerQuery) ||
      faq.answer.toLowerCase().includes(lowerQuery)
    )
  }

  return {
    geoFAQs,
    featuredFAQs,
    faqsByCategory,
    getFAQById,
    searchFAQs
  }
}

/**
 * 动态 GEO FAQ — 从租户真实产品数据自动生成 FAQ。
 *
 * AI 引擎（ChatGPT / Perplexity / Google AI）需要产品页面有 FAQPage schema
 * 才能在 AI 搜索结果中展示问答内容。此函数根据租户的产品目录自动
 * 生成常见问题，确保每个产品都有对应的 GEO 优化 FAQ。
 */
export function useRealGeoFaqs() {
  const config = useRuntimeConfig()
  const apiBase = (config.public as any)?.apiBase || ''

  const faqs = ref<FAQ[]>([])
  const loading = ref(false)

  async function loadFaqs() {
    loading.value = true
    try {
      // 获取租户产品数据来生成 FAQ
      const res = await $fetch<any>(`${apiBase}/api/v1/products/sitemap-feed?limit=50`)
      const products = res?.data || []
      const generated: FAQ[] = []

      products.forEach((p: any, i: number) => {
        const name = p.name || ''
        if (!name) return

        // 产品介绍 FAQ
        generated.push({
          id: `auto-${i}-what`,
          question: `What is ${name}?`,
          answer: p.description || `${name} is a high-quality product available from our factory.`,
          category: 'Product Knowledge',
          order: i * 3 + 1,
          featured: i < 3,
        })

        // 规格参数 FAQ
        if (p.specs?.length || p.specifications) {
          const specs = (p.specs || []).map((s: any) => `${s.label}: ${s.value}`).join(', ')
          generated.push({
            id: `auto-${i}-specs`,
            question: `What are the specifications of ${name}?`,
            answer: specs ? `Key specifications of ${name}: ${specs}.` : `Please contact us for detailed specifications of ${name}.`,
            category: 'Product Specifications',
            order: i * 3 + 2,
            featured: false,
          })
        }

        // 采购 FAQ
        generated.push({
          id: `auto-${i}-order`,
          question: `How to order ${name}?`,
          answer: `You can order ${name} by contacting us through the inquiry form on our website. We offer competitive factory prices, flexible MOQ, and worldwide shipping.`,
          category: 'Ordering',
          order: i * 3 + 3,
          featured: i === 0,
        })
      })

      faqs.value = generated
    } catch {
      faqs.value = []
    } finally {
      loading.value = false
    }
  }

  if (import.meta.client) {
    onMounted(() => { loadFaqs() })
  }

  // 生成 FAQPage JSON-LD
  const faqJsonLd = computed(() => {
    if (!faqs.value.length) return null
    return {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: faqs.value.slice(0, 30).map(faq => ({
        '@type': 'Question',
        name: faq.question,
        acceptedAnswer: {
          '@type': 'Answer',
          text: faq.answer,
        },
      })),
    }
  })

  return { faqs, loading, loadFaqs, faqJsonLd }
}
