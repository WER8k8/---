<script setup lang="ts">
/**
 * Schema.org JSON-LD injection for SEO/GEO.
 * Injects structured data into <head> via Nuxt's built-in Head/Script components.
 */
const props = defineProps<{
  type: 'Organization' | 'WebSite' | 'Product' | 'BreadcrumbList' | 'FAQPage' | 'LocalBusiness' | 'QAPage'
  data: Record<string, any>
  locale?: 'zh' | 'en' | 'all'
}>()

const schemaData = computed(() => ({
  '@context': 'https://schema.org',
  '@type': props.type,
  ...props.data,
}))

const schemaString = computed(() => JSON.stringify(schemaData.value, null, 2))
</script>

<template>
  <Head>
    <Script
      type="application/ld+json"
      :children="schemaString"
    />
  </Head>
</template>
