import { defineNuxtPlugin } from '#app';

/**
 * PWA Service Worker 注册插件
 *
 * 注意：@vite-pwa/nuxt 模块已自动处理 SW 注册。
 * 此插件仅在 @vite-pwa/nuxt 未注册 SW 时作为后备方案手动注册，
 * 避免重复注册导致冲突。
 */
export default defineNuxtPlugin(() => {
  if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
    return;
  }

  window.addEventListener('load', () => {
    // 检查是否已有活跃的 service worker（由 @vite-pwa/nuxt 注册）
    if (navigator.serviceWorker.controller) {
      return;
    }

    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .then((registration) => {
        console.log('[pwa plugin] SW registered as fallback:', registration.scope);

        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                console.log('[pwa plugin] New content available, please refresh.');
              }
            });
          }
        });
      })
      .catch((error) => {
        console.log('[pwa plugin] SW registration failed:', error);
      });
  });
});
