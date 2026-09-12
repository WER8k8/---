/**
 * index.ts — Cloudflare Workers 入口文件
 *
 * 整合 crawler / extractor / transmitter 三大模块
 * 通过 HTTP 接口触发爬取 -> 提取 -> 加密传输全流程
 */

import { crawlPage } from '../crawler';
import { extractInquiryInfo } from '../extractor';
import { encryptAndTransmit, TransmitResult } from '../transmitter';

export interface Env {
  WEBHOOK_URL: string;
  ENCRYPTION_KEY: string;
  HMAC_KEY: string;
  PROXY_ENDPOINT?: string;
  CRAWLER_CACHE?: KVNamespace;
  CRAWLER_DB?: D1Database;
}

/**
 * 生成唯一 inquiryId（基于 URL + 时间戳 + 随机数）
 */
function generateInquiryId(url: string): string {
  const urlHash = Array.from(new TextEncoder().encode(url))
    .reduce((hash, byte) => ((hash << 5) - hash) + byte, 0)
    .toString(36);
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 6);
  return `inq_${urlHash}_${timestamp}_${random}`;
}

/**
 * 请求体接口
 */
interface CrawlRequest {
  url: string;
  region?: 'auto' | 'en' | 'zh' | 'jp' | 'kr' | 'ru' | 'de' | 'fr' | 'es' | 'ar' | 'pt';
  timeout?: number;
  useProxy?: boolean;
  extractOnly?: boolean;
}

/**
 * 响应体接口
 */
interface CrawlResponse {
  success: boolean;
  inquiryId?: string;
  url?: string;
  crawlResult?: {
    statusCode: number;
    responseTimeMs: number;
    title: string;
    detectedLanguage: string;
    finalUrl: string;
  };
  extractionResult?: ReturnType<typeof extractInquiryInfo>;
  transmitResult?: TransmitResult;
  error?: string;
}

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext
  ): Promise<Response> {
    // CORS 预检
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, X-Inquiry-Id',
          'Access-Control-Max-Age': '86400',
        },
      });
    }

    // 只允许 POST
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Only POST method is allowed' }), {
        status: 405,
        headers: { 'Content-Type': 'application/json', 'Allow': 'POST' },
      });
    }

    try {
      const body: CrawlRequest = await request.json();

      if (!body.url || typeof body.url !== 'string') {
        return new Response(JSON.stringify({ error: 'Missing or invalid "url" field' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      // 校验 URL 格式
      try {
        new URL(body.url);
      } catch {
        return new Response(JSON.stringify({ error: 'Invalid URL format' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      // 第 1 步：爬取页面
      const crawlResult = await crawlPage({
        url: body.url,
        region: body.region || 'auto',
        timeout: body.timeout || 30000,
        useProxy: body.useProxy || false,
      });

      if (!crawlResult.success) {
        return new Response(JSON.stringify({
          success: false,
          url: body.url,
          crawlResult: {
            statusCode: crawlResult.statusCode,
            responseTimeMs: crawlResult.responseTimeMs,
            title: crawlResult.title,
            detectedLanguage: crawlResult.detectedLanguage,
            finalUrl: crawlResult.finalUrl,
          },
          error: crawlResult.error || 'Failed to crawl page',
        } as CrawlResponse), {
          status: 502,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      // 第 2 步：提取信息
      const extractionResult = extractInquiryInfo(crawlResult.html);

      // 如果是 extractOnly 模式，只返回提取结果
      if (body.extractOnly) {
        return new Response(JSON.stringify({
          success: true,
          url: body.url,
          crawlResult: {
            statusCode: crawlResult.statusCode,
            responseTimeMs: crawlResult.responseTimeMs,
            title: crawlResult.title,
            detectedLanguage: crawlResult.detectedLanguage,
            finalUrl: crawlResult.finalUrl,
          },
          extractionResult,
        } as CrawlResponse), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }

      // 第 3 步：加密传输
      const inquiryId = generateInquiryId(body.url);

      const transmitData: Record<string, unknown> = {
        url: body.url,
        title: crawlResult.title,
        detectedLanguage: crawlResult.detectedLanguage,
        statusCode: crawlResult.statusCode,
        responseTimeMs: crawlResult.responseTimeMs,
        emails: extractionResult.emails.map(e => e.email),
        phones: extractionResult.phones.map(p => p.phone),
        urls: extractionResult.urls.slice(0, 10).map(u => u.url),
        formFields: extractionResult.formFields,
        inquiryParagraphs: extractionResult.inquiryParagraphs.slice(0, 5),
        contactSectionFound: extractionResult.contactSectionFound,
        overallConfidence: extractionResult.overallConfidence,
      };

      let transmitResult: TransmitResult | undefined;

      if (env.WEBHOOK_URL && env.ENCRYPTION_KEY && env.HMAC_KEY) {
        transmitResult = await encryptAndTransmit(
          inquiryId,
          transmitData,
          env.WEBHOOK_URL,
          env.ENCRYPTION_KEY,
          env.HMAC_KEY
        );
      }

      const response: CrawlResponse = {
        success: true,
        inquiryId,
        url: body.url,
        crawlResult: {
          statusCode: crawlResult.statusCode,
          responseTimeMs: crawlResult.responseTimeMs,
          title: crawlResult.title,
          detectedLanguage: crawlResult.detectedLanguage,
          finalUrl: crawlResult.finalUrl,
        },
        extractionResult,
        transmitResult,
      };

      return new Response(JSON.stringify(response, null, 2), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      });
    } catch (error) {
      return new Response(JSON.stringify({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      });
    }
  },
};
