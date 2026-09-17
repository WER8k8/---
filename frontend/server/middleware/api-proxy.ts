/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { defineEventHandler, proxyRequest, createError, sendError } from 'h3';
import { useRuntimeConfig } from '#imports';

const RATE_LIMIT = 100;
const RATE_LIMIT_WINDOW = 60 * 1000;
const requestCounts = new Map<string, { count: number; timestamp: number }>();

function getClientIp(event: any): string {
  const xForwardedFor = event.node.req.headers['x-forwarded-for'];
  const xRealIp = event.node.req.headers['x-real-ip'];
  if (xForwardedFor) {
    return Array.isArray(xForwardedFor) ? xForwardedFor[0] : xForwardedFor.split(',')[0].trim();
  }
  if (xRealIp) {
    return xRealIp;
  }
  return event.node.req.socket.remoteAddress || '127.0.0.1';
}

function checkRateLimit(ip: string): boolean {
  const now = Date.now();
  const entry = requestCounts.get(ip);

  if (!entry || now - entry.timestamp > RATE_LIMIT_WINDOW) {
    requestCounts.set(ip, { count: 1, timestamp: now });
    return true;
  }

  if (entry.count >= RATE_LIMIT) {
    return false;
  }

  entry.count++;
  return true;
}

const WHITELISTED_PATHS = ['/api/v1/auth/login', '/api/v1/system/health'];

function isWhitelisted(path: string): boolean {
  return WHITELISTED_PATHS.some((wp) => path.startsWith(wp));
}

export default defineEventHandler(async (event) => {
  const url = event.node.req.url;
  if (!url || !url.startsWith('/api/')) {
    return;
  }

  const config = useRuntimeConfig();
  const targetHost = config.public.apiHost || 'http://localhost:8000';

  const clientIp = getClientIp(event);

  if (!isWhitelisted(url) && !checkRateLimit(clientIp)) {
    const error = createError({
      statusCode: 429,
      statusMessage: 'Too Many Requests',
      message: '请求过于频繁，请稍后重试',
    });
    return sendError(event, error);
  }

  const target = `${targetHost}${url}`;

  try {
    const response = await proxyRequest(event, target, {
      headers: {
        'X-Forwarded-Host': event.node.req.headers.host || 'localhost:3000',
        'X-Real-IP': clientIp,
        'X-Forwarded-For': clientIp,
        'X-Forwarded-Proto': 'http',
      },
      onResponse: (responseEvent) => {
        const statusCode = responseEvent.node.res.statusCode;
        if (import.meta.dev && statusCode >= 400) {
          console.warn(`[ApiProxy] ${url} → ${statusCode}`);
        }
      },
    });
    return response;
  } catch (error: any) {
    // 生产环境仅记录简要信息，避免泄露堆栈中的敏感数据
    if (import.meta.dev) {
      console.error(`[ApiProxy] Error proxying ${url}:`, error instanceof Error ? error.message : error);
    } else {
      console.error(`[ApiProxy] Proxy failed for ${url}: ${error instanceof Error ? error.message : 'unknown'}`);
    }
    const proxyError = createError({
      statusCode: error.statusCode || 503,
      statusMessage: 'Service Unavailable',
      message: '后端服务暂不可用，请稍后重试',
    });
    return sendError(event, proxyError);
  }
});
