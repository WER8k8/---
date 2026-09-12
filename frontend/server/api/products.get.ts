/**
 * Products list API with in-memory mock data and HTTP cache headers.
 */
import { defineEventHandler, getQuery } from 'h3'
import { cacheHeaders } from '../utils/cache'

interface Product {
  id: string
  name: string
  slug: string
  category: string
  price: number
  unit: string
  description: string
  features: string[]
  applications: string[]
  specifications: Record<string, string>
  image: string
  tag?: string
}

const mockProducts: Product[] = [
  {
    id: '1',
    name: '聚氨酯颗粒轻集料混凝土',
    slug: 'polyurethane-lightweight-aggregate-concrete',
    category: '轻集料混凝土',
    price: 680,
    unit: 'm³',
    description: '高性能保温轻质混凝土，适用于建筑屋面、墙体保温',
    features: [
      '导热系数低，保温性能优异',
      '容重轻，减轻建筑自重',
      '施工便捷，浇筑流动性好',
      '耐久性好，使用寿命长',
    ],
    applications: ['建筑屋面保温', '墙体自保温', '地暖回填', '钢结构防火保护'],
    specifications: {
      '容重': '300-500 kg/m³',
      '导热系数': '≤0.08 W/(m·K)',
      '抗压强度': '≥3.0 MPa',
      '燃烧等级': 'A级不燃',
    },
    image: '/products/puc-concrete.jpg',
    tag: '热销',
  },
  {
    id: '2',
    name: '陶粒轻集料混凝土',
    slug: 'ceramsite-lightweight-concrete',
    category: '轻集料混凝土',
    price: 520,
    unit: 'm³',
    description: '天然陶粒为骨料的轻质混凝土',
    features: [
      '天然材料，环保无害',
      '强度高，结构安全',
      '隔音效果好',
      '施工适应性强',
    ],
    applications: ['楼地面垫层', '屋面保温', '墙体材料', '桥梁减重'],
    specifications: {
      '容重': '500-800 kg/m³',
      '导热系数': '≤0.15 W/(m·K)',
      '抗压强度': '≥5.0 MPa',
      '粒径': '5-20mm',
    },
    image: '/products/ceramsite-concrete.jpg',
  },
  {
    id: '3',
    name: '泡沫水泥保温板',
    slug: 'foam-cement-insulation-board',
    category: '保温板',
    price: 280,
    unit: 'm³',
    description: '新型无机保温材料，A级防火',
    features: [
      'A级防火，安全可靠',
      '与建筑同寿命',
      '抗水防潮',
      '施工简便',
    ],
    applications: ['外墙保温', '内墙保温', '屋面保温', '冷库保温'],
    specifications: {
      '容重': '200-300 kg/m³',
      '导热系数': '≤0.06 W/(m·K)',
      '抗压强度': '≥0.4 MPa',
      '燃烧等级': 'A级不燃',
    },
    image: '/products/foam-cement.jpg',
    tag: '新品',
  },
  {
    id: '4',
    name: '加气轻质回填料',
    slug: 'aerated-lightweight-fill',
    category: '回填材料',
    price: 380,
    unit: 'm³',
    description: '气泡混合轻质填料，用于管道回填',
    features: [
      '流动性好，自流平',
      '强度可调节',
      '防水性能优',
      '施工速度快',
    ],
    applications: ['管道回填', '地基填充', '地下管廊回填', '屋顶轻质填充'],
    specifications: {
      '容重': '400-600 kg/m³',
      '流动度': '≥180mm',
      '抗压强度': '≥1.0 MPa',
      '吸水率': '≤10%',
    },
    image: '/products/aerated-fill.jpg',
  },
]

export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const category = query.category as string | undefined
  const search = query.search as string | undefined

  let products = [...mockProducts]

  if (category) {
    products = products.filter(p => p.category === category)
  }

  if (search) {
    const searchLower = search.toLowerCase()
    products = products.filter(p =>
      p.name.toLowerCase().includes(searchLower)
      || p.description.toLowerCase().includes(searchLower)
    )
  }

  // Set cache headers for 1h with stale-while-revalidate
  cacheHeaders(event, {
    maxAge: 3600,
    staleMaxAge: 7200,
  })

  return {
    success: true,
    data: products,
    meta: {
      total: products.length,
      timestamp: new Date().toISOString(),
    },
  }
})
