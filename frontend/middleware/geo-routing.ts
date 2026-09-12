// Geo路由中间件 - 服务端IP识别，设置买家国家代码
// 在SSR阶段完成，确保SEO爬虫看到正确内容

export default defineNuxtRouteMiddleware((to) => {
  // 从URL参数或cookie获取国家代码
  const countryCode = to.query.country || useCookie('buyer_country').value || 'US'

  // 设置HTML lang属性（SEO）
  const langMap: Record<string, string> = {
    'CN': 'zh-CN', 'SA': 'ar-SA', 'AE': 'ar-AE', 'BR': 'pt-BR',
    'RU': 'ru-RU', 'DE': 'de-DE', 'FR': 'fr-FR', 'ES': 'es-ES',
    'US': 'en-US', 'TH': 'th-TH', 'VN': 'vi-VN', 'JP': 'ja-JP', 'KR': 'ko-KR',
    'NG': 'en-NG', 'KE': 'en-KE'
  }
  const htmlLang = langMap[countryCode as string] || 'en-US'
  useHead({
    htmlAttrs: { lang: htmlLang },
    meta: [
      { property: 'og:locale', content: htmlLang }
    ]
  })
})
