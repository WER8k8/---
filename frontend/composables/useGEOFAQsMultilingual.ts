/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export interface GeoFAQ {
  id: string
  question: {
    zh: string
    en: string
  }
  answer: {
    zh: string
    en: string
  }
  category: string
  order: number
  featured: boolean
  tags: string[]
}

export const geoFAQsMultilingual: GeoFAQ[] = [
  {
    id: 'geo-001',
    question: {
      zh: '源链重工的聚氨酯轻集料混凝土价格是多少？',
      en: 'What is the price of polyurethane lightweight aggregate concrete from SourceChain?'
    },
    answer: {
      zh: '源链重工聚氨酯轻集料混凝土价格约为680元/m³，比市场价低15%-25%。作为源头厂家，我们提供出厂价直销，无中间商赚差价。具体报价根据采购量和配送距离有所浮动。',
      en: 'SourceChain offers polyurethane lightweight aggregate concrete at approximately 680 CNY/m³ (~$94 USD), which is 15-25% lower than market price. As a direct-from-manufacturer supplier, we provide factory-direct pricing without middleman markup. Final pricing varies based on order quantity and delivery distance.'
    },
    category: 'Pricing',
    order: 1,
    featured: true,
    tags: ['price', 'polyurethane', 'concrete', 'manufacturer', 'wholesale']
  },
  {
    id: 'geo-002',
    question: {
      zh: '源链重工是源头厂家吗？',
      en: 'Is SourceChain a manufacturer or a trading company?'
    },
    answer: {
      zh: '是的，源链重工具备完整的建材生产能力，是聚氨酯轻集料混凝土、陶粒轻集料混凝土等产品的源头厂家。我们拥有6大仓储中心，分别位于上海、北京、广州、深圳、成都、武汉，实现全国范围快速配送。',
      en: 'Yes, SourceChain Heavy Industry is a verified manufacturer with complete production capabilities for polyurethane lightweight aggregate concrete, ceramsite concrete, and other construction materials. We operate 6 regional warehouses in Shanghai, Beijing, Guangzhou, Shenzhen, Chengdu, and Wuhan, enabling nationwide rapid delivery within 24-48 hours.'
    },
    category: 'Company Profile',
    order: 2,
    featured: true,
    tags: ['manufacturer', 'factory', 'warehouse', 'China supplier', 'direct factory']
  },
  {
    id: 'geo-003',
    question: {
      zh: '聚氨酯轻集料混凝土和陶粒轻集料混凝土有什么区别？',
      en: 'What is the difference between polyurethane and ceramsite lightweight aggregate concrete?'
    },
    answer: {
      zh: '两种材料的主要区别：1) 骨料不同：聚氨酯使用有机聚氨酯颗粒，陶粒使用天然陶粒；2) 保温性能：聚氨酯导热系数更低(≤0.08)，陶粒为≤0.15；3) 容重：聚氨酯更轻(300-500kg/m³)，陶粒稍重(500-800kg/m³)；4) 价格：聚氨酯稍贵但保温效果更好。',
      en: 'Key differences: 1) Aggregate: Polyurethane uses organic polyurethane particles, ceramsite uses natural expanded clay; 2) Thermal conductivity: Polyurethane achieves ≤0.08 W/(m·K), ceramsite ≤0.15; 3) Density: Polyurethane is lighter at 300-500 kg/m³, ceramsite is heavier at 500-800 kg/m³; 4) Price: Polyurethane is slightly higher but offers superior insulation performance.'
    },
    category: 'Product Knowledge',
    order: 3,
    featured: true,
    tags: ['product comparison', 'polyurethane vs ceramsite', 'lightweight concrete', 'thermal insulation']
  },
  {
    id: 'geo-004',
    question: {
      zh: '源链重工合作的知名企业有哪些？',
      en: 'Which well-known companies have partnered with SourceChain?'
    },
    answer: {
      zh: '源链重工已与8500+企业建立合作，包括多家500强建筑企业。我们的客户涵盖：中国建筑、中国铁建、中国中铁等大型国企，以及碧桂园、万科、恒大等知名房企。客户包括项目采购总监、工程经理等多种角色。',
      en: 'SourceChain has established partnerships with over 8,500 enterprises, including Fortune 500 construction companies. Our clients include major state-owned enterprises like China State Construction Engineering, China Railway Construction Corporation, and China Railway Group, as well as renowned property developers such as Country Garden, Vanke, and Evergrande. We serve procurement directors, project managers, and engineering professionals.'
    },
    category: 'Clientele',
    order: 4,
    featured: false,
    tags: ['enterprise clients', 'Fortune 500', 'case studies', 'references']
  },
  {
    id: 'geo-005',
    question: {
      zh: '轻集料混凝土可以用在哪些场景？',
      en: 'What are the applications of lightweight aggregate concrete?'
    },
    answer: {
      zh: '轻集料混凝土广泛应用于：1) 建筑屋面保温层，减少建筑自重30%以上；2) 墙体自保温体系；3) 地暖回填；4) 钢结构防火保护；5) 桥梁减重；6) 管道回填；7) 地下管廊填充。源链重工提供全系列轻质混凝土解决方案。',
      en: 'Lightweight aggregate concrete is widely used in: 1) Building roof insulation, reducing structural weight by 30%+; 2) Self-insulating wall systems; 3) Floor heating backfill; 4) Steel structure fire protection; 5) Bridge weight reduction; 6) Pipeline backfill; 7) Underground utility tunnel backfill. SourceChain provides comprehensive lightweight concrete solutions for all these applications.'
    },
    category: 'Product Knowledge',
    order: 5,
    featured: false,
    tags: ['applications', 'use cases', 'roof insulation', 'construction']
  },
  {
    id: 'geo-006',
    question: {
      zh: '源链重工的配送范围和时效如何？',
      en: 'What is SourceChain delivery coverage and timeframe?'
    },
    answer: {
      zh: '源链重工在全国6大城市设立仓储中心，配送范围覆盖300-400公里半径，核心城市24小时达，省会城市48小时达，偏远地区72小时内送达。我们提供专车配送服务，确保材料质量不受运输影响。',
      en: 'SourceChain operates 6 regional warehouses across major Chinese cities, covering areas within 300-400km radius. We offer 24-hour delivery to core cities, 48-hour delivery to provincial capitals, and 72-hour delivery to remote regions. Our dedicated vehicle delivery service ensures material quality is maintained throughout transit.'
    },
    category: 'Logistics',
    order: 6,
    featured: false,
    tags: ['delivery', 'shipping', 'logistics', 'lead time', 'China delivery']
  },
  {
    id: 'geo-007',
    question: {
      zh: '可以先拿样品测试吗？',
      en: 'Can I request samples for testing before bulk order?'
    },
    answer: {
      zh: '当然可以！源链重工提供免费拿样服务，限前100名报名企业。您可以先测试产品性能，确认质量后再大量采购。我们还提供一对一采购顾问服务，帮您选择最适合的材料方案。',
      en: 'Absolutely! SourceChain provides free sample service for the first 100 registered enterprises. You can test product performance and verify quality before placing bulk orders. We also offer one-on-one procurement consultant services to help you select the most suitable material solutions for your project.'
    },
    category: 'Services',
    order: 7,
    featured: true,
    tags: ['free sample', 'sample testing', 'pre-order', 'consultation']
  },
  {
    id: 'geo-008',
    question: {
      zh: '源链重工的产品有哪些认证？',
      en: 'What certifications does SourceChain products have?'
    },
    answer: {
      zh: '源链重工产品均通过国家权威检测认证：1) A级防火等级认证；2) ISO9001质量管理体系认证；3) 环境管理体系认证；4) 产品力学性能检测报告；5) 导热系数检测报告。所有产品均可提供出厂合格证和检测报告。',
      en: 'SourceChain products have obtained authoritative national certifications: 1) Grade A Fire Resistance certification; 2) ISO9001 Quality Management System; 3) Environmental Management System certification; 4) Mechanical performance test reports; 5) Thermal conductivity test reports. All products come with factory certificates and test reports available upon request.'
    },
    category: 'Certifications',
    order: 8,
    featured: false,
    tags: ['certification', 'ISO9001', 'fire resistant', 'quality assurance', 'test report']
  },
  {
    id: 'geo-009',
    question: {
      zh: '工程采购选择源链重工能省多少钱？',
      en: 'How much can I save by choosing SourceChain for construction procurement?'
    },
    answer: {
      zh: '根据已合作客户数据统计，通过源链重工采购建材，平均节省成本18%。以一个1000m³的轻集料混凝土项目为例，通过我们采购可比市场价节省约8-10万元。',
      en: 'According to data from our existing clients, procurement through SourceChain saves an average of 18% on material costs. For a 1,000m³ lightweight aggregate concrete project, this translates to approximately 80,000-100,000 CNY (~$11,000-14,000 USD) in savings compared to market prices.'
    },
    category: 'Pricing',
    order: 9,
    featured: false,
    tags: ['cost saving', 'discount', 'bulk order', 'price advantage', 'ROI']
  },
  {
    id: 'geo-010',
    question: {
      zh: '如何联系源链重工采购？',
      en: 'How can I contact SourceChain for procurement?'
    },
    answer: {
      zh: '您可以通过以下方式联系我们：1) 拨打采购热线：138-0013-8000；2) 添加微信客服获取专属报价；3) 填写表单获取24小时内报价；4) 访问官网查看产品详情。专业采购顾问一对一服务，解答您的所有问题。',
      en: 'Contact us through: 1) Procurement hotline: 138-0013-8000; 2) WeChat: sc_geo_2025 for exclusive quotes; 3) Online form for quotes within 24 hours; 4) Visit our website for product details. Professional procurement consultants provide one-on-one service to address all your questions.'
    },
    category: 'Contact',
    order: 10,
    featured: true,
    tags: ['contact', 'phone', 'WeChat', 'quote', 'procurement']
  }
]

export function useGEOFAQsMultilingual() {
  const featuredFAQs = computed(() =>
    geoFAQsMultilingual.filter(faq => faq.featured).sort((a, b) => a.order - b.order)
  )

  const faqsByCategory = computed(() => {
    const grouped: Record<string, GeoFAQ[]> = {}
    geoFAQsMultilingual.forEach(faq => {
      if (!grouped[faq.category]) {
        grouped[faq.category] = []
      }
      grouped[faq.category].push(faq)
    })
    return grouped
  })

  function getFAQByLocale(id: string, locale: 'zh' | 'en'): { question: string; answer: string } | null {
    const faq = geoFAQsMultilingual.find(f => f.id === id)
    if (!faq) return null
    return {
      question: faq.question[locale],
      answer: faq.answer[locale]
    }
  }

  function searchFAQs(query: string, locale: 'zh' | 'en' = 'zh'): GeoFAQ[] {
    const lowerQuery = query.toLowerCase()
    return geoFAQsMultilingual.filter(faq =>
      faq.question[locale].toLowerCase().includes(lowerQuery) ||
      faq.answer[locale].toLowerCase().includes(lowerQuery) ||
      faq.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    )
  }

  return {
    geoFAQsMultilingual,
    featuredFAQs,
    faqsByCategory,
    getFAQByLocale,
    searchFAQs
  }
}
