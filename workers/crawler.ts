/**
 * crawler.ts — Cloudflare Workers 网页爬虫引擎
 *
 * 功能：
 * - 智能路由（按 region 选择请求头/语言偏好）
 * - UA 轮换池（20+ 真实 UA，覆盖 Chrome/Firefox/Safari/Edge 桌面 + 移动端）
 * - 随机延迟 500-3000ms
 * - 代理接口预留
 * - 完整 HTML 获取（状态码、响应时间、页面标题、检测到的语言）
 * - Cookie 管理（模拟浏览器会话）
 */

export interface CrawlResult {
  success: boolean;
  statusCode: number;
  responseTimeMs: number;
  title: string;
  html: string;
  detectedLanguage: string;
  finalUrl: string;
  error?: string;
}

export interface CrawlOptions {
  url: string;
  region?: 'auto' | 'en' | 'zh' | 'jp' | 'kr' | 'ru' | 'de' | 'fr' | 'es' | 'ar' | 'pt';
  timeout?: number;
  useProxy?: boolean;
  cookieJar?: Map<string, string>;
  extraHeaders?: Record<string, string>;
}

// ===== UA 轮换池（20+ 真实 UA，覆盖主流浏览器桌面 + 移动端） =====

const USER_AGENTS: string[] = [
  // Chrome 120+ 桌面 (Windows)
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
  // Chrome 桌面 (Mac)
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
  // Firefox 桌面
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
  // Safari 桌面 (Mac)
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
  // Edge 桌面
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
  // Chrome 移动端 (Android)
  'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36',
  'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.164 Mobile Safari/537.36',
  // Chrome 移动端 (iOS)
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1',
  // Firefox 移动端
  'Mozilla/5.0 (Android 14; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0',
  // Safari 移动端 (iPad)
  'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
  // Edge 移动端
  'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36 Edg/120.0.0.0',
  // 额外：Opera 桌面
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
  // 额外：Samsung Internet 移动端
  'Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/24.0 Chrome/120.0.6099.144 Mobile Safari/537.36',
  // 额外：Chrome Linux
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  // 额外：Firefox Linux
  'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
];

// ===== 智能路由：按 region 选择 Accept-Language =====

const REGION_LANGUAGE_MAP: Record<string, string> = {
  auto: 'en-US,en;q=0.9',
  en: 'en-US,en;q=0.9',
  zh: 'zh-CN,zh;q=0.9,en;q=0.8',
  jp: 'ja-JP,ja;q=0.9,en;q=0.8',
  kr: 'ko-KR,ko;q=0.9,en;q=0.8',
  ru: 'ru-RU,ru;q=0.9,en;q=0.8',
  de: 'de-DE,de;q=0.9,en;q=0.8',
  fr: 'fr-FR,fr;q=0.9,en;q=0.8',
  es: 'es-ES,es;q=0.9,en;q=0.8',
  ar: 'ar-SA,ar;q=0.9,en;q=0.8',
  pt: 'pt-BR,pt;q=0.9,en;q=0.8',
};

const REGION_ACCEPT_MAP: Record<string, string> = {
  auto: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  en: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  zh: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
  jp: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
  kr: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  ru: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  de: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  fr: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  es: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  ar: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
  pt: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
};

/**
 * 从 UA 池中随机获取一个 User-Agent 字符串
 */
export function getRandomUserAgent(): string {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

/**
 * 返回代理端点 URL（预留接口）
 */
export function getProxyEndpoint(): string {
  // 返回值由 wrangler.toml vars 或环境变量覆盖
  return typeof PROXY_ENDPOINT !== 'undefined'
    ? PROXY_ENDPOINT
    : 'https://proxy.example.com/fetch';
}

/**
 * 提取页面 <title> 内容
 */
function extractTitle(html: string): string {
  const match = html.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
  return match ? match[1].trim() : '';
}

/**
 * 基于 Unicode 范围快速检测页面语言
 */
function detectPageLanguage(html: string): string {
  const text = html.replace(/<[^>]+>/g, '').substring(0, 2000);

  // 统计各 Unicode 区块字符数
  let cjkCount = 0;
  let cyrillicCount = 0;
  let arabicCount = 0;
  let koreanCount = 0;
  let japaneseKanaCount = 0;
  let latinCount = 0;

  for (const ch of text) {
    const code = ch.charCodeAt(0);
    if ((code >= 0x4E00 && code <= 0x9FFF) || (code >= 0x3400 && code <= 0x4DBF)) {
      cjkCount++;
    } else if (code >= 0x0400 && code <= 0x04FF) {
      cyrillicCount++;
    } else if (code >= 0x0600 && code <= 0x06FF || code >= 0x0750 && code <= 0x077F) {
      arabicCount++;
    } else if (code >= 0xAC00 && code <= 0xD7AF) {
      koreanCount++;
    } else if ((code >= 0x3040 && code <= 0x309F) || (code >= 0x30A0 && code <= 0x30FF)) {
      japaneseKanaCount++;
    } else if ((code >= 0x0041 && code <= 0x005A) || (code >= 0x0061 && code <= 0x007A)) {
      latinCount++;
    }
  }

  // 检查 lang/ charset meta
  const langMeta = html.match(/<html[^>]*\slang=["'](\w+)/i);
  if (langMeta) {
    const lang = langMeta[1].toLowerCase();
    if (lang.startsWith('zh')) return 'zh';
    if (lang.startsWith('ja')) return 'ja';
    if (lang.startsWith('ko')) return 'ko';
    if (lang.startsWith('ru')) return 'ru';
    if (lang.startsWith('ar')) return 'ar';
    if (lang.startsWith('de')) return 'de';
    if (lang.startsWith('fr')) return 'fr';
    if (lang.startsWith('es')) return 'es';
    if (lang.startsWith('pt')) return 'pt';
    return 'en';
  }

  const total = cjkCount + cyrillicCount + arabicCount + koreanCount + japaneseKanaCount + latinCount;
  if (total === 0) return 'unknown';

  const cjkRatio = cjkCount / total;
  const cyrillicRatio = cyrillicCount / total;
  const arabicRatio = arabicCount / total;
  const koreanRatio = koreanCount / total;
  const jpRatio = japaneseKanaCount / total;

  if (arabicRatio > 0.3) return 'ar';
  if (cyrillicRatio > 0.3) return 'ru';
  if (koreanRatio > 0.2) return 'ko';
  if (jpRatio > 0.1) return 'ja';
  if (cjkRatio > 0.3) {
    // 区分中文和日文：包含大量平假名/片假名才是日文
    if (jpRatio > 0.05) return 'ja';
    return 'zh';
  }
  return 'en';
}

/**
 * 构建请求头
 */
function buildHeaders(options: CrawlOptions): Record<string, string> {
  const lang = REGION_LANGUAGE_MAP[options.region || 'auto'] || REGION_LANGUAGE_MAP.auto;
  const accept = REGION_ACCEPT_MAP[options.region || 'auto'] || REGION_ACCEPT_MAP.auto;

  const headers: Record<string, string> = {
    'User-Agent': getRandomUserAgent(),
    'Accept': accept,
    'Accept-Language': lang,
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
  };

  if (options.cookieJar && options.cookieJar.size > 0) {
    const cookies: string[] = [];
    options.cookieJar.forEach((value, key) => {
      cookies.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
    });
    headers['Cookie'] = cookies.join('; ');
  }

  if (options.extraHeaders) {
    Object.assign(headers, options.extraHeaders);
  }

  return headers;
}

/**
 * 解析 Set-Cookie 并更新 Cookie Jar
 */
function updateCookieJar(cookieJar: Map<string, string>, setCookieHeaders: string[]): void {
  for (const setCookie of setCookieHeaders) {
    const parts = setCookie.split(';')[0].trim();
    const eqIndex = parts.indexOf('=');
    if (eqIndex > 0) {
      const key = decodeURIComponent(parts.substring(0, eqIndex));
      const value = decodeURIComponent(parts.substring(eqIndex + 1));
      cookieJar.set(key, value);
    }
  }
}

/**
 * 随机延迟 500-3000ms
 */
async function randomDelay(): Promise<void> {
  const ms = Math.floor(Math.random() * 2500) + 500;
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 核心函数：爬取页面
 *
 * 返回完整的 CrawlResult，含状态码、响应时间、标题、HTML、检测语言、最终 URL
 */
export async function crawlPage(options: CrawlOptions): Promise<CrawlResult> {
  const {
    url,
    timeout = 30000,
    useProxy = false,
    cookieJar = new Map<string, string>(),
  } = options;

  // 随机延迟防止反爬
  await randomDelay();

  const startTime = Date.now();
  const headers = buildHeaders(options);

  // 如果启用代理，设置代理相关参数
  let fetchUrl = url;
  if (useProxy) {
    const proxyEndpoint = getProxyEndpoint();
    fetchUrl = `${proxyEndpoint}?url=${encodeURIComponent(url)}`;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(fetchUrl, {
      method: 'GET',
      headers,
      signal: controller.signal,
      redirect: 'follow',
    });

    clearTimeout(timeoutId);
    const responseTimeMs = Date.now() - startTime;

    // 更新 Cookie
    const setCookieHeaders = response.headers.get('Set-Cookie');
    if (setCookieHeaders) {
      // 多个 Set-Cookie 行被合并到同一个头中，需要按行拆分
      const cookies = setCookieHeaders.split(/\n|,(?=\s*[^;]+=)/);
      updateCookieJar(cookieJar, cookies);
    }

    const html = await response.text();
    const title = extractTitle(html);
    const detectedLanguage = detectPageLanguage(html);

    return {
      success: response.ok,
      statusCode: response.status,
      responseTimeMs,
      title,
      html,
      detectedLanguage,
      finalUrl: response.url,
    };
  } catch (error) {
    const responseTimeMs = Date.now() - startTime;
    return {
      success: false,
      statusCode: 0,
      responseTimeMs,
      title: '',
      html: '',
      detectedLanguage: 'unknown',
      finalUrl: url,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
