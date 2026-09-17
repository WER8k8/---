/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { defineNuxtPlugin } from '#app';

function safeMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return '发生未知错误';
}

function logError(context: string, error: unknown, extra?: string) {
  if (import.meta.dev) {
    console.error(`[${context}]`, error instanceof Error ? error.message : error, extra || '');
    return;
  }
  // 生产环境：可替换为 Sentry/DataDog 等错误上报
  if (typeof window !== 'undefined') {
    const msg = `[${context}] ${safeMessage(error)}`;
    console.error(msg); // 最小化信息，避免泄露敏感数据
  }
}

export default defineNuxtPlugin((nuxtApp) => {
  // Vue 应用级错误
  nuxtApp.vueApp.config.errorHandler = (error: unknown, _instance: any, info: string) => {
    logError('Vue Error', error, info);
  };

  // 未处理的 Promise 拒绝
  nuxtApp.hook('app:created', () => {
    if (import.meta.client) {
      const onUnhandledRejection = (event: PromiseRejectionEvent) => {
        logError('Unhandled Rejection', event.reason);
        event.preventDefault();
      };
      const onGlobalError = (event: ErrorEvent) => {
        logError('Global Error', event.error || event.message);
      };

      window.addEventListener('unhandledrejection', onUnhandledRejection);
      window.addEventListener('error', onGlobalError);

      // 清理
      nuxtApp.hook('app:beforeUnmount', () => {
        window.removeEventListener('unhandledrejection', onUnhandledRejection);
        window.removeEventListener('error', onGlobalError);
      });
    }
  });

  nuxtApp.hook('page:error', (error) => {
    logError('Page Error', error);
  });

  nuxtApp.hook('route:error', (error) => {
    logError('Route Error', error);
  });
});
