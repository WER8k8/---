// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  devtools: { enabled: true },

  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@nuxtjs/color-mode',
    '@nuxt/image',
    '@vite-pwa/nuxt'
  ],

  colorMode: {
    preference: 'light',
    fallback: 'light',
    classSuffix: ''
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE || '/api/v1',
      siteUrl: process.env.SITE_URL || 'https://www.youdingjiancai.com'
    }
  },

  app: {
    head: {
      titleTemplate: '%s | 优丁建材 - 专业保温材料制造商',
      title: '优丁建材 - 专业轻集料混凝土生产企业',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: '优丁建材专注新型建筑材料研发与生产，为客户提供优质、环保、高性能的轻集料混凝土产品' },
        { name: 'keywords', content: '轻集料混凝土,陶粒混凝土,加气混凝土,保温砂浆,建筑材料' },
        // Open Graph defaults
        { property: 'og:type', content: 'website' },
        { property: 'og:site_name', content: '优丁建材' },
        { property: 'og:url', content: 'https://www.youdingjiancai.com' },
        { property: 'og:image', content: '/images/og-default.jpg' },
        { property: 'og:image:width', content: '1200' },
        { property: 'og:image:height', content: '630' },
        // Twitter Card defaults
        { name: 'twitter:card', content: 'summary_large_image' },
        { name: 'twitter:site', content: '@youdingjiancai' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'canonical', href: 'https://www.youdingjiancai.com' }
      ],
      script: [
        {
          type: 'application/ld+json',
          children: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'Organization',
            name: '优丁建材有限公司',
            url: 'https://www.youdingjiancai.com',
            logo: 'https://www.youdingjiancai.com/images/logo.png',
            contactPoint: {
              '@type': 'ContactPoint',
              telephone: '+86-400-888-8888',
              contactType: 'customer service'
            }
          })
        }
      ]
    }
  },

  css: [
    '~/assets/css/main.css'
  ],

  // Performance optimizations
  experimental: {
    payloadExtraction: false,
    componentIslands: false,
    viewTransition: true
  },

  // Route rules for static generation
  routeRules: {
    '/': { prerender: true },
    '/products/**': { swr: 3600 }, // Cache for 1 hour
    '/cases/**': { swr: 3600 },
    '/news/**': { swr: 1800 }
  },

  // Image optimization (if using @nuxt/image)
  image: {
    format: ['webp', 'png'],
    quality: 80,
    screens: {
      xs: 320,
      sm: 640,
      md: 768,
      lg: 1024,
      xl: 1280,
      '2xl': 1536
    }
  },

  // PWA configuration
  pwa: {
    manifest: {
      name: '优丁建材 - 专业轻集料混凝土生产企业',
      short_name: '优丁建材',
      description: '优丁建材专注新型建筑材料研发与生产，为客户提供优质、环保、高性能的轻集料混凝土产品',
      theme_color: '#1890ff',
      background_color: '#ffffff',
      display: 'standalone',
      icons: [
        {
          src: '/images/icons/icon-192x192.png',
          sizes: '192x192',
          type: 'image/png'
        },
        {
          src: '/images/icons/icon-512x512.png',
          sizes: '512x512',
          type: 'image/png'
        }
      ]
    },
    workbox: {
      navigateFallback: '/',
      globPatterns: ['**/*.{js,css,html,png,svg,ico,json,webp}']
    },
    devOptions: {
      enabled: false,
      type: 'module'
    }
  },

  // Build optimizations
  vite: {
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['vue', 'vue-router'],
            ui: ['ant-design-vue']
          }
        }
      }
    },
    server: {
      hmr: {
        overlay: true
      }
    }
  }
})
