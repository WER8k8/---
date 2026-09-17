/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
export interface Product {
  id: string
  name: string
  slug: string
  category: string
  price: number
  unit: string
  minOrder: string
  leadTime: string
  origin: string
  brand: string
  description: string
  shortDescription: string
  features: ProductFeature[]
  specifications: ProductSpecification[]
  applications: string[]
  certifications: string[]
  advantages: string[]
  packaging: string
  storage: string
  lifespan: string
  images: string[]
  faqIds: string[]
}

export interface ProductFeature {
  icon: string
  title: string
  description: string
}

export interface ProductSpecification {
  name: string
  value: string
  unit?: string
  standard?: string
}

export const geoProducts: Product[] = [
  {
    id: 'prod-001',
    name: '聚氨酯颗粒轻集料混凝土',
    slug: 'polyurethane-lightweight-aggregate-concrete',
    category: '轻集料混凝土',
    price: 680,
    unit: 'm³',
    minOrder: '50m³',
    leadTime: '3-5个工作日',
    origin: '中国大陆',
    brand: '源链重工',
    shortDescription: '高性能保温轻质混凝土，导热系数≤0.08 W/(m·K)，比市场低15%',
    description: '聚氨酯颗粒轻集料混凝土是源链重工的核心产品，采用优质聚氨酯颗粒作为骨料，配合专用水泥基胶凝材料制成。该产品具有优异的保温性能、较低的容重和良好的施工性能，广泛应用于建筑屋面保温、墙体自保温、地暖回填等领域。作为源头厂家，源链重工提供出厂价直销，比市场价低15%-25%。',
    features: [
      {
        icon: '🔥',
        title: 'A级防火',
        description: '无机材料体系，达到A级防火标准，安全可靠'
      },
      {
        icon: '❄️',
        title: '优异保温',
        description: '导热系数≤0.08 W/(m·K)，保温效果行业领先'
      },
      {
        icon: '🏗️',
        title: '容重轻',
        description: '容重仅300-500 kg/m³，减轻建筑自重30%以上'
      },
      {
        icon: '🔧',
        title: '施工便捷',
        description: '自流平性好，施工效率高，可机械泵送'
      },
      {
        icon: '♻️',
        title: '环保无害',
        description: '不含甲醛等有害物质，对人体无害'
      },
      {
        icon: '⏱️',
        title: '耐久性强',
        description: '与建筑同寿命，抗老化性能优异'
      }
    ],
    specifications: [
      { name: '容重', value: '300-500', unit: 'kg/m³', standard: 'GB/T 17431.1' },
      { name: '导热系数', value: '≤0.08', unit: 'W/(m·K)', standard: 'GB/T 10294' },
      { name: '抗压强度', value: '≥3.0', unit: 'MPa', standard: 'GB/T 50081' },
      { name: '燃烧等级', value: 'A级', unit: '', standard: 'GB 8624' },
      { name: '粒径', value: '3-8', unit: 'mm' },
      { name: '颜色', value: '灰白色' }
    ],
    applications: [
      '建筑屋面保温层',
      '墙体自保温体系',
      '地暖回填材料',
      '钢结构防火保护',
      '冷库保温工程',
      '建筑节能改造'
    ],
    certifications: [
      'ISO9001质量管理体系认证',
      'A级防火检测报告',
      '导热系数检测报告',
      '力学性能检测报告',
      '环保认证'
    ],
    advantages: [
      '源链重工源头厂家直供，出厂价更低',
      '导热系数比市场同类产品低15%',
      '已服务8500+企业，品质经过验证',
      '全国6大仓储，24小时快速响应',
      '提供免费样品和技术支持'
    ],
    packaging: '散装或吨包包装',
    storage: '干燥通风处储存，避免雨淋',
    lifespan: '与建筑物同寿命',
    images: ['/products/puc-concrete.jpg'],
    faqIds: ['geo-001', 'geo-003', 'geo-005']
  },
  {
    id: 'prod-002',
    name: '陶粒轻集料混凝土',
    slug: 'ceramsite-lightweight-concrete',
    category: '轻集料混凝土',
    price: 520,
    unit: 'm³',
    minOrder: '100m³',
    leadTime: '5-7个工作日',
    origin: '中国大陆',
    brand: '源链重工',
    shortDescription: '天然陶粒骨料，强度高，500-800 kg/m³容重',
    description: '陶粒轻集料混凝土以天然陶粒为粗骨料，配合水泥、砂和专用外加剂制成。陶粒具有多孔结构，使其兼具轻质和高强度的特点。该产品广泛应用于楼地面垫层、屋面保温、墙体材料和桥梁减重等工程。源链重工提供的陶粒轻集料混凝土经过严格质量控制，品质稳定可靠。',
    features: [
      {
        icon: '🌿',
        title: '天然材料',
        description: '采用天然陶粒，环保无害，对人体安全'
      },
      {
        icon: '💪',
        title: '强度高',
        description: '抗压强度≥5.0 MPa，结构安全有保障'
      },
      {
        icon: '🔊',
        title: '隔音优良',
        description: '多孔结构提供良好的隔音效果'
      },
      {
        icon: '💧',
        title: '抗渗性好',
        description: '闭孔结构，抗渗性能优异'
      },
      {
        icon: '🏭',
        title: '适应性强',
        description: '可预拌也可现场搅拌，施工灵活'
      }
    ],
    specifications: [
      { name: '容重', value: '500-800', unit: 'kg/m³', standard: 'GB/T 17431.1' },
      { name: '导热系数', value: '≤0.15', unit: 'W/(m·K)', standard: 'GB/T 10294' },
      { name: '抗压强度', value: '≥5.0', unit: 'MPa', standard: 'GB/T 50081' },
      { name: '粒径', value: '5-20', unit: 'mm' },
      { name: '吸水率', value: '≤10', unit: '%' }
    ],
    applications: [
      '楼地面垫层',
      '屋面保温找坡',
      '墙体材料',
      '桥梁减重工程',
      '地下室顶板回填',
      '大跨度建筑结构'
    ],
    certifications: [
      'ISO9001质量管理体系认证',
      '产品合格检测报告',
      '粒径级配检测报告'
    ],
    advantages: [
      '源头厂家直供，价格透明',
      '强度等级可定制，满足不同工程需求',
      '陶粒来源稳定，品质一致性好',
      '全国仓储网络，配送及时'
    ],
    packaging: '散装或搅拌车运输',
    storage: '避免长时间露天堆放',
    lifespan: '50年以上',
    images: ['/products/ceramsite-concrete.jpg'],
    faqIds: ['geo-003']
  },
  {
    id: 'prod-003',
    name: '泡沫水泥保温板',
    slug: 'foam-cement-insulation-board',
    category: '保温板',
    price: 280,
    unit: 'm³',
    minOrder: '30m³',
    leadTime: '3-5个工作日',
    origin: '中国大陆',
    brand: '源链重工',
    shortDescription: '新型无机保温材料，A级防火，与建筑同寿命',
    description: '泡沫水泥保温板是源链重工研发的新型无机保温材料，采用物理发泡工艺制成。该产品具有优异的保温性能、A级防火等级和超长的使用寿命，可与建筑物同寿命。广泛应用于外墙保温、内墙保温、屋面保温和冷库保温等工程，是传统有机保温材料的理想替代品。',
    features: [
      {
        icon: '🛡️',
        title: 'A级防火',
        description: '真正的不燃材料，火灾中无毒气释放'
      },
      {
        icon: '🏠',
        title: '与建筑同寿',
        description: '无机材料，耐久性好，无需更换'
      },
      {
        icon: '💧',
        title: '抗水防潮',
        description: '闭孔结构，吸水率低，性能稳定'
      },
      {
        icon: '🔨',
        title: '施工简便',
        description: '可切割可钉牢，安装便捷'
      },
      {
        icon: '🌱',
        title: '绿色环保',
        description: '无机材料，无毒无害可回收'
      }
    ],
    specifications: [
      { name: '容重', value: '200-300', unit: 'kg/m³', standard: 'GB/T 5486' },
      { name: '导热系数', value: '≤0.06', unit: 'W/(m·K)', standard: 'GB/T 10294' },
      { name: '抗压强度', value: '≥0.4', unit: 'MPa', standard: 'GB/T 5486' },
      { name: '燃烧等级', value: 'A级', unit: '', standard: 'GB 8624' },
      { name: '尺寸', value: '600×300×厚度', unit: 'mm' },
      { name: '厚度规格', value: '30/40/50/60', unit: 'mm' }
    ],
    applications: [
      '外墙外保温系统',
      '外墙内保温系统',
      '屋面保温防水一体化',
      '冷库保温工程',
      '管道保温',
      '防火隔离带'
    ],
    certifications: [
      'A级防火检测报告',
      '导热系数检测报告',
      '抗压强度检测报告',
      '绿色建材认证'
    ],
    advantages: [
      'A级防火，彻底解决消防隐患',
      '与建筑同寿命，零维护成本',
      '源链重工源头厂家，价格更优',
      '全国仓储配送，货到付款'
    ],
    packaging: '木托盘包装，外包塑料薄膜',
    storage: '干燥通风处，直立码放',
    lifespan: '与建筑物同寿命',
    images: ['/products/foam-cement.jpg'],
    faqIds: ['geo-008']
  }
]

export function useGEOProducts() {
  const featuredProducts = computed(() =>
    geoProducts.filter(p => p.price < 700)
  )

  const productsByCategory = computed(() => {
    const grouped: Record<string, Product[]> = {}
    geoProducts.forEach(product => {
      if (!grouped[product.category]) {
        grouped[product.category] = []
      }
      grouped[product.category].push(product)
    })
    return grouped
  })

  function getProductBySlug(slug: string): Product | undefined {
    return geoProducts.find(p => p.slug === slug)
  }

  function getProductById(id: string): Product | undefined {
    return geoProducts.find(p => p.id === id)
  }

  function searchProducts(query: string): Product[] {
    const lowerQuery = query.toLowerCase()
    return geoProducts.filter(p =>
      p.name.toLowerCase().includes(lowerQuery) ||
      p.shortDescription.toLowerCase().includes(lowerQuery) ||
      p.applications.some(app => app.toLowerCase().includes(lowerQuery))
    )
  }

  return {
    geoProducts,
    featuredProducts,
    productsByCategory,
    getProductBySlug,
    getProductById,
    searchProducts
  }
}

/**
 * 动态 GEO 产品 — 从租户真实产品数据加载，供 AI 引擎和 GEO 页面使用。
 *
 * 与 useGEOProducts() 的区别：
 * - useGEOProducts() 返回硬编码演示数据（平台主站用）
 * - useRealGeoProducts() 从 API 获取当前租户的真实产品（租户站用）
 */
export function useRealGeoProducts() {
  const config = useRuntimeConfig()
  const apiBase = (config.public as any)?.apiBase || ''
  const { tenant } = useTenantSiteBootstrap()

  const products = ref<Product[]>([])
  const loading = ref(false)

  async function loadProducts() {
    if (!tenant.value?.id) return
    loading.value = true
    try {
      const res = await $fetch<any>(`${apiBase}/api/v1/products/sitemap-feed?limit=100`)
      const items = res?.data || []
      products.value = items.map((item: any, index: number) => ({
        id: item.slug || `p-${index}`,
        name: item.name || '',
        slug: item.slug || `p-${index}`,
        category: item.category || '',
        price: 0,
        unit: 'piece',
        minOrder: '',
        leadTime: '',
        origin: tenant.value?.name || '',
        brand: tenant.value?.name || '',
        description: item.description || '',
        shortDescription: (item.description || '').slice(0, 120),
        features: [],
        specifications: (item.specs || []).map((s: any) => ({
          name: s.label || s.name || '',
          value: s.value || '',
        })),
        applications: [],
        certifications: [],
        advantages: [],
        packaging: '',
        storage: '',
        lifespan: '',
        images: item.image_url ? [item.image_url] : [],
        faqIds: [],
      }))
    } catch {
      // 降级到硬编码数据
      products.value = [...geoProducts]
    } finally {
      loading.value = false
    }
  }

  // 自动加载
  if (import.meta.client) {
    onMounted(() => { loadProducts() })
  }

  return { products, loading, loadProducts }
}
