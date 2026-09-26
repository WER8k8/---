/**
 * 统一滚动读取/控制。
 * 移动端(<768px)body 为 position:fixed,实际滚动容器是 #app(mobile.css iOS 橡皮筋规避);
 * 桌面端(≥768px)body 恢复 static,由 window 滚动。组件内直接读 window.scrollY 在移动端恒为 0。
 */

export function getAppScrollY(): number {
  if (typeof window === 'undefined') return 0;
  const app = document.getElementById('app');
  return window.scrollY || (app ? app.scrollTop : 0);
}

export function scrollAppToTop(behavior: ScrollBehavior = 'smooth'): void {
  if (typeof window === 'undefined') return;
  const app = document.getElementById('app');
  if (app && getComputedStyle(document.body).position === 'fixed') {
    app.scrollTo({ top: 0, behavior });
  } else {
    window.scrollTo({ top: 0, behavior });
  }
}

/** 同时监听 window 与 #app 两个滚动源,返回解绑函数 */
export function onAppScroll(handler: () => void): () => void {
  if (typeof window === 'undefined') return () => {};
  const app = document.getElementById('app');
  window.addEventListener('scroll', handler, { passive: true });
  app?.addEventListener('scroll', handler, { passive: true });
  return () => {
    window.removeEventListener('scroll', handler);
    app?.removeEventListener('scroll', handler);
  };
}
