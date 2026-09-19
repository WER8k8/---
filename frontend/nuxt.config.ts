// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-01',
  devtools: { enabled: false },

  modules: ['@nuxtjs/tailwindcss', '@pinia/nuxt', '@nuxt/image', '@vite-pwa/nuxt', '@nuxtjs/i18n'],

  i18n: {
    locales: [
      { code: 'zh', iso: 'zh-CN', name: '简体中文', file: 'zh-CN.json' },
      { code: 'en', iso: 'en-US', name: 'English', file: 'en-US.json' },
      { code: 'de', iso: 'de-DE', name: 'Deutsch', file: 'de-DE.json' },
      { code: 'fr', iso: 'fr-FR', name: 'Français', file: 'fr-FR.json' },
      { code: 'es', iso: 'es-ES', name: 'Español', file: 'es-ES.json' },
      { code: 'ar', iso: 'ar-SA', name: 'العربية', file: 'ar-SA.json' },
      { code: 'ja', iso: 'ja-JP', name: '日本語', file: 'ja-JP.json' },
      { code: 'ko', iso: 'ko-KR', name: '한국어', file: 'ko-KR.json' },
      { code: 'ru', iso: 'ru-RU', name: 'Русский', file: 'ru-RU.json' },
      { code: 'pt', iso: 'pt-PT', name: 'Português', file: 'pt-PT.json' },
      { code: 'th', iso: 'th-TH', name: 'ไทย', file: 'th-TH.json' },
      { code: 'vi', iso: 'vi-VN', name: 'Tiếng Việt', file: 'vi-VN.json' },
    ],
    defaultLocale: 'zh',
    lazy: process.env.NODE_ENV !== 'production',
    restructureDir: '.',
    langDir: 'locales',
    strategy: 'prefix_except_default',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_redirected',
      redirectOn: 'root',
    },
  },

  // 错误处理配置
  errorHandler: {
    debug: process.env.NODE_ENV !== 'production',
    fallback: '/error',
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE || '/api/v1',
      // ENV-LOCK：本项目主后端固定 8001；8000 历史上被无关 Apache 占用
      apiHost: process.env.API_HOST || 'http://127.0.0.1:8001',
      siteUrl: process.env.SITE_URL || 'http://127.0.0.1:3000',
      merchantId: process.env.DEFAULT_MERCHANT_ID || process.env.NUXT_PUBLIC_MERCHANT_ID || '1',
      /** SaaS 租户 UUID，埋点与询盘归因必填（部署按域名注入） */
      tenantId: process.env.NUXT_PUBLIC_TENANT_ID || '',
      /** 代理节点 ID，代理子树流量汇总用 */
      agentNodeId: process.env.NUXT_PUBLIC_AGENT_NODE_ID || '',
      /** SaaS 主域名 */
      saasPrimaryDomain: process.env.SAAS_PRIMARY_DOMAIN || 'youding-saas.com',
      /** 与 frontend/admin 统一登录页；勿在仓库内写死端口，部署时通过环境变量注入 */
      unifiedAdminLoginUrl: process.env.NUXT_PUBLIC_UNIFIED_ADMIN_LOGIN_URL || '',
      /** Google Analytics 4 Measurement ID（G-XXXXXXXXX），留空则不加载 */
      ga4MeasurementId: process.env.NUXT_PUBLIC_GA4_MEASUREMENT_ID || '',
    },
  },

  app: {
    head: {
      titleTemplate: `%s | ${process.env.SITE_NAME || '优丁建材'} - 专业保温材料制造商`,
      title: `${process.env.SITE_NAME || '优丁建材'} - 专业轻集料混凝土生产企业`,
      htmlAttrs: {
        lang: 'zh-CN',
        dir: 'ltr',
      },
      meta: [
        { charset: 'utf-8' },
        {
          name: 'viewport',
          content:
            'width=device-width, initial-scale=1, maximum-scale=5, viewport-fit=cover',
        },
        {
          name: 'description',
          content: process.env.SITE_DESCRIPTION || '优丁建材专注新型建筑材料研发与生产，为客户提供优质、环保、高性能的轻集料混凝土产品',
        },
        { name: 'keywords', content: '轻集料混凝土,陶粒混凝土,保温砂浆,建筑材料,保温材料,轻质混凝土' },
        { name: 'theme-color', content: '#4a9b8c' },
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' },
        { name: 'mobile-web-app-capable', content: 'yes' },
        { name: 'format-detection', content: 'telephone=yes, address=no, email=no' },
        { name: 'HandheldFriendly', content: 'true' },
        { name: 'MobileOptimized', content: 'width' },
        { name: 'X-UA-Compatible', content: 'IE=edge' },
        // robots 与搜索引擎优化
        { name: 'robots', content: 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1' },
        { name: 'googlebot', content: 'index, follow' },
        // 地理标签（GEO 优化）
        { name: 'geo.region', content: 'CN-GD' },
        { name: 'geo.placename', content: '佛山' },
        { name: 'geo.position', content: '23.0288;113.1067' },
        { name: 'ICBM', content: '23.0288, 113.1067' },
        // Open Graph defaults
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: process.env.SITE_NAME || '优丁建材' },
        { property: 'og:url', content: process.env.SITE_URL || 'https://www.youdingjiancai.com' },
        { property: 'og:image', content: '/images/og-default.jpg' },
        { property: 'og:image:width', content: '1200' },
        { property: 'og:image:height', content: '630' },
        { property: 'og:image:alt', content: '优丁建材 - 专业轻集料混凝土生产企业' },
        { property: 'og:locale', content: 'zh_CN' },
        // Twitter Card defaults
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:site', content: process.env.TWITTER_HANDLE || '@youdingjiancai' },
        { name: 'twitter:image', content: '/images/og-default.jpg' },
        { name: 'twitter:image:alt', content: '优丁建材 - 专业轻集料混凝土生产企业' },
        // Mobile optimization
        { property: 'og:title', content: `${process.env.SITE_NAME || '优丁建材'} - 专业轻集料混凝土生产企业` },
        {
          property: 'og:description',
          content: process.env.SITE_DESCRIPTION || '优丁建材专注新型建筑材料研发与生产，为客户提供优质、环保、高性能的轻集料混凝土产品',
        },
        // 性能优化提示
        { 'http-equiv': 'x-dns-prefetch-control', content: 'on' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'canonical', href: process.env.SITE_URL || 'https://www.youdingjiancai.com' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'dns-prefetch', href: 'https://fonts.googleapis.com' },
        { rel: 'dns-prefetch', href: 'https://fonts.gstatic.com' },
        // 字体预加载 - 减少 CLS
        {
          rel: 'preload',
          href: 'https://fonts.gstatic.com/s/notosanssc/v37/k3kCo84MPvpLmixcA63oeAL7Iq4X_qUYlqoO_IvE.woff2',
          as: 'font',
          type: 'font/woff2',
          crossorigin: '',
        },
        {
          rel: 'preload',
          href: 'https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiJ-Ek-_EeA.woff2',
          as: 'font',
          type: 'font/woff2',
          crossorigin: '',
        },
        // Non-blocking webfonts
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap',
          media: 'print',
          onload: "this.media='all'",
        },
        { rel: 'apple-touch-icon', sizes: '180x180', href: '/images/icons/icon-192x192.png' },
        { rel: 'apple-touch-icon-precomposed', href: '/images/icons/icon-192x192.png' },
        // 多语言链接（hreflang）
        { rel: 'alternate', hreflang: 'zh-CN', href: process.env.SITE_URL || 'https://www.youdingjiancai.com' },
        { rel: 'alternate', hreflang: 'en', href: `${process.env.SITE_URL || 'https://www.youdingjiancai.com'}/en` },
        { rel: 'alternate', hreflang: 'x-default', href: process.env.SITE_URL || 'https://www.youdingjiancai.com' },
      ],
      script: [
        {
          type: 'application/ld+json',
          children: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'LocalBusiness',
            '@id': `${process.env.SITE_URL || 'https://www.youdingjiancai.com'}/#organization`,
            name: process.env.SITE_FULL_NAME || '优丁建材有限公司',
            alternateName: '优丁建材',
            url: process.env.SITE_URL || 'https://www.youdingjiancai.com',
            logo: `${process.env.SITE_URL || 'https://www.youdingjiancai.com'}/images/logo.png`,
            image: `${process.env.SITE_URL || 'https://www.youdingjiancai.com'}/images/og-default.jpg`,
            description: process.env.SITE_DESCRIPTION || '优丁建材专注新型建筑材料研发与生产，为客户提供优质、环保、高性能的轻集料混凝土产品',
            foundingDate: '2006',
            priceRange: '$$',
            areaServed: [
              { '@type': 'Country', name: 'China' },
              { '@type': 'Country', name: 'United States' },
              { '@type': 'Country', name: 'Germany' },
              { '@type': 'Country', name: 'Japan' },
              { '@type': 'Country', name: 'South Korea' },
            ],
            address: {
              '@type': 'PostalAddress',
              streetAddress: '广东省佛山市南海区',
              addressLocality: '佛山',
              addressRegion: '广东省',
              postalCode: '528000',
              addressCountry: 'CN',
            },
            geo: {
              '@type': 'GeoCoordinates',
              latitude: 23.0288,
              longitude: 113.1067,
            },
            contactPoint: {
              '@type': 'ContactPoint',
              telephone: process.env.SITE_PHONE || '+86-400-888-8888',
              contactType: 'customer service',
              availableLanguage: ['Chinese', 'English'],
            },
            sameAs: [
              'https://www.youdingjiancai.com',
            ],
            hasOfferCatalog: {
              '@type': 'OfferCatalog',
              name: '建筑材料产品',
              itemListElement: [
                { '@type': 'Offer', itemOffered: { '@type': 'Product', name: '轻集料混凝土' } },
                { '@type': 'Offer', itemOffered: { '@type': 'Product', name: '陶粒混凝土' } },
                { '@type': 'Offer', itemOffered: { '@type': 'Product', name: '保温砂浆' } },
              ],
            },
          }),
        },
        {
          type: 'application/ld+json',
          children: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            '@id': `${process.env.SITE_URL || 'https://www.youdingjiancai.com'}/#website`,
            url: process.env.SITE_URL || 'https://www.youdingjiancai.com',
            name: process.env.SITE_NAME || '优丁建材',
            inLanguage: 'zh-CN',
            potentialAction: {
              '@type': 'SearchAction',
              target: {
                '@type': 'EntryPoint',
                urlTemplate: `${process.env.SITE_URL || 'https://www.youdingjiancai.com'}/search?q={search_term_string}`,
              },
              'query-input': 'required name=search_term_string',
            },
          }),
        },
        ...(process.env.NUXT_PUBLIC_GA4_MEASUREMENT_ID
          ? [
              {
                src: `https://www.googletagmanager.com/gtag/js?id=${process.env.NUXT_PUBLIC_GA4_MEASUREMENT_ID}`,
                async: true,
              },
              {
                children: `
                  window.dataLayer = window.dataLayer || [];
                  function gtag(){dataLayer.push(arguments);}
                  gtag('js', new Date());
                  gtag('config', '${process.env.NUXT_PUBLIC_GA4_MEASUREMENT_ID}', {
                    send_page_view: true
                  });
                `,
              },
            ]
          : []),
      ],
    },
  },

  css: [
    '~/assets/css/main.css',
    '~/assets/css/animations.css',
    '~/assets/css/mobile.css',
    '~/assets/css/luna-tokens.css',
  ],

  // Performance optimizations
  experimental: {
    payloadExtraction: true,
    componentIslands: true,
    viewTransition: false,
  },

  // Critical CSS inlining for faster FCP
  features: {
    inlineStyles: true,
    clientFallback: true,
  },

  // Preload strategy
  preload: {
    match: '/_nuxt/(?:app|runtime|vendors).*\\.js$',
    files: ['critical.*'],
  },

  // Nitro server optimizations
  nitro: {
    compressPublicAssets: true,
    minify: true,
    devProxy: {
      '/api': {
        target: process.env.API_HOST || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/uploads': {
        target: process.env.API_HOST || 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
    },
    prerender: {
      crawlLinks: true,
      routes: ['/', '/about', '/contact', '/products', '/cases', '/news'],
      failOnError: false,
    },
  },

  // Sourcemap: hidden in production for smaller bundles + debugging
  sourcemap: {
    server: true,
    client: false,
  },

  // Route rules for static generation & caching
  // PWA 配置
  pwa: {
    enabled: true,
    devOptions: {
      enabled: false,
    },
    manifest: {
      name: '优丁建材',
      short_name: '优丁建材',
      description: '专业轻集料混凝土与保温材料供应商',
      theme_color: '#4a9b8c',
      background_color: '#ffffff',
      display: 'standalone',
      display_override: ['window-controls-overlay', 'minimal-ui'],
      orientation: 'portrait-primary',
      start_url: '/',
      scope: '/',
      lang: 'zh-CN',
      icons: [
        {
          src: '/images/icons/icon-192x192.png',
          sizes: '192x192',
          type: 'image/png',
        },
        {
          src: '/images/icons/icon-512x512.png',
          sizes: '512x512',
          type: 'image/png',
        },
        {
          src: '/images/icons/icon-512x512.png',
          sizes: '512x512',
          type: 'image/png',
          purpose: 'maskable',
        },
      ],
      categories: ['business', 'industrial'],
    },
    workbox: {
      globPatterns: ['**/*.{js,css,html,png,jpg,jpeg,gif,svg,ico,webp,woff,woff2}'],
      navigateFallback: '/',
      // 缓存大小限制
      maximumFileSizeToCacheInBytes: 5 * 1024 * 1024, // 5MB
      // 运行时缓存策略
      runtimeCaching: [
        // API 请求 - Network First（优先网络，离线时回退缓存）
        {
          urlPattern: /^https?:\/\/.*\/api\/.*/i,
          handler: 'NetworkFirst' as const,
          method: 'GET',
          options: {
            networkTimeoutSeconds: 10,
            cacheName: 'api-cache',
            expiration: {
              maxEntries: 50,
              maxAgeSeconds: 5 * 60, // 5 分钟
            },
            cacheableResponse: {
              statuses: [0, 200],
            },
          },
        },
        // 图片资源 - Cache First（优先缓存，减少网络请求）
        {
          urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|ico)$/,
          handler: 'CacheFirst' as const,
          options: {
            cacheName: 'image-cache',
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 30 * 24 * 60 * 60, // 30 天
            },
            cacheableResponse: {
              statuses: [0, 200],
            },
          },
        },
        // 字体文件 - Cache First（字体变化少，长期缓存）
        {
          urlPattern: /\.(?:woff|woff2|ttf|eot)$/,
          handler: 'CacheFirst' as const,
          options: {
            cacheName: 'font-cache',
            expiration: {
              maxEntries: 20,
              maxAgeSeconds: 365 * 24 * 60 * 60, // 1 年
            },
            cacheableResponse: {
              statuses: [0, 200],
            },
          },
        },
        // Nuxt 构建资源 - Stale While Revalidate（后台更新）
        {
          urlPattern: /^https?:\/\/.*\/_nuxt\/.*/i,
          handler: 'StaleWhileRevalidate' as const,
          options: {
            cacheName: 'nuxt-assets-cache',
            expiration: {
              maxEntries: 200,
              maxAgeSeconds: 30 * 24 * 60 * 60, // 30 天
            },
            cacheableResponse: {
              statuses: [0, 200],
            },
          },
        },
        // Google Fonts - Stale While Revalidate
        {
          urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
          handler: 'StaleWhileRevalidate' as const,
          options: {
            cacheName: 'google-fonts-stylesheets',
            expiration: {
              maxEntries: 10,
              maxAgeSeconds: 7 * 24 * 60 * 60, // 7 天
            },
          },
        },
        {
          urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/i,
          handler: 'CacheFirst' as const,
          options: {
            cacheName: 'google-fonts-webfonts',
            expiration: {
              maxEntries: 30,
              maxAgeSeconds: 365 * 24 * 60 * 60, // 1 年
            },
            cacheableResponse: {
              statuses: [0, 200],
            },
          },
        },
        // 页面导航 - Network First（确保页面内容最新）
        {
          urlPattern: /^https?:\/\/.*\/(?:products|cases|news|about|contact)?.*$/i,
          handler: 'NetworkFirst' as const,
          options: {
            networkTimeoutSeconds: 5,
            cacheName: 'pages-cache',
            expiration: {
              maxEntries: 50,
              maxAgeSeconds: 24 * 60 * 60, // 1 天
            },
          },
        },
      ],
      // 2026-09-05：移除 precacheManifest——workbox-build 新版 GenerateSW 已删除该
      // 选项（WorkboxConfigError: property is not expected to be here），预缓存由
      // 上方 globPatterns 自动生成，SPA 路由离线回退由 navigateFallback 兜底。
    },
    registerType: 'autoUpdate',
    client: {
      installPrompt: true,
    },
  },

  routeRules: {
    '/': { prerender: true },
    '/products/**': { swr: 3600 },
    '/cases/**': { swr: 3600 },
    '/news/**': { swr: 1800 },
    '/about': { swr: 3600 },
    '/contact': { swr: 1800 },
    // 租户 L-Pro 预览：SSR 首屏有内容（intersect 插件已修，水合可正常完成）
    '/tenant': { ssr: true },
    '/tenant/**': { ssr: true },
  },

  // Image optimization
  image: {
    format: ['webp', 'png'],
    quality: 80,
    screens: {
      xs: 320,
      sm: 640,
      md: 768,
      lg: 1024,
      xl: 1280,
      '2xl': 1536,
    },
  },

  devServer: {
    host: '127.0.0.1',
    port: 3000,
  },

  // Build optimizations
  vite: {
    build: {
      cssMinify: 'esbuild',
      minify: 'esbuild',
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('vue') || id.includes('vue-router')) {
                return 'vendor-vue';
              }
              if (id.includes('pinia')) {
                return 'vendor-pinia';
              }
              if (id.includes('ant-design-vue') || id.includes('@ant-design')) {
                return 'vendor-ui';
              }
              if (id.includes('echarts') || id.includes('vue-echarts')) {
                return 'vendor-charts';
              }
              if (id.includes('axios')) {
                return 'vendor-axios';
              }
              if (id.includes('@tiptap')) {
                return 'vendor-editor';
              }
              if (id.includes('@vueuse')) {
                return 'vendor-vueuse';
              }
              return 'vendor-common';
            }
            if (id.includes('composables')) {
              return 'chunk-composables';
            }
            if (id.includes('components')) {
              return 'chunk-components';
            }
            if (id.includes('stores')) {
              return 'chunk-stores';
            }
            if (id.includes('utils')) {
              return 'chunk-utils';
            }
          },
        },
      },
    },
    server: {
      host: '127.0.0.1',
      port: 3000,
      proxy: {
        '/api': {
          target: process.env.API_HOST || 'http://127.0.0.1:8001',
          changeOrigin: true,
          secure: false,
        },
        '/uploads': {
          target: process.env.API_HOST || 'http://127.0.0.1:8001',
          changeOrigin: true,
          secure: false,
        },
      },
      hmr: {
        overlay: true,
      },
    },
  },
});
