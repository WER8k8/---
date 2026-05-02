<template>
  <div>
    <h1 class="text-2xl font-bold text-primary-900 mb-6">
      管理后台
    </h1>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <NuxtLink
        to="/admin/seo/llms-txt"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover transition-all hover:-translate-y-0.5"
      >
        <div class="text-3xl mb-3">
          📄
        </div>
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          LLMs.txt 生成
        </h2>
        <p class="text-sm text-text-secondary">
          生成AI搜索引擎友好的LLMs.txt文件，优化AI抓取效果
        </p>
      </NuxtLink>
      <NuxtLink
        to="/admin/seo/content-optimizer"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover transition-all hover:-translate-y-0.5"
      >
        <div class="text-3xl mb-3">
          ✨
        </div>
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          AI 内容优化
        </h2>
        <p class="text-sm text-text-secondary">
          利用AI技术优化网站内容，提升SEO排名和用户体验
        </p>
      </NuxtLink>
      <NuxtLink
        to="/admin/seo/site-audit"
        class="bg-surface rounded-xl border border-border p-6 hover:shadow-card-hover transition-all hover:-translate-y-0.5"
      >
        <div class="text-3xl mb-3">
          🔍
        </div>
        <h2 class="text-lg font-semibold text-primary-900 mb-2">
          站点审计
        </h2>
        <p class="text-sm text-text-secondary">
          11维度全面审计网站SEO健康状况，发现优化机会
        </p>
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'admin' })
</script>
