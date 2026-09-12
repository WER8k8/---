/**
 * Service Worker — 移动端离线缓存与后台同步
 * Workbox 风格（原生 Cache API，无外部依赖）
 * @version 2.0.0
 */

const CACHE_VERSION = 'v2';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const DYNAMIC_CACHE = `dynamic-${CACHE_VERSION}`;
const API_CACHE = `api-${CACHE_VERSION}`;
const IMAGE_CACHE = `image-${CACHE_VERSION}`;
const FONT_CACHE = `font-${CACHE_VERSION}`;

const ALL_CACHES = [STATIC_CACHE, DYNAMIC_CACHE, API_CACHE, IMAGE_CACHE, FONT_CACHE];

// 预缓存核心资源（构建时注入或手动维护）
const PRECACHE_ASSETS = [
  '/',
  '/offline',
  '/manifest.json',
  '/favicon.ico',
  '/logo.png',
  '/images/icons/icon-192x192.png',
  '/images/icons/icon-512x512.png',
];

// 后台同步队列数据库
const DB_NAME = 'youding-sw-db';
const DB_VERSION = 1;
const STORE_NAME = 'offline-queue';

// ============ IndexedDB 工具（Service Worker 内） ============

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
        store.createIndex('timestamp', 'timestamp', { unique: false });
        store.createIndex('synced', 'synced', { unique: false });
      }
    };
  });
}

async function enqueueOperation(op) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const item = {
      ...op,
      timestamp: Date.now(),
      synced: 0,
      retries: 0,
    };
    const request = store.add(item);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function getPendingOperations() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const index = store.index('synced');
    const request = index.getAll(0);
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

async function markOperationSynced(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const request = store.delete(id);
    request.onsuccess = () => resolve(true);
    request.onerror = () => reject(request.error);
  });
}

async function incrementRetry(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    const getReq = store.get(id);
    getReq.onsuccess = () => {
      const data = getReq.result;
      if (data) {
        data.retries = (data.retries || 0) + 1;
        const putReq = store.put(data);
        putReq.onsuccess = () => resolve(data.retries);
      } else {
        resolve(0);
      }
    };
    getReq.onerror = () => reject(getReq.error);
  });
}

// ============ 缓存策略 ============

async function cacheFirst(request, cacheName, fallbackUrl) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;

  try {
    const response = await fetch(request);
    if (response && response.status === 200) {
      const clone = response.clone();
      await cache.put(request, clone);
    }
    return response;
  } catch (err) {
    if (fallbackUrl) {
      const fallback = await cache.match(fallbackUrl);
      if (fallback) return fallback;
    }
    throw err;
  }
}

async function networkFirst(request, cacheName, timeoutMs = 10000) {
  const cache = await caches.open(cacheName);

  return new Promise((resolve, reject) => {
    let resolved = false;
    const timer = setTimeout(async () => {
      if (!resolved) {
        resolved = true;
        const cached = await cache.match(request);
        if (cached) {
          resolve(cached);
        } else {
          reject(new Error('Network timeout and no cache'));
        }
      }
    }, timeoutMs);

    fetch(request)
      .then((response) => {
        if (!resolved) {
          resolved = true;
          clearTimeout(timer);
          if (response && response.status === 200) {
            const clone = response.clone();
            cache.put(request, clone).catch(() => {});
          }
          resolve(response);
        }
      })
      .catch(async (err) => {
        if (!resolved) {
          resolved = true;
          clearTimeout(timer);
          const cached = await cache.match(request);
          if (cached) {
            resolve(cached);
          } else {
            reject(err);
          }
        }
      });
  });
}

async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request)
    .then((response) => {
      if (response && response.status === 200) {
        const clone = response.clone();
        cache.put(request, clone).catch(() => {});
      }
      return response;
    })
    .catch(() => cached);

  return cached || fetchPromise;
}

// ============ 后台同步处理器 ============

async function processOfflineQueue() {
  const ops = await getPendingOperations();
  const results = [];

  for (const op of ops) {
    if (op.retries >= 5) {
      await markOperationSynced(op.id);
      results.push({ id: op.id, status: 'dropped', reason: 'max_retries' });
      continue;
    }

    try {
      const response = await fetch(op.url, {
        method: op.method,
        headers: op.headers || { 'Content-Type': 'application/json' },
        body: op.body ? JSON.stringify(op.body) : undefined,
        credentials: 'same-origin',
      });

      if (response.ok) {
        await markOperationSynced(op.id);
        results.push({ id: op.id, status: 'synced' });
      } else {
        await incrementRetry(op.id);
        results.push({ id: op.id, status: 'retry', code: response.status });
      }
    } catch (err) {
      await incrementRetry(op.id);
      results.push({ id: op.id, status: 'retry', error: err.message });
    }
  }

  // 通知所有客户端
  const clientsList = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
  clientsList.forEach((client) => {
    client.postMessage({
      type: 'OFFLINE_QUEUE_SYNCED',
      results,
      remaining: ops.length - results.filter((r) => r.status === 'synced').length,
    });
  });

  return results;
}

// ============ 安装 / 激活 ============

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(STATIC_CACHE)
      .then((cache) => cache.addAll(PRECACHE_ASSETS))
      .then(() => self.skipWaiting())
      .catch((err) => {
        console.warn('[SW] Precache failed:', err);
        self.skipWaiting();
      })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => {
        return Promise.all(
          keys
            .filter((key) => !ALL_CACHES.includes(key))
            .map((key) => caches.delete(key))
        );
      })
      .then(() => self.clients.claim())
      .then(async () => {
        // 通知所有客户端 SW 已激活
        const clientsList = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
        clientsList.forEach((client) => {
          client.postMessage({ type: 'SW_ACTIVATED', version: CACHE_VERSION });
        });
      })
  );
});

// ============ Fetch 拦截 ============

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // 非 GET 请求不走缓存（除后台同步相关的 POST/PUT/DELETE）
  if (request.method !== 'GET') {
    // 离线时将写操作存入队列
    if (!self.navigator.onLine && (request.method === 'POST' || request.method === 'PUT' || request.method === 'DELETE')) {
      if (url.pathname.startsWith('/api/')) {
        event.respondWith(
          request
            .clone()
            .json()
            .catch(() => undefined)
            .then((body) => {
              const headers = {};
              request.headers.forEach((v, k) => {
                headers[k] = v;
              });
              return enqueueOperation({
                url: request.url,
                method: request.method,
                headers,
                body,
                path: url.pathname,
              });
            })
            .then(() => {
              return new Response(
                JSON.stringify({
                  success: true,
                  offline: true,
                  message: '操作已离线保存，将在网络恢复后同步',
                  queued: true,
                }),
                { status: 202, headers: { 'Content-Type': 'application/json' } }
              );
            })
            .catch((err) => {
              return new Response(
                JSON.stringify({ success: false, error: err.message }),
                { status: 500, headers: { 'Content-Type': 'application/json' } }
              );
            })
        );
      }
    }
    return;
  }

  // API 请求：/api/v1/mobile/* 和 /api/v1/app/*
  if (
    url.pathname.startsWith('/api/v1/mobile/') ||
    url.pathname.startsWith('/api/v1/app/') ||
    url.pathname.startsWith('/api/v1/')
  ) {
    event.respondWith(
      networkFirst(request, API_CACHE, 8000).catch(() => {
        // 完全离线时的 JSON 回退
        return new Response(
          JSON.stringify({
            error: '离线模式，数据不可用',
            offline: true,
            timestamp: new Date().toISOString(),
          }),
          {
            status: 503,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      })
    );
    return;
  }

  // 字体
  if (request.destination === 'font' || url.pathname.match(/\.(woff2?|ttf|otf|eot)$/)) {
    event.respondWith(cacheFirst(request, FONT_CACHE));
    return;
  }

  // 图片
  if (
    request.destination === 'image' ||
    url.pathname.match(/\.(png|jpe?g|gif|webp|svg|ico|avif)$/i)
  ) {
    event.respondWith(
      cacheFirst(request, IMAGE_CACHE).catch(() => {
        return new Response('', { status: 404, statusText: 'Not Found' });
      })
    );
    return;
  }

  // CSS
  if (request.destination === 'style' || url.pathname.endsWith('.css')) {
    event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
    return;
  }

  // JS
  if (request.destination === 'script' || url.pathname.endsWith('.js')) {
    event.respondWith(staleWhileRevalidate(request, STATIC_CACHE));
    return;
  }

  // 文档 / 导航
  if (request.mode === 'navigate') {
    event.respondWith(
      cacheFirst(request, STATIC_CACHE, '/').catch(() => {
        return new Response(
          `<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>离线模式</title></head>
<body><h1>您当前处于离线状态</h1><p>请检查网络连接后重试。</p></body>
</html>`,
          { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
        );
      })
    );
    return;
  }

  // 默认策略
  event.respondWith(
    staleWhileRevalidate(request, DYNAMIC_CACHE).catch(() => {
      return new Response('', { status: 404 });
    })
  );
});

// ============ 后台同步 ============

self.addEventListener('sync', (event) => {
  if (event.tag === 'offline-queue-sync') {
    event.waitUntil(processOfflineQueue());
  }
});

// ============ 推送（可选占位） ============

self.addEventListener('push', (event) => {
  if (!event.data) return;
  const data = event.data.json().catch(() => ({}));
  event.waitUntil(
    Promise.resolve(data).then((payload) => {
      return self.registration.showNotification(payload.title || '优丁建材', {
        body: payload.body || '您有一条新消息',
        icon: '/images/icons/icon-192x192.png',
        badge: '/images/icons/icon-192x192.png',
        tag: payload.tag || 'default',
        data: payload.data || {},
        requireInteraction: false,
      });
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientsList) => {
        const url = event.notification.data?.url || '/';
        for (const client of clientsList) {
          if (client.url === url && 'focus' in client) {
            return client.focus();
          }
        }
        if (self.clients.openWindow) {
          return self.clients.openWindow(url);
        }
      })
  );
});

// ============ 消息通道（与主线程通信） ============

self.addEventListener('message', (event) => {
  const { data, source } = event;
  if (!data || !data.type) return;

  switch (data.type) {
    case 'SKIP_WAITING': {
      self.skipWaiting();
      break;
    }

    case 'GET_CACHE_STATUS': {
      event.waitUntil(
        Promise.all(
          ALL_CACHES.map(async (name) => {
            const cache = await caches.open(name);
            const keys = await cache.keys();
            return { name, count: keys.length };
          })
        ).then((status) => {
          source.postMessage({ type: 'CACHE_STATUS', status });
        })
      );
      break;
    }

    case 'CLEAR_ALL_CACHES': {
      event.waitUntil(
        caches
          .keys()
          .then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
          .then(() => {
            source.postMessage({ type: 'CACHE_CLEARED', success: true });
          })
          .catch((err) => {
            source.postMessage({ type: 'CACHE_CLEARED', success: false, error: err.message });
          })
      );
      break;
    }

    case 'GET_OFFLINE_QUEUE': {
      event.waitUntil(
        getPendingOperations().then((ops) => {
          source.postMessage({ type: 'OFFLINE_QUEUE_STATUS', count: ops.length, items: ops });
        })
      );
      break;
    }

    case 'FORCE_SYNC_QUEUE': {
      event.waitUntil(
        processOfflineQueue().then((results) => {
          source.postMessage({ type: 'OFFLINE_QUEUE_FORCED', results });
        })
      );
      break;
    }

    case 'ENQUEUE_OPERATION': {
      if (data.operation) {
        event.waitUntil(
          enqueueOperation(data.operation)
            .then((id) => {
              source.postMessage({ type: 'ENQUEUE_DONE', success: true, id });
            })
            .catch((err) => {
              source.postMessage({ type: 'ENQUEUE_DONE', success: false, error: err.message });
            })
        );
      }
      break;
    }

    case 'PRECACHE_ASSETS': {
      if (Array.isArray(data.assets)) {
        event.waitUntil(
          caches
            .open(STATIC_CACHE)
            .then((cache) => cache.addAll(data.assets))
            .then(() => {
              source.postMessage({ type: 'PRECACHE_DONE', success: true });
            })
            .catch((err) => {
              source.postMessage({ type: 'PRECACHE_DONE', success: false, error: err.message });
            })
        );
      }
      break;
    }

    default:
      break;
  }
});
