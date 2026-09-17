/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { ref, computed, onMounted, onUnmounted } from 'vue';

export interface OfflineQueueItem {
  id?: number;
  url: string;
  method: string;
  headers: Record<string, string>;
  body: unknown;
  path: string;
  timestamp: number;
  synced: number;
  retries: number;
}

export interface CacheStatusEntry {
  name: string;
  count: number;
}

export interface SyncResult {
  id: number;
  status: 'synced' | 'retry' | 'dropped';
  code?: number;
  error?: string;
  reason?: string;
}

export interface FetchWithCacheOptions {
  url: string;
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  body?: unknown;
  cacheFirst?: boolean;
  timeout?: number;
}

export interface FetchResult<T = unknown> {
  data: T | null;
  error: string | null;
  fromCache: boolean;
  status: number;
}

const SW_PATH = '/service-worker.js';
const SW_SCOPE = '/';

/**
 * 移动端离线缓存管理 Composable
 *
 * 功能：
 * - Service Worker 注册/注销
 * - 网络状态监听（navigator.onLine）
 * - 缓存优先请求（先读缓存再刷新）
 * - 离线操作队列（POST/PUT/DELETE 离线暂存，恢复后批量同步）
 * - 与 Service Worker 消息通道通信
 */
export function useOfflineCache() {
  // ===== 响应式状态 =====
  const isOnline = ref(true);
  const isRegistered = ref(false);
  const registration = ref<ServiceWorkerRegistration | null>(null);
  const cacheStatus = ref<CacheStatusEntry[]>([]);
  const queueCount = ref(0);
  const queueItems = ref<OfflineQueueItem[]>([]);
  const swVersion = ref<string | null>(null);
  const updateAvailable = ref(false);

  // ===== 计算属性 =====
  const isOffline = computed(() => !isOnline.value);
  const hasPendingQueue = computed(() => queueCount.value > 0);

  // ===== 工具函数 =====

  function getDefaultHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    // 尝试读取认证 token
    try {
      const token = document.cookie
        .split('; ')
        .find((row) => row.startsWith('admin_token='))
        ?.split('=')[1];
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    } catch {
      // ignore
    }
    return headers;
  }

  async function postMessageToSW<T = unknown>(
    type: string,
    payload?: Record<string, unknown>
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const controller = navigator.serviceWorker?.controller;
      if (!controller) {
        reject(new Error('Service Worker controller not available'));
        return;
      }

      const channel = new MessageChannel();
      channel.port1.onmessage = (event) => {
        if (event.data?.type?.includes('ERROR') || event.data?.error) {
          reject(new Error(event.data.error || 'SW message error'));
        } else {
          resolve(event.data as T);
        }
      };

      controller.postMessage({ type, ...payload }, [channel.port2]);

      // 5 秒超时
      setTimeout(() => {
        reject(new Error('SW message timeout'));
      }, 5000);
    });
  }

  // ===== Service Worker 生命周期 =====

  async function register(): Promise<boolean> {
    if (!('serviceWorker' in navigator)) {
      console.warn('[useOfflineCache] Service Worker not supported');
      return false;
    }

    try {
      const reg = await navigator.serviceWorker.register(SW_PATH, {
        scope: SW_SCOPE,
        updateViaCache: 'imports',
      });

      registration.value = reg;
      isRegistered.value = true;

      // 监听更新
      reg.addEventListener('updatefound', () => {
        const newWorker = reg.installing;
        if (newWorker) {
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              updateAvailable.value = true;
            }
          });
        }
      });

      // 等待激活
      if (reg.active) {
        await refreshCacheStatus();
        await refreshQueueStatus();
      }

      console.log('[useOfflineCache] SW registered:', reg.scope);
      return true;
    } catch (err) {
      console.error('[useOfflineCache] SW registration failed:', err);
      isRegistered.value = false;
      return false;
    }
  }

  async function unregister(): Promise<boolean> {
    if (!registration.value) {
      return false;
    }
    try {
      const success = await registration.value.unregister();
      isRegistered.value = !success;
      if (success) {
        registration.value = null;
      }
      return success;
    } catch (err) {
      console.error('[useOfflineCache] SW unregister failed:', err);
      return false;
    }
  }

  async function skipWaiting(): Promise<void> {
    await postMessageToSW('SKIP_WAITING');
    updateAvailable.value = false;
  }

  // ===== 网络状态 =====

  function updateOnlineStatus() {
    isOnline.value = navigator.onLine;
    if (isOnline.value && queueCount.value > 0) {
      // 网络恢复时自动触发后台同步
      requestSync();
    }
  }

  function requestSync(): void {
    if (!registration.value || !('sync' in registration.value)) {
      // 降级：手动同步
      forceSyncQueue().catch(() => {});
      return;
    }
    try {
      (registration.value as any).sync
        .register('offline-queue-sync')
        .catch(() => {
          // 权限被拒绝时降级手动同步
          forceSyncQueue().catch(() => {});
        });
    } catch {
      forceSyncQueue().catch(() => {});
    }
  }

  // ===== 缓存管理 =====

  async function refreshCacheStatus(): Promise<void> {
    try {
      const result = (await postMessageToSW<{ status: CacheStatusEntry[] }>(
        'GET_CACHE_STATUS'
      )) as any;
      if (result?.status) {
        cacheStatus.value = result.status;
      }
    } catch (err) {
      console.warn('[useOfflineCache] Failed to get cache status:', err);
    }
  }

  async function clearAllCaches(): Promise<boolean> {
    try {
      const result = (await postMessageToSW<{ success: boolean }>(
        'CLEAR_ALL_CACHES'
      )) as any;
      await refreshCacheStatus();
      return result?.success ?? false;
    } catch (err) {
      console.error('[useOfflineCache] Failed to clear caches:', err);
      return false;
    }
  }

  async function precacheAssets(assets: string[]): Promise<boolean> {
    try {
      const result = (await postMessageToSW<{ success: boolean }>('PRECACHE_ASSETS', {
        assets,
      })) as any;
      await refreshCacheStatus();
      return result?.success ?? false;
    } catch (err) {
      console.error('[useOfflineCache] Failed to precache:', err);
      return false;
    }
  }

  // ===== 离线队列管理 =====

  async function refreshQueueStatus(): Promise<void> {
    try {
      const result = (await postMessageToSW<{
        count: number;
        items: OfflineQueueItem[];
      }>('GET_OFFLINE_QUEUE')) as any;
      if (result) {
        queueCount.value = result.count ?? 0;
        queueItems.value = result.items ?? [];
      }
    } catch (err) {
      console.warn('[useOfflineCache] Failed to get queue status:', err);
    }
  }

  async function forceSyncQueue(): Promise<SyncResult[]> {
    try {
      const result = (await postMessageToSW<{ results: SyncResult[] }>(
        'FORCE_SYNC_QUEUE'
      )) as any;
      await refreshQueueStatus();
      return result?.results ?? [];
    } catch (err) {
      console.error('[useOfflineCache] Failed to sync queue:', err);
      return [];
    }
  }

  /**
   * 手动将操作加入离线队列（供业务层主动使用）
   */
  async function enqueueOperation(op: {
    url: string;
    method: string;
    headers?: Record<string, string>;
    body?: unknown;
  }): Promise<{ success: boolean; id?: number; error?: string }> {
    if (isOnline.value) {
      return { success: false, error: 'Device is online, send directly instead' };
    }

    try {
      const result = (await postMessageToSW<{ success: boolean; id?: number }>(
        'ENQUEUE_OPERATION',
        {
          operation: {
            ...op,
            path: new URL(op.url, location.origin).pathname,
          },
        }
      )) as any;
      await refreshQueueStatus();
      return { success: result?.success ?? false, id: result?.id };
    } catch (err: any) {
      return { success: false, error: err.message };
    }
  }

  // ===== 缓存优先请求 =====

  /**
   * 缓存优先请求：先读 Cache API，再发网络请求刷新缓存
   * 适用于 GET 请求，如 /api/v1/app/*、/api/v1/mobile/*
   */
  async function fetchWithCache<T = unknown>(
    options: FetchWithCacheOptions
  ): Promise<FetchResult<T>> {
    const { url, method = 'GET', headers = {}, body, cacheFirst = true, timeout = 15000 } =
      options;

    const mergedHeaders = { ...getDefaultHeaders(), ...headers };
    const requestInit: RequestInit = {
      method,
      headers: mergedHeaders,
      credentials: 'same-origin',
    };
    if (body && method !== 'GET') {
      requestInit.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    // 在线且不需要缓存优先：直接 fetch
    if (isOnline.value && !cacheFirst) {
      try {
        const response = await fetchWithTimeout(url, requestInit, timeout);
        const data = await parseResponse<T>(response);
        return {
          data,
          error: null,
          fromCache: false,
          status: response.status,
        };
      } catch (err: any) {
        return { data: null, error: err.message, fromCache: false, status: 0 };
      }
    }

    // 尝试从 Cache API 读取（仅 GET）
    let cachedResponse: Response | undefined;
    if (method === 'GET' && 'caches' in window) {
      try {
        const cacheNames = await caches.keys();
        for (const name of cacheNames) {
          const cache = await caches.open(name);
          const match = await cache.match(new Request(url, { method: 'GET' }));
          if (match) {
            cachedResponse = match;
            break;
          }
        }
      } catch {
        // ignore cache read errors
      }
    }

    // 如果有缓存且离线，直接返回缓存
    if (cachedResponse && isOffline.value) {
      try {
        const data = await parseResponse<T>(cachedResponse.clone());
        return {
          data,
          error: null,
          fromCache: true,
          status: cachedResponse.status,
        };
      } catch {
        // 缓存解析失败，继续尝试网络
      }
    }

    // 在线时：优先网络，但返回缓存作为兜底；或先返回缓存再后台刷新
    if (isOnline.value) {
      try {
        const response = await fetchWithTimeout(url, requestInit, timeout);
        // 更新缓存
        if (method === 'GET' && response.ok && 'caches' in window) {
          try {
            const cache = await caches.open('api-v2');
            await cache.put(new Request(url), response.clone());
          } catch {
            // ignore cache write errors
          }
        }
        const data = await parseResponse<T>(response);
        return {
          data,
          error: null,
          fromCache: false,
          status: response.status,
        };
      } catch (err: any) {
        // 网络失败，回退到缓存
        if (cachedResponse) {
          try {
            const data = await parseResponse<T>(cachedResponse.clone());
            return {
              data,
              error: null,
              fromCache: true,
              status: cachedResponse.status,
            };
          } catch {
            // ignore
          }
        }
        return { data: null, error: err.message, fromCache: false, status: 0 };
      }
    }

    // 离线且没有缓存
    return {
      data: null,
      error: '离线模式，且未找到缓存数据',
      fromCache: false,
      status: 503,
    };
  }

  async function fetchWithTimeout(
    url: string,
    init: RequestInit,
    timeoutMs: number
  ): Promise<Response> {
    return new Promise((resolve, reject) => {
      const controller = new AbortController();
      const timer = setTimeout(() => {
        controller.abort();
        reject(new Error(`Request timeout after ${timeoutMs}ms`));
      }, timeoutMs);

      fetch(url, { ...init, signal: controller.signal })
        .then((response) => {
          clearTimeout(timer);
          resolve(response);
        })
        .catch((err) => {
          clearTimeout(timer);
          reject(err);
        });
    });
  }

  async function parseResponse<T>(response: Response): Promise<T | null> {
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return response.json() as Promise<T>;
    }
    if (contentType.includes('text/')) {
      return (await response.text()) as unknown as T;
    }
    return response.blob() as unknown as T;
  }

  // ===== Service Worker 消息监听 =====

  function handleSWMessage(event: MessageEvent) {
    const data = event.data;
    if (!data || !data.type) return;

    switch (data.type) {
      case 'SW_ACTIVATED':
        swVersion.value = data.version ?? null;
        break;
      case 'CACHE_STATUS':
        if (data.status) cacheStatus.value = data.status;
        break;
      case 'OFFLINE_QUEUE_SYNCED':
        refreshQueueStatus().catch(() => {});
        break;
      case 'OFFLINE_QUEUE_STATUS':
        queueCount.value = data.count ?? 0;
        queueItems.value = data.items ?? [];
        break;
      default:
        break;
    }
  }

  // ===== 生命周期挂载 =====

  onMounted(() => {
    if (import.meta.server) return;

    updateOnlineStatus();
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    navigator.serviceWorker?.addEventListener('message', handleSWMessage);

    // 检查是否已有注册
    navigator.serviceWorker?.ready.then((reg) => {
      registration.value = reg;
      isRegistered.value = !!reg.active;
    });
  });

  onUnmounted(() => {
    if (import.meta.server) return;

    window.removeEventListener('online', updateOnlineStatus);
    window.removeEventListener('offline', updateOnlineStatus);
    navigator.serviceWorker?.removeEventListener('message', handleSWMessage);
  });

  return {
    // 状态
    isOnline,
    isOffline,
    isRegistered,
    updateAvailable,
    swVersion,
    cacheStatus,
    queueCount,
    queueItems,
    hasPendingQueue,

    // Service Worker 生命周期
    register,
    unregister,
    skipWaiting,

    // 缓存管理
    refreshCacheStatus,
    clearAllCaches,
    precacheAssets,

    // 离线队列
    refreshQueueStatus,
    forceSyncQueue,
    enqueueOperation,
    requestSync,

    // 请求封装
    fetchWithCache,
  };
}
