<template>
  <div class="industry-hub-page min-h-screen bg-surface">
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-12 sm:py-16 lg:py-20">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <p class="text-sm font-medium text-primary mb-3">行业内容枢纽</p>
        <h1 class="text-2xl sm:text-3xl lg:text-4xl font-bold text-text-primary mb-4">
          {{ tenantLabel }} · 精选摘要
        </h1>
        <p class="text-sm sm:text-base text-text-secondary max-w-2xl mx-auto leading-relaxed">
          本站为平台权重枢纽页，展示合作企业的公开内容摘要。完整内容请访问企业独立站点。
        </p>
      </div>
    </section>

    <section class="py-10 sm:py-14">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="bg-surface rounded-2xl shadow-card border border-border p-6 sm:p-8">
          <h2 class="text-lg font-semibold text-text-primary mb-3">关于 {{ tenantLabel }}</h2>
          <p class="text-text-secondary text-sm sm:text-base leading-relaxed mb-6">
            {{ hubIntro }}
          </p>
          <a
            :href="tenantSiteUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-colors"
          >
            访问企业官网
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
          <p v-if="!hasTenantUrl" class="mt-3 text-xs text-text-secondary">
            提示：可通过 <code class="px-1 py-0.5 bg-surface-elevated rounded">?url=</code> 指定企业站点地址
          </p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const config = useRuntimeConfig()

const tenantSlug = computed(() => String(route.params.tenantSlug || ''))
const tenantLabel = computed(() => tenantSlug.value.replace(/-/g, ' '))

const hasTenantUrl = computed(() => Boolean(route.query.url))
const tenantSiteUrl = computed(() => {
  const fromQuery = route.query.url as string | undefined
  if (fromQuery) return fromQuery
  return `https://${tenantSlug.value}.youding-saas.com`
})

const hubIntro = computed(
  () => `${tenantLabel.value} 是平台合作企业。本页为平台 SEO 枢纽摘要入口，完整产品与企业信息请前往其独立站点浏览。`,
)

const siteUrl = (config.public.siteUrl as string) || SITE_CONFIG.url
const canonicalUrl = computed(() => `${siteUrl.replace(/\/$/, '')}/industry/${tenantSlug.value}`)

useHead({
  title: computed(() => `${tenantLabel.value} - 行业内容枢纽`),
  meta: [
    {
      name: 'description',
      content: computed(() => `${tenantLabel.value} 在平台的内容摘要枢纽页`),
    },
    { name: 'robots', content: 'index, follow' },
  ],
  link: [{ rel: 'canonical', href: canonicalUrl }],
})
</script>
