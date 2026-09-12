/** 出海计 PWA — 轻量离线壳（不缓存 API） */
const CACHE = 'chuhaiji-shell-v1'
const SHELL = ['/', '/manifest.webmanifest', '/vite.svg']

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => undefined))
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)
  if (url.pathname.startsWith('/api/')) return
  if (event.request.method !== 'GET') return
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return (
        cached ||
        fetch(event.request).catch(() =>
          caches.match('/').then((r) => r || new Response('offline', { status: 503 }))
        )
      )
    })
  )
})
