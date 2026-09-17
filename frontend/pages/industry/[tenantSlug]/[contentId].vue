/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="industry-content-page min-h-screen bg-surface">
    <div v-if="pending" class="min-h-[50vh] flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto" />
        <p class="mt-4 text-text-secondary text-sm">加载中...</p>
      </div>
    </div>

    <div v-else-if="fetchError" class="min-h-[50vh] flex items-center justify-center px-4">
      <div class="text-center max-w-md">
        <h1 class="text-xl font-bold text-text-primary mb-2">内容不可用</h1>
        <p class="text-text-secondary text-sm mb-6">{{ fetchError }}</p>
        <NuxtLink
          :to="`/industry/${tenantSlug}`"
          class="inline-flex px-5 py-2.5 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          返回租户枢纽
        </NuxtLink>
      </div>
    </div>

    <template v-else>
      <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <NuxtLink
            :to="`/industry/${tenantSlug}`"
            class="inline-flex items-center gap-1 text-sm text-primary hover:underline mb-4"
          >
            ← 返回 {{ tenantLabel }} 枢纽
          </NuxtLink>
          <p class="text-xs font-medium text-primary mb-2">行业内容摘要</p>
          <h1 class="text-2xl sm:text-3xl font-bold text-text-primary mb-4">
            {{ pageTitle }}
          </h1>
        </div>
      </section>

      <section class="py-8 sm:py-12">
        <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <article class="bg-surface rounded-2xl shadow-card border border-border p-6 sm:p-8">
            <p class="text-text-secondary text-sm sm:text-base leading-relaxed whitespace-pre-line mb-8">
              {{ pageSummary }}
            </p>

            <div class="pt-6 border-t border-border">
              <p class="text-sm text-text-secondary mb-4">
                本文为平台枢纽摘要，完整内容请访问企业官网：
              </p>
              <a
                :href="tenantCanonicalUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-colors"
              >
                阅读完整内容
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </a>
              <p v-if="!hasExplicitUrl" class="mt-3 text-xs text-text-secondary">
                提示：可通过 <code class="px-1 py-0.5 bg-surface-elevated rounded">?url=</code> 覆盖跳转地址
              </p>
            </div>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
interface HubPageData {
  title: string
  hub_summary: string | null
  tenant_canonical_url: string | null
}

interface HubApiResponse {
  code: number
  message: string
  data?: HubPageData
}

const route = useRoute()
const config = useRuntimeConfig()
const { apiUrl } = useApiRoot()

const tenantSlug = computed(() => String(route.params.tenantSlug || ''))
const contentId = computed(() => String(route.params.contentId || ''))
const tenantLabel = computed(() => tenantSlug.value.replace(/-/g, ' '))

const hubUrl = computed(
  () => apiUrl(`/hub/pages/${tenantSlug.value}/${contentId.value}`),
)

const { data: hubResponse, pending, error } = await useFetch<HubApiResponse>(hubUrl, {
  key: `hub-page-${tenantSlug.value}-${contentId.value}`,
})

const fetchError = computed(() => {
  if (error.value) return '内容不存在或未公开'
  if (hubResponse.value && hubResponse.value.code !== 0) return hubResponse.value.message || '加载失败'
  return null
})

const hubData = computed(() => hubResponse.value?.data)

const pageTitle = computed(() => hubData.value?.title || `${tenantLabel.value} 内容摘要`)
const pageSummary = computed(
  () =>
    hubData.value?.hub_summary
    || '暂无摘要内容。完整信息请访问企业独立站点。',
)

const hasExplicitUrl = computed(() => Boolean(route.query.url || hubData.value?.tenant_canonical_url))
const tenantCanonicalUrl = computed(() => {
  const fromQuery = route.query.url as string | undefined
  if (fromQuery) return fromQuery
  if (hubData.value?.tenant_canonical_url) return hubData.value.tenant_canonical_url
  return `https://${tenantSlug.value}.youding-saas.com`
})

const siteUrl = (config.public.siteUrl as string) || SITE_CONFIG.url
const canonicalUrl = computed(
  () => `${siteUrl.replace(/\/$/, '')}/industry/${tenantSlug.value}/${contentId.value}`,
)

useHead({
  title: computed(() => `${pageTitle.value} - 行业内容枢纽`),
  meta: [
    {
      name: 'description',
      content: computed(() => pageSummary.value.slice(0, 160)),
    },
    { name: 'robots', content: 'index, follow' },
  ],
  link: [{ rel: 'canonical', href: canonicalUrl }],
})
</script>
