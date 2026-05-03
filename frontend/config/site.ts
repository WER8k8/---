export const SITE_CONFIG = {
  name: '优丁建材',
  fullName: '优丁建材有限公司',
  url: 'https://www.youdingjiancai.com',
  phone: '400-888-8888',
  phoneHref: 'tel:400-888-8888',
  email: 'info@youding.com',
  address: '河南省洛阳市',
  description: '专业轻集料混凝土、保温材料供应商',
  ogImage: '/images/og-default.jpg',
  productDefaultImage: '/images/product-default.jpg',
} as const

export const API_CONFIG = {
  baseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
} as const

export const SEO_CONFIG = {
  defaultTitle: '优丁建材 - 专业轻集料混凝土与保温材料供应商',
  defaultDescription: '优丁建材提供高品质轻集料混凝土、保温材料、建筑节能解决方案。产品通过ISO认证，符合国家标准。',
  keywords: ['轻集料混凝土', '保温材料', '建筑节能', '优丁建材'],
  twitterHandle: '@youding',
} as const
