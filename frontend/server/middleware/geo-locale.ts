/**
 * IP 地理位置 → 语言自动切换中间件
 *
 * 检测优先级：
 *   1. Cloudflare CF-IPCountry 头
 *   2. Vercel x-vercel-ip-country 头
 *   3. ip-api.com 免费 API（45次/分钟，无需 key）
 *   4. 默认 zh（中国大陆）
 *
 * 跳过条件：
 *   - 已有 i18n_redirected cookie（用户手动选过语言）
 *   - URL 已包含 locale 前缀（如 /en/、/de/）
 *   - 非 GET 请求
 *   - API/静态资源请求
 */

import { defineEventHandler, getHeader, getRequestIP, setCookie, sendRedirect, getCookie } from 'h3'

// 国家代码 → locale 映射表（覆盖全球主要国家）
const COUNTRY_TO_LOCALE: Record<string, string> = {
  // 中文地区
  cn: 'zh', hk: 'zh', tw: 'zh', mo: 'zh', sg: 'zh',
  // 英语地区
  us: 'en', gb: 'en', ca: 'en', au: 'en', nz: 'en', ie: 'en',
  in: 'en', ph: 'en', my: 'en', za: 'en', ng: 'en', ke: 'en',
  gh: 'en', tz: 'en', ug: 'en', pk: 'en', bd: 'en', lk: 'en',
  // 德语地区
  de: 'de', at: 'de', ch: 'de', li: 'de', lu: 'de',
  // 法语地区
  fr: 'fr', be: 'fr', mc: 'fr', ci: 'fr', sn: 'fr', ma: 'fr',
  dz: 'fr', tn: 'fr', ml: 'fr', bf: 'fr', ne: 'fr', tg: 'fr',
  bj: 'fr', cm: 'fr', cg: 'fr', ga: 'fr', cd: 'fr', mg: 'fr',
  // 西班牙语地区
  es: 'es', mx: 'es', ar: 'es', co: 'es', cl: 'es', pe: 'es',
  ve: 'es', ec: 'es', gt: 'es', cu: 'es', bo: 'es', do: 'es',
  hn: 'es', py: 'es', sv: 'es', ni: 'es', cr: 'es', pa: 'es',
  uy: 'es', gq: 'es',
  // 阿拉伯语地区
  sa: 'ar', ae: 'ar', qa: 'ar', kw: 'ar', om: 'ar', bh: 'ar',
  eg: 'ar', jo: 'ar', lb: 'ar', iq: 'ar', sy: 'ar', ye: 'ar',
  ly: 'ar', sd: 'ar', mr: 'ar', ps: 'ar',
  // 日语
  jp: 'ja',
  // 韩语
  kr: 'ko', kp: 'ko',
  // 俄语地区
  ru: 'ru', by: 'ru', kz: 'ru', kg: 'ru', tj: 'ru', uz: 'ru',
  tm: 'ru', am: 'ru', az: 'ru', md: 'ru', ua: 'ru',
  // 葡萄牙语地区
  pt: 'pt', br: 'pt', ao: 'pt', mz: 'pt', cv: 'pt', gw: 'pt',
  st: 'pt',
  // 泰语
  th: 'th',
  // 越南语
  vn: 'vi',
}

// 已知的 locale 前缀列表（不包含默认 zh）
const LOCALE_PREFIXES = ['en', 'de', 'fr', 'es', 'ar', 'ja', 'ko', 'ru', 'pt', 'th', 'vi']

// ip-api.com 免费 API（无需 key，45次/分钟限制）
async function detectCountryByIP(ip: string): Promise<string | null> {
  try {
    // 跳过本地/内网 IP
    if (ip === '127.0.0.1' || ip === '::1' || ip === 'localhost'
      || ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.')) {
      return null
    }

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000)

    const res = await fetch(`http://ip-api.com/json/${ip}?fields=countryCode`, {
      signal: controller.signal,
    })
    clearTimeout(timeout)

    if (!res.ok) return null
    const data = await res.json() as { countryCode?: string }
    return data.countryCode?.toLowerCase() ?? null
  } catch {
    return null
  }
}

// 可被 locale 前缀匹配的路径
const LOCALE_PATH_RE = new RegExp(`^/(${LOCALE_PREFIXES.join('|')})(?:/|$)`)

export default defineEventHandler(async (event) => {
  // 只处理 GET 请求
  if (event.method !== 'GET') return

  const url = event.path || event.node.req.url || '/'

  // 跳过非页面请求：API、静态资源、llms、_nuxt
  if (/^\/(api\/|_nuxt\/|__|favicon|images\/|fonts\/|sw\.|llms)/.test(url)) return

  // URL 已有 locale 前缀 → 用户已在使用特定语言，不干预
  if (LOCALE_PATH_RE.test(url)) return

  // 已有 cookie → 用户已选过语言或已被重定向过
  const cookie = getCookie(event, 'i18n_redirected')
  if (cookie && LOCALE_PREFIXES.includes(cookie)) return

  // ====== 检测国家 ======
  let countryCode: string | null = null

  // 1. Cloudflare
  const cfCountry = getHeader(event, 'cf-ipcountry')
  if (cfCountry) {
    countryCode = cfCountry.toLowerCase()
  }

  // 2. Vercel
  if (!countryCode) {
    const vercelCountry = getHeader(event, 'x-vercel-ip-country')
    if (vercelCountry) {
      countryCode = vercelCountry.toLowerCase()
    }
  }

  // 3. ip-api.com
  if (!countryCode) {
    const ip = getRequestIP(event, { xForwardedFor: true })
    if (ip) {
      countryCode = await detectCountryByIP(ip)
    }
  }

  // 4. 无结果 → 不干预（让浏览器语言检测兜底）
  if (!countryCode) return

  // ====== 映射到 locale ======
  const locale = COUNTRY_TO_LOCALE[countryCode]
  if (!locale) return // 未覆盖的国家，不干预

  // 设置 cookie（有效期 365 天）
  setCookie(event, 'i18n_redirected', locale, {
    path: '/',
    maxAge: 365 * 24 * 60 * 60,
    httpOnly: false,
    secure: false,
    sameSite: 'lax',
  })

  // 默认语言 zh 不需要前缀重定向
  if (locale === 'zh') {
    // 已在根路径，无需跳转
    return
  }

  // 非默认语言 → 302 跳转到 /{locale}/
  const target = `/${locale}${url === '/' ? '/' : url}`
  await sendRedirect(event, target, 302)
})
