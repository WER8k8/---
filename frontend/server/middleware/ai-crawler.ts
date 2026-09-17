/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * Nuxt 版 AI 爬虫网关 — 识别 Bot UA，预取 llms 语义载荷 + 产品结构化数据供 render 钩子注入。
 * 对标 Next.js Edge GEO Middleware，运行在 Nitro server middleware 层。
 */
import { defineEventHandler, getHeader, getQuery, setHeader } from 'h3'
import {
  detectAiCrawlerFamily,
  isAiCrawlerUserAgent,
  resolveTenantDomainFromEvent,
} from '../utils/ai-crawler'

export default defineEventHandler(async (event) => {
  if (event.method !== 'GET') return

  const url = event.path || event.node.req.url || '/'
  if (/^\/(api\/|_nuxt\/|uploads\/|llms|favicon|images\/|fonts\/)/.test(url)) return

  const ua = getHeader(event, 'user-agent') || ''
  if (!isAiCrawlerUserAgent(ua)) return

  event.context.isAiCrawler = true
  event.context.aiCrawlerFamily = detectAiCrawlerFamily(ua)
  setHeader(event, 'X-YouDing-AI-Crawler', event.context.aiCrawlerFamily || '1')

  const q = getQuery(event)
  const tenant =
    String(q.__tenant || q.tenant || '').trim() || resolveTenantDomainFromEvent(event)
  if (!tenant) return

  const config = useRuntimeConfig()
  const apiHost = String(config.public.apiHost || 'http://127.0.0.1:8001').replace(/\/$/, '')

  // 1. 预取 llms.txt 语义载荷
  try {
    const text = await $fetch<string>(
      `${apiHost}/api/v1/public/tenants/${encodeURIComponent(tenant)}/llms-full.txt`,
      { responseType: 'text' },
    )
    event.context.aiSemanticText = text
  } catch {
    try {
      event.context.aiSemanticText = await $fetch<string>(
        `${apiHost}/api/v1/public/tenants/${encodeURIComponent(tenant)}/llms.txt`,
        { responseType: 'text' },
      )
    } catch {
      event.context.aiSemanticText = ''
    }
  }

  // 2. 预取产品结构化数据（供 AI 爬虫直接读取，不需要等页面渲染）
  try {
    const products = await $fetch<any>(
      `${apiHost}/api/v1/products/sitemap-feed?limit=20`,
    )
    const items = products?.data || []
    if (items.length > 0) {
      // 生成 Product[] JSON-LD for AI crawlers
      const productJsonLd = items.slice(0, 10).map((p: any) => {
        const schema: Record<string, unknown> = {
          '@type': 'Product',
          name: p.name,
          description: p.description || p.name,
        }
        if (p.image_url) schema.image = p.image_url
        if (p.slug) schema.url = `${tenant}/products/${p.slug}`
        return schema
      })
      event.context.aiProductJsonLd = JSON.stringify({
        '@context': 'https://schema.org',
        '@graph': productJsonLd,
      })
    }
  } catch {
    // 产品数据获取失败不影响页面渲染
  }
})
