// Geo工具函数 - IP地理位置识别
// 支持浏览器端和SSR端

export interface GeoResult {
  countryCode: string
  countryName: string
  region: string
}

// 国家代码 → 语言映射
export const COUNTRY_TO_LANG: Record<string, string> = {
  'CN': 'zh', 'TW': 'zh', 'HK': 'zh',
  'SA': 'ar', 'AE': 'ar', 'EG': 'ar', 'DZ': 'ar', 'MA': 'ar',
  'DE': 'de',
  'FR': 'fr',
  'ES': 'es', 'MX': 'es', 'AR': 'es', 'CO': 'es',
  'BR': 'pt', 'PT': 'pt',
  'RU': 'ru', 'BY': 'ru', 'KZ': 'ru', 'UZ': 'ru',
  'TH': 'th',
  'VN': 'vi',
  'JP': 'ja',
  'KR': 'ko',
  'US': 'en', 'CA': 'en', 'GB': 'en', 'AU': 'en',
  'NG': 'en', 'KE': 'en', 'GH': 'en', 'ZA': 'en'
}

// 国家代码 → 默认IM工具
export const COUNTRY_TO_IM: Record<string, { type: string; priority: number }[]> = {
  'TH': [{ type: 'line', priority: 0 }],
  'RU': [{ type: 'telegram', priority: 0 }, { type: 'viber', priority: 1 }],
  'VN': [{ type: 'zalo', priority: 0 }],
  'JP': [],
  'KR': [],
  'US': [{ type: 'live_chat', priority: 0 }],
  'CA': [{ type: 'live_chat', priority: 0 }],
  // 默认：WhatsApp
  'default': [{ type: 'whatsapp', priority: 0 }]
}

// 识别访客国家（浏览器端 - 调用后端API）
export async function detectCountryClient(): Promise<string> {
  try {
    // 优先使用缓存
    const cached = localStorage.getItem('buyer_country')
    if (cached) return cached

    // 调用后端Geo API
    const res = await $fetch<GeoResult>('/api/v1/v1/geo/detect', { timeout: 2000 })
    const code = res.countryCode || 'US'
    localStorage.setItem('buyer_country', code)
    return code
  } catch (e) {
    return 'US' // 兜底
  }
}

// 识别访客国家（SSR端 - 从请求头解析）
export function detectCountryServer(event: any): string {
  const forwarded = getHeader(event, 'x-forwarded-for')
  const realIp = getHeader(event, 'x-real-ip')
  // 这里仅返回默认值，真正的IP识别由后端中间件完成
  // SSR端通过API获取
  return 'US'
}

// 获取Header辅助函数（Nuxt 3兼容）
function getHeader(event: any, name: string): string | null {
  if (event.node?.req?.headers) {
    return event.node.req.headers[name.toLowerCase()] || null
  }
  if (event.headers) {
    return event.headers.get(name) || null
  }
  return null
}

// 根据国家代码获取语言
export function getLanguageByCountry(countryCode: string): string {
  return COUNTRY_TO_LANG[countryCode] || 'en'
}

// 根据国家代码获取IM工具配置
export function getImToolsByCountry(countryCode: string): { type: string; priority: number }[] {
  return COUNTRY_TO_IM[countryCode] || COUNTRY_TO_IM['default']
}

// WhatsApp链接生成
export function getWhatsAppLink(phone: string, text: string): string {
  const cleanPhone = phone.replace(/[^0-9]/g, '')
  return `https://wa.me/${cleanPhone}?text=${encodeURIComponent(text)}`
}

// Telegram链接生成
export function getTelegramLink(username: string): string {
  return `https://t.me/${username.replace('@', '')}`
}
