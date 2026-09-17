/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/** AI 爬虫 UA 识别 — 对标 Edge GEO Middleware，适配 Nuxt Nitro */

const AI_CRAWLER_PATTERNS: Array<{ family: string; re: RegExp }> = [
  { family: 'openai', re: /GPTBot|ChatGPT-User|OAI-SearchBot/i },
  { family: 'anthropic', re: /ClaudeBot|Claude-Web|anthropic-ai/i },
  { family: 'perplexity', re: /PerplexityBot/i },
  { family: 'google', re: /Google-Extended|GoogleOther/i },
  { family: 'bing', re: /bingbot/i },
  { family: 'meta', re: /FacebookBot|meta-externalagent/i },
]

export function isAiCrawlerUserAgent(userAgent: string): boolean {
  if (!userAgent) return false
  return AI_CRAWLER_PATTERNS.some(({ re }) => re.test(userAgent))
}

export function detectAiCrawlerFamily(userAgent: string): string | null {
  if (!userAgent) return null
  for (const { family, re } of AI_CRAWLER_PATTERNS) {
    if (re.test(userAgent)) return family
  }
  return null
}

export function resolveTenantDomainFromEvent(event: {
  path?: string
  node?: { req?: { url?: string } }
}): string {
  try {
    const raw = event.path || event.node?.req?.url || '/'
    const qIndex = raw.indexOf('?')
    const qs = qIndex >= 0 ? raw.slice(qIndex + 1) : ''
    const params = new URLSearchParams(qs)
    const tenant = params.get('__tenant') || params.get('tenant')
    if (tenant?.trim()) return tenant.trim()
  } catch {
    /* ignore */
  }
  return ''
}
