const CACHE_NAME = 'youding-cache-v1'
const STATIC_CACHE = 'youding-static-v1'
const DYNAMIC_CACHE = 'youding-dynamic-v1'

const STATIC_ASSETS = [
  '/',
  '/offline',
  '/images/logo.png',
  '/images/icons/icon-192x192.png',
  '/images/icons/icon-512x512.png',
  '/favicon.ico'
]

const API_CACHE = [
  '/api/v1/products',
  '/api/v1/content',
  '/api/v1/cases'
]

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => {
      return cache.addAll(STATIC_ASSETS)
    })
  )
  self.skipWaiting()
})

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== STATIC_CACHE && key !== DYNAMIC_CACHE)
          .map(key => caches.delete(key))
      )
    })
  )
  self.clients.claim()
})

self.addEventListener('fetch', event => {
  const { request } = event
  const url = new URL(request.url)

  if (request.method !== 'GET') return

  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          const responseClone = response.clone()
          caches.open(DYNAMIC_CACHE).then(cache => {
            cache.put(request, responseClone)
          })
          return response
        })
        .catch(() => {
          return caches.match(request).then(cached => {
            if (cached) return cached
            return new Response(JSON.stringify({ error: '离线模式，数据不可用' }), {
              headers: { 'Content-Type': 'application/json' }
            })
          })
        })
    )
  } else if (request.destination === 'image' || url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/)) {
    event.respondWith(
      caches.match(request).then(cached => {
        return cached || fetch(request).then(response => {
          const responseClone = response.clone()
          caches.open(STATIC_CACHE).then(cache => {
            cache.put(request, responseClone)
          })
          return response
        }).catch(() => {
          return new Response('', { status: 404 })
        })
      })
    )
  } else if (request.destination === 'style' || url.pathname.match(/\.(css)$/)) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(cache => {
        return cache.match(request).then(cached => {
          return cached || fetch(request).then(response => {
            cache.put(request, response.clone())
            return response
          })
        })
      })
    )
  } else if (request.destination === 'script' || url.pathname.match(/\.(js)$/)) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(cache => {
        return cache.match(request).then(cached => {
          return cached || fetch(request).then(response => {
            cache.put(request, response.clone())
            return response
          })
        })
      })
    )
  } else {
    event.respondWith(
      caches.match(request).then(cached => {
        return cached || fetch(request).then(response => {
          const responseClone = response.clone()
          caches.open(DYNAMIC_CACHE).then(cache => {
            cache.put(request, responseClone)
          })
          return response
        }).catch(() => {
          return caches.match('/offline')
        })
      })
    )
  }
})

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})
