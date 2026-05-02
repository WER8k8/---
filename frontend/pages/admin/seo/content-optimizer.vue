<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      AI 内容优化
    </h1>
    <p class="text-sm text-text-secondary mb-6">
      利用AI技术优化网站内容，提升SEO排名和用户体验，
      同时确保行业技术参数的准确保留。
    </p>
    <ContentOptimizer />
  </div>
</template>

<script setup lang="ts">
import ContentOptimizer from '~/components/seo/ContentOptimizer.vue'
definePageMeta({ layout: 'admin' })
</script>
