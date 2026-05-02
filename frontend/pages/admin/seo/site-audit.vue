<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      站点审计
    </h1>
    <p class="text-sm text-text-secondary mb-6">
      11维度全面审计网站SEO健康状况，涵盖技术合规、元标签、页面结构、
      安全合规、AI爬虫友好度、移动适配、性能、链接质量、内容质量、社交媒
      体、AI搜索优化，发现潜在问题并获取优化建议。
    </p>
    <SiteAudit />
  </div>
</template>

<script setup lang="ts">
import SiteAudit from '~/components/seo/SiteAudit.vue'
definePageMeta({ layout: 'admin' })
</script>
